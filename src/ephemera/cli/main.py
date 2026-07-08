"""Ephemera CLI entry point."""

import typer

from ephemera.proxy.runner import run as run_proxy

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
def start(port: int = 8888):
    """Start the Ephemera interception proxy."""
    typer.echo(f"Starting Ephemera proxy on port {port}...")
    typer.echo(f"Configure your tools to use proxy: http://localhost:{port}")
    typer.echo(f"Trust the CA cert at: ~/.mitmproxy/mitmproxy-ca-cert.pem")
    run_proxy(listen_port=port)


if __name__ == "__main__":
    app()
