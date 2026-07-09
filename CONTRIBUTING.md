# Contributing to Ephemera

Thanks for considering contributing. This project is early (v0.1.0
foundation), so there's real room to shape it.

## Getting Set Up

```bash
git clone https://github.com/sberrch95/ephemera.git
cd ephemera
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Confirm your setup works before making changes:

```bash
pytest -v
ruff check src/ tests/
```

Both should pass cleanly on a fresh clone. If they don't, that's a bug
in the setup instructions - please open an issue.

## Project Structure
```src/ephemera/
├── proxy/       # mitmproxy addon - traffic interception, no business logic
├── core/        # memory.py - the scoping/deduplication/storage logic
├── database/    # SQLModel table definitions and session management
├── extractor/   # pluggable extractors (currently: JSON body key allowlist)
└── cli/         # Typer commands - thin layer over core/ and database/
```
**Key design principle:** functions in `core/` and `database/` accept a
`session` parameter rather than opening their own database connection
internally. This was a deliberate fix (see commit history) - it's what
makes these modules unit-testable in isolation against an in-memory
database. New code should follow the same pattern.

## Making Changes

1. Open an issue first for anything beyond a small fix, so we can agree
   on direction before you invest time in an implementation.
2. Write tests for new logic - especially anything touching `core/` or
   `extractor/`. PRs without test coverage for new behavior will likely
   get a request to add some before merge.
3. Run `pytest -v` and `ruff check src/ tests/` locally before opening
   a PR - CI runs both automatically, but catching issues locally first
   saves a round trip.
4. Keep commit messages descriptive - explain *why*, not just *what*,
   especially for anything non-obvious. Look at the existing commit
   history for the style this project uses.

## Extending the Extractor

The extraction engine is deliberately allowlist-based, not heuristic
(see `extractor/builtin.py`). If you're adding a new extractor:

- Prefer explicit matching (known key names, known header names) over
  pattern-guessing what "looks like" a token - this keeps false-positive
  risk low and behavior auditable.
- Give it its own `variable_type` value so it's distinguishable from
  other extractors in `ephemera state`/`export` output.
- Add both a scan for the case you're targeting and at least one test
  confirming it does *not* match things it shouldn't.

## Good First Issues

Look for issues labeled `good first issue` on the
[issues page](https://github.com/sberrch95/ephemera/issues). If none
are currently labeled, feel free to open an issue proposing something
from the [Roadmap](README.md#roadmap) and we can scope it together.

## Code of Conduct

Be respectful, assume good faith, and keep discussion focused on the
technical merits of changes. This is a security tool - if you find a
genuine security issue in Ephemera itself (not in a target you're
testing), please open an issue marked clearly as a security concern
rather than a general bug report.
