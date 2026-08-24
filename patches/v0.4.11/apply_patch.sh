#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-.}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$TARGET"

if [[ ! -f pyproject.toml ]]; then
  echo "ERROR: pyproject.toml not found in target: $TARGET" >&2
  exit 2
fi

CURRENT="$(python - <<'PY'
from pathlib import Path
import re
text = Path("pyproject.toml").read_text(encoding="utf-8")
m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
print(m.group(1) if m else "")
PY
)"

if [[ "$CURRENT" != "0.4.10" ]]; then
  echo "ERROR: v0.4.11 patch requires base version 0.4.10; found '$CURRENT'." >&2
  exit 3
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "ERROR: tracked Git changes are present; commit/stash them before applying v0.4.11." >&2
    exit 4
  fi
fi

(
  cd "$PATCH_DIR"
  sha256sum -c SHA256SUMS
)

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP=".patch_backups/v0_4_11-${STAMP}"

mkdir -p \
  "$BACKUP/src/zse_tool" \
  "$BACKUP/tests" \
  "$BACKUP/examples"

cp pyproject.toml "$BACKUP/pyproject.toml"
cp -a src/zse_tool/classification_backbone.py \
  "$BACKUP/src/zse_tool/classification_backbone.py"

for f in \
  tests/test_classification_showvoc_v0_4_11.py \
  examples/eurostat_classification_catalog_v0_4_11.json \
  CLASSIFICATION_BACKBONE_V0_3.md \
  SOURCES_V0_4_11.md
do
  if [[ -e "$f" ]]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$f" "$BACKUP/$f"
  fi
done

python \
  "$PATCH_DIR/files/patch_classification_backbone_v0_4_11.py" \
  src/zse_tool/classification_backbone.py

install -D -m 0644 \
  "$PATCH_DIR/files/tests/test_classification_showvoc_v0_4_11.py" \
  tests/test_classification_showvoc_v0_4_11.py

install -D -m 0644 \
  "$PATCH_DIR/files/examples/eurostat_classification_catalog_v0_4_11.json" \
  examples/eurostat_classification_catalog_v0_4_11.json

install -D -m 0644 \
  "$PATCH_DIR/files/CLASSIFICATION_BACKBONE_V0_3.md" \
  CLASSIFICATION_BACKBONE_V0_3.md

install -D -m 0644 \
  "$PATCH_DIR/files/SOURCES_V0_4_11.md" \
  SOURCES_V0_4_11.md

python - <<'PY'
from pathlib import Path
import re

p = Path("pyproject.toml")
text = p.read_text(encoding="utf-8")
new, n = re.subn(
    r'(?m)^version\s*=\s*"0\.4\.10"\s*$',
    'version = "0.4.11"',
    text,
    count=1,
)
if n != 1:
    raise SystemExit("ERROR: could not update version 0.4.10 -> 0.4.11")
p.write_text(new, encoding="utf-8")
PY

python -m py_compile \
  src/zse_tool/classification_backbone.py \
  tests/test_classification_showvoc_v0_4_11.py

grep '^version' pyproject.toml

echo "Applied ZSE Value Scanner v0.4.11 ShowVoc classification backbone to: $TARGET"
echo "Backup: $BACKUP"
echo "Installation performed no network access and no database write."
echo "Next: pytest -q"
