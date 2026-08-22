ZSE Value Scanner v0.4.0 — European Activity Evidence Discovery

Purpose
-------
Build a bounded, read-only activity evidence pack for an external European company from its exact LEI and latest ESEF filing.

Adds
----
- src/zse_tool/esef.py
  - exact-LEI filings.xbrl.org discovery
  - bounded page size
  - ESEF latest-filing selection with language preference
  - source URLs, package URL and repository-reported package SHA-256 metadata
- src/zse_tool/esef_activity.py
  - bounded xBRL-JSON/XHTML retrieval
  - xBRL custom-dimension/member inventory
  - activity-related numeric and tagged text fact candidates
  - bounded narrative evidence windows from reported XHTML
  - explicit evidence classes and provenance manifest
- tests/test_esef_activity_v0_4_0.py
- SOURCES_V0_4_0.md

Safety / provenance
-------------------
- Requires base version 0.3.9.
- No schema migration.
- No SQLite mutation.
- No research entity write.
- No peer assignment.
- No external financial fact write.
- No ingestion-job or raw-artifact registration.
- No LLM use.
- The public API query is always scoped to one exact LEI and a bounded first page.
- xBRL-JSON and XHTML downloads are byte-capped.
- Repository absence is not treated as proof that no official filing exists.

Commands after installation
---------------------------
Discovery only:
  python -m zse_tool.esef --lei <LEI> --latest

Activity evidence:
  python -m zse_tool.esef_activity --lei <LEI> --latest --output /scratch/.../activity-evidence.json

v0.4.0 intentionally analyzes only the latest ESEF filing. Historical activity packs, peer scoring, taxonomy mapping, package persistence, and database ingestion are later stages.
