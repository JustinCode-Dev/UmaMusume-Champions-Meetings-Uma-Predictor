from PIL import Image
import pytesseract
import cv2
import numpy as np
from rapidfuzz import process
import json
import re
import pandas as pd
from pathlib import Path

pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

with open("data/raw/character.json", "r", encoding="utf-8") as f:
    characters = json.load(f)

with open("data/raw/skills.json", "r", encoding="utf-8") as f:
    skills_data = json.load(f)

skill_names = [s["name"] for s in skills_data]
char_names = [c["name"] for c in characters]

# ================================================================================
# ================================ Box Detection =================================
# ================================================================================

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

# ================================================================================
# ============================ Preprocessing Function ============================
# ================================================================================

def ocr_zone(zone, thresh_val=120, psm=7, whitelist=None):
    zone = zone.resize((zone.width * 2, zone.height * 2))
    zone_np = np.array(zone)
    zone_gray = cv2.cvtColor(zone_np, cv2.COLOR_RGB2GRAY)
    _, zone_thresh = cv2.threshold(zone_gray, thresh_val, 255, cv2.THRESH_BINARY)
    zone_processed = Image.fromarray(zone_thresh)
    
    config = f'--psm {psm}'
    if whitelist:
        config += f' -c tessedit_char_whitelist={whitelist}'

    return pytesseract.image_to_string(zone_processed, config=config)

def ocr_zone_adaptive(zone, psm=10, whitelist=None, max_wh_ratio=None):
    zone = zone.resize((zone.width * 3, zone.height * 3))
    zone_np = np.array(zone)
    zone_gray = cv2.cvtColor(zone_np, cv2.COLOR_RGB2GRAY)
    zone_processed_np = cv2.adaptiveThreshold(
    zone_gray, 
    255, 
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
    cv2.THRESH_BINARY, 
    11,
    1
    )
    padded_np = cv2.copyMakeBorder(
        zone_processed_np, 10, 10, 10, 10, 
        cv2.BORDER_CONSTANT, 
        value=[255, 255, 255]
    )
    zone_processed = Image.fromarray(padded_np)
    
    config = f'--psm {psm}'
    if whitelist:
        config += f' -c tessedit_char_whitelist={whitelist}'
    if max_wh_ratio:
        config += f' -c tessedit_max_char_wh_ratio={max_wh_ratio}'

    return pytesseract.image_to_string(zone_processed, config=config)

def preprocess_zone(zone):
    zone = zone.resize((zone.width * 2, zone.height * 2))
    zone_np = np.array(zone)
    zone_gray = cv2.cvtColor(zone_np, cv2.COLOR_RGB2GRAY)

    return Image.fromarray(zone_gray)


# =====================================================================================
# ====================================== Image 1 ======================================
# =====================================================================================


