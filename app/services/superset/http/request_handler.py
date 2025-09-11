"""
Request handler that combines authentication, CSRF, and API client functionality.
"""
import json
from typing import Dict, Any, Optional
import logging

from ..constants import (
    HTTP_UNAUTHORIZED,
    HTTP_BAD_REQUEST,
    LOGIN_PAGE_ENDPOINT
)
from ..exceptions import APIRequestError
from ..auth.auth_manager import AuthManager
from ..auth.csrf_handler import CSRFHandler
from .api_client import APIClient

logger = logging.getLogger(__name__)


class RequestHandler:
    """Handles API requests with authentication, CSRF, and retry logic."""

    def __init__(self, session_manager, base_url: str, username: str, password: str):
        self.auth_manager = AuthManager(session_manager, base_url, username, password)
        self.csrf_handler = CSRFHandler(session_manager, base_url)
        self.api_client = APIClient(session_manager, base_url)

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request with CSRF handling and retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON payload
            **kwargs: Additional arguments

        Returns:
            JSON response data
        """
        try:
            # Ensure we have authentication
            access_token = self.auth_manager.ensure_authenticated()

            # Get CSRF token if needed
            csrf_token = self.csrf_handler.get_csrf_token(access_token)

            # Prepare headers
            headers = self._prepare_headers(access_token, csrf_token)

            # Make the request
            return self.api_client.request(
                method=method,
                endpoint=endpoint,
                headers=headers,
                params=params,
                json=json_data,
                **kwargs
            )

        except APIRequestError as e:
            # Handle authentication errors
            if self._is_authentication_error(e):
                return self._handle_authentication_retry(method, endpoint, params, json_data, kwargs)

            # Handle CSRF errors
            if self._is_csrf_error(e):
                return self._handle_csrf_retry(method, endpoint, params, json_data, kwargs)

            raise

    def _prepare_headers(self, access_token: str, csrf_token: Optional[str]) -> Dict[str, str]:
        """Prepare request headers with authentication and CSRF tokens."""
        headers = {"Authorization": f"Bearer {access_token}"}
        if csrf_token:
            headers["X-CSRFToken"] = csrf_token
        return headers

    def _is_authentication_error(self, error: APIRequestError) -> bool:
        """Check if the error is due to authentication issues."""
        error_str = str(error).lower()
        return '401' in error_str or 'unauthorized' in error_str

    def _is_csrf_error(self, error: APIRequestError) -> bool:
        """Check if the error is due to CSRF token issues."""
        error_str = str(error).lower()
        return 'csrf' in error_str or 'token' in error_str

    def _handle_authentication_retry(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        json_data: Optional[Dict[str, Any]],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle authentication retry after token expiration."""
        logger.info("🔄 Access token expired or invalid. Re-authenticating...")

        # Clear current authentication
        self.auth_manager.clear_authentication()

        # Retry with new authentication
        logger.info("🔄 Retrying request with new token...")
        return self.request(method, endpoint, params, json_data, **kwargs)

    def _handle_csrf_retry(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        json_data: Optional[Dict[str, Any]],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle CSRF token retry."""
        logger.info("CSRF token issue detected. Attempting to refresh token.")

        # Reset CSRF token
        self.csrf_handler.reset_token()

        # Try to get fresh CSRF token
        access_token = self.auth_manager.ensure_authenticated()
        csrf_token = self.csrf_handler.get_csrf_token(access_token)

        # If still no CSRF token, try session-based approach
        if not csrf_token:
            logger.info("Standard CSRF retrieval failed. Trying session-based approach.")
            session_response = self._session_based_request(method, endpoint, params, json_data, kwargs)
            if session_response:
                return session_response

        # Retry with new CSRF token
        return self.request(method, endpoint, params, json_data, **kwargs)

    def _session_based_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        json_data: Optional[Dict[str, Any]],
        kwargs: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Fallback session-based request for problematic endpoints."""
        try:
            logger.info("Attempting session-based authentication for CSRF token.")

            # This is a simplified version - in a real implementation,
            # you might want to implement the full session-based login flow
            # from the original code

            logger.warning("Session-based request not fully implemented in refactored version")
            return None

        except Exception as e:
            logger.error(f"Session-based request failed: {e}")
            return None
