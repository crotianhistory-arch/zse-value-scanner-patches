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
text=Path("pyproject.toml").read_text()
m=re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
print(m.group(1) if m else "")
PY
)"

if [[ "$CURRENT" != "0.4.7" ]]; then
  echo "ERROR: v0.4.8 patch requires base version 0.4.7; found '$CURRENT'." >&2
  exit 3
fi

(
  cd "$PATCH_DIR"
  sha256sum -c SHA256SUMS
)

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP=".patch_backups/v0_4_8-${STAMP}"
mkdir -p "$BACKUP/src/zse_tool" "$BACKUP/tests" "$BACKUP/examples"
cp pyproject.toml "$BACKUP/pyproject.toml"

for f in src/zse_tool/classification_backbone.py tests/test_classification_backbone_v0_4_8.py examples/eurostat_classification_catalog_v0_4_8.json CLASSIFICATION_BACKBONE_V0_1.md SOURCES_V0_4_8.md; do
  if [[ -e "$f" ]]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$f" "$BACKUP/$f"
  fi
done

mkdir -p src/zse_tool
cat "$PATCH_DIR"/files/src/zse_tool/fragments/classification_backbone.py.part* > src/zse_tool/classification_backbone.py
chmod 0644 src/zse_tool/classification_backbone.py
echo "751724e32a68fac0122d571ae21919e1b87f5b1daed73a4315881bc3f47a77ca  src/zse_tool/classification_backbone.py" | sha256sum -c -
mkdir -p tests
cat "$PATCH_DIR"/files/tests/fragments/test_classification_backbone_v0_4_8.py.part* > tests/test_classification_backbone_v0_4_8.py
chmod 0644 tests/test_classification_backbone_v0_4_8.py
echo "b85570ed5b51721fcc057f2457ea2bac8cb65e46ca5728541d2ef10811123dd3  tests/test_classification_backbone_v0_4_8.py" | sha256sum -c -
install -D -m 0644 "$PATCH_DIR/files/examples/eurostat_classification_catalog_v0_4_8.json" examples/eurostat_classification_catalog_v0_4_8.json
install -D -m 0644 "$PATCH_DIR/files/CLASSIFICATION_BACKBONE_V0_1.md" CLASSIFICATION_BACKBONE_V0_1.md
install -D -m 0644 "$PATCH_DIR/files/SOURCES_V0_4_8.md" SOURCES_V0_4_8.md

python - <<'PY'
from pathlib import Path
import re
p=Path("pyproject.toml")
text=p.read_text()
new,n=re.subn(r'(?m)^version\s*=\s*"0\.4\.7"\s*$', 'version = "0.4.8"', text, count=1)
if n != 1:
    raise SystemExit("ERROR: could not update version 0.4.7 -> 0.4.8")
p.write_text(new)
PY

python -m py_compile src/zse_tool/classification_backbone.py

echo "Applied ZSE Value Scanner v0.4.8 official classification backbone to: $TARGET"
echo "Backup: $BACKUP"
echo "No data/zse.sqlite, warehouse metadata, company, peer, competitor, financial-fact, job or artifact write was performed by the installer."
echo "The optional classification sync command creates a separate rebuildable SQLite DB only at the path you explicitly provide."
echo "Next: pytest -q"
