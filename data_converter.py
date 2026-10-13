from PIL import Image
import cv2
import numpy as np
import json
import re
from converter import ocr_predict, ocr_with_fuzzy, model, val_transform, idx_to_char, device, skill_names, char_names_outer, char_names_full, mood_list, style_list
from pathlib import Path
import os
from rapidfuzz import fuzz

# ==========================================================================================
# ============================= THIS FILE IS FOR IMG2JSON ==================================
# ==========================================================================================

# ============================== Images Pre-processing =============================

# ================================= Box Detection =================================

def find_boxes(zone, min_w=150, max_w=310, min_h=30, max_h=70, kernel_size=3):
    zone_np = np.array(zone)
    zone_gray = cv2.cvtColor(zone_np, cv2.COLOR_RGB2GRAY)
    
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
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

    return padded_img

# ================================ Regex/Number Extractor ================================

def extract_number(text):
    match = re.search(r"\d+", text)
    if match:
        return int(match.group())
    return None
# ================================ Trainer Name Validation ================================

my_trainer = ["Ellen Joe"]

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

    name = ocr_with_fuzzy(name_zone, model, val_transform, idx_to_char, device, char_names_full, threshold=70)
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

    # ===================== Level =====================
    unique_skill = skills[0]
    x, y, w, h = unique_skill
    level = skills_zone.crop((x + 220, y, x + w, y + h))
    level_text = ocr_predict(level, model, val_transform, idx_to_char, device)
    level_num = extract_number(level_text)

    if level_num is not None:
        result_detail["skill_level"] = level_num
        result_detail["unique_skill"] = result_detail["skills"][0]["name"]
    else:
        result_detail["skill_level"] = None
        result_detail["unique_skill"] = None

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
        aptitude_text = ocr_predict(aptitude_crop, model, val_transform, idx_to_char, device)
        result_detail[category][label] = aptitude_text

    return result_detail

# ===================================== Mood, Part 1 =====================================

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
        print("Warning no rectangle found")
        return {}

    topmost_rect = min(rectangles, key=lambda r: r[1])
    rx1, ry1, rw1, rh1 = topmost_rect
    mood_crop1 = img2_1.crop((rx1 + 5, ry1, rx1 + rw1 + 5, ry1 + 717))

    result_mood1 = []

    for i in range(6):
        y = 0 + (i * 120)
        rows = mood_crop1.crop((0, y, 561, y + 105))
        boxes = find_boxes(rows, 45, 110, 25, 54)
        boxes = boxes[:1]
        
        for box_idx, (x, y2, w, h) in enumerate(boxes):
            mood = rows.crop((x + 30, y2, x + w, y2 + h))
            mood_text = ocr_with_fuzzy(mood, model, val_transform, idx_to_char, device, mood_list, threshold=70)

            t_name_img = rows.crop((x - 200, y2 + 35, x + w - 170, y2 + h + 30))
            t_name_text = ocr_with_fuzzy(t_name_img, model, val_transform, idx_to_char, device, my_trainer)

            number_img = rows.crop((x + 137, y2 + 8, x + w + 68, y2 + h))
            number_text = ocr_predict(number_img, model, val_transform, idx_to_char, device, allowed_chars=set("0123456789"))
            number = extract_number(number_text)

            style = rows.crop((x + 108, y2 + 35, x + w + 100, y2 + h + 23))
            style_text = ocr_with_fuzzy(style, model, val_transform, idx_to_char, device, style_list)
            style_normal = normalize_style_name(style_text)

            name = rows.crop((x - 200, y2, x + w - 125, y2 + h))
            name_text = ocr_with_fuzzy(name, model, val_transform, idx_to_char, device, char_names_outer, threshold=75, score_choice=fuzz.token_set_ratio)
            
            result_mood1.append({
                "name" : name_text,
                "mood" : mood_text,
                "number" : number,
                "trainer" : t_name_text,
                "main_style" : style_normal
            })
    print(result_mood1)
    print("--" * 50)
    return result_mood1

# =================================== Mood, Part 2 ===================================

