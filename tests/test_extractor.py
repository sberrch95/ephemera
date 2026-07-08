"""Tests for extractor/builtin.py - the allowlist-based JSON extraction."""

from ephemera.extractor.builtin import extract_from_json_body


def test_extracts_top_level_allowlisted_key():
    body = b'{"token": "abc123"}'
    results = extract_from_json_body(body)

    assert len(results) == 1
    assert results[0].key == "token"
    assert results[0].value == "abc123"
    assert results[0].variable_type == "json_body_key"


def test_extracts_nested_allowlisted_key():
    # matches the real Juice Shop response shape from today's session
    body = b'{"authentication": {"token": "eyJabc"}, "bid": 1}'
    results = extract_from_json_body(body)

    assert len(results) == 1
    assert results[0].key == "token"
    assert results[0].value == "eyJabc"


def test_ignores_non_allowlisted_keys():
    body = b'{"username": "admin", "bid": 1, "umail": "a@b.com"}'
    results = extract_from_json_body(body)
    assert results == []


def test_ignores_non_string_values_even_if_key_matches():
    # token key present, but value is an object, not a string - should skip
    body = b'{"token": {"nested": "object"}}'
    results = extract_from_json_body(body)
    assert results == []


def test_finds_multiple_allowlisted_keys_in_one_response():
    body = b'{"access_token": "aaa", "refresh_token": "bbb"}'
    results = extract_from_json_body(body)

    keys_found = {r.key for r in results}
    assert keys_found == {"access_token", "refresh_token"}


def test_scans_inside_lists():
    body = b'{"sessions": [{"token": "aaa"}, {"token": "bbb"}]}'
    results = extract_from_json_body(body)

    values_found = {r.value for r in results}
    assert values_found == {"aaa", "bbb"}


def test_handles_invalid_json_gracefully():
    body = b"<html>not json at all</html>"
    results = extract_from_json_body(body)
    assert results == []


def test_handles_empty_body():
    results = extract_from_json_body(b"")
    assert results == []
