"""
Metric Builder
Handles enhancement and building of metric objects with proper column metadata.
"""

import hashlib
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MetricBuilder:
    """Builder untuk metric objects dengan column metadata yang lengkap."""
    
    def enhance_metric_with_column_metadata(
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
                            return self.build_metric_object("COUNT", first_col, f"COUNT({first_col.get('column_name', 'id')})")
                    else:
                        # count(column_name) - cari column yang sesuai
                        columns = dataset_selected.get('columns', [])
                        for col in columns:
                            if col.get('column_name') == col_match:
                                return self.build_metric_object("COUNT", col, f"COUNT({col_match})")
            elif metric.startswith("sum"):
                col_match = metric[metric.find("(")+1:metric.find(")")]
                columns = dataset_selected.get('columns', [])
                for col in columns:
                    if col.get('column_name') == col_match:
                        return self.build_metric_object("SUM", col, f"SUM({col_match})")
            elif metric.startswith("avg"):
                col_match = metric[metric.find("(")+1:metric.find(")")]
                columns = dataset_selected.get('columns', [])
                for col in columns:
                    if col.get('column_name') == col_match:
                        return self.build_metric_object("AVG", col, f"AVG({col_match})")
            
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
                    return self.build_metric_object(aggregate, column_info, label)
                
                # Just enhance column metadata if missing id
                column = metric["column"]
                if "id" not in column:
                    # Enhance dengan column metadata dari dataset
                    column_name = column.get("column_name", "")
                    columns = dataset_selected.get('columns', [])
                    for col in columns:
                        if col.get('column_name') == column_name:
                            # Update column dengan metadata lengkap
                            enhanced_column = self.build_column_metadata(col)
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
                                    return self.build_metric_object(aggregate, col, label)
                    
                    # Fallback - gunakan kolom pertama
                    columns = dataset_selected.get('columns', [])
                    if columns:
                        first_col = columns[0]
                        return self.build_metric_object(aggregate, first_col, label)
                
                return metric
        
        # Fallback default
        columns = dataset_selected.get('columns', [])
        if columns:
            first_col = columns[0]
            return self.build_metric_object("COUNT", first_col, f"COUNT({first_col.get('column_name', 'id')})")
        
        return {"expressionType": "SQL", "sqlExpression": "count(*)", "label": "COUNT(*)"}
    
    def build_metric_object(self, aggregate: str, column_info: Dict[str, Any], label: str) -> Dict[str, Any]:
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
        hash_input = f"{label}_{int(time.time())}"
        hash_object = hashlib.md5(hash_input.encode())
        hash_hex = hash_object.hexdigest()
        option_name = f"metric_{hash_hex[:10]}_{hash_hex[10:23]}"
        
        return {
            "expressionType": "SIMPLE",
            "column": self.build_column_metadata(column_info),
            "aggregate": aggregate.upper(),
            "sqlExpression": None,
            "datasourceWarning": False,
            "hasCustomLabel": False,
            "label": label,
            "optionName": option_name
        }
    
    def build_column_metadata(self, column_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build column metadata yang lengkap sesuai format Superset.
        
        Args:
            column_info: Info kolom dari dataset
            
        Returns:
            Column metadata yang lengkap
        """
        # Fix: Ensure column_name is never empty - use id as fallback
        column_name = column_info.get("column_name")
        if not column_name:
            column_name = column_info.get("id", "unknown_column")
        
        return {
            "advanced_data_type": None,
            "certification_details": None,
            "certified_by": None,
            "column_name": column_name,
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