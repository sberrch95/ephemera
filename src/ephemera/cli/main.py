"""Ephemera CLI entry point."""
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import typer
from sqlmodel import select
from ephemera.database.models import Endpoint, Target, TimelineEvent, Variable
from ephemera.database.session import get_session, init_db
from ephemera.proxy.runner import run as run_proxy

app = typer.Typer(
    name="ephemera",
    help="A security context engine: shared memory between pentesting tools.",
    no_args_is_help=True,
)

PID_DIR = Path.home() / ".ephemera"
PID_FILE = PID_DIR / "ephemera.pid"
LOG_FILE = PID_DIR / "ephemera-daemon.log"


def _read_pid() -> int | None:
    if not PID_FILE.is_file():
        return None
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, SystemError):
        return False
    except Exception:
        # Windows may raise different errors; fall through to a softer check.
        pass
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return False
    return False


def _write_pid(pid: int) -> None:
    PID_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid), encoding="utf-8")


def _clear_pid() -> None:
    try:
        PID_FILE.unlink(missing_ok=True)
    except OSError:
        pass


@app.command()
def version():
    """Print the current Ephemera version."""
    typer.echo("Ephemera v0.1.0 (foundation build)")


@app.command()
def start(
    port: int = 8888,
    daemon: bool = typer.Option(
        False, "--daemon", "-d",
        help="Background the proxy so you can run state/history/export in the same terminal.",
    ),
):
    """Start the Ephemera interception proxy."""
    init_db()

    existing = _read_pid()
    if existing and _pid_alive(existing):
        typer.echo(f"Ephemera is already running (pid {existing}). Use 'ephemera stop' first.")
        raise typer.Exit(code=1)

    if daemon:
        PID_DIR.mkdir(parents=True, exist_ok=True)
        log_fh = open(LOG_FILE, "a", encoding="utf-8")
        # Re-invoke without --daemon so the child runs the proxy in the foreground
        # of its own process group / detached session.
        cmd = [sys.executable, "-m", "ephemera.cli.main", "start", "--port", str(port)]
        kwargs: dict = {
            "stdin": subprocess.DEVNULL,
            "stdout": log_fh,
            "stderr": subprocess.STDOUT,
            "close_fds": True,
        }
        if sys.platform == "win32":
            # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            kwargs["creationflags"] = 0x00000008 | 0x00000200
        else:
            kwargs["start_new_session"] = True

        proc = subprocess.Popen(cmd, **kwargs)
        _write_pid(proc.pid)
        typer.echo(f"Ephemera proxy daemon started on port {port} (pid {proc.pid}).")
        typer.echo(f"Configure your tools to use proxy: http://localhost:{port}")
        typer.echo(f"Logs: {LOG_FILE}")
        typer.echo("Stop with: ephemera stop")
        return

    # Foreground: record pid so `ephemera stop` can find us too.
    _write_pid(os.getpid())
    try:
        typer.echo(f"Starting Ephemera proxy on port {port}...")
        typer.echo(f"Configure your tools to use proxy: http://localhost:{port}")
        typer.echo("Trust the CA cert at: ~/.mitmproxy/mitmproxy-ca-cert.pem")
        run_proxy(listen_port=port)
    finally:
        _clear_pid()


@app.command()
def stop():
    """Stop a running Ephemera proxy daemon (or foreground process with a PID file)."""
    pid = _read_pid()
    if pid is None:
        typer.echo("No Ephemera PID file found — is the proxy running?")
        raise typer.Exit(code=1)
    if not _pid_alive(pid):
        _clear_pid()
        typer.echo(f"Stale PID file for {pid} removed (process not running).")
        raise typer.Exit()

    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F", "/T"],
                check=False,
                capture_output=True,
            )
        else:
            os.kill(pid, signal.SIGTERM)
    except Exception as e:
        typer.echo(f"Failed to stop pid {pid}: {e}")
        raise typer.Exit(code=1)

    _clear_pid()
    typer.echo(f"Stopped Ephemera proxy (pid {pid}).")


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

@app.command()
def export(
    target: str = typer.Argument(..., help="Hostname to export (e.g. localhost:3000)"),
    format: str = typer.Option("json", help="Output format: json or markdown"),
):
    """Export everything known about a target."""
    with get_session() as session:
        target_row = session.exec(select(Target).where(Target.hostname == target)).first()
        if not target_row:
            typer.echo(f"No data found for target '{target}'.")
            raise typer.Exit(code=1)

        endpoints = session.exec(
            select(Endpoint).where(Endpoint.target_id == target_row.id)
        ).all()
        variables = session.exec(
            select(Variable).where(Variable.target_id == target_row.id)
        ).all()
        events = session.exec(
            select(TimelineEvent)
            .where(TimelineEvent.target_id == target_row.id)
            .order_by(TimelineEvent.timestamp)
        ).all()

        if format == "json":
            data = {
                "target": target_row.hostname,
                "first_seen": target_row.first_seen.isoformat(),
                "last_seen": target_row.last_seen.isoformat(),
                "endpoints": [
                    {"method": e.method, "path": e.path, "times_seen": e.times_seen}
                    for e in endpoints
                ],
                "variables": [
                    {
                        "type": v.variable_type,
                        "key": v.key,
                        "value": v.value,
                        "source_url": v.source_url,
                        "extracted_at": v.extracted_at.isoformat(),
                    }
                    for v in variables
                ],
                "timeline": [
                    {
                        "timestamp": ev.timestamp.isoformat(),
                        "event_type": ev.event_type,
                        "description": ev.description,
                    }
                    for ev in events
                ],
            }
            typer.echo(json.dumps(data, indent=2))

        elif format == "markdown":
            typer.echo(f"# Ephemera Export: {target_row.hostname}\n")
            typer.echo(f"First seen: {target_row.first_seen}  ")
            typer.echo(f"Last seen: {target_row.last_seen}\n")

            typer.echo(f"## Endpoints ({len(endpoints)})\n")
            for e in endpoints:
                typer.echo(f"- `{e.method} {e.path}` — seen {e.times_seen}x")

            typer.echo(f"\n## Extracted Variables ({len(variables)})\n")
            for v in variables:
                typer.echo(f"- **{v.key}** (`{v.variable_type}`): `{v.value[:50]}...`")
                typer.echo(f"  - source: {v.source_url}")

            typer.echo(f"\n## Timeline ({len(events)})\n")
            for ev in events:
                ts = ev.timestamp.strftime("%H:%M:%S")
                typer.echo(f"- `{ts}` **[{ev.event_type}]** {ev.description}")

        else:
            typer.echo(f"Unknown format '{format}'. Use 'json' or 'markdown'.")
            raise typer.Exit(code=1)
if __name__ == "__main__":
    app()
