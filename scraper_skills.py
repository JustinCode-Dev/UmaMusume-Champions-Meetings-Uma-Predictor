import json
import os
import re
import shutil
import requests
from bs4 import BeautifulSoup

URL = "https://game8.co/games/Umamusume-Pretty-Derby/archives/535927"
FILEPATH = "data/raw/skills.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def main():
    os.makedirs(os.path.dirname(FILEPATH), exist_ok=True)

    if os.path.exists(FILEPATH):
        shutil.copy(FILEPATH, FILEPATH + ".bak")
        print("Backup old data to skills.json.bak")

    try:
        response = requests.get(URL, headers=HEADERS, timeout=20)
    except requests.RequestException as e:
        print(f"Request error: {e}. Scraping stopped.")
        return

    if response.status_code != 200:
        print(f"Status {response.status_code}. Scraping stopped.")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table")

    if len(tables) < 6:
        print(f"Table less than 6 (found {len(tables)}), old web's structure might be changed. Stopped.")
        return

    rarity_tables = [
        (tables[3], "unique skill"),
        (tables[4], "rare skill"),
        (tables[5], "normal skill"),
    ]

    skills = []
    seen_names = set()

    for table, rarity in rarity_tables:
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) != 2:
                continue

            name = cols[0].get_text(strip=True)
            effect = cols[1].get_text(strip=True)

            if name in seen_names:
                continue
            seen_names.add(name)

            skills.append({
                "name": name,
                "effect": effect,
                "rarity": rarity,
            })

    with open(FILEPATH, "w", encoding="utf-8") as f:
        json.dump(skills, f, indent=2, ensure_ascii=False)

    print(f"Done! Successfully overwrite with new data. Total {len(skills)} skill saved to {FILEPATH}.")

if __name__ == "__main__":
    main()

# Data sourced from game8 (https://game8.co/games/Umamusume-Pretty-Derby/archives/535927)