"""Fetcher voor het Vlaams Parlement via de officiele open-data API (ws.vlpar.be).

LET OP - eerlijke inschatting van de betrouwbaarheid van dit bestand:
De eerdere versie gebruikte het pad 'api/search/query', wat een bevestigde
404 opleverde. Het juiste basis-pad is 'e/opendata/api' (bevestigd via de
publieke documentatie van het flempar R-pakket, dat dezelfde API gebruikt --
zie www.flempar.be). De EXACTE naam van de resource voor wetgevend werk
(decreten, amendementen, resoluties) binnen dat pad kon ik echter niet
bevestigen zonder de swagger-pagina zelf te kunnen doorzoeken (die is een
JavaScript-app).

Daarom probeert dit script een reeks aannemelijke resource-paden na elkaar
(zie CANDIDATE_PATHS) en gebruikt het eerste dat een geldig JSON-antwoord
teruggeeft. Werkt geen enkele? Dan faalt enkel dit hoofdstuk (de andere 3
blijven werken) en meldt state.json welk pad als laatste geprobeerd werd.

Actie vereist na de eerste live run: bekijk data/state.json. Bevat het een
fout voor 'vlaams_parlement'? Open dan zelf https://ws.vlpar.be/e/opendata/swagger-ui/index.html
in een browser, zoek de juiste resource-naam voor parlementaire initiatieven,
en stuur me die door -- dan vervang ik de kandidatenlijst door de bevestigde,
directe aanroep.
"""

import requests

from common import matched_keywords, passes_filter, make_item

API_BASE = "https://ws.vlpar.be/e/opendata"

# Aannemelijke resource-namen, in volgorde van waarschijnlijkheid.
CANDIDATE_PATHS = [
    "parlementaire-initiatieven",
    "parlementaireinitiatieven",
    "parlementair-initiatief",
    "feiten",
    "activiteiten",
]

TARGET_DOC_TYPES = [
    "Voorstel of ontwerp van decreet",
    "Amendement",
    "Voorstel van resolutie",
    "Begrotingsontwerp en -documenten",
]


def _flatten_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _flatten_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _flatten_strings(v)


def _find_doc_type(result):
    all_text = " | ".join(_flatten_strings(result))
    for doc_type in TARGET_DOC_TYPES:
        if doc_type.lower() in all_text.lower():
            return doc_type
    return None


def _extract(result, *candidate_keys):
    for key in candidate_keys:
        if key in result and result[key]:
            return result[key]
    return None


def _try_fetch_results():
    """Probeert elk kandidaat-pad, geeft (pad, lijst_resultaten) van de eerste die werkt."""
    last_error = None
    for path in CANDIDATE_PATHS:
        url = f"{API_BASE}/{path}"
        try:
            r = requests.get(url, params={"max": 100}, timeout=20)
            if r.status_code != 200:
                last_error = f"{path} -> HTTP {r.status_code}"
                continue
            data = r.json()
            results = data if isinstance(data, list) else data.get("items") or data.get("results") or []
            if results:
                return path, results
            last_error = f"{path} -> 200 OK maar lege/onherkenbare data"
        except Exception as e:
            last_error = f"{path} -> {type(e).__name__}: {e}"
            continue
    raise RuntimeError(f"Geen enkel kandidaat-pad werkte. Laatste poging: {last_error}")


def fetch(known_ids, keywords):
    _, results = _try_fetch_results()

    items = []
    for result in results:
        doc_type = _find_doc_type(result)
        if not doc_type:
            continue

        uid = _extract(result, "id", "documentId", "nid") or _extract(result, "url", "link")
        title = _extract(result, "title", "titel", "name") or "(geen titel)"
        date = _extract(result, "date", "datum", "publicatiedatum", "publicationDate")
        url = _extract(result, "url", "link", "documentUrl") or ""

        if not uid or uid in known_ids:
            continue

        if passes_filter(title, keywords):
            items.append(make_item(
                source="vlaams_parlement",
                doc_type=doc_type,
                date=str(date)[:10] if date else None,
                title=title,
                url=url,
                matched=matched_keywords(title, keywords),
            ))
        known_ids.add(uid)

    return items, known_ids
