"""Fetcher voor de federale ministerraad (news.belgium.be)."""

import re

from bs4 import BeautifulSoup

from common import matched_keywords, passes_filter, make_item, fetch_url

BASE = "https://news.belgium.be"
LIST_URL = f"{BASE}/nl/ministerraad"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "nl-BE,nl;q=0.9,en;q=0.8",
    "Referer": "https://news.belgium.be/nl/ministerraad",
}

MONTHS_NL = {
    "januari": 1, "februari": 2, "maart": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "augustus": 8, "september": 9, "oktober": 10,
    "november": 11, "december": 12,
}

EXCLUDE_SNIPPETS = [
    "/nl/ministerraad", "/fr/", "/de/", "/en/", "facebook.com", "twitter.com",
    "/nl/feeds", "/nl/contactpunten", "/nl/zoek-een-nieuwsbericht", "/nl/corona",
    "/nl/source/", "/nl/fod-kanselarij", "premier.be", "federale-regering.be",
    "kanselarij.belgium.be", "/nl/persoonsgegevens", "/nl/voorwaarden",
    "/nl/contacteer-ons", "/nl/toegankelijkheidsverklaring", "/node/",
    "mailto:", "tel:", "belgium.be/nl\"", "europa.eu",
]


def parse_dutch_date(url):
    m = re.search(r"ministerraad-van-(\d{1,2})-([a-zA-Z]+)-(\d{4})", url)
    if not m:
        return None
    day, month_nl, year = m.groups()
    month = MONTHS_NL.get(month_nl.lower())
    if not month:
        return None
    return f"{year}-{month:02d}-{int(day):02d}"


def get_session_links():
    r = fetch_url(LIST_URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    links, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.search(r"/ministerraad-van-\d{1,2}-[a-zA-Z]+-\d{4}$", href):
            full = href if href.startswith("http") else BASE + href
            if full not in seen:
                seen.add(full)
                links.append(full)
    return links


def get_decisions(session_url):
    r = fetch_url(session_url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    main = soup.find("main") or soup

    decisions, seen = [], set()
    for a in main.find_all("a", href=True):
        href = a["href"]
        if any(s in href for s in EXCLUDE_SNIPPETS):
            continue
        if not (href.startswith(BASE) or href.startswith("/nl/")):
            continue
        title = a.get_text(strip=True)
        if not title or len(title) < 8:
            continue
        full = href if href.startswith("http") else BASE + href
        if full in seen:
            continue
        seen.add(full)

        parent = a.find_parent()
        parent_text = parent.get_text(" ", strip=True) if parent else ""
        summary = parent_text.replace(title, "", 1).strip()

        decisions.append({"title": title, "summary": summary, "url": full})
    return decisions


def fetch(known_ids, keywords):
    """Geeft (nieuwe_items, bijgewerkte_known_ids) terug."""
    session_links = get_session_links()
    new_links = [u for u in session_links if u not in known_ids]
    items = []

    for url in reversed(new_links):
        date_iso = parse_dutch_date(url)
        for d in get_decisions(url):
            text = d["title"] + " " + d["summary"]
            if passes_filter(text, keywords):
                items.append(make_item(
                    source="federale_ministerraad",
                    doc_type="Beslissing",
                    date=date_iso,
                    title=d["title"],
                    url=d["url"],
                    matched=matched_keywords(text, keywords),
                    summary=d["summary"],
                ))
        known_ids.add(url)

    return items, known_ids
