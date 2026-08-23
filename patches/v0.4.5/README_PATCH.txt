ZSE Value Scanner v0.4.5 — Reviewable Activity Taxonomy Mapping

Purpose
-------
Map v0.4.4 annual ESEF activity-baseline evidence into a controlled multi-label
business taxonomy while preserving fact-level evidence and keeping analytical
mapping separate from reported facts.

Observed live basis
-------------------
The v0.4.4 annual-baseline pilot produced rich, stable activity evidence for
Alfen, Schneider Electric, Prysmian, NKT and Vestas. The companies overlap at
different levels: grid equipment/solutions, power cables, electrification,
automation, distributed energy and wind generation. A generic industry label
would collapse economically different businesses.

Adds
----
- src/zse_tool/activity_mapping.py
  - controlled taxonomy version energy-electrical-v0.1
  - deterministic multilingual/punctuation-tolerant phrase rules
  - A1 analytical mappings with source fact/concept/period/language/excerpt
  - A2 derived taxonomy ancestors kept separate from explicit mappings
  - offline consumption of existing v0.4.4 annual-baseline manifests
  - bounded input files
  - batch mapped profiles and exact pairwise taxonomy intersections
  - no numeric similarity score or peer ranking
- tests/test_activity_mapping_v0_4_5.py
- ACTIVITY_TAXONOMY_V0_1.md
- SOURCES_V0_4_5.md

Safety / interpretation
-----------------------
- Requires base version 0.4.4.
- Additive module only; no existing extraction module is modified.
- No network access from the mapping module.
- No schema migration or SQLite mutation.
- No entity, peer, similarity, financial-fact, job or raw-artifact write.
- No LLM.
- Mapping is explicitly analytical, not a reported accounting fact.
- No segment exposure percentage is inferred.
- Pairwise output is set intersection only; no score, rank or peer conclusion.

Command
-------
python -m zse_tool.activity_mapping \
  --input-dir /scratch/.../v0.4.4-annual-grid-pilot \
  --output-dir /scratch/.../v0.4.5-mapped-grid-pilot
