"""Ephemera's core mitmproxy addon.

Intercepts HTTP(S) traffic. On each completed response: logs it, opens
a database session, and stores + extracts through the memory layer.
"""

from mitmproxy import http

from ephemera.core.memory import record_extracted_variables, record_request
from ephemera.database.session import get_session


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

        with get_session() as session:
            record_request(
                session=session,
                url=flow.request.pretty_url,
                method=flow.request.method,
                status_code=status,
                response_bytes=length,
            )
            if content:
                record_extracted_variables(
                    session=session, url=flow.request.pretty_url, response_body=content
                )


addons = [EphemeraAddon()]
