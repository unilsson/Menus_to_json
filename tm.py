#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hämtar https://www.tmbagarstuga.se/Menus och extraherar 'Veckans meny'
till en JSON-struktur per veckodag.

Kräver: requests, beautifulsoup4
> pip install requests beautifulsoup4
"""

import re
import json
import sys
from typing import Dict, List
import requests
from bs4 import BeautifulSoup

URL = "https://www.tmbagarstuga.se/Menus"

WEEKDAYS = ["måndag", "tisdag", "onsdag", "torsdag", "fredag"]
START_HEADER = "veckans meny"
END_HEADER = "veckans salladsmeny"

# Prisrad: exempel "125kr", "169 kronor", "125 kr", "150 kronor"
PRICE_RE = re.compile(r"^\s*\d+\s*(kr|kronor)\s*$", re.IGNORECASE)

def normalize_line(s: str) -> str:
    # Normalisera whitespace och trimma
    s = re.sub(r"\s+", " ", s).strip()
    # Ta bort överflödiga mellanslag kring skiljetecken
    s = re.sub(r"\s+([,.:;])", r"\1", s)
    return s

def is_price_line(s: str) -> bool:
    return bool(PRICE_RE.match(s))

def extract_week_menu(text_lines: List[str]) -> Dict[str, List[str]]:
    menu: Dict[str, List[str]] = {d: [] for d in WEEKDAYS}

    # Hitta sektionens start och slut
    lower_lines = [l.lower() for l in text_lines]

    def find_index(keyword: str, start=0):
        for i in range(start, len(lower_lines)):
            if lower_lines[i] == keyword:
                return i
        return -1

    start_idx = find_index(START_HEADER)
    if start_idx == -1:
        raise RuntimeError("Hittade inte rubriken 'Veckans Meny'.")

    end_idx = find_index(END_HEADER, start=start_idx + 1)
    if end_idx == -1:
        # Om vi inte hittar 'Veckans Salladsmeny', ta till slutet av dokumentet
        end_idx = len(text_lines)

    # Gå igenom raderna i sektionen
    current_day = None
    i = start_idx + 1
    while i < end_idx:
        raw = text_lines[i]
        line = normalize_line(raw)

        if not line:
            i += 1
            continue

        low = line.lower()

        # Ny veckodag?
        if low in WEEKDAYS:
            current_day = low
            i += 1
            continue

        # Hoppa över prisrader
        if is_price_line(low):
            i += 1
            continue

        # Bara samla rätter om vi befinner oss i ett dagblock
        if current_day is not None:
            # Filtrera bort uppenbart trasiga platshållare (valfritt – kommentera bort om du vill ha exakt text)
            incomplete_placeholders = {"omelett", "grillad macka med", "stenugnsbakad paj med", "stenugnsbakad paj", "omelett med"}
            if low in incomplete_placeholders:
                i += 1
                continue

            menu[current_day].append(line)

        i += 1

    # Ta bort dagar som saknar rätter helt (om så önskas)
    # menu = {k: v for k, v in menu.items() if v}

    return menu

def main():
    resp = requests.get(URL, timeout=20)
    # För säkerhets skull – säkerställ rätt encoding
    if not resp.encoding:
        resp.encoding = "utf-8"

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extrahera ren text i ordning – sidan använder enklare markup,
    # så det är mest robust att utgå från textflödet.
    # Separator "\n" så att varje visuellt block blir en egen rad.
    full_text = soup.get_text("\n", strip=True)

    # Splitta till rader och rensa bort helt tomma
    lines = [l.strip() for l in full_text.split("\n") if l.strip()]

    veckans_meny = extract_week_menu(lines)

    # Skriv ut JSON
    result = {"veckans_meny": veckans_meny}
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()  # newline

if __name__ == "__main__":
    main()
