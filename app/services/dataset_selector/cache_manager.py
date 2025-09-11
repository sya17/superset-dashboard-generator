"""
Cache manager for dataset summaries to improve performance
"""
import json
import os
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


class DatasetCacheManager:
    """
    Manages caching of dataset summaries to avoid repeated API calls
    """

    def __init__(self, cache_dir: str = "cache", cache_duration_hours: int = 24):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory to store cache files
            cache_duration_hours: Cache validity duration in hours
        """
        self.cache_dir = cache_dir
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache_file = os.path.join(cache_dir, "dataset_summaries.json")
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        logger.info(f"Cache manager initialized: {self.cache_file}, duration: {cache_duration_hours}h")

    def _generate_cache_key(self, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate cache key based on parameters
        
        Args:
            params: Parameters used for dataset fetching
            
        Returns:
            Cache key string
        """
        if params:
            # Create hash from sorted params to ensure consistency
            params_str = json.dumps(params, sort_keys=True)
            return hashlib.md5(params_str.encode()).hexdigest()
        return "default"

    def get_cached_summaries(self, params: Optional[Dict[str, Any]] = None, 
                           fetch_columns: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get cached dataset summaries if available and valid
        
        Args:
            params: Parameters used for dataset fetching
            fetch_columns: Whether detailed columns were fetched
            
        Returns:
            Cached data if valid, None otherwise
        """
        try:
            if not os.path.exists(self.cache_file):
                logger.info("No cache file found")
                return None
                
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cache_key = self._generate_cache_key(params)
            
            # Check if cache key exists
            if cache_key not in cache_data:
                logger.info(f"Cache key {cache_key} not found")
                return None
            
            cached_entry = cache_data[cache_key]
            
            # Check cache validity
            cache_time = datetime.fromisoformat(cached_entry['timestamp'])
            if datetime.now() - cache_time > self.cache_duration:
                logger.info(f"Cache expired for key {cache_key}")
                return None
            
            # Check if fetch_columns setting matches
            if cached_entry.get('fetch_columns', True) != fetch_columns:
                logger.info(f"Cache fetch_columns setting mismatch: cached={cached_entry.get('fetch_columns')}, requested={fetch_columns}")
                return None
            
            logger.info(f"Cache hit for key {cache_key}, age: {datetime.now() - cache_time}")
            return cached_entry['data']
            
        except Exception as e:
            logger.warning(f"Failed to read cache: {e}")
            return None

    def save_summaries_to_cache(self, summaries: List[Dict[str, Any]], 
                               formatted_summaries: str,
                               params: Optional[Dict[str, Any]] = None,
                               fetch_columns: bool = True) -> None:
        """
        Save dataset summaries to cache
        
        Args:
            summaries: List of dataset summary dictionaries
            formatted_summaries: Formatted string for AI
            params: Parameters used for dataset fetching
            fetch_columns: Whether detailed columns were fetched
        """
        try:
            cache_key = self._generate_cache_key(params)
            
            # Load existing cache or create new
            cache_data = {}
            if os.path.exists(self.cache_file):
                try:
                    with open(self.cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load existing cache, creating new: {e}")
                    cache_data = {}
            
            # Prepare cache entry
            cache_entry = {
                'timestamp': datetime.now().isoformat(),
                'fetch_columns': fetch_columns,
                'params': params,
                'data': {
                    'summaries': summaries,
                    'formatted_summaries': formatted_summaries,
                    'total_datasets': len(summaries)
                }
            }
            
            # Save to cache
            cache_data[cache_key] = cache_entry
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(summaries)} dataset summaries to cache with key {cache_key}")
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def clear_cache(self, cache_key: Optional[str] = None) -> None:
        """
        Clear cache - either specific key or all
        
        Args:
            cache_key: Specific key to clear, if None clears all
        """
        try:
            if cache_key:
                # Clear specific key
                if os.path.exists(self.cache_file):
                    with open(self.cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    if cache_key in cache_data:
                        del cache_data[cache_key]
                        
                        with open(self.cache_file, 'w', encoding='utf-8') as f:
                            json.dump(cache_data, f, indent=2, ensure_ascii=False)
                        
                        logger.info(f"Cleared cache key: {cache_key}")
                    else:
                        logger.info(f"Cache key {cache_key} not found")
            else:
                # Clear all cache
                if os.path.exists(self.cache_file):
                    os.remove(self.cache_file)
                    logger.info("Cleared all cache")
                    
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache information
        
        Returns:
            Cache info dictionary
        """
        info = {
            'cache_file': self.cache_file,
            'cache_exists': os.path.exists(self.cache_file),
            'cache_duration_hours': self.cache_duration.total_seconds() / 3600,
            'entries': []
        }
        
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                for key, entry in cache_data.items():
                    cache_time = datetime.fromisoformat(entry['timestamp'])
                    age = datetime.now() - cache_time
                    is_valid = age <= self.cache_duration
                    
                    info['entries'].append({
                        'key': key,
                        'timestamp': entry['timestamp'],
                        'age_hours': age.total_seconds() / 3600,
                        'is_valid': is_valid,
                        'fetch_columns': entry.get('fetch_columns', True),
                        'total_datasets': entry.get('data', {}).get('total_datasets', 0)
                    })
                    
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            
        return info

    def cleanup_expired_cache(self) -> None:
        """
        Remove expired cache entries
        """
        try:
            if not os.path.exists(self.cache_file):
                return
                
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            expired_keys = []
            for key, entry in cache_data.items():
                cache_time = datetime.fromisoformat(entry['timestamp'])
                if datetime.now() - cache_time > self.cache_duration:
                    expired_keys.append(key)
            
            # Remove expired entries
            for key in expired_keys:
                del cache_data[key]
            
            if expired_keys:
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            else:
                logger.info("No expired cache entries found")
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired cache: {e}")