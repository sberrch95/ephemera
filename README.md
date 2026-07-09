# Ephemera

A security context engine: shared memory between pentesting tools.

Modern security tools work in isolation — Burp, ffuf, and custom scripts
each discover things (endpoints, tokens, session state) without sharing
that knowledge with each other. Ephemera sits between your tools and a
target as an HTTP(S) proxy, automatically remembering what's discovered
so it doesn't get lost between tools or lost when you close a terminal.

**Status: working foundation (v0.1.0).** Core pipeline is functional and
tested. Not yet a v1.0 - see [Roadmap](#roadmap) below.

Ephemera does **not** automate exploitation and does **not** attack
targets. It's a memory layer for traffic you're already generating with
your own tools, against targets you're authorized to test.

## What it does today

- **Intercepts HTTP(S) traffic** via a local proxy (built on
  [mitmproxy](https://mitmproxy.org)) - point your tools at it like any
  other proxy
- **Remembers targets and endpoints** automatically, deduplicated, with
  a timeline of what was discovered and when
- **Extracts security-relevant values** (tokens, session IDs) from JSON
  response bodies using an explicit, auditable key allowlist - no
  heuristic guessing
- **Exports** everything captured for a target as JSON or Markdown

## Quickstart

```bash
git clone https://github.com/sberrch95/ephemera.git
cd ephemera
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

ephemera start
```

In another terminal, point a tool at the proxy:

```bash
curl -x http://localhost:8888 --cacert ~/.mitmproxy/mitmproxy-ca-cert.pem https://example.com
```

(The `--cacert` flag is required for HTTPS traffic - mitmproxy generates
its own CA certificate on first run, and your client needs to trust it
to allow interception. This is the same trust model tools like Burp use.)

Then check what Ephemera learned:

```bash
ephemera state
ephemera history
ephemera export <hostname>
```

## Development

```bash
pytest -v                    # run tests (29 passing, ~95% coverage on core logic)
ruff check src/ tests/       # lint
```

## Roadmap

- [ ] Cookie and JWT-claim extractors (beyond today's JSON-body-key extractor)
- [ ] Variable injection (`{{TOKEN}}` templating in outgoing requests)
- [ ] `ephemera --daemon` mode (currently runs in the foreground)
- [ ] Multi-target export / reporting

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
