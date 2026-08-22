ZSE Value Scanner v0.3.8 — Official ZSE Identity Corroboration

Purpose
-------
Promote unresolved ZSE entities from weak name candidates/research leads to a stronger,
read-only B_CORROBORATED_OFFICIAL_EVIDENCE state when two official sources agree:

1. Zagreb Stock Exchange issuer page reached by exact local ISIN.
2. Exact GLEIF LEI record.

The patch does NOT automatically attach an LEI and performs no schema migration.

Expected pilot
--------------
GRNL: ZSE page should expose LEI 213800O3Z6ZSDBAKG321.
HT:   ZSE page should expose LEI 097900BFHJ0000029454.

Both should then be independently validated against exact GLEIF records and shown as
B_CORROBORATED_OFFICIAL_EVIDENCE / REVIEW_CONFIRM.
