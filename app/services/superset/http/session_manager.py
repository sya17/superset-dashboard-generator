"""
Session management for Superset client.
"""
import requests
from requests.adapters import HTTPAdapter, Retry
from typing import Optional
import logging

from ..constants import (
    RETRY_TOTAL,
    RETRY_BACKOFF_FACTOR,
    RETRY_STATUS_FORCELIST
)
from ..exceptions import SessionError

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages HTTP sessions with retry configuration."""

    def __init__(self):
        self._session: Optional[requests.Session] = None

    def get_session(self) -> requests.Session:
        """Get or create a configured session."""
        if self._session is None:
            self._session = self._create_session()
        return self._session

    def _create_session(self) -> requests.Session:
        """Create a new session with retry configuration."""
        try:
            session = requests.Session()
            retry_config = Retry(
                total=RETRY_TOTAL,
                backoff_factor=RETRY_BACKOFF_FACTOR,
                status_forcelist=RETRY_STATUS_FORCELIST
            )
            adapter = HTTPAdapter(max_retries=retry_config)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            logger.debug("Created new HTTP session with retry configuration")
            return session
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise SessionError(f"Could not create HTTP session: {e}")

    def close_session(self) -> None:
        """Close the current session."""
        if self._session:
            try:
                self._session.close()
                logger.debug("HTTP session closed")
            except Exception as e:
                logger.warning(f"Error closing session: {e}")
            finally:
                self._session = None

    def reset_session(self) -> None:
        """Reset the session by closing and creating a new one."""
        self.close_session()
        self._session = self._create_session()
        logger.debug("HTTP session reset")
