import requests
import json
from bs4 import BeautifulSoup

url = "https://game8.co/games/Umamusume-Pretty-Derby/archives/535926"
response = requests.get(url)

print(response.status_code)

soup = BeautifulSoup(response.text, "html.parser")
class_char = soup.find_all("a", class_="a-link")

character = []

for i in class_char:
    if i["href"].startswith("https://"):
        nama = i.text
        url = i["href"]
        character.append({"name": nama, "url": url})

for j in character:
    url = j["url"]
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    unique_skill = soup.find("h3", string=lambda t: t and "Unique Skill" in t)
    tables = unique_skill.find_next_sibling("table")
    skills = tables.find("a", class_="a-link")
    j["unique_skill"] = skills.text.strip()

with open("character.json", "w") as f:
    json.dump(character, f, indent=2)

print("Done!")