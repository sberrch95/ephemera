"""Ephemera CLI entry point."""

import typer
from sqlmodel import select

from ephemera.database.models import Endpoint, Target, TimelineEvent
from ephemera.database.session import get_session, init_db
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
    init_db()
    typer.echo(f"Starting Ephemera proxy on port {port}...")
    typer.echo(f"Configure your tools to use proxy: http://localhost:{port}")
    typer.echo(f"Trust the CA cert at: ~/.mitmproxy/mitmproxy-ca-cert.pem")
    run_proxy(listen_port=port)


@app.command()
def state():
    """Show all known targets and their discovered endpoints."""
    with get_session() as session:
        targets = session.exec(select(Target)).all()

        if not targets:
            typer.echo("No targets recorded yet. Run 'ephemera start' and generate some traffic.")
            raise typer.Exit()

        for target in targets:
            typer.echo(f"\nTarget: {target.hostname}")
            typer.echo(f"  First seen: {target.first_seen}")
            typer.echo(f"  Last seen:  {target.last_seen}")

            endpoints = session.exec(
                select(Endpoint).where(Endpoint.target_id == target.id)
            ).all()
            typer.echo(f"  Endpoints ({len(endpoints)}):")
            for ep in endpoints:
                typer.echo(f"    {ep.method:6} {ep.path}  (seen {ep.times_seen}x)")


@app.command()
def history(target: str = typer.Option(None, help="Filter by hostname")):
    """Show the timeline of recorded events."""
    with get_session() as session:
        query = select(TimelineEvent).order_by(TimelineEvent.timestamp)

        if target:
            target_row = session.exec(select(Target).where(Target.hostname == target)).first()
            if not target_row:
                typer.echo(f"No target found matching '{target}'.")
                raise typer.Exit()
            query = query.where(TimelineEvent.target_id == target_row.id)

        events = session.exec(query).all()

        if not events:
            typer.echo("No events recorded yet.")
            raise typer.Exit()

        for event in events:
            ts = event.timestamp.strftime("%H:%M:%S")
            typer.echo(f"{ts}  [{event.event_type}]  {event.description}")


if __name__ == "__main__":
    app()
