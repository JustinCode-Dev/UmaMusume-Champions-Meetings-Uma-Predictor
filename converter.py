from PIL import Image
import cv2
import numpy as np
from rapidfuzz import process, fuzz
import json
import re
import pandas as pd
from pathlib import Path

import torch
from crnn import CrnnUma, decoder_predictions, build_vocab, build_char_maps, val_transform

with open("data/raw/character.json", "r", encoding="utf-8") as f:
    characters = json.load(f)

with open("data/raw/skills.json", "r", encoding="utf-8") as f:
    skills_data = json.load(f)

skill_names = [s["name"] for s in skills_data]
char_names_outer = [c["name"].split("(")[0].strip() for c in characters]
char_names = []
for c in characters:
    match = re.search(r"\((.*?)\)", c["name"])
    if match:
        char_names.append(match.group(1))

char_names_full = [k["name"] for k in characters]

# ======================== Mood & Style Validation ========================

mood_list = ["BAD", "NORMAL", "GOOD", "GREAT"]
style_list = ["Front", "Pace", "Late", "End"]

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

# =================================== OCR ===================================

chars = build_vocab("uma_data/labels_dl.csv")
char_to_idx, idx_to_char = build_char_maps(chars)
num_classes = len(char_to_idx)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = CrnnUma(num_classes=num_classes)
model.load_state_dict(torch.load("model/ocr/UmaOCR_v6.pth", map_location=device))
model.to(device)
model.eval()

def ocr_predict(pil_image, model, val_transform, idx_to_char, device, allowed_chars=None):
    padded = padding_img(pil_image)
    tensor = val_transform(padded).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(tensor)
        prediction = decoder_predictions(output, idx_to_char, allowed_chars=allowed_chars)

    return prediction[0]

def ocr_with_fuzzy(pil_image, model, val_transform, idx_to_char, device, choices, threshold=80, score_choice=fuzz.WRatio):
    raw_text = ocr_predict(pil_image, model, val_transform, idx_to_char, device)

    cleaned_text = re.sub(r'\.', ' ', raw_text)
    cleaned_text = " ".join(cleaned_text.split())
    cleaned_text = cleaned_text.replace("[", "(").replace("]", ")")
    
    match, score, _ = process.extractOne(cleaned_text, choices, scorer=score_choice)

    if score >= threshold:
        return match
    else:
        return f"{raw_text} (unsure)"

# =====================================================================================
# ====================================== Image 1 ======================================
# =====================================================================================

def process_img1(img1, prefix, rows):

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

    if not contours1:
        print(f"Warning: green header not found on")
        return

    ui_top1 = y1
    ui_crop1 = img1.crop((x1, ui_top1, x1 + w1, ui_top1 + 925))

    # ================== UI Button ==================

    button_zone = ui_crop1.crop((203, 420, 425, 480))
    button_np = np.array(button_zone)
    hsv = cv2.cvtColor(button_np, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, lower_green1, upper_green1)
    is_opponent = np.sum(mask) > 20000

    stats_zone = ui_crop1.crop((10, 250, 580, 300))
    aptitude_zone = ui_crop1.crop((133, 310, 567, 410))

    if is_opponent:
        name_zone = ui_crop1.crop((295, 75, 570, 115))
        skills_zone = ui_crop1.crop((0, 570, 580, 905))

    else:
        name_zone = ui_crop1.crop((285, 50, 525, 100))
        skills_zone = ui_crop1.crop((0, 470, 580, 925))

    name = ocr_with_fuzzy(name_zone, model, val_transform, idx_to_char, device, char_names)
    text = (f"[{name}]")
    filename = f"uma_data/images/uma_name_{prefix}.png"
    name_zone.convert('L').save(filename)
    rows.append({"filename": filename, "label": text})
    

    # ==================== Stats ====================
    stat_labels = ["speed", "stamina", "power", "guts", "wit"]
    for k in range(5):
        h = 115 + (k * 115)
        offset = k * 115
        stat = stats_zone.crop((40 + offset, 0, h, 40))
        filename = f"uma_data/images/{stat_labels[k]}_{prefix}.png"
        stat.convert('L').save(filename)
        text = ocr_predict(stat, model, val_transform, idx_to_char, device)
        rows.append({"filename": filename, "label": text})

    # ==================== Skills ====================
    skills = find_boxes(skills_zone)
    for i, (x, y, w, h) in enumerate(skills):
        skill = skills_zone.crop((x + 35, y, x + w, y + h))
        filename = f"uma_data/images/skill_{i+1}_{prefix}.png"
        skill.convert('L').save(filename)
        text = ocr_with_fuzzy(skill, model, val_transform, idx_to_char, device, skill_names)
        rows.append({"filename": filename, "label": text})

    # ==================== Aptitude ====================
    aptitude_labels = ["turf", "dirt", "sprint", "mile", "medium", "long", "front_runner", "pace_chaser", "late_surger", "end_closer"]
    aptitude = find_boxes(aptitude_zone, 83, 123, 20, 40)
    for label, (x, y, w, h) in zip(aptitude_labels, aptitude):
        aptitude_crop = aptitude_zone.crop((x + 70, y, x + w, y + h))
        filename = f"uma_data/images/{label}_{prefix}.png"
        aptitude_crop.convert('L').save(filename)
        text = ocr_predict(aptitude_crop, model, val_transform, idx_to_char, device)
        rows.append({"filename": filename, "label": text})

