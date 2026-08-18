from PIL import Image
import cv2
import numpy as np
from rapidfuzz import process
import json
import re

img1 = Image.open("photo/cm14/round1/detail/race1/Screenshot 2026-06-05 173640.png") #skill_img

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

# ============================ Box Detection ============================

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
    aptitude_zone.save("zzzz.png")
    stats_zone.save("zz.png")
else:
    name_zone = ui_crop1.crop((285, 50, 530, 100))
    skills_zone = ui_crop1.crop((0, 470, 580, 925))
    stats_zone = ui_crop1.crop((10, 250, 580, 300))
    aptitude_zone = ui_crop1.crop((133, 310, 567, 410))
    aptitude_zone.save("zzzz.png")

# ================================ Debugging ================================
#boxes = find_boxes(skills_zone)
aptitude = find_boxes(aptitude_zone, 83, 123, 20, 40, 70)
"""print(len(boxes))
print(boxes)"""
skills_zone.save("zkill_crop.png")
