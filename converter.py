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

img1 = Image.open("photo/cm14/round1/detail/race2/Screenshot 2026-06-05 173730.png") # Uma Detail
img2 = Image.open("photo/cm14/round2/rank/Screenshot 2026-06-07 152321.png") # Ranks UI
img3 = Image.open("photo/cm14/round1/mood/Screenshot 2026-06-05 173504.png") # Mood UI 1
img3_2 = Image.open("photo/cm14/round1/mood/Screenshot 2026-06-05 181021.png") # mood UI 2 
img3_2.save("mood_test2.png")
img3_np = np.array(img3)
img3_2_np = np.array(img3_2)
img_np = np.array(img1)
img2_np = np.array(img2)

# ==============================================================
# =================== Preprocessing Function ===================
# ==============================================================

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
    zone = zone.resize((zone.width * 2, zone.height * 2))
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

# =====================================
# ============== Image 1 ==============
# =====================================

hsv1 = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
lower_green1 = np.array([40, 100, 100])
upper_green1 = np.array([80, 255, 255])

mask1 = cv2.inRange(hsv1, lower_green1, upper_green1)
contours1, _ = cv2.findContours(mask1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

if contours1:
    topmost1 = min(contours1, key=lambda c: cv2.boundingRect(c)[1])
    x1, y1, w1, h1 = cv2.boundingRect(topmost1)
    #print(f"Header: x={x}, y={y}, w={w}, h={h}")

ui_top1 = y1
ui_crop1 = img1.crop((x1, ui_top1, x1 + w1, ui_top1 + 919))
ui_crop1.save("test.png")
"""
# =====================================
# ============== Image 2 ==============
# =====================================

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
placing_crop.save("RankUI.png")

# =======================================
# =========== Image 3, Part 1 ===========
# =======================================

gray3 = cv2.cvtColor(img3_np, cv2.COLOR_RGB2GRAY)
edges3 = cv2.Canny(gray3, 30, 80)
contours3, _ = cv2.findContours(edges3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

rectangles = []
for c in contours3:
    x, y, w, h = cv2.boundingRect(c)
    if w > 500 and h > 100:
        rectangles.append((x, y, w, h))
print(f"rectangles found: {len(rectangles)}")
print(rectangles)

topmost_rect = min(rectangles, key=lambda r: r[1])
rx1, ry1, rw1, rh1 = topmost_rect

mood_crop1 = img3.crop((rx1, ry1, rx1 + rw1, ry1 + 717))
mood_crop1.save("mood_test1.png")

# =======================================================
# =========== Uma Names (Mood Screen), Part 1 ===========
# =======================================================

m_uma_gray1 = {}
m_uma_results1 = {}
for i in range(6):
    y = 35 + (i * 120)
    zone = mood_crop1.crop((155, y, 350, y + 45))
    m_uma_gray1[f"m_uma{i+1}"] = preprocess_zone(zone)
    m_uma_results1[f"m_uma{i+1}"] = ocr_zone(zone)
    #preprocess_zone(zone).save(f"m_uma{i+1}.png"

# ===========================================================
# =========== Trainer Names (Mood Screen), Part 1 ===========
# ===========================================================

mood_tname_gray1 = {}
mood_tname_results1 = {}
for i in range(6):
    y = 70 + (i * 120)
    zone = mood_crop1.crop((110, y, 350, y + 30))
    mood_tname_gray1[f"mood_tname{i+1}"] = preprocess_zone(zone)
    mood_tname_results1[f"mood_tname{i+1}"] = ocr_zone(zone)
    #preprocess_zone(zone).save(f"mood_tname{i+1}.png")

# ======================================
# ============ Mood, Part 1 ============
# ======================================

mood_gray1 = {}
mood_results1 = {}
for i in range(6):
    y = 25 + (i * 120)
    zone = mood_crop1.crop((340, y, 470, y + 55))
    mood_gray1[f"mood{i+1}"] = preprocess_zone(zone)
    mood_results1[f"mood{i+1}"] = ocr_zone(zone)
    #preprocess_zone(zone).save(f"mood{i+1}.png")

# =======================================================
# =========== Uma Names (Mood Screen), Part 2 ===========
# =======================================================

m_uma_gray2 = {}
m_uma_results2 = {}
for i in range(3):
    y = 390 + (i * 120)
    zone = img3_2.crop((155, y, 350, y + 35))
    m_uma_gray2[f"m_uma{i+7}"] = preprocess_zone(zone)
    m_uma_results2[f"m_uma{i+7}"] = ocr_zone(zone)
    #preprocess_zone(zone).save(f"m_uma{i+7}.png")

# ===========================================================
# =========== Trainer Names (Mood Screen), Part 2 ===========
# ===========================================================

mood_tname_gray2 = {}
mood_tname_results2 = {}
for i in range(3):
    y = 421 + (i * 120)
    zone = img3_2.crop((110, y, 367, y + 45))
    mood_tname_gray2[f"mood_tname{i+7}"] = preprocess_zone(zone)
    mood_tname_results2[f"mood_tname{i+7}"] = ocr_zone(zone)
    #preprocess_zone(zone).save(f"mood_tname{i+7}.png")

# ======================================
# ============ Mood, Part 2 ============
# ======================================

mood_gray2 = {}
mood_results2 = {}
for i in range(3):
    y = 375 + (i * 120)
    zone = img3_2.crop((350, y, 475, y + 70))
    mood_gray2[f"mood{i+7}"] = preprocess_zone(zone)
    mood_results2[f"mood{i+7}"] = ocr_zone(zone)
    #preprocess_zone(zone).save(f"mood{i+7}.png")

# ==============================================================
# ===========  Trainers Name, Placement/Rank, Part 1 ===========
# ==============================================================

r_tname_gray1 = {}
r_tname_results1 = {}
for i in range (4):
    y = 475 + (i * 120)
    zone = placing_crop.crop((230, y, 450, y + 40))
    r_tname_gray1[f"r_tname{i+1}"] = preprocess_zone(zone)
    r_tname_results1[f"r_tname{i+1}"] = ocr_zone(zone)
    #preprocess_zone(zone).save(f"r_tname{i+1}.png")

# ==============================================================
# ===========  Trainers Name, Placement/Rank, Part 2 ===========
# ==============================================================

r_tname_res = {}
r_tname_gray2 = {}
r_tname_results2 = {}
for i in range(4):
    y = 460 + (i * 120)
    zone = placing_crop.crop((230, y, 450, y + 40))
    r_tname_gray2[f"r_tname{i+5}"] = preprocess_zone(zone)
    r_tname_results2[f"r_tname{i+5}"] = ocr_zone(zone)
    #preprocess_zone(zone).save(f"r_tname{i+5}.png")

# ==============================================
# =========== Placement/Rank, Part 1 ===========
# ==============================================

rank_gray1 = {}
rank_results1 = {}
for i in range(4):
    y = 410 + (i * 120)
    zone = placing_crop.crop((10, y, 125, y + 99))
    rank_gray1[f"rank{i+1}"] = preprocess_zone(zone)
    rank_results1[f"rank{i+1}"] = ocr_zone(zone)
    #preprocess_zone(zone).save(f"rank{i+1}.png")

# ==============================================
# =========== Placement/Rank, Part 2 ===========
# ==============================================

rank_gray2 = {}
rank_results2 = {}
for i in range(4):
    y = 400 + (i * 120)
    zone = placing_crop.crop((10, y, 125, y + 100))
    rank_gray2[f"rank{i+5}"] = preprocess_zone(zone)
    rank_results2[f"rank{i+5}"] = ocr_zone(zone)
    #preprocess_zone(zone).save(f"rank{i+5}.png")

# ========================================================
# =========== Uma Name, Placement/Rank, Part 1 ===========
# ========================================================

r_uma_gray1 = {}
r_uma_results1 = {}
for i in range(4):
    y = 440 + (i * 120)
    zone = placing_crop.crop((250, y, 450, y + 40))
    r_uma_gray1[f"r_uma{i+1}"] = preprocess_zone(zone)
    r_tname_results1[f"r_uma{i+1}"] = ocr_zone(zone)
    #preprocess_zone(zone).save(f"r_uma{i+1}.png")

# ========================================================
# =========== Uma Name, Placement/Rank, Part 2 ===========
# ========================================================

r_uma_gray2 = {}
r_uma_results2 = {}
for i in range(4):
    y = 430 + (i * 120)
    zone = placing_crop.crop((250, y, 465, y + 40))
    r_uma_gray2[f"r_uma{i+5}"] = preprocess_zone(zone)
    r_uma_results2[f"r_uma{i+5}"] = ocr_zone(zone)
    #preprocess_zone(zone).save(f"r_uma{i+5}.png")
"""
# =========================================
# =============== UI Button ===============
# =========================================

button_zone = ui_crop1.crop((203, 420, 425, 480))
button_np = np.array(button_zone)
hsv = cv2.cvtColor(button_np, cv2.COLOR_RGB2HSV)
mask = cv2.inRange(hsv, lower_green1, upper_green1)
print("Green pixels:", np.sum(mask))
is_opponent = np.sum(mask) > 20000

if is_opponent:
    name_zone = ui_crop1.crop((295, 75, 570, 120))
    skills_zone = ui_crop1.crop((0, 570, 665, 900))
    skill_1 = skills_zone.crop((55, 25, 300, 70))
    skill_2 = skills_zone.crop((55, 85, 300, 130))
    skill_3 = skills_zone.crop((55, 145, 300, 190))
    skill_4 = skills_zone.crop((55, 205, 300, 250))
    skill_5 = skills_zone.crop((55, 265, 300, 310))
    skill_6 = skills_zone.crop((335, 25, 540, 70))
    skill_7 = skills_zone.crop((335, 85, 540, 130))
    skill_8 = skills_zone.crop((335, 145, 540, 190))
    skill_9 = skills_zone.crop((335, 205, 540, 250))
    skill_10 = skills_zone.crop((335, 265, 540, 310))

    skills_zones = {
    "skill1" : (skill_1, 170),
    "skill2" : (skill_2, 170),
    "skill3" : (skill_3, 170),
    "skill4" : (skill_4, 170),
    "skill5" : (skill_5, 170),
    "skill6" : (skill_6, 170),
    "skill7" : (skill_7, 170),
    "skill8" : (skill_8, 170),
    "skill9" : (skill_9, 170),
    "skill10" : (skill_10, 170)
    }
else:
    name_zone = ui_crop1.crop((285, 50, 530, 100))
    skills_zone = ui_crop1.crop((0, 485, 665, 919))
    skill_1 = skills_zone.crop((48, 0, 300, 50))
    skill_2 = skills_zone.crop((48, 60, 300, 110))
    skill_3 = skills_zone.crop((48, 120, 285, 170))
    skill_4 = skills_zone.crop((48, 180, 300, 250))
    skill_5 = skills_zone.crop((48, 240, 300, 310))
    skill_6 = skills_zone.crop((48, 300, 300, 370))
    skill_7 = skills_zone.crop((48, 367, 300, 430))
    skill_8 = skills_zone.crop((335, 0, 560, 50))
    skill_9 = skills_zone.crop((335, 60, 540, 110))
    skill_10 = skills_zone.crop((335, 120, 540, 170))
    skill_11 = skills_zone.crop((335, 180, 540, 250))
    skill_12 = skills_zone.crop((335, 240, 540, 310))
    skill_13 = skills_zone.crop((335, 300, 540, 370))
    skill_14 = skills_zone.crop((335, 367, 540, 430))
    skills_zones = {
    "skill1" : (skill_1, 170),
    "skill2" : (skill_2, 170),
    "skill3" : (skill_3, 170),
    "skill4" : (skill_4, 170),
    "skill5" : (skill_5, 170),
    "skill6" : (skill_6, 170),
    "skill7" : (skill_7, 170),
    "skill8" : (skill_8, 170),
    "skill9" : (skill_9, 170),
    "skill10" : (skill_10, 170),
    "skill11" : (skill_11, 170),
    "skill12" : (skill_12, 170),
    "skill13" : (skill_13, 170),
    "skill14" : (skill_14, 170),
    }

"""
# ==========================================
# ============ Ranks Validation ============
# ==========================================

valid_ranks = ["S", "A", "B", "C", "D", "E", "F", "G"]

# =============================================================
# ============ Uma Name Processing (Uma Detail UI) ============
# =============================================================

name_text = ocr_zone(name_zone)
print("Name:", name_text)
name_raw = name_text.strip()
best_match = process.extractOne(name_raw, char_names)
print("Match:", best_match)
matched_name = best_match[0]
matched_score = best_match[1]

# Checking the Accuracy
if matched_score >= 70:
    print("Name:", matched_name)
else:
    print("Name not found")

# ==========================================
# ============ Track Coordinate ============
# ==========================================

turf_zone = ui_crop1.crop((198, 313, 250, 340))  
dirt_zone = ui_crop1.crop((300, 313, 360, 340))
turf_zone.save("turf.png")
dirt_zone.save("dirt.png")

track_zones = {
    "turf" : (turf_zone, 185),
    "dirt" : (dirt_zone, 185)
}

tracks = {}

for track_name, (zone, thresh_val) in track_zones.items():
    raw_ocr_text = ocr_zone_adaptive(zone, whitelist="SABCDEFG", max_wh_ratio=1.2)

    if raw_ocr_text:
        matched_rank = process.extractOne(raw_ocr_text, valid_ranks)[0]
    else:
        matched_rank = "unkwnown"

    tracks[track_name] = matched_rank

turf_rank = tracks.get("turf", "?")
dirt_rank = tracks.get("dirt", "?")

print(f"Turf: {turf_rank} Dirt: {dirt_rank}")

# =============================================
# ============ Distance Coordinate ============
# =============================================

distance_zone = ui_crop1.crop((125, 340, 570, 378))
sprint_zone = distance_zone.crop ((80, 7, 110, 30))
mile_zone = distance_zone.crop ((185, 7, 220, 29))
medium_zone = distance_zone.crop ((299, 8, 325, 28))
long_zone = distance_zone.crop ((401, 7, 435, 30))

distance_zones = {
    "sprint" : (sprint_zone, 180),
    "mile" : (mile_zone, 185),
    "medium" : (medium_zone, 185),
    "long" : (long_zone, 183)
}

distance = {}
for distance_name, (zone, thresh_val) in distance_zones.items():
    text = ocr_zone_adaptive(zone, whitelist="SABCDEFG", max_wh_ratio=1.2)
    raw_text = text.strip().upper().replace(" ", "")
    valid_char = ""
    for char in raw_text:
        if char in valid_ranks:  
            valid_char = char
            break
    distance[distance_name] = valid_char
print(distance)

# ==========================================
# ============ Style Coordinate ============
# ==========================================

style_zone = ui_crop1.crop((125, 370, 570, 410))
front_zone = style_zone.crop((80, 12, 110, 32))
pace_zone = style_zone.crop((186, 10, 220, 30))
late_zone = style_zone.crop((285, 11, 325, 33))
end_zone = style_zone.crop((400, 12, 435, 32))

style_zones = {
    "front_runner" : (front_zone, 183),
    "pace_chaser" : (pace_zone, 188),
    "late_surger" : (late_zone, 183),
    "end_closer" : (end_zone, 183)
}

style = {}
for style_name, (zone, thresh_val) in style_zones.items():
    text = ocr_zone_adaptive(zone, whitelist="SABCDEFG", max_wh_ratio=1.2)
    raw_text = text.strip().upper().replace(" ", "")
    valid_char = ""
    for char in raw_text:
        if char in valid_ranks:  
            valid_char = char
            break
    style[style_name] = valid_char
print(style)

# ==========================================
# ============ Stats Coordinate ============
# ==========================================

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
    text = ocr_zone(zone, thresh_val=thresh_val)
    text = re.sub(r'[^\d]', '', text)
    stats[stat_name] = text.strip()
print(stats)"""

# ==========================================
# ============ Skill Processing ============
# ==========================================

skills = {}
for skill_name, (zone, thresh_val) in skills_zones.items():
    #text = ocr_zone(zone, thresh_val=thresh_val)
    preprocess_zone(zone).save(f"{skill_name}.png")
    # Fuzzy Match
    """best_match = process.extractOne(text, skill_names)
    if best_match and best_match[1] >= 60:
        skills[skill_name] = best_match[0]
    else:
        skills[skill_name] = "unknown"
skills = {k: v for k, v in skills.items() if v != "unknown"}
print(skills)"""