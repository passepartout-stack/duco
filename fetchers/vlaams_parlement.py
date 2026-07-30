"""Fetcher voor het Vlaams Parlement via de officiele zoek-webservice (ws.vlpar.be).

LET OP - eerlijke inschatting van de betrouwbaarheid van dit bestand:
De basis-aanroep (collection, sort, max, requiredfields) staat letterlijk
gedocumenteerd onderaan https://www.vlaamsparlement.be/nl/parlementaire-documenten.
De EXACTE veldnaam waarmee je filtert op documentsoort (bv. 'Amendement',
'Voorstel of ontwerp van decreet') kon ik niet bevestigen: de swagger-pagina
(ws.vlpar.be/api/swagger) is zelf een JavaScript-app die ik niet kon
doorzoeken. Dit script haalt daarom een brede set recente documenten op en
filtert de documentsoort CLIENT-SIDE in Python, door alle tekstvelden van elk
resultaat te doorzoeken op een van de gewenste documentsoort-namen. Dat werkt,
maar is minder efficient dan een servery-side filter.

Actie vereist na de eerste live run: bekijk de ruwe JSON-respons (bv. via
https://ws.vlpar.be/api/swagger/#!/search/getSearchResult in een browser) en
laat het gericht weten als er een directe filterparameter bestaat -- dan
vervang ik de client-side filtering door een efficiëntere server-side query.
"""

import requests

from common import matched_keywords, passes_filter, make_item

SEARCH_URL = "https://ws.vlpar.be/api/search/query/"

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


def fetch(known_ids, keywords):
    params = {
        "collection": "vp_collection",
        "sort": "date",
        "max": 100,
        "requiredfields": "paginatype:Parlementair document",
    }
    r = requests.get(SEARCH_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    results = data.get("results") or data.get("items") or data if isinstance(data, list) else []
    if isinstance(data, dict) and not results:
        results = data.get("documents", [])

    items = []
    for result in results:
        doc_type = _find_doc_type(result)
        if not doc_type:
            continue

        uid = _extract(result, "id", "documentId", "nid") or _extract(result, "url", "link")
        title = _extract(result, "title", "titel", "name") or "(geen titel)"
        date = _extract(result, "date", "datum", "publicationDate")
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
