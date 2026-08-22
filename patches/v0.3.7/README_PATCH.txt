ZSE Value Scanner v0.3.7 — ISIN-first identity resolution

Adds a read-only deterministic identity-resolution ladder:
  A. official GLEIF/ANNA ISIN-to-LEI mapping
  B. reserved multi-source official corroboration
  C. legal-name candidate search
  D. official web / optional LLM research lead

No LEI is attached by this resolver. Existing v0.3.5 explicit confirmation remains the only write path.
No schema migration is performed.

Recommended pilot after pytest:
  python -m zse_tool.gleif_resolve --all-unidentified --limit 5
