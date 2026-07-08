"""Ephemera CLI entry point.

This is intentionally minimal for Phase 0 — just enough to prove the
packaging works end-to-end. Real commands (start, state, history, export)
get added in later phases once the proxy and database exist.
"""

import typer

app = typer.Typer(
    name="ephemera",
    help="A security context engine: shared memory between pentesting tools.",
    no_args_is_help=True,
)


@app.command()
def version():
    """Print the current Ephemera version."""
    typer.echo("Ephemera v0.1.0 (foundation build)")

@app.command()
def status():
    """Show Ephemera's current status (placeholder — real logic comes in Phase 1/2)."""
    typer.echo("Ephemera is not yet running. Proxy and database not implemented.")

if __name__ == "__main__":
    app()
