"""
Chart Validator
Handles validation of AI responses and chart parameters.
"""

import json
import logging
from typing import Dict, List, Any

from ..constants import CHART_CONFIGS

logger = logging.getLogger(__name__)


class ChartValidator:
    """Validator untuk chart configuration dan parameters."""
    
    def validate_ai_response(
        self, 
        ai_response: Dict[str, Any], 
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validasi dan normalisasi response dari AI model.
        
        Args:
            ai_response: Response dari AI model
            dataset_selected: Dataset yang digunakan
            
        Returns:
            Chart configuration yang tervalidasi
        """
        try:
            # Pastikan format sesuai dengan Superset API
            required_fields = ["viz_type", "slice_name", "datasource_id"]
            
            # Cek field wajib
            for field in required_fields:
                if field not in ai_response:
                    if field == "datasource_id":
                        ai_response[field] = dataset_selected.get("id")
                    elif field == "slice_name" and not ai_response.get("slice_name"):
                        ai_response[field] = f"Generated Chart - {dataset_selected.get('table_name', 'Unknown')}"
            
            # Validasi viz_type
            viz_type = ai_response.get("viz_type")
            if viz_type not in CHART_CONFIGS:
                logger.warning(f"Unknown viz_type: {viz_type}, defaulting to 'table'")
                ai_response["viz_type"] = "table"
                viz_type = "table"
            
            # Pastikan params berupa string JSON dan sesuai chart type
            if "params" in ai_response and isinstance(ai_response["params"], dict):
                # Convert dict to JSON string, tapi validate dulu sesuai chart type
                params = ai_response["params"]
                validated_params = self.validate_params_by_chart_type(params, viz_type, dataset_selected)
                ai_response["params"] = json.dumps(validated_params)
            elif "params" not in ai_response:
                # Generate default params untuk chart type
                default_params = CHART_CONFIGS[viz_type]["default_params"].copy()
                default_params["datasource"] = f"{dataset_selected.get('id')}__table"
                ai_response["params"] = json.dumps(default_params)
            
            # Set datasource_type
            if "datasource_type" not in ai_response:
                ai_response["datasource_type"] = "table"
            
            # Remove invalid fields yang tidak dikenali oleh Superset API
            invalid_fields = ["dataset_id", "table_name"]
            for field in invalid_fields:
                if field in ai_response:
                    logger.warning(f"Removing invalid field '{field}' from chart configuration")
                    del ai_response[field]
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error validating AI response: {e}")
            # Return minimal valid config
            return {
                "viz_type": "table",
                "slice_name": f"Generated Chart - {dataset_selected.get('table_name', 'Unknown')}",
                "datasource_id": dataset_selected.get("id"),
                "datasource_type": "table",
                "params": json.dumps({
                    "datasource": f"{dataset_selected.get('id')}__table",
                    "viz_type": "table"
                })
            }
    
    def validate_params_by_chart_type(
        self,
        params: Dict[str, Any],
        chart_type: str,
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate dan sesuaikan params berdasarkan chart type.
        
        Args:
            params: Raw params dari AI response
            chart_type: Tipe chart (pie, table, dll)
            dataset_selected: Dataset yang digunakan
            
        Returns:
            Validated params sesuai chart type
        """
        validated_params = params.copy()
        
        if chart_type in ["pie", "funnel"]:
            validated_params = self._validate_pie_funnel_params(validated_params, dataset_selected)
        elif chart_type in ["echarts_timeseries_line", "echarts_timeseries_bar", "echarts_area"]:
            validated_params = self._validate_timeseries_params(validated_params, dataset_selected)
        elif chart_type == "big_number":
            validated_params = self._validate_big_number_params(validated_params, dataset_selected)
        elif chart_type == "big_number_total":
            validated_params = self._validate_big_number_total_params(validated_params, dataset_selected)
        elif chart_type == "table":
            validated_params = self._validate_table_params(validated_params, dataset_selected)
        
        return validated_params
    
    def _validate_pie_funnel_params(
        self,
        params: Dict[str, Any],
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate params untuk pie dan funnel charts."""
        from ..builders.metric_builder import MetricBuilder
        metric_builder = MetricBuilder()
        
        # PIE and FUNNEL charts menggunakan "metric" singular di params
        if "metrics" in params and "metric" not in params:
            # Convert metrics array ke metric singular
            metrics = params["metrics"]
            if isinstance(metrics, list) and len(metrics) > 0:
                # Ambil metric pertama dan enhance dengan column metadata
                metric = metrics[0]
                enhanced_metric = metric_builder.enhance_metric_with_column_metadata(metric, dataset_selected)
                params["metric"] = enhanced_metric
                logger.info(f"PIE/FUNNEL chart: converted metrics array to singular metric")
            del params["metrics"]
        elif "metric" in params:
            # Enhance existing metric dengan column metadata
            metric = params["metric"]
            enhanced_metric = metric_builder.enhance_metric_with_column_metadata(metric, dataset_selected)
            params["metric"] = enhanced_metric
        
        return params
    
    def _validate_big_number_params(
        self,
        params: Dict[str, Any],
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate params untuk big_number charts."""
        from ..builders.metric_builder import MetricBuilder
        metric_builder = MetricBuilder()
        
        # Big number charts menggunakan "metric" singular
        if "metrics" in params and "metric" not in params:
            # Convert metrics array ke metric singular
            metrics = params["metrics"]
            if isinstance(metrics, list) and len(metrics) > 0:
                # Ambil metric pertama dan enhance dengan column metadata
                metric = metrics[0]
                enhanced_metric = metric_builder.enhance_metric_with_column_metadata(metric, dataset_selected)
                params["metric"] = enhanced_metric
                logger.info(f"BIG_NUMBER chart: converted metrics array to singular metric")
            del params["metrics"]
        elif "metric" in params:
            # Enhance existing metric dengan column metadata
            metric = params["metric"]
            enhanced_metric = metric_builder.enhance_metric_with_column_metadata(metric, dataset_selected)
            params["metric"] = enhanced_metric
        
        # Handle temporal parameters for big_number if x_axis is specified
        if "x_axis" in params or "time_grain_sqla" in params:
            params = self._validate_big_number_temporal_params(params, dataset_selected)
        
        return params
    
    def _validate_big_number_total_params(
        self,
        params: Dict[str, Any],
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate params untuk big_number_total charts."""
        from ..builders.metric_builder import MetricBuilder
        metric_builder = MetricBuilder()
        
        # Big number total charts menggunakan "metric" singular (seperti pie/funnel)
        if "metrics" in params and "metric" not in params:
            # Convert metrics array ke metric singular
            metrics = params["metrics"]
            if isinstance(metrics, list) and len(metrics) > 0:
                # Ambil metric pertama dan enhance dengan column metadata
                metric = metrics[0]
                enhanced_metric = metric_builder.enhance_metric_with_column_metadata(metric, dataset_selected)
                params["metric"] = enhanced_metric
                logger.info(f"BIG_NUMBER_TOTAL chart: converted metrics array to singular metric")
            del params["metrics"]
        elif "metric" in params:
            # Enhance existing metric dengan column metadata
            metric = params["metric"]
            enhanced_metric = metric_builder.enhance_metric_with_column_metadata(metric, dataset_selected)
            params["metric"] = enhanced_metric
        
        return params
    
    def _validate_timeseries_params(
        self,
        params: Dict[str, Any],
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate dan sesuaikan params khusus untuk timeseries charts."""
        from ..builders.metric_builder import MetricBuilder
        metric_builder = MetricBuilder()
        
        validated_params = params.copy()
        columns = dataset_selected.get('columns', [])
        
        # 1. Ensure x_axis (time column) is set correctly
        if "x_axis" not in validated_params:
            # Find date/time column
            date_columns = [col for col in columns if 'date' in str(col.get('type', '')).lower() or col.get('is_dttm', False)]
            if date_columns:
                validated_params["x_axis"] = date_columns[0].get('column_name')
            else:
                # Fallback - cari kolom yang nama mengandung date/time
                date_named_cols = [col for col in columns if any(word in col.get('column_name', '').lower() for word in ['date', 'time', 'created', 'updated'])]
                if date_named_cols:
                    validated_params["x_axis"] = date_named_cols[0].get('column_name')
                else:
                    validated_params["x_axis"] = columns[0].get('column_name', 'id') if columns else 'id'
        
        # 2. Set default time_grain_sqla
        if "time_grain_sqla" not in validated_params:
            validated_params["time_grain_sqla"] = "P1W"  # Default weekly
        
        # 3. Handle metrics - convert any format ke proper format
        if "metrics" in validated_params:
            metrics = validated_params["metrics"]
            if isinstance(metrics, list):
                enhanced_metrics = []
                for metric in metrics:
                    enhanced_metric = metric_builder.enhance_metric_with_column_metadata(metric, dataset_selected)
                    enhanced_metrics.append(enhanced_metric)
                validated_params["metrics"] = enhanced_metrics
        elif "metric" in validated_params:
            # Convert singular to plural
            metric = validated_params["metric"]
            enhanced_metric = metric_builder.enhance_metric_with_column_metadata(metric, dataset_selected)
            validated_params["metrics"] = [enhanced_metric]
            del validated_params["metric"]
        else:
            # No metrics specified, create default
            numeric_cols = [col for col in columns if any(t in str(col.get('type', '')).lower() for t in ['int', 'float', 'decimal', 'numeric'])]
            if numeric_cols:
                first_numeric = numeric_cols[0]
                default_metric = metric_builder.build_metric_object("SUM", first_numeric, f"SUM({first_numeric.get('column_name')})")
                validated_params["metrics"] = [default_metric]
            else:
                # Fallback to count
                first_col = columns[0] if columns else {"column_name": "id", "type": "INTEGER"}
                default_metric = metric_builder.build_metric_object("COUNT", first_col, f"COUNT({first_col.get('column_name')})")
                validated_params["metrics"] = [default_metric]
        
        # 4. Handle groupby (dimensions for series)
        if "groupby" not in validated_params:
            # Find categorical columns untuk series
            categorical_cols = [col for col in columns if any(t in str(col.get('type', '')).lower() for t in ['varchar', 'text', 'string', 'char'])]
            if categorical_cols:
                # Pilih kolom kategoris yang bukan time column
                x_axis = validated_params.get("x_axis", "")
                non_time_categoricals = [col for col in categorical_cols if col.get('column_name') != x_axis]
                if non_time_categoricals:
                    validated_params["groupby"] = [non_time_categoricals[0].get('column_name')]
                else:
                    validated_params["groupby"] = []
            else:
                validated_params["groupby"] = []
        
        # 5. Handle contribution mode if specified
        if "contribution_mode" not in validated_params and "contributionMode" not in validated_params:
            # Check if AI specified contribution mode in any format
            for key in validated_params:
                if "contribution" in str(key).lower():
                    value = validated_params[key]
                    if isinstance(value, str) and value.lower() in ["column", "row"]:
                        validated_params["contributionMode"] = value.lower()
                        break
        elif "contribution_mode" in validated_params:
            # Convert snake_case to camelCase
            validated_params["contributionMode"] = validated_params["contribution_mode"]
            del validated_params["contribution_mode"]

        # 5a. Validate contributionMode for line chart - fix invalid 'series' value
        if "contributionMode" in validated_params:
            contribution_mode = validated_params["contributionMode"]
            if contribution_mode not in ["column", "row"]:
                logger.warning(f"Invalid contributionMode '{contribution_mode}' for timeseries chart, correcting to 'column'")
                validated_params["contributionMode"] = "column"

        # 6. Remove invalid fields yang tidak dipakai timeseries
        invalid_fields = ["series", "x_axis_object", "y_axis"]
        for field in invalid_fields:
            if field in validated_params:
                del validated_params[field]
        
        # Set default timeseries specific params
        default_timeseries_params = {
            "x_axis_sort_asc": True,
            "x_axis_sort_series": "name",
            "x_axis_sort_series_ascending": True,
            "order_desc": True,
            "row_limit": 1000,
            "truncate_metric": True,
            "show_empty_columns": True,
            "comparison_type": "values",
            "contributionMode": "column",
            "annotation_layers": [],
            "forecastPeriods": 10,
            "forecastInterval": 0.8,
            "x_axis_title_margin": 15,
            "y_axis_title_margin": 30,
            "y_axis_title_position": "Left",
            "sort_series_type": "sum",
            "color_scheme": "bnbColors",
            "time_shift_color": True,
            "seriesType": "line",
            "only_total": True,
            "opacity": 0.2,
            "markerSize": 6,
            "show_legend": True,
            "legendType": "scroll",
            "legendOrientation": "top",
            "x_axis_time_format": "smart_date",
            "rich_tooltip": True,
            "showTooltipTotal": True,
            "tooltipTimeFormat": "smart_date",
            "y_axis_format": ",.2f",
            "truncateXAxis": True,
            "y_axis_bounds": [None, None]
        }
        
        for key, value in default_timeseries_params.items():
            if key not in validated_params:
                validated_params[key] = value
        
        # 7. Ensure temporal filter is set correctly
        if "adhoc_filters" not in validated_params or not validated_params["adhoc_filters"]:
            x_axis = validated_params.get("x_axis", "")
            if x_axis:
                temporal_filter = {
                    "clause": "WHERE",
                    "subject": x_axis,
                    "operator": "TEMPORAL_RANGE",
                    "comparator": "No filter",
                    "expressionType": "SIMPLE"
                }
                validated_params["adhoc_filters"] = [temporal_filter]
        else:
            # Update existing temporal filter with correct x_axis
            x_axis = validated_params.get("x_axis", "")
            if x_axis:
                for filter_item in validated_params["adhoc_filters"]:
                    if filter_item.get("operator") == "TEMPORAL_RANGE":
                        filter_item["subject"] = x_axis
                        break
        
        logger.info(f"Timeseries params validated: x_axis={validated_params.get('x_axis')}, metrics_count={len(validated_params.get('metrics', []))}, groupby={validated_params.get('groupby')}")
        
        return validated_params
    
    def _validate_big_number_temporal_params(
        self,
        params: Dict[str, Any],
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate dan sesuaikan params khusus untuk big_number charts dengan temporal functionality."""
        validated_params = params.copy()
        columns = dataset_selected.get('columns', [])
        
        # 1. Ensure x_axis (time column) is set correctly
        if "x_axis" not in validated_params or not validated_params["x_axis"]:
            # Find date/time column
            date_columns = [col for col in columns if 'date' in str(col.get('type', '')).lower() or col.get('is_dttm', False)]
            if date_columns:
                validated_params["x_axis"] = date_columns[0].get('column_name')
            else:
                # Fallback - cari kolom yang nama mengandung date/time
                date_named_cols = [col for col in columns if any(word in col.get('column_name', '').lower() for word in ['date', 'time', 'created', 'updated'])]
                if date_named_cols:
                    validated_params["x_axis"] = date_named_cols[0].get('column_name')
        
        # 2. Set default time_grain_sqla if not specified
        if "time_grain_sqla" not in validated_params:
            validated_params["time_grain_sqla"] = "P1D"  # Default daily
        
        # 3. Ensure adhoc_filters includes temporal filter for x_axis
        if "x_axis" in validated_params:
            x_axis = validated_params["x_axis"]
            
            # Check if temporal filter already exists
            adhoc_filters = validated_params.get("adhoc_filters", [])
            has_temporal_filter = any(
                filter_item.get("operator") == "TEMPORAL_RANGE" and filter_item.get("subject") == x_axis
                for filter_item in adhoc_filters
            )
            
            if not has_temporal_filter:
                temporal_filter = {
                    "clause": "WHERE",
                    "subject": x_axis,
                    "operator": "TEMPORAL_RANGE",
                    "comparator": "No filter",
                    "expressionType": "SIMPLE"
                }
                adhoc_filters.append(temporal_filter)
                validated_params["adhoc_filters"] = adhoc_filters
        
        logger.info(f"Big number temporal params validated: x_axis={validated_params.get('x_axis')}, time_grain={validated_params.get('time_grain_sqla')}")
        
        return validated_params
    
    def _validate_table_params(
        self,
        params: Dict[str, Any],
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate dan sesuaikan params khusus untuk table charts (aggregate/raw mode)."""
        from ..builders.metric_builder import MetricBuilder
        metric_builder = MetricBuilder()
        
        validated_params = params.copy()
        columns = dataset_selected.get('columns', [])
        
        # Determine query mode
        query_mode = validated_params.get("query_mode", "aggregate")
        
        if query_mode == "aggregate":
            # Aggregate mode: needs groupby + metrics
            # Handle metrics conversion and enhancement
            if "metric" in validated_params and "metrics" not in validated_params:
                # Convert singular ke plural array
                metric = validated_params["metric"]
                enhanced_metric = metric_builder.enhance_metric_with_column_metadata(metric, dataset_selected)
                validated_params["metrics"] = [enhanced_metric]
                del validated_params["metric"]
                logger.info("Table aggregate: converted singular metric to metrics array")
            elif "metrics" in validated_params:
                # Enhance existing metrics dengan column metadata
                metrics = validated_params["metrics"]
                if isinstance(metrics, list):
                    enhanced_metrics = []
                    for metric in metrics:
                        enhanced_metric = metric_builder.enhance_metric_with_column_metadata(metric, dataset_selected)
                        enhanced_metrics.append(enhanced_metric)
                    validated_params["metrics"] = enhanced_metrics
            
            # Ensure percent_metrics and timeseries_limit_metric are set if metrics exist
            if "metrics" in validated_params and validated_params["metrics"]:
                if "percent_metrics" not in validated_params:
                    validated_params["percent_metrics"] = validated_params["metrics"].copy()
                if "timeseries_limit_metric" not in validated_params:
                    validated_params["timeseries_limit_metric"] = validated_params["metrics"][0]
            
            # Set temporal_columns_lookup if time columns exist
            if "temporal_columns_lookup" not in validated_params:
                temporal_lookup = {}
                date_columns = [col for col in columns if 'date' in str(col.get('type', '')).lower() or col.get('is_dttm', False)]
                if not date_columns:
                    date_named_cols = [col for col in columns if any(word in col.get('column_name', '').lower() for word in ['date', 'time', 'created', 'updated'])]
                    if date_named_cols:
                        temporal_lookup[date_named_cols[0].get('column_name')] = True
                else:
                    temporal_lookup[date_columns[0].get('column_name')] = True
                validated_params["temporal_columns_lookup"] = temporal_lookup
            
        else:  # raw mode
            # Raw mode: just needs columns list
            if "columns" not in validated_params or not validated_params["columns"]:
                # Auto-select reasonable columns
                column_names = [col.get('column_name') for col in columns[:7]]  # First 7 columns
                validated_params["columns"] = column_names
            
            # Process ordering for raw mode
            validated_params = self._process_table_ordering(validated_params, dataset_selected)
            
            # Clear aggregate-specific fields
            validated_params["groupby"] = []
            validated_params["metrics"] = []
            validated_params["all_columns"] = validated_params.get("columns", [])
        
        logger.info(f"Table params validated: query_mode={query_mode}, columns={len(validated_params.get('columns', []))}, metrics={len(validated_params.get('metrics', []))}, order_by_cols={validated_params.get('order_by_cols', [])}")
        
        return validated_params
    
    def _process_table_ordering(
        self,
        params: Dict[str, Any],
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process ordering parameters for table raw mode."""
        validated_params = params.copy()
        columns = dataset_selected.get('columns', [])
        column_names = [col.get('column_name') for col in columns]
        
        # Check if AI provided order_by_cols
        order_by_cols = validated_params.get("order_by_cols", [])
        
        # If no order_by_cols provided, check for common ordering patterns
        if not order_by_cols:
            # Look for ordering hints in other parameters
            ordering_hints = []
            
            # Check for ordering-related keywords in params
            for key, value in validated_params.items():
                if "order" in str(key).lower() and isinstance(value, (str, list)) and value:
                    if isinstance(value, str):
                        ordering_hints.append(value)
                    elif isinstance(value, list):
                        ordering_hints.extend([str(v) for v in value])
            
            # Map common ordering terms to actual column names
            order_columns = self._map_ordering_terms_to_columns(ordering_hints, column_names)
            if order_columns:
                validated_params["order_by_cols"] = order_columns
                logger.info(f"Mapped ordering hints {ordering_hints} to columns: {order_columns}")
        else:
            # Validate existing order_by_cols against actual column names
            valid_order_cols = []
            for order_col in order_by_cols:
                mapped_col = self._map_single_ordering_term(order_col, column_names)
                if mapped_col:
                    valid_order_cols.append(mapped_col)
            
            if valid_order_cols:
                # Format order_by_cols sesuai dengan format Superset: ["[\"column_name\", ascending_boolean]"]
                order_desc = validated_params.get("order_desc", True)
                formatted_order_cols = []
                for col in valid_order_cols:
                    # Format: "[\"column_name\", true]" untuk ASC, "[\"column_name\", false]" untuk DESC
                    formatted_col = f"[\"{col}\", {str(not order_desc).lower()}]"
                    formatted_order_cols.append(formatted_col)
                
                validated_params["order_by_cols"] = formatted_order_cols
                logger.info(f"Validated order_by_cols: {formatted_order_cols}")
            else:
                # If no valid columns found, clear ordering
                validated_params["order_by_cols"] = []
                logger.warning(f"No valid columns found for ordering: {order_by_cols}")
        
        # Ensure order_desc is set (default to True for descending)
        if "order_desc" not in validated_params:
            validated_params["order_desc"] = True
        
        return validated_params
    
    def _map_ordering_terms_to_columns(
        self,
        ordering_terms: List[str],
        column_names: List[str]
    ) -> List[str]:
        """Map ordering terms to actual column names."""
        mapped_columns = []
        
        for term in ordering_terms:
            mapped_col = self._map_single_ordering_term(term, column_names)
            if mapped_col and mapped_col not in mapped_columns:
                mapped_columns.append(mapped_col)
        
        return mapped_columns
    
    def _map_single_ordering_term(
        self,
        term: str,
        column_names: List[str]
    ) -> str:
        """Map a single ordering term to actual column name."""
        if not term or not isinstance(term, str):
            return ""
        
        term_lower = term.lower().strip()
        
        # Direct match first
        if term in column_names:
            return term
        
        # Common date/time ordering mappings
        date_mappings = {
            "created date": ["created_date", "created_at", "date_created", "create_date"],
            "updated date": ["updated_date", "updated_at", "date_updated", "update_date"],
            "order date": ["order_date", "date_order", "order_time"],
            "tanggal dibuat": ["created_date", "tanggal_dibuat", "created_at"],
            "tanggal": ["date", "tanggal", "created_date", "order_date"],
            "waktu": ["time", "waktu", "created_at", "updated_at"]
        }
        
        # Check for date mapping matches
        for mapping_key, possible_columns in date_mappings.items():
            if mapping_key in term_lower:
                for col_candidate in possible_columns:
                    if col_candidate in column_names:
                        return col_candidate
        
        # Fuzzy matching for column names containing the term
        for col in column_names:
            col_lower = col.lower()
            # Check if term is part of column name or vice versa
            if term_lower in col_lower or col_lower in term_lower:
                # Additional check for common date/time words
                if any(word in col_lower for word in ['date', 'time', 'created', 'updated', 'tanggal', 'waktu']):
                    return col
        
        # Last resort: exact match ignoring case
        for col in column_names:
            if col.lower() == term_lower:
                return col
        
        return ""