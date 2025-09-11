"""
AI processor module for dataset selection using AI models
"""
import logging
from typing import Dict, List, Any, Optional

from app.services.model_client import get_model_client
from .constants import AI_INSTRUCTION_TEMPLATE

logger = logging.getLogger(__name__)


class AIProcessor:
    """
    Handles AI model processing for dataset selection
    """

    def __init__(self, model_client=None):
        """
        Initialize AIProcessor
        
        Args:
            model_client: Optional model client instance
        """
        self.model_client = model_client or get_model_client()

    def build_ai_instruction(self, datasets_summary: str, user_prompt: str) -> str:
        """
        Build AI instruction for dataset selection
        
        Args:
            datasets_summary: Formatted summary of available datasets
            user_prompt: User's request for dashboard/visualization
            
        Returns:
            Complete instruction for AI model
        """
        instruction = AI_INSTRUCTION_TEMPLATE.format(
            datasets_summary=datasets_summary,
            user_prompt=user_prompt
        )
        
        logger.info("Built AI instruction for dataset selection")
        return instruction

    def process_dataset_selection(self, datasets_summary: str, user_prompt: str) -> Dict[str, Any]:
        """
        Process dataset selection using AI model
        
        Args:
            datasets_summary: Formatted summary of available datasets
            user_prompt: User's request for dashboard/visualization
            
        Returns:
            Dictionary containing AI response and selected datasets
            
        Raises:
            Exception: If AI processing fails
        """
        try:
            # Build instruction for AI model
            instruction = self.build_ai_instruction(datasets_summary, user_prompt)
            
            # Prepare messages for AI model
            messages = [
                {
                    "role": "system",
                    "content": "You are a Superset Dashboard Engineering Assistant. Analyze the available datasets and user requirements to recommend the most suitable datasets."
                },
                {
                    "role": "user", 
                    "content": instruction
                }
            ]
            
            logger.info("Sending request to AI model for dataset selection")
            
            # Generate response from AI model
            response = self.model_client.generate_with_retry(
                messages=messages,
                temperature=0.1,
                max_tokens=500
            )
            
            ai_content = response.get("content", "").strip()
            
            # Parse selected datasets from AI response
            selected_datasets = self._parse_selected_datasets(ai_content)
            
            result = {
                "ai_response": ai_content,
                "selected_datasets": selected_datasets,
                "user_prompt": user_prompt,
                "processing_time_ms": response.get("processing_time_ms", 0),
                "model_info": response.get("model", "unknown")
            }
            
            logger.info(f"AI processed dataset selection: {len(selected_datasets)} datasets selected")
            return result
            
        except Exception as e:
            logger.error(f"AI processing failed: {e}")
            raise Exception(f"Dataset selection AI processing failed: {e}")

    async def process_dataset_selection_async(self, datasets_summary: str, user_prompt: str) -> Dict[str, Any]:
        """
        Process dataset selection using AI model asynchronously
        
        Args:
            datasets_summary: Formatted summary of available datasets
            user_prompt: User's request for dashboard/visualization
            
        Returns:
            Dictionary containing AI response and selected datasets
            
        Raises:
            Exception: If AI processing fails
        """
        try:
            # Build instruction for AI model
            instruction = self.build_ai_instruction(datasets_summary, user_prompt)
            
            # Prepare messages for AI model
            messages = [
                {
                    "role": "system",
                    "content": "You are a Superset Dashboard Engineering Assistant. Analyze the available datasets and user requirements to recommend the most suitable datasets."
                },
                {
                    "role": "user",
                    "content": instruction
                }
            ]
            
            logger.info("Sending async request to AI model for dataset selection")
            
            # Generate response from AI model asynchronously
            # logger.info(f'messages : {messages}')
            response = await self.model_client.generate_with_retry_async(
                messages=messages,
                temperature=0.1,
                max_tokens=500
            )
            logger.info(f'response : {response}')
            
            ai_content = response.get("content", "").strip()
            
            # Parse selected datasets from AI response
            selected_datasets = self._parse_selected_datasets(ai_content)
            
            result = {
                "ai_response": ai_content,
                "selected_datasets": selected_datasets,
                "user_prompt": user_prompt,
                "processing_time_ms": response.get("processing_time_ms", 0),
                "model_info": response.get("model", "unknown")
            }
            
            logger.info(f"AI processed dataset selection (async): {len(selected_datasets)} datasets selected")
            return result
            
        except Exception as e:
            logger.error(f"AI processing failed (async): {e}")
            raise Exception(f"Dataset selection AI processing failed: {e}")

    def _parse_selected_datasets(self, ai_response: str) -> List[str]:
        """
        Parse selected datasets from AI response
        
        Args:
            ai_response: Raw response from AI model
            
        Returns:
            List of selected dataset names
        """
        try:
            # Remove any markdown formatting and extra whitespace
            cleaned_response = ai_response.strip()
            
            # Remove common markdown elements
            cleaned_response = cleaned_response.replace("**", "")
            cleaned_response = cleaned_response.replace("*", "")
            
            # Split into lines and process
            lines = cleaned_response.split('\n')
            
            # Look for lines that contain dataset names (exclude headers and explanations)
            dataset_candidates = []
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines, headers, and analysis sections
                if not line or line.startswith(('SELECTED DATASET', 'Analysis:', 'Key Terms:', 'Description Match:', 'Column Verification:', 'Visualization Suitability:', 'Purpose Alignment:', 'The other datasets')):
                    continue
                
                # Skip numbered list items
                if line.startswith(tuple(f"{i}." for i in range(1, 10))):
                    continue
                
                # Extract dataset name from parentheses format like "sav_trn_accounts(Saving/Simpanan Dataset)"
                if '(' in line and ')' in line:
                    dataset_name = line.split('(')[0].strip()
                    if dataset_name and not any(skip_word in dataset_name.lower() for skip_word in ['analysis', 'terms', 'match', 'verification', 'suitability', 'alignment', 'other']):
                        dataset_candidates.append(dataset_name)
                # Also handle simple comma-separated format
                elif ',' in line and not any(skip_word in line.lower() for skip_word in ['analysis', 'terms', 'match', 'verification', 'suitability', 'alignment', 'other']):
                    for dataset in line.split(','):
                        dataset = dataset.strip()
                        if dataset and not any(skip_word in dataset.lower() for skip_word in ['analysis', 'terms', 'match', 'verification', 'suitability', 'alignment', 'other']):
                            dataset_candidates.append(dataset)
                # Handle single dataset name
                elif line and not any(skip_word in line.lower() for skip_word in ['analysis', 'terms', 'match', 'verification', 'suitability', 'alignment', 'other', 'the ', 'or ', 'various']):
                    dataset_candidates.append(line)
            
            # Clean up and deduplicate
            cleaned_datasets = []
            for dataset in dataset_candidates:
                # Further cleanup
                dataset = dataset.strip().strip('.,!?')
                if dataset and len(dataset) > 2:  # Avoid single characters
                    cleaned_datasets.append(dataset)
            
            # Remove duplicates while preserving order
            unique_datasets = []
            for dataset in cleaned_datasets:
                if dataset not in unique_datasets:
                    unique_datasets.append(dataset)
            
            logger.info(f"Parsed {len(unique_datasets)} datasets from AI response: {unique_datasets}")
            return unique_datasets
            
        except Exception as e:
            logger.warning(f"Failed to parse AI response for datasets: {e}")
            return []

    def validate_selected_datasets(self, selected_datasets: List[str], available_datasets: List[Dict[str, Any]]) -> List[str]:
        """
        Validate that selected datasets exist in available datasets
        
        Args:
            selected_datasets: List of dataset names selected by AI
            available_datasets: List of available dataset summaries
            
        Returns:
            List of validated dataset names that exist
        """
        available_names = {dataset.get('name', '').lower() for dataset in available_datasets}
        validated = []
        
        for dataset_name in selected_datasets:

            print(f'selected dataset name : {dataset_name}')

            if dataset_name.lower() in available_names:
                validated.append(dataset_name)
            else:
                logger.warning(f"Selected dataset '{dataset_name}' not found in available datasets")
        
        logger.info(f"Validated {len(validated)} out of {len(selected_datasets)} selected datasets")
        return validated