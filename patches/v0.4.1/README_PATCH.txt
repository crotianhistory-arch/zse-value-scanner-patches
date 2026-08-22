ZSE Value Scanner v0.4.1 — ESEF Repository URL Normalization

Purpose
-------
Fix the first live v0.4.0 ESEF activity pilot, where filings.xbrl.org discovery succeeded but evidence download failed because API link fields can be repository-relative paths rather than absolute HTTPS URLs.

Change
------
- src/zse_tool/esef.py
  - resolve root-relative, scheme-relative and plain-relative repository links against https://filings.xbrl.org/
  - require resulting scheme HTTPS
  - require resulting host filings.xbrl.org
  - reject embedded credentials and non-standard ports
  - preserve already-absolute trusted HTTPS links
- tests/test_esef_url_normalization_v0_4_1.py
  - regression coverage for the live failure and network trust boundary

Safety
------
- Requires base version 0.4.0.
- No schema migration.
- No SQLite write.
- No entity, peer, financial fact, job or raw-artifact write.
- Does NOT relax the HTTPS-only evidence downloader.
- Does NOT follow arbitrary external hosts supplied by API metadata.

After installation
------------------
Run the full suite, then rerun the same Alfen discovery/activity command.
