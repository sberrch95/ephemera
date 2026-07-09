"""Cookie extractor: scan Set-Cookie response headers via an explicit allowlist.

Same philosophy as the JSON body extractor — only capture cookie names we
explicitly recognize as security-relevant. No heuristic guessing.
"""

from http.cookies import SimpleCookie

from ephemera.extractor.base import Candidate

# Explicit allowlist of cookie names worth remembering.
COOKIE_NAME_ALLOWLIST = {
    "session",
    "sessionid",
    "session_id",
    "sid",
    "token",
    "access_token",
    "refresh_token",
    "jwt",
    "auth",
    "auth_token",
    "api_key",
    "csrftoken",
    "csrf_token",
    "xsrf-token",
}


def extract_from_set_cookie(headers) -> list[Candidate]:
    """Extract allowlisted cookies from Set-Cookie header value(s).

    ``headers`` may be:
    - a mapping with a ``Set-Cookie`` / ``set-cookie`` key (str or list of str)
    - a list/tuple of raw Set-Cookie header strings
    - a single Set-Cookie header string
    """
    raw_values = _collect_set_cookie_values(headers)
    if not raw_values:
        return []

    candidates: list[Candidate] = []
    seen: set[tuple[str, str]] = set()
    for raw in raw_values:
        cookie = SimpleCookie()
        try:
            cookie.load(raw)
        except Exception:
            continue
        for name, morsel in cookie.items():
            if name not in COOKIE_NAME_ALLOWLIST:
                continue
            value = morsel.value
            if not value or not isinstance(value, str):
                continue
            key = (name, value)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                Candidate(key=name, value=value, variable_type="cookie")
            )
    return candidates


def _collect_set_cookie_values(headers) -> list[str]:
    if headers is None:
        return []
    if isinstance(headers, str):
        return [headers] if headers.strip() else []
    if isinstance(headers, (list, tuple)):
        out: list[str] = []
        for item in headers:
            if isinstance(item, str) and item.strip():
                out.append(item)
        return out
    # Mapping-like (dict, CaseInsensitiveDict, mitmproxy headers, ...)
    try:
        keys = list(headers.keys())
    except Exception:
        return []
    values: list[str] = []
    for key in keys:
        if str(key).lower() != "set-cookie":
            continue
        val = headers[key]
        if isinstance(val, (list, tuple)):
            values.extend(str(v) for v in val if v)
        elif val:
            values.append(str(val))
    # mitmproxy MultiDict-style: get_all
    get_all = getattr(headers, "get_all", None)
    if callable(get_all) and not values:
        try:
            values.extend(str(v) for v in get_all("Set-Cookie") if v)
        except Exception:
            pass
    return values
