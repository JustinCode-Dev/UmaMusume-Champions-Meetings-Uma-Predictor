# Uma Musume CM Reviewer Pipeline Architecture

This document explains the architecture of the end-to-end data processing and machine learning pipeline for this project.

## Overview

![Uma CM Reviewer Main WorkFlow](../assets/main_dark.excalidraw.png#gh-dark-mode-only)
![Uma CM Reviewer Main WorkFlow](../assets/main_light.excalidraw.png#gh-light-mode-only)

## Image Preprocessing
### 1. Box Detection
**Problem**: CRNN models cannot process a full screenshot efficiently in one shot. Hardcoded pixel positions also break whenever the UI shifts slightly.

**Approach**: Uses `OpenCV's` `morphologyEx` to dynamically detect UI bounding boxes, filtering by width and height to handle elements of different sizes.

```python
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
```

### 2. Optical Character Recognition (OCR) & Text Correction
**Problem**: Raw text outputs from CRNN model sometimes contains minor reading errors or misregocnized characters.

**Approach**: Each cropped image is passed to a CRNN model to extract raw text. The extracted stings is then matched against predefined reference lists using `RapidFuzz` to automatically correct typos.

```python
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
```

> **Note**: For name in mood and rank images, the extraction uses `token_set_ratio` instead of `Wratio`.
```python
name_text = ocr_with_fuzzy(name, model, val_transform, idx_to_char,device, char_names_outer, threshold=75, score_choice=fuzz.token_set_ratio)
```

## Matching Data
**Problem**: Data extracted from three different images must be consolidated into a single dictionary per character before being exported to a JSON file.

**Approach**: The pipeline ingests targeted screenshots per character to capture all necessary UI elements:
* **Image 1 (Character Detail Screen)**: Captures stats, aptitude, character name, and skills.
* **Image 2 (Mood Detail Screen)**:  Captures character name, mood, trainer name, and favorite number.
* **Image 3 (Rank/Placement Screen)**: Captures character name, trainer name, favorite number, and rank/placement.
  
**Consolidation Strategy**:
* **Entity Aggregation**: 
  * Uses character name, and stats for image 1 to verify if the character between others image 1 is the same character, before merging skills name into one set.
  * Combines character name and favorite number to connect mood and rank images.
  * Cross-checks character name and trainer name to link Image 1 with the merged Image 2/3 dataset, before merging both datasets into one list, containing character name, stats, skill, aptitudes, mood, and rank.
* **Skill Merging**: Appends skill entries from multiple detail screenshots into a unified skill set to automatically handle duplicates.

## Machine Learning

### 1. Feature Extraction
- **Categorical Data**: One-Hot Encoding, Multi-Hot Encoding or Ordinal Encoding.
- **Stats**: Uses raw numerical values without scaling.
  
### 2. Model Training & Validation

* **K-Fold Cross-Validation**: Validates model performance across multiple splits to prevent overfitting.
* **Feature Subspace Stacking**: Trains separate models with different feature combinations.
  * **Problem**: High-Dimensional Data and Sparse Features make it harder for the model to capture the correlation.
  * **Approach**: Uses Feature Subspace Stacking, letting distinct models handle different feature subsets to maintain an optimal column-to-row ratio.
  * **Base Model**: Trains LightGBM on skills and stats features, and XGBoost on stats and conditions features.
  * **Meta Model**: Uses a simple linear model such as Logistic Regression to combine predictions and prevent overfitting.

## File Structure

```
UmaMusume-Champions-Meetings-Uma-Predictor/
├── assets/
│   ├── Uma_Banner.png
│   ├── favicon_uma.png
│   ├── main_dark.excalidraw.png
│   └── main_light.excalidraw.png
├── data/
│   ├── raw/
│   │   └── input/
│   │       └── cm12_input/ ... cm21_input/
│   ├── character.json      #(not pushed — scraped via scraping/scraper_char.py)
│   ├── frequent_skill.json
│   ├── rule.json
│   ├── skills.json      #(scraped via scraping/scraper_skills.py)
│   └── style_skill.json
├── docs/
│   └── ARCHITECTURE.md
├── model/
│   ├── ml/
│   │   ├── lgb_model.pkl
│   │   ├── meta_model.pkl
│   │   └── xgb_model.pkl
│   └── ocr/
│       └── UmaOCR_v6.pth
├── photo/
│   └── cm14/ ... cm21/      #(not pushed — 7.9k+ manually collected race screenshots)
├── scraping/
│   ├── scraper_char.py
│   └── scraper_skills.py
├── src/
│   ├── build_skill_list.py
│   ├── check_input.py
│   ├── converter.py
│   ├── crnn.py
│   ├── data_converter.py
│   ├── data_loader.py
│   ├── extract_features.py
│   └── ml.py
├── tools/
│   ├── eval.py
│   └── scan_data.py
├── uma_data/
│   ├── images/      #(not pushed — 75k+ cropped images for ocr training data)
│   └── labels_dl.csv      #(not pushed — generated by src/converter.py)
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```