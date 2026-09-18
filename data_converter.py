from PIL import Image
import cv2
import numpy as np
from rapidfuzz import process
import json
import re
import torch
from converter import ocr_predict, ocr_with_fuzzy, model, val_transform, idx_to_char, device, skill_names, char_names_outer, char_names, characters, mood_list
import torch
import torchvision.transforms as transforms

# ==========================================================================================
# ============================= THIS FILE IS FOR IMG2JSON ==================================
# ==========================================================================================

img1 = Image.open("photo/cm14/round1/detail/race1/Screenshot 2026-06-05 173640.png") # uma detail img
img2_1 = Image.open("photo/cm14/round1/mood/Screenshot 2026-06-05 173504.png") # mood img (not scrolled)
img2_2 = Image.open("photo/cm14/round1/mood/Screenshot 2026-06-05 173513.png") # mood img (scrolled)
img3_1 = Image.open("photo/cm14/round1/rank/Screenshot 2026-06-05 173620.png") # rank img (not scrolled)
img3_2 = Image.open("photo/cm14/round1/rank/Screenshot 2026-06-05 173635.png") # rank img (scrolled)

# ============================== Images Pre-processing =============================

# ================================= Box Detection =================================

def find_boxes(zone, min_w=150, max_w=310, min_h=30, max_h=70):
    zone_np = np.array(zone)
    zone_gray = cv2.cvtColor(zone_np, cv2.COLOR_RGB2GRAY)
    
    kernel = np.ones((3, 3), np.uint8)
    gradient = cv2.morphologyEx(zone_gray, cv2.MORPH_GRADIENT, kernel)
    _, binary = cv2.threshold(gradient, 20, 255, cv2.THRESH_BINARY)
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours: 
        x, y, w, h = cv2.boundingRect(c)
        
        if min_w <= w <= max_w and min_h <= h <= max_h:
            boxes.append((x, y, w, h))

    boxes.sort(key=lambda b: (b[1], b[0]))
    
    return boxes

# =============================== Size/Padding Processing ===============================

def padding_img(image, target_height=48, max_width=460):
    img = image.convert('L')

    w, h = img.size
    new_w = int(w * (target_height / h))
    if new_w > max_width - 5:
        final_w = max_width - 5
    else:
        final_w = new_w
    img = img.resize((final_w, target_height), Image.Resampling.LANCZOS)
    padded_img = Image.new('L', (max_width, target_height), color=255)
    padded_img.paste(img, (5, 0))
    padded_img.save("padding_test.png")

    return padded_img

# ================================ Regex/Number Extractor ================================

def extract_number(text):
    match = re.search(r"/d+", text)
    if match:
        return int(match.group())
    return None

# ============================ Image 1 pre-processing ============================

