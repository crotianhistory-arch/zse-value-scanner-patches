from __future__ import annotations

import base64
import sys
import zlib
from pathlib import Path


_SHOWVOC_BLOCK_ZLIB_B64 = (
    "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"
)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"ERROR: {label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_classification_backbone_v0_4_11.py PATH")

    showvoc_code = zlib.decompress(
        base64.b64decode(_SHOWVOC_BLOCK_ZLIB_B64)
    ).decode("utf-8")

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        'ALLOWED_ENDPOINT_HOSTS = {"publications.europa.eu", "ec.europa.eu"}',
        'ALLOWED_ENDPOINT_HOSTS = {"publications.europa.eu", "ec.europa.eu", "showvoc.op.europa.eu"}',
        "endpoint allow-list",
    )

    dataclass_anchor = """@dataclass(frozen=True)
class SdmxSchemeSpec:
    key: str
    system: str
    version: str
    title_contains: str
    preferred_ids: tuple[str, ...]
    expected_item_count: int
    expected_levels: int
    expected_level_counts: dict[int, int]


@dataclass(frozen=True)
class PageResult:
"""

    dataclass_replacement = """@dataclass(frozen=True)
class SdmxSchemeSpec:
    key: str
    system: str
    version: str
    title_contains: str
    preferred_ids: tuple[str, ...]
    expected_item_count: int
    expected_levels: int
    expected_level_counts: dict[int, int]


@dataclass(frozen=True)
class ShowVocSchemeSpec:
    key: str
    system: str
    version: str
    project: str
    expected_item_count: int
    expected_levels: int
    expected_level_counts: dict[int, int]
    required_languages: tuple[str, ...]


@dataclass(frozen=True)
class PageResult:
"""

    text = replace_once(
        text,
        dataclass_anchor,
        dataclass_replacement,
        "ShowVocSchemeSpec insertion",
    )

    sync_marker = "\n\ndef sync(catalog: Path, output_db: Path, raw_dir: Path, *, replace: bool = False) -> dict[str, Any]:\n"
    if text.count(sync_marker) != 1:
        raise SystemExit(
            f"ERROR: ShowVoc code insertion: expected one sync marker, found {text.count(sync_marker)}"
        )
    text = text.replace(sync_marker, showvoc_code + sync_marker, 1)

    sync_anchor = """def sync(catalog: Path, output_db: Path, raw_dir: Path, *, replace: bool = False) -> dict[str, Any]:
    obj = json.loads(catalog.read_text(encoding="utf-8"))
    schema_version = obj.get("schema_version")
    if schema_version == "official-classification-catalog-v0.2":
        return _sync_sdmx(catalog, output_db, raw_dir, replace=replace)
    if schema_version == "official-classification-catalog-v0.1":
        return _sync_cellar(catalog, output_db, raw_dir, replace=replace)
    raise ClassificationError(f"unsupported classification catalog schema: {schema_version!r}")
"""

    sync_replacement = """def sync(catalog: Path, output_db: Path, raw_dir: Path, *, replace: bool = False) -> dict[str, Any]:
    obj = json.loads(catalog.read_text(encoding="utf-8"))
    schema_version = obj.get("schema_version")
    if schema_version == "official-classification-catalog-v0.3":
        return _sync_showvoc(catalog, output_db, raw_dir, replace=replace)
    if schema_version == "official-classification-catalog-v0.2":
        return _sync_sdmx(catalog, output_db, raw_dir, replace=replace)
    if schema_version == "official-classification-catalog-v0.1":
        return _sync_cellar(catalog, output_db, raw_dir, replace=replace)
    raise ClassificationError(f"unsupported classification catalog schema: {schema_version!r}")
"""

    text = replace_once(
        text,
        sync_anchor,
        sync_replacement,
        "sync dispatch",
    )

    path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
