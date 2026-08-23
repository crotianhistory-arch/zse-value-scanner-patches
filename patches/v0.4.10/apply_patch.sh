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
text=Path('pyproject.toml').read_text()
m=re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
print(m.group(1) if m else '')
PY
)"
if [[ "$CURRENT" != "0.4.9" ]]; then
  echo "ERROR: v0.4.10 patch requires base version 0.4.9; found '$CURRENT'." >&2
  exit 3
fi

(
  cd "$PATCH_DIR"
  sha256sum -c SHA256SUMS
)

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP=".patch_backups/v0_4_10-${STAMP}"
mkdir -p "$BACKUP/src/zse_tool" "$BACKUP/tests" "$BACKUP/examples"
cp pyproject.toml "$BACKUP/pyproject.toml"
cp -a src/zse_tool/classification_backbone.py "$BACKUP/src/zse_tool/classification_backbone.py"
for f in tests/test_classification_sdmx_v0_4_10.py examples/eurostat_classification_catalog_v0_4_10.json CLASSIFICATION_BACKBONE_V0_2.md SOURCES_V0_4_10.md; do
  if [[ -e "$f" ]]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$f" "$BACKUP/$f"
  fi
done

TMP_MODULE="$(mktemp)"
cat "$PATCH_DIR"/files/src/zse_tool/fragments/classification_backbone.py.part* > "$TMP_MODULE"
echo "5665ff1557ca8ffd1f15cc602eb3ca7abb591d8e0f54afbde300b7ac8d2a4e0d  $TMP_MODULE" | sha256sum -c -
install -m 0644 "$TMP_MODULE" src/zse_tool/classification_backbone.py
rm -f "$TMP_MODULE"

TMP_TEST="$(mktemp)"
cat "$PATCH_DIR"/files/tests/fragments/test_classification_sdmx_v0_4_10.py.part* > "$TMP_TEST"
echo "8ca4ba62ac448e9691a775d97d7d196f812e7e06cd19aa3819a7d8dbaaec4e7e  $TMP_TEST" | sha256sum -c -
install -m 0644 "$TMP_TEST" tests/test_classification_sdmx_v0_4_10.py
rm -f "$TMP_TEST"

install -D -m 0644 "$PATCH_DIR/files/examples/eurostat_classification_catalog_v0_4_10.json" examples/eurostat_classification_catalog_v0_4_10.json
install -D -m 0644 "$PATCH_DIR/files/CLASSIFICATION_BACKBONE_V0_2.md" CLASSIFICATION_BACKBONE_V0_2.md
install -D -m 0644 "$PATCH_DIR/files/SOURCES_V0_4_10.md" SOURCES_V0_4_10.md

python - <<'PY'
from pathlib import Path
import re
p=Path('pyproject.toml')
text=p.read_text()
new,n=re.subn(r'(?m)^version\s*=\s*"0\.4\.9"\s*$', 'version = "0.4.10"', text, count=1)
if n != 1:
    raise SystemExit('ERROR: could not update version 0.4.9 -> 0.4.10')
p.write_text(new)
PY

echo "5665ff1557ca8ffd1f15cc602eb3ca7abb591d8e0f54afbde300b7ac8d2a4e0d  src/zse_tool/classification_backbone.py" | sha256sum -c -
echo "8ca4ba62ac448e9691a775d97d7d196f812e7e06cd19aa3819a7d8dbaaec4e7e  tests/test_classification_sdmx_v0_4_10.py" | sha256sum -c -
python -m py_compile src/zse_tool/classification_backbone.py

echo "Applied ZSE Value Scanner v0.4.10 Eurostat SDMX classification snapshot to: $TARGET"
echo "Backup: $BACKUP"
echo "Installation performed no network access and no database write."
echo "Next: pytest -q"
