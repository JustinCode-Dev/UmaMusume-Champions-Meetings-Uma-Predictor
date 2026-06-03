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

#img1 = Image.open("") # Uma Detail
#img2 = Image.open("") # Ranks UI
img3 = Image.open("photo/cm13/mood/round1/Screenshot 2026-05-15 184928.png") # Mood UI
img3_np = np.array(img3)
"""img_np = np.array(img1)
img2_np = np.array(img2)


# =========== Image 1 ===========
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

# =========== Image 2 ===========
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
placing_crop.save("zzzz.png")"""

# =========== Image 3 ===========
gray3 = cv2.cvtColor(img3_np, cv2.COLOR_RGB2GRAY)
edges3 = cv2.Canny(gray3, 30, 80)
contours3, _ = cv2.findContours(edges3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

rectangles = []
for c in contours3:
    x, y, w, h = cv2.boundingRect(c)
    if w > 500 and h > 90:
        rectangles.append((x, y, w, h))
print(f"rectangles found: {len(rectangles)}")
print(rectangles)

# =========== Trainer Name ===========
"""train1 = placing_crop.crop((230, 465, 450, 504))
train2 = placing_crop.crop((230, 585, 450, 624)) 
train3 = placing_crop.crop((230, 708, 450, 744))
train4 = placing_crop.crop((230, 828, 450, 864))
train1.save("train1.png")
train2.save("train2.png")
train3.save("train3.png")
train4.save("train4.png")

# =========== Placement/Rank ===========
rank1 = placing_crop.crop((10, 410, 125, 509))
rank2 = placing_crop.crop((10, 530, 125, 629)) 
rank3 = placing_crop.crop((10, 650, 125, 749))
rank4 = placing_crop.crop((10, 770, 125, 869))
rank1.save("rank1.png")
rank2.save("rank2.png")
rank3.save("rank3.png")
rank4.save("rank4.png")

# =========== UI Button ===========
button_zone = ui_crop1.crop((203, 420, 425, 480))
button_np = np.array(button_zone)
hsv = cv2.cvtColor(button_np, cv2.COLOR_RGB2HSV)
mask = cv2.inRange(hsv, lower_green1, upper_green1)
print("Green pixels:", np.sum(mask))
is_opponent = np.sum(mask) > 20000

if is_opponent:
    name_zone = ui_crop1.crop((295, 75, 570, 120))
    skills_zone = ui_crop1.crop((0, 570, 665, 900))
    skill_1 = skills_zone.crop((55, 20, 300, 60))
    skill_2 = skills_zone.crop((55, 80, 300, 120))
    skill_3 = skills_zone.crop((55, 145, 285, 185))
    skill_4 = skills_zone.crop((55, 210, 300, 250))
    skill_5 = skills_zone.crop((55, 275, 300, 315))
    skill_6 = skills_zone.crop((335, 20, 540, 60))
    skill_7 = skills_zone.crop((335, 80, 540, 120))
    skill_8 = skills_zone.crop((335, 145, 540, 185))
    skill_9 = skills_zone.crop((335, 210, 540, 250))
    skill_10 = skills_zone.crop((335, 275, 540, 315))
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
    skill_1 = skills_zone.crop((40, 0, 300, 50))
    skill_2 = skills_zone.crop((40, 60, 300, 110))
    skill_3 = skills_zone.crop((40, 120, 285, 170))
    skill_4 = skills_zone.crop((40, 180, 300, 250))
    skill_5 = skills_zone.crop((40, 240, 300, 310))
    skill_6 = skills_zone.crop((40, 300, 300, 370))
    skill_7 = skills_zone.crop((40, 367, 300, 430))
    skill_8 = skills_zone.crop((325, 0, 560, 50))
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

# ============ Ranks Validation ============
valid_ranks = ["S", "A", "B", "C", "D", "E", "F", "G"]

# ============ Name Processing ============

name_zone = name_zone.resize((name_zone.width * 2, name_zone.height * 2))
name_np = np.array(name_zone)
name_gray = cv2.cvtColor(name_np, cv2.COLOR_RGB2GRAY)
_, name_thresh = cv2.threshold(name_gray, 120, 255, cv2.THRESH_BINARY)
name_processed = Image.fromarray(name_thresh)
name_processed.save("name.png")
name_text = pytesseract.image_to_string(name_processed, config='--psm 7')
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

# ============ Track Coordinate ============

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
    zone = zone.resize((zone.width * 2, zone.height * 2))
    zone_np = np.array(zone)
    zone_gray = cv2.cvtColor(zone_np, cv2.COLOR_RGB2GRAY)
    zone_processed_np = cv2.adaptiveThreshold(
    zone_gray, 
    255, 
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
    cv2.THRESH_BINARY, 
    11,  # only odds number
    1    # 2-5
    )
    padded_np = cv2.copyMakeBorder(
        zone_processed_np, 10, 10, 10, 10, 
        cv2.BORDER_CONSTANT, 
        value=[255, 255, 255]
    )
    zone_processed = Image.fromarray(padded_np)
    raw_ocr_text = pytesseract.image_to_string(zone_processed, config='--psm 10')
    zone_processed.save(f"{track_name}_processed.png")

    if raw_ocr_text:
        matched_rank = process.extractOne(raw_ocr_text, valid_ranks)[0]
    else:
        matched_rank = "unkwnown"

    tracks[track_name] = matched_rank

turf_rank = tracks.get("turf", "?")
dirt_rank = tracks.get("dirt", "?")

print(f"Turf: {turf_rank} Dirt: {dirt_rank}")

# ============ Distance Coordinate ============

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
    zone = zone.resize((zone.width * 2, zone.height * 2))
    zone_np = np.array(zone)
    zone_gray = cv2.cvtColor(zone_np, cv2.COLOR_RGB2GRAY)
    zone_processed_np = cv2.adaptiveThreshold(
    zone_gray, 
    255, 
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
    cv2.THRESH_BINARY, 
    11,  # only odds number
    1    # 2-5
    )
    padded_np = cv2.copyMakeBorder(
        zone_processed_np, 10, 10, 10, 10, 
        cv2.BORDER_CONSTANT, 
        value=[255, 255, 255]
    )
    zone_processed = Image.fromarray(padded_np)
    text = pytesseract.image_to_string(zone_processed, config='--psm 10 -c tessedit_char_whitelist=SABCDEFG -c tessedit_max_char_wh_ratio=1.2')
    raw_text = text.strip().upper().replace(" ", "")
    valid_char = ""
    for char in raw_text:
        if char in valid_ranks:  
            valid_char = char
            break
    distance[distance_name] = valid_char
    zone_processed.save(f"test_{distance_name}.png")
print(distance)

# ============ Style Coordinate ============

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
    zone = zone.resize((zone.width * 2, zone.height * 2))
    zone_np = np.array(zone)
    zone_gray = cv2.cvtColor(zone_np, cv2.COLOR_RGB2GRAY)
    zone_processed_np = cv2.adaptiveThreshold(
    zone_gray, 
    255, 
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
    cv2.THRESH_BINARY, 
    11,  # only odds number
    1    # 2-5
    )
    padded_np = cv2.copyMakeBorder(
        zone_processed_np, 10, 10, 10, 10, 
        cv2.BORDER_CONSTANT, 
        value=[255, 255, 255]
    )
    zone_processed = Image.fromarray(padded_np)
    text = pytesseract.image_to_string(zone_processed, config='--psm 10 -c tessedit_char_whitelist=SABCDEFG -c tessedit_max_char_wh_ratio=1.2')
    raw_text = text.strip().upper().replace(" ", "")
    valid_char = ""
    for char in raw_text:
        if char in valid_ranks:  
            valid_char = char
            break
    style[style_name] = valid_char
    zone_processed.save(f"test_{style_name}.png")
print(style)

# ============ Stats Coordinate ============

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
    #upscale 2x
    zone = zone.resize((zone.width * 2, zone.height * 2))

    # preprocessing
    zone_np = np.array(zone)
    zone_gray = cv2.cvtColor(zone_np, cv2.COLOR_RGB2GRAY)
    _, zone_thresh = cv2.threshold(zone_gray, thresh_val, 255, cv2.THRESH_BINARY)
    zone_processed = Image.fromarray(zone_thresh)
    zone_processed.save(f"test_{stat_name}.png")
    # OCR -Takes numbers only
    text = pytesseract.image_to_string(zone_processed, config='--psm 7 digits')
    stats[stat_name] = text.strip()
    text = re.sub(r'[^\d]', '', text)
    stats[stat_name] = text.strip()
print(stats)

# ============ Skill Processing ============

skills = {}
for skill_name, (zone, thresh_val) in skills_zones.items():
    zone = zone.resize((zone.width * 2, zone.height * 2))

    # Preprocessing
    zone_np = np.array(zone)
    zone_gray = cv2.cvtColor(zone_np, cv2.COLOR_RGB2GRAY)
    _, zone_thresh = cv2.threshold(zone_gray, thresh_val, 255, cv2.THRESH_BINARY)
    zone_processed = Image.fromarray(zone_thresh)
    zone_processed.save(f"test_{skill_name}.png")
    
    text = pytesseract.image_to_string(zone_processed, config='--psm 7')

    # Fuzzy Match
    best_match = process.extractOne(text, skill_names)
    if best_match and best_match[1] >= 60:
        skills[skill_name] = best_match[0]
    else:
        skills[skill_name] = "unknown"
skills = {k: v for k, v in skills.items() if v != "unknown"}
print(skills)"""