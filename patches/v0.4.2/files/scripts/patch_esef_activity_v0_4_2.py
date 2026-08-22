from __future__ import annotations

import sys
from pathlib import Path

CLASS_ANCHOR = '''def _fetch_bounded(\n'''
CLASS_INSERT = '''class EvidenceTooLarge(ValueError):\n    """Evidence object exceeded an explicit bounded-download limit."""\n\n\ndef _fetch_bounded(\n'''

OLD_CONTENT_LENGTH = '''                raise ValueError(f"evidence object exceeds byte limit: {length} > {max_bytes}")\n'''
NEW_CONTENT_LENGTH = '''                raise EvidenceTooLarge(f"evidence object exceeds byte limit: {length} > {max_bytes}")\n'''

OLD_STREAM_LIMIT = '''            raise ValueError(f"evidence object exceeds byte limit while downloading: > {max_bytes}")\n'''
NEW_STREAM_LIMIT = '''            raise EvidenceTooLarge(f"evidence object exceeds byte limit while downloading: > {max_bytes}")\n'''

OLD_BUILD = '''    if not filing.json_url:\n        raise ValueError("selected ESEF filing does not provide xBRL-JSON")\n    if not filing.xhtml_url:\n        raise ValueError("selected ESEF filing does not provide XHTML")\n\n    json_bytes = fetcher(filing.json_url, max_bytes=json_limit, timeout=timeout)\n    xhtml_bytes = fetcher(filing.xhtml_url, max_bytes=xhtml_limit, timeout=timeout)\n    xbrl_payload = parse_xbrl_json(json_bytes)\n    inventory = inventory_xbrl_activity(xbrl_payload)\n    narrative = extract_narrative_evidence(xhtml_bytes)\n'''

NEW_BUILD = '''    if not filing.json_url:\n        raise ValueError("selected ESEF filing does not provide xBRL-JSON")\n\n    # Structured xBRL evidence is the required foundation. Narrative XHTML is a\n    # bounded enrichment layer: very large annual reports must not discard valid\n    # structured evidence or force an unbounded download.\n    json_bytes = fetcher(filing.json_url, max_bytes=json_limit, timeout=timeout)\n    xbrl_payload = parse_xbrl_json(json_bytes)\n    inventory = inventory_xbrl_activity(xbrl_payload)\n\n    narrative: list[NarrativeEvidence] = []\n    narrative_status: dict[str, Any]\n    if not filing.xhtml_url:\n        narrative_status = {\n            "state": "unavailable",\n            "reason": "selected ESEF filing does not provide XHTML",\n            "download_limit_bytes": xhtml_limit,\n        }\n    else:\n        try:\n            xhtml_bytes = fetcher(filing.xhtml_url, max_bytes=xhtml_limit, timeout=timeout)\n            narrative = extract_narrative_evidence(xhtml_bytes)\n            narrative_status = {\n                "state": "available",\n                "reason": None,\n                "download_limit_bytes": xhtml_limit,\n            }\n        except EvidenceTooLarge as exc:\n            narrative_status = {\n                "state": "skipped_oversize",\n                "reason": str(exc),\n                "download_limit_bytes": xhtml_limit,\n            }\n'''

OLD_POLICY = '''            "reported_facts_are_not_analytical_mappings": True,\n'''
NEW_POLICY = '''            "reported_facts_are_not_analytical_mappings": True,\n            "narrative_enrichment_is_bounded_and_optional": True,\n'''

OLD_NARRATIVE = '''        "narrative_evidence": [row.to_dict() for row in narrative],\n'''
NEW_NARRATIVE = '''        "narrative_evidence": [row.to_dict() for row in narrative],\n        "narrative_status": narrative_status,\n'''

OLD_SUMMARY = '''    print(f"Narrative evidence windows: {len(payload['narrative_evidence'])}")\n'''
NEW_SUMMARY = '''    print(f"Narrative evidence windows: {len(payload['narrative_evidence'])}")\n    print(f"Narrative status: {payload.get('narrative_status', {}).get('state', 'unknown')}")\n'''

OLD_HELP = '''    parser.add_argument("--latest", action="store_true", help="Required semantic marker; v0.4.0 analyzes latest ESEF only")\n'''
NEW_HELP = '''    parser.add_argument("--latest", action="store_true", help="Required semantic marker; v0.4.2 analyzes latest ESEF only")\n'''

OLD_ERROR = '''        parser.error("v0.4.0 requires --latest; historical activity packs come later")\n'''
NEW_ERROR = '''        parser.error("v0.4.2 requires --latest; historical activity packs come later")\n'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"ERROR: expected {label} exactly once; found {text.count(old)}")
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_esef_activity_v0_4_2.py PATH")
    path = Path(sys.argv[1])
    text = path.read_text()

    if "class EvidenceTooLarge" in text or '"narrative_status": narrative_status' in text:
        raise SystemExit("ERROR: esef_activity.py already contains the v0.4.2 bounded narrative fallback")

    text = replace_once(text, CLASS_ANCHOR, CLASS_INSERT, "_fetch_bounded anchor")
    text = replace_once(text, OLD_CONTENT_LENGTH, NEW_CONTENT_LENGTH, "Content-Length limit raise")
    text = replace_once(text, OLD_STREAM_LIMIT, NEW_STREAM_LIMIT, "streaming limit raise")
    text = replace_once(text, OLD_BUILD, NEW_BUILD, "v0.4.1 activity-build block")
    text = replace_once(text, OLD_POLICY, NEW_POLICY, "policy field")
    text = replace_once(text, OLD_NARRATIVE, NEW_NARRATIVE, "narrative manifest field")
    text = replace_once(text, OLD_SUMMARY, NEW_SUMMARY, "summary narrative line")
    text = replace_once(text, OLD_HELP, NEW_HELP, "CLI latest help")
    text = replace_once(text, OLD_ERROR, NEW_ERROR, "CLI latest error")

    path.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
