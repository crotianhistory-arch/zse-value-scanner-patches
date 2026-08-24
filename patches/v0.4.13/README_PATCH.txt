ZSE Value Scanner v0.4.13 — official crosswalk ingestion framework

Base source release:
  v0.4.12
  1160db4837de883bb998a891ca415ea4dbd1c590

This patch adds:
- a generic normalized crosswalk graph and standalone SQLite reference DB;
- an official UNSD ISIC Rev.4 -> Rev.5 XLSX adapter;
- strict 419-source-class / 463-target-class coverage gates;
- graph-derived one-to-one / one-to-many / many-to-one / many-to-many shape;
- shortest-path translation across multiple future crosswalk sources;
- reverse traversal of official correspondence edges;
- a separate E1 empirical company co-classification evidence table;
- raw source preservation and SHA-256 provenance;
- 10 regression tests including an unrelated food-sector anti-overfitting case.

Important boundaries:
- official correspondence rows remain O1_OFFICIAL_CROSSWALK;
- company observations remain E1_EMPIRICAL_CROSS_SYSTEM_EVIDENCE;
- empirical observations never overwrite or promote themselves into official edges;
- existing A3 analytical activity mappings remain separate;
- installation performs no network access and no database writes;
- live sync writes only to the explicitly supplied crosswalk DB/raw directory.
