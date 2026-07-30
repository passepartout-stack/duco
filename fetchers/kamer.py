"""Fetcher voor de Kamer van volksvertegenwoordigers (dekamer.be/flwb).

Haalt de 'recent gepubliceerde documenten'-lijst op en filtert op:
wetsontwerp, wetsvoorstel, amendement, en programmawetten (via titel-detectie,
want 'programmawet' is geen apart documenttype in dit systeem).

LET OP: LEGISLATUUR is hardcoded op "56". Na de volgende verkiezingen moet dit
nummer verhoogd worden (bv. naar "57") -- dekamer.be wijzigt dan zelf de URL.
"""

import re

import requests
from bs4 import BeautifulSoup

from common import matched_keywords, passes_filter, make_item

LEGISLATUUR = "56"
LIST_URL = f"https://www.dekamer.be/flwb/html/{LEGISLATUUR}/N/lastdocument_4.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (RubenDucoTracker/1.0; +https://www.rubend.be)"}

INCLUDED_TYPES = {"WETSONTWERP", "WETSVOORSTEL", "AMENDEMENT"}

SUBENTRY_RE = re.compile(
    r"(\d{3})\s*Datum\s*:\s*(\d{2}/\d{2}/\d{4})\s*([A-ZÀ-Þ()\s]+?)(?=\d{3}\s*Datum\s*:|$)"
)


def doc_url(doc_nr, volgnr):
    return f"https://www.dekamer.be/FLWB/pdf/{LEGISLATUUR}/{doc_nr}/{LEGISLATUUR}K{doc_nr}{volgnr}.pdf"


def fetch(known_ids, keywords):
    r = requests.get(LIST_URL, timeout=30, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    items = []
    rows = soup.find_all("tr") or soup.find_all("li")

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        doc_nr = cells[0].get_text(strip=True)
        if not re.fullmatch(r"\d{4}", doc_nr):
            continue
        cell_text = cells[1].get_text(" ", strip=True)

        subentries = SUBENTRY_RE.findall(cell_text)
        if not subentries:
            continue

        title = cell_text.split(subentries[0][0] + " Datum")[0].strip()
        is_programmawet = "programmawet" in title.lower()

        for volgnr, datum_str, doc_type_raw in subentries:
            doc_type = doc_type_raw.strip()
            if doc_type not in INCLUDED_TYPES and not is_programmawet:
                continue

            uid = f"{doc_nr}/{volgnr}"
            if uid in known_ids:
                continue

            day, month, year = datum_str.split("/")
            date_iso = f"{year}-{month}-{day}"
            label = doc_type if not is_programmawet else f"{doc_type} (programmawet)"

            if passes_filter(title, keywords):
                items.append(make_item(
                    source="kamer",
                    doc_type=label,
                    date=date_iso,
                    title=f"DOC {LEGISLATUUR} {doc_nr}/{volgnr} - {title}",
                    url=doc_url(doc_nr, volgnr),
                    matched=matched_keywords(title, keywords),
                ))
            known_ids.add(uid)

    return items, known_ids
