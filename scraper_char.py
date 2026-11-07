import json
import os
import re
import shutil
import time
import requests
from bs4 import BeautifulSoup

URL = "https://game8.co/games/Umamusume-Pretty-Derby/archives/535926"
FILEPATH = "data/raw/character.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_soup(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
    except requests.RequestException as e:
        print(f"Request error: {url} ({e})")
        return None
    if response.status_code != 200:
        print(f"Failed ({response.status_code}): {url}")
        return None
    return BeautifulSoup(response.text, "html.parser")


def collect_links(heading, base_star):
    table = heading.find_next_sibling("table")
    if table is None:
        return []
    result = []
    for link in table.find_all("a", class_="a-link"):
        href = link.get("href", "")
        if href.startswith("https://"):
            result.append({
                "name": link.text,
                "url": href,
                "base_star": base_star,
            })
    return result


def get_star(heading_text):
    match = re.search(r"(\d)\s*-", heading_text)
    if match:
        return match.group(1)
    return None


def scrape_unique_skill(char):
    soup = get_soup(char["url"])
    if soup is None:
        return False

    heading = soup.find("h3", string=lambda t: t and "Unique Skill" in t)
    if heading is None:
        print(f"Unique skill not found: {char['name']}")
        return False

    table = heading.find_next_sibling("table")
    if table is None:
        print(f"Tabel unique skill not found: {char['name']}")
        return False

    names = []
    for row in table.find_all("tr"):
        link = row.find("a", class_="a-link")
        if link:
            names.append(link.text.strip())

    if not names:
        print(f"Unique skill's name is empty: {char['name']}")
        return False

    char["unique_skill"] = names[0]
    if len(names) >= 2:
        char["unique_skill_evolved"] = names[1]
    return True

def main():
    os.makedirs(os.path.dirname(FILEPATH), exist_ok=True)

    old_chars = []
    if os.path.exists(FILEPATH):
        with open(FILEPATH, "r", encoding="utf-8") as f:
            old_chars = json.load(f)
        shutil.copy(FILEPATH, FILEPATH + ".bak")
    old_urls = {c["url"] for c in old_chars}
    print(f"Old data: {len(old_chars)} character")

    soup = get_soup(URL)
    if soup is None:
        print("Scrape fail, stopped. Old data saved.")
        return

    h3_featured = soup.find_all("h3", string=lambda t: t and "Featured Spotlight Characters" in t)
    h3_stars = soup.find_all("h3", string=lambda t: t and "Star Characters" in t)

    scraped = []
    for heading in h3_featured:
        scraped += collect_links(heading, "3")

    for heading in h3_stars:
        star = get_star(heading.text)
        if star is None:
            print(f"The star rating cannot be read from the heading: {heading.text!r}")
            continue
        scraped += collect_links(heading, star)

    seen = set()
    unique_scraped = []
    for char in scraped:
        if char["url"] not in seen:
            seen.add(char["url"])
            unique_scraped.append(char)

    new_chars = [c for c in unique_scraped if c["url"] not in old_urls]
    print(f"From web: {len(unique_scraped)} Character, new: {len(new_chars)}")

    if not new_chars:
        print("There's no new character. file doesn't changed.")
        return

    added = []
    for i, char in enumerate(new_chars, start=1):
        print(f"[{i}/{len(new_chars)}] {char['name']}")
        if scrape_unique_skill(char):
            added.append(char)
        time.sleep(1)

    with open(FILEPATH, "w", encoding="utf-8") as f:
        json.dump(old_chars + added, f, indent=2, ensure_ascii=False)

    failed = len(new_chars) - len(added)
    print(f"Done. Added {len(added)} Character, failed {failed}.")

if __name__ == "__main__":
    main()

# Data sourced from game8 (https://game8.co/games/Umamusume-Pretty-Derby/archives/535926)