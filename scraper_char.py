import requests
import json
from bs4 import BeautifulSoup

url = "https://game8.co/games/Umamusume-Pretty-Derby/archives/535926"

ua_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=ua_headers)
print(response.status_code)

soup = BeautifulSoup(response.text, "html.parser")
h3_stars = soup.find_all("h3", string=lambda t: t and "Star Characters" in t)
h3_featured = soup.find_all("h3", string=lambda t: t and "Featured Spotlight Characters" in t)

character = []

for i in h3_featured:
    tables = i.find_next_sibling("table")
    links = tables.find_all("a", class_="a-link")
    for link in links:
        if link["href"].startswith("https://"):
            character.append({
                "name": link.text,
                "url": link["href"],
                "base_star": "3"
            })

for h in h3_stars:
    star = h.text.split()[3].split("-")[0]
    tables = h.find_next_sibling("table")
    links = tables.find_all("a", class_="a-link")
    for link in links:
        if link["href"].startswith("https://"):
            character.append({
                "name": link.text,
                "url": link["href"],
                "base_star": star
            })

for j in character:
    char_url = j["url"]
    response = requests.get(char_url, headers=ua_headers)
    soup = BeautifulSoup(response.text, "html.parser")
    unique_skill = soup.find("h3", string=lambda t: t and "Unique Skill" in t)
    if unique_skill is None:
        print(f"Unique skill not found for: {j['name']}")
        continue
    tables = unique_skill.find_next_sibling("table")
    rows = tables.find_all("tr")
    if len(rows) == 1:
        unique_skill = rows[0].find("a", class_="a-link").text.strip()
        j["unique_skill"] = unique_skill
    else:
        unique_skill = rows[0].find("a", class_="a-link").text.strip()
        unique_skill_evolved = rows[1].find("a", class_="a-link").text.strip()
        j["unique_skill"] = unique_skill
        j["unique_skill_evolved"] = unique_skill_evolved

with open("data/raw/character.json", "w", encoding="utf-8") as f:
    json.dump(character, f, indent=2, ensure_ascii=False)

print("Done!")