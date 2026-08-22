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

if [[ "$CURRENT" != "0.3.6" ]]; then
  echo "ERROR: v0.3.7 patch requires base version 0.3.6; found '$CURRENT'." >&2
  exit 3
fi

(cd "$PATCH_DIR" && sha256sum -c SHA256SUMS)

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP=".patch_backups/v0_3_7-${STAMP}"
mkdir -p "$BACKUP/src/zse_tool" "$BACKUP/tests" "$BACKUP/scripts"
cp pyproject.toml "$BACKUP/pyproject.toml"
for f in src/zse_tool/gleif_resolve.py tests/test_gleif_resolve_v0_3_7.py scripts/gleif_identity_resolve.py SOURCES_V0_3_7.md; do
  if [[ -e "$f" ]]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$f" "$BACKUP/$f"
  fi
done

install -D -m 0644 "$PATCH_DIR/files/src/zse_tool/gleif_resolve.py" src/zse_tool/gleif_resolve.py
install -D -m 0644 "$PATCH_DIR/files/tests/test_gleif_resolve_v0_3_7.py" tests/test_gleif_resolve_v0_3_7.py
install -D -m 0755 "$PATCH_DIR/files/scripts/gleif_identity_resolve.py" scripts/gleif_identity_resolve.py
install -D -m 0644 "$PATCH_DIR/files/SOURCES_V0_3_7.md" SOURCES_V0_3_7.md

python - <<'PY'
from pathlib import Path
import re
p=Path("pyproject.toml")
text=p.read_text()
new,n=re.subn(r'(?m)^version\s*=\s*"0\.3\.6"\s*$', 'version = "0.3.7"', text, count=1)
if n != 1:
    raise SystemExit("ERROR: could not update version 0.3.6 -> 0.3.7")
p.write_text(new)
PY

echo "Applied ZSE Value Scanner v0.3.7 ISIN-first identity resolution to: $TARGET"
echo "Backup: $BACKUP"
echo "No schema migration was performed."
echo "gleif_resolve is read-only with respect to LEI/entity metadata."
echo "Next: pytest -q"
echo "Then: python -m zse_tool.gleif_resolve --all-unidentified --limit 5"
