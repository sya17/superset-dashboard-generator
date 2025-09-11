"""
Pydantic models for API responses and requests.
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


# Base models
class SupersetBase(BaseModel):
    """Base model for Superset resources."""
    id: int


# Dataset models
class DatasetResponse(SupersetBase):
    """Dataset response model."""
    table_name: str = Field(..., description="Name of the table")
    schema_name: Optional[str] = Field(None, description="Database schema name")
    database: Optional[Dict[str, Any]] = Field(None, description="Database information")
    owners: Optional[List[Dict[str, Any]]] = Field(None, description="Dataset owners")


class DatasetListResponse(BaseModel):
    """Response model for dataset list endpoint."""
    result: List[DatasetResponse]
    count: int = Field(..., description="Total number of datasets")


# Chart models
class ChartResponse(SupersetBase):
    """Chart response model."""
    slice_name: str = Field(..., description="Name of the chart")
    viz_type: Optional[str] = Field(None, description="Visualization type")
    datasource_id: Optional[int] = Field(None, description="Datasource ID")
    owners: Optional[List[Dict[str, Any]]] = Field(None, description="Chart owners")


class ChartListResponse(BaseModel):
    """Response model for chart list endpoint."""
    result: List[ChartResponse]
    count: int = Field(..., description="Total number of charts")


# Dashboard models
class DashboardResponse(SupersetBase):
    """Dashboard response model."""
    dashboard_title: str = Field(..., description="Title of the dashboard")
    slug: Optional[str] = Field(None, description="Dashboard slug")
    owners: Optional[List[Dict[str, Any]]] = Field(None, description="Dashboard owners")


class DashboardListResponse(BaseModel):
    """Response model for dashboard list endpoint."""
    result: List[DashboardResponse]
    count: int = Field(..., description="Total number of dashboards")


# Query parameter models
class PaginationParams(BaseModel):
    """Common pagination parameters."""
    page: int = Field(0, ge=0, description="Page number (0-based)")
    page_size: int = Field(25, ge=1, le=100, description="Items per page")


class SearchParams(PaginationParams):
    """Search and pagination parameters."""
    q: Optional[str] = Field(None, description="Search query")


# Info response models
class SupersetInfo(BaseModel):
    """Generic info response model."""
    result: Dict[str, Any]


# Debug models
class UserInfoResponse(BaseModel):
    """User information response."""
    id: int
    username: str
    email: Optional[str] = None
    roles: List[Dict[str, Any]] = []


class ResourceAccessSummary(BaseModel):
    """Summary of accessible resources."""
    datasets: Dict[str, Any]
    charts: Dict[str, Any]
    dashboards: Dict[str, Any]


# Error response models
class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: Optional[str] = None
