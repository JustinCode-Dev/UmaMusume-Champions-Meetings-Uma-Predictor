# UmaMusume Champions Meeting Uma Predictor

![Umamusume Champions Meetings Reviewer](assets/Uma_Banner.png)

---
Introducing **UmaMusume CM Uma Predictor**, a project exploring whether 
historical race data can predict how an Uma will place in a Champions 
Meeting race.

## Why I Made This
Every time a new Champions Meeting drops, the meta shifts drastically. Opponents just keep getting stronger, which leaves casual and F2P players like me struggling to keep up. This frustration led me to explore a few different questions:
  - Can this problem be framed as a machine learning task?
  - UmaMusume races are pretty random (skill trigger timing, AI rival behavior, starting position). Can historical race data still predict finishing position well, or does the randomness make that too hard?
  - How accurate can a prediction model actually get for this?
  
## Installation / Running This Yourself
> **Note:** This repo isn't really meant to be cloned and run end-to-end. The OCR pipeline (cropping, preprocessing, data matching), expects screenshots in a specific format, it won't work with arbitrary images. It also depends on a personal dataset of 7,900+ manually collected race screenshots (2.4GB+) that isn't included here due to size. The code is here mainly for people who want to see how it works, not to be run as a plug-and-play tool.

- **Want to try the predictor?** → [Live Demo](https://umamusume-cm-predictor.streamlit.app/)
  
  **What do the ranks mean?**
  - Rank 1 → Finishing 1st place
  - Rank 2 → Finishing 2nd–3rd place
  - Rank 3 → Finishing 4th–6th place
  - Rank 4 → Finishing 7th–9th (unranked)

- **Want to run predictions locally (without the full pipeline)?** → the trained predictor models (~13MB) are included in `/model/ml`:
  
1. Clone the repository
    ```bash
    git clone https://github.com/JustinCode-Dev/  UmaMusume-Champions-Meetings-Uma-Predictor.git
    cd UmaMusume-Champions-Meetings-Uma-Predictor
    ```
2. Create a virtual environment
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```
3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app
    ```bash
    streamlit run app.py
    ```

# WorkFlow

## 🧩 How It Works

![Uma CM Reviewer Main WorkFlow](assets/main_dark.excalidraw.png#gh-dark-mode-only)
![Uma CM Reviewer Main WorkFlow](assets/main_light.excalidraw.png#gh-light-mode-only)

- **✂️ Image Preprocessing** — Hardcoded pixel positions broke whenever a screenshot shifted a bit. So I use `OpenCV's` `morphologyEx` to find the boxes (skills, aptitude, etc.) and crop with their coordinates, plus a small offset for a cleaner result. Now the crop stays precise whenever the UI sits.
   
- **✒️ Image Processing (OCR)** — Each crop is read by CRNN model, which returns raw text. Names (skills, characters, moods) are then matched against reference lists with `RapidFuzz` to fix small reading errors. The results are stored per category (detail, mood, rank).

- **🔍 Matching Data** — Info about uma (character) is spread across several screenshots. The pipeline links them by name, stats, and favorite number. then merges them into one profile per uma (character). Each profile is saved as structured JSON.
  
- **📖 Feature Extraction** — Raw JSON data is manually parsed and transformed into feature vectors using custom python mapping logic (e.g `Multi-hot encoding` for skills, `One-hot encoding` for main style, `Ordinal encoding` for aptitude, etc.) without relying on automated processing pipelines.

- **🧠 Machine Learning** — Trained on thousands of umas' race records, including rank, stats, skills, race condition, etc. I use `Feature Subspace Stacking` method with 2 base models `(LightGBM and XGBoost)` and a meta model `(LogisticRegression)`, to handle `High-Dimensional Data`.

## 📁 Documentation
For a detailed explaination, check out the [Architecture Documentation](docs/ARCHITECTURE.md)

## About This Project
I'm a self-taught programmer, and this project is basically how I learned to code. I spent around 7 months building it from scratch. I designed the pipeline, the matching logic, and the data cleaning workflow myself, and used AI as a mentor for syntax questions and picking the right library functions (OpenCV, PyTorch).

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

> **Disclaimer:** This is an unofficial, non-commercial fan project. *Uma Musume: Pretty Derby* and all associated assets, character names, and logos are trademarks/copyrights of Cygames, Inc.