"""Draait alle 4 fetchers en bundelt het resultaat in data/items.json.

Gebruik: python run_all.py
Wordt dagelijks aangeroepen via .github/workflows/daily-scrape.yml
"""

import traceback
from datetime import datetime, timezone

from common import load_json, save_json, load_keywords, ITEMS_FILE, STATE_FILE
from fetchers import federale_ministerraad, vlaamse_regering, kamer, vlaams_parlement

SOURCES = {
    "federale_ministerraad": federale_ministerraad,
    "vlaamse_regering": vlaamse_regering,
    "kamer": kamer,
    "vlaams_parlement": vlaams_parlement,
}


def main():
    state = load_json(STATE_FILE, {"known_ids": {}, "errors": {}, "last_checked": None})
    known_ids_by_source = {
        src: set(state.get("known_ids", {}).get(src, []))
        for src in SOURCES
    }
    items_store = load_json(ITEMS_FILE, {"items": []})
    keywords = load_keywords()

    errors = {}
    total_new = 0

    for source_name, module in SOURCES.items():
        try:
            new_items, updated_ids = module.fetch(known_ids_by_source[source_name], keywords)
            known_ids_by_source[source_name] = updated_ids
            items_store["items"] = new_items + items_store["items"]
            total_new += len(new_items)
            print(f"{source_name}: {len(new_items)} nieuwe items")
        except Exception as e:
            errors[source_name] = f"{type(e).__name__}: {e}"
            print(f"{source_name}: FOUT -- {e}")
            traceback.print_exc()

    state["known_ids"] = {src: sorted(ids) for src, ids in known_ids_by_source.items()}
    state["errors"] = errors
    state["last_checked"] = datetime.now(timezone.utc).isoformat()

    save_json(STATE_FILE, state)
    save_json(ITEMS_FILE, items_store)

    print(f"\nTotaal nieuwe items: {total_new}")
    if errors:
        print(f"Bronnen met een fout deze run: {', '.join(errors.keys())}")


if __name__ == "__main__":
    main()
