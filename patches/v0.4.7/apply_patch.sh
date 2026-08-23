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

if [[ "$CURRENT" != "0.4.6" ]]; then
  echo "ERROR: v0.4.7 patch requires base version 0.4.6; found '$CURRENT'." >&2
  exit 3
fi

(
  cd "$PATCH_DIR"
  sha256sum -c SHA256SUMS
)

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP=".patch_backups/v0_4_7-${STAMP}"
mkdir -p "$BACKUP/src/zse_tool" "$BACKUP/tests" "$BACKUP/examples"
cp pyproject.toml "$BACKUP/pyproject.toml"

for f in src/zse_tool/commercial_trajectory.py tests/test_commercial_trajectory_v0_4_7.py examples/koei_commercial_trajectory_evidence_v0_4_7.json COMMERCIAL_TRAJECTORY_V0_1.md SOURCES_V0_4_7.md; do
  if [[ -e "$f" ]]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$f" "$BACKUP/$f"
  fi
done

install -D -m 0644 "$PATCH_DIR/files/src/zse_tool/commercial_trajectory.py" src/zse_tool/commercial_trajectory.py
install -D -m 0644 "$PATCH_DIR/files/tests/test_commercial_trajectory_v0_4_7.py" tests/test_commercial_trajectory_v0_4_7.py
install -D -m 0644 "$PATCH_DIR/files/examples/koei_commercial_trajectory_evidence_v0_4_7.json" examples/koei_commercial_trajectory_evidence_v0_4_7.json
install -D -m 0644 "$PATCH_DIR/files/COMMERCIAL_TRAJECTORY_V0_1.md" COMMERCIAL_TRAJECTORY_V0_1.md
install -D -m 0644 "$PATCH_DIR/files/SOURCES_V0_4_7.md" SOURCES_V0_4_7.md

python - <<'PY'
from pathlib import Path
import re
p=Path("pyproject.toml")
text=p.read_text()
new,n=re.subn(r'(?m)^version\s*=\s*"0\.4\.6"\s*$', 'version = "0.4.7"', text, count=1)
if n != 1:
    raise SystemExit("ERROR: could not update version 0.4.6 -> 0.4.7")
p.write_text(new)
PY

python -m py_compile src/zse_tool/commercial_trajectory.py

echo "Applied ZSE Value Scanner v0.4.7 historical commercial trajectory foundation to: $TARGET"
echo "Backup: $BACKUP"
echo "No schema/data/entity/peer/competitor/market-share/financial-fact/job/artifact write was performed."
echo "Next: pytest -q"
