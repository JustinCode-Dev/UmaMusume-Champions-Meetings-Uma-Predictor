import requests
import json
from bs4 import BeautifulSoup, Tag, NavigableString

url = "https://game8.co/games/Umamusume-Pretty-Derby/archives/591865"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)

print(response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

name_node = soup.find("h2", class_="a-header--2")
name = name_node.get_text().replace(" Race Info", "").strip() if name_node else "Unknown Cup"
print("name:", name)

tds = soup.find_all("td", class_="center")
baseline_stats = {}
track = distance = direction = course = season = weather = ground = "Unknown"

if len(tds) >= 11:
    lines = tds[5].get_text(separator="\n").split("\n")
    lines = [l.strip() for l in lines if l.strip()]
    if len(lines) >= 6:
        course = lines[2]
        track_info = lines[3] 
        track = track_info.split()[0]
        if "(" in track_info and ")" in track_info:
            distance = track_info.split("(")[1].split(")")[0]
        direction = track_info.split(",")[-1].strip()
        season = lines[4].replace(",", "").strip()
        weather_ground = lines[5].split(",")
        weather = weather_ground[0].strip()
        if len(weather_ground) > 1:
            ground = weather_ground[1].strip().replace(" Ground", "")

    stat_names = ["speed", "stamina", "power", "guts", "wit"]
    for i, stat in enumerate(stat_names):
        if 6+i < len(tds):
            value = tds[6+i].get_text().strip()
            if "-" in value:
                value = value.split("-")[-1]
            try:
                baseline_stats[stat] = int(value)
            except:
                baseline_stats[stat] = 0

priority_text = soup.find(string=lambda t: t and "Prioritize maximizing stats" in t)
stat_priority = []
if priority_text and priority_text.parent:
    links = priority_text.parent.find_all("a")
    for link in links:
        stat_priority.append(link.get_text().strip().lower())

print("stat_priority:", stat_priority)

fix_uma_names = {
    "Symboli Rudolf (Emperor": "Symboli Rudolf (Emperor's Path)",
    "Special Week (Hopp": "Special Week (Hopp'n♪Happy Heart)"
}
rows = soup.find_all("tr")
uma_tier = {}
for row in rows:
    th = row.find("th")
    if th:
        img = th.find("img")
        if img and "Rank" in img.get("alt", ""):
            tier = img.get("alt").replace(" Rank", "")
            uma_tier[tier] = []  
            td = row.find("td")
            if td:
                for uma_img in td.find_all("img"):
                    uma_name = uma_img.get("alt", "").strip()
                    if uma_name in fix_uma_names:
                        uma_name = fix_uma_names[uma_name]
                    if uma_name:
                        uma_tier[tier].append(uma_name)

def get_skills_by_section(soup, section_type):
    keywords = []
    if section_type == "green":
        keywords = ["green skill", "track-based"]
    elif section_type == "yellow":
        keywords = ["speed and accel", "speed & accel", "speed/accel", "yellow skill", "speed skill", "acceleration skill"]
    elif section_type == "blue":
        keywords = ["recovery skill", "blue skill"]
    elif section_type == "red":
        keywords = ["red skill", "debuff skill"]
        
    tables = []
    for kw in keywords:
        headings = soup.find_all(["h2", "h3", "h4"], string=lambda t: t and kw.lower() in t.lower())
        for h in headings:
            t = h.find_next("table")
            if t and t not in tables:
                prev_h = t.find_previous(["h2", "h3", "h4"])
                if prev_h == h:
                    tables.append(t)

    if section_type == "red":
        debuff_list = []
        for table in tables:
            for link in table.find_all("a"):
                sn = link.get_text().strip()
                if sn and sn != "/" and len(sn) > 2:
                    sn = sn.split(" (")[0]
                    if sn not in debuff_list:
                        debuff_list.append(sn)
        return debuff_list

    if section_type == "green":
        skills_data = {"track_based": [], "style_based": []}
        for table in tables:
            td = table.find("td")
            if not td: continue
            current_key = "track_based"
            for node in td.contents:
                if isinstance(node, str) and node.strip():
                    text = node.strip().lower()
                    if "track-based" in text:
                        current_key = "track_based"
                    elif "racer-based" in text or "style" in text:
                        current_key = "style_based"
                elif getattr(node, "name", None) in ["a", "div"]:
                    links = node.find_all("a") if node.name == "div" else [node]
                    for link in links:
                        sn = link.get_text().strip()
                        if sn and sn != "/" and "style" not in sn.lower() and len(sn) > 2:
                            sn = sn.split(" (")[0]
                            if sn not in skills_data[current_key]:
                                skills_data[current_key].append(sn)
        return skills_data

    skills_data = {
        "all_style": [],
        "front_runner": [],
        "pace_chaser": [],
        "late_surger": [],
        "end_closer": []
    }

    for table in tables:
        current_keys = ["all_style"]
        
        for node in table.descendants:
            if getattr(node, "name", None) == "a":
                sn = node.get_text().strip()
                if (sn and sn != "/" and 
                    "style" not in sn.lower() and 
                    "mandatory" not in sn.lower() and len(sn) > 2):
                    
                    if " (" in sn:
                        sn = sn.split(" (")[0]
                    for tk in current_keys:
                        if sn not in skills_data[tk]:
                            skills_data[tk].append(sn)
                            
            elif isinstance(node, str) and node.strip():
                parent = getattr(node, "parent", None)
                if parent and parent.name == "a":
                    continue
                    
                text = node.strip().lower()
                if "all style" in text or "all:" in text or text == "all":
                    current_keys = ["all_style"]
                elif "front runner" in text or "front:" in text or text == "front":
                    current_keys = ["front_runner"]
                elif "pace chaser" in text or "pace:" in text or text == "pace":
                    current_keys = ["pace_chaser"]
                elif "late/end" in text:
                    current_keys = ["late_surger", "end_closer"]
                elif "late surger" in text or "late:" in text or text == "late":
                    current_keys = ["late_surger"]
                elif "end closer" in text or "end:" in text or text == "end":
                    current_keys = ["end_closer"]

    return skills_data

cm_data = {
    "name": name,
    "track": track,
    "distance": distance,
    "course": course,
    "direction": direction,
    "season": season,
    "weather": weather,
    "ground": ground,
    "baseline_stats": baseline_stats,
    "stat_priority": stat_priority,
    "recommended_skills": {
        "char_specific": {},
        "green": get_skills_by_section(soup, "green"),
        "yellow": get_skills_by_section(soup, "yellow"),
        "blue": get_skills_by_section(soup, "blue"),
        "debuff": get_skills_by_section(soup, "red")
    },
    "uma_tier": uma_tier
}

with open("data/raw/cm_data/cm_13.json", "w") as f:
    json.dump(cm_data, f, indent=2)

print("Done!")