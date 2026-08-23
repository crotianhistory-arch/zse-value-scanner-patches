ZSE Value Scanner v0.4.9 — Cellar Virtuoso 8 SPARQL Transport Hotfix

Purpose
-------
Fix the v0.4.8 live Eurostat classification sync failure seen on 2026-08-23:
  HTTP Error 500: SPARQL Request Failed

The Publications Office Cellar endpoint was upgraded from Virtuoso 7 to Virtuoso 8 in March 2026. A currently maintained EU-law client for the same endpoint uses URL-encoded HTTP GET requests. v0.4.8 used form-encoded POST only.

Change
------
- GET is attempted first for SPARQL queries.
- POST remains a bounded fallback.
- Both paths retain the same HTTPS allow-list, timeouts, bounded response reader and strict JSON parser.
- Error output preserves both GET and POST failures if neither works.
- No classification counts, normalization, database schema, provenance model or search behavior changes.

Safety
------
- Requires base version 0.4.8.
- Source-only transport hotfix.
- No data/SQLite/warehouse writes during installation.
- Existing v0.4.8 reference DB is not required and is not touched.