def process_mood2(img2_2):
    img3_2_np = np.array(img2_2)
    gray3_2 = cv2.cvtColor(img3_2_np, cv2.COLOR_RGB2GRAY)
    _, thresh3_2 = cv2.threshold(gray3_2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (80, 2))
    morph_closed = cv2.morphologyEx(thresh3_2, cv2.MORPH_CLOSE, kernel_horizontal)

    contours3_2, _ = cv2.findContours(morph_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for c in contours3_2:
        x, y, w, h = cv2.boundingRect(c)
        if w > 553 and h > 108:
            rectangles.append((x, y, w, h))
    if not rectangles:
        print("Warning no rectangle found")
        return {}
    
    botmost_rect = max(rectangles, key=lambda r: r[1])
    rx2, ry2, rw2, rh2 = botmost_rect
    mood_crop2 = img2_2.crop((rx2, ry2 - 575, rx2 + rw2, rh2 + ry2))

    result_mood2 = []

    mood_coords = {
        7 : (0, 340, 561, 440),
        8 : (0, 460, 561, 560),
        9 : (0, 580, 561, 680)
    }
        
    for row_num, coords in mood_coords.items():
        rows = mood_crop2.crop(coords)
        boxes = find_boxes(rows, 45, 103, 25, 56)

        for x, y, w, h in boxes:
            mood = rows.crop((x + 33, y, x + w, y + h - 5))
            mood_text = ocr_with_fuzzy(mood, model, val_transform, idx_to_char, device, mood_list, threshold=70)

            t_name = rows.crop((x - 200, y + 35, x + w - 170, y + h + 30))
            t_name_text = ocr_with_fuzzy(t_name, model, val_transform, idx_to_char, device, my_trainer)

            number_img = rows.crop((x + 137, y + 8, x + w + 68, y + h - 5))
            number_text = ocr_predict(number_img, model, val_transform, idx_to_char, device, allowed_chars=set("0123456789"))
            number = extract_number(number_text)

            style = rows.crop((x + 110, y + 37, x + w + 105, y + h + 24))
            style_text = ocr_with_fuzzy(style, model, val_transform, idx_to_char, device, style_list)
            style_normal = normalize_style_name(style_text)

            name = rows.crop((x - 200, y, x + w - 125, y + h))
            name_text = ocr_with_fuzzy(name, model, val_transform, idx_to_char, device, char_names_outer, threshold=75, score_choice=fuzz.token_set_ratio)

            result_mood2.append({
                "name" : name_text,
                "mood" : mood_text,
                "number" : number,
                "trainer" : t_name_text,
                "main_style" : style_normal
            })
    print(result_mood2)
    return result_mood2

# ===================================== Rank Image =====================================

def process_rank(img3_1, start_num=1):

    img3_np = np.array(img3_1)
    hsv2 = cv2.cvtColor(img3_np, cv2.COLOR_RGB2HSV)
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
    rank_crop = img3_1.crop((x2, rank_top, x2 + w2 - 15, rank_top + 925))

    result_rank = []

    boxes = find_boxes(rank_crop, 160, 200, 45, 67, kernel_size=5)

    for i, (x, y, w, h) in enumerate(boxes):
        rank_num = start_num + i

        number_img = rank_crop.crop((x + 250, y + 55, x + w + 87, y + h + 34))
        number_text = ocr_predict(number_img, model, val_transform, idx_to_char, device, allowed_chars=set("0123456789"))
        number = extract_number(number_text)

        r_uma = rank_crop.crop((x, y + 25, x + w, y + h))
        r_uma_text = ocr_with_fuzzy(r_uma, model, val_transform, idx_to_char, device, char_names_outer, threshold=75, score_choice=fuzz.token_set_ratio)

        t_name = rank_crop.crop((x, y + 60, x + w - 80, y + h + 35))
        t_name_text = ocr_with_fuzzy(t_name, model, val_transform, idx_to_char, device, my_trainer)
        
        result_rank.append({
            "name" : r_uma_text,
            "trainer" : t_name_text,
            "number" : number,
            "rank" : rank_num
        })
    #print("--"*50)
    #print(result_rank)
    #print("--"*50)
    return result_rank

# ===================================== Style Name Normalization =====================================

def normalize_style_name(style_text):
    style_map = {
        "Front" : "front_runner",
        "Pace" : "pace_chaser",
        "Late" : "late_surger",
        "End" : "end_closer"
    }
    return style_map.get(style_text, "unknown")

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

            candidate = all_detail_result[j]
            if (current["name"] == candidate["name"]
                and current["stats"]["speed"] == candidate["stats"]["speed"]
                and current["stats"]["stamina"] == candidate["stats"]["stamina"]):

                current_skill = {s["name"] for s in current["skills"]}

                for skill in candidate["skills"]:
                    if skill["name"] not in current_skill:
                        current_skill.add(skill["name"])
                        current["skills"].append(skill)

                if current["skill_level"] is None and candidate["skill_level"] is not None:
                    current["skill_level"] = candidate["skill_level"]

                if current["unique_skill"] is None and candidate["unique_skill"] is not None:
                    current["unique_skill"] = candidate["unique_skill"]

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
        r["main_style"] = match["main_style"] if match else None
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
                "mood" : m["mood"],
                "main_style" : m["main_style"]
            }
            r_m_result.append(rank_9)
            
    print("--"*50)
    print(r_m_result)
    return r_m_result

