#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import json
import re

URL = "https://golfrestaurang.com/our-store.html"
OUTPUT_FILE = "veckans_meny.json"

def fetch_page(url: str) -> str:
    """Hämta HTML från sidan."""
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    # Försök få rätt encoding (åäö osv)
    if resp.encoding is None or resp.encoding.lower() == "iso-8859-1":
        resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text

def parse_menu(html: str) -> dict:
    """Parsa sidan och bygg upp strukturen:
       { "veckans_meny": { "måndag": [...], "tisdag": [...], ... } }
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n")

    # Dela upp i rader och städa
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]  # ta bort tomma rader

    weekday_pattern = re.compile(
        r"^(Måndag|Tisdag|Onsdag|Torsdag|Fredag|Lördag|Söndag)\b",
        re.IGNORECASE,
    )

    veckans_meny = {}
    current_day_key = None

    for line in lines:
        lower_line = line.lower()

        # Menyn för dagarna ligger före sektionerna "Pasta", "Vegetarisk", "Husets hamburgare"
        if lower_line.startswith("pasta") or \
           lower_line.startswith("vegetarisk") or \
           lower_line.startswith("husets hamburgare"):
            # Vi bryter här – resten är inte en del av dagsmenyn
            break

        # Ny veckodag?
        m = weekday_pattern.match(line)
        if m:
            weekday_swedish = m.group(1).lower()  # t.ex. "måndag"
            current_day_key = weekday_swedish
            if current_day_key not in veckans_meny:
                veckans_meny[current_day_key] = []
            continue

        # Om vi "befinner oss" i en dag, tolka raden som maträtt
        if current_day_key is not None:
            veckans_meny[current_day_key].append(line)

    return {"veckans_meny": veckans_meny}

def save_json(data: dict, filename: str) -> None:
    """Spara JSON till fil."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    html = fetch_page(URL)
    data = parse_menu(html)
    save_json(data, OUTPUT_FILE)
    print(f"Veckans meny sparades i {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
