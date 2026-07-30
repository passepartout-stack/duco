"""Fetcher voor de Vlaamse regering via het Themis open-data SPARQL-eindpunt.

LET OP - eerlijke inschatting van de betrouwbaarheid van dit bestand:
Themis (https://themis.vlaanderen.be) publiceert de besluitvorming van de
Vlaamse Regering als linked open data via het vocabularium OSLO-Besluitvorming
(https://data.vlaanderen.be/ns/besluitvorming#). Er bestaat GEEN publieke
voorbeeldquery of schema-documentatie die ik met de beschikbare tools kon
raadplegen (de documentatiepagina's zijn zelf JavaScript-apps). Deze query is
dus een onderbouwde inschatting op basis van het vocabularium-concept
("Nieuwsbericht" = een publieke beslissing/mededeling), geen bevestigde,
geteste query.

Actie vereist na de eerste live run: controleer of dit script effectief
resultaten teruggeeft. Zo niet, open https://themis.vlaanderen.be/sparql in
een browser (heeft een ingebouwde query-editor, "yasgui"), verken het schema
interactief, en stuur me de werkende query door -- dan pas ik dit bestand
gericht aan.
"""

import requests

from common import matched_keywords, passes_filter, make_item

SPARQL_ENDPOINT = "https://themis.vlaanderen.be/sparql"

QUERY = """
PREFIX besluitvorming: <https://data.vlaanderen.be/ns/besluitvorming#>
PREFIX dct: <http://purl.org/dc/terms/>

SELECT ?item ?titel ?datum WHERE {
  ?item a besluitvorming:Nieuwsbericht ;
        dct:title ?titel ;
        dct:issued ?datum .
}
ORDER BY DESC(?datum)
LIMIT 200
"""


def query_themis():
    r = requests.get(
        SPARQL_ENDPOINT,
        params={"query": QUERY, "format": "application/sparql-results+json"},
        headers={"Accept": "application/sparql-results+json"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("results", {}).get("bindings", [])


def fetch(known_ids, keywords):
    """Geeft (nieuwe_items, bijgewerkte_known_ids) terug.
    Faalt deze fetcher (bv. door een verkeerde query), dan geeft de
    orchestrator (run_all.py) gewoon een lege lijst door -- de andere
    bronnen blijven werken."""
    rows = query_themis()
    items = []

    for row in rows:
        item_uri = row.get("item", {}).get("value")
        titel = row.get("titel", {}).get("value", "")
        datum_raw = row.get("datum", {}).get("value", "")
        datum = datum_raw[:10] if datum_raw else None

        if not item_uri or item_uri in known_ids:
            continue

        if passes_filter(titel, keywords):
            items.append(make_item(
                source="vlaamse_regering",
                doc_type="Beslissing",
                date=datum,
                title=titel,
                url=item_uri,
                matched=matched_keywords(titel, keywords),
            ))
        known_ids.add(item_uri)

    return items, known_ids
