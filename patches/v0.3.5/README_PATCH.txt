ZSE Value Scanner v0.3.5 — Confirmed GLEIF Identity Persistence

Base required: v0.3.4

Purpose
-------
This patch adds the first persistent GLEIF identity write path. It is intentionally
narrow: the caller must explicitly provide an existing ZSE ticker and a reviewed LEI.
There is no automatic fuzzy merge.

Safety gates
------------
- exact 20-character LEI syntax
- existing TICKER:ZSE entity required
- refuses a different LEI already attached to the target entity
- refuses an LEI already attached to another entity
- live GLEIF legal-address country must not conflict with local country
- live GLEIF registration status must be ISSUED
- live GLEIF entity status must be ACTIVE when reported
- explicit --yes-confirm flag required for CLI writes

Provenance
----------
The exact LEI record is fetched from the official GLEIF API, canonicalized as JSON,
hashed with SHA-256, stored immutably under:
  $ZSE_WAREHOUSE_DIR/raw/gleif/api/lei-records/<LEI>/<SHA256>.json

The artifact is registered in raw_artifacts with source URL, retrieval timestamp,
hash, byte size and validation metadata. An ingestion job records completion/failure.

No schema migration is needed. Existing ZSE data, reports and market data are not
deleted or rewritten.

After applying
--------------
1. pytest -q
2. Keep: export ZSE_WAREHOUSE_DIR=/scratch/lbarisic/zse-research
3. First validate with KOEI:
   python -m zse_tool.gleif_ingest --ticker KOEI --lei 74780000H0SHMRAW0I15 --yes-confirm
4. Inspect:
   zse-tool entity-lookup KOEI
   zse-tool ingestion-jobs
   zse-tool warehouse-status
5. Re-run the same command; expected state is already_attached and no duplicate LEI.
