ZSE Value Scanner v0.4.4 — Annual Activity Baseline Selection

Purpose
-------
Prevent sparse quarterly/interim ESEF filings from becoming the business-activity baseline merely because they are the newest filing.

Observed live issue
-------------------
The v0.4.3 five-company pilot selected 2026-03-31 filings for NKT A/S and Vestas Wind Systems A/S. Both returned zero tagged activity facts, while their 2025 annual reports are separately available. Alfen, Schneider Electric and Prysmian selected annual reports and produced rich segment/business evidence.

Adds
----
- src/zse_tool/esef_activity_baseline.py
  - deterministic full-fiscal-year assessment from XBRL reporting-period start/end facts
  - corroborating annual-duration fact assessment aligned to filing period end
  - no assumption that fiscal year ends in December
  - one preferred-language filing per reporting period
  - bounded backward scan across recent filing periods
  - explicit rejected-interim / accepted-annual candidate audit
  - annual-baseline single-company and batch manifests
- tests/test_esef_activity_baseline_v0_4_4.py

Safety / interpretation
-----------------------
- Requires base version 0.4.3.
- Additive module; v0.4.3 latest-filing command remains available unchanged.
- No schema migration or SQLite mutation.
- No entity, peer, similarity, financial-fact, job or raw-artifact write.
- No LLM.
- No full XHTML download.
- Annuality is a deterministic selection heuristic from reported XBRL period evidence, not a claim about a regulator's legal document classification.
- If no annual-like filing is found within the bounded candidate scan, the command fails explicitly rather than silently using an interim filing.

Command
-------
python -m zse_tool.esef_activity_baseline \
  --lei <LEI> [--lei <LEI2> ...] \
  --annual-baseline \
  --output-dir /scratch/.../annual-baseline-pilot
