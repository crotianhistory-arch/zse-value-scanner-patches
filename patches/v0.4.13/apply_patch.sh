#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 /path/to/zse_value_scanner_v0_1_0" >&2
    return 2 2>/dev/null || false
fi

PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$(cd "$1" && pwd)"

cd "$PATCH_DIR"
sha256sum -c SHA256SUMS

if [[ ! -f "$TARGET/pyproject.toml" || ! -d "$TARGET/src/zse_tool" ]]; then
    echo "ERROR: target does not look like the ZSE Value Scanner source tree" >&2
    return 1 2>/dev/null || false
fi

VERSION_LINE="$(grep '^version' "$TARGET/pyproject.toml" || true)"
if [[ "$VERSION_LINE" != 'version = "0.4.12"' && \
      "$VERSION_LINE" != 'version = "0.4.13"' ]]; then
    echo "ERROR: v0.4.13 patch requires source version 0.4.12 or an uncommitted v0.4.13 retry state" >&2
    echo "$VERSION_LINE" >&2
    return 1 2>/dev/null || false
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$TARGET/.patch_backups/v0_4_13-$STAMP"
mkdir -p "$BACKUP"

TOUCHED=(
    "pyproject.toml"
    "src/zse_tool/classification_crosswalk.py"
    "src/zse_tool/classification_crosswalk_unsd.py"
    "tests/test_classification_crosswalk_v0_4_13.py"
    "tests/test_classification_crosswalk_unsd_realshape_v0_4_13.py"
    "examples/official_crosswalk_catalog_v0_4_13.json"
    "CLASSIFICATION_CROSSWALK_V0_1.md"
    "SOURCES_V0_4_13.md"
)

for rel in "${TOUCHED[@]}"; do
    if [[ -f "$TARGET/$rel" ]]; then
        mkdir -p "$BACKUP/$(dirname "$rel")"
        cp "$TARGET/$rel" "$BACKUP/$rel"
    fi
done

install -m 0644 files/src/zse_tool/classification_crosswalk.py \
    "$TARGET/src/zse_tool/classification_crosswalk.py"
install -m 0644 files/src/zse_tool/classification_crosswalk_unsd.py \
    "$TARGET/src/zse_tool/classification_crosswalk_unsd.py"
install -m 0644 files/tests/test_classification_crosswalk_v0_4_13.py \
    "$TARGET/tests/test_classification_crosswalk_v0_4_13.py"
install -m 0644 files/tests/test_classification_crosswalk_unsd_realshape_v0_4_13.py \
    "$TARGET/tests/test_classification_crosswalk_unsd_realshape_v0_4_13.py"
install -m 0644 files/examples/official_crosswalk_catalog_v0_4_13.json \
    "$TARGET/examples/official_crosswalk_catalog_v0_4_13.json"
install -m 0644 files/CLASSIFICATION_CROSSWALK_V0_1.md \
    "$TARGET/CLASSIFICATION_CROSSWALK_V0_1.md"
install -m 0644 files/SOURCES_V0_4_13.md \
    "$TARGET/SOURCES_V0_4_13.md"

TARGET_PYPROJECT="$TARGET/pyproject.toml" python - <<'PY'
from pathlib import Path
import os

path = Path(os.environ["TARGET_PYPROJECT"])
text = path.read_text(encoding="utf-8")
old = 'version = "0.4.12"'
new = 'version = "0.4.13"'

if text.count(old) == 1:
    text = text.replace(old, new)
elif text.count(new) == 1:
    pass
else:
    raise SystemExit(
        "ERROR: expected exactly one v0.4.12 or v0.4.13 version marker"
    )

path.write_text(text, encoding="utf-8")
PY

python -m py_compile \
    "$TARGET/src/zse_tool/classification_crosswalk.py" \
    "$TARGET/src/zse_tool/classification_crosswalk_unsd.py" \
    "$TARGET/tests/test_classification_crosswalk_v0_4_13.py" \
    "$TARGET/tests/test_classification_crosswalk_unsd_realshape_v0_4_13.py"

grep '^version' "$TARGET/pyproject.toml"
echo "Applied ZSE Value Scanner v0.4.13 official crosswalk framework to: $TARGET"
echo "Backup: ${BACKUP#$TARGET/}"
echo "Installation performed no network access and no database write."
echo "Next: pytest -q"
