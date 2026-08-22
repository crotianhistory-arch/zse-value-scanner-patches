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

if [[ "$CURRENT" != "0.3.5" ]]; then
  echo "ERROR: v0.3.6 patch requires base version 0.3.5; found '$CURRENT'." >&2
  exit 3
fi

(
  cd "$PATCH_DIR"
  sha256sum -c SHA256SUMS
)

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP=".patch_backups/v0_3_6-${STAMP}"
mkdir -p "$BACKUP/src/zse_tool" "$BACKUP/tests" "$BACKUP/scripts"

cp pyproject.toml "$BACKUP/pyproject.toml"
for f in \
  src/zse_tool/gleif_review.py \
  tests/test_gleif_review_v0_3_6.py \
  scripts/gleif_batch_review.py \
  SOURCES_V0_3_6.md
do
  if [[ -e "$f" ]]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$f" "$BACKUP/$f"
  fi
done

install -D -m 0644 "$PATCH_DIR/files/src/zse_tool/gleif_review.py" src/zse_tool/gleif_review.py
install -D -m 0644 "$PATCH_DIR/files/tests/test_gleif_review_v0_3_6.py" tests/test_gleif_review_v0_3_6.py
install -D -m 0755 "$PATCH_DIR/files/scripts/gleif_batch_review.py" scripts/gleif_batch_review.py
install -D -m 0644 "$PATCH_DIR/files/SOURCES_V0_3_6.md" SOURCES_V0_3_6.md

python - <<'PY'
from pathlib import Path
import re
p=Path("pyproject.toml")
text=p.read_text()
new, n=re.subn(r'(?m)^version\s*=\s*"0\.3\.5"\s*$', 'version = "0.3.6"', text, count=1)
if n != 1:
    raise SystemExit("ERROR: could not update version 0.3.5 -> 0.3.6")
p.write_text(new)
PY

echo "Applied ZSE Value Scanner v0.3.6 read-only GLEIF batch review to: $TARGET"
echo "Backup: $BACKUP"
echo "No schema migration was performed."
echo "No LEI, ingestion-job or raw-artifact write is performed by gleif_review."
echo "Next: pytest -q"
echo "Then: python -m zse_tool.gleif_review --all-unidentified --limit 5"
