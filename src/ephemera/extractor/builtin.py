"""Built-in extractors for Ephemera.

Deliberately allowlist-based, not heuristic: we only extract keys we
explicitly recognize as security-relevant. This keeps behavior fully
predictable and avoids false positives from guessing at what "looks
like" a token.
"""

import json
from http.cookies import SimpleCookie
from collections.abc import Mapping

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


def extract_from_response_headers(headers) -> list[Candidate]:
    """Extract cookies from ``Set-Cookie`` response headers.

    Header names are matched case-insensitively, and each header value is
    parsed independently so one malformed cookie cannot hide valid cookies
    in other response headers.
    """
    values = _set_cookie_values(headers)
    candidates: list[Candidate] = []
    for raw_value in values:
        cookie = SimpleCookie()
        try:
            cookie.load(str(raw_value))
        except (TypeError, ValueError):
            continue
        for key, morsel in cookie.items():
            candidates.append(Candidate(key=key, value=morsel.value, variable_type="cookie"))
    return candidates


def _set_cookie_values(headers) -> list[str]:
    """Return Set-Cookie values from mapping- or mitmproxy-like headers."""
    if headers is None:
        return []
    if hasattr(headers, "get_all"):
        return [str(value) for value in headers.get_all("set-cookie")]
    if isinstance(headers, Mapping):
        values = []
        for key, value in headers.items():
            if str(key).lower() != "set-cookie":
                continue
            values.extend(value if isinstance(value, (list, tuple)) else [value])
        return [str(value) for value in values]
    return []


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
