"""
Chart Generator Service
Service utama untuk menggenerate chart Superset menggunakan AI model.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from app.services.model_client import get_model_client
from app.services.superset.client import SupersetClient
from .instruction_builder import InstructionBuilder
from .constants import DEFAULT_QUERY_CONTEXT, CHART_CONFIGS

logger = logging.getLogger(__name__)


class ChartGeneratorError(Exception):
    """Exception untuk Chart Generator service."""
    pass


class ChartGenerator:
    """
    Service untuk menggenerate chart Superset menggunakan AI model.
    
    Flow:
    1. Terima user_prompt dan dataset_selected
    2. Build instruksi AI menggunakan InstructionBuilder  
    3. Kirim ke AI model untuk generate konfigurasi
    4. Validasi dan parse response AI
    5. Create chart via Superset API
    """
    
    def __init__(self):
        self.instruction_builder = InstructionBuilder()
        self.model_client = get_model_client()
        self.superset_client = SupersetClient()
        
        logger.info("ChartGenerator service initialized")
    
    async def generate_chart(
        self, 
        user_prompt: str, 
        dataset_selected: Dict[str, Any],
        dashboard_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate chart berdasarkan user prompt dan dataset.
        
        Args:
            user_prompt: Prompt dari user (e.g., "Buat Dashboard Pie Simpanan status")
            dataset_selected: Dataset hasil dari dataset_selector
            dashboard_id: Optional dashboard ID untuk associate chart
            
        Returns:
            Dictionary dengan informasi chart yang dibuat
        """
        try:
            logger.info(f"Starting chart generation for prompt: '{user_prompt}'")
            
            # 1. Build instruksi AI
            messages = self.instruction_builder.build_complete_instruction(
                user_prompt, dataset_selected
            )
            
            # 2. Generate konfigurasi via AI model
            logger.info("Generating chart configuration via AI model")
            ai_response = await self.model_client.generate_json_async(
                messages=messages,
                temperature=0.1,
                max_tokens=4000
            )
            
            logger.info(f"AI response received: {ai_response}")
            
            # Debug: Print messages yang dikirim ke AI
            logger.info(f"Messages sent to AI: {messages}")
            
            # Debug: Print raw content jika ada error
            if "error" in ai_response and "raw_content" in ai_response:
                logger.error(f"Raw AI content causing error: {repr(ai_response['raw_content'])}")
            
            if "error" in ai_response:
                logger.error(f"AI model JSON parsing failed: {ai_response['error']}")
                if "raw_content" in ai_response:
                    logger.error(f"Raw AI content: {ai_response['raw_content']}")
                raise ChartGeneratorError(f"AI model error: {ai_response['error']}")
            
            # 3. Validasi dan parse AI response
            chart_config = self._validate_ai_response(ai_response, dataset_selected)
            
            # 4. Create chart via Superset API
            logger.info("Creating chart via Superset API")
            created_chart = self.superset_client.create_chart(chart_config)
            logger.info(f'created_chart: {created_chart}')
            
            # 5. Associate dengan dashboard jika diminta
            if dashboard_id and created_chart.get("id"):
                await self._associate_chart_to_dashboard(
                    created_chart["id"], dashboard_id
                )
            
            result = {
                "success": True,
                "chart": created_chart,
                "ai_config": chart_config,
                "user_prompt": user_prompt,
                "dataset_used": dataset_selected.get("table_name"),
                "chart_type": chart_config.get("viz_type")
            }
            
            logger.info(f"Chart generated successfully: {created_chart.get('id')}")
            return result
            
        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_prompt": user_prompt,
                "dataset_used": dataset_selected.get("table_name") if dataset_selected else None
            }
    
    def _validate_ai_response(
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
                validated_params = self._validate_params_by_chart_type(params, viz_type, dataset_selected)
                ai_response["params"] = json.dumps(validated_params)
            elif "params" not in ai_response:
                # Generate default params untuk chart type
                default_params = CHART_CONFIGS[viz_type]["default_params"].copy()
                default_params["datasource"] = f"{dataset_selected.get('id')}__table"
                ai_response["params"] = json.dumps(default_params)
            
            # Set datasource_type
            if "datasource_type" not in ai_response:
                ai_response["datasource_type"] = "table"
            
            # Generate query_context jika diperlukan
            if "query_context" not in ai_response:
                query_context = self._generate_query_context(ai_response, dataset_selected)
                ai_response["query_context"] = json.dumps(query_context)
            elif isinstance(ai_response["query_context"], dict):
                # Pastikan query_context adalah string JSON
                ai_response["query_context"] = json.dumps(ai_response["query_context"])
            
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
    
    def _validate_params_by_chart_type(
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
            # PIE and FUNNEL charts menggunakan "metric" singular di params
            if "metrics" in validated_params and "metric" not in validated_params:
                # Convert metrics array ke metric singular
                metrics = validated_params["metrics"]
                if isinstance(metrics, list) and len(metrics) > 0:
                    # Ambil metric pertama dan enhance dengan column metadata
                    metric = metrics[0]
                    enhanced_metric = self._enhance_metric_with_column_metadata(metric, dataset_selected)
                    validated_params["metric"] = enhanced_metric
                    logger.info(f"{chart_type.upper()} chart: converted metrics array to singular metric")
                del validated_params["metrics"]
            elif "metric" in validated_params:
                # Enhance existing metric dengan column metadata
                metric = validated_params["metric"]
                enhanced_metric = self._enhance_metric_with_column_metadata(metric, dataset_selected)
                validated_params["metric"] = enhanced_metric
        
        elif chart_type in ["echarts_timeseries_line", "echarts_timeseries_bar", "echarts_area"]:
            # Timeseries and area charts membutuhkan struktur yang berbeda
            validated_params = self._validate_timeseries_params(validated_params, dataset_selected)
            
        elif chart_type == "table":
            # Table charts menggunakan "metrics" plural
            if "metric" in validated_params and "metrics" not in validated_params:
                # Convert singular ke plural array
                metric = validated_params["metric"]
                enhanced_metric = self._enhance_metric_with_column_metadata(metric, dataset_selected)
                validated_params["metrics"] = [enhanced_metric]
                del validated_params["metric"]
                logger.info(f"{chart_type}: converted singular metric to metrics array")
            elif "metrics" in validated_params:
                # Enhance existing metrics dengan column metadata
                metrics = validated_params["metrics"]
                if isinstance(metrics, list):
                    enhanced_metrics = []
                    for metric in metrics:
                        enhanced_metric = self._enhance_metric_with_column_metadata(metric, dataset_selected)
                        enhanced_metrics.append(enhanced_metric)
                    validated_params["metrics"] = enhanced_metrics
        
        elif chart_type in ["big_number", "big_number_total"]:
            # Big number charts menggunakan "metrics" plural
            if "metric" in validated_params and "metrics" not in validated_params:
                metric = validated_params["metric"]
                enhanced_metric = self._enhance_metric_with_column_metadata(metric, dataset_selected)
                validated_params["metrics"] = [enhanced_metric]
                del validated_params["metric"]
                logger.info(f"{chart_type}: converted singular metric to metrics array")
        
        return validated_params
    
    def _validate_timeseries_params(
        self,
        params: Dict[str, Any],
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate dan sesuaikan params khusus untuk timeseries charts.
        
        Args:
            params: Raw params
            dataset_selected: Dataset yang digunakan
            
        Returns:
            Validated timeseries params
        """
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
                    enhanced_metric = self._enhance_metric_with_column_metadata(metric, dataset_selected)
                    enhanced_metrics.append(enhanced_metric)
                validated_params["metrics"] = enhanced_metrics
        elif "metric" in validated_params:
            # Convert singular to plural
            metric = validated_params["metric"]
            enhanced_metric = self._enhance_metric_with_column_metadata(metric, dataset_selected)
            validated_params["metrics"] = [enhanced_metric]
            del validated_params["metric"]
        else:
            # No metrics specified, create default
            numeric_cols = [col for col in columns if any(t in str(col.get('type', '')).lower() for t in ['int', 'float', 'decimal', 'numeric'])]
            if numeric_cols:
                first_numeric = numeric_cols[0]
                default_metric = self._build_metric_object("SUM", first_numeric, f"SUM({first_numeric.get('column_name')})")
                validated_params["metrics"] = [default_metric]
            else:
                # Fallback to count
                first_col = columns[0] if columns else {"column_name": "id", "type": "INTEGER"}
                default_metric = self._build_metric_object("COUNT", first_col, f"COUNT({first_col.get('column_name')})")
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
        
        # 6. Set default timeseries specific params
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
    
    def _enhance_metric_with_column_metadata(
        self,
        metric: Any,
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance metric dengan column metadata yang lengkap.
        
        Args:
            metric: Raw metric dari AI
            dataset_selected: Dataset untuk mendapatkan column info
            
        Returns:
            Enhanced metric dengan column metadata
        """
        # Jika sudah dalam format string sederhana, convert ke format yang proper
        if isinstance(metric, str):
            if metric.startswith("count"):
                # Extract column name dari count(column_name) atau gunakan count(*)
                if "(" in metric and ")" in metric:
                    col_match = metric[metric.find("(")+1:metric.find(")")]
                    if col_match == "*":
                        # count(*) - gunakan kolom pertama yang ada
                        columns = dataset_selected.get('columns', [])
                        if columns:
                            first_col = columns[0]
                            return self._build_metric_object("COUNT", first_col, f"COUNT({first_col.get('column_name', 'id')})")
                    else:
                        # count(column_name) - cari column yang sesuai
                        columns = dataset_selected.get('columns', [])
                        for col in columns:
                            if col.get('column_name') == col_match:
                                return self._build_metric_object("COUNT", col, f"COUNT({col_match})")
            elif metric.startswith("sum"):
                col_match = metric[metric.find("(")+1:metric.find(")")]
                columns = dataset_selected.get('columns', [])
                for col in columns:
                    if col.get('column_name') == col_match:
                        return self._build_metric_object("SUM", col, f"SUM({col_match})")
            elif metric.startswith("avg"):
                col_match = metric[metric.find("(")+1:metric.find(")")]
                columns = dataset_selected.get('columns', [])
                for col in columns:
                    if col.get('column_name') == col_match:
                        return self._build_metric_object("AVG", col, f"AVG({col_match})")
            
            # Fallback untuk string format
            return {"expressionType": "SQL", "sqlExpression": metric, "label": metric.upper()}
        
        elif isinstance(metric, dict):
            # Jika sudah dict, enhance dengan column metadata jika belum ada
            if "column" in metric and isinstance(metric["column"], dict):
                # Sudah ada column metadata, tapi check apakah complete
                if "expressionType" not in metric or "optionName" not in metric:
                    # Missing required fields - rebuild metric completely
                    aggregate = metric.get("aggregate", "COUNT")
                    label = metric.get("label", f"{aggregate}(*)")
                    column_info = metric["column"]
                    return self._build_metric_object(aggregate, column_info, label)
                
                # Just enhance column metadata if missing id
                column = metric["column"]
                if "id" not in column:
                    # Enhance dengan column metadata dari dataset
                    column_name = column.get("column_name", "")
                    columns = dataset_selected.get('columns', [])
                    for col in columns:
                        if col.get('column_name') == column_name:
                            # Update column dengan metadata lengkap
                            enhanced_column = self._build_column_metadata(col)
                            metric["column"] = enhanced_column
                            break
                return metric
            else:
                # Dict tapi belum ada column metadata yang proper
                if "aggregate" in metric and "sqlExpression" not in metric:
                    # Format aggregate tanpa column - coba enhance
                    aggregate = metric.get("aggregate", "COUNT")
                    label = metric.get("label", f"{aggregate}(*)")
                    
                    # Extract column name dari label jika ada
                    if "(" in label and ")" in label:
                        col_match = label[label.find("(")+1:label.find(")")]
                        if col_match != "*":
                            columns = dataset_selected.get('columns', [])
                            for col in columns:
                                if col.get('column_name') == col_match:
                                    return self._build_metric_object(aggregate, col, label)
                    
                    # Fallback - gunakan kolom pertama
                    columns = dataset_selected.get('columns', [])
                    if columns:
                        first_col = columns[0]
                        return self._build_metric_object(aggregate, first_col, label)
                
                return metric
        
        # Fallback default
        columns = dataset_selected.get('columns', [])
        if columns:
            first_col = columns[0]
            return self._build_metric_object("COUNT", first_col, f"COUNT({first_col.get('column_name', 'id')})")
        
        return {"expressionType": "SQL", "sqlExpression": "count(*)", "label": "COUNT(*)"}
    
    def _build_metric_object(self, aggregate: str, column_info: Dict[str, Any], label: str) -> Dict[str, Any]:
        """
        Build metric object dengan format yang sesuai Superset.
        
        Args:
            aggregate: Jenis aggregate (COUNT, SUM, AVG, dll)
            column_info: Info kolom dari dataset
            label: Label untuk metric
            
        Returns:
            Metric object yang lengkap
        """
        # Generate proper optionName similar to Superset format
        import hashlib
        import time
        
        # Create unique optionName based on label and timestamp
        hash_input = f"{label}_{int(time.time())}"
        hash_object = hashlib.md5(hash_input.encode())
        hash_hex = hash_object.hexdigest()
        option_name = f"metric_{hash_hex[:10]}_{hash_hex[10:23]}"
        
        return {
            "expressionType": "SIMPLE",
            "column": self._build_column_metadata(column_info),
            "aggregate": aggregate.upper(),
            "sqlExpression": None,
            "datasourceWarning": False,
            "hasCustomLabel": False,
            "label": label,
            "optionName": option_name
        }
    
    def _build_column_metadata(self, column_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build column metadata yang lengkap sesuai format Superset.
        
        Args:
            column_info: Info kolom dari dataset
            
        Returns:
            Column metadata yang lengkap
        """
        return {
            "advanced_data_type": None,
            "certification_details": None,
            "certified_by": None,
            "column_name": column_info.get("column_name", ""),
            "description": column_info.get("description"),
            "expression": column_info.get("expression"),
            "filterable": column_info.get("filterable", True),
            "groupby": column_info.get("groupby", True),
            "id": column_info.get("id", hash(column_info.get("column_name", "")) % 10000),
            "is_certified": False,
            "is_dttm": column_info.get("is_dttm", False),
            "python_date_format": column_info.get("python_date_format"),
            "type": column_info.get("type", "VARCHAR"),
            "type_generic": column_info.get("type_generic", 1),
            "verbose_name": column_info.get("verbose_name"),
            "warning_markdown": None
        }
    
    def _generate_query_context(
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
            if viz_type in ["pie", "funnel"]:
                # PIE and FUNNEL charts: params menggunakan "metric" (singular), query_context menggunakan "metrics" (array)
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
                    
            elif viz_type in ["echarts_timeseries_line", "echarts_timeseries_bar", "echarts_area"]:
                # Timeseries and area charts membutuhkan struktur query yang khusus
                self._build_timeseries_query_context(query, params, dataset_selected)
                
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
    
    def _build_timeseries_query_context(
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
    
    async def _associate_chart_to_dashboard(
        self, 
        chart_id: int, 
        dashboard_id: int
    ) -> Dict[str, Any]:
        """
        Associate chart ke dashboard.
        
        Args:
            chart_id: ID chart yang baru dibuat
            dashboard_id: ID dashboard target
            
        Returns:
            Response dari API
        """
        try:
            logger.info(f"Associating chart {chart_id} to dashboard {dashboard_id}")
            
            # Get existing charts di dashboard
            dashboard = self.superset_client.get_dashboard(dashboard_id)
            existing_chart_ids = [chart["id"] for chart in dashboard.get("charts", [])]
            
            # Add new chart to list
            updated_chart_ids = existing_chart_ids + [chart_id]
            
            # Update dashboard
            result = self.superset_client.add_charts_to_dashboard(
                dashboard_id, updated_chart_ids
            )
            
            logger.info(f"Chart {chart_id} associated to dashboard {dashboard_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error associating chart to dashboard: {e}")
            raise ChartGeneratorError(f"Failed to associate chart to dashboard: {e}")
    
    def get_supported_chart_types(self) -> List[Dict[str, Any]]:
        """
        Get list chart types yang didukung dengan deskripsi.
        
        Returns:
            List chart types dengan metadata
        """
        chart_types = []
        for chart_type, config in CHART_CONFIGS.items():
            chart_types.append({
                "type": chart_type,
                "description": config.get("description", ""),
                "required_params": config.get("required_params", [])
            })
        
        return chart_types
    
    def validate_dataset_compatibility(
        self, 
        chart_type: str, 
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validasi kompatibilitas dataset dengan chart type.
        
        Args:
            chart_type: Jenis chart yang akan dibuat
            dataset_selected: Dataset yang dipilih
            
        Returns:
            Dictionary dengan status validasi
        """
        return self.instruction_builder.validate_chart_requirements(
            chart_type, dataset_selected
        )
    
    def preview_chart_config(
        self, 
        user_prompt: str, 
        dataset_selected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Preview konfigurasi chart tanpa membuat chart actual.
        
        Args:
            user_prompt: Prompt dari user
            dataset_selected: Dataset yang dipilih
            
        Returns:
            Preview konfigurasi chart
        """
        try:
            # Build instruksi
            messages = self.instruction_builder.build_complete_instruction(
                user_prompt, dataset_selected
            )
            
            # Generate config via AI (sync untuk preview)
            ai_response = self.model_client.generate_json(
                messages=messages,
                temperature=0.1,
                max_tokens=2000
            )
            
            if "error" in ai_response:
                return {"error": ai_response["error"]}
            
            # Validate response
            chart_config = self._validate_ai_response(ai_response, dataset_selected)
            
            return {
                "success": True,
                "preview": chart_config,
                "chart_type": chart_config.get("viz_type"),
                "slice_name": chart_config.get("slice_name")
            }
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            return {"error": str(e)}
    
    def close(self):
        """Clean up resources."""
        if hasattr(self, 'superset_client'):
            self.superset_client.close()
        logger.info("ChartGenerator service closed")