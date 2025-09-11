"""
Authentication management for Superset client.
"""
from typing import Optional, Dict, Any
from urllib.parse import urljoin
import logging

from ..constants import (
    LOGIN_ENDPOINT,
    AUTH_PROVIDER,
    LOGIN_TIMEOUT
)
from ..exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class AuthManager:
    """Handles authentication with Superset API."""

    def __init__(self, session_manager, base_url: str, username: str, password: str):
        self.session_manager = session_manager
        self.base_url = base_url
        self.username = username
        self.password = password
        self._access_token: Optional[str] = None

    @property
    def access_token(self) -> Optional[str]:
        """Get the current access token."""
        return self._access_token

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._access_token is not None

    def authenticate(self) -> str:
        """
        Authenticate with Superset and retrieve access token.

        Returns:
            JWT access token

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            session = self.session_manager.get_session()
            login_url = urljoin(self.base_url, LOGIN_ENDPOINT)

            payload = {
                "username": self.username,
                "password": self.password,
                "provider": AUTH_PROVIDER
            }

            logger.info(f"Authenticating with Superset at {login_url}")
            response = session.post(login_url, json=payload, timeout=LOGIN_TIMEOUT)
            response.raise_for_status()

            response_data = response.json()
            if "access_token" not in response_data:
                raise AuthenticationError("No access token in authentication response")

            self._access_token = response_data["access_token"]
            logger.info("Successfully authenticated with Superset API")
            return self._access_token

        except Exception as e:
            error_msg = f"Failed to authenticate with Superset API: {e}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg)

    def ensure_authenticated(self) -> str:
        """
        Ensure we have a valid access token, re-authenticating if necessary.

        Returns:
            Valid access token
        """
        if not self.is_authenticated:
            return self.authenticate()
        return self._access_token

    def clear_authentication(self) -> None:
        """Clear the current access token."""
        self._access_token = None
        logger.debug("Authentication cleared")
