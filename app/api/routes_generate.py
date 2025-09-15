"""
Routes for generating content using AI models.

This module provides endpoints for generating charts, dashboards, and other
Superset resources using AI assistance.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.services import get_superset_client
from app.services.chart_generator.chart_generator import ChartGenerator
from app.services.chart_exporter.chart_exporter import ChartExporter
from app.services.dataset_selector.dataset_selector import DatasetSelector
from app.services.model_client import get_model_client
from app.services.superset.client import SupersetClient
from .models import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate")


class GenerationRequest(BaseModel):
    """Request model for content generation."""
    prompt: str = Field(..., description="Natural language description of what to generate")


class DatasetInfo(BaseModel):
    """Dataset information model."""
    name: str = Field(..., description="Dataset name")
    id: Optional[int] = Field(None, description="Dataset ID")
    table_name: Optional[str] = Field(None, description="Table name")
    columns: Optional[list] = Field(None, description="Available columns")

class ChartInfo(BaseModel):
    """Chart information model."""
    id: Optional[int] = Field(None, description="Chart ID in Superset")
    name: Optional[str] = Field(None, description="Chart name")
    viz_type: Optional[str] = Field(None, description="Visualization type")
    url: Optional[str] = Field(None, description="Chart URL in Superset")
    success: bool = Field(..., description="Whether chart creation was successful")
    error: Optional[str] = Field(None, description="Error message if chart creation failed")

class ExportInfo(BaseModel):
    """Chart export information model."""
    success: bool = Field(..., description="Whether export was successful")
    chart_id: Optional[int] = Field(None, description="Exported chart ID")
    files_exported: Optional[int] = Field(None, description="Number of files exported")
    export_path: Optional[str] = Field(None, description="Path to export files")
    error: Optional[str] = Field(None, description="Error message if export failed")

class GenerationResult(BaseModel):
    """Detailed generation result model."""
    dataset: DatasetInfo = Field(..., description="Selected dataset information")
    chart: ChartInfo = Field(..., description="Generated chart information")
    export: Optional[ExportInfo] = Field(None, description="Chart export information (optional)")

class GenerationResponse(BaseModel):
    """Response model for generation requests."""
    success: bool = Field(..., description="Overall generation success status")
    task_id: str = Field(..., description="Generation task ID")
    message: str = Field(..., description="Human-readable status message")
    result: Optional[GenerationResult] = Field(None, description="Generation result details")
    execution_time: float = Field(..., description="Time taken to execute (seconds)")
    timestamp: str = Field(..., description="Generation timestamp")


class GenerationStatus(BaseModel):
    """Status model for generation tasks."""
    id: str
    status: str  # pending, processing, completed, failed
    progress: Optional[float] = None
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


# Generation tasks storage removed - using synchronous processing now


@router.post(
    "/",
    response_model=GenerationResponse,
    summary="Generate Superset Resource",
    description="""Generate a Superset resource (chart, dashboard, etc.) using AI assistance.

    The response includes:
    - **success**: Overall operation success (based on chart creation)
    - **result.dataset**: Selected dataset information with columns
    - **result.chart**: Generated chart details with Superset URL
    - **result.export**: Optional chart export details (won't affect main response if fails)

    Chart export is optional and handled asynchronously with timeout protection.
    The main response success depends only on chart creation, not export status.
    """
)
async def generate_resource(
    request: GenerationRequest
) -> GenerationResponse:
    """
    Generate a Superset resource based on natural language description.

    This endpoint processes the generation request synchronously and returns
    the result immediately. Useful for development and testing.
    """
    import time
    import uuid

    start_time = time.time()
    task_id = str(uuid.uuid4())

    try:
        logger.info(f"🚀 Starting generation task {task_id}")
        logger.info(f"📝 Prompt: {request.prompt}")

        # 
        print("\n")
        print("="*50)
        custom_superset = SupersetClient()
        custom_model = get_model_client()
        selector = DatasetSelector(superset_client=custom_superset,model_client=custom_model)
        chart_generator = ChartGenerator()

        result = await selector.select_datasets_async(request.prompt, include_details=True)
        
        # Ambil dataset pertama yang terpilih (atau bisa dikustomisasi)
        selected_dataset_names = result["selected_datasets"]
        
        if not selected_dataset_names:
            raise HTTPException(status_code=400, detail="No suitable datasets found for the given prompt")
        
        selected_dataset_name = selected_dataset_names[0]
        logger.info(f'selected_dataset_name: {selected_dataset_name}')

        print("="*50)
        print("\n")

        # Get dataset details from result (sudah di-fetch otomatis)
        dataset_details = result.get("dataset_details", {})
        
        if selected_dataset_name not in dataset_details:
            raise HTTPException(status_code=500, detail=f"Details for dataset '{selected_dataset_name}' not found")
            
        dataset_selected = dataset_details[selected_dataset_name]
        # logger.info(f'dataset_selected: {dataset_selected}')

        print("\n")
        print("="*50)
        chart_result = await chart_generator.generate_chart(user_prompt=request.prompt, dataset_selected=dataset_selected)
        # logger.info(f'chart_result: {chart_result}')

        print("="*50)
        print("\n")
        
        
        print("\n")
        print("="*50)
        # Optional chart export - tidak mempengaruhi response utama jika gagal
        export_result = None
        if chart_result.get("success") and chart_result.get("chart", {}).get("id"):
            try:
                chart_id = chart_result["chart"]["id"]
                logger.info(f"🔄 Starting optional chart export for chart ID: {chart_id}")

                # Timeout untuk export agar tidak mengganggu response utama
                import asyncio
                
                chart_exporter = ChartExporter()

                # Export dengan timeout 30 detik
                export_task = asyncio.create_task(
                    chart_exporter.export_chart(chart_id)
                )

                try:
                    export_result = await asyncio.wait_for(export_task, timeout=30.0)

                    if export_result.get("success"):
                        logger.info(f"📦 Chart export completed successfully")
                    else:
                        logger.warning(f"⚠️ Chart export failed but won't affect main response: {export_result.get('error')}")

                except asyncio.TimeoutError:
                    logger.warning(f"⏰ Chart export timed out after 30 seconds, continuing with main response")
                    export_result = {"success": False, "error": "Export timed out after 30 seconds"}
                    
            except Exception as export_error:
                logger.warning(f"⚠️ Chart export failed but won't affect main response: {export_error}")
                export_result = {"success": False, "error": str(export_error)}
        else:
            logger.info("📋 Skipping chart export (chart not created successfully or chart ID missing)")

        print("="*50)
        print("\n")        
        # 

        execution_time = time.time() - start_time
        logger.info(f"⏱️ Generation completed in {execution_time:.2f}s")
        logger.info(f"✅ Generation completed successfully")

        # Build structured result untuk frontend
        dataset_info = DatasetInfo(
            name=selected_dataset_name,
            id=dataset_selected.get("id"),
            table_name=dataset_selected.get("table_name"),
            columns=[col.get("column_name") for col in dataset_selected.get("columns", [])]
        )

        chart_info = ChartInfo(
            success=chart_result.get("success", False),
            id=chart_result.get("chart", {}).get("id"),
            name=chart_result.get("chart", {}).get("slice_name"),
            viz_type=chart_result.get("chart", {}).get("viz_type"),
            url=chart_result.get("chart", {}).get("url"),
            error=chart_result.get("error")
        )

        export_info = None
        if export_result:
            export_info = ExportInfo(
                success=export_result.get("success", False),
                chart_id=export_result.get("chart_id"),
                files_exported=export_result.get("extracted_files", {}).get("total_files"),
                export_path=export_result.get("extracted_files", {}).get("extract_directory"),
                error=export_result.get("error")
            )

        generation_result = GenerationResult(
            dataset=dataset_info,
            chart=chart_info,
            export=export_info
        )

        # Determine overall success and create informative message
        chart_success = chart_result.get("success", False)
        export_success = export_result.get("success", False) if export_result else None

        if chart_success:
            if export_success:
                message = "Dashboard and chart export completed successfully"
            elif export_success is False:
                message = "Dashboard created successfully, but chart export failed (this doesn't affect chart functionality)"
            else:
                message = "Dashboard created successfully (chart export was skipped)"
        else:
            message = f"Dashboard creation failed: {chart_result.get('error', 'Unknown error')}"

        return GenerationResponse(
            success=chart_success,  # Main success only depends on chart creation
            task_id=task_id,
            message=message,
            result=generation_result,
            execution_time=round(execution_time, 2),
            timestamp=_get_current_timestamp()
        )

    except HTTPException as he:
        # Re-raise HTTP exceptions to maintain proper status codes
        raise he

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ Generation failed after {execution_time:.2f}s: {e}")

        # Provide more specific error messages based on error type
        if "dataset" in str(e).lower():
            error_message = "Failed to select or process dataset. Please check if the dataset exists and is accessible."
        elif "chart" in str(e).lower():
            error_message = "Failed to generate chart. Please check the chart configuration and dataset compatibility."
        elif "connection" in str(e).lower() or "request" in str(e).lower():
            error_message = "Failed to connect to Superset. Please check the connection settings and try again."
        else:
            error_message = f"Unexpected error during dashboard generation: {str(e)}"

        return GenerationResponse(
            success=False,
            task_id=task_id,
            message=error_message,
            result=None,
            execution_time=round(execution_time, 2),
            timestamp=_get_current_timestamp()
        )

def _get_current_timestamp() -> str:
    """Get current timestamp dalam format ISO."""
    from datetime import datetime
    return datetime.now().isoformat()
