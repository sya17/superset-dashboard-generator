"""
Chart Generator Service
Service utama untuk menggenerate chart Superset menggunakan AI model.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from app.services.model_client import get_model_client
from app.services.superset.client import SupersetClient
from .instruction_builder import InstructionBuilder
from .constants import DEFAULT_QUERY_CONTEXT, CHART_CONFIGS
from .validators.chart_validator import ChartValidator
from .builders.query_context_builder import QueryContextBuilder

logger = logging.getLogger(__name__)


class ChartGeneratorError(Exception):
    """Exception untuk Chart Generator service."""
    pass


class ChartGenerator:
    """
    Service untuk menggenerate chart Superset menggunakan AI model.
    
    Flow:
    1. Terima user_prompt dan dataset_selected
    2. Build instruksi AI menggunakan InstructionBuilder  
    3. Kirim ke AI model untuk generate konfigurasi
    4. Validasi dan parse response AI
    5. Create chart via Superset API
    """
    
    def __init__(self):
        self.instruction_builder = InstructionBuilder()
        self.model_client = get_model_client()
        self.superset_client = SupersetClient()
        self.chart_validator = ChartValidator()
        self.query_context_builder = QueryContextBuilder()
        
        logger.info("ChartGenerator service initialized")
    
    async def generate_chart(
        self, 
        user_prompt: str, 
        dataset_selected: Dict[str, Any],
        dashboard_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate chart berdasarkan user prompt dan dataset.
        
        Args:
            user_prompt: Prompt dari user (e.g., "Buat Dashboard Pie Simpanan status")
            dataset_selected: Dataset hasil dari dataset_selector
            dashboard_id: Optional dashboard ID untuk associate chart
            
        Returns:
            Dictionary dengan informasi chart yang dibuat
        """
        try:
            logger.info(f"Starting chart generation for prompt: '{user_prompt}'")
            
            # 1. Build instruksi AI
            messages = self.instruction_builder.build_complete_instruction(
                user_prompt, dataset_selected
            )
            
            # 2. Generate konfigurasi via AI model
            logger.info("Generating chart configuration via AI model")
            ai_response = await self.model_client.generate_json_async(
                messages=messages,
                temperature=0.1,
                max_tokens=4000
            )
            
            logger.info(f"AI response received: {ai_response}")
            
            # Debug: Print messages yang dikirim ke AI
            logger.info(f"Messages sent to AI: {messages}")
            
            # Debug: Print raw content jika ada error
            if "error" in ai_response and "raw_content" in ai_response:
                logger.error(f"Raw AI content causing error: {repr(ai_response['raw_content'])}")
            
            if "error" in ai_response:
                logger.error(f"AI model JSON parsing failed: {ai_response['error']}")
                if "raw_content" in ai_response:
                    logger.error(f"Raw AI content: {ai_response['raw_content']}")
                raise ChartGeneratorError(f"AI model error: {ai_response['error']}")
            
            # 3. Validasi dan parse AI response
            chart_config = self.chart_validator.validate_ai_response(ai_response, dataset_selected)
            
            # 4. Generate query_context jika diperlukan
            if "query_context" not in chart_config:
                query_context = self.query_context_builder.generate_query_context(chart_config, dataset_selected)
                chart_config["query_context"] = json.dumps(query_context)
            elif isinstance(chart_config["query_context"], dict):
                # Pastikan query_context adalah string JSON
                chart_config["query_context"] = json.dumps(chart_config["query_context"])
            
            # 5. Create chart via Superset API
            logger.info("Creating chart via Superset API")
            created_chart = self.superset_client.create_chart(chart_config)
            logger.info(f'created_chart: {created_chart}')
            
            # 6. Associate dengan dashboard jika diminta
            if dashboard_id and created_chart.get("id"):
                await self._associate_chart_to_dashboard(
                    created_chart["id"], dashboard_id
                )
            
            result = {
                "success": True,
                "chart": created_chart,
                "ai_config": chart_config,
                "user_prompt": user_prompt,
                "dataset_used": dataset_selected.get("table_name"),
                "chart_type": chart_config.get("viz_type")
            }
            
            logger.info(f"Chart generated successfully: {created_chart.get('id')}")
            return result
            
        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_prompt": user_prompt,
                "dataset_used": dataset_selected.get("table_name") if dataset_selected else None
            }
    
    async def _associate_chart_to_dashboard(
        self, 
        chart_id: int, 
        dashboard_id: int
    ) -> Dict[str, Any]:
        """
        Associate chart ke dashboard.
        
        Args:
            chart_id: ID chart yang baru dibuat
            dashboard_id: ID dashboard target
            
        Returns:
            Response dari API
        """
        try:
            logger.info(f"Associating chart {chart_id} to dashboard {dashboard_id}")
            
            # Get existing charts di dashboard
            dashboard = self.superset_client.get_dashboard(dashboard_id)
            existing_chart_ids = [chart["id"] for chart in dashboard.get("charts", [])]
            
            # Add new chart to list
            updated_chart_ids = existing_chart_ids + [chart_id]
            
            # Update dashboard
            result = self.superset_client.add_charts_to_dashboard(
                dashboard_id, updated_chart_ids
            )
            
            logger.info(f"Chart {chart_id} associated to dashboard {dashboard_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error associating chart to dashboard: {e}")
            raise ChartGeneratorError(f"Failed to associate chart to dashboard: {e}")
    
    def get_supported_chart_types(self) -> List[Dict[str, Any]]:
        """
        Get list chart types yang didukung dengan deskripsi.
        
        Returns:
            List chart types dengan metadata
        """
        chart_types = []
        for chart_type, config in CHART_CONFIGS.items():
            chart_types.append({
                "type": chart_type,
                "description": config.get("description", ""),
                "required_params": config.get("required_params", [])
            })
        
        return chart_types
    
    def validate_dataset_compatibility(
        self, 
        chart_type: str, 
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validasi kompatibilitas dataset dengan chart type.
        
        Args:
            chart_type: Jenis chart yang akan dibuat
            dataset_selected: Dataset yang dipilih
            
        Returns:
            Dictionary dengan status validasi
        """
        return self.instruction_builder.validate_chart_requirements(
            chart_type, dataset_selected
        )
    
    def preview_chart_config(
        self, 
        user_prompt: str, 
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Preview konfigurasi chart tanpa membuat chart actual.
        
        Args:
            user_prompt: Prompt dari user
            dataset_selected: Dataset yang dipilih
            
        Returns:
            Preview konfigurasi chart
        """
        try:
            # Build instruksi
            messages = self.instruction_builder.build_complete_instruction(
                user_prompt, dataset_selected
            )
            
            # Generate config via AI (sync untuk preview)
            ai_response = self.model_client.generate_json(
                messages=messages,
                temperature=0.1,
                max_tokens=2000
            )
            
            if "error" in ai_response:
                return {"error": ai_response["error"]}
            
            # Validate response
            chart_config = self.chart_validator.validate_ai_response(ai_response, dataset_selected)
            
            return {
                "success": True,
                "preview": chart_config,
                "chart_type": chart_config.get("viz_type"),
                "slice_name": chart_config.get("slice_name")
            }
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            return {"error": str(e)}
    
    def close(self):
        """Clean up resources."""
        if hasattr(self, 'superset_client'):
            self.superset_client.close()
        logger.info("ChartGenerator service closed")