import streamlit as st
import pandas as pd
from extract_features import extract_conditions, extract_skills
import json
import numpy as np
import joblib
import re
import os

st.set_page_config(
    page_title="Uma CM Reviewer",
    page_icon="assets/favicon_uma.png",
    layout="wide",
)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    div[data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlockBorderWrapper"] {
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlockBorderWrapper"] > div {
        height: 100% !important;
        flex-grow: 1 !important;
    }
    div[data-testid="column"] > div {
        height: 100% !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div > div {
        height: 100% !important;
        flex-grow: 1 !important;
        display: flex !important;
        flex-direction: column !important;
    }

    div[data-testid="stExpanderDetails"] {
        max-height: 270px !important;
        overflow-y: auto !important;
        padding-right: 10px !important;
    }
    
    /* Progress bar hasil rank */
    .rank-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
    }
    .rank-label {
        font-size: 13px;
        color: #8f93a2;
        min-width: 52px;
    }
    .rank-bar-bg {
        flex: 1;
        background-color: #2a2d3e;
        border-radius: 6px;
        height: 12px;
        overflow: hidden;
    }
    .rank-bar-fill {
        height: 12px;
        border-radius: 6px;
        transition: width 0.4s ease;
    }
    .rank-pct {
        font-size: 13px;
        font-weight: bold;
        min-width: 38px;
        text-align: right;
    }
    .block-container {
        padding-top: 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ======================================== Header ========================================

st.markdown("<h1 style='text-align:center; color:#ff4b72; margin-bottom:0;'>🐎 Uma Musume CM Reviewer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#8f93a2; margin-bottom:30px;'>Predict Your Uma's Win Probability in Champions Meetings</p>", unsafe_allow_html=True)

# ======================================== Input ========================================

with st.container(border=True):
    col_input, col_output= st.columns([1, 1.5])

# ========================================== Stats ==========================================

    with col_input:
    
        st.write("")
        st.subheader("📊 Input")
        tab_stats, tab_condition, tab_skills, tab_cm = st.tabs(["📊 Stats", "✨ Condition", "🔬 Skills", "🎠 CM Info"])

        with tab_stats:
            speed   = st.number_input("Speed",   min_value=0, max_value=1800, value=0, step=10)
            stamina = st.number_input("Stamina", min_value=0, max_value=1600, value=0, step=10)
            power   = st.number_input("Power",   min_value=0, max_value=1600, value=0, step=10)
            guts    = st.number_input("Guts",    min_value=0, max_value=1600, value=0, step=10)
            wit     = st.number_input("Wit",     min_value=0, max_value=1600, value=0, step=10)

# ======================================== Aptitude (3 sub-kolom) ========================================

        with tab_condition:

            st.write("##### 🧭 Distance")
            d1, d2, d3, d4 = st.columns(4)
            with d1:
                sprint = st.selectbox("Sprint", ["G","F","E","D","C","B","A","S"])
            with d2:
                mile   = st.selectbox("Mile",   ["G","F","E","D","C","B","A","S"])
            with d3: 
                medium = st.selectbox("Medium", ["G","F","E","D","C","B","A","S"])
            with d4:
                long  = st.selectbox("Long",   ["G","F","E","D","C","B","A","S"])

            st.write("##### 🏃 Style")
            s1, s2, s3, s4, s5 = st.columns(5)
            with s1:
                front_runner = st.selectbox("Front", ["G","F","E","D","C","B","A","S"])
            with s2:
                pace_chaser  = st.selectbox("Pace",  ["G","F","E","D","C","B","A","S"])
            with s3:
                late_surger  = st.selectbox("Late",  ["G","F","E","D","C","B","A","S"])
            with s4:
                end_closer   = st.selectbox("End",   ["G","F","E","D","C","B","A","S"])
            with s5:
                main_style = st.selectbox("Main Style", ["Front", "Pace", "Late", "End"])

            st.write("##### 🛣️ Track")
            t1, t2 = st.columns(2)
            with t1:
                turf = st.selectbox("Turf", ["G","F","E","D","C","B","A","S"])
            with t2:
                dirt = st.selectbox("Dirt", ["G","F","E","D","C","B","A","S"])    

            st.write("##### 🔥 Mood")
            mood = st.selectbox("Mood", ["GREAT", "GOOD", "NORMAL", "BAD"])

# ======================================== Skills Column ========================================

    with tab_skills:

        if "selected_skills" not in st.session_state:
            st.session_state.selected_skills = set()
        if "skills_reset_nonce" not in st.session_state:
            st.session_state.skills_reset_nonce = 0

        col_search, col_btn = st.columns([6, 2])

        with col_search:
            search_query = st.text_input("Search Skills", placeholder="Type to filter...", label_visibility="collapsed")

        with col_btn:
            btn_reset = st.button("Reset", use_container_width=True, type="primary")

        with open("data/raw/skills.json", "r", encoding="utf-8") as f:
            skills_data = json.load(f)

        skill_list = [s["name"] for s in skills_data]

        if btn_reset:
            st.session_state.selected_skills = set()
            st.session_state.skills_reset_nonce += 1   # bikin semua key checkbox jadi "baru"
            st.rerun()

        skill_filtered = [s for s in skill_list if search_query.lower() in s.lower()]

        def _on_skill_toggle(skill_name, widget_key):
            if st.session_state.get(widget_key, False):
                st.session_state.selected_skills.add(skill_name)
            else:
                st.session_state.selected_skills.discard(skill_name)

        with st.expander("📋 Select Skills From List", expanded=True):
            for skill in skill_filtered:
                widget_key = f"skill_{skill}_{st.session_state.skills_reset_nonce}"
                st.checkbox(
                    skill,
                    value=skill in st.session_state.selected_skills,
                    key=widget_key,
                    on_change=_on_skill_toggle,
                    args=(skill, widget_key),
                )

        skill_level = st.selectbox("Skill Level", [2, 3, 4, 5, 6])

        with tab_cm:
            cm_id = st.selectbox("CM Info", [14, 16, 17, 18, 19, 20, 21, 22, 23, 24])

# ======================================== Predict Button ========================================
with col_output:
    st.write("")
    predict = st.button("Predict Win Probability", use_container_width=True, type="primary")

# ======================================== Result (Probability) ========================================

if predict:
    uma_data = {
        "distance": {
          "sprint": sprint,
          "mile": mile,
          "medium": medium,
          "long": long
        },
        "track": {
          "turf": turf,
          "dirt": dirt
        },
        "style": {
          "front_runner": front_runner,
          "pace_chaser": pace_chaser,
          "late_surger": late_surger,
          "end_closer": end_closer
        },
        "stats": {
          "speed": speed,
          "stamina": stamina,
          "power": power,
          "guts": guts,
          "wit": wit
        },
        "skills": [{"name": skill} for skill in st.session_state.selected_skills], 
        "mood": mood,
        "skill_level": skill_level,
        "main_style": main_style,
        "cm_id": cm_id
    }

    def apply_shrinkage(proba, weird_event_rate, n_classes=4):
        predicted_class = np.argmax(proba)
        rate = weird_event_rate[predicted_class]
        proba_uniform = np.full(n_classes, 1 / n_classes)
        return (1 - rate) * proba + rate * proba_uniform
    
    # `weird_event_rate` measures how often the model's top-predicted class 
    # turned out wrong in a "surprising" way — i.e., it gave a low probability 
    # to the outcome that actually happened. Calculated once from the trained 
    # model's test-set results (see `calculate_weird_event_rate_per_class()` 
    # in src/ml.py). Used to shrink raw probabilities toward uniform when the 
    # model's top pick belongs to a historically unreliable class.

    weird_event_rate = {
       0: 0.4083,
       1: 0.2692,
       2: 0.3182,
       3: 0.1343,
    }

    def clean_name(c):
        c = (str(c).replace("◎", "_dbl")
                .replace("○", "_circ")
                .replace("×", "_x"))
        return re.sub(r'[^0-9a-zA-Z_]+', '_', c)

    with open("data/raw/rule.json", "r") as n:
        rules = json.load(n)

    with open("data/raw/frequent_skill.json") as f:
        frequent_skill = json.load(f)

    @st.cache_resource
    def load_models(file_sigs):
        lgb_model = joblib.load('model/ml/lgb_model.pkl')
        xgb_model = joblib.load('model/ml/xgb_model.pkl')
        lr_model = joblib.load('model/ml/meta_model.pkl')
        return lgb_model, xgb_model, lr_model

    model_files = ("model/ml/lgb_model.pkl", "model/ml/xgb_model.pkl", "model/ml/meta_model.pkl")

    file_sigs = tuple(os.path.getmtime(f) for f in model_files)

    lgb_model, xgb_model, lr_model = load_models(file_sigs)

    def run_inference(uma_data):

        feature_lgbm = extract_skills(uma_data, rules, frequent_skill, train=False)
        feature_xgb = extract_conditions(uma_data, rules, train=False)

        df_lgb = pd.DataFrame([feature_lgbm])
        df_xgb = pd.DataFrame([feature_xgb])

        orig_cols_lgb = list(df_lgb.columns)
        clean_cols_lgb = [f"f{i}_" + clean_name(c) for i, c in enumerate(orig_cols_lgb)]
        df_lgb.columns = clean_cols_lgb

        proba_1 = lgb_model.predict_proba(df_lgb)
        proba_2 = xgb_model.predict_proba(df_xgb)

        meta_input = np.hstack([proba_1, proba_2])
        final_proba = lr_model.predict_proba(meta_input)

        return final_proba
    
    raw_proba = run_inference(uma_data)[0]
    print(raw_proba)
    adjusted_proba = apply_shrinkage(raw_proba, weird_event_rate)
    print("ADJUSTED:", adjusted_proba)
    print("WEIRD_EVENT_RATE used:", weird_event_rate)

# ======================================== predict feature ========================================

    with col_output:
        with st.container(height= 200, border=True):
            st.write("### 🏆 Win Probability")

            model_output = run_inference(uma_data)

            rank_probs = {i + 1: float(p) for i, p in enumerate(model_output[0])}

            def bar_color(rank):
                if rank <= 2:   return "#4e8ef7", "#4e8ef7"  
                elif rank <= 3: return "#2ecc71", "#2ecc71"  
                else:           return "#e74c3c", "#e74c3c"  

            bars_html = ""
            for rank, prob in rank_probs.items():
                color, _ = bar_color(rank)
                pct = int(prob * 100)
                bars_html += f"""
                <div class="rank-row">
                    <span class="rank-label">Rank {rank}</span>
                    <div class="rank-bar-bg">
                        <div class="rank-bar-fill" style="width:{pct}%; background-color:{color};"></div>
                    </div>
                    <span class="rank-pct" style="color:{color};">{pct}%</span>
                </div>
                """
            st.markdown(bars_html, unsafe_allow_html=True)

        with st.container(height= 200, border=True):
            st.write("### 🏆 Adjusted Win Probability (RNG/Weird Condition)")
            rank_probs_adjusted = {i + 1: float(p) for i, p in enumerate(adjusted_proba)}

            def bar_color(rank):
                if rank <= 2:   return "#4e8ef7", "#4e8ef7"  
                elif rank <= 3: return "#2ecc71", "#2ecc71"  
                else:           return "#e74c3c", "#e74c3c"  

            bars_html = ""
            for rank, prob in rank_probs_adjusted.items():
                color, _ = bar_color(rank)
                pct = int(prob * 100)
                bars_html += f"""
                <div class="rank-row">
                    <span class="rank-label">Rank {rank}</span>
                    <div class="rank-bar-bg">
                        <div class="rank-bar-fill" style="width:{pct}%; background-color:{color};"></div>
                    </div>
                    <span class="rank-pct" style="color:{color};">{pct}%</span>
                </div>
                """
            st.markdown(bars_html, unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(
            "<p style='text-align:center; color:#8f93a2; font-size:13px;'>"
            "Enjoyed this tool? "
            "<a href='https://github.com/JustinCode-Dev/UmaMusume-Champions-Meetings-Reviewer' style='color:#ff4b72; text-decoration:none;'>⭐ Star on GitHub</a>"
            " — it means a lot!"
            "</p>",
            unsafe_allow_html=True
        )