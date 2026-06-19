from PIL import Image
import pytesseract
import cv2
import numpy as np
from rapidfuzz import process
import json
import re
import os

pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

with open("data/raw/character.json", "r") as f:
    characters = json.load(f)

with open("data/raw/skills.json", "r") as f:
    skills_data = json.load(f)

skill_names = [s["name"] for s in skills_data]
char_names = [c["name"] for c in characters]

img1 = Image.open("photo/cm14/round1/detail/race1/Screenshot 2026-06-05 173640.png") # Uma Detail
img2 = Image.open("photo/cm14/round2/rank/Screenshot 2026-06-07 152321.png") # Ranks UI
img3 = Image.open("photo/cm14/round2/mood/Screenshot 2026-06-07 152253.png") # Mood UI 1
img3_2 = Image.open("photo/cm14/round1/mood/Screenshot 2026-06-05 175046.png") # mood UI 2 


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



def process_img1(img1, idx):

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

    if is_opponent:
        name_zone = ui_crop1.crop((295, 75, 570, 120))
        skills_zone = ui_crop1.crop((0, 570, 665, 905))

        skills_zones = {}
        for i in range(5):
            y = 25 + (i * 60)
            skills_zones[f"skill_{i+1}"] = skills_zone.crop((55, y, 300, y + 45))
            skills_zones[f"skill_{i+6}"] = skills_zone.crop((335, y, 540, y + 45))

    else:
        name_zone = ui_crop1.crop((285, 50, 530, 100))
        skills_zone = ui_crop1.crop((0, 470, 665, 925))

        skills_zones = {}
        for i in range(7):
            y = 15 + (i * 60)
            skills_zones[f"skill_{i+1}"] = skills_zone.crop((48, y, 300, y + 55))
            skills_zones[f"skill_{i+8}"] = skills_zone.crop((335, y, 540, y + 55))

    # =============== Ranks Validation ===============

    valid_ranks = ["S", "A", "B", "C", "D", "E", "F", "G"]

    # ================ Uma Name Processing ================

    name_text = ocr_zone(name_zone).strip()
    preprocess_zone(zone).save(f"C:/uma_data/uma_name_{idx}.png")
    name_raw = name_text.strip()
    best_match = process.extractOne(name_raw, char_names)
    #print("Match:", best_match)
    matched_name = best_match[0]
    matched_score = best_match[1]

    uma_name = matched_name if matched_score >= 70 else "unknown"

    # =============== Track Processing ===============

    turf_zone = ui_crop1.crop((198, 313, 250, 340))  
    dirt_zone = ui_crop1.crop((300, 313, 360, 340))
    #turf_zone.save("turf.png")
    #dirt_zone.save("dirt.png")

    track_zones = {
        "turf" : (turf_zone, 185),
        "dirt" : (dirt_zone, 185)
    }

    tracks = {}
    for track_name, (zone, thresh_val) in track_zones.items():
        preprocess_zone(zone).save(f"C:/uma_data/{track_name}_{idx}.png")
        raw_ocr_text = ocr_zone_adaptive(zone, whitelist="SABCDEFG", max_wh_ratio=1.2).strip()
        best_match = process.extractOne(raw_ocr_text, valid_ranks)
        if best_match and best_match[1] >= 60:
            matched_rank = best_match[0]
        else:
            matched_rank = "unknown"

        tracks[track_name] = matched_rank

    #turf_rank = tracks.get("turf", "?")
    #dirt_rank = tracks.get("dirt", "?")

    #print(f"Turf: {turf_rank} Dirt: {dirt_rank}")

    # =============== Distance Processing ===============

    distance_zone = ui_crop1.crop((125, 340, 570, 378))
    sprint_zone = distance_zone.crop ((85, 7, 110, 31))
    mile_zone = distance_zone.crop ((193, 7, 215, 31))
    medium_zone = distance_zone.crop ((299, 8, 325, 31))
    long_zone = distance_zone.crop ((401, 7, 435, 31))
    #sprint_zone.save("sprint.png") 
    #mile_zone.save("mile.png")
    #medium_zone.save("medium.png")

    distance_zones = {
        "sprint" : sprint_zone,
        "mile" : mile_zone,
        "medium" : medium_zone,
        "long" : long_zone
    }

    distance = {}
    for distance_name, zone in distance_zones.items():
        text = ocr_zone_adaptive(zone, whitelist="SABCDEFG", max_wh_ratio=1.2).strip()
        preprocess_zone(zone).save(f"C:/uma_data/{distance_name}_{idx}.png")
        raw_text = text.strip().upper().replace(" ", "")
        valid_char = ""
        for char in raw_text:
            if char in valid_ranks:  
                valid_char = char
                break
        distance[distance_name] = valid_char
    #print(distance)

    # =============== Style Processing ===============

    style_zone = ui_crop1.crop((125, 370, 570, 410))
    front_zone = style_zone.crop((84, 11, 110, 32))
    pace_zone = style_zone.crop((186, 12, 220, 33))
    late_zone = style_zone.crop((285, 11, 325, 33))
    end_zone = style_zone.crop((400, 12, 435, 32))

    style_zones = {
        "front_runner" : front_zone,
        "pace_chaser" : pace_zone,
        "late_surger" : late_zone,
        "end_closer" : end_zone
    }

    style = {}
    for style_name, zone in style_zones.items():
        text = ocr_zone_adaptive(zone, whitelist="SABCDEFG", max_wh_ratio=1.2).strip()
        preprocess_zone(zone).save(f"C:/uma_data/{style_name}_{idx}.png")
        best_match = process.extractOne(text, valid_ranks)
        if best_match and best_match[1] >= 60:
            style[style_name] = best_match[0]
        else:
            style[style_name] = "unknown"
    #print(style)

    # =============== Stats Processing ===============

    stats_zone = ui_crop1.crop((0, 255, 665, 330))

    speed_zone = stats_zone.crop((53, 0, 127, 50))
    stamina_zone = stats_zone.crop((165, 0, 240, 50))
    power_zone = stats_zone.crop((276, 0, 350, 40))
    guts_zone = stats_zone.crop((388, 0, 472, 55))
    wit_zone = stats_zone.crop((505, 0, 597, 50))

    stats_zones = {
        "speed": (speed_zone, 160),
        "stamina": (stamina_zone, 172),
        "power": (power_zone, 178),
        "guts": (guts_zone, 134),
        "wit": (wit_zone, 170)
    }

    stats = {}
    for stat_name, (zone, thresh_val) in stats_zones.items():
        text = ocr_zone(zone, thresh_val=thresh_val).strip()
        preprocess_zone(zone).save(f"C:/uma_data/{stat_name}_{idx}.png")
        text = re.sub(r'[^\d]', '', text)
        stats[stat_name] = text.strip()
    #print(stats)

    # =============== Skill Processing ===============

    skills = {}
    for skill_name, zone in skills_zones.items():
        text = ocr_zone(zone, thresh_val=170).strip()
        preprocess_zone(zone).save(f"C:/uma_data/{skill_name}_{idx}.png")
        best_match = process.extractOne(text, skill_names)
        if best_match and best_match[1] >= 60:
            skills[skill_name] = best_match[0]
        else:
            skills[skill_name] = "unknown"
    skills = {k: v for k, v in skills.items() if v != "unknown"}
    #print(skills)

    result = {}
    result["uma_name"] = uma_name
    result.update(tracks)      
    result.update(distance)    
    result.update(style)       
    result.update(stats)       
    result.update(skills) 

    return result

