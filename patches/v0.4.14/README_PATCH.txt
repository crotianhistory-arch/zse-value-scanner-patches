ZSE Value Scanner v0.4.14 — deterministic semantic crosswalk audit

Base source release:
  v0.4.13
  d349638bc911ef22f03ae03bb05f1ea2760f8aa2

This patch adds:
- a generic deterministic semantic-audit layer over official crosswalk edges;
- official title + explanatory-note retrieval through provider adapters;
- strict separation between graph topology and semantic equivalence;
- semantic states for exact text equivalence, definition/title changes, and structural reorganization;
- explicit refusal to infer broader/narrower scope from a text difference alone;
- standalone semantic DB preparation by copying the v0.4.13 reference DB;
- raw official HTML preservation and SHA-256 provenance;
- an UNSD ISIC Rev.4/Rev.5 detail-page adapter catalog;
- 11 focused regression tests.

Important boundaries:
- O1 official correspondence remains unchanged;
- D2 deterministic semantic audits are separate evidence;
- one_to_one does not mean semantic equivalence;
- LLM/heuristic output cannot promote itself to D2 or O1;
- the operational ZSE database is not touched;
- installation performs no network access or database write;
- live semantic audit writes only to an explicitly supplied copied crosswalk DB/raw directory.
