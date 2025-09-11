"""
Main dataset selector service for Superset dashboard generation
"""
import logging
from typing import Dict, List, Any, Optional

from .dataset_fetcher import DatasetFetcher
from .ai_processor import AIProcessor
from app.services.superset.exceptions import SupersetClientError

logger = logging.getLogger(__name__)


class DatasetSelector:
    """
    Main service for selecting relevant datasets using AI model processing
    
    This service:
    1. Fetches available datasets from Superset
    2. Builds AI instructions for dataset analysis
    3. Processes user prompts with AI to select relevant datasets
    4. Returns accurate and relevant dataset recommendations
    """

    def __init__(self, superset_client=None, model_client=None, use_cache=True, cache_duration_hours=24):
        """
        Initialize DatasetSelector service
        
        Args:
            superset_client: Optional SupersetClient instance
            model_client: Optional model client instance
            use_cache: Whether to use caching for dataset summaries
            cache_duration_hours: Cache validity duration in hours
        """
        self.dataset_fetcher = DatasetFetcher(superset_client, use_cache=use_cache, cache_duration_hours=cache_duration_hours)
        self.ai_processor = AIProcessor(model_client)
        logger.info(f"DatasetSelector service initialized (cache: {use_cache})")

    def select_datasets(self, user_prompt: str, dataset_params: Optional[Dict[str, Any]] = None, fetch_columns: bool = True, include_details: bool = False) -> Dict[str, Any]:
        """
        Select relevant datasets based on user prompt using AI analysis
        
        Args:
            user_prompt: User's request for dashboard/visualization
            dataset_params: Optional parameters for dataset filtering
            fetch_columns: Whether to fetch column information
            include_details: Whether to fetch detailed information for selected datasets
            
        Returns:
            Dictionary containing:
            - selected_datasets: List of recommended dataset names
            - ai_analysis: AI model's reasoning and response
            - available_datasets: Summary of all available datasets
            - processing_info: Metadata about the selection process
            - dataset_details: (if include_details=True) Detailed info for selected datasets
            
        Raises:
            SupersetClientError: If Superset API fails
            Exception: If AI processing fails
        """
        try:
            logger.info(f"Starting dataset selection for user prompt: {user_prompt[:100]}...")
            
            # Step 1: Get dataset summaries (with caching)
            logger.info("Getting dataset summaries (checking cache first)")
            summaries_result = self.dataset_fetcher.get_dataset_summaries_with_cache(
                params=dataset_params, 
                fetch_columns=fetch_columns
            )
            
            dataset_summaries = summaries_result['summaries']
            datasets_formatted = summaries_result['formatted_summaries']
            from_cache = summaries_result['from_cache']
            total_datasets = summaries_result['total_datasets']
            
            if from_cache:
                logger.info(f"Using cached data for {total_datasets} datasets")
            else:
                logger.info(f"Fetched fresh data for {total_datasets} datasets")
            
            if not dataset_summaries:
                logger.warning("No datasets found")
                return {
                    "selected_datasets": [],
                    "ai_analysis": "No datasets available in Superset",
                    "available_datasets": [],
                    "processing_info": {
                        "status": "no_datasets",
                        "total_datasets": 0,
                        "from_cache": from_cache,
                        "error": "No datasets found"
                    }
                }
            
            # Step 2: Process with AI model
            logger.info("Processing dataset selection with AI model")
            ai_result = self.ai_processor.process_dataset_selection(
                datasets_summary=datasets_formatted,
                user_prompt=user_prompt
            )
            
            # Step 3: Validate selected datasets
            selected_datasets = self.ai_processor.validate_selected_datasets(
                selected_datasets=ai_result.get("selected_datasets", []),
                available_datasets=dataset_summaries
            )
            
            # Step 4: Fetch dataset details if requested
            dataset_details = {}
            if include_details and selected_datasets:
                logger.info(f"Fetching details for {len(selected_datasets)} selected datasets")
                try:
                    dataset_details = self.get_dataset_details(selected_datasets)
                    logger.info(f"Successfully fetched details for {len(dataset_details)} datasets")
                except Exception as e:
                    logger.warning(f"Failed to fetch dataset details: {e}")
                    # Continue without details rather than failing the entire request
                    dataset_details = {}

            # Step 5: Build final result
            result = {
                "selected_datasets": selected_datasets,
                "ai_analysis": {
                    "response": ai_result.get("ai_response", ""),
                    "reasoning": ai_result.get("ai_response", ""),
                    "model_used": ai_result.get("model_info", "unknown"),
                    "processing_time_ms": ai_result.get("processing_time_ms", 0)
                },
                "available_datasets": dataset_summaries,
                "processing_info": {
                    "status": "success",
                    "total_datasets": total_datasets,
                    "selected_count": len(selected_datasets),
                    "from_cache": from_cache,
                    "user_prompt": user_prompt,
                    "details_included": include_details
                }
            }
            
            # Add dataset details if requested and available
            if include_details:
                result["dataset_details"] = dataset_details
            
            logger.info(f"Dataset selection completed: {len(selected_datasets)} datasets selected from {total_datasets} available (from_cache: {from_cache}, details_included: {include_details})")
            return result
            
        except SupersetClientError as e:
            logger.error(f"Superset API error during dataset selection: {e}")
            raise
        except Exception as e:
            logger.error(f"Dataset selection failed: {e}")
            raise Exception(f"Dataset selection process failed: {e}")

    async def select_datasets_async(self, user_prompt: str, dataset_params: Optional[Dict[str, Any]] = None, fetch_columns: bool = True, include_details: bool = False) -> Dict[str, Any]:
        """
        Select relevant datasets asynchronously
        
        Args:
            user_prompt: User's request for dashboard/visualization
            dataset_params: Optional parameters for dataset filtering
            fetch_columns: Whether to fetch column information
            include_details: Whether to fetch detailed information for selected datasets
            
        Returns:
            Dictionary containing selection results. If include_details=True, also includes 'dataset_details' key
            
        Raises:
            SupersetClientError: If Superset API fails
            Exception: If AI processing fails
        """
        try:
            logger.info(f"Starting async dataset selection for user prompt: {user_prompt[:100]}...")
            
            # Step 1: Get dataset summaries (with caching)
            logger.info("Getting dataset summaries (checking cache first)")
            summaries_result = self.dataset_fetcher.get_dataset_summaries_with_cache(
                params=dataset_params, 
                fetch_columns=fetch_columns
            )
            
            dataset_summaries = summaries_result['summaries']
            datasets_formatted = summaries_result['formatted_summaries']
            from_cache = summaries_result['from_cache']
            total_datasets = summaries_result['total_datasets']
            
            if from_cache:
                logger.info(f"Using cached data for {total_datasets} datasets")
            else:
                logger.info(f"Fetched fresh data for {total_datasets} datasets")
            
            if not dataset_summaries:
                logger.warning("No datasets found")
                return {
                    "selected_datasets": [],
                    "ai_analysis": "No datasets available in Superset",
                    "available_datasets": [],
                    "processing_info": {
                        "status": "no_datasets",
                        "total_datasets": 0,
                        "from_cache": from_cache,
                        "error": "No datasets found"
                    }
                }
            
            # Step 4: Process with AI model asynchronously
            logger.info("Processing dataset selection with AI model (async)")
            ai_result = await self.ai_processor.process_dataset_selection_async(
                datasets_summary=datasets_formatted,
                user_prompt=user_prompt
            )
            
            # Step 5: Validate selected datasets
            selected_datasets = self.ai_processor.validate_selected_datasets(
                selected_datasets=ai_result.get("selected_datasets", []),
                available_datasets=dataset_summaries
            )
            
            # Step 6: Fetch dataset details if requested
            dataset_details = {}
            if include_details and selected_datasets:
                logger.info(f"Fetching details for {len(selected_datasets)} selected datasets")
                try:
                    dataset_details = self.get_dataset_details(selected_datasets)
                    logger.info(f"Successfully fetched details for {len(dataset_details)} datasets")
                except Exception as e:
                    logger.warning(f"Failed to fetch dataset details: {e}")
                    # Continue without details rather than failing the entire request
                    dataset_details = {}

            # Step 7: Build final result
            result = {
                "selected_datasets": selected_datasets,
                "ai_analysis": {
                    "response": ai_result.get("ai_response", ""),
                    "reasoning": ai_result.get("ai_response", ""),
                    "model_used": ai_result.get("model_info", "unknown"),
                    "processing_time_ms": ai_result.get("processing_time_ms", 0)
                },
                "available_datasets": dataset_summaries,
                "processing_info": {
                    "status": "success",
                    "total_datasets": total_datasets,
                    "selected_count": len(selected_datasets),
                    "from_cache": from_cache,
                    "user_prompt": user_prompt,
                    "details_included": include_details
                }
            }
            
            # Add dataset details if requested and available
            if include_details:
                result["dataset_details"] = dataset_details
            
            logger.info(f"Async dataset selection completed: {len(selected_datasets)} datasets selected from {total_datasets} available (from_cache: {from_cache}, details_included: {include_details})")
            return result
            
        except SupersetClientError as e:
            logger.error(f"Superset API error during async dataset selection: {e}")
            raise
        except Exception as e:
            logger.error(f"Async dataset selection failed: {e}")
            raise Exception(f"Async dataset selection process failed: {e}")

    def get_dataset_details(self, dataset_names: List[str]) -> Dict[str, Any]:
        """
        Get detailed information for selected datasets
        
        Args:
            dataset_names: List of dataset names to get details for
            
        Returns:
            Dictionary mapping dataset names to their detailed information
        """
        try:
            logger.info(f"Fetching details for {len(dataset_names)} datasets")
            
            # First get all datasets to find IDs
            datasets_response = self.dataset_fetcher.get_datasets()
            datasets = datasets_response.get('result', [])
            
            # Create mapping of names to IDs
            name_to_id = {}
            for dataset in datasets:
                name = dataset.get('table_name', '')
                if name in dataset_names:
                    name_to_id[name] = dataset.get('id')
            
            # Fetch details for each dataset
            details = {}
            for name, dataset_id in name_to_id.items():
                if dataset_id:
                    try:
                        detail_response = self.dataset_fetcher.get_dataset_details(dataset_id)
                        details[name] = detail_response.get('result', {})
                    except Exception as e:
                        logger.warning(f"Failed to fetch details for dataset {name}: {e}")
                        details[name] = {"error": str(e)}
            
            logger.info(f"Fetched details for {len(details)} datasets")
            return details
            
        except Exception as e:
            logger.error(f"Failed to get dataset details: {e}")
            raise Exception(f"Dataset details fetch failed: {e}")

    def clear_cache(self, cache_key: Optional[str] = None) -> None:
        """
        Clear dataset cache
        
        Args:
            cache_key: Specific cache key to clear, if None clears all
        """
        self.dataset_fetcher.clear_cache(cache_key)

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache information
        
        Returns:
            Cache information dictionary
        """
        return self.dataset_fetcher.get_cache_info()

    def close(self):
        """Clean up resources"""
        self.dataset_fetcher.close()
        logger.info("DatasetSelector service closed")