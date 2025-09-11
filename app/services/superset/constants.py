"""
Constants and configuration values for Superset client.
"""
import re
from typing import List

# API Endpoints
API_BASE_PATH = "/api/v1"
LOGIN_ENDPOINT = "/api/v1/security/login"
CSRF_TOKEN_ENDPOINT = "/api/v1/security/csrf_token"
LOGIN_PAGE_ENDPOINT = "/login"

# HTTP Configuration
DEFAULT_TIMEOUT = 15
LOGIN_TIMEOUT = 10
CSRF_TIMEOUT = 10

# Retry Configuration
RETRY_TOTAL = 3
RETRY_BACKOFF_FACTOR = 1
RETRY_STATUS_FORCELIST = [500, 502, 503, 504]

# CSRF Token Patterns
CSRF_PATTERNS: List[str] = [
    r'csrf_token["\'\s:=]+([a-zA-Z0-9_-]+)',
    r'_csrf_token["\'\s:=]+([a-zA-Z0-9_-]+)',
    r'name=["\']csrf_token["\'].*?value=["\']([a-zA-Z0-9_-]+)["\']'
]

# Authentication
AUTH_PROVIDER = "db"
MIN_CSRF_TOKEN_LENGTH = 10

# HTTP Status Codes
HTTP_SUCCESS_MIN = 200
HTTP_SUCCESS_MAX = 399
HTTP_UNAUTHORIZED = 401
HTTP_BAD_REQUEST = 400
HTTP_REDIRECT_MIN = 300
HTTP_REDIRECT_MAX = 399

# Response size limits for logging
MAX_ERROR_RESPONSE_LOG_LENGTH = 200

# Chart query parameters
DEFAULT_CHART_QUERY_PARAMS = {
    "columns": [],
    "keys": ["show_columns"],
}
