ZSE Value Scanner v0.3.6 — GLEIF Batch Review

Base version: v0.3.5

Purpose
-------
Add a deterministic, read-only batch review layer over the v0.3.4 discovery
and v0.3.5 explicit-confirmation persistence path.

What this patch adds
--------------------
- `python -m zse_tool.gleif_review`
- review selected tickers or all currently unidentified ZSE entities
- skip entities that already have an LEI without querying GLEIF again
- classify country/status conflicts as REJECT
- mark eligible records REVIEW_CONFIRM; never attach them automatically
- optional JSON review manifest
- explicit confirmation command strings for human-reviewed candidates

Safety
------
- No schema migration.
- No financial data/report rewrite.
- The review command does not write LEIs, ingestion jobs, or raw artifacts.
- Existing `gleif_ingest --yes-confirm` remains the only identity-write path.
