import requests
import json
from bs4 import BeautifulSoup

url = "https://game8.co/games/Umamusume-Pretty-Derby/archives/535927"
response = requests.get(url)

print(response.status_code)

soup = BeautifulSoup(response.text, "html.parser")
tables = soup.find_all("table")
print(len(tables))

skills = []

for table in [tables[3], tables[4], tables[5]]:
    rows = table.find_all("tr")
for row in rows:
    cols = row.find_all("td")
    if len(cols) == 2:
        nama = cols[0].get_text(strip=True)
        effect = cols[1].get_text(strip=True)
        skills.append({"name": nama, "effect": effect})

with open("skills.json", "w") as f:
    print(len(skills))
    json.dump(skills, f, indent=2)

print("Done!")

# Data sourced from game8 (https://game8.co/games/Umamusume-Pretty-Derby/archives/535927)