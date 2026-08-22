ZSE Value Scanner v0.4.3 — Structured Tagged Activity Extraction + Bounded Multi-Company Pilot

Purpose
-------
Turn ESEF xBRL-JSON tagged narrative facts into clean, provenance-linked business activity evidence without downloading the full XHTML annual report, and support bounded multi-company pilots by exact LEI.

Adds
----
- src/zse_tool/esef_tagged_activity.py
  - clean visible-text extraction from tagged HTML facts
  - bounded HTML table extraction from tagged facts
  - deterministic disclosure-purpose categories:
    principal_activity, operating_segments, revenue_business_line,
    subsidiaries, geography, customers, products_services
  - full-fact processing (not the older 1,500-character preview)
  - exact provenance to XBRL fact ID, concept, period and language
  - single-company and repeated-LEI batch CLI
  - per-LEI manifests plus batch-summary.json
  - batch isolation: one unavailable filing does not erase successful results
- tests/test_esef_tagged_activity_v0_4_3.py
- PILOT_V0_4_3.md
- SOURCES_V0_4_3.md

Safety / interpretation
-----------------------
- Requires base version 0.4.2.
- No schema migration.
- No SQLite write.
- No entity registration.
- No peer assignment.
- No similarity score.
- No external financial fact write.
- No ingestion-job or raw-artifact registration.
- No LLM use.
- Full XHTML is not fetched by this module.
- Categories describe disclosure purpose only; they do not assert industry equivalence or peer status.

Commands after installation
---------------------------
Single company:
  python -m zse_tool.esef_tagged_activity --lei <LEI> --latest --output /scratch/.../<LEI>.json

Bounded batch:
  python -m zse_tool.esef_tagged_activity \
    --lei <LEI1> --lei <LEI2> --lei <LEI3> \
    --latest --output-dir /scratch/.../pilot

v0.4.3 is a market-scanning evidence layer. Historical trends, business-overlap scoring,
contract/order comparison, embeddings and LLM-assisted interpretation are later stages.
