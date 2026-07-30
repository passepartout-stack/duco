"""Gedeelde hulpfuncties voor alle fetchers."""

import json
import os

KEYWORDS_FILE = "keywords.json"
ITEMS_FILE = "data/items.json"
STATE_FILE = "data/state.json"

SOURCE_LABELS = {
    "federale_ministerraad": "Federale ministerraad",
    "vlaamse_regering": "Vlaamse regering",
    "kamer": "Federaal parlement (Kamer)",
    "vlaams_parlement": "Vlaams Parlement",
}


def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_keywords():
    return load_json(KEYWORDS_FILE, {"keywords": []}).get("keywords", [])


def matched_keywords(text, keywords):
    """Geeft de lijst van keywords terug die in de tekst voorkomen.
    Lege lijst + lege keywords-lijst = geen filter ingesteld -> item telt als match."""
    if not text:
        return []
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]


def passes_filter(text, keywords):
    """True als er geen filter is ingesteld, of als minstens 1 keyword matcht."""
    if not keywords:
        return True
    return len(matched_keywords(text, keywords)) > 0


def make_item(source, doc_type, date, title, url, matched=None, summary=""):
    return {
        "source": source,
        "source_label": SOURCE_LABELS.get(source, source),
        "doc_type": doc_type,
        "date": date,
        "title": title,
        "summary": summary,
        "url": url,
        "matched_keywords": matched or [],
    }
