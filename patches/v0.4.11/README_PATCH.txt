ZSE Value Scanner v0.4.11 — Eurostat ShowVoc Full Classification Backbone

Purpose
-------
Correct the v0.4.10 full-classification acquisition blocker without weakening
integrity gates.

Adds / changes
--------------
- Adds catalog schema `official-classification-catalog-v0.3`.
- Adds transport `eurostat-showvoc-sparql`.
- Uses the verified Eurostat ShowVoc project contexts for NACE Rev. 2.1 and CPA 2.2.
- Preserves official concept URIs and explicit `skos:broader` parents.
- Requires complete EN/FR/DE `skos:prefLabel` coverage.
- Hard-gates exact totals and per-level counts:
  - NACE Rev. 2.1 = 1,047 = 22 + 87 + 287 + 651.
  - CPA 2.2 = 5,824 = 22 + 87 + 284 + 644 + 1,433 + 3,354.
- Stores content-addressed raw ShowVoc JSON and a retrieval manifest.
- Keeps legacy v0.1 Cellar and v0.2 SDMX catalog support for reproducibility.
- Adds regression tests for the live Semantic Turkey response envelope,
  hierarchy validation, multilingual coverage, catalog counts, provenance, and
  standalone reference DB creation.

Safety
------
- Requires base version 0.4.10.
- Installer performs no network access.
- Installer performs no database write.
- Installer backs up each touched local file.
- Live sync writes only to the explicitly supplied standalone reference DB/raw dir.
- Existing reference DBs are not overwritten unless `--replace` is explicit.
- No company classification, peer, competitor, similarity, valuation, or LLM decision.

After installation
------------------
1. Run the complete test suite.
2. Run the live ShowVoc sync into a fresh scratch reference area.
3. Inspect status/search/show output.
4. Commit the v0.4.11 source changes on the Git branch only after validation.