# =====================================================================================
# ====================================== Image 2 ======================================
# =====================================================================================



def process_img2(img2, idx):

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
        
    placing_top = y2
    placing_crop = img2.crop((x2, placing_top, x2 + w2, placing_top + 925))
    #placing_crop.save("RankUI.png")

    # ==================== Trainers Name, Placement/Rank, Part 1 ====================

    r_tname_results1 = {}
    for i in range (4):
        y = 475 + (i * 120)
        zone = placing_crop.crop((250, y, 450, y + 40))
        r_tname_results1[f"r_tname{i+1}"] = ocr_zone(zone).strip()
        preprocess_zone(zone).save(f"C:/uma_data/r_tname{i+1}_{idx}.png")
    #print(r_tname_results1)

    # ==================== Trainers Name, Placement/Rank, Part 2 ====================

    r_tname_results2 = {}
    for i in range(4):
        y = 460 + (i * 120)
        zone = placing_crop.crop((230, y, 450, y + 40))
        r_tname_results2[f"r_tname{i+5}"] = ocr_zone(zone).strip()
        preprocess_zone(zone).save(f"C:/uma_data/r_tname{i+5}_{idx}.png")

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
            r_uma_results1[f"r_uma{i+1}"] = best_match[0]
        else:
            r_uma_results1[f"r_uma{i+1}"] = "unknown"
        preprocess_zone(zone).save(f"C:/uma_data/r_uma{i+1}_{idx}.png")
    #print(r_uma_results1)

    # ==================== Uma Name, Placement/Rank, Part 2 ====================

    r_uma_results2 = {}
    for i in range(4):
        y = 430 + (i * 120)
        zone = placing_crop.crop((250, y, 465, y + 40))
        text = ocr_zone(zone).strip()
        best_match = process.extractOne(text, char_names)
        if best_match and best_match[1] >= 60:
            r_uma_results2[f"r_uma{i+5}"] = best_match[0]
        else:
            r_uma_results2[f"r_uma{i+5}"] = "unknown"
        preprocess_zone(zone).save(f"C:/uma_data/r_uma{i+5}_{idx}.png")

    result = {}

    result.update(r_tname_results1)
    result.update(r_tname_results2)
    result.update(r_uma_results1)
    result.update(r_uma_results2)

    return result

