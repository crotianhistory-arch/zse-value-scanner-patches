from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

import zse_tool.classification_semantic_audit as sa


def make_crosswalk_db(path: Path, edges: list[tuple[str, str]]) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        INSERT INTO metadata VALUES('schema_version','official-classification-crosswalk-v0.1');

        CREATE TABLE crosswalk_sources(
            source_id TEXT PRIMARY KEY,
            provider TEXT,
            adapter TEXT,
            source_url TEXT,
            from_system TEXT,
            from_version TEXT,
            to_system TEXT,
            to_version TEXT,
            evidence_class TEXT,
            retrieved_at TEXT,
            raw_path TEXT,
            raw_sha256 TEXT,
            edge_count INT,
            from_code_count INT,
            to_code_count INT
        );

        CREATE TABLE crosswalk_edges(
            edge_id INTEGER PRIMARY KEY,
            source_id TEXT,
            from_system TEXT,
            from_version TEXT,
            from_code TEXT,
            to_system TEXT,
            to_version TEXT,
            to_code TEXT,
            relation TEXT,
            official_change_type TEXT,
            official_note TEXT,
            evidence_class TEXT
        );
        """
    )
    conn.execute(
        """
        INSERT INTO crosswalk_sources VALUES(
            'S','UNSD','fixture','https://unstats.un.org/x',
            'ISIC','4','ISIC','5','O1_OFFICIAL_CROSSWALK',
            '2026-08-24T00:00:00Z','/tmp/x','0',?,?,?
        )
        """,
        (len(edges), len({a for a, _ in edges}), len({b for _, b in edges})),
    )
    for a, b in edges:
        conn.execute(
            """
            INSERT INTO crosswalk_edges(
                source_id,from_system,from_version,from_code,
                to_system,to_version,to_code,relation,
                official_change_type,official_note,evidence_class
            )
            VALUES(
                'S','ISIC','4',?,
                'ISIC','5',?,'official_correspondence',
                'fixture change','fixture note','O1_OFFICIAL_CROSSWALK'
            )
            """,
            (a, b),
        )
    conn.commit()
    conn.close()


def catalog(path: Path) -> Path:
    p = path / "catalog.json"
    p.write_text(json.dumps({
        "schema_version": sa.SEMANTIC_CATALOG_SCHEMA_VERSION,
        "sources": [
            {
                "provider": "UNSD",
                "adapter": "unsd-isic-detail-html",
                "system": "ISIC",
                "version": "4",
                "url_template":
                    "https://unstats.un.org/unsd/classifications/Econ/Detail/EN/27/{code}",
            },
            {
                "provider": "UNSD",
                "adapter": "unsd-isic-detail-html",
                "system": "ISIC",
                "version": "5",
                "url_template":
                    "https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/EN/2095/{code}",
            },
        ],
    }))
    return p


def html_page(version: str, code: str, title: str, note: str) -> bytes:
    tail = (
        "<h4>Correspondence</h4>"
        if version == "4"
        else "<h2>UNSD classifications</h2>"
    )
    return f"""
    <html><body>
      <h3>ISIC, Rev. {version} - Code {code}</h3>
      <h4>Hierarchy</h4>
      <div>Class:</div>
      <div>{code} - {title}</div>
      <h4>Explanatory note</h4>
      <div>{note}</div>
      {tail}
    </body></html>
    """.encode()


def test_parse_unsd_detail_html():
    result = sa.parse_unsd_isic_detail_html(
        html_page("4", "2710", "Electrical equipment", "Includes transformers."),
        expected_version="4",
        expected_code="2710",
    )
    assert result["title"] == "Electrical equipment"
    assert result["explanatory_note"] == "Includes transformers."


def test_parser_rejects_wrong_revision_or_code():
    with pytest.raises(sa.SemanticAuditError, match="did not identify"):
        sa.parse_unsd_isic_detail_html(
            html_page("4", "2710", "X", "Y"),
            expected_version="5",
            expected_code="2710",
        )


def test_catalog_rejects_nonallowlisted_host(tmp_path: Path):
    p = tmp_path / "catalog.json"
    p.write_text(json.dumps({
        "schema_version": sa.SEMANTIC_CATALOG_SCHEMA_VERSION,
        "sources": [{
            "provider": "X",
            "adapter": "unsd-isic-detail-html",
            "system": "ISIC",
            "version": "4",
            "url_template": "https://example.com/{code}",
        }],
    }))
    with pytest.raises(sa.SemanticAuditError, match="allowlisted"):
        sa.load_catalog(p)


def test_prepare_copies_crosswalk_without_touching_source(tmp_path: Path):
    src = tmp_path / "src.sqlite"
    out = tmp_path / "out.sqlite"
    make_crosswalk_db(src, [("2710", "2710")])
    before = src.read_bytes()

    result = sa.prepare(src, out)

    assert src.read_bytes() == before
    assert out.exists()
    assert result["semantic_schema_version"] == sa.SEMANTIC_DB_SCHEMA_VERSION
    conn = sqlite3.connect(out)
    try:
        assert conn.execute(
            "SELECT value FROM semantic_metadata WHERE key='schema_version'"
        ).fetchone()[0] == sa.SEMANTIC_DB_SCHEMA_VERSION
        assert conn.execute("SELECT COUNT(*) FROM crosswalk_edges").fetchone()[0] == 1
    finally:
        conn.close()


def test_assess_text_equivalent_is_cautious():
    result = sa.assess_semantics(
        mapping_shape="one_to_one",
        from_title="Same title",
        from_note="Same   note",
        to_title="same TITLE",
        to_note="same note",
    )
    assert result["semantic_status"] == "text_equivalent"
    assert result["automatic_equivalence_asserted"] is False
    assert result["scope_direction"] == "not_inferred"


def test_same_title_definition_change_is_not_equivalence():
    result = sa.assess_semantics(
        mapping_shape="one_to_one",
        from_title="Same title",
        from_note="Includes A.",
        to_title="Same title",
        to_note="Includes A and B.",
    )
    assert result["semantic_status"] == "same_title_definition_changed"
    assert result["title_equal"] is True
    assert result["definition_equal"] is False


def test_structural_shape_overrides_text_identity():
    result = sa.assess_semantics(
        mapping_shape="one_to_many",
        from_title="Same title",
        from_note="Same note",
        to_title="Same title",
        to_note="Same note",
    )
    assert result["semantic_status"] == "structural_reorganization"


def test_audit_edge_preserves_official_edges_and_raw(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source = tmp_path / "source.sqlite"
    db = tmp_path / "semantic.sqlite"
    make_crosswalk_db(source, [("2710", "2710")])
    sa.prepare(source, db)
    cat = catalog(tmp_path)
    raw = tmp_path / "raw"

    pages = {
        "/27/2710": html_page(
            "4", "2710", "Electrical equipment",
            "Includes transformers. Excludes electronic transformers, see 2610.",
        ),
        "/2095/2710": html_page(
            "5", "2710", "Electrical equipment",
            "Includes transformers. Excludes electronic transformers, see 2619.",
        ),
    }

    def fake_download(url: str) -> bytes:
        for suffix, body in pages.items():
            if url.endswith(suffix):
                return body
        raise AssertionError(url)

    monkeypatch.setattr(sa, "_download_bounded", fake_download)

    before = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM crosswalk_edges"
    ).fetchone()[0]

    result = sa.audit_edge(
        db,
        cat,
        raw,
        from_system="ISIC",
        from_version="4",
        from_code="2710",
        to_system="ISIC",
        to_version="5",
        to_code="2710",
    )

    assert result["semantic_status"] == "same_title_definition_changed"
    assert result["mapping_shape"] == "one_to_one"
    assert result["policy"]["llm_equivalence_promotion_allowed"] is False
    assert result["scope_direction"] == "not_inferred"

    conn = sqlite3.connect(db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM crosswalk_edges").fetchone()[0] == before
        assert conn.execute("SELECT COUNT(*) FROM semantic_definitions").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM semantic_audits").fetchone()[0] == 1
    finally:
        conn.close()

    assert len(list(raw.rglob("*.html"))) == 2


def test_audit_reuses_cached_definitions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source = tmp_path / "source.sqlite"
    db = tmp_path / "semantic.sqlite"
    make_crosswalk_db(source, [("1073", "1073")])
    sa.prepare(source, db)
    cat = catalog(tmp_path)
    raw = tmp_path / "raw"

    calls = []

    def fake_download(url: str) -> bytes:
        calls.append(url)
        version = "4" if "/27/" in url else "5"
        return html_page(version, "1073", "Confectionery", "Same note")

    monkeypatch.setattr(sa, "_download_bounded", fake_download)

    kwargs = dict(
        from_system="ISIC",
        from_version="4",
        from_code="1073",
        to_system="ISIC",
        to_version="5",
        to_code="1073",
    )
    sa.audit_edge(db, cat, raw, **kwargs)
    sa.audit_edge(db, cat, raw, **kwargs)

    assert len(calls) == 2


def test_structural_one_to_many_audit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source = tmp_path / "source.sqlite"
    db = tmp_path / "semantic.sqlite"
    make_crosswalk_db(source, [("4791", "4711"), ("4791", "4721")])
    sa.prepare(source, db)
    cat = catalog(tmp_path)

    def fake_download(url: str) -> bytes:
        if "/27/4791" in url:
            return html_page("4", "4791", "Retail via Internet", "Channel-defined retail.")
        code = url.rsplit("/", 1)[-1]
        return html_page("5", code, f"Retail {code}", "Product-defined retail.")

    monkeypatch.setattr(sa, "_download_bounded", fake_download)
    result = sa.audit_edge(
        db,
        cat,
        tmp_path / "raw",
        from_system="ISIC",
        from_version="4",
        from_code="4791",
        to_system="ISIC",
        to_version="5",
        to_code="4711",
    )
    assert result["mapping_shape"] == "one_to_many"
    assert result["semantic_status"] == "structural_reorganization"


def test_status_reports_counts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source = tmp_path / "source.sqlite"
    db = tmp_path / "semantic.sqlite"
    make_crosswalk_db(source, [("2710", "2710")])
    sa.prepare(source, db)
    cat = catalog(tmp_path)
    monkeypatch.setattr(
        sa,
        "_download_bounded",
        lambda url: html_page(
            "4" if "/27/" in url else "5",
            "2710",
            "Same",
            "Same",
        ),
    )
    sa.audit_edge(
        db,
        cat,
        tmp_path / "raw",
        from_system="ISIC",
        from_version="4",
        from_code="2710",
        to_system="ISIC",
        to_version="5",
        to_code="2710",
    )
    result = sa.status(db)
    assert result["definition_count"] == 2
    assert result["audit_count"] == 1
    assert result["status_counts"] == {"text_equivalent": 1}
