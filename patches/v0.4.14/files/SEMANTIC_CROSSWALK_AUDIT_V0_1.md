# Semantic crosswalk audit v0.1

ZSE Value Scanner v0.4.14 adds a deterministic semantic audit layer on top of the v0.4.13 official crosswalk graph.

## Why

An official correspondence edge is not automatically a semantic equivalence. Likewise, `one_to_one` only describes graph topology. A class can keep the same code and title while its explanatory note changes, and a one-to-many or many-to-one correspondence is a structural reorganization even when some wording overlaps.

## Evidence classes

- `O1_OFFICIAL_CROSSWALK`: official correspondence rows ingested by v0.4.13.
- `D2_DETERMINISTIC_SEMANTIC_AUDIT`: deterministic comparison of official titles and official explanatory notes.
- `E1_EMPIRICAL_CROSS_SYSTEM_EVIDENCE`: company co-classification observations.
- `A3_ANALYTICAL_CLASSIFICATION_MAPPING`: scanner activity-to-classification analysis.

These classes remain separate.

## Semantic states

For a single official edge:

- `text_equivalent`: one-to-one topology and normalized title plus normalized explanatory note are identical.
- `same_title_definition_changed`: one-to-one topology, title identical, explanatory note different.
- `title_changed_definition_same`: one-to-one topology, title different, explanatory note identical.
- `title_and_definition_changed`: one-to-one topology, both differ.
- `structural_reorganization`: graph shape is one-to-many, many-to-one or many-to-many.

The scanner does **not** infer `broader` or `narrower` from a text diff. Scope direction stays `not_inferred` until supported by an official change description or a separate reviewed analytical layer.

## Generalization rule

The semantic rule engine does not contain ISIC class codes or sector-specific rules. Source peculiarities live in adapters/catalog entries. Adding a new provider may require an adapter, but adding a new sector must not require changing the semantic rule engine.

## Storage policy

`prepare` copies an existing standalone v0.4.13 crosswalk database into a new semantic-audit database. The operational ZSE SQLite database is never modified.

Official HTML detail pages are preserved under the explicitly supplied raw directory with SHA-256 provenance. Parsed titles and explanatory notes are cached in `semantic_definitions`; edge audits are stored in `semantic_audits`.

## Commands

Prepare a semantic DB:

```bash
python -m zse_tool.classification_semantic_audit prepare \
  --source-db /path/to/v0.4.13/official_crosswalks.sqlite \
  --output-db /path/to/v0.4.14/semantic_crosswalks.sqlite
```

Audit one official edge:

```bash
python -m zse_tool.classification_semantic_audit audit-edge \
  --db /path/to/v0.4.14/semantic_crosswalks.sqlite \
  --catalog examples/classification_semantic_source_catalog_v0_4_14.json \
  --raw-dir /path/to/v0.4.14/raw \
  --from-system ISIC --from-version 4 --from-code 2710 \
  --to-system ISIC --to-version 5 --to-code 2710
```

The module never promotes an LLM or heuristic judgment into official or deterministic semantic equivalence.
