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

if [[ "$CURRENT" != "0.4.8" ]]; then
  echo "ERROR: v0.4.9 patch requires base version 0.4.8; found '$CURRENT'." >&2
  exit 3
fi

(
  cd "$PATCH_DIR"
  sha256sum -c SHA256SUMS
)

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP=".patch_backups/v0_4_9-${STAMP}"
mkdir -p "$BACKUP/src/zse_tool" "$BACKUP/tests"
cp pyproject.toml "$BACKUP/pyproject.toml"
cp -a src/zse_tool/classification_backbone.py "$BACKUP/src/zse_tool/classification_backbone.py"
if [[ -e tests/test_classification_transport_v0_4_9.py ]]; then
  cp -a tests/test_classification_transport_v0_4_9.py "$BACKUP/tests/"
fi

python "$PATCH_DIR/files/tools/apply_classification_transport_hotfix.py" \
  src/zse_tool/classification_backbone.py
install -D -m 0644 "$PATCH_DIR/files/tests/test_classification_transport_v0_4_9.py" \
  tests/test_classification_transport_v0_4_9.py

python - <<'PY'
from pathlib import Path
import re
p=Path("pyproject.toml")
text=p.read_text()
new,n=re.subn(r'(?m)^version\s*=\s*"0\.4\.8"\s*$', 'version = "0.4.9"', text, count=1)
if n != 1:
    raise SystemExit("ERROR: could not update version 0.4.8 -> 0.4.9")
p.write_text(new)
PY

echo "5e0ee01ec660e4c12f697b616b483569c6a6f648139c714abb402fab69d9b66a  src/zse_tool/classification_backbone.py" | sha256sum -c -
echo "4a21f0ba2d7aa0ca6081cb503c9ed2fecbeee4024385ea96a9814f556e4ef5bb  tests/test_classification_transport_v0_4_9.py" | sha256sum -c -
python -m py_compile src/zse_tool/classification_backbone.py

echo "Applied ZSE Value Scanner v0.4.9 Cellar SPARQL transport hotfix to: $TARGET"
echo "Backup: $BACKUP"
echo "No classification/reference/operational database write was performed."
echo "Next: pytest -q"
