ZSE Value Scanner v0.4.10 — Eurostat SDMX Classification Snapshot

Purpose
-------
Replace the failing Cellar/SPARQL acquisition path with Eurostat's documented
SDMX codelist dissemination API for the core NACE Rev. 2.1 / CPA 2.2 snapshot.

Adds / changes
--------------
- classification_backbone.py supports catalog schema v0.2:
  - discovers codelists from SDMX all/latest?detail=allstubs
  - downloads official codelist TSV separately in en/fr/de
  - filters statistical aggregates that are not classification positions
  - reconstructs classification hierarchy deterministically from official code order
  - hard-gates exact total and per-level counts
  - preserves content-addressed raw XML/TSV plus a retrieval manifest
  - builds the same standalone SQLite reference schema used by v0.4.8
  - derives CPA -> NACE structural links as before
- legacy v0.1 Cellar catalog remains supported but is not used by the v0.4.10 pilot.
- explanatory notes are not part of the core SDMX codelist snapshot; note_count=0
  until a separately reliable official enrichment source is added.

Official expected counts
------------------------
NACE Rev. 2.1: 22 sections + 87 divisions + 287 groups + 651 classes = 1,047.
CPA 2.2: 22 sections + 87 divisions + 284 groups + 644 classes +
         1,432 categories + 3,359 subcategories = 5,828.

Safety
------
- Requires base version 0.4.9.
- Installation does not access the network.
- Installation does not modify data/zse.sqlite or the warehouse metadata DB.
- Live sync writes only to the explicitly supplied standalone reference DB/raw dir.
- Existing reference DBs are not overwritten unless --replace is explicit.
- No company classification, peer, competitor, similarity, valuation or LLM decision.
