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

if [[ "$CURRENT" != "0.4.11" ]]; then
  echo "ERROR: v0.4.12 patch requires base version 0.4.11; found '$CURRENT'." >&2
  exit 3
fi

(
  cd "$PATCH_DIR"
  sha256sum -c SHA256SUMS
)

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP=".patch_backups/v0_4_12-${STAMP}"
mkdir -p "$BACKUP/src/zse_tool" "$BACKUP/tests" "$BACKUP/examples"
cp pyproject.toml "$BACKUP/pyproject.toml"

for f in \
  src/zse_tool/classification_mapping.py \
  tests/test_classification_mapping_v0_4_12.py \
  examples/activity_classification_mapping_catalog_v0_4_12.json \
  CLASSIFICATION_TRANSLATION_V0_1.md \
  SOURCES_V0_4_12.md
do
  if [[ -e "$f" ]]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$f" "$BACKUP/$f"
  fi
done

install -D -m 0644 \
  "$PATCH_DIR/files/src/zse_tool/classification_mapping.py" \
  src/zse_tool/classification_mapping.py

install -D -m 0644 \
  "$PATCH_DIR/files/tests/test_classification_mapping_v0_4_12.py" \
  tests/test_classification_mapping_v0_4_12.py

install -D -m 0644 \
  "$PATCH_DIR/files/examples/activity_classification_mapping_catalog_v0_4_12.json" \
  examples/activity_classification_mapping_catalog_v0_4_12.json

install -D -m 0644 \
  "$PATCH_DIR/files/CLASSIFICATION_TRANSLATION_V0_1.md" \
  CLASSIFICATION_TRANSLATION_V0_1.md

install -D -m 0644 \
  "$PATCH_DIR/files/SOURCES_V0_4_12.md" \
  SOURCES_V0_4_12.md

python - <<'PY'
from pathlib import Path
import re

p = Path("pyproject.toml")
text = p.read_text(encoding="utf-8")
new, n = re.subn(
    r'(?m)^version\s*=\s*"0\.4\.11"\s*$',
    'version = "0.4.12"',
    text,
    count=1,
)
if n != 1:
    raise SystemExit("ERROR: could not update version 0.4.11 -> 0.4.12")
p.write_text(new, encoding="utf-8")
PY

python -m py_compile \
  src/zse_tool/classification_mapping.py \
  tests/test_classification_mapping_v0_4_12.py

grep -q '^version = "0.4.12"$' pyproject.toml

echo "Applied ZSE Value Scanner v0.4.12 activity/classification translation pilot to: $TARGET"
echo "Backup: $BACKUP"
echo "Installation performed no network access and no database write."
echo "Next: pytest -q"
