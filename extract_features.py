import json

with open("data/raw/rule.json", "r") as f:
    rules = json.load(f)

with open("data/raw/skills.json", "r", encoding="utf-8") as f:
    skills_data = json.load(f)
skill_names = [s["name"] for s in skills_data]

with open("data/raw/style_skill.json", "r", encoding="utf-8") as s:
    data_style_skills = json.load(s)

all_style_skills = {style: set(skills) for style, skills in data_style_skills.items()}

def get_tier_score(uma, rules, cm_data):
    name = uma["name"]
    for tier, names in cm_data["uma_tier"].items():
        if name in names:
            score = rules["scoring"]["performance_score"]["uma_tier"][tier]
            return score
    return 0

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

def get_all_skills_cm(cm_data):
    return{
    "yellow" : [yellow_skills for sublist in cm_data["recommended_skills"]["yellow"].values() for yellow_skills in sublist],
    "green" : [green_skills for sublist in cm_data["recommended_skills"]["green"].values() for green_skills in sublist],
    "blue" : [blue_skills for sublist in cm_data["recommended_skills"]["blue"].values() for blue_skills in sublist],
    "debuff" : cm_data["recommended_skills"]["debuff"]
    }

def is_debuffer(uma):
    debuff = all_style_skills.get("debuff", set())
    input_skills = set(uma["skills"])
    yellow_skills = set()
    for style, skills in all_style_skills.items():
        if style != "debuff":
            yellow_skills.update(skills)

    yellow_count = len(input_skills & yellow_skills)
    debuff_count = len(input_skills & debuff)    

    if debuff_count > yellow_count:
        return True
    return False

def get_stats(uma):
    return uma["stats"]

def get_skill_level(uma):
    return uma["skill_level"]

def get_mood_score(uma, rules):
    mood = uma["mood"]
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
            return max(candidate, key=lambda c: style_scores[c])
            
        return max(style_count, key=style_count.get)

# ============================================ Main ============================================

def extract(uma, cm_data, training=True):
    features = {}
    features["tier"] = get_tier_score(uma, rules, cm_data)
    features["skill_level"] = get_skill_level(uma)
    style_scores = get_style_score(uma, rules)

    for dist, score in get_distance(uma, rules).items():
        features[dist] = score

    for track, score in get_track(uma, rules).items():
        features[track] = score

    for style, score in style_scores.items():
        features[style] = score

    features["mood"] = get_mood_score(uma, rules)
    features["debuffer"] = is_debuffer(uma, cm_data)

    for stat, value in get_stats(uma).items():
        features[stat] = value

    main_style = get_main_style(uma, rules, cm_data)

    for style in ["front_runner", "pace_chaser", "late_surger", "end_closer"]:
        features[f"main_{style}"] = 1 if style == main_style else 0

    all_recommended = get_all_skills_cm(cm_data)
    uma_skills = get_skills(uma)

    for all_skill in skill_names:
        features[all_skill] = 1 if all_skill in uma_skills else 0

    for category in ["green", "yellow", "blue", "debuff"]:
        for skill in all_recommended[category]:
            features[skill] = 1 if skill in uma_skills else 0
    if training:
        features["rank"] = get_rank(uma)
    return features