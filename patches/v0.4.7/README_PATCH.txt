ZSE Value Scanner v0.4.7 — Historical Commercial Trajectory

Purpose
-------
Turn reported commercial observations into provenance-preserving historical series so future competitor analysis can distinguish rising, falling and mixed trajectories without confusing revenue growth with market-share gain.

Adds
----
- src/zse_tool/commercial_trajectory.py
  - bounded offline JSON evidence input
  - compact source registry with reusable source_id provenance references
  - series keyed by metric + period basis + scope + market + unit/currency/scale
  - FY/H1/Q1/Q1-Q3 kept separate
  - same-period YoY derivation only when prior year exists
  - FY CAGR and deterministic monotonic direction
  - no market-share or competitor-displacement inference
  - no database writes / no LLM
- examples/koei_commercial_trajectory_evidence_v0_4_7.json
  - official KONCAR-only pilot history
- tests/test_commercial_trajectory_v0_4_7.py
- COMMERCIAL_TRAJECTORY_V0_1.md
- SOURCES_V0_4_7.md

Pilot highlights
----------------
- Germany FY market revenue: 2023 109.0m, 2024 130.6m, 2025 188.3m EUR.
- Germany H1: 2025 98.2m -> 2026 124.4m EUR.
- Sweden FY: 2023 87.0m, 2024 109.7m, 2025 119.8m EUR.
- Sweden H1: 2025 67.6m -> 2026 60.6m EUR.
- PT&D division revenue FY 2023-2025.
- Group order intake FY 2022-2024 and H1 2025-2026.
- Group backlog FY 2023-2025.

Safety / interpretation
-----------------------
- Requires base version 0.4.6.
- Additive module only.
- No network access from the module.
- No schema migration or SQLite mutation.
- Reported values and precision are preserved.
- Group/country revenue is not silently treated as product-specific revenue.
- Market revenue is not market share.
- Faster growth does not prove competitor displacement.

Pilot command
-------------
python -m zse_tool.commercial_trajectory \
  --input examples/koei_commercial_trajectory_evidence_v0_4_7.json \
  --output /scratch/.../KOEI-v0.4.7.json
