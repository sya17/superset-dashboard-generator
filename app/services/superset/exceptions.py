"""
Custom exceptions for Superset client operations.
"""


class SupersetClientError(Exception):
    """Base exception for Superset client errors."""
    pass


class AuthenticationError(SupersetClientError):
    """Raised when authentication with Superset fails."""
    pass


class CSRFTokenError(SupersetClientError):
    """Raised when CSRF token retrieval or validation fails."""
    pass


class APIRequestError(SupersetClientError):
    """Raised when an API request fails."""
    pass


class SessionError(SupersetClientError):
    """Raised when session management fails."""
    pass