# =====================================================================================================
# ========================================== Image 2, part 1 ==========================================
# =====================================================================================================

def process_img2_1(img2_1, race_prefix, rows):

    img2_np = np.array(img2_1)

    gray2 = cv2.cvtColor(img2_np, cv2.COLOR_RGB2GRAY)
    edges3 = cv2.Canny(gray2, 30, 80)
    contours2, _ = cv2.findContours(edges3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for c in contours2:
        x, y, w, h = cv2.boundingRect(c)
        if w > 500 and h > 100:
            rectangles.append((x, y, w, h))
    if not rectangles:
        print(f"Warning: box not found on")
        return 
    
    topmost_rect = min(rectangles, key=lambda r: r[1])
    rx1, ry1, rw1, rh1 = topmost_rect

    mood_crop1 = img2_1.crop((rx1, ry1, rx1 + rw1, ry1 + 717))

    # ==================== Uma Names (Mood Screen), Part 1 ====================

    for i in range(6):
        y = 0 + (i * 120)
        row = mood_crop1.crop((0, y, 561, y + 105))
        boxes = find_boxes(row, 40, 110, 25, 45)
        boxes = boxes[:1]
        
        for box_idx, (x, y2, w, h) in enumerate(boxes):
            moods = row.crop((x + 33, y2, x + w, y2 + h - 5))
            filename = f"uma_data/images/mood{i+1}_{race_prefix}.png"
            moods.convert('L').save(filename)
            text_mood = ocr_with_fuzzy(moods, model, val_transform, idx_to_char, device, mood_list, 80)
            rows.append({"filename": filename, "label": text_mood})

            names = row.crop((x - 200, y2, x + w - 125, y2 + h))
            filename = f"uma_data/images/uma_name{i+1}_{race_prefix}.png"
            names.convert('L').save(filename)
            text_name = ocr_with_fuzzy(names, model, val_transform, idx_to_char, device, char_names_outer, 80)
            rows.append({"filename": filename, "label": text_name})

# =====================================================================================================
# ========================================== Image 2, Part 2 ==========================================
# =====================================================================================================

def process_img2_2(img2_2, race_prefix, rows):
    img2_2_np = np.array(img2_2)
    gray2_2 = cv2.cvtColor(img2_2_np, cv2.COLOR_RGB2GRAY)
    edges2_2 = cv2.Canny(gray2_2, 30, 80)
    contours2_2, _ = cv2.findContours(edges2_2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for c in contours2_2:
        x, y, w, h = cv2.boundingRect(c)
        if w > 553 and h > 108:
            rectangles.append((x, y, w, h))
    if not rectangles:
        print(f"Warning: box not found on")
        return

    botmost_rect = max(rectangles, key=lambda r: r[1])
    rx2, ry2, rw2, rh2 = botmost_rect
    mood_crop2 = img2_2.crop((rx2, ry2 - 575, rx2 + rw2, rh2 + ry2))

    # ==================== Uma Names (Mood Screen), Part 2 ====================
    
    mood_coords = {
            7 : (0, 340, 561, 440),
            8 : (0, 460, 561, 560),
            9 : (0, 580, 561, 680)
        }
            
    for row_num, coords in mood_coords.items():
        row = mood_crop2.crop(coords)
        boxes = find_boxes(row, 45, 103, 25, 45)

        for x, y, w, h in boxes:
            moods = row.crop((x + 33, y, x + w, y + h - 5))
            filename = f"uma_data/images/mood{row_num}_{race_prefix}.png"
            moods.convert('L').save(filename)
            text_mood = ocr_with_fuzzy(moods, model, val_transform, idx_to_char, device, mood_list, 80)
            rows.append({"filename": filename, "label": text_mood})

            names = row.crop((x - 200, y, x + w - 125, y + h))
            filename = f"uma_data/images/uma_name{row_num}_{race_prefix}.png"
            names.convert('L').save(filename)
            text_name = ocr_with_fuzzy(names, model, val_transform, idx_to_char, device, char_names_outer, 80)
            rows.append({"filename": filename, "label": text_name})

# =====================================================================================
# ====================================== Image 3 ======================================
# =====================================================================================

def process_img3(img3_1, race_prefix, rows, start_num=1):

    img3_np = np.array(img3_1)
    hsv3 = cv2.cvtColor(img3_np, cv2.COLOR_RGB2HSV)
    lower_green2 = np.array([40, 100, 100])
    upper_green2 = np.array([80, 255, 255])

    mask2 = cv2.inRange(hsv3, lower_green2, upper_green2)
    contours2, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours2:
        topmost2 = min(contours2, key=lambda c: cv2.boundingRect(c)[1])
        x2, y2, w2, h2 = cv2.boundingRect(topmost2)
    else:
        print(f"Warning: green header not found")
        return 
        
    rank_top = y2
    rank_crop = img3_1.crop((x2, rank_top, x2 + w2 - 15, rank_top + 925))

    boxes = find_boxes(rank_crop, 160, 200, 45, 65)

    for i, (x, y, w, h) in enumerate(boxes):
        rank = rank_crop.crop((x - 5, y + 25, x + w, y + h + 5))
        rank_num = start_num + i
        filename = f"uma_data/images/r_uma{rank_num}_{race_prefix}.png"
        rank.convert('L').save(filename)
        text = ocr_with_fuzzy(rank, model, val_transform, idx_to_char, device, char_names_outer)
        rows.append({"filename": filename,"label": text})

# ==========================================================================================
# ========================================== Main ==========================================
# ==========================================================================================

if __name__ == "__main__":
    rows = []
    cm_rounds = {
        "cm16" : ["round1", "round2"],
        "cm17" : ["round2"]
    }
    
    for cm, rounds in cm_rounds.items():
        for round_name in rounds:
           race_dirs = sorted(Path(f"photo/{cm}/{round_name}/detail").glob("race*"))
           mood_photos = sorted(Path(f"photo/{cm}/{round_name}/mood").glob("*.png"))
           rank_photos = sorted(Path(f"photo/{cm}/{round_name}/rank").glob("*.png"))
    
           for race_idx, race_dir in enumerate(race_dirs):
               race_name = race_dir.name
               detail_photos = sorted(race_dir.glob("*.png"))
               mood_pair = mood_photos[race_idx * 2 : race_idx * 2 + 2]
               rank_pair = rank_photos[race_idx * 2 : race_idx * 2 + 2]
    
               race_prefix = f"{cm}_{round_name}_{race_name}"
    
               img2_1 = Image.open(mood_pair[0])
               img2_2 = Image.open(mood_pair[1])
               img3_1 = Image.open(rank_pair[0])
               img3_2 = Image.open(rank_pair[1])
               
               result2_1 = process_img2_1(img2_1, race_prefix, rows)
               result2_2 = process_img2_2(img2_2, race_prefix, rows)
               result3_1 = process_img3(img3_1, race_prefix, rows, start_num=1)
               result3_2 = process_img3(img3_2, race_prefix, rows, start_num=5)
    
               for i, detail_path in enumerate(detail_photos):
                   prefix = f"{cm}_{round_name}_{race_name}_{i}"
                   img1 = Image.open(detail_path)
                   result1 = process_img1(img1, prefix, rows)
    
    df = pd.DataFrame(rows)
    df["filename"] = df["filename"].str.replace("uma_data/images/", "images/", regex=False)
    df.to_csv("uma_data/labels_dl.csv", mode='a', header=False, index=False, encoding='utf-8-sig')