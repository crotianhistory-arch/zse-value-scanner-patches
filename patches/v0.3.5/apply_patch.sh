#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-.}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$TARGET/pyproject.toml" || ! -d "$TARGET/src/zse_tool" ]]; then
  echo "ERROR: target does not look like the ZSE Value Scanner project: $TARGET" >&2
  exit 2
fi

CURRENT_VERSION="$(python3 - <<'PY' "$TARGET/pyproject.toml"
import re, sys
text = open(sys.argv[1], encoding='utf-8').read()
m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
print(m.group(1) if m else '')
PY
)"

if [[ "$CURRENT_VERSION" != "0.3.4" ]]; then
  echo "ERROR: v0.3.5 patch requires base version 0.3.4; found '$CURRENT_VERSION'." >&2
  exit 3
fi

(
  cd "$PATCH_DIR"
  sha256sum -c SHA256SUMS
)

STAMP="$(date -u +%Y%m%d_%H%M%S)"
BACKUP="$TARGET/.patch_backups/v0_3_5-$STAMP"
mkdir -p "$BACKUP/src/zse_tool" "$BACKUP/scripts" "$BACKUP/tests"
cp -a "$TARGET/pyproject.toml" "$BACKUP/pyproject.toml"

for rel in \
  src/zse_tool/gleif.py \
  src/zse_tool/gleif_ingest.py \
  scripts/gleif_confirm.py \
  tests/test_gleif_ingest_v0_3_5.py \
  SOURCES_V0_3_5.md
do
  if [[ -e "$TARGET/$rel" ]]; then
    mkdir -p "$BACKUP/$(dirname "$rel")"
    cp -a "$TARGET/$rel" "$BACKUP/$rel"
  fi
done

install -m 0644 "$PATCH_DIR/files/src/zse_tool/gleif.py" "$TARGET/src/zse_tool/gleif.py"
install -m 0644 "$PATCH_DIR/files/src/zse_tool/gleif_ingest.py" "$TARGET/src/zse_tool/gleif_ingest.py"
mkdir -p "$TARGET/scripts" "$TARGET/tests"
install -m 0755 "$PATCH_DIR/files/scripts/gleif_confirm.py" "$TARGET/scripts/gleif_confirm.py"
install -m 0644 "$PATCH_DIR/files/tests/test_gleif_ingest_v0_3_5.py" "$TARGET/tests/test_gleif_ingest_v0_3_5.py"
install -m 0644 "$PATCH_DIR/files/SOURCES_V0_3_5.md" "$TARGET/SOURCES_V0_3_5.md"

python3 - <<'PY' "$TARGET/pyproject.toml"
from pathlib import Path
import re, sys
path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')
new, n = re.subn(r'^(version\s*=\s*)"0\.3\.4"', r'\1"0.3.5"', text, count=1, flags=re.M)
if n != 1:
    raise SystemExit('ERROR: expected exactly one version = "0.3.4" line')
path.write_text(new, encoding='utf-8')
PY

echo "Applied ZSE Value Scanner v0.3.5 confirmed GLEIF identity persistence to: $TARGET"
echo "Backup: $BACKUP"
echo "No schema migration was performed."
echo "Existing financial data/reports were not deleted or rewritten."
echo "Next: pytest -q"
echo "Then keep ZSE_WAREHOUSE_DIR pointed at /scratch before the live confirmation pilot."
