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

if [[ "$CURRENT_VERSION" != "0.3.3" ]]; then
  echo "ERROR: v0.3.4 patch requires base version 0.3.3; found '$CURRENT_VERSION'." >&2
  exit 3
fi

STAMP="$(date -u +%Y%m%d_%H%M%S)"
BACKUP="$TARGET/.patch_backups/v0_3_4-$STAMP"
mkdir -p "$BACKUP/src/zse_tool" "$BACKUP/scripts" "$BACKUP/tests"
cp -a "$TARGET/pyproject.toml" "$BACKUP/pyproject.toml"
for rel in src/zse_tool/gleif.py scripts/gleif_preflight.py tests/test_gleif_v0_3_4.py SOURCES_V0_3_4.md; do
  if [[ -e "$TARGET/$rel" ]]; then
    mkdir -p "$BACKUP/$(dirname "$rel")"
    cp -a "$TARGET/$rel" "$BACKUP/$rel"
  fi
done

install -m 0644 "$PATCH_DIR/files/src/zse_tool/gleif.py" "$TARGET/src/zse_tool/gleif.py"
mkdir -p "$TARGET/scripts" "$TARGET/tests"
install -m 0755 "$PATCH_DIR/files/scripts/gleif_preflight.py" "$TARGET/scripts/gleif_preflight.py"
install -m 0644 "$PATCH_DIR/files/tests/test_gleif_v0_3_4.py" "$TARGET/tests/test_gleif_v0_3_4.py"
install -m 0644 "$PATCH_DIR/files/SOURCES_V0_3_4.md" "$TARGET/SOURCES_V0_3_4.md"

python3 - <<'PY' "$TARGET/pyproject.toml"
from pathlib import Path
import re, sys
path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')
new, n = re.subn(r'^(version\s*=\s*)"0\.3\.3"', r'\1"0.3.4"', text, count=1, flags=re.M)
if n != 1:
    raise SystemExit("ERROR: expected exactly one version = \"0.3.3\" line")
path.write_text(new, encoding='utf-8')
PY

echo "Applied ZSE Value Scanner v0.3.4 bounded GLEIF discovery preflight to: $TARGET"
echo "Backup: $BACKUP"
echo "Existing data/ and SQLite files were not touched."
echo "Next: pytest -q"
echo "Then: python -m zse_tool.gleif --name 'KONČAR - ELEKTROINDUSTRIJA d.d.' --country HR --limit 5"
