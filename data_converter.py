from PIL import Image
import cv2
import numpy as np
from rapidfuzz import process
import json
import re

img1 = Image.open("photo/cm14/round1/mood/Screenshot 2026-06-05 173504.png") #skill_img
img2 = Image.open("photo/cm14/round1/mood/Screenshot 2026-06-05 174301.png")

# ============================= Images Pre-processing ============================

# ============================ Image 1 pre-processing ============================

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
    print(f"Warning")
ui_top1 = y1
ui_crop1 = img1.crop((x1, ui_top1, x1 + w1, ui_top1 + 925))
ui_crop1.save("z_test.png")


# ================================ Mood pre-processing ================================


# =================================== Mood, Part 1 ===================================
def process_img3(img1):
    img3_np = np.array(img1)
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
    print(f"rectangles found: {len(rectangles)}")

    topmost_rect = min(rectangles, key=lambda r: r[1])
    rx1, ry1, rw1, rh1 = topmost_rect
    print(rw1)
    mood_crop1 = img1.crop((rx1 + 5, ry1, rx1 + rw1 + 5, ry1 + 717))
    mood_crop1.save("mood_test1.png")

    return mood_crop1


# =================================== Mood, Part 2 ===================================

def process_img3_2(img2):
    img3_2_np = np.array(img2)
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
    mood_crop2 = img2.crop((rx2, ry2 - 575, rx2 + rw2, rh2 + ry2 - 30))
    mood_crop2.save("mood_test2.png")

    return mood_crop2


# ============================ Size Processing ============================

def preprocessing_img(image, target_height=48, max_width=460):
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


# ================================= Box Detection =================================

def find_boxes(zone, min_w=150, max_w=310, min_h=30, max_h=70, offset=0):
    zone_np = np.array(zone)
    zone_gray = cv2.cvtColor(zone_np, cv2.COLOR_RGB2GRAY)
    
    kernel = np.ones((3, 3), np.uint8)
    gradient = cv2.morphologyEx(zone_gray, cv2.MORPH_GRADIENT, kernel)
    _, binary = cv2.threshold(gradient, 20, 255, cv2.THRESH_BINARY)
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    cv2.imwrite("debug_skill_mask.png", closed)
    
    boxes = []
    for c in contours: 
        x, y, w, h = cv2.boundingRect(c)
        print(f"x={x}, y={y}, w={w}, h={h}")
        if min_w <= w <= max_w and min_h <= h <= max_h:
            boxes.append((x, y, w, h))

    boxes.sort(key=lambda b: (b[1], b[0]))

    for i, (x, y, w, h) in enumerate(boxes):
        crop = zone.crop((x + offset, y, x + w, y + h))
        crop_gray = crop.convert('L')
        crop_gray.save(f"zkill_{i}.png")
    
    return boxes


# ================================ UI Button ================================

button_zone = ui_crop1.crop((203, 420, 425, 480))
button_np = np.array(button_zone)
hsv = cv2.cvtColor(button_np, cv2.COLOR_RGB2HSV)
mask = cv2.inRange(hsv, lower_green1, upper_green1)
#print("Green pixels:", np.sum(mask))
is_opponent = np.sum(mask) > 20000

if is_opponent:
    name_zone = name_zone = ui_crop1.crop((295, 75, 570, 120))
    skills_zone = ui_crop1.crop((0, 570, 580, 905))
    stats_zone = ui_crop1.crop((10, 250, 580, 300))
    aptitude_zone = ui_crop1.crop((133, 310, 567, 410))
    #aptitude_zone.save("zzzz.png")
    #stats_zone.save("zz.png")
else:
    name_zone = ui_crop1.crop((285, 50, 530, 100))
    skills_zone = ui_crop1.crop((0, 470, 580, 925))
    stats_zone = ui_crop1.crop((10, 250, 580, 300))
    aptitude_zone = ui_crop1.crop((133, 310, 567, 410))
    #aptitude_zone.save("zzzz.png")


# ================================ Debugging ================================
#skills = find_boxes(skills_zone, offset=35)
#aptitude = find_boxes(aptitude_zone, 83, 123, 20, 40, 70)
#skills_zone.save("zkill_crop.png")
#stats = find_boxes(stats_zone)
mood_zone = process_img3_2(img2)
#mood = find_boxes(mood_zone)

for i in range(6):
    y = 0 + (i * 120)
    rows = mood_zone.crop((0, y, 561, y + 105))
    boxes = find_boxes(rows, 45, 103, 25, 45)
    rows.save(f"zmood_{i+1}.png")

    for box_idx, (x, y2, w, h) in enumerate(boxes):
        crop = rows.crop((x, y2, x + w, y2 + h))
        crop.save(f"mood_1_{i+1}.png")

mood_coords = {
    1 : (0, 0, 561, 90),
    2 : (0, 100, 561, 200),
    3 : (0, 220, 561, 320),
    4 : (0, 340, 561, 440),
    5 : (0, 460, 561, 560),
    6 : (0, 580, 561, 680)
}

for row_num, coords in mood_coords.items():
    rows = mood_zone.crop(coords)
    boxes = find_boxes(rows, 45, 103, 25, 45)

    for x, y, w, h in boxes:
        mood_crop = rows.crop((x, y, x + w, y + h))
        mood_crop.save(f"mood_2_{row_num}.png")

#mood1.save("zmood_1.png")
#mood2.save("zmood_2.png")
#mood3.save("zmood_3.png")
#mood4.save("zmood_4.png")
#mood5.save("zmood_5.png")
#mood6.save("zmood_6.png")
#find_boxes(mood1)