#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hämtar index.html från https://dantorpsrestaurang.kvartersmenyn.se/med wget
och extraherar rätterna under Lunchmeny per veckodag.
"""

import json
import re
import subprocess
from bs4 import BeautifulSoup

URL = "https://dantorpsrestaurang.kvartersmenyn.se/"
INPUT_FILE = "index.html"

WEEKDAYS = ["MÅNDAG", "TISDAG", "ONSDAG", "TORSDAG", "FREDAG"]

def clean_text(s):
    s = re.sub(r"\b\d+\s*[:-]?\b", "", s)   # Ta bort prisfragment
    s = s.replace("\xa0", " ")
    s = s.strip(" ,;:-")
    if s.startswith(". "):
        s = s[2:]
    return s

def parse_menu(html):
    soup = BeautifulSoup(html, "html.parser")
    menu_div = soup.find("div", class_="meny")
    if not menu_div:
        raise RuntimeError("Kunde inte hitta <div class='meny'> i HTML-filen")

    parts = []
    for elem in menu_div.descendants:
        if elem.name == "br":
            parts.append("\n")
        elif elem.name == "strong":
            parts.append(f"\n{elem.get_text(strip=True)}\n")
        elif elem.name is None:
            txt = elem.strip()
            if txt:
                parts.append(txt)

    text = " ".join(parts)
    lines = [clean_text(x) for x in text.split("\n") if x.strip()]

    menu = {d.lower(): [] for d in WEEKDAYS}
    current_day = None
    for line in lines:
        if line in WEEKDAYS:
            current_day = line.lower()
            continue
        if (line[:12]=="VECKANS TIPS"):
            break
        if current_day:
            menu[current_day].append(line)

    return menu

def main():
    # Ladda ner sidan med wget
    subprocess.run(["wget", "-q", "-O", INPUT_FILE, URL], check=True)

    # Läs nedladdad fil
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    menu = parse_menu(html)
    result = {"lunchmeny": menu}

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
