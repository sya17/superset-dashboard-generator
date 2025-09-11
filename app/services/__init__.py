"""
Superset services package.

This package provides modular components for interacting with Apache Superset API,
including authentication, CSRF handling, session management, and API client functionality.
"""

# Import from the new superset package
from .superset import (
    SupersetClient,
    get_superset_client,
    SupersetClientError,
    AuthenticationError,
    CSRFTokenError,
    APIRequestError,
    SessionError,
    API_BASE_PATH,
    LOGIN_ENDPOINT,
    CSRF_TOKEN_ENDPOINT,
    DEFAULT_TIMEOUT,
    DEFAULT_CHART_QUERY_PARAMS
)

# Also import individual components for advanced usage
from .superset.auth import AuthManager, CSRFHandler
from .superset.http import SessionManager, APIClient, RequestHandler

# Import model client
from .model_client import get_model_client, DynamicModelClient

__all__ = [
    # Main client
    "SupersetClient",
    "get_superset_client",

    # Model client
    "get_model_client",
    "DynamicModelClient",

    # Core components
    "SessionManager",
    "AuthManager",
    "CSRFHandler",
    "APIClient",
    "RequestHandler",

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