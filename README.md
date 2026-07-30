# Duco — politiek dossier op www.rubend.be/duco

Volgt dagelijks 4 bronnen, filtert op jouw keyword-lijst, en toont alles op
één dashboard, per bron in een eigen hoofdstuk. Elk item toont: bron,
documenttype (in de naamgeving van de bronwebsite zelf), datum, onderwerp,
en de trefwoorden waarop de filter matchte.

## De 4 bronnen

| Hoofdstuk | Bron | Ophaalmethode |
|---|---|---|
| Federale ministerraad | news.belgium.be | HTML, gestructureerd |
| Vlaamse regering | Themis (open data) | SPARQL — **best-effort, zie fetchers/vlaamse_regering.py** |
| Federaal parlement (Kamer) | dekamer.be/flwb | HTML, gestructureerd |
| Vlaams Parlement | ws.vlpar.be | Officiële JSON-zoek-API — **best-effort filter, zie fetchers/vlaams_parlement.py** |

## Wat zit erin
- `common.py` — gedeelde opslag- en keyword-matchlogica
- `fetchers/` — 1 los bestand per bron
- `run_all.py` — draait alle 4, bundelt het resultaat, faalt 1 bron dan gaan
  de andere 3 gewoon door
- `keywords.json` — jouw filterwoorden
- `index.html` — het dashboard (4 hoofdstukken + mascotte)
- `assets/otter.svg` — de Duco-mascotte
- `data/items.json`, `data/state.json` — de "database"
- `.github/workflows/daily-scrape.yml` — dagelijkse automatisering

## Setup — ongewijzigd t.o.v. de eerste versie
Zie de vorige instructies: GitHub-repo aanmaken, Pages inschakelen op
"GitHub Actions", workflow-permissions op "Read and write", eerste run
manueel starten via het Actions-tabblad, en de resulterende Pages-URL in de
Wix-iFrame op je "duco"-pagina plakken (www.rubend.be/duco).

## Belangrijk: twee onderdelen vragen een controle na de eerste live run
Twee bronnen draaien op een API waarvan ik de exacte schema-/veldnamen niet
kon verifiëren zonder er zelf live tegen te kunnen bevragen:

1. **Vlaamse regering (Themis SPARQL)** — de query in
   `fetchers/vlaamse_regering.py` is een onderbouwde inschatting, geen
   geteste query. Levert de eerste run niets op voor dit hoofdstuk? Open
   https://themis.vlaanderen.be/sparql (heeft een ingebouwde query-editor)
   en stuur me door wat je er vindt.
2. **Vlaams Parlement (ws.vlpar.be)** — de basis-aanroep is bevestigd, maar
   het filteren op documentsoort gebeurt nu client-side (in Python) bij
   gebrek aan een bevestigde filterparameter. Werkt dit onverwacht slecht,
   laat het weten.

Als een van deze 2 faalt, blijven de andere hoofdstukken gewoon werken --
de orchestrator (`run_all.py`) vangt fouten per bron individueel op.

## Je keyword-lijst aanpassen
Zoals voorheen: pas `keywords.json` aan in de repository, commit de
wijziging. Geldt nu voor alle 4 bronnen tegelijk.
