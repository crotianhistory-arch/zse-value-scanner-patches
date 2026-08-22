ZSE Value Scanner v0.4.2 — Bounded Narrative Fallback

Purpose
-------
Keep a valid ESEF activity evidence pack when the selected filing's XHTML annual report is too large for the explicit narrative download cap.

Change
------
- Add EvidenceTooLarge, a ValueError subtype used only for bounded-download overflow.
- xBRL-JSON remains required and fatal if unavailable/oversized.
- XHTML becomes bounded enrichment:
  - available: extract heuristic narrative windows as before
  - unavailable: keep structured xBRL evidence and record narrative_status
  - oversized: keep structured xBRL evidence and record narrative_status=skipped_oversize
- Non-size XHTML failures still propagate; security/network errors are not silently swallowed.
- Manifest records the narrative state and download limit.

Safety
------
- Requires base version 0.4.1.
- Does NOT raise the 80 MiB XHTML download cap.
- No schema migration.
- No SQLite write.
- No entity, peer, financial-fact, ingestion-job or raw-artifact write.
- No LLM use.

After installation
------------------
Run the full suite and rerun the same Alfen activity command. The manifest should now be produced even if Alfen's XHTML remains over 80 MiB.
