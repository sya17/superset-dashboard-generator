"""
Routes for chart export functionality.

This module provides endpoints for exporting charts from Superset.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

from app.services.chart_exporter.chart_exporter import ChartExporter
from .models import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export")


class ExportResponse(BaseModel):
    """Response model for export requests."""
    success: bool = Field(..., description="Export success status")
    chart_id: int = Field(..., description="Chart ID that was exported")
    zip_file_path: Optional[str] = Field(None, description="Path to exported ZIP file")
    extracted_files: Optional[Dict[str, Any]] = Field(None, description="Information about extracted files")
    export_timestamp: Optional[str] = Field(None, description="Export timestamp")
    error: Optional[str] = Field(None, description="Error message if export failed")


class ExportInfoResponse(BaseModel):
    """Response model for export info requests."""
    chart_id: int = Field(..., description="Chart ID")
    exists: bool = Field(..., description="Whether export exists")
    info: Optional[Dict[str, Any]] = Field(None, description="Export information")


@router.post(
    "/chart/{chart_id}",
    response_model=ExportResponse,
    summary="Export Chart",
    description="Export a specific chart from Superset and save to cache."
)
async def export_chart(
    chart_id: int = Path(..., description="Chart ID to export", gt=0)
) -> ExportResponse:
    """
    Export a chart from Superset by ID.

    This endpoint exports the specified chart, saves the ZIP file to cache,
    and extracts the contents for analysis.

    Args:
        chart_id: The ID of the chart to export

    Returns:
        ExportResponse with export result information

    Raises:
        HTTPException: If chart_id is invalid or export fails
    """
    try:
        logger.info(f"🚀 Starting manual chart export for chart ID: {chart_id}")

        # Initialize chart exporter
        chart_exporter = ChartExporter()

        # Perform export
        export_result = await chart_exporter.export_chart(chart_id)

        if export_result.get("success"):
            logger.info(f"✅ Chart export completed successfully for chart ID: {chart_id}")
            return ExportResponse(**export_result)
        else:
            error_msg = export_result.get("error", "Unknown export error")
            logger.error(f"❌ Chart export failed for chart ID {chart_id}: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Chart export failed: {error_msg}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during chart export: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during export: {str(e)}"
        )


@router.get(
    "/chart/{chart_id}/info",
    response_model=ExportInfoResponse,
    summary="Get Export Info",
    description="Get information about existing chart export."
)
async def get_export_info(
    chart_id: int = Path(..., description="Chart ID to check", gt=0)
) -> ExportInfoResponse:
    """
    Get information about an existing chart export.

    Args:
        chart_id: The ID of the chart to check

    Returns:
        ExportInfoResponse with export information

    Raises:
        HTTPException: If chart_id is invalid
    """
    try:
        logger.info(f"📋 Getting export info for chart ID: {chart_id}")

        # Initialize chart exporter
        chart_exporter = ChartExporter()

        # Get export info
        export_info = chart_exporter.get_export_info(chart_id)

        if export_info:
            return ExportInfoResponse(
                chart_id=chart_id,
                exists=True,
                info=export_info
            )
        else:
            return ExportInfoResponse(
                chart_id=chart_id,
                exists=False,
                info=None
            )

    except Exception as e:
        logger.error(f"❌ Error getting export info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting export info: {str(e)}"
        )


@router.delete(
    "/chart/{chart_id}",
    summary="Clean Export",
    description="Clean up export files for a specific chart."
)
async def cleanup_export(
    chart_id: int = Path(..., description="Chart ID to clean up", gt=0)
) -> Dict[str, Any]:
    """
    Clean up export files for a specific chart.

    Args:
        chart_id: The ID of the chart to clean up

    Returns:
        Dictionary with cleanup result

    Raises:
        HTTPException: If chart_id is invalid or cleanup fails
    """
    try:
        logger.info(f"🧹 Cleaning up export for chart ID: {chart_id}")

        # Initialize chart exporter
        chart_exporter = ChartExporter()

        # Perform cleanup
        success = chart_exporter.cleanup_export(chart_id)

        if success:
            return {
                "success": True,
                "chart_id": chart_id,
                "message": "Export files cleaned up successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to cleanup export files"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error during cleanup: {str(e)}"
        )