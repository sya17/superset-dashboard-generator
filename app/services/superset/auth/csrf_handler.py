"""
CSRF token management for Superset client.
"""
import re
from typing import Optional, Dict, Any
from urllib.parse import urljoin
import logging

from ..constants import (
    CSRF_PATTERNS,
    MIN_CSRF_TOKEN_LENGTH,
    CSRF_TIMEOUT,
    LOGIN_PAGE_ENDPOINT,
    CSRF_TOKEN_ENDPOINT
)
from ..exceptions import CSRFTokenError

logger = logging.getLogger(__name__)


class CSRFHandler:
    """Handles CSRF token retrieval and management."""

    def __init__(self, session_manager, base_url: str):
        self.session_manager = session_manager
        self.base_url = base_url
        self._csrf_token: Optional[str] = None

    @property
    def csrf_token(self) -> Optional[str]:
        """Get the current CSRF token."""
        return self._csrf_token

    def get_csrf_token(self, access_token: Optional[str] = None) -> Optional[str]:
        """
        Retrieve CSRF token using multiple fallback methods.

        Args:
            access_token: Optional JWT access token for authenticated requests

        Returns:
            CSRF token string or None if retrieval fails
        """
        try:
            # Method 1: API endpoint with authentication
            if access_token:
                token = self._get_csrf_from_api(access_token)
                if token:
                    return token

            # Method 2: Login page extraction
            token = self._get_csrf_from_login_page()
            if token:
                return token

            # Method 3: Unauthenticated API endpoint
            token = self._get_csrf_from_unauthenticated_api()
            if token:
                return token

            # Method 4: Extract from session cookies
            token = self._get_csrf_from_cookies()
            if token:
                return token

            logger.warning("Could not retrieve CSRF token using any method")
            return None

        except Exception as e:
            logger.error(f"Failed to get CSRF token: {e}")
            return None

    def _get_csrf_from_api(self, access_token: str) -> Optional[str]:
        """Get CSRF token from authenticated API endpoint."""
        try:
            session = self.session_manager.get_session()
            csrf_url = urljoin(self.base_url, CSRF_TOKEN_ENDPOINT)
            headers = {"Authorization": f"Bearer {access_token}"}

            response = session.get(csrf_url, headers=headers, timeout=CSRF_TIMEOUT)
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    self._csrf_token = result["result"]
                    logger.info("Successfully retrieved CSRF token via API")
                    return self._csrf_token
        except Exception as e:
            logger.warning(f"API CSRF retrieval failed: {e}")
        return None

    def _get_csrf_from_login_page(self) -> Optional[str]:
        """Extract CSRF token from login page HTML."""
        try:
            session = self.session_manager.get_session()
            login_page_url = urljoin(self.base_url, LOGIN_PAGE_ENDPOINT)

            response = session.get(login_page_url, timeout=CSRF_TIMEOUT)
            response.raise_for_status()

            for pattern in CSRF_PATTERNS:
                match = re.search(pattern, response.text)
                if match:
                    potential_token = match.group(1)
                    if len(potential_token) > MIN_CSRF_TOKEN_LENGTH:
                        self._csrf_token = potential_token
                        logger.info("Retrieved CSRF token from login page")
                        return self._csrf_token
        except Exception as e:
            logger.warning(f"Login page CSRF extraction failed: {e}")
        return None

    def _get_csrf_from_unauthenticated_api(self) -> Optional[str]:
        """Get CSRF token from unauthenticated API endpoint."""
        try:
            session = self.session_manager.get_session()
            csrf_url = urljoin(self.base_url, CSRF_TOKEN_ENDPOINT)

            response = session.get(csrf_url, timeout=CSRF_TIMEOUT)
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    self._csrf_token = result["result"]
                    logger.info("Retrieved CSRF token via unauthenticated API")
                    return self._csrf_token
        except Exception as e:
            logger.warning(f"Unauthenticated CSRF retrieval failed: {e}")
        return None

    def _get_csrf_from_cookies(self) -> Optional[str]:
        """Extract CSRF token from session cookies."""
        try:
            session = self.session_manager.get_session()
            for cookie in session.cookies:
                if 'csrf' in cookie.name.lower():
                    self._csrf_token = cookie.value
                    logger.info(f"Retrieved CSRF token from cookie: {cookie.name}")
                    return self._csrf_token
        except Exception as e:
            logger.warning(f"Cookie CSRF extraction failed: {e}")
        return None

    def reset_token(self) -> None:
        """Reset the CSRF token."""
        self._csrf_token = None
        logger.debug("CSRF token reset")
