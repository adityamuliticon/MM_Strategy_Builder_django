"""Market Maya authentication — builds request headers from the current thread-local token.

Stateless: each call reads the thread-local token so concurrent requests
(different users in different threads) each get their own correct header.
"""


class Auth:

    @staticmethod
    def headers() -> dict:
        from services.token_service import get_auth_header
        return {
            "Authorization": get_auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @staticmethod
    def refreshed_headers() -> dict:
        """Force-refresh the bearer token then return fresh headers (called after a 401)."""
        from services.token_service import force_refresh, get_auth_header
        force_refresh()
        return {
            "Authorization": get_auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
