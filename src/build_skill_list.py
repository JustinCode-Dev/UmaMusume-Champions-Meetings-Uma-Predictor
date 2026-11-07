from collections import Counter
import json

def build_skill_list(input_data, skill_rarity, threshold):
    counter = Counter()
    for uma in input_data:
        for skill in uma["skills"]:
            counter[skill["name"]] += 1

    frequent_skill = []

    for skill_name, count in counter.items():

        rarity = skill_rarity.get(skill_name, None)
        limit = threshold.get(rarity, 5)

        if count >= limit:
            frequent_skill.append(skill_name)

    with open("data/raw/frequent_skill.json", "w", encoding="utf-8") as f:
        json.dump(frequent_skill, f, ensure_ascii=False, indent=4)
   
    return frequent_skill
