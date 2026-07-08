# Ephemera

A security context engine: shared memory between pentesting tools.

**Status: early foundation (v0.1.0-dev).** Not yet functional. Currently
just a CLI skeleton — proxy and memory layer are being built next.

## What this will be

Ephemera sits between security tools (Burp, ffuf, custom scripts) and a
target, capturing tokens, cookies, and discovered endpoints so tools don't
have to manually share state with each other.

It does not automate exploitation. It is a memory layer, not an attack tool.

## Development setup

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
ephemera --help
```

## License

MIT
