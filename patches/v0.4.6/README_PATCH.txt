ZSE Value Scanner v0.4.6 — Commercial Market Search Profile Foundation

Purpose
-------
Create a provenance-preserving search brief that says where competitor discovery should be attempted for a target company, without scanning the whole world and without pretending that group geography equals segment geography.

Adds
----
- src/zse_tool/market_profile.py
  - bounded offline JSON evidence input
  - separate business-scope, geography-revenue, order-intake and direct project evidence
  - market anchors with explicit evidence strength
  - direct activity-market examples from reported projects
  - H1 search hypotheses when dominant business scope is combined with group-level geography
  - no competitor/peer/similarity decision
- examples/koei_market_evidence_v0_4_6.json
  - official KONCAR-only pilot evidence for KOEI
- tests/test_market_profile_v0_4_6.py
- MARKET_PROFILE_V0_1.md
- SOURCES_V0_4_6.md

Safety / interpretation
-----------------------
- Requires base version 0.4.5.
- Additive module only.
- No network access from the module.
- No schema migration or SQLite mutation.
- No automatic competitor, peer or similarity assignment.
- No LLM.
- Group-level geography is never silently converted into segment/product geography.

Pilot command
-------------
python -m zse_tool.market_profile \
  --input examples/koei_market_evidence_v0_4_6.json \
  --output /scratch/.../koei-commercial-search-profile-v0.4.6.json
