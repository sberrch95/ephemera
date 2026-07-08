"""Ephemera's core mitmproxy addon.

Intercepts HTTP(S) traffic and, on each completed response, hands it to
the memory layer (core/memory.py) for storage. The addon itself stays
"dumb" - it doesn't know about SQL or scoping rules, it just reports
what it saw.
"""

from mitmproxy import http

from ephemera.core.memory import record_request


class EphemeraAddon:
    """mitmproxy addon: logs and stores every request/response passing through."""

    def request(self, flow: http.HTTPFlow) -> None:
        """Called when a request arrives, before it's forwarded to the target."""
        print(f"[REQUEST]  {flow.request.method} {flow.request.pretty_url}")

    def response(self, flow: http.HTTPFlow) -> None:
        """Called when the response arrives, before it's returned to the client."""
        status = flow.response.status_code
        length = len(flow.response.content) if flow.response.content else 0
        print(f"[RESPONSE] {status} {flow.request.pretty_url} ({length} bytes)")

        record_request(
            url=flow.request.pretty_url,
            method=flow.request.method,
            status_code=status,
            response_bytes=length,
        )


addons = [EphemeraAddon()]
