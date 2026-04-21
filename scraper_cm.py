import requests
import json
from bs4 import BeautifulSoup

url = "https://game8.co/games/Umamusume-Pretty-Derby/archives/587444"
response = requests.get(url)

print(response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

