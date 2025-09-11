"""
Service layer for Superset API operations.
"""
import json
import logging
from typing import Dict, Any, Optional, List

from app.services import SupersetClient
from .constants import (
    build_query_params,
    add_search_filter,
    DATASET_COLUMNS,
    CHART_COLUMNS,
    DASHBOARD_COLUMNS
)
from .models import (
    DatasetListResponse,
    ChartListResponse,
    DashboardListResponse,
    SearchParams
)

logger = logging.getLogger(__name__)


class SupersetAPIService:
    """Service layer for Superset API operations."""

    def __init__(self, client: SupersetClient):
        self.client = client

    def get_datasets(self, params: SearchParams) -> DatasetListResponse:
        """Get list of datasets with optional search and pagination."""
        try:
            # Build query parameters
            filters = []
            add_search_filter(filters, "table_name", params.q)

            query_params = build_query_params(
                columns=DATASET_COLUMNS,
                filters=filters,
                page=params.page,
                page_size=params.page_size
            )

            # Convert to JSON string as expected by Superset API
            api_params = {"q": json.dumps(query_params)}

            response = self.client.get_datasets(params=api_params)

            return DatasetListResponse(
                result=response.get("result", []),
                count=response.get("count", 0)
            )
        except Exception as e:
            logger.error(f"Failed to fetch datasets: {e}")
            raise

    def get_dataset(self, dataset_id: int) -> Dict[str, Any]:
        """Get single dataset details."""
        try:
            return self.client.get_dataset(dataset_id)
        except Exception as e:
            logger.error(f"Failed to fetch dataset {dataset_id}: {e}")
            raise

    def get_dataset_info(self) -> Dict[str, Any]:
        """Get dataset metadata for creation."""
        try:
            return self.client.get_dataset_info()
        except Exception as e:
            logger.error(f"Failed to fetch dataset info: {e}")
            raise

    def get_charts(self, params: SearchParams) -> ChartListResponse:
        """Get list of charts with optional search and pagination."""
        try:
            # Build query parameters
            filters = []
            add_search_filter(filters, "slice_name", params.q)

            query_params = build_query_params(
                columns=CHART_COLUMNS,
                filters=filters,
                page=params.page,
                page_size=params.page_size
            )

            # Convert to JSON string as expected by Superset API
            api_params = {"q": json.dumps(query_params)}

            response = self.client.get_charts(params=api_params)

            return ChartListResponse(
                result=response.get("result", []),
                count=response.get("count", 0)
            )
        except Exception as e:
            logger.error(f"Failed to fetch charts: {e}")
            raise

    def get_chart(self, chart_id: int) -> Dict[str, Any]:
        """Get single chart details."""
        try:
            return self.client.get_chart(chart_id)
        except Exception as e:
            logger.error(f"Failed to fetch chart {chart_id}: {e}")
            raise

    def get_chart_info(self) -> Dict[str, Any]:
        """Get chart metadata for creation."""
        try:
            return self.client.get_chart_info()
        except Exception as e:
            logger.error(f"Failed to fetch chart info: {e}")
            raise

    def get_dashboards(self, params: SearchParams) -> DashboardListResponse:
        """Get list of dashboards with optional search and pagination."""
        try:
            # Build query parameters
            filters = []
            add_search_filter(filters, "dashboard_title", params.q)

            query_params = build_query_params(
                columns=DASHBOARD_COLUMNS,
                filters=filters,
                page=params.page,
                page_size=params.page_size
            )

            # Convert to JSON string as expected by Superset API
            api_params = {"q": json.dumps(query_params)}

            response = self.client.get_dashboards(params=api_params)

            return DashboardListResponse(
                result=response.get("result", []),
                count=response.get("count", 0)
            )
        except Exception as e:
            logger.error(f"Failed to fetch dashboards: {e}")
            raise

    def get_dashboard(self, dashboard_id: int) -> Dict[str, Any]:
        """Get single dashboard details."""
        try:
            return self.client.get_dashboard(dashboard_id)
        except Exception as e:
            logger.error(f"Failed to fetch dashboard {dashboard_id}: {e}")
            raise

    def get_dashboard_info(self) -> Dict[str, Any]:
        """Get dashboard metadata for creation."""
        try:
            return self.client.get_dashboard_info()
        except Exception as e:
            logger.error(f"Failed to fetch dashboard info: {e}")
            raise

    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information."""
        try:
            logger.info("🔍 Getting current user info for debugging...")
            response = self.client._request("GET", "security/me")
            logger.info(f"🔍 Current user info: {response}")
            return response
        except Exception as e:
            logger.error(f"❌ Failed to get user info: {e}")
            raise

    def get_accessible_resources(self) -> Dict[str, Any]:
        """Get summary of accessible resources."""
        try:
            logger.info("🔍 Checking all accessible resources...")

            result = {}

            # Check datasets
            try:
                datasets_response = self.client.get_datasets(params={"q": ""})
                result["datasets"] = {
                    "count": datasets_response.get("count", 0),
                    "accessible": len(datasets_response.get("result", []))
                }
            except Exception as e:
                result["datasets"] = {"error": str(e)}

            # Check charts
            try:
                charts_response = self.client.get_charts(params={"q": ""})
                result["charts"] = {
                    "count": charts_response.get("count", 0),
                    "accessible": len(charts_response.get("result", []))
                }
            except Exception as e:
                result["charts"] = {"error": str(e)}

            # Check dashboards
            try:
                dashboards_response = self.client.get_dashboards(params={"q": ""})
                result["dashboards"] = {
                    "count": dashboards_response.get("count", 0),
                    "accessible": len(dashboards_response.get("result", []))
                }
            except Exception as e:
                result["dashboards"] = {"error": str(e)}

            logger.info(f"🔍 Access summary: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to check accessible resources: {e}")
            raise


# Dependency injection function
def get_superset_service() -> SupersetAPIService:
    """Dependency injection for SupersetAPIService."""
    from app.services import get_superset_client
    client = get_superset_client()
    return SupersetAPIService(client)