# =============================================================================================
# ========================================== Image 3 ==========================================
# =============================================================================================



def process_img3(img3, img3_2, idx):

    # ================================ Image 3 pre-processing ================================

    img3_np = np.array(img3)
    img3_2_np = np.array(img3_2)

    # =============================== Image 3, Part 1 ===============================

    gray3 = cv2.cvtColor(img3_np, cv2.COLOR_RGB2GRAY)
    edges3 = cv2.Canny(gray3, 30, 80)
    contours3, _ = cv2.findContours(edges3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for c in contours3:
        x, y, w, h = cv2.boundingRect(c)
        if w > 500 and h > 100:
            rectangles.append((x, y, w, h))
    #print(f"rectangles found: {len(rectangles)}")
    #print(rectangles)

    topmost_rect = min(rectangles, key=lambda r: r[1])
    rx1, ry1, rw1, rh1 = topmost_rect

    mood_crop1 = img3.crop((rx1, ry1, rx1 + rw1, ry1 + 717))
    #mood_crop1.save("mood_test1.png")

    # =============================== Image 3, Part 2 ===============================

    gray3_2 = cv2.cvtColor(img3_2_np, cv2.COLOR_RGB2GRAY)
    edges3_2 = cv2.Canny(gray3_2, 30, 80)
    contours3_2, _ = cv2.findContours(edges3_2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for c in contours3_2:
        x, y, w, h = cv2.boundingRect(c)
        if w > 553 and h > 108:
            rectangles.append((x, y, w, h))
    #print(f"rectangles found: {len(rectangles)}")
    #print(rectangles)

    botmost_rect = max(rectangles, key=lambda r: r[1])
    rx2, ry2, rw2, rh2 = botmost_rect
    #print(f"Header: x={rx2}, y={ry2}, w={rw2}, h={rh2}")
    mood_crop2 = img3_2.crop((rx2, ry2 - 575, rx2 + rw2, rh2 + ry2))
    #mood_crop2.save("mood_test2.png")

    # ======================== Mood Validation ========================

    mood_list = ["BAD", "NORMAL", "GOOD", "GREAT"]

    # ==================== Uma Names (Mood Screen), Part 1 ====================

    m_uma_results1 = {}
    for i in range(6):
        y = 35 + (i * 120)
        zone = mood_crop1.crop((155, y, 350, y + 45))
        text = ocr_zone(zone).strip()
        best_match = process.extractOne(text, char_names)
        if best_match and best_match[1] >= 60:
            m_uma_results1[f"m_uma{i+1}"] = best_match[0]
        else:
            m_uma_results1[f"m_uma{i+1}"] = "unknown"
        preprocess_zone(zone).save(f"C:/uma_data/m_uma{i+1}_{idx}.png")
    #print(m_uma_results1)

    # ==================== Uma Names (Mood Screen), Part 2 ====================

    m_uma_results2 = {}
    for i in range(3):
        y = 375 + (i * 120)
        zone = mood_crop2.crop((145, y, 350, y + 30))
        text = ocr_zone(zone).strip()
        best_match = process.extractOne(text, char_names)
        if best_match and best_match[1] >= 60:
            m_uma_results2[f"m_uma{i+7}"] = best_match[0]
        else:
            m_uma_results2[f"m_uma{i+7}"] = "unknown"
        preprocess_zone(zone).save(f"C:/uma_data/m_uma{i+7}_{idx}.png")
    #print(m_uma_results2)

    # ==================== Trainer Names (Mood Screen), Part 1 ====================

    mood_tname_results1 = {}
    for i in range(6):
        y = 70 + (i * 120)
        zone = mood_crop1.crop((110, y, 350, y + 30))
        mood_tname_results1[f"mood_tname{i+1}"] = ocr_zone(zone).strip()
        preprocess_zone(zone).save(f"C:/uma_data/mood_tname{i+1}_{idx}.png")
    #print(mood_tname_results1)

    # ==================== Trainer Names (Mood Screen), Part 2 ====================

    mood_tname_results2 = {}
    for i in range(3):
        y = 405 + (i * 120)
        zone = mood_crop2.crop((140, y, 367, y + 30))
        mood_tname_results2[f"mood_tname{i+7}"] = ocr_zone(zone).strip()
        preprocess_zone(zone).save(f"C:/uma_data/mood_tname{i+7}_{idx}.png")
    #print(mood_tname_results2)

    # ===================== Mood, Part 1 =====================

    mood_results1 = {}
    for i in range(6):
        y = 45 + (i * 120)
        zone = mood_crop1.crop((387, y, 440, y + 17))
        text = ocr_zone_adaptive(zone, whitelist="BADNORMLGET").strip()
        best_match = process.extractOne(text, mood_list)
        if best_match and best_match[1] >= 60:
            mood_results1[f"mood{i+1}"] = best_match[0]
        else:
            mood_results1[f"mood{i+1}"] = "unknown"
        preprocess_zone(zone).save(f"C:/uma_data/mood{i+1}_{idx}.png")

    #print(mood_results1)

    # ===================== Mood, Part 2 =====================

    mood_results2 = {}
    for i in range(3):
        y = 369 + (i * 120)
        zone = mood_crop2.crop((380, y, 430, y + 38))
        text = ocr_zone_adaptive(zone, whitelist="BADNORMLGET").strip()
        best_match = process.extractOne(text, mood_list)
        if best_match and best_match[1] >= 60:
            mood_results2[f"mood{i+7}"] = best_match[0]
        else:
            mood_results2[f"mood{i+7}"] = "unknown"
        preprocess_zone(zone).save(f"C:/uma_data/mood{i+7}_{idx}.png")
    #print(mood_results2)

    result = {}

    result.update(m_uma_results1)
    result.update(m_uma_results2)
    result.update(mood_tname_results1)
    result.update(mood_tname_results2)
    result.update(mood_results1)
    result.update(mood_results2)

    return result