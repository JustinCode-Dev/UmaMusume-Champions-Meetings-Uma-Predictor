import json

with open("data/raw/skills.json", "r", encoding="utf-8") as f:
    skills_data = json.load(f)

skill_rarity = {s["name"]: s["rarity"] for s in skills_data}

with open("data/raw/style_skill.json", "r", encoding="utf-8") as s:
    data_style_skills = json.load(s)

all_style_skills = {style: set(skills) for style, skills in data_style_skills.items()}

def get_distance(uma, rules):
    distance_input = uma["distance"]
    distance_score = {}
    for dist, rank in distance_input.items():
        score = rules["scoring"]["performance_score"]["distance"][rank]
        distance_score[dist] = score
    return distance_score
    
def get_track(uma, rules):
    track_input = uma["track"]
    track_score = {}
    for track, rank in track_input.items():
        score = rules["scoring"]["performance_score"]["track"][rank]
        track_score[track] = score
    return track_score

def get_style_score(uma, rules):
    style_input = uma["style"]
    style_score = {}
    for style, rank in style_input.items():
        score = rules["scoring"]["performance_score"]["style"][rank]
        style_score[style] = score
    return style_score

def get_skills(uma):
    return [skill["name"] for skill in uma["skills"]]

def is_debuffer(uma):
    debuff = all_style_skills.get("debuff", set())
    input_skills = set(get_skills(uma))
    yellow_skills = set()
    for style, skills in all_style_skills.items():
        if style != "debuff":
            yellow_skills.update(skills)

    yellow_count = len(input_skills & yellow_skills)
    debuff_count = len(input_skills & debuff)    

    if debuff_count > yellow_count:
        return True
    return False

def get_name(uma):
    return uma["name"]

def get_stats(uma):
    return uma["stats"]

def get_stats_modified(uma, rules):
    mood = uma["mood"].lower()
    mood_modifier = rules["mood_modifier"][mood]

    new_stats = {}
    for stats_name, stats_value in uma["stats"].items():
        calculated_value = int(stats_value) * mood_modifier
        new_stats[stats_name] = int(calculated_value)

    return new_stats

def get_skill_level(uma):
    return uma["skill_level"]

def get_mood_score(uma, rules):
    mood = uma["mood"].lower()
    return rules["scoring"]["performance_score"]["mood"][mood]

def get_rank(uma):
    return uma["rank"]

def get_main_style(uma, rules):
    if "main_style" in uma:
        return uma["main_style"]
    
    skills = set(get_skills(uma))
    style_scores = get_style_score(uma, rules)
    candidates = [style for style, score in style_scores.items() if score >= 9]
    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        style_count = {}
        for candidate in candidates:
            style_skills = all_style_skills.get(candidate, set())
            style_count[candidate] = len(skills & style_skills)

        if max(style_count.values()) == 0:
            return max(candidates, key=lambda c: style_scores[c])
            
        return max(style_count, key=style_count.get)

# =========================================== CM Data ===========================================

def get_cm_track_distance_info(uma, rules):
    cm_id = str(uma["cm_id"])
    cm_info = rules["cm"][cm_id]
    key = ["track", "distance"]
    tr_ds_cm = [cm_info[k] for k in key]
    return tr_ds_cm

def get_race_info(uma):
    round = uma["round"]
    race = uma["race_no"]
    cm_id = uma["cm_id"]
    return f"{race}_{round}_{cm_id}"

# ============================================ Main ============================================
def extract_skills(uma, rules, frequent_skill, train=True):
    features = {}

    uma_skills = set(get_skills(uma))

    for all_skill in frequent_skill:
        features[all_skill] = 1 if all_skill in uma_skills else 0

    features["skill_level"] = get_skill_level(uma)

    main_style = get_main_style(uma, rules)
    
    for style in ["front_runner", "pace_chaser", "late_surger", "end_closer"]:
        features[f"main_{style}"] = 1 if style == main_style else 0

    for stat, value in get_stats(uma).items():
        features[stat] = value

    for stat_name, stats_value in get_stats_modified(uma, rules).items():
        features[f"{stat_name}_modified"] = stats_value

    if train == True:
        features["rank"] = get_rank(uma)

    return features

def extract_conditions(uma, rules, train=True):
    features = {}
    
    features["mood"] = get_mood_score(uma, rules)
    
    if train == True:
        features["rank"] = get_rank(uma)

    debuffer = is_debuffer(uma)
    features["debuffer"] = 1 if debuffer is True else 0

    main_style = get_main_style(uma, rules)
    style_scores = get_style_score(uma, rules)
    for dist, score in get_distance(uma, rules).items():
        features[dist] = score
    for track, score in get_track(uma, rules).items():
        features[track] = score
    for style, score in style_scores.items():
        features[style] = score
    for style in ["front_runner", "pace_chaser", "late_surger", "end_closer"]:
        features[f"main_{style}"] = 1 if style == main_style else 0
    for stat, value in get_stats(uma).items():
        features[stat] = int(value)

    info = get_cm_track_distance_info(uma, rules)
    track = ["turf", "dirt"]
    distance = ["sprint", "mile", "medium", "long"]
    for dist in distance:
        features[f"is_{dist}"] = 1 if info[1] == dist else 0
    for tr in track:
        features[f"is_{tr}"] = 1 if info[0] == tr else 0
    return features