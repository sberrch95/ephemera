"""Ephemera's core mitmproxy addon.

This is the interception layer: mitmproxy calls request() and response()
on this class at the right points in the HTTP(S) lifecycle. For Phase 1,
we only observe and log — no storage, no extraction, no modification.
That comes in Phase 2+.
"""

from mitmproxy import http


class EphemeraAddon:
    """mitmproxy addon: logs every request/response passing through."""

    def request(self, flow: http.HTTPFlow) -> None:
        """Called when a request arrives, before it's forwarded to the target."""
        print(f"[REQUEST]  {flow.request.method} {flow.request.pretty_url}")

    def response(self, flow: http.HTTPFlow) -> None:
        """Called when the response arrives, before it's returned to the client."""
        status = flow.response.status_code
        length = len(flow.response.content) if flow.response.content else 0
        print(f"[RESPONSE] {status} {flow.request.pretty_url} ({length} bytes)")


addons = [EphemeraAddon()]
