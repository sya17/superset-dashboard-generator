"""
Superset API routes - Production endpoints.

This module provides REST API endpoints for interacting with Apache Superset
datasets, charts, and dashboards.
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Depends, Query

from .service import SupersetAPIService, get_superset_service
from .models import (
    DatasetListResponse,
    DatasetResponse,
    ChartListResponse,
    ChartResponse,
    DashboardListResponse,
    DashboardResponse,
    SupersetInfo,
    SearchParams
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/superset")


# Dataset endpoints
@router.get(
    "/datasets",
    response_model=DatasetListResponse,
    summary="List Datasets",
    description="Get a paginated list of all available datasets with optional search."
)
async def list_datasets(
    q: str = Query(None, description="Search query for table names"),
    page: int = Query(0, ge=0, description="Page number (0-based)"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    service: SupersetAPIService = Depends(get_superset_service)
) -> DatasetListResponse:
    """List all available datasets with search and pagination."""
    try:
        params = SearchParams(q=q, page=page, page_size=page_size)
        return service.get_datasets(params)
    except Exception as e:
        logger.error(f"Failed to fetch datasets: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch datasets from Superset: {str(e)}"
        )


@router.get(
    "/datasets/{dataset_id}",
    response_model=DatasetResponse,
    summary="Get Dataset Details",
    description="Get detailed information for a specific dataset."
)
async def get_dataset_detail(
    dataset_id: int,
    service: SupersetAPIService = Depends(get_superset_service)
) -> DatasetResponse:
    """Get details for a single dataset."""
    try:
        return service.get_dataset(dataset_id)
    except Exception as e:
        logger.error(f"Failed to fetch dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch dataset {dataset_id}: {str(e)}"
        )


@router.get(
    "/datasets/info",
    response_model=SupersetInfo,
    summary="Get Dataset Metadata",
    description="Get metadata information for dataset creation and configuration."
)
async def get_dataset_info(service: SupersetAPIService = Depends(get_superset_service)) -> SupersetInfo:
    """Get metadata for dataset creation (_info endpoint)."""
    try:
        return SupersetInfo(result=service.get_dataset_info())
    except Exception as e:
        logger.error(f"Failed to fetch dataset info: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch dataset info: {str(e)}"
        )


# Chart endpoints
@router.get(
    "/charts",
    response_model=ChartListResponse,
    summary="List Charts",
    description="Get a paginated list of all available charts with optional search."
)
async def list_charts(
    q: str = Query(None, description="Search query for chart names"),
    page: int = Query(0, ge=0, description="Page number (0-based)"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    service: SupersetAPIService = Depends(get_superset_service)
) -> ChartListResponse:
    """List all available charts with search and pagination."""
    try:
        params = SearchParams(q=q, page=page, page_size=page_size)
        return service.get_charts(params)
    except Exception as e:
        logger.error(f"Failed to fetch charts: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch charts from Superset: {str(e)}"
        )


@router.get(
    "/charts/{chart_id}",
    response_model=ChartResponse,
    summary="Get Chart Details",
    description="Get detailed information for a specific chart."
)
async def get_chart_detail(
    chart_id: int,
    service: SupersetAPIService = Depends(get_superset_service)
) -> ChartResponse:
    """Get details for a single chart."""
    try:
        return service.get_chart(chart_id)
    except Exception as e:
        logger.error(f"Failed to fetch chart {chart_id}: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch chart {chart_id}: {str(e)}"
        )


@router.get(
    "/charts/info",
    response_model=SupersetInfo,
    summary="Get Chart Metadata",
    description="Get metadata information for chart creation and configuration."
)
async def get_chart_info(service: SupersetAPIService = Depends(get_superset_service)) -> SupersetInfo:
    """Get metadata for chart creation (_info endpoint)."""
    try:
        return SupersetInfo(result=service.get_chart_info())
    except Exception as e:
        logger.error(f"Failed to fetch chart info: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch chart info: {str(e)}"
        )


# Dashboard endpoints
@router.get(
    "/dashboards",
    response_model=DashboardListResponse,
    summary="List Dashboards",
    description="Get a paginated list of all available dashboards with optional search."
)
async def list_dashboards(
    q: str = Query(None, description="Search query for dashboard titles"),
    page: int = Query(0, ge=0, description="Page number (0-based)"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    service: SupersetAPIService = Depends(get_superset_service)
) -> DashboardListResponse:
    """List all available dashboards with search and pagination."""
    try:
        params = SearchParams(q=q, page=page, page_size=page_size)
        return service.get_dashboards(params)
    except Exception as e:
        logger.error(f"Failed to fetch dashboards: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch dashboards from Superset: {str(e)}"
        )


@router.get(
    "/dashboards/{dashboard_id}",
    response_model=DashboardResponse,
    summary="Get Dashboard Details",
    description="Get detailed information for a specific dashboard."
)
async def get_dashboard_detail(
    dashboard_id: int,
    service: SupersetAPIService = Depends(get_superset_service)
) -> DashboardResponse:
    """Get details for a single dashboard."""
    try:
        return service.get_dashboard(dashboard_id)
    except Exception as e:
        logger.error(f"Failed to fetch dashboard {dashboard_id}: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch dashboard {dashboard_id}: {str(e)}"
        )


@router.get(
    "/dashboards/info",
    response_model=SupersetInfo,
    summary="Get Dashboard Metadata",
    description="Get metadata information for dashboard creation and configuration."
)
async def get_dashboard_info(service: SupersetAPIService = Depends(get_superset_service)) -> SupersetInfo:
    """Get metadata for dashboard creation (_info endpoint)."""
    try:
        return SupersetInfo(result=service.get_dashboard_info())
    except Exception as e:
        logger.error(f"Failed to fetch dashboard info: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch dashboard info: {str(e)}"
        )
