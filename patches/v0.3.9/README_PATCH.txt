ZSE Value Scanner v0.3.9 — ZSE issuer-name provenance parser fix

Purpose
-------
Fix the v0.3.8 ZSE issuer-page parser after the live page showed a navigation
tab sequence "Issuer" -> "Announcements". v0.3.8 incorrectly recorded
"Announcements" as zse_issuer_name even though the ISIN, LEI, tax number and
GLEIF corroboration were correct.

v0.3.9:
- anchors the issuer legal name to the official issuer-detail block immediately
  before Home Member State / Matična država članica;
- keeps the older explicit Issuer/Izdavatelj field layout as a fallback;
- rejects common navigation labels (including Announcements/Objave) as issuer names;
- adds regression tests reproducing the live ZSE navigation-tab trap.

Safety
------
- Requires base version exactly 0.3.8.
- Creates a timestamped backup.
- No schema migration.
- Does not alter data/, SQLite, warehouse metadata, LEIs, jobs or raw artifacts.
- zse_identity remains read-only.
