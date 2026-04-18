import requests
import json
from bs4 import BeautifulSoup

url = "https://game8.co/games/Umamusume-Pretty-Derby/archives/535926"
response = requests.get(url)

print(response.status_code)

soup = BeautifulSoup(response.text, "html.parser")
headers = soup.find_all("h3", string=lambda t: t and "Star Characters" in t)
headers_ = soup.find_all("h3", string=lambda t: t and "Featured Spotlight Characters" in t)
header = soup.find
character = []

for i in headers_:
    i.text
    tables = i.find_next_sibling("table")
    links = tables.find_all("a", class_="a-link")

    for link in links:
        if link["href"].startswith("https://"):
            character.append({
                "name": link.text,
                "url": link["href"],
                "base_star": "3"
            })

for h in headers:
    h.text.split()
    h.text.split()[3]
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
    url = j["url"]
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    unique_skill = soup.find("h3", string=lambda t: t and "Unique Skill" in t)
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

with open("character.json", "w") as f:
    json.dump(character, f, indent=2)

print("Done!")

# Data sourced from game8 ("https://game8.co/games/Umamusume-Pretty-Derby/archives/535926")