def process_detail(img1):
    img1_np = np.array(img1)
    hsv1 = cv2.cvtColor(img1_np, cv2.COLOR_RGB2HSV)
    lower_green1 = np.array([40, 100, 100])
    upper_green1 = np.array([80, 255, 255])

    mask1 = cv2.inRange(hsv1, lower_green1, upper_green1)
    contours1, _ = cv2.findContours(mask1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours1:
        topmost1 = min(contours1, key=lambda c: cv2.boundingRect(c)[1])
        x1, y1, w1, h1 = cv2.boundingRect(topmost1)
    if not contours1:
        print(f"Warning")
    ui_top1 = y1
    ui_crop1 = img1.crop((x1, ui_top1, x1 + w1, ui_top1 + 925))
    #ui_crop1.save("z_test.png")

    # ================================ Uma Detail / UI Button ================================

    button_zone = ui_crop1.crop((203, 420, 425, 480))
    button_np = np.array(button_zone)
    hsv = cv2.cvtColor(button_np, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, lower_green1, upper_green1)
    is_opponent = np.sum(mask) > 20000

    result_detail = {
        "name": None,
        "distance": {},
        "track": {},
        "style": {},
        "stats": {},
        "skills": [],
        "mood": None,
        "skill_level": None,
        "unique_skill": None,
        "trainer": None
    }

    stats_zone = ui_crop1.crop((10, 250, 580, 300))
    aptitude_zone = ui_crop1.crop((133, 310, 567, 410))

    if is_opponent:
        name_zone = ui_crop1.crop((295, 75, 570, 115))
        skills_zone = ui_crop1.crop((0, 570, 580, 905))
        result_detail["trainer"] = "opponent"

    else:
        name_zone = ui_crop1.crop((285, 50, 525, 100))
        skills_zone = ui_crop1.crop((0, 470, 580, 925))
        result_detail["trainer"] = "Ellen Joe"

    name = ocr_with_fuzzy(name_zone, model, val_transform, idx_to_char, device, characters)
    result_detail["name"] = name

    # ==================== Stats ====================
    stat_labels = ["speed", "stamina", "power", "guts", "wit"]
    for k, label in enumerate(stat_labels):
        h = 115 + (k * 115)
        offset = k * 115
        stat = stats_zone.crop((40 + offset, 0, h, 40))
        stats_text = ocr_predict(stat, model, val_transform, idx_to_char, device)
        result_detail["stats"][label] = stats_text

    # ==================== Skills ====================
    skills = find_boxes(skills_zone)
    for i, (x, y, w, h) in enumerate(skills):
        skill = skills_zone.crop((x + 35, y, x + w, y + h))
        skill_text = ocr_with_fuzzy(skill, model, val_transform, idx_to_char, device, skill_names)
        result_detail["skills"].append({"name": skill_text})
        #skill.save(f"skill_{i + 1}.png")

    # ===================== Level =====================
    unique_skill = skills[0]
    x, y, w, h = unique_skill
    uni_skill = skills_zone.crop((x + 35, y, x + w - 48, y + h))
    level = skills_zone.crop((x + 220, y, x + w, y + h))
    level_text = ocr_predict(level, model, val_transform, idx_to_char, device)
    level_num = extract_number(level_text)
    result_detail["skill_level"] = level_num
    
    # ==================== Aptitude ====================
    aptitude_labels = ["turf", "dirt", "sprint", "mile", "medium", "long", "front_runner", "pace_chaser", "late_surger", "end_closer"]

    aptitude_map = {
        "sprint": "distance", "mile": "distance", "medium": "distance", "long": "distance",
        "turf": "track", "dirt": "track",
        "front_runner": "style", "pace_chaser": "style", "late_surger": "style", "end_closer": "style"
    }

    aptitude = find_boxes(aptitude_zone, 83, 123, 20, 40)
    for label, (x, y, w, h) in zip(aptitude_labels, aptitude):
        category = aptitude_map[label]
        aptitude_crop = aptitude_zone.crop((x + 70, y, x + w, y + h))
        #aptitude_crop.save(f"aptitude_{j + 1}.png")
        aptitude_text = ocr_predict(aptitude_crop, model, val_transform, idx_to_char, device)
        result_detail[category][label] = aptitude_text

    return result_detail

# ================================ Mood pre-processing ================================

# =================================== Mood, Part 1 ===================================

def process_mood1(img2_1):
    img3_np = np.array(img2_1)
    gray3 = cv2.cvtColor(img3_np, cv2.COLOR_RGB2GRAY)
    edges3 = cv2.Canny(gray3, 30, 80)
    contours3, _ = cv2.findContours(edges3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for c in contours3:
        x, y, w, h = cv2.boundingRect(c)
        if w > 500 and h > 100:
            rectangles.append((x, y, w, h))
    if not rectangles:
        print("Warning")
        return {}

    topmost_rect = min(rectangles, key=lambda r: r[1])
    rx1, ry1, rw1, rh1 = topmost_rect
    print(rw1)
    mood_crop1 = img2_1.crop((rx1 + 5, ry1, rx1 + rw1 + 5, ry1 + 717))
    #mood_crop1.save("mood_test1.png")

    result_mood1 = []

    for i in range(6):
        y = 0 + (i * 120)
        rows = mood_crop1.crop((0, y, 561, y + 105))
        boxes = find_boxes(rows, 45, 110, 25, 45)
        boxes = boxes[:1]
        #rows.save(f"zmood_{i+1}.png")
        
        for box_idx, (x, y2, w, h) in enumerate(boxes):
            mood = rows.crop((x, y2, x + w, y2 + h))
            mood_text = ocr_with_fuzzy(mood, model, val_transform, idx_to_char, device, mood_list)

            t_name_img = rows.crop((x - 200, y2 + 35, x + w - 170, y2 + h + 30))
            t_name_text = ocr_predict(t_name_img, model, val_transform, idx_to_char, device)

            number_img = rows.crop((x + 105, y2, x + w + 100, y2 + h))
            number_text = ocr_predict(number_img, model, val_transform, idx_to_char, device)
            number = extract_number(number_text)

            name = rows.crop((x - 200, y2, x + w - 125, y2 + h))
            name_text = ocr_with_fuzzy(name, model, val_transform, idx_to_char, device, char_names_outer)
            
            result_mood1.append({
                "name" : name_text,
                "mood" : mood_text,
                "number" : number,
                "trainer" : t_name_text
            })

    return result_mood1

# =================================== Mood, Part 2 ===================================

def process_mood2(img2_2):
    img3_2_np = np.array(img2_2)
    gray3_2 = cv2.cvtColor(img3_2_np, cv2.COLOR_RGB2GRAY)
    edges3_2 = cv2.Canny(gray3_2, 30, 80)
    contours3_2, _ = cv2.findContours(edges3_2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for c in contours3_2:
        x, y, w, h = cv2.boundingRect(c)
        if w > 553 and h > 108:
            rectangles.append((x, y, w, h))
    if not rectangles:
        print("Warning")
        return {}

    botmost_rect = max(rectangles, key=lambda r: r[1])
    rx2, ry2, rw2, rh2 = botmost_rect
    mood_crop2 = img2_2.crop((rx2, ry2 - 575, rx2 + rw2, rh2 + ry2))
    mood_crop2.save("mood_test2.png")

    result_mood2 = []

    mood_coords = {
        7 : (0, 340, 561, 440),
        8 : (0, 460, 561, 560),
        9 : (0, 580, 561, 680)
    }
        
    for row_num, coords in mood_coords.items():
        rows = mood_crop2.crop(coords)
        boxes = find_boxes(rows, 45, 103, 25, 45)

        for x, y, w, h in boxes:
            mood = rows.crop((x + 33, y, x + w, y + h - 5))
            mood_text = ocr_with_fuzzy(mood, model, val_transform, idx_to_char, device, mood_list)

            t_name = rows.crop((x - 200, y + 35, x + w - 170, y + h + 30))
            t_name_text = ocr_predict(t_name, model, val_transform, idx_to_char, device)

            number_img = rows.crop((x + 110, y + 5, x + w + 105, y + h - 5))
            number_text = ocr_predict(number_img, model, val_transform, idx_to_char, device)
            number = extract_number(number_text)

            name = rows.crop((x - 200, y, x + w - 125, y + h))
            name_text = ocr_with_fuzzy(name, model, val_transform, idx_to_char, device, char_names_outer)

            result_mood2.append({
                "name" : name_text,
                "mood" : mood_text,
                "number" : number,
                "trainer" : t_name_text
            })
            
    return result_mood2

# =================================== Rank Image ===================================

def process_img3(img3_2, start_num=1):

    img2_np = np.array(img3_2)
    hsv2 = cv2.cvtColor(img2_np, cv2.COLOR_RGB2HSV)
    lower_green2 = np.array([40, 100, 100])
    upper_green2 = np.array([80, 255, 255])

    mask2 = cv2.inRange(hsv2, lower_green2, upper_green2)
    contours2, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours2:
        topmost2 = min(contours2, key=lambda c: cv2.boundingRect(c)[1])
        x2, y2, w2, h2 = cv2.boundingRect(topmost2)
    else:
        print(f"Warning: green header not found")
        return {}
        
    rank_top = y2
    rank_crop = img3_2.crop((x2, rank_top, x2 + w2 - 15, rank_top + 925))
    #rank_crop.save("rank.png")

    result_rank = []

    boxes = find_boxes(rank_crop, 160, 200, 45, 65)

    for i, (x, y, w, h) in enumerate(boxes):
        rank_num = start_num + i

        number_img = rank_crop.crop((x + 215, y + 55, x + w + 120, y + h + 34))
        number_text = ocr_predict(number_img, model, val_transform, idx_to_char, device)
        number = extract_number(number_text)

        r_uma = rank_crop.crop((x, y + 25, x + w, y + h))
        r_uma_text = ocr_with_fuzzy(r_uma, model, val_transform, idx_to_char, device, char_names_outer)

        t_name = rank_crop.crop((x, y + 60, x + w - 80, y + h + 35))
        t_name_text = ocr_predict(t_name, model, val_transform, idx_to_char, device)
        
        result_rank.append({
            "name" : r_uma_text,
            "trainer" : t_name_text,
            "number" : number,
            "rank" : rank_num
        })
        
    return result_rank

# ===================================== Matching Data (detail) =====================================
def matching_detail(all_detail_result):
    uma_detail = []
    processed = set()

    for i in range(len(all_detail_result)):
        if i in processed:
            continue

        current = all_detail_result[i]
        for j in range(i + 1, len(all_detail_result)):
            if j in processed:
                continue

            new = all_detail_result[j]
            if (current["name"] == new["name"]
                and current["stats"]["speed"] == new["stats"]["speed"]
                and current["stats"]["stamina"] == new["stats"]["stamina"]):

                current_skill = {s["name"] for s in current["skills"]}

                for skill in new["skills"]:
                    if skill["name"] not in current_skill:
                        current_skill.add(skill["name"])
                        current["skills"].append(skill)

                processed.add(j)

        uma_detail.append(current)
        processed.add(i)

    return uma_detail

# =================================== Matching Data (Rank & Mood) ===================================

def matching_r_m(result_ranks, result_moods):
    r_m_result = []
    mood_processed = set()

    for r in result_ranks:
        match = next((m for m in result_moods if m["number"] == r["number"]), None)
        r["mood"] = match["mood"] if match else None
        if match:
            mood_processed.add(match["number"])
        r_m_result.append(r)

    for m in result_moods:
        if m["number"] not in mood_processed:
            rank_9 = {
                "name" : m["name"],
                "trainer" : m["trainer"],
                "number" : m["number"],
                "rank" : 9,
                "mood" : m["mood"]
            }
            r_m_result.append(rank_9)

    return r_m_result

# ================================== Matching Data (detail, Mood & Rank) ==================================

def matching_d_r_m(uma_detail, r_m_result):
    final_match = []
    
    for detail in uma_detail:
        trainer_detail = detail["trainer"]

        if trainer_detail == "Ellen Joe":
            match = next((rm for rm in r_m_result if rm["trainer"] == detail["trainer"] and rm["name"] == detail["name"]), None)

        else:
            candidate = [rm for rm in r_m_result if rm["name"] == detail["name"]]
            match = candidate[0] if candidate else None

        if match:
            detail["rank"] = match["rank"]
            detail["mood"] = match["mood"]
            r_m_result.remove(match)

        final_match.append(detail)

    return final_match

# ================================ Debugging ================================

# ================================ Load All Uma Detail ================================

all_detail_result = []
for detail_path in detail_photos:  # detail_photos = all images in race folder, variable name can be change
    img = Image.open(detail_path)
    result = process_detail(img)
    all_detail_result.append(result)

process_detail(img1)
#for test in ep:
#    text = ocr_predict(test, model, val_transform, idx_to_char, device)
#    print(text)

#merger mood1 and mood2
result_moods = process_mood1(img2_1) + process_mood2(img2_2)

#merger rank
result_ranks = process_img3(img3_1, start_num=1) + process_img3(img3_2, start_num=5)