from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import sqlite3
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen


SEMANTIC_CATALOG_SCHEMA_VERSION = "classification-semantic-source-catalog-v0.1"
SEMANTIC_DB_SCHEMA_VERSION = "classification-semantic-audit-v0.1"
SEMANTIC_EVIDENCE_CLASS = "D2_DETERMINISTIC_SEMANTIC_AUDIT"
ALLOWED_SOURCE_HOSTS = {"unstats.un.org"}
MAX_SOURCE_BYTES = 2 * 1024 * 1024

SEMANTIC_STATUSES = {
    "text_equivalent",
    "same_title_definition_changed",
    "title_changed_definition_same",
    "title_and_definition_changed",
    "structural_reorganization",
}


class SemanticAuditError(RuntimeError):
    pass


@dataclass(frozen=True)
class SemanticSourceSpec:
    provider: str
    adapter: str
    system: str
    version: str
    url_template: str


class _VisibleTextParser(HTMLParser):
    _SKIP = {"script", "style", "noscript"}
    _BLOCK = {
        "article", "br", "dd", "div", "dl", "dt", "footer", "h1", "h2",
        "h3", "h4", "h5", "h6", "header", "li", "main", "nav", "ol", "p",
        "section", "table", "td", "th", "tr", "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self._SKIP:
            self._skip_depth += 1
        elif not self._skip_depth and tag in self._BLOCK:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif not self._skip_depth and tag in self._BLOCK:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self._parts.append(data)

    def text(self) -> str:
        return "".join(self._parts)


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _norm(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = value.replace("\u00a0", " ")
    return " ".join(value.split()).casefold()


def _validate_absolute_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise SemanticAuditError("semantic source URL must use HTTPS")
    if (parsed.hostname or "").lower() not in ALLOWED_SOURCE_HOSTS:
        raise SemanticAuditError(
            f"semantic source host is not allowlisted: {parsed.hostname!r}"
        )
    if parsed.username or parsed.password:
        raise SemanticAuditError("semantic source URL must not contain credentials")


def _validate_template(template: str) -> None:
    if template.count("{code}") != 1:
        raise SemanticAuditError("semantic source url_template needs exactly one {code}")
    _validate_absolute_url(template.replace("{code}", "2710"))


def load_catalog(path: Path) -> dict[tuple[str, str], SemanticSourceSpec]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if obj.get("schema_version") != SEMANTIC_CATALOG_SCHEMA_VERSION:
        raise SemanticAuditError("unsupported semantic source catalog schema")

    specs: dict[tuple[str, str], SemanticSourceSpec] = {}
    for item in obj.get("sources") or []:
        spec = SemanticSourceSpec(
            provider=str(item["provider"]),
            adapter=str(item["adapter"]),
            system=str(item["system"]),
            version=str(item["version"]),
            url_template=str(item["url_template"]),
        )
        if spec.adapter != "unsd-isic-detail-html":
            raise SemanticAuditError(f"unsupported semantic adapter: {spec.adapter}")
        _validate_template(spec.url_template)
        key = (spec.system, spec.version)
        if key in specs:
            raise SemanticAuditError(f"duplicate semantic source for {key}")
        specs[key] = spec

    if not specs:
        raise SemanticAuditError("semantic source catalog is empty")
    return specs


def _download(url: str, timeout: float = 45.0) -> bytes:
    _validate_absolute_url(url)
    req = Request(
        url,
        headers={"User-Agent": "zse-value-scanner/0.4.14 semantic-audit"},
    )
    error: Exception | None = None
    for attempt in range(3):
        try:
            with urlopen(req, timeout=timeout) as response:  # nosec B310
                data = response.read(MAX_SOURCE_BYTES + 1)
                if len(data) > MAX_SOURCE_BYTES:
                    raise SemanticAuditError("semantic source exceeds byte limit")
                return data
        except Exception as exc:
            error = exc
            if attempt < 2:
                time.sleep(0.4 * (attempt + 1))
    raise SemanticAuditError(f"semantic source download failed after retries: {error}")


_download_bounded = _download


def parse_unsd_isic_detail_html(
    data: bytes,
    *,
    expected_version: str,
    expected_code: str,
) -> dict[str, str]:
    try:
        raw = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise SemanticAuditError(f"UNSD detail page is not UTF-8: {exc}") from exc

    parser = _VisibleTextParser()
    parser.feed(raw)
    visible = " ".join(parser.text().split())

    version_pattern = re.escape(expected_version)
    code_pattern = re.escape(expected_code)

    heading = re.search(
        rf"ISIC,\s*Rev\.\s*{version_pattern}\s*-\s*Code\s*{code_pattern}\b",
        visible,
        flags=re.IGNORECASE,
    )
    if not heading:
        raise SemanticAuditError(
            f"UNSD detail page did not identify ISIC Rev. {expected_version} "
            f"code {expected_code}"
        )

    class_match = re.search(
        rf"\bClass:\s*{code_pattern}\s*-\s*(.*?)\s*Explanatory note\b",
        visible,
        flags=re.IGNORECASE,
    )
    if not class_match:
        raise SemanticAuditError(
            f"UNSD detail page did not expose class title for {expected_code}"
        )
    title = " ".join(class_match.group(1).split())

    note_match = re.search(
        r"\bExplanatory note\b(.*?)(?:\bCorrespondence\b|\bUNSD classifications\b)",
        visible,
        flags=re.IGNORECASE,
    )
    if not note_match:
        raise SemanticAuditError(
            f"UNSD detail page did not expose explanatory note for {expected_code}"
        )
    note = " ".join(note_match.group(1).split())
    if not note:
        raise SemanticAuditError(f"empty explanatory note for {expected_code}")

    return {
        "system": "ISIC",
        "version": expected_version,
        "code": expected_code,
        "title": title,
        "explanatory_note": note,
    }


def _connect(path: Path, *, readonly: bool = False) -> sqlite3.Connection:
    path = path.expanduser().resolve()
    if readonly:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    else:
        conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _ensure_crosswalk_db(conn: sqlite3.Connection) -> None:
    required = {"metadata", "crosswalk_sources", "crosswalk_edges"}
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    missing = sorted(required - tables)
    if missing:
        raise SemanticAuditError(
            f"database is not a v0.4.13 crosswalk DB; missing tables: {missing}"
        )


def _init_semantic_schema(conn: sqlite3.Connection) -> None:
    _ensure_crosswalk_db(conn)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS semantic_metadata(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS semantic_definitions(
            system TEXT NOT NULL,
            version TEXT NOT NULL,
            code TEXT NOT NULL,
            provider TEXT NOT NULL,
            adapter TEXT NOT NULL,
            source_url TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            raw_path TEXT NOT NULL,
            raw_sha256 TEXT NOT NULL,
            title TEXT NOT NULL,
            explanatory_note TEXT NOT NULL,
            normalized_title TEXT NOT NULL,
            normalized_note TEXT NOT NULL,
            PRIMARY KEY(system, version, code)
        );

        CREATE TABLE IF NOT EXISTS semantic_audits(
            edge_id INTEGER PRIMARY KEY
                REFERENCES crosswalk_edges(edge_id),
            evidence_class TEXT NOT NULL,
            mapping_shape TEXT NOT NULL,
            semantic_status TEXT NOT NULL,
            title_equal INTEGER NOT NULL,
            definition_equal INTEGER NOT NULL,
            scope_direction TEXT NOT NULL,
            automatic_equivalence_asserted INTEGER NOT NULL,
            audited_at TEXT NOT NULL,
            from_raw_sha256 TEXT NOT NULL,
            to_raw_sha256 TEXT NOT NULL
        );
        """
    )
    conn.execute(
        "INSERT OR REPLACE INTO semantic_metadata(key,value) VALUES(?,?)",
        ("schema_version", SEMANTIC_DB_SCHEMA_VERSION),
    )


def prepare(source_db: Path, output_db: Path) -> dict[str, Any]:
    source_db = source_db.expanduser().resolve()
    output_db = output_db.expanduser().resolve()
    if output_db.exists():
        raise SemanticAuditError(f"output DB exists: {output_db}")

    with _connect(source_db, readonly=True) as src:
        _ensure_crosswalk_db(src)
        integrity = src.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise SemanticAuditError(f"source integrity_check={integrity}")

    output_db.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output_db.parent, delete=False) as handle:
        tmp = Path(handle.name)
    try:
        shutil.copyfile(source_db, tmp)
        with _connect(tmp) as conn:
            _init_semantic_schema(conn)
            conn.commit()
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise SemanticAuditError(f"prepared integrity_check={integrity}")
        tmp.replace(output_db)
    finally:
        if tmp.exists():
            tmp.unlink()

    return {
        "source_db": str(source_db),
        "output_db": str(output_db),
        "semantic_schema_version": SEMANTIC_DB_SCHEMA_VERSION,
    }


def _mapping_shape(conn: sqlite3.Connection, edge: sqlite3.Row) -> str:
    forward_count = conn.execute(
        """
        SELECT COUNT(DISTINCT to_code)
        FROM crosswalk_edges
        WHERE source_id=? AND from_code=?
        """,
        (edge["source_id"], edge["from_code"]),
    ).fetchone()[0]
    reverse_count = conn.execute(
        """
        SELECT COUNT(DISTINCT from_code)
        FROM crosswalk_edges
        WHERE source_id=? AND to_code=?
        """,
        (edge["source_id"], edge["to_code"]),
    ).fetchone()[0]

    if forward_count == reverse_count == 1:
        return "one_to_one"
    if forward_count > 1 and reverse_count == 1:
        return "one_to_many"
    if forward_count == 1 and reverse_count > 1:
        return "many_to_one"
    return "many_to_many"


def assess_semantics(
    *,
    mapping_shape: str,
    from_title: str,
    from_note: str,
    to_title: str,
    to_note: str,
) -> dict[str, Any]:
    title_equal = _norm(from_title) == _norm(to_title)
    definition_equal = _norm(from_note) == _norm(to_note)

    if mapping_shape != "one_to_one":
        status = "structural_reorganization"
    elif title_equal and definition_equal:
        status = "text_equivalent"
    elif title_equal:
        status = "same_title_definition_changed"
    elif definition_equal:
        status = "title_changed_definition_same"
    else:
        status = "title_and_definition_changed"

    if status not in SEMANTIC_STATUSES:
        raise SemanticAuditError(f"unexpected semantic status: {status}")

    return {
        "semantic_status": status,
        "title_equal": title_equal,
        "definition_equal": definition_equal,
        "scope_direction": "not_inferred",
        "automatic_equivalence_asserted": False,
    }


def _fetch_or_get_definition(
    conn: sqlite3.Connection,
    *,
    spec: SemanticSourceSpec,
    code: str,
    raw_dir: Path,
) -> sqlite3.Row:
    existing = conn.execute(
        """
        SELECT *
        FROM semantic_definitions
        WHERE system=? AND version=? AND code=?
        """,
        (spec.system, spec.version, code),
    ).fetchone()
    if existing:
        return existing

    if not re.fullmatch(r"\d{4}", code):
        raise SemanticAuditError(
            f"semantic audit currently expects four-digit class code, got {code!r}"
        )

    url = spec.url_template.replace("{code}", code)
    data = _download_bounded(url)
    digest = _sha(data)
    definition = parse_unsd_isic_detail_html(
        data,
        expected_version=spec.version,
        expected_code=code,
    )

    root = raw_dir.expanduser().resolve() / f"{spec.system}-{spec.version}" / code
    root.mkdir(parents=True, exist_ok=True)
    raw_path = root / f"{digest}.html"
    if not raw_path.exists():
        raw_path.write_bytes(data)

    retrieved_at = _now()
    conn.execute(
        """
        INSERT INTO semantic_definitions(
            system,version,code,provider,adapter,source_url,retrieved_at,
            raw_path,raw_sha256,title,explanatory_note,
            normalized_title,normalized_note
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            spec.system,
            spec.version,
            code,
            spec.provider,
            spec.adapter,
            url,
            retrieved_at,
            str(raw_path),
            digest,
            definition["title"],
            definition["explanatory_note"],
            _norm(definition["title"]),
            _norm(definition["explanatory_note"]),
        ),
    )
    return conn.execute(
        """
        SELECT *
        FROM semantic_definitions
        WHERE system=? AND version=? AND code=?
        """,
        (spec.system, spec.version, code),
    ).fetchone()


def audit_edge(
    db: Path,
    catalog: Path,
    raw_dir: Path,
    *,
    from_system: str,
    from_version: str,
    from_code: str,
    to_system: str,
    to_version: str,
    to_code: str,
) -> dict[str, Any]:
    specs = load_catalog(catalog)
    db = db.expanduser().resolve()

    with _connect(db) as conn:
        _init_semantic_schema(conn)
        edge = conn.execute(
            """
            SELECT *
            FROM crosswalk_edges
            WHERE from_system=? AND from_version=? AND from_code=?
              AND to_system=? AND to_version=? AND to_code=?
            """,
            (
                from_system,
                from_version,
                from_code,
                to_system,
                to_version,
                to_code,
            ),
        ).fetchone()
        if edge is None:
            raise SemanticAuditError("official crosswalk edge not found")

        from_spec = specs.get((from_system, from_version))
        to_spec = specs.get((to_system, to_version))
        if from_spec is None:
            raise SemanticAuditError(
                f"no semantic source configured for {(from_system, from_version)}"
            )
        if to_spec is None:
            raise SemanticAuditError(
                f"no semantic source configured for {(to_system, to_version)}"
            )

        from_def = _fetch_or_get_definition(
            conn, spec=from_spec, code=from_code, raw_dir=raw_dir
        )
        to_def = _fetch_or_get_definition(
            conn, spec=to_spec, code=to_code, raw_dir=raw_dir
        )

        mapping_shape = _mapping_shape(conn, edge)
        assessment = assess_semantics(
            mapping_shape=mapping_shape,
            from_title=from_def["title"],
            from_note=from_def["explanatory_note"],
            to_title=to_def["title"],
            to_note=to_def["explanatory_note"],
        )
        audited_at = _now()

        conn.execute(
            """
            INSERT OR REPLACE INTO semantic_audits(
                edge_id,evidence_class,mapping_shape,semantic_status,
                title_equal,definition_equal,scope_direction,
                automatic_equivalence_asserted,audited_at,
                from_raw_sha256,to_raw_sha256
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                edge["edge_id"],
                SEMANTIC_EVIDENCE_CLASS,
                mapping_shape,
                assessment["semantic_status"],
                int(assessment["title_equal"]),
                int(assessment["definition_equal"]),
                assessment["scope_direction"],
                int(assessment["automatic_equivalence_asserted"]),
                audited_at,
                from_def["raw_sha256"],
                to_def["raw_sha256"],
            ),
        )
        conn.commit()

        return {
            "edge": {
                "edge_id": edge["edge_id"],
                "source_id": edge["source_id"],
                "from": {
                    "system": from_system,
                    "version": from_version,
                    "code": from_code,
                    "title": from_def["title"],
                    "source_url": from_def["source_url"],
                },
                "to": {
                    "system": to_system,
                    "version": to_version,
                    "code": to_code,
                    "title": to_def["title"],
                    "source_url": to_def["source_url"],
                },
                "official_change_type": edge["official_change_type"],
                "official_note": edge["official_note"],
            },
            "evidence_class": SEMANTIC_EVIDENCE_CLASS,
            "mapping_shape": mapping_shape,
            **assessment,
            "policy": {
                "graph_topology_is_not_semantic_equivalence": True,
                "scope_direction_inferred_from_text_diff": False,
                "automatic_company_classification_created": False,
                "llm_equivalence_promotion_allowed": False,
            },
        }


def show_audit(
    db: Path,
    *,
    from_system: str,
    from_version: str,
    from_code: str,
    to_system: str,
    to_version: str,
    to_code: str,
) -> dict[str, Any]:
    with _connect(db, readonly=True) as conn:
        _ensure_crosswalk_db(conn)
        edge = conn.execute(
            """
            SELECT *
            FROM crosswalk_edges
            WHERE from_system=? AND from_version=? AND from_code=?
              AND to_system=? AND to_version=? AND to_code=?
            """,
            (
                from_system,
                from_version,
                from_code,
                to_system,
                to_version,
                to_code,
            ),
        ).fetchone()
        if edge is None:
            raise SemanticAuditError("official crosswalk edge not found")

        audit = conn.execute(
            "SELECT * FROM semantic_audits WHERE edge_id=?",
            (edge["edge_id"],),
        ).fetchone()
        if audit is None:
            return {
                "edge_id": edge["edge_id"],
                "audited": False,
                "mapping_shape": _mapping_shape(conn, edge),
            }
        return {"edge_id": edge["edge_id"], "audited": True, **dict(audit)}


def status(db: Path) -> dict[str, Any]:
    with _connect(db, readonly=True) as conn:
        _ensure_crosswalk_db(conn)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "semantic_audits" not in tables:
            return {
                "database": str(db.expanduser().resolve()),
                "semantic_schema_version": None,
                "definition_count": 0,
                "audit_count": 0,
                "status_counts": {},
            }

        schema = conn.execute(
            "SELECT value FROM semantic_metadata WHERE key='schema_version'"
        ).fetchone()
        counts = {
            row[0]: row[1]
            for row in conn.execute(
                """
                SELECT semantic_status, COUNT(*)
                FROM semantic_audits
                GROUP BY semantic_status
                ORDER BY semantic_status
                """
            )
        }
        return {
            "database": str(db.expanduser().resolve()),
            "semantic_schema_version": schema[0] if schema else None,
            "definition_count": conn.execute(
                "SELECT COUNT(*) FROM semantic_definitions"
            ).fetchone()[0],
            "audit_count": conn.execute(
                "SELECT COUNT(*) FROM semantic_audits"
            ).fetchone()[0],
            "status_counts": counts,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare")
    p.add_argument("--source-db", type=Path, required=True)
    p.add_argument("--output-db", type=Path, required=True)

    p = sub.add_parser("audit-edge")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--raw-dir", type=Path, required=True)
    p.add_argument("--from-system", required=True)
    p.add_argument("--from-version", required=True)
    p.add_argument("--from-code", required=True)
    p.add_argument("--to-system", required=True)
    p.add_argument("--to-version", required=True)
    p.add_argument("--to-code", required=True)

    p = sub.add_parser("show")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--from-system", required=True)
    p.add_argument("--from-version", required=True)
    p.add_argument("--from-code", required=True)
    p.add_argument("--to-system", required=True)
    p.add_argument("--to-version", required=True)
    p.add_argument("--to-code", required=True)

    p = sub.add_parser("status")
    p.add_argument("--db", type=Path, required=True)

    args = parser.parse_args(argv)

    if args.cmd == "prepare":
        out = prepare(args.source_db, args.output_db)
    elif args.cmd == "audit-edge":
        out = audit_edge(
            args.db,
            args.catalog,
            args.raw_dir,
            from_system=args.from_system,
            from_version=args.from_version,
            from_code=args.from_code,
            to_system=args.to_system,
            to_version=args.to_version,
            to_code=args.to_code,
        )
    elif args.cmd == "show":
        out = show_audit(
            args.db,
            from_system=args.from_system,
            from_version=args.from_version,
            from_code=args.from_code,
            to_system=args.to_system,
            to_version=args.to_version,
            to_code=args.to_code,
        )
    else:
        out = status(args.db)

    print(json.dumps(out, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
