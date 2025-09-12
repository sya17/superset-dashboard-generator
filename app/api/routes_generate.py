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


class GenerationResponse(BaseModel):
    """Response model for generation requests."""
    id: str = Field(..., description="Generation task ID")
    status: str = Field(..., description="Generation status")
    message: str = Field(..., description="Status message")
    result: Optional[Dict[str, Any]] = Field(None, description="Generation result if completed")
    execution_time: Optional[float] = Field(None, description="Time taken to execute (seconds)")


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
    description="Generate a Superset resource (chart, dashboard, etc.) using AI assistance."
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
        # Export chart jika berhasil dibuat
        export_result = None
        if chart_result.get("success") and chart_result.get("chart", {}).get("id"):
            try:
                chart_id = chart_result["chart"]["id"]
                logger.info(f"🔄 Starting chart export for chart ID: {chart_id}")
                
                chart_exporter = ChartExporter()
                export_result = await chart_exporter.export_chart(chart_id)
                
                if export_result.get("success"):
                    logger.info(f"📦 Chart export completed successfully")
                else:
                    logger.warning(f"⚠️ Chart export failed: {export_result.get('error')}")
                    
            except Exception as export_error:
                logger.error(f"❌ Chart export error: {export_error}")
                export_result = {"success": False, "error": str(export_error)}

        print("="*50)
        print("\n")        
        # 

        execution_time = time.time() - start_time
        logger.info(f"⏱️ Generation completed in {execution_time:.2f}s")
        logger.info(f"✅ Generation completed successfully")

        # Build result dengan informasi chart dan export
        result_data = {
            "chart_generation": chart_result,
            "chart_export": export_result
        }

        return GenerationResponse(
            id=task_id,
            status="completed",
            message="Generation completed successfully",
            result=result_data,
            execution_time=round(execution_time, 2)
        )

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ Generation failed after {execution_time:.2f}s: {e}")

        return GenerationResponse(
            id=task_id,
            status="failed",
            message=f"Generation failed: {str(e)}",
            result=None,
            execution_time=round(execution_time, 2)
        )
