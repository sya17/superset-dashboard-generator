"""
Query Context Builder
Handles building query context for different chart types.
"""

import json
import logging
from typing import Dict, List, Any

from ..constants import DEFAULT_QUERY_CONTEXT

logger = logging.getLogger(__name__)


class QueryContextBuilder:
    """Builder untuk query context berdasarkan chart type dan params."""
    
    def generate_query_context(
        self, 
        chart_config: Dict[str, Any], 
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate query context untuk chart.
        
        Args:
            chart_config: Konfigurasi chart
            dataset_selected: Dataset yang digunakan
            
        Returns:
            Query context dictionary
        """
        query_context = DEFAULT_QUERY_CONTEXT.copy()
        query_context["datasource"]["id"] = dataset_selected.get("id")
        
        # Parse params untuk mendapatkan query info
        try:
            if isinstance(chart_config.get("params"), str):
                params = json.loads(chart_config["params"])
            else:
                params = chart_config.get("params", {})
            
            # Update query berdasarkan params - sesuaikan dengan chart type
            query = query_context["queries"][0]
            viz_type = chart_config.get("viz_type", "table")
            
            # Handle metrics - berbeda untuk setiap chart type
            if viz_type in ["pie", "funnel", "big_number", "big_number_total"]:
                # PIE, FUNNEL, BIG_NUMBER, and BIG_NUMBER_TOTAL charts: params menggunakan "metric" (singular), query_context menggunakan "metrics" (array)
                if "metric" in params:
                    metric = params["metric"]
                    if isinstance(metric, dict):
                        query["metrics"] = [metric]  # Convert singular to array
                    else:
                        query["metrics"] = [metric]
                elif "metrics" in params:
                    query["metrics"] = params["metrics"]
                else:
                    query["metrics"] = ["count(*)"]
                
                # Handle temporal configuration for big_number
                if viz_type == "big_number" and "x_axis" in params and "time_grain_sqla" in params:
                    self.build_big_number_temporal_query_context(query, params, dataset_selected)
                    
            elif viz_type in ["echarts_timeseries_line", "echarts_timeseries_bar", "echarts_area"]:
                # Timeseries and area charts membutuhkan struktur query yang khusus
                self.build_timeseries_query_context(query, params, dataset_selected)
                
            elif viz_type == "table":
                # Table charts membutuhkan handling berbeda untuk aggregate vs raw mode
                self.build_table_query_context(query, params, dataset_selected)
                
            else:
                # Chart types lain menggunakan "metrics" (plural)
                if "metrics" in params:
                    metrics = params["metrics"]
                    if isinstance(metrics, list) and len(metrics) > 0:
                        validated_metrics = []
                        for metric in metrics:
                            if isinstance(metric, str):
                                validated_metrics.append(metric)
                            elif isinstance(metric, dict):
                                validated_metrics.append(metric)
                            else:
                                logger.warning(f"Unknown metric type, using count(*): {metric}")
                                validated_metrics.append("count(*)")
                        query["metrics"] = validated_metrics
                    else:
                        query["metrics"] = ["count(*)"]
                else:
                    query["metrics"] = ["count(*)"]
            
            if "groupby" in params:
                query["columns"] = params["groupby"]
            if "row_limit" in params:
                query["row_limit"] = params["row_limit"]
                
        except Exception as e:
            logger.warning(f"Error parsing params for query_context: {e}")
            # Fallback ke default metrics
            query_context["queries"][0]["metrics"] = ["count(*)"]
        
        return query_context
    
    def build_timeseries_query_context(
        self,
        query: Dict[str, Any],
        params: Dict[str, Any],
        dataset_selected: Dict[str, Any]
    ) -> None:
        """
        Build query context khusus untuk timeseries charts.
        
        Args:
            query: Query object untuk dimodifikasi
            params: Params dari chart config
            dataset_selected: Dataset yang digunakan
        """
        # 1. Set metrics dari params
        if "metrics" in params:
            query["metrics"] = params["metrics"]
        
        # 2. Build columns dengan time axis dan groupby
        columns = []
        
        # Add time axis dengan proper structure sesuai database format
        if "x_axis" in params:
            x_axis = params["x_axis"]
            time_grain = params.get("time_grain_sqla", "P1W")
            
            # Cari column metadata untuk x_axis
            x_axis_column_info = None
            dataset_columns = dataset_selected.get('columns', [])
            for col in dataset_columns:
                if col.get('column_name') == x_axis:
                    x_axis_column_info = col
                    break
            
            if x_axis_column_info:
                time_column = {
                    "timeGrain": time_grain,
                    "columnType": "BASE_AXIS",
                    "sqlExpression": x_axis,
                    "label": x_axis,
                    "expressionType": "SIMPLE",
                    "column": {
                        "column_name": x_axis_column_info.get('column_name'),
                        "type": x_axis_column_info.get('type'),
                        "is_dttm": x_axis_column_info.get('is_dttm', True),
                        "python_date_format": x_axis_column_info.get('python_date_format', 'mixed'),
                        "description": x_axis_column_info.get('description', ''),
                        "filterable": x_axis_column_info.get('filterable', True),
                        "groupby": x_axis_column_info.get('groupby', True),
                        "verbose_name": x_axis_column_info.get('verbose_name', x_axis)
                    }
                }
                columns.append(time_column)
            else:
                # Fallback jika column info tidak ditemukan
                time_column = {
                    "timeGrain": time_grain,
                    "columnType": "BASE_AXIS", 
                    "sqlExpression": x_axis,
                    "label": x_axis,
                    "expressionType": "SIMPLE"
                }
                columns.append(time_column)
        
        # Add groupby columns (series dimensions)
        if "groupby" in params:
            for groupby_col in params["groupby"]:
                columns.append(groupby_col)
        
        query["columns"] = columns
        
        # 3. Set series_columns untuk groupby
        if "groupby" in params and params["groupby"]:
            query["series_columns"] = params["groupby"]
        
        # 4. Set time_grain di extras
        if "time_grain_sqla" in params:
            query["extras"]["time_grain_sqla"] = params["time_grain_sqla"]
        
        # 5. Add temporal filter untuk x_axis
        if "x_axis" in params:
            temporal_filter = {
                "col": params["x_axis"],
                "op": "TEMPORAL_RANGE", 
                "val": "No filter"
            }
            query["filters"].append(temporal_filter)
        
        # 6. Set post_processing untuk pivot operations
        x_axis = params.get("x_axis", "")
        groupby = params.get("groupby", [])
        metrics = params.get("metrics", [])
        
        if groupby and metrics:
            # Build post processing for pivot
            metric_labels = {}
            for metric in metrics:
                if isinstance(metric, dict) and "label" in metric:
                    metric_labels[metric["label"]] = {"operator": "mean"}
                elif isinstance(metric, str):
                    metric_labels[metric] = {"operator": "mean"}
            
            post_processing = [
                {
                    "operation": "pivot",
                    "options": {
                        "index": [x_axis],
                        "columns": groupby,
                        "aggregates": metric_labels,
                        "drop_missing_columns": False
                    }
                },
                {
                    "operation": "rename", 
                    "options": {
                        "columns": {list(metric_labels.keys())[0]: None if len(metric_labels) == 1 else list(metric_labels.keys())[0]},
                        "level": 0,
                        "inplace": True
                    }
                },
                {
                    "operation": "contribution",
                    "options": {
                        "orientation": params.get("contributionMode", "column"),
                        "time_shifts": []
                    }
                },
                {
                    "operation": "flatten"
                }
            ]
            
            query["post_processing"] = post_processing
        
        logger.info(f"Built timeseries query context: x_axis={params.get('x_axis')}, groupby={params.get('groupby')}, time_grain={params.get('time_grain_sqla')}")
    
    def build_big_number_temporal_query_context(
        self,
        query: Dict[str, Any],
        params: Dict[str, Any],
        dataset_selected: Dict[str, Any]
    ) -> None:
        """
        Build query context khusus untuk big_number charts dengan temporal functionality.
        
        Args:
            query: Query object untuk dimodifikasi
            params: Params dari chart config
            dataset_selected: Dataset yang digunakan
        """
        # 1. Add time axis dengan proper structure
        if "x_axis" in params:
            x_axis = params["x_axis"]
            time_grain = params.get("time_grain_sqla", "P1D")
            
            # Cari column metadata untuk x_axis
            x_axis_column_info = None
            dataset_columns = dataset_selected.get('columns', [])
            for col in dataset_columns:
                if col.get('column_name') == x_axis:
                    x_axis_column_info = col
                    break
            
            if x_axis_column_info:
                time_column = {
                    "timeGrain": time_grain,
                    "columnType": "BASE_AXIS",
                    "sqlExpression": x_axis,
                    "label": x_axis,
                    "expressionType": "SQL"
                }
                query["columns"] = [time_column]
            
            # Set time_grain di extras
            query["extras"]["time_grain_sqla"] = time_grain
            
            # Add temporal filter
            temporal_filter = {
                "col": x_axis,
                "op": "TEMPORAL_RANGE",
                "val": "No filter"
            }
            query["filters"].append(temporal_filter)
        
        # 2. Set post_processing untuk big_number temporal
        x_axis = params.get("x_axis", "")
        metrics = params.get("metric", {})
        
        if x_axis and metrics:
            metric_label = metrics.get("label", "metric") if isinstance(metrics, dict) else str(metrics)
            
            post_processing = [
                {
                    "operation": "pivot",
                    "options": {
                        "index": [x_axis],
                        "columns": [],
                        "aggregates": {
                            metric_label: {"operator": "mean"}
                        },
                        "drop_missing_columns": True
                    }
                },
                {
                    "operation": "flatten"
                }
            ]
            
            query["post_processing"] = post_processing
        
        logger.info(f"Built big_number temporal query context: x_axis={params.get('x_axis')}, time_grain={params.get('time_grain_sqla')}")
    
    def build_table_query_context(
        self,
        query: Dict[str, Any],
        params: Dict[str, Any],
        dataset_selected: Dict[str, Any]
    ) -> None:
        """
        Build query context khusus untuk table charts (aggregate/raw mode).
        
        Args:
            query: Query object untuk dimodifikasi
            params: Params dari chart config
            dataset_selected: Dataset yang digunakan
        """
        query_mode = params.get("query_mode", "aggregate")
        
        if query_mode == "aggregate":
            # Aggregate mode: groupby + metrics with post_processing
            
            # Set columns untuk groupby
            if "groupby" in params and params["groupby"]:
                query["columns"] = params["groupby"]
            
            # Set metrics
            if "metrics" in params and params["metrics"]:
                query["metrics"] = params["metrics"]
            
            # Set orderby jika ada
            if "metrics" in params and params["metrics"] and len(params["metrics"]) > 0:
                primary_metric = params["metrics"][0]
                query["orderby"] = [[primary_metric, False]]  # DESC order
                
                # Set series_limit_metric
                if "timeseries_limit_metric" in params and params["timeseries_limit_metric"]:
                    query["series_limit_metric"] = params["timeseries_limit_metric"]
                else:
                    query["series_limit_metric"] = primary_metric
            
            # Set post_processing untuk contribution calculation
            if "percent_metrics" in params and params["percent_metrics"]:
                metric_columns = []
                rename_columns = []
                for metric in params["percent_metrics"]:
                    if isinstance(metric, dict) and "label" in metric:
                        label = metric["label"]
                        metric_columns.append(label)
                        rename_columns.append(f"%{label}")
                    elif isinstance(metric, str):
                        metric_columns.append(metric)
                        rename_columns.append(f"%{metric}")
                
                if metric_columns:
                    post_processing = [{
                        "operation": "contribution",
                        "options": {
                            "columns": metric_columns,
                            "rename_columns": rename_columns
                        }
                    }]
                    query["post_processing"] = post_processing
            
            # Set temporal handling jika ada
            if "temporal_columns_lookup" in params and params["temporal_columns_lookup"]:
                for col_name, enabled in params["temporal_columns_lookup"].items():
                    if enabled:
                        temporal_filter = {
                            "col": col_name,
                            "op": "TEMPORAL_RANGE",
                            "val": "No filter"
                        }
                        query["filters"].append(temporal_filter)
                        
                        # Set time_grain_sqla di extras
                        if "time_grain_sqla" in params:
                            query["extras"]["time_grain_sqla"] = params["time_grain_sqla"]
                        
                        break
        
        else:  # raw mode
            # Raw mode: simple column selection
            if "columns" in params and params["columns"]:
                # For raw mode, set simple metrics
                query["metrics"] = ["count(*)"]
                query["columns"] = []
                
                # Set temporal column structure if date column exists
                date_columns = [col for col in params["columns"] if any(word in col.lower() for word in ['date', 'time'])]
                if date_columns:
                    time_column = {
                        "timeGrain": params.get("time_grain_sqla", "P1D"),
                        "columnType": "BASE_AXIS",
                        "sqlExpression": date_columns[0],
                        "label": date_columns[0],
                        "expressionType": "SQL"
                    }
                    query["columns"] = [time_column]
                    
                    # Set post_processing for raw mode
                    post_processing = [
                        {
                            "operation": "pivot",
                            "options": {
                                "index": [date_columns[0]],
                                "columns": [],
                                "aggregates": {"Total Saldo": {"operator": "mean"}},
                                "drop_missing_columns": True
                            }
                        },
                        {"operation": "flatten"}
                    ]
                    query["post_processing"] = post_processing
        
        logger.info(f"Built table query context: query_mode={query_mode}, columns={len(query.get('columns', []))}, metrics={len(query.get('metrics', []))}")