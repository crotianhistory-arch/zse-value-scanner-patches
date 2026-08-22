ZSE Value Scanner v0.3.4 — bounded GLEIF discovery preflight

Purpose
-------
Add a conservative, read-only first connection to the official GLEIF API before building persistent entity ingestion.

Changes
-------
- adds src/zse_tool/gleif.py
- adds scripts/gleif_preflight.py
- adds tests/test_gleif_v0_3_4.py
- adds SOURCES_V0_3_4.md
- bumps pyproject.toml version from 0.3.3 to 0.3.4

Safety
------
- refuses to apply unless pyproject.toml says version 0.3.3
- creates a timestamped .patch_backups/v0_3_4-* backup
- does not delete or move data/
- does not modify data/zse.sqlite
- does not mutate research_entities/entity_identifiers
- caps API candidate queries at 25 records
- no bulk GLEIF download

After applying
--------------
pytest -q
python -m zse_tool.gleif --name "KONČAR - ELEKTROINDUSTRIJA d.d." --country HR --limit 5
python -m zse_tool.gleif --name "Podravka d.d." --country HR --limit 5
