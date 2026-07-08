"""Ephemera's core mitmproxy addon.

Intercepts HTTP(S) traffic. On each completed response: logs it, stores
it via the memory layer, and runs extraction against the response body
to capture any security-relevant values (tokens, session IDs, etc.).
"""

from mitmproxy import http

from ephemera.core.memory import record_extracted_variables, record_request


class EphemeraAddon:
    """mitmproxy addon: logs, stores, and extracts from every request/response."""

    def request(self, flow: http.HTTPFlow) -> None:
        """Called when a request arrives, before it's forwarded to the target."""
        print(f"[REQUEST]  {flow.request.method} {flow.request.pretty_url}")

    def response(self, flow: http.HTTPFlow) -> None:
        """Called when the response arrives, before it's returned to the client."""
        status = flow.response.status_code
        content = flow.response.content
        length = len(content) if content else 0
        print(f"[RESPONSE] {status} {flow.request.pretty_url} ({length} bytes)")

        record_request(
            url=flow.request.pretty_url,
            method=flow.request.method,
            status_code=status,
            response_bytes=length,
        )

        if content:
            record_extracted_variables(url=flow.request.pretty_url, response_body=content)


addons = [EphemeraAddon()]
