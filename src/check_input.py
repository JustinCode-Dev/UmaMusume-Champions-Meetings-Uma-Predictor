from data_loader import data_load
import sys

sys.stdout.reconfigure(encoding="utf-8")

all_data = data_load(["cm21_input"], check=True)
keywords = ["unknown", "unsure", "none", "null"]

def search_items(all_data, keywords):
    for item in all_data:
        data = item.get("data") or {}
        filename = item.get("filename", "unknown")
        mood_raw = data.get("mood")
        main_style_raw = data.get("main_style")
        rank_raw = data.get("rank")

        has_error = False
        
        if rank_raw is None or rank_raw == "":
            print(f"Warning : Missing rank in \n{filename}")
            has_error = True

        if mood_raw is None or main_style_raw is None or mood_raw == "" or main_style_raw == "":
            print(f"Warning : Missing mood/Main_style in \n{filename}")
            has_error = True
        else:
            mood = str(mood_raw).lower()
            main_style = str(main_style_raw).lower()
            if any(kw in mood for kw in keywords) or any(kw in main_style for kw in keywords):
                print(f"Warning : Missing mood/Main_style in \n{filename}")
                has_error = True

        for skill in data.get("skills", []):
            skill_name = (skill.get("name") or "").lower()
            if any(kw in skill_name for kw in keywords):
                print(f"Warning : Wrong skill in \n{filename}")
                has_error = True
                break
        if not has_error:
            print(f"Clean : {filename} - No error found.")
    return

search_items(all_data, keywords)