"""Launches mitmproxy programmatically with our addon loaded."""

from pathlib import Path

from mitmproxy.tools.main import mitmdump


def run(listen_port: int = 8888) -> None:
    """Start mitmproxy in dump mode (no interactive UI) with Ephemera's addon."""
    addon_path = Path(__file__).parent / "addon.py"
    mitmdump([
        "--listen-port", str(listen_port),
        "-s", str(addon_path),
        "--set", "flow_detail=0",
    ])
