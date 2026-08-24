ZSE Value Scanner v0.4.12 — Activity / Classification Translation Pilot

Purpose
-------
Connect the existing energy-electrical controlled activity taxonomy to the
official NACE/CPA backbone created in v0.4.11, and prove the translation model
against a second convention/market using ISIC Rev. 5 and NAICS 2022.

Adds
----
- `zse_tool.classification_mapping`
  - validates a versioned activity/classification mapping catalog;
  - validates NACE Rev. 2.1 / CPA 2.2 targets against the standalone v0.4.11 DB;
  - supports official pinned ISIC Rev. 5 / NAICS 2022 reference targets;
  - translates individual taxonomy nodes or a complete controlled-activity
    profile;
  - translates explicit activity nodes only;
  - records relation type, evidence class and rationale for every mapping;
  - exposes information loss instead of pretending all codes are equivalent.
- Pilot mappings for transformers, switchgear and power-cable activities.
- Cross-system demonstration:
  Transformers -> NACE 27.11 / CPA 27.11.4 / ISIC 2710 / NAICS 335311.
- Unit tests for target validation, coarsening, profile translation and source
  host integrity.

Safety
------
- Requires base version 0.4.11.
- Installation performs no network request and no database write.
- Translation opens the classification reference DB read-only.
- Does not modify `data/zse.sqlite`.
- Does not assign a whole-company primary classification.
- Does not infer exposure percentages.
- Does not create peers/competitors/rankings.
