"""Decode JWT payloads into individual claim variables (no signature verify).

When a captured value looks like a JWT, decode the middle segment (payload)
as base64url JSON and emit notable claims as separate Candidate rows with
``variable_type="jwt_claim"``.
"""

from __future__ import annotations

import base64
import json
import re

from ephemera.extractor.base import Candidate

# Claims worth extracting when present. Explicit allowlist, not a heuristic.
JWT_CLAIM_ALLOWLIST = {
    "sub",
    "iss",
    "aud",
    "exp",
    "iat",
    "nbf",
    "jti",
    "role",
    "roles",
    "scope",
    "scopes",
    "email",
    "name",
    "preferred_username",
    "uid",
    "user_id",
    "permissions",
}

_JWT_RE = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*$")


def looks_like_jwt(value: str) -> bool:
    if not value or not isinstance(value, str):
        return False
    # Bearer prefix is common in Authorization headers / JSON bodies.
    if value.lower().startswith("bearer "):
        value = value[7:].strip()
    return bool(_JWT_RE.match(value)) and value.count(".") == 2


def decode_jwt_payload(token: str) -> dict | None:
    """Return the JWT payload as a dict, or None if it cannot be decoded."""
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not looks_like_jwt(token):
        return None
    try:
        payload_b64 = token.split(".")[1]
        # base64url padding
        pad = "=" * (-len(payload_b64) % 4)
        raw = base64.urlsafe_b64decode(payload_b64 + pad)
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def extract_jwt_claims(token: str, *, parent_key: str = "jwt") -> list[Candidate]:
    """Decode *token* and emit allowlisted claims as ``jwt_claim`` candidates.

    ``parent_key`` is used only for the Candidate.key prefix so claims stay
    distinguishable (e.g. ``token.role``, ``token.exp``).
    """
    payload = decode_jwt_payload(token)
    if not payload:
        return []

    candidates: list[Candidate] = []
    for claim, value in payload.items():
        if claim not in JWT_CLAIM_ALLOWLIST:
            continue
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        else:
            rendered = str(value)
        candidates.append(
            Candidate(
                key=f"{parent_key}.{claim}",
                value=rendered,
                variable_type="jwt_claim",
            )
        )
    return candidates
