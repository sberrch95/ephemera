"""Built-in extractors for Ephemera.

Deliberately allowlist-based, not heuristic: we only extract keys we
explicitly recognize as security-relevant. This keeps behavior fully
predictable and avoids false positives from guessing at what "looks
like" a token.
"""

import json

from ephemera.extractor.base import Candidate

# Explicit allowlist. Add to this list deliberately - each addition is a
# judgment call about what's worth remembering, not a heuristic guess.
JSON_KEY_ALLOWLIST = {
    "token",
    "access_token",
    "accessToken",
    "jwt",
    "session_id",
    "sessionId",
    "refresh_token",
    "refreshToken",
    "api_key",
    "apiKey",
}


def extract_from_json_body(body_bytes: bytes) -> list[Candidate]:
    """Recursively scan a JSON response body for allowlisted keys."""
    try:
        data = json.loads(body_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []

    candidates: list[Candidate] = []
    _scan(data, candidates)
    return candidates


def _scan(node, candidates: list[Candidate]) -> None:
    """Walk a parsed JSON structure (dict/list/scalar) looking for
    allowlisted keys at any nesting depth."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in JSON_KEY_ALLOWLIST and isinstance(value, str):
                candidates.append(Candidate(key=key, value=value, variable_type="json_body_key"))
            else:
                _scan(value, candidates)
    elif isinstance(node, list):
        for item in node:
            _scan(item, candidates)
