"""
Debug routes for Superset API - separated from production routes.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends

from .service import SupersetAPIService, get_superset_service
from .models import UserInfoResponse, ResourceAccessSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug")


@router.get(
    "/user-info",
    response_model=UserInfoResponse,
    summary="Get Current User Information",
    description="Debug endpoint to check current user permissions and info."
)
async def get_current_user_info(service: SupersetAPIService = Depends(get_superset_service)):
    """Get current user information for debugging purposes."""
    try:
        return service.get_user_info()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to get user info: {str(e)}"
        )


@router.get(
    "/all-accessible",
    response_model=ResourceAccessSummary,
    summary="Get Accessible Resources Summary",
    description="Debug endpoint to check what resources current user can access."
)
async def get_all_accessible_resources(service: SupersetAPIService = Depends(get_superset_service)):
    """Get summary of all accessible resources for debugging."""
    try:
        return service.get_accessible_resources()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to check accessible resources: {str(e)}"
        )
