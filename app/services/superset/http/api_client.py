"""
API client for making HTTP requests to Superset.
"""
import time
from typing import Dict, Any, Optional
from urllib.parse import urljoin
import logging

from ..constants import (
    API_BASE_PATH,
    DEFAULT_TIMEOUT,
    HTTP_SUCCESS_MIN,
    HTTP_SUCCESS_MAX,
    HTTP_UNAUTHORIZED,
    HTTP_BAD_REQUEST,
    MAX_ERROR_RESPONSE_LOG_LENGTH
)
from ..exceptions import APIRequestError

logger = logging.getLogger(__name__)


class APIClient:
    """Handles HTTP requests to Superset API with proper error handling and logging."""

    def __init__(self, session_manager, base_url: str):
        self.session_manager = session_manager
        self.base_url = base_url

    def request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the Superset API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without /api/v1 prefix)
            headers: Additional headers to include
            **kwargs: Additional arguments for requests

        Returns:
            JSON response data

        Raises:
            APIRequestError: If the request fails
        """
        url = urljoin(self.base_url, f"{API_BASE_PATH}/{endpoint}")
        start_time = time.time()

        try:
            session = self.session_manager.get_session()
            request_headers = headers or {}

            # Log request details
            self._log_request(method, endpoint, url, request_headers, kwargs)

            # Set default timeout if not provided
            if 'timeout' not in kwargs:
                kwargs['timeout'] = DEFAULT_TIMEOUT

            response = session.request(method, url, headers=request_headers, **kwargs)

            # Log response details
            response_time_ms = (time.time() - start_time) * 1000
            self._log_response(method, endpoint, response, response_time_ms)

            response.raise_for_status()
            return response.json()

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            self._log_error(method, endpoint, e, response_time_ms)
            raise APIRequestError(f"API request failed: {e}")

    def _log_request(
        self,
        method: str,
        endpoint: str,
        url: str,
        headers: Dict[str, str],
        kwargs: Dict[str, Any]
    ) -> None:
        """Log request details."""
        logger.info(f"🔗 SUPERSET API CALL: {method} {endpoint}")
        logger.info(f"🔗 SUPERSET API URL: {url}")
        logger.info(f"🔗 SUPERSET API HEADERS: {self._mask_sensitive_headers(headers)}")
        logger.info(f"🔗 SUPERSET API **kwargs: {kwargs}")

    def _log_response(self, method: str, endpoint: str, response, response_time_ms: float) -> None:
        """Log response details."""
        status_code = response.status_code

        if HTTP_SUCCESS_MIN <= status_code <= HTTP_SUCCESS_MAX:
            logger.info(f"✅ SUPERSET API SUCCESS: {method} {endpoint} → {status_code} | {response_time_ms:.2f}ms")
        else:
            logger.warning(f"⚠️ SUPERSET API WARNING: {method} {endpoint} → {status_code} | {response_time_ms:.2f}ms")

        # Log response size
        content_length = response.headers.get('content-length')
        if content_length:
            logger.debug(f"Response size: {content_length} bytes")

        # Log error details for failed requests
        if status_code >= HTTP_BAD_REQUEST:
            try:
                error_data = response.json()
                logger.error(f"SUPERSET API ERROR DETAILS: {error_data}")
            except:
                error_text = response.text[:MAX_ERROR_RESPONSE_LOG_LENGTH]
                logger.error(f"SUPERSET API ERROR: {error_text}...")

    def _log_error(self, method: str, endpoint: str, error: Exception, response_time_ms: float) -> None:
        """Log error details."""
        logger.error(f"❌ SUPERSET API ERROR: {method} {endpoint} | {error} | {response_time_ms:.2f}ms")

    def _mask_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Mask sensitive header values for logging."""
        masked = {}
        for key, value in headers.items():
            if 'authorization' in key.lower():
                masked[key] = '***Bearer***'
            elif 'csrf' in key.lower():
                masked[key] = '***' if value else 'None'
            else:
                masked[key] = value
        return masked
