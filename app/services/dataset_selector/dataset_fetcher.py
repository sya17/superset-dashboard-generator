"""
Dataset fetcher module for retrieving and processing Superset datasets
"""
import logging
from typing import Dict, List, Any, Optional

from app.services.superset.client import SupersetClient
from app.services.superset.exceptions import SupersetClientError
from .cache_manager import DatasetCacheManager

logger = logging.getLogger(__name__)


class DatasetFetcher:
    """
    Handles fetching and processing datasets from Superset API
    """

    def __init__(self, superset_client: Optional[SupersetClient] = None, 
                 use_cache: bool = True, cache_duration_hours: int = 24):
        """
        Initialize DatasetFetcher
        
        Args:
            superset_client: Optional SupersetClient instance
            use_cache: Whether to use caching for dataset summaries
            cache_duration_hours: Cache validity duration in hours
        """
        self.superset_client = superset_client or SupersetClient()
        self.use_cache = use_cache
        self.cache_manager = DatasetCacheManager(cache_duration_hours=cache_duration_hours) if use_cache else None

    def get_datasets(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve datasets from Superset API
        
        Args:
            params: Optional query parameters for filtering
            
        Returns:
            Dictionary containing datasets response
            
        Raises:
            SupersetClientError: If API request fails
        """
        try:
            logger.info("Fetching datasets from Superset API")
            
            # Set default params to get all datasets
            if params is None:
                params = {}
            
            # Add page size parameter to get more datasets (default is usually 20)
            # Note: Some Superset installations may have max page_size limits
            if 'page_size' not in params:
                params['page_size'] = 100  # Use reasonable page size that most Superset configs accept
            
            response = self.superset_client.get_datasets(params=params)
            
            if not response or 'result' not in response:
                raise SupersetClientError("Invalid response format from datasets API")
                
            datasets = response.get('result', [])
            total_count = response.get('count', len(datasets))
            
            # Deduplicate datasets based on ID (in case API returns duplicates)
            unique_datasets = []
            seen_ids = set()
            duplicates_found = 0
            
            for dataset in datasets:
                dataset_id = dataset.get('id')
                if dataset_id and dataset_id not in seen_ids:
                    seen_ids.add(dataset_id)
                    unique_datasets.append(dataset)
                elif dataset_id:
                    duplicates_found += 1
            
            if duplicates_found > 0:
                logger.warning(f"Found {duplicates_found} duplicate datasets in API response")
                # Update response with deduplicated data
                response['result'] = unique_datasets
            
            logger.info(f"Successfully fetched {len(unique_datasets)} unique datasets out of {total_count} total")
            
            # If there are more datasets than what we got, log a warning
            if len(unique_datasets) < total_count:
                logger.warning(f"Only fetched {len(unique_datasets)} out of {total_count} total datasets. Consider using get_all_datasets() for complete data.")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to fetch datasets: {e}")
            raise SupersetClientError(f"Dataset fetch failed: {e}")

    def get_dataset_details(self, dataset_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific dataset
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            Dictionary containing dataset details
            
        Raises:
            SupersetClientError: If API request fails
        """
        try:
            logger.info(f"Fetching details for dataset ID: {dataset_id}")
            response = self.superset_client.get_dataset(dataset_id)
            
            if not response or 'result' not in response:
                raise SupersetClientError(f"Invalid response format for dataset {dataset_id}")
                
            logger.info(f"Successfully fetched details for dataset {dataset_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to fetch dataset {dataset_id}: {e}")
            raise SupersetClientError(f"Dataset details fetch failed: {e}")

    def build_dataset_summary(self, datasets: List[Dict[str, Any]], fetch_columns: bool = True) -> List[Dict[str, Any]]:
        """
        Build summary information for datasets suitable for AI processing
        
        Args:
            datasets: List of dataset dictionaries from API
            fetch_columns: Whether to fetch detailed column information by calling get_dataset(id)
            
        Returns:
            List of simplified dataset summaries
        """
        summaries = []
        
        for dataset in datasets:
            try:
                dataset_id = dataset.get('id')
                
                # Basic dataset info
                summary = {
                    'name': dataset.get('table_name', 'Unknown'),
                    'id': dataset_id,
                    'database': dataset.get('database', {}).get('database_name', 'Unknown'),
                    'schema': dataset.get('schema', ''),
                    'description': dataset.get('description', ''),
                    'is_managed_externally': dataset.get('is_managed_externally', False),
                    'columns': []
                }
                
                # Fetch detailed columns if requested and dataset_id exists
                if fetch_columns and dataset_id:
                    try:
                        logger.info(f"Fetching detailed columns for dataset {dataset_id}: {summary['name']}")
                        detail_response = self.get_dataset_details(dataset_id)
                        detailed_dataset = detail_response.get('result', {})
                        summary['columns'] = self._extract_column_info(detailed_dataset)
                        
                        # Also update description from detailed response if available
                        if detailed_dataset.get('description'):
                            summary['description'] = detailed_dataset.get('description', summary['description'])
                            
                    except Exception as e:
                        logger.warning(f"Failed to fetch detailed columns for dataset {dataset_id}: {e}")
                        # Fallback to basic column extraction from list response
                        summary['columns'] = self._extract_column_info(dataset)
                else:
                    # Use basic column extraction from list response
                    summary['columns'] = self._extract_column_info(dataset)
                
                summaries.append(summary)
                
            except Exception as e:
                logger.warning(f"Failed to process dataset {dataset.get('id', 'unknown')}: {e}")
                continue
                
        logger.info(f"Built summaries for {len(summaries)} datasets (with detailed columns: {fetch_columns})")
        return summaries

    def _extract_column_info(self, dataset: Dict[str, Any]) -> List[str]:
        """
        Extract column information from dataset
        
        Args:
            dataset: Dataset dictionary from API (can be from list or detailed response)
            
        Returns:
            List of column names/descriptions
        """
        columns = []
        
        # Try to get columns from different possible locations in the response
        if 'columns' in dataset:
            for column in dataset['columns']:
                if isinstance(column, dict):
                    # Try different possible column name fields
                    col_name = column.get('column_name') or column.get('name') or column.get('id')
                    if col_name:
                        # Add type information if available
                        col_type = column.get('type') or column.get('type_generic')
                        if col_type:
                            columns.append(f"{col_name}({col_type})")
                        else:
                            columns.append(col_name)
                elif isinstance(column, str):
                    columns.append(column)
        
        # Also try 'table_columns' field which might be in detailed response
        if not columns and 'table_columns' in dataset:
            for column in dataset['table_columns']:
                if isinstance(column, dict):
                    col_name = column.get('column_name') or column.get('name')
                    if col_name:
                        col_type = column.get('type') or column.get('type_generic')
                        if col_type:
                            columns.append(f"{col_name}({col_type})")
                        else:
                            columns.append(col_name)
        
        # Add metrics as supplementary information
        if 'metrics' in dataset:
            for metric in dataset['metrics']:
                if isinstance(metric, dict):
                    metric_name = metric.get('metric_name') or metric.get('name')
                    if metric_name:
                        columns.append(f"metric_{metric_name}")
                elif isinstance(metric, str):
                    columns.append(f"metric_{metric}")
        
        # If still no columns found, log for debugging
        if not columns:
            logger.warning(f"No columns found for dataset. Available keys: {list(dataset.keys())}")
            
        return columns[:15]  # Increased limit for detailed columns

    def format_for_ai(self, dataset_summaries: List[Dict[str, Any]]) -> str:
        """
        Format dataset summaries for AI model consumption
        
        Args:
            dataset_summaries: List of dataset summary dictionaries
            
        Returns:
            Formatted string for AI processing following the format:
            nama_dataset: [column1, column2, column3]
        """
        formatted_lines = []
        
        for summary in dataset_summaries:
            name = summary.get('name', 'Unknown')
            columns = summary.get('columns', [])
            database = summary.get('database', '')
            description = summary.get('description', '')
            
            # Format columns as array-like list
            if columns:
                # Use first 8 columns for readability
                display_columns = columns[:8]
                columns_str = ", ".join(display_columns)
                if len(columns) > 8:
                    columns_str += f", +{len(columns) - 8}_more"
                columns_formatted = f"[{columns_str}]"
            else:
                columns_formatted = "[no_columns_available]"
                
            # Build formatted line: nama_dataset(description): [column1, column2, column3]
            if description:
                desc_clean = description.replace('\n', ' ').replace('\r', ' ').strip()
                if len(desc_clean) > 80:
                    desc_clean = desc_clean[:80] + "..."
                line = f"{name}({desc_clean}): {columns_formatted}"
            else:
                line = f"{name}(no description): {columns_formatted}"
            
            # Add database info separately if needed
            if database and database != 'Unknown':
                line += f" [DB:{database}]"
                
            formatted_lines.append(line)
            
        return "\n".join(formatted_lines)

    def get_dataset_summaries_with_cache(self, params: Optional[Dict[str, Any]] = None, 
                                       fetch_columns: bool = True, 
                                       force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get dataset summaries with caching support
        
        Args:
            params: Optional query parameters for filtering
            fetch_columns: Whether to fetch detailed column information
            force_refresh: If True, skip cache and fetch fresh data
            
        Returns:
            Dictionary containing:
            - summaries: List of dataset summaries
            - formatted_summaries: Formatted string for AI
            - from_cache: Boolean indicating if data came from cache
            - total_datasets: Number of datasets
        """
        try:
            # Try to get from cache first (unless force refresh)
            if not force_refresh and self.use_cache and self.cache_manager:
                cached_data = self.cache_manager.get_cached_summaries(params, fetch_columns)
                if cached_data:
                    logger.info("Using cached dataset summaries")
                    cached_data['from_cache'] = True
                    return cached_data
            
            # Cache miss - fetch fresh data
            logger.info("Cache miss - fetching fresh dataset summaries")
            
            # Fetch datasets
            if params and ('page_size' in params or 'page' in params):
                datasets_response = self.get_datasets(params=params)
            else:
                datasets_response = self.get_all_datasets()
            
            datasets = datasets_response.get('result', [])
            
            if not datasets:
                return {
                    'summaries': [],
                    'formatted_summaries': '',
                    'from_cache': False,
                    'total_datasets': 0
                }
            
            # Build summaries
            summaries = self.build_dataset_summary(datasets, fetch_columns=fetch_columns)
            
            # Format for AI
            formatted_summaries = self.format_for_ai(summaries)
            
            result = {
                'summaries': summaries,
                'formatted_summaries': formatted_summaries,
                'from_cache': False,
                'total_datasets': len(summaries)
            }
            
            # Save to cache
            if self.use_cache and self.cache_manager:
                self.cache_manager.save_summaries_to_cache(
                    summaries=summaries,
                    formatted_summaries=formatted_summaries,
                    params=params,
                    fetch_columns=fetch_columns
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get dataset summaries: {e}")
            raise SupersetClientError(f"Dataset summaries fetch failed: {e}")

    def clear_cache(self, cache_key: Optional[str] = None) -> None:
        """
        Clear dataset cache
        
        Args:
            cache_key: Specific cache key to clear, if None clears all
        """
        if self.cache_manager:
            self.cache_manager.clear_cache(cache_key)
        else:
            logger.warning("Cache manager not available")

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache information
        
        Returns:
            Cache information dictionary
        """
        if self.cache_manager:
            return self.cache_manager.get_cache_info()
        else:
            return {'cache_enabled': False}

    def get_all_datasets(self, max_datasets: int = 10000) -> Dict[str, Any]:
        """
        Get all datasets using pagination if necessary with deduplication
        
        Args:
            max_datasets: Maximum number of datasets to fetch
            
        Returns:
            Dictionary containing all unique datasets
        """
        try:
            logger.info("Fetching all datasets with pagination and deduplication")
            
            all_datasets = []
            seen_ids = set()  # Track dataset IDs to avoid duplicates
            page = 0
            page_size = 20  # Use Superset's default page size to avoid limits
            total_count = 0
            consecutive_empty_pages = 0
            max_empty_pages = 3  # Stop after 3 consecutive empty pages
            
            while len(all_datasets) < max_datasets and consecutive_empty_pages < max_empty_pages:
                params = {
                    "order_column": "table_name",
                    "order_direction": "asc",
                    'page': page,
                    'page_size': page_size
                }
                
                logger.info(f"Fetching page {page} with page_size {page_size}")
                response = self.superset_client.get_datasets(params=params)
                datasets = response.get('result', [])
                
                # Get total count from first response
                if page == 0:
                    total_count = response.get('count', 0)
                    logger.info(f"Total datasets available: {total_count}")
                
                if not datasets:
                    consecutive_empty_pages += 1
                    logger.info(f"No datasets found on page {page} (empty page {consecutive_empty_pages}/{max_empty_pages})")
                    page += 1
                    continue
                else:
                    consecutive_empty_pages = 0  # Reset counter when we find data
                
                # Deduplicate datasets based on ID
                new_datasets = []
                duplicates_found = 0
                
                for dataset in datasets:
                    dataset_id = dataset.get('id')
                    if dataset_id and dataset_id not in seen_ids:
                        seen_ids.add(dataset_id)
                        new_datasets.append(dataset)
                    elif dataset_id:
                        duplicates_found += 1
                        logger.debug(f"Duplicate dataset found: ID {dataset_id}, name: {dataset.get('table_name', 'Unknown')}")
                
                all_datasets.extend(new_datasets)
                
                log_msg = f"Page {page}: Found {len(datasets)} datasets, {len(new_datasets)} new, {duplicates_found} duplicates. Total unique: {len(all_datasets)}"
                logger.info(log_msg)
                
                page += 1
                
                # Stop if we got fewer NEW results than expected (accounting for duplicates)
                if len(new_datasets) == 0 and len(datasets) > 0:
                    logger.info(f"All datasets on page {page-1} were duplicates, likely reached end")
                    break
                    
                # Stop if we got fewer results than page_size (last page)
                if len(datasets) < page_size:
                    logger.info(f"Last page reached (got {len(datasets)} < {page_size})")
                    break
                    
                # Safety check: if we have more unique datasets than total count, something is wrong
                if total_count > 0 and len(all_datasets) >= total_count:
                    logger.info(f"Reached expected total count: {len(all_datasets)} >= {total_count}")
                    break
            
            # Final validation
            final_seen_ids = set()
            unique_datasets = []
            for dataset in all_datasets:
                dataset_id = dataset.get('id')
                if dataset_id and dataset_id not in final_seen_ids:
                    final_seen_ids.add(dataset_id)
                    unique_datasets.append(dataset)
            
            if len(unique_datasets) != len(all_datasets):
                logger.warning(f"Found additional duplicates in final validation: {len(all_datasets)} -> {len(unique_datasets)}")
                all_datasets = unique_datasets
            
            logger.info(f"Fetched total of {len(all_datasets)} unique datasets using pagination (expected {total_count})")
            
            return {
                'result': all_datasets,
                'count': len(all_datasets)
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch all datasets: {e}")
            raise SupersetClientError(f"All datasets fetch failed: {e}")

    def close(self):
        """Clean up resources"""
        if self.superset_client:
            self.superset_client.close()