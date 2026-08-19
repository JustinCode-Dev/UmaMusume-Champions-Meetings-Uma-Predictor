import requests
import json
from bs4 import BeautifulSoup

url = "https://game8.co/games/Umamusume-Pretty-Derby/archives/535927"
response = requests.get(url)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)
print(response.status_code)
print(len(response.text))
soup = BeautifulSoup(response.text, "html.parser")
tables = soup.find_all("table")
print(f"Tables found: {len(tables)}")


skills = []

for table, rarity in zip ([tables[3], tables[4], tables[5]], ["special skill", "rare skill", "normal skill"]):
    rows = table.find_all("tr")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) == 2:
            nama = cols[0].get_text(strip=True)
            effect = cols[1].get_text(strip=True)
            skills.append({"name": nama, "effect": effect, "rarity": rarity})

with open("data/raw/skills.json", "w", encoding="utf-8") as f:
    json.dump(skills, f, indent=2, ensure_ascii=False)
    print(len(skills))

print("Done!")

# Data sourced from game8 (https://game8.co/games/Umamusume-Pretty-Derby/archives/535927)