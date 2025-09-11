"""
AI Instruction Builder
Membangun instruksi untuk AI model dalam menggenerate konfigurasi chart.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from .constants import (
    AI_INSTRUCTIONS_TEMPLATE, 
    CHART_TYPES, 
    CHART_TYPE_KEYWORDS,
    CHART_CONFIGS
)

logger = logging.getLogger(__name__)


class InstructionBuilder:
    """
    Builder untuk membuat instruksi AI yang tepat berdasarkan user prompt dan dataset.
    """
    
    def __init__(self):
        self.chart_types = CHART_TYPES
        self.chart_configs = CHART_CONFIGS
        self.keyword_mapping = CHART_TYPE_KEYWORDS
        
    # Removed detect_chart_type_from_prompt - AI model will determine chart type
    
    def extract_dataset_info(self, dataset_selected: Dict[str, Any]) -> str:
        """
        Ekstrak informasi dataset untuk instruksi AI.
        
        Args:
            dataset_selected: Dataset yang dipilih dari dataset_selector
            
        Returns:
            String informasi dataset yang terformat
        """
        try:
            dataset_name = dataset_selected.get('table_name', 'Unknown')
            columns = dataset_selected.get('columns', [])
            database_name = dataset_selected.get('database', {}).get('database_name', 'Unknown')
            
            # Format kolom dengan tipe data
            columns_info = []
            for col in columns:
                col_name = col.get('column_name', 'unknown')
                col_type = col.get('type', 'unknown')
                col_desc = col.get('description', '')
                
                if col_desc:
                    columns_info.append(f"- {col_name} ({col_type}): {col_desc}")
                else:
                    columns_info.append(f"- {col_name} ({col_type})")
            
            dataset_info = f"""
Dataset: {dataset_name}
Database: {database_name}
Columns:
{chr(10).join(columns_info)}

Dataset ID: {dataset_selected.get('id')}
Total Columns: {len(columns)}
"""
            
            return dataset_info.strip()
            
        except Exception as e:
            logger.error(f"Error extracting dataset info: {e}")
            return f"Dataset: {dataset_selected.get('table_name', 'Unknown')}\nError extracting detailed info: {str(e)}"
    
    def build_system_instruction(self) -> str:
        """
        Build system instruction untuk AI model.
        
        Returns:
            System instruction yang lengkap
        """
        return AI_INSTRUCTIONS_TEMPLATE["system_role"]
    
    def build_user_prompt(self, user_prompt: str, dataset_selected: Dict[str, Any]) -> str:
        """
        Build user prompt lengkap untuk AI model.
        
        Args:
            user_prompt: Prompt asli dari user
            dataset_selected: Dataset yang dipilih
            
        Returns:
            User prompt yang lengkap dengan context dataset
        """
        dataset_info = self.extract_dataset_info(dataset_selected)
        available_chart_types = ", ".join(self.chart_types)
        
        formatted_prompt = AI_INSTRUCTIONS_TEMPLATE["user_prompt_template"].format(
            dataset_info=dataset_info,
            user_prompt=user_prompt,
            available_chart_types=available_chart_types
        )
        
        return formatted_prompt
    
    def build_complete_instruction(
        self, 
        user_prompt: str, 
        dataset_selected: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Build instruksi lengkap untuk AI model dalam format messages.
        
        Args:
            user_prompt: Prompt dari user
            dataset_selected: Dataset yang dipilih
            
        Returns:
            List of messages untuk AI model
        """
        # Build system instruction tanpa deteksi chart type - biarkan AI menentukan
        system_instruction = self.build_system_instruction()
        
        # Build user prompt
        formatted_user_prompt = self.build_user_prompt(user_prompt, dataset_selected)
        
        # Format messages
        messages = [
            {
                "role": "system",
                "content": system_instruction
            },
            {
                "role": "user", 
                "content": formatted_user_prompt
            }
        ]
        
        logger.info("Built instruction for AI model - chart type will be determined by AI")
        return messages
    
    def add_chart_examples(self, chart_type: str) -> str:
        """
        Tambahkan contoh konfigurasi untuk chart type tertentu.
        
        Args:
            chart_type: Jenis chart
            
        Returns:
            String contoh konfigurasi
        """
        if chart_type not in self.chart_configs:
            return ""
        
        config = self.chart_configs[chart_type]
        example = {
            "viz_type": chart_type,
            "slice_name": f"Example {chart_type.title().replace('_', ' ')} Chart",
            "params": json.dumps(config["default_params"])
        }
        
        return f"\nContoh konfigurasi untuk {chart_type}:\n{json.dumps(example, indent=2)}"
    
    def validate_chart_requirements(
        self, 
        chart_type: str, 
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validasi apakah dataset memiliki kolom yang diperlukan untuk chart type.
        
        Args:
            chart_type: Jenis chart
            dataset_selected: Dataset yang dipilih
            
        Returns:
            Dictionary dengan status validasi dan saran
        """
        if chart_type not in self.chart_configs:
            return {
                "valid": False,
                "message": f"Chart type {chart_type} not supported"
            }
        
        config = self.chart_configs[chart_type]
        required_params = config.get("required_params", [])
        columns = dataset_selected.get("columns", [])
        column_names = [col.get("column_name") for col in columns]
        
        suggestions = {
            "groupby": [col for col in column_names if any(t in str(col).lower() for t in ["string", "varchar", "text"])],
            "metric": [col for col in column_names if any(t in str(col).lower() for t in ["int", "float", "decimal", "number"])],
            "x_axis": column_names,
            "metrics": [col for col in column_names if any(t in str(col).lower() for t in ["int", "float", "decimal", "number"])]
        }
        
        return {
            "valid": True,
            "required_params": required_params,
            "suggestions": suggestions,
            "message": f"Chart type {chart_type} compatible with dataset"
        }