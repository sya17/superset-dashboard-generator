"""
API package for Superset backend.

This package contains all API-related modules including routes, models,
services, and utilities for the Superset backend application.
"""

from .constants import (
    build_query_params,
    add_search_filter,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    DATASET_COLUMNS,
    CHART_COLUMNS,
    DASHBOARD_COLUMNS
)

from .models import (
    DatasetResponse,
    DatasetListResponse,
    ChartResponse,
    ChartListResponse,
    DashboardResponse,
    DashboardListResponse,
    SupersetInfo,
    PaginationParams,
    SearchParams,
    UserInfoResponse,
    ResourceAccessSummary,
    ErrorResponse
)

from .service import SupersetAPIService, get_superset_service

from .routes_superset import router as superset_router
from .routes_debug import router as debug_router
from .routes_generate import router as generate_router
from .routes_export import router as export_router

__all__ = [
    # Constants
    "build_query_params",
    "add_search_filter",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "DATASET_COLUMNS",
    "CHART_COLUMNS",
    "DASHBOARD_COLUMNS",

    # Models
    "DatasetResponse",
    "DatasetListResponse",
    "ChartResponse",
    "ChartListResponse",
    "DashboardResponse",
    "DashboardListResponse",
    "SupersetInfo",
    "PaginationParams",
    "SearchParams",
    "UserInfoResponse",
    "ResourceAccessSummary",
    "ErrorResponse",

    # Services
    "SupersetAPIService",
    "get_superset_service",

    # Routers
    "superset_router",
    "debug_router",
    "generate_router",
    "export_router",
]
