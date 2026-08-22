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

if [[ "$CURRENT" != "0.4.2" ]]; then
  echo "ERROR: v0.4.3 patch requires base version 0.4.2; found '$CURRENT'." >&2
  exit 3
fi

(
  cd "$PATCH_DIR"
  sha256sum -c SHA256SUMS
)

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP=".patch_backups/v0_4_3-${STAMP}"
mkdir -p "$BACKUP/src/zse_tool" "$BACKUP/tests"
cp pyproject.toml "$BACKUP/pyproject.toml"

for f in src/zse_tool/esef_tagged_activity.py tests/test_esef_tagged_activity_v0_4_3.py PILOT_V0_4_3.md SOURCES_V0_4_3.md; do
  if [[ -e "$f" ]]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$f" "$BACKUP/$f"
  fi
done

install -D -m 0644 "$PATCH_DIR/files/src/zse_tool/esef_tagged_activity.py" src/zse_tool/esef_tagged_activity.py
install -D -m 0644 "$PATCH_DIR/files/tests/test_esef_tagged_activity_v0_4_3.py" tests/test_esef_tagged_activity_v0_4_3.py
install -D -m 0644 "$PATCH_DIR/files/PILOT_V0_4_3.md" PILOT_V0_4_3.md
install -D -m 0644 "$PATCH_DIR/files/SOURCES_V0_4_3.md" SOURCES_V0_4_3.md

python - <<'PY'
from pathlib import Path
import re
p=Path("pyproject.toml")
text=p.read_text()
new,n=re.subn(r'(?m)^version\s*=\s*"0\.4\.2"\s*$', 'version = "0.4.3"', text, count=1)
if n != 1:
    raise SystemExit("ERROR: could not update version 0.4.2 -> 0.4.3")
p.write_text(new)
PY

python -m py_compile src/zse_tool/esef_tagged_activity.py

echo "Applied ZSE Value Scanner v0.4.3 structured tagged activity extraction to: $TARGET"
echo "Backup: $BACKUP"
echo "No schema/data/entity/peer/similarity/financial-fact/job/artifact write was performed."
echo "Next: pytest -q"
