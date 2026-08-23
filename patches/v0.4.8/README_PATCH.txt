ZSE Value Scanner v0.4.8 — Official Classification Backbone

Purpose
-------
Build the professional reference layer before competitor discovery: full current NACE Rev. 2.1 and CPA 2.2 hierarchies, multilingual official labels, English explanatory notes and deterministic CPA->NACE structural links.

Adds
----
- src/zse_tool/classification_backbone.py
  - patch payload is transported as small checksum-verified source fragments; installer reconstructs and verifies the exact module SHA-256
- examples/eurostat_classification_catalog_v0_4_8.json
- tests/test_classification_backbone_v0_4_8.py
- CLASSIFICATION_BACKBONE_V0_1.md
- SOURCES_V0_4_8.md

Key behavior
------------
- Fetches only from the allow-listed official Cellar HTTPS endpoint.
- Resolves current scheme URIs from official scheme metadata instead of hard-coding an RDF namespace.
- Retains raw SPARQL pages content-addressed with SHA-256.
- Validates exact current official item counts: NACE=1,047; CPA=5,828.
- Stores all available language-tagged prefLabel/altLabel values.
- Stores English scope/inclusion/exclusion notes where published.
- Creates a standalone SQLite reference DB in a caller-selected scratch path.
- Does not modify data/zse.sqlite or warehouse metadata tables.
- Existing reference DB replacement requires explicit --replace.
- No company classifications, peers, competitors, similarity scores or LLM output.

Pilot sync
----------
python -m zse_tool.classification_backbone sync \
  --catalog examples/eurostat_classification_catalog_v0_4_8.json \
  --raw-dir /scratch/.../raw/reference/eurostat-classifications \
  --output-db /scratch/.../reference/eurostat-classifications-v0.4.8.sqlite

After sync
----------
python -m zse_tool.classification_backbone status --db <db>
python -m zse_tool.classification_backbone search --db <db> transformer --language en
python -m zse_tool.classification_backbone search --db <db> Transformatoren --language de
