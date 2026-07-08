"""Tests for cli/main.py - state, history, and export commands.

Uses the cli_db fixture (in-memory database wired via override_engine())
so these tests never touch ~/.ephemera/ephemera.db. We seed data by
calling record_request()/record_extracted_variables() directly against
a session on the same in-memory engine, then invoke the CLI commands
via Typer's CliRunner and check what they printed.
"""

import json

from sqlmodel import Session
from typer.testing import CliRunner

from ephemera.cli.main import app
from ephemera.core.memory import record_extracted_variables, record_request

runner = CliRunner()


def seed_basic_traffic(engine):
    """Helper: writes one request + one extracted variable, using the
    same engine the CLI test is wired to via cli_db."""
    with Session(engine) as session:
        record_request(
            session, url="http://example.com/login", method="POST",
            status_code=200, response_bytes=100,
        )
        record_extracted_variables(
            session, url="http://example.com/login",
            response_body=b'{"token": "abc123"}',
        )


def test_state_shows_no_targets_message_when_empty(cli_db):
    result = runner.invoke(app, ["state"])
    assert result.exit_code == 0
    assert "No targets recorded yet" in result.stdout


def test_state_shows_target_and_endpoint(cli_db):
    seed_basic_traffic(cli_db)

    result = runner.invoke(app, ["state"])
    assert result.exit_code == 0
    assert "example.com" in result.stdout
    assert "/login" in result.stdout
    assert "seen 1x" in result.stdout


def test_history_shows_no_events_message_when_empty(cli_db):
    result = runner.invoke(app, ["history"])
    assert result.exit_code == 0
    assert "No events recorded yet" in result.stdout


def test_history_shows_events_in_order(cli_db):
    seed_basic_traffic(cli_db)

    result = runner.invoke(app, ["history"])
    assert result.exit_code == 0

    # TARGET_SEEN should appear before VARIABLE_EXTRACTED in the output
    target_seen_pos = result.stdout.find("TARGET_SEEN")
    var_extracted_pos = result.stdout.find("VARIABLE_EXTRACTED")
    assert target_seen_pos != -1
    assert var_extracted_pos != -1
    assert target_seen_pos < var_extracted_pos


def test_history_filters_by_target(cli_db):
    seed_basic_traffic(cli_db)

    result = runner.invoke(app, ["history", "--target", "nonexistent.com"])
    assert result.exit_code == 0
    assert "No target found matching" in result.stdout


def test_export_json_contains_expected_fields(cli_db):
    seed_basic_traffic(cli_db)

    result = runner.invoke(app, ["export", "example.com"])
    assert result.exit_code == 0

    data = json.loads(result.stdout)
    assert data["target"] == "example.com"
    assert len(data["endpoints"]) == 1
    assert data["endpoints"][0]["path"] == "/login"
    assert len(data["variables"]) == 1
    assert data["variables"][0]["key"] == "token"
    assert data["variables"][0]["value"] == "abc123"


def test_export_markdown_format(cli_db):
    seed_basic_traffic(cli_db)

    result = runner.invoke(app, ["export", "example.com", "--format", "markdown"])
    assert result.exit_code == 0
    assert "# Ephemera Export: example.com" in result.stdout
    assert "token" in result.stdout


def test_export_unknown_target_fails_cleanly(cli_db):
    result = runner.invoke(app, ["export", "nowhere.com"])
    assert result.exit_code == 1
    assert "No data found for target" in result.stdout


def test_history_no_target_matching_message(cli_db):
    result = runner.invoke(app, ["history", "--target", "totally-unknown-host.com"])
    assert result.exit_code == 0
    assert "No target found matching" in result.stdout


def test_export_unknown_format_fails_cleanly(cli_db):
    seed_basic_traffic(cli_db)
    result = runner.invoke(app, ["export", "example.com", "--format", "yaml"])
    assert result.exit_code == 1
    assert "Unknown format" in result.stdout
