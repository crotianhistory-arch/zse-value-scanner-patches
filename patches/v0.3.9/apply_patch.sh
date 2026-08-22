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

if [[ "$CURRENT" != "0.3.8" ]]; then
  echo "ERROR: v0.3.9 patch requires base version 0.3.8; found '$CURRENT'." >&2
  exit 3
fi

(
  cd "$PATCH_DIR"
  sha256sum -c SHA256SUMS
)

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP=".patch_backups/v0_3_9-${STAMP}"
mkdir -p "$BACKUP/src/zse_tool" "$BACKUP/tests" "$BACKUP/scripts"

cp pyproject.toml "$BACKUP/pyproject.toml"
cp src/zse_tool/zse_identity.py "$BACKUP/src/zse_tool/zse_identity.py"

for f in tests/test_zse_identity_v0_3_9.py SOURCES_V0_3_9.md; do
  if [[ -e "$f" ]]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$f" "$BACKUP/$f"
  fi
done

python "$PATCH_DIR/files/scripts/patch_zse_identity_v0_3_9.py" \
  src/zse_tool/zse_identity.py

install -D -m 0644 \
  "$PATCH_DIR/files/tests/test_zse_identity_v0_3_9.py" \
  tests/test_zse_identity_v0_3_9.py

install -D -m 0644 \
  "$PATCH_DIR/files/SOURCES_V0_3_9.md" \
  SOURCES_V0_3_9.md

python - <<'PY'
from pathlib import Path
import re
p=Path("pyproject.toml")
text=p.read_text()
new,n=re.subn(r'(?m)^version\s*=\s*"0\.3\.8"\s*$', 'version = "0.3.9"', text, count=1)
if n != 1:
    raise SystemExit("ERROR: could not update version 0.3.8 -> 0.3.9")
p.write_text(new)
PY

python -m py_compile src/zse_tool/zse_identity.py

echo "Applied ZSE Value Scanner v0.3.9 ZSE issuer-name provenance parser fix to: $TARGET"
echo "Backup: $BACKUP"
echo "No schema/data/LEI/job/artifact write was performed."
echo "Next: pytest -q"
echo "Then rerun the read-only zse_identity corroboration pilot."