# ======================================== Shorting name ========================================

# Example : Mayano Top Gun (Scramble☆Zone) --> Mayano Top Gun

def shorting_name(full_name):
    return full_name.split("(")[0].strip()

# ================================== Matching Data (detail, Mood & Rank) ==================================

def matching_d_r_m(uma_detail, r_m_result):
    final_match = []
    #print("--"*50)
    #print("\nRM    :", [(rm["name"], rm["rank"]) for rm in r_m_result])
    #print("\nDETAIL:", [d["name"] for d in uma_detail])

    for detail in uma_detail:
        short_name = shorting_name(detail["name"])
        trainer_detail = detail["trainer"]

        if trainer_detail == "Ellen Joe":
            match = next((rm for rm in r_m_result if rm["trainer"] == detail["trainer"] and rm["name"] == short_name), None)

        else:
            candidate = [rm for rm in r_m_result if rm["name"] == short_name]
            match = candidate[0] if candidate else None

        if match:
            detail["rank"] = match["rank"]
            detail["mood"] = match["mood"]
            detail["main_style"] = match["main_style"]
            r_m_result.remove(match)
        else:
            print(f"NO MATCH: {short_name!r} | available: {[rm['name'] for rm in r_m_result]}")

        final_match.append(detail)

    return final_match

# ================================== Add CM, Round, Race (number) ==================================

def add_race_info(final_match, cm, round_name, race_name):
    for uma in final_match:
        uma["cm_id"] = extract_number(cm)          
        uma["round"] = extract_number(round_name)  
        uma["race_no"] = extract_number(race_name) 
    return final_match

# ===============================================================================================
# ============================================= Main ============================================
# ===============================================================================================

cm_rounds = {
    "cm14" : ["round1", "round2"]
}

for cm, rounds in cm_rounds.items():
    for round_name in rounds:
        print(f"\n=== Processing {cm} {round_name} ===")
        race_dirs = sorted(Path(f"photo/{cm}/{round_name}/detail").glob("race*"), key=lambda p: extract_number(p.name))
        mood_photos = sorted(Path(f"photo/{cm}/{round_name}/mood").glob("*.png"))
        rank_photos = sorted(Path(f"photo/{cm}/{round_name}/rank").glob("*.png"))

        for race_idx, race_dir in enumerate(race_dirs):
            race_name = race_dir.name
            race_prefix = f"{cm}_{round_name}_{race_name}"
            print(f"\n--- race {race_idx+1}/{len(race_dirs)}: {race_name} ---")
            detail_photos = sorted(race_dir.glob("*.png"))
            mood_pair = mood_photos[race_idx * 2 : race_idx * 2 + 2]
            rank_pair = rank_photos[race_idx * 2 : race_idx * 2 + 2]

            img2_1 = Image.open(mood_pair[0])
            img2_2 = Image.open(mood_pair[1])
            img3_1 = Image.open(rank_pair[0])
            img3_2 = Image.open(rank_pair[1])

            r1 = process_rank(img3_1, start_num=1)
            r2 = process_rank(img3_2, start_num=5)
            m1 = process_mood1(img2_1)
            m2 = process_mood2(img2_2)

            result_moods = m1 + m2
            result_ranks = r1 + r2
            r_m_result = matching_r_m(result_ranks, result_moods)
            
            print("rank:", len(r1), len(r2), "| mood:", len(m1), len(m2))

            all_detail_result = []
            for i, detail_path in enumerate(detail_photos):
                img1 = Image.open(detail_path)
                result1 = process_detail(img1)
                all_detail_result.append(result1)

            uma_detail = matching_detail(all_detail_result)

            final_match = matching_d_r_m(uma_detail, r_m_result)
            final_match = add_race_info(final_match, cm, round_name, race_name)

            if len(final_match) != 9:
                print(f"WARNING {race_prefix}: {len(final_match)} uma (supposed to be 9)")
                
            for u in final_match:
                if "rank" not in u:
                    print(f"WARNING {race_prefix}: {u['name']} rank not found")
                if u.get("mood") is None:
                    print(f"WARNING {race_prefix}: {u['name']} mood not found")

# ================================== List to JSON ==================================

            folder_output = f"data/raw/input/{cm}_input"
            os.makedirs(folder_output, exist_ok=True)

            for idx, uma in enumerate(final_match):
                uma.pop("number", None)
                uma.pop("trainer", None)

                name_uma_file = uma["name"].split("(")[0].strip()
                file_name = f"{folder_output}/{name_uma_file}_{race_prefix}_{idx}.json"

                with open(file_name, "w", encoding="utf-8") as f:
                    json.dump(uma, f, indent=2, ensure_ascii=False)