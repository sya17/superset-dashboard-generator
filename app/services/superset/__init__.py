"""
Superset API client package.

This package provides a modular and well-organized client for interacting
with Apache Superset API, with proper separation of concerns.
"""

from .client import SupersetClient
from .import_manager import SupersetImportManager
from .constants import (
    API_BASE_PATH,
    LOGIN_ENDPOINT,
    CSRF_TOKEN_ENDPOINT,
    DEFAULT_TIMEOUT,
    DEFAULT_CHART_QUERY_PARAMS
)
from .exceptions import (
    SupersetClientError,
    AuthenticationError,
    CSRFTokenError,
    APIRequestError,
    SessionError
)

# For backward compatibility
def get_superset_client() -> SupersetClient:
    """Get singleton Superset client instance."""
    return SupersetClient()

__all__ = [
    # Main client
    "SupersetClient",
    "SupersetImportManager",
    "get_superset_client",

    # Exceptions
    "SupersetClientError",
    "AuthenticationError",
    "CSRFTokenError",
    "APIRequestError",
    "SessionError",

    # Constants
    "API_BASE_PATH",
    "LOGIN_ENDPOINT",
    "CSRF_TOKEN_ENDPOINT",
    "DEFAULT_TIMEOUT",
    "DEFAULT_CHART_QUERY_PARAMS",
]
