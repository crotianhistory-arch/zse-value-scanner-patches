from __future__ import annotations

import sys
from pathlib import Path

INSERT_ANCHOR = """def parse_zse_issuer_html(html: str, *, isin: str, source_url: str) -> ZSEIssuerIdentity:\n"""

INSERT_TEXT = '''_ZSE_NAVIGATION_TOKENS = {
    "announcements",
    "objave",
    "trading",
    "trgovanje",
    "instrument",
    "issuer",
    "izdavatelj",
    "historical data",
    "povijesni podaci",
}


def _issuer_name_from_tokens(tokens: list[str]) -> str | None:
    """Return the issuer legal name from the ZSE issuer-detail block.

    Current ZSE pages place the issuer legal name immediately before the
    Home Member State field. This avoids confusing the navigation-tab label
    "Issuer" with the issuer-detail content.
    """
    member_labels = {"home member state", "matična država članica"}
    for idx, token in enumerate(tokens):
        if token.casefold() in member_labels:
            for candidate in reversed(tokens[max(0, idx - 4) : idx]):
                folded = candidate.casefold()
                if candidate and folded not in member_labels and folded not in _ZSE_NAVIGATION_TOKENS:
                    return candidate

    # Compatibility fallback for older/simple ZSE layouts where an explicit
    # Issuer/Izdavatelj field directly precedes the legal name.
    fallback = _next_token(tokens, {"Issuer", "Izdavatelj"})
    if fallback and fallback.casefold() not in _ZSE_NAVIGATION_TOKENS:
        return fallback
    return None


def parse_zse_issuer_html(html: str, *, isin: str, source_url: str) -> ZSEIssuerIdentity:
'''

OLD_BLOCK = '''    issuer_name = _next_token(tokens, {"Issuer", "Izdavatelj"})
    if not issuer_name:
        raise ValueError("official ZSE issuer page did not expose a parseable issuer name")
'''

NEW_BLOCK = '''    issuer_name = _issuer_name_from_tokens(tokens)
    if not issuer_name:
        raise ValueError("official ZSE issuer page did not expose a parseable issuer name")
'''


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_zse_identity_v0_3_9.py PATH")
    path = Path(sys.argv[1])
    text = path.read_text()

    if "_issuer_name_from_tokens" in text:
        raise SystemExit("ERROR: zse_identity.py already contains the v0.3.9 issuer parser")

    if INSERT_ANCHOR not in text:
        raise SystemExit("ERROR: expected parse_zse_issuer_html anchor not found")
    if text.count(INSERT_ANCHOR) != 1:
        raise SystemExit("ERROR: parse_zse_issuer_html anchor is not unique")
    if OLD_BLOCK not in text or text.count(OLD_BLOCK) != 1:
        raise SystemExit("ERROR: expected v0.3.8 issuer-name parser block not found exactly once")

    text = text.replace(INSERT_ANCHOR, INSERT_TEXT, 1)
    text = text.replace(OLD_BLOCK, NEW_BLOCK, 1)
    path.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
