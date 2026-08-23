from __future__ import annotations

from pathlib import Path
import sys

START = "def _sparql_request(endpoint: str, query: str, *, timeout: float = 45.0) -> bytes:\n"
END = "\ndef _parse_sparql_json(data: bytes) -> list[dict[str, Any]]:\n"

NEW_BLOCK = '''def _sparql_request(endpoint: str, query: str, *, timeout: float = 45.0) -> bytes:\n    _validate_https_endpoint(endpoint)\n    payload_text = urlencode({"query": query})\n    common_headers = {\n        "Accept": "application/sparql-results+json",\n        "User-Agent": "zse-value-scanner/0.4.9 classification-backbone",\n    }\n    get_request = Request(\n        f"{endpoint}?{payload_text}",\n        method="GET",\n        headers=common_headers,\n    )\n    post_request = Request(\n        endpoint,\n        data=payload_text.encode("utf-8"),\n        method="POST",\n        headers={\n            **common_headers,\n            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",\n        },\n    )\n\n    failures: list[str] = []\n    for transport, request in (("GET", get_request), ("POST", post_request)):\n        last_error: Exception | None = None\n        for attempt in range(3):\n            try:\n                with urlopen(request, timeout=timeout) as response:  # nosec B310 - endpoint is validated above\n                    status = getattr(response, "status", 200)\n                    if status != 200:\n                        raise ClassificationError(f"SPARQL endpoint returned HTTP {status}")\n                    return _read_bounded(response)\n            except Exception as exc:  # network boundary; re-raised with context\n                last_error = exc\n                if attempt < 2:\n                    time.sleep(0.5 * (attempt + 1))\n        failures.append(f"{transport}: {last_error}")\n\n    raise ClassificationError("SPARQL request failed via GET and POST after retries: " + " | ".join(failures))\n\n'''


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_classification_transport_hotfix.py <classification_backbone.py>")
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit("ERROR: expected classification transport function boundaries not found")
    before, rest = text.split(START, 1)
    old_body, after = rest.split(END, 1)
    old_block = START + old_body
    if 'method="POST"' not in old_block or 'zse-value-scanner/0.4.8 classification-backbone' not in old_block:
        raise SystemExit("ERROR: target is not the expected v0.4.8 POST-only transport")
    path.write_text(before + NEW_BLOCK + END + after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
