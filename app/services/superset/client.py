"""
Superset API client for managing datasets, charts, and dashboards.
"""
import json
from typing import Dict, List, Any, Optional
import logging

from app.core.config import settings

from .http.session_manager import SessionManager
from .http.request_handler import RequestHandler
from .constants import DEFAULT_CHART_QUERY_PARAMS
from .exceptions import SupersetClientError

logger = logging.getLogger(__name__)


class SupersetClient:
    """
    Client for interacting with Apache Superset API.

    Provides methods to manage datasets, charts, and dashboards
    with automatic authentication, CSRF handling, and retry logic.
    """

    def __init__(self):
        """Initialize the Superset client with configuration from settings."""
        self.base_url = settings.SUPERSET_URL
        self.username = settings.SUPERSET_API_USER
        self.password = settings.SUPERSET_API_PASS

        # Initialize components
        self.session_manager = SessionManager()
        self.request_handler = RequestHandler(
            self.session_manager,
            self.base_url,
            self.username,
            self.password
        )

        logger.info("Superset client initialized")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint without /api/v1 prefix
            params: Query parameters
            json_data: JSON payload for POST/PUT requests

        Returns:
            JSON response from the API
        """
        try:
            return self.request_handler.request(
                method=method,
                endpoint=endpoint,
                params=params,
                json_data=json_data
            )
        except Exception as e:
            logger.error(f"Request failed: {method} {endpoint} - {e}")
            raise SupersetClientError(f"API request failed: {e}")

    # Database operations
    def get_databases(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve all databases.

        Args:
            params: Optional query parameters for filtering

        Returns:
            Dictionary containing databases list
        """
        return self._make_request("GET", "database", params=params)

    def get_database(self, database_id: int) -> Dict[str, Any]:
        """
        Retrieve a specific database by ID.

        Args:
            database_id: The database ID

        Returns:
            Dictionary containing database details
        """
        return self._make_request("GET", f"database/{database_id}")

    # Dataset operations
    def get_datasets(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve all datasets.

        Args:
            params: Optional query parameters for filtering

        Returns:
            Dictionary containing datasets list
        """
        return self._make_request("GET", "dataset", params=params)

    def get_dataset(self, dataset_id: int) -> Dict[str, Any]:
        """
        Retrieve a specific dataset by ID.

        Args:
            dataset_id: The dataset ID

        Returns:
            Dictionary containing dataset details
        """
        return self._make_request("GET", f"dataset/{dataset_id}")

    # Chart operations
    def get_charts(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve all charts.

        Args:
            params: Optional query parameters for filtering

        Returns:
            Dictionary containing charts list
        """
        return self._make_request("GET", "chart", params=params)

    def get_chart(self, chart_id: int) -> Dict[str, Any]:
        """
        Retrieve a specific chart by ID.

        Args:
            chart_id: The chart ID

        Returns:
            Dictionary containing chart details
        """
        query_params = DEFAULT_CHART_QUERY_PARAMS.copy()
        api_params = {"q": json.dumps(query_params)}
        return self._make_request("GET", f"chart/{chart_id}", params=api_params)

    def create_chart(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new chart.

        Args:
            chart_data: Chart configuration data

        Returns:
            Dictionary containing created chart details
        """
        return self._make_request("POST", "chart", json_data=chart_data)

    # Dashboard operations
    def get_dashboards(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve all dashboards.

        Args:
            params: Optional query parameters for filtering

        Returns:
            Dictionary containing dashboards list
        """
        return self._make_request("GET", "dashboard", params=params)

    def get_dashboard(self, dashboard_id: int) -> Dict[str, Any]:
        """
        Retrieve a specific dashboard by ID.

        Args:
            dashboard_id: The dashboard ID

        Returns:
            Dictionary containing dashboard details
        """
        return self._make_request("GET", f"dashboard/{dashboard_id}")

    def create_dashboard(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new dashboard.

        Args:
            dashboard_data: Dashboard configuration data

        Returns:
            Dictionary containing created dashboard details
        """
        return self._make_request("POST", "dashboard", json_data=dashboard_data)
    
    def update_dashboard(self, dashboard_id: int, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing dashboard.

        Args:
            dashboard_id: ID of the dashboard to update
            dashboard_data: Dashboard configuration data

        Returns:
            Dictionary containing updated dashboard details
        """
        return self._make_request("PUT", f"dashboard/{dashboard_id}", json_data=dashboard_data)
    
    def add_charts_to_dashboard(self, dashboard_id: int, chart_ids: List[int]) -> Dict[str, Any]:
        """
        Associate charts with a dashboard by updating its slices field.

        Args:
            dashboard_id: ID of the dashboard
            chart_ids: List of chart IDs to associate

        Returns:
            Dictionary containing update response
        """
        # Use the update dashboard endpoint with slices field
        dashboard_data = {"slices": chart_ids}
        return self._make_request("PUT", f"dashboard/{dashboard_id}", json_data=dashboard_data)
    

    # Info endpoints
    def get_chart_info(self) -> Dict[str, Any]:
        """
        Retrieve chart-related metadata.

        Returns:
            Dictionary containing chart metadata
        """
        return self._make_request("GET", "chart/_info")

    def get_dashboard_info(self) -> Dict[str, Any]:
        """
        Retrieve dashboard-related metadata.

        Returns:
            Dictionary containing dashboard metadata
        """
        return self._make_request("GET", "dashboard/_info")

    def get_dataset_info(self) -> Dict[str, Any]:
        """
        Retrieve dataset-related metadata.

        Returns:
            Dictionary containing dataset metadata
        """
        return self._make_request("GET", "dataset/_info")

    def close(self) -> None:
        """
        Clean up resources by closing the HTTP session.
        """
        self.session_manager.close_session()
        logger.info("Superset client closed")
