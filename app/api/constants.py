"""
API route constants and configurations.
"""
from typing import Dict, Any

# Default pagination settings
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

# Common query parameter structures
DATASET_COLUMNS = ["id", "table_name", "schema", "database", "owners"]
CHART_COLUMNS = ["id", "slice_name", "viz_type", "datasource_id", "owners"]
DASHBOARD_COLUMNS = ["id", "dashboard_title", "slug", "owners"]

# Default ordering
DEFAULT_ORDER_COLUMN = "changed_on_delta_humanized"
DEFAULT_ORDER_DIRECTION = "desc"

# Search operators
SEARCH_OPERATOR_CONTAINS = "ct"

def build_query_params(
    columns: list,
    filters: list = None,
    order_column: str = DEFAULT_ORDER_COLUMN,
    order_direction: str = DEFAULT_ORDER_DIRECTION,
    page: int = 0,
    page_size: int = DEFAULT_PAGE_SIZE
) -> Dict[str, Any]:
    """Build standardized query parameters for Superset API."""
    return {
        "columns": columns,
        "filters": filters or [],
        "order_column": order_column,
        "order_direction": order_direction,
        "page": page,
        "page_size": min(page_size, MAX_PAGE_SIZE)  # Cap page size
    }

def add_search_filter(filters: list, column: str, query: str) -> None:
    """Add search filter to existing filters list."""
    if query:
        filters.append({
            "col": column,
            "opr": SEARCH_OPERATOR_CONTAINS,
            "value": query
        })