def process_img1(img1, prefix, rows, photo_idx=0):

    # ============== Image 1 pre-processing ==============

    img1_np = np.array(img1)
    hsv1 = cv2.cvtColor(img1_np, cv2.COLOR_RGB2HSV)
    lower_green1 = np.array([40, 100, 100])
    upper_green1 = np.array([80, 255, 255])

    mask1 = cv2.inRange(hsv1, lower_green1, upper_green1)
    contours1, _ = cv2.findContours(mask1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours1:
        topmost1 = min(contours1, key=lambda c: cv2.boundingRect(c)[1])
        x1, y1, w1, h1 = cv2.boundingRect(topmost1)
        #print(f"Header: x={x}, y={y}, w={w}, h={h}")
    if not contours1:
        print(f"Warning: green header not found on {prefix}")
        return {}

    ui_top1 = y1
    ui_crop1 = img1.crop((x1, ui_top1, x1 + w1, ui_top1 + 925))
    #ui_crop1.save("test.png")

    # ================== UI Button ==================

    button_zone = ui_crop1.crop((203, 420, 425, 480))
    button_np = np.array(button_zone)
    hsv = cv2.cvtColor(button_np, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, lower_green1, upper_green1)
    #print("Green pixels:", np.sum(mask))
    is_opponent = np.sum(mask) > 20000

    result = {
        "name" : None,
        "aptitude" : [],
        "stats" : [],
        "skills" : []
    }

    stats_zone = ui_crop1.crop((10, 250, 580, 300))
    aptitude_zone = ui_crop1.crop((133, 310, 567, 410))

    if is_opponent:
        name_zone = ui_crop1.crop((295, 75, 570, 115))
        skills_zone = ui_crop1.crop((0, 570, 580, 905))

    else:
        name_zone = ui_crop1.crop((285, 50, 525, 100))
        skills_zone = ui_crop1.crop((0, 470, 580, 925))

    result["name"] = name_zone

    # ==================== Stats ====================
    for k in range(5):
        h = 115 + (k * 115)
        offset = k * 115
        stats = stats_zone.crop((40 + offset, 0, h, 100))
        result["stats"].append(stats)

    # ==================== Skills ====================
    skills = find_boxes(skills_zone)
    for i, (x, y, w, h) in enumerate(skills):
        skill = skills_zone.crop((x + 35, y, x + w, y + h))
        result["skills"].append(skill)
        skill.save(f"skill_{i + 1}.png")

    # ==================== Aptitude ====================
    aptitude = find_boxes(aptitude_zone, 83, 123, 20, 40)
    for j, (x, y, w, h) in enumerate(aptitude):
         aptitude_crop = aptitude_zone.crop((x + 70, y, x + w, y + h))
         #aptitude_crop.save(f"aptitude_{j + 1}.png")
         result["aptitude"].append(aptitude_crop)

    # =============== Ranks Validation ===============

    #valid_ranks = ["S", "A", "B", "C", "D", "E", "F", "G"]

    return result


# =====================================================================================
# ====================================== Image 2 ======================================
# =====================================================================================


def process_img2(img2, race_prefix, rows):

    # ======================= Image 2 pre-processing =======================

    img2_np = np.array(img2)
    hsv2 = cv2.cvtColor(img2_np, cv2.COLOR_RGB2HSV)
    lower_green2 = np.array([40, 100, 100])
    upper_green2 = np.array([80, 255, 255])

    mask2 = cv2.inRange(hsv2, lower_green2, upper_green2)
    contours2, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours2:
        topmost2 = min(contours2, key=lambda c: cv2.boundingRect(c)[1])
        x2, y2, w2, h2 = cv2.boundingRect(topmost2)
    else:
        print(f"Warning: green header not found on {race_prefix}")
        return {}
        
    placing_top = y2
    placing_crop = img2.crop((x2, placing_top, x2 + w2, placing_top + 925))
    #placing_crop.save("RankUI.png")

    # ==================== Trainers Name, Placement/Rank, Part 1 ====================

    r_tname_results1 = {}
    for i in range (4):
        y = 475 + (i * 120)
        zone = placing_crop.crop((250, y, 450, y + 40))
        text = ocr_zone(zone).strip()
        r_tname_results1[f"r_tname{i+1}"] = text
        preprocess_zone(zone).save(f"C:/uma_data/images/r_tname{i+1}_{race_prefix}.png")
        rows.append({"filename": f"images/r_tname{i+1}_{race_prefix}.png", "label": text})

    # ======================== Placement/Rank ========================

    rank = {f"rank_{i+1}": i+1 for i in range(9)}

    # ==================== Uma Name, Placement/Rank, Part 1 ====================

    r_uma_results1 = {}
    for i in range(4):
        y = 440 + (i * 120)
        zone = placing_crop.crop((250, y, 450, y + 40))
        text = ocr_zone(zone).strip()
        best_match = process.extractOne(text, char_names)
        if best_match and best_match[1] >= 60:
            matched = best_match[0].split("(")[0].strip()
        else:
            matched = "unknown"
        r_uma_results1[f"r_uma{i+1}"] = matched
        preprocess_zone(zone).save(f"C:/uma_data/images/r_uma{i+1}_{race_prefix}.png")
        rows.append({"filename": f"images/r_uma{i+1}_{race_prefix}.png", "label": matched})
    #print(r_uma_results1)

    result = {}

    result.update(rank)
    result.update(r_tname_results1)
    result.update(r_uma_results1)
    
    return result


# ============================================================================================
# ====================================== Image 2, Part2 ======================================
# ============================================================================================


def process_img2_2(img2_2, race_prefix, rows):

    img2_np = np.array(img2_2)
    hsv2 = cv2.cvtColor(img2_np, cv2.COLOR_RGB2HSV)
    lower_green2 = np.array([40, 100, 100])
    upper_green2 = np.array([80, 255, 255])

    mask2 = cv2.inRange(hsv2, lower_green2, upper_green2)
    contours2, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours2:
        topmost2 = min(contours2, key=lambda c: cv2.boundingRect(c)[1])
        x2, y2, w2, h2 = cv2.boundingRect(topmost2)
    else:
        print(f"Warning: green header not found on {race_prefix}")
        return {}
        
    placing_top = y2
    placing_crop = img2_2.crop((x2, placing_top, x2 + w2, placing_top + 925))

    # ==================== Trainers Name, Placement/Rank, Part 2 ====================
    
    r_tname_results2 = {}
    for i in range(4):
        y = 460 + (i * 120)
        zone = placing_crop.crop((230, y, 450, y + 40))
        text = ocr_zone(zone).strip()
        r_tname_results2[f"r_tname{i+5}"] = text
        preprocess_zone(zone).save(f"C:/uma_data/images/r_tname{i+5}_{race_prefix}.png")
        rows.append({"filename": f"images/r_tname{i+5}_{race_prefix}.png", "label": text})

    # ==================== Uma Name, Placement/Rank, Part 2 ====================

    r_uma_results2 = {}
    for i in range(4):
        y = 430 + (i * 120)
        zone = placing_crop.crop((250, y, 465, y + 40))
        text = ocr_zone(zone).strip()
        best_match = process.extractOne(text, char_names)
        if best_match and best_match[1] >= 60:
            matched = best_match[0].split("(")[0].strip()
        else:
            matched = "unknown"
        r_uma_results2[f"r_uma{i+5}"] = matched
        preprocess_zone(zone).save(f"C:/uma_data/images/r_uma{i+5}_{race_prefix}.png")
        rows.append({"filename": f"images/r_uma{i+5}_{race_prefix}.png", "label": matched})
        
    result = {}
    result.update(r_tname_results2)
    result.update(r_uma_results2)
        

# =============================================================================================
# ========================================== Image 3 ==========================================
# =============================================================================================


def process_img3(img3, race_prefix, rows):

    # ================================ Image 3 pre-processing ================================

    img3_np = np.array(img3)
    
    # =============================== Image 3, Part 1 ===============================

    gray3 = cv2.cvtColor(img3_np, cv2.COLOR_RGB2GRAY)
    edges3 = cv2.Canny(gray3, 30, 80)
    contours3, _ = cv2.findContours(edges3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for c in contours3:
        x, y, w, h = cv2.boundingRect(c)
        if w > 500 and h > 100:
            rectangles.append((x, y, w, h))
    if not rectangles:
        print(f"Warning: box not found on {race_prefix}")
        return {}
    #print(f"rectangles found: {len(rectangles)}")
    #print(rectangles)

    topmost_rect = min(rectangles, key=lambda r: r[1])
    rx1, ry1, rw1, rh1 = topmost_rect

    mood_crop1 = img3.crop((rx1, ry1, rx1 + rw1, ry1 + 717))
    #mood_crop1.save("mood_test1.png")

    # ======================== Mood Validation ========================

    mood_list = ["BAD", "NORMAL", "GOOD", "GREAT"]

    # ==================== Uma Names (Mood Screen), Part 1 ====================

    result = []

    for i in range(6):
        y = 0 + (i * 120)
        rows = mood_crop1.crop((0, y, 561, y + 105))
        boxes = find_boxes(rows, 45, 110, 25, 45)
        #rows.save(f"zmood_{i+1}.png")
        
        for box_idx, (x, y2, w, h) in enumerate(boxes):
            moods = rows.crop((x, y2, x + w, y2 + h))
            names = rows.crop((x - 200, y2, x + w - 125, y2 + h))
            
            result.append({
                "name" : names,
                "mood" : moods
            })

    return result



# ======================================================================================================
# ========================================== Image 3, Part 2  ==========================================
# ======================================================================================================


def process_img3_2(img3_2, race_prefix, rows):
    # =============================== Image 3, Part 2 ===============================
    img3_2_np = np.array(img3_2)
    gray3_2 = cv2.cvtColor(img3_2_np, cv2.COLOR_RGB2GRAY)
    edges3_2 = cv2.Canny(gray3_2, 30, 80)
    contours3_2, _ = cv2.findContours(edges3_2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for c in contours3_2:
        x, y, w, h = cv2.boundingRect(c)
        if w > 553 and h > 108:
            rectangles.append((x, y, w, h))
    if not rectangles:
        print(f"Warning: box not found on {race_prefix}")
        return {}
    #print(f"rectangles found: {len(rectangles)}")
    #print(rectangles)

    botmost_rect = max(rectangles, key=lambda r: r[1])
    rx2, ry2, rw2, rh2 = botmost_rect
    #print(f"Header: x={rx2}, y={ry2}, w={rw2}, h={rh2}")
    mood_crop2 = img3_2.crop((rx2, ry2 - 575, rx2 + rw2, rh2 + ry2))
    #mood_crop2.save("mood_test2.png")
    
    # ======================== Mood Validation ========================

    mood_list = ["BAD", "NORMAL", "GOOD", "GREAT"]

    # ==================== Uma Names (Mood Screen), Part 2 ====================

    result = []
    
    mood_coords = {
            1 : (0, 0, 561, 90),
            2 : (0, 100, 561, 200),
            3 : (0, 220, 561, 320),
            4 : (0, 340, 561, 440),
            5 : (0, 460, 561, 560),
            6 : (0, 580, 561, 680)
        }
            
    for row_num, coords in mood_coords.items():
        rows = mood_crop2.crop(coords)
        boxes = find_boxes(rows, 45, 103, 25, 45)

        for x, y, w, h in boxes:
            moods = rows.crop((x, y, x + w, y + h))
            names = rows.crop((x - 200, y, x + w - 125, y + h))

            result.append({
                "name" : names,
                "mood" : moods
            })
                
    return result

# ==========================================================================================
# ========================================== Main ==========================================
# ==========================================================================================

#rows = []
#rounds = ["round1", "round2"]

#for round_name in rounds:
#    race_dirs = sorted(Path(f"photo/cm14/{round_name}/detail").glob("race*"))
#    mood_photos = sorted(Path(f"photo/cm14/{round_name}/mood").glob("*.png"))
#    rank_photos = sorted(Path(f"photo/cm14/{round_name}/rank").glob("*.png"))
#
#    for race_idx, race_dir in enumerate(race_dirs):
#        race_name = race_dir.name
#        detail_photos = sorted(race_dir.glob("*.png"))
#        mood_pair = mood_photos[race_idx * 2 : race_idx * 2 + 2]
#        rank_pair = rank_photos[race_idx * 2 : race_idx * 2 + 2]
#
#        race_prefix = f"{round_name}_{race_name}"
#
#        img2 = Image.open(rank_pair[0])
#        img2_2 = Image.open(rank_pair[1])
#        img3 = Image.open(mood_pair[0])
#        img3_2 = Image.open(mood_pair[1])
#
#        result2_1 = process_img2(img2, race_prefix, rows)
#        result2_2 = process_img2_2(img2_2, race_prefix, rows)
#        result3_1 = process_img3(img3, race_prefix, rows)
#        result3_2 = process_img3_2(img3_2, race_prefix, rows)
#
#        for i, detail_path in enumerate(detail_photos):
#            prefix = f"{round_name}_{race_name}_{i}"
#            img1 = Image.open(detail_path)
#            result1 = process_img1(img1, prefix, rows, i % 2)
#
#pd.DataFrame(rows).to_csv("C:/uma_data/labels_dl.csv", index=False, encoding='utf-8-sig')