"""
Chart Generator Constants
Berisi konfigurasi dan konstanta untuk berbagai jenis chart Superset.
"""

from typing import Dict, List, Any

# Chart types yang didukung sesuai dengan swagger doc
CHART_TYPES = [
    "echarts_timeseries_bar",
    "big_number", 
    "big_number_total",
    "echarts_funnel",
    "echarts_gauge", 
    "pie",
    "pivot_table_v2",
    "table",
    "echarts_treemap",
    "mixed_timeseries",
    "echarts_timeseries_area",
    "echarts_timeseries_line", 
    "echarts_timeseries_scatter",
    "echarts_timeseries_smooth",
    "echarts_timeseries_step",
    "echarts_graph",
    "echarts_radar",
    "echarts_sankey",
    "echarts_tree"
]

# Konfigurasi default untuk setiap jenis chart
CHART_CONFIGS = {
    "pie": {
        "viz_type": "pie",
        "required_params": ["groupby", "metric"],
        "default_params": {
            "adhoc_filters": [],
            "color_scheme": "d3Category20c",
            "datasource": "",
            "granularity_sqla": "",
            "groupby": [],
            "innerRadius": 30,
            "metric": "count(*)",
            "outerRadius": 300,
            "row_limit": 50,
            "show_labels": True,
            "show_legend": True,
            "show_values": True,
            "sort_by_metric": True
        },
        "description": "Chart lingkaran untuk menampilkan proporsi data kategorik"
    },
    
    "table": {
        "viz_type": "table", 
        "required_params": ["groupby"],
        "default_params": {
            "adhoc_filters": [],
            "all_columns": [],
            "datasource": "",
            "granularity_sqla": "",
            "groupby": [],
            "metrics": [],
            "order_by_cols": [],
            "row_limit": 1000,
            "show_totals": True,
            "table_timestamp_format": "%Y-%m-%d %H:%M:%S"
        },
        "description": "Tabel untuk menampilkan data dalam format tabular"
    },
    
    "echarts_timeseries_bar": {
        "viz_type": "echarts_timeseries_bar",
        "required_params": ["x_axis", "metrics"],
        "default_params": {
            "adhoc_filters": [],
            "datasource": "",
            "granularity_sqla": "",
            "x_axis": "",
            "metrics": [],
            "row_limit": 10000,
            "sort_by": "",
            "x_axis_sort_asc": True,
            "y_axis_format": "",
            "show_legend": True,
            "rich_tooltip": True,
            "show_controls": True
        },
        "description": "Bar chart berbasis waktu menggunakan ECharts"
    },
    
    "echarts_timeseries_line": {
        "viz_type": "echarts_timeseries_line",
        "required_params": ["x_axis", "metrics"],
        "default_params": {
            "adhoc_filters": [],
            "datasource": "",
            "granularity_sqla": "",
            "x_axis": "",
            "metrics": [],
            "row_limit": 10000,
            "sort_by": "",
            "x_axis_sort_asc": True,
            "y_axis_format": "",
            "show_legend": True,
            "rich_tooltip": True,
            "show_controls": True,
            "line_interpolation": "linear"
        },
        "description": "Line chart berbasis waktu menggunakan ECharts"
    },
    
    "big_number": {
        "viz_type": "big_number",
        "required_params": ["metrics"],
        "default_params": {
            "adhoc_filters": [],
            "datasource": "",
            "granularity_sqla": "",
            "metrics": ["count(*)"],
            "subheader": "",
            "y_axis_format": "",
            "force_categorical": False
        },
        "description": "Menampilkan satu angka besar sebagai KPI"
    },
    
    "big_number_total": {
        "viz_type": "big_number_total",
        "required_params": ["metrics"],
        "default_params": {
            "adhoc_filters": [],
            "datasource": "",
            "granularity_sqla": "",
            "metrics": ["count(*)"],
            "subheader": "",
            "y_axis_format": "",
            "force_categorical": False
        },
        "description": "Menampilkan total agregat sebagai angka besar"
    },
    
    "echarts_funnel": {
        "viz_type": "echarts_funnel",
        "required_params": ["groupby", "metrics"],
        "default_params": {
            "adhoc_filters": [],
            "datasource": "",
            "granularity_sqla": "",
            "groupby": [],
            "metrics": ["count(*)"],
            "row_limit": 50,
            "sort_by_metric": True,
            "label_type": "key_value"
        },
        "description": "Funnel chart untuk menampilkan alur konversi"
    }
}

# Template instruksi AI untuk berbagai jenis chart
AI_INSTRUCTIONS_TEMPLATE = {
    "system_role": """Anda adalah AI Data Analyst Expert untuk Apache Superset yang mampu menganalisis permintaan user dan menghasilkan konfigurasi chart yang tepat.

CORE MISSION: Buat konfigurasi chart Superset yang akurat berdasarkan:
1. Analisis INTENT dari user prompt
2. Analisis STRUKTUR dataset yang tersedia  
3. Pemilihan VISUALISASI yang optimal
4. Generate KONFIGURASI sesuai Superset API terbaru

ANALYTICAL APPROACH:
🔍 LANGKAH 1 - ANALISIS PROMPT:
- Identifikasi kata kunci: distribusi, trend, perbandingan, total, ranking, dll
- Tentukan fokus analisis: kategorikal, numerikal, temporal, atau relasional
- Pahami output yang diinginkan: overview, detail, atau insight spesifik

🔍 LANGKAH 2 - ANALISIS DATASET:
- Evaluasi tipe kolom: string/categorical, numeric, date/time
- Identifikasi primary dimensions (untuk groupby)
- Identifikasi measure columns (untuk metrics)
- Pertimbangkan kardinalitas dan distribusi data

🔍 LANGKAH 3 - CHART TYPE SELECTION:
Pilih berdasarkan kombinasi intent + data structure:
- Distribusi kategorikal → pie, bar
- Trend temporal → timeseries_line, timeseries_bar  
- Perbandingan → bar, table
- KPI/Metrics → big_number
- Relasi/Flow → funnel, sankey

🔍 LANGKAH 4 - SMART CONFIGURATION:
- Gunakan kolom yang paling relevan dengan prompt
- Sesuaikan aggregation dengan jenis analisis
- Optimalkan parameter untuk readability

TECHNICAL REQUIREMENTS:
✅ OUTPUT FORMAT: JSON sesuai Superset POST /chart/ API
✅ REQUIRED FIELDS: viz_type, slice_name, datasource_id, datasource_type, params
✅ METRICS: gunakan format yang valid dan sesuai dengan Superset versi terbaru
✅ NO INVALID FIELDS: dataset_id, table_name, datasource_name

ADAPTIVE INTELLIGENCE:
- Jika prompt ambigu → pilih chart type yang paling informatif untuk data
- Jika kolom tidak eksplisit → gunakan kolom yang paling logis
- Jika metrics tidak spesifik → gunakan aggregation yang meaningful
- Selalu prioritaskan user intent over rigid rules""",
    
    "user_prompt_template": """📊 DATASET CONTEXT:
{dataset_info}

🎯 USER REQUEST: "{user_prompt}"

📈 AVAILABLE VISUALIZATIONS: {available_chart_types}

💡 ANALYSIS FRAMEWORK:

1️⃣ INTENT ANALYSIS:
   - Apa yang ingin ditampilkan dari prompt ini?
   - Apakah fokus pada: distribusi, perbandingan, trend, atau total?
   - Target audience: executive summary atau detailed analysis?

2️⃣ DATA MAPPING:
   - Kolom mana yang sesuai untuk groupby/dimensions?
   - Kolom mana yang cocok untuk metrics/measures?  
   - Apakah ada filter atau kondisi khusus?

3️⃣ VISUALIZATION CHOICE:
   - Chart type apa yang paling efektif untuk intent + data ini?
   - Parameter apa saja yang perlu dikustomisasi?

4️⃣ CONFIGURATION:
   - slice_name: deskriptif dan informatif
   - datasource_id: gunakan dari dataset info
   - params: sesuai chart type yang dipilih
   - metrics: gunakan format SIMPLE dengan column metadata lengkap sesuai Superset standard

🎯 OUTPUT: Generate valid Superset chart JSON configuration.


RESPOND WITH JSON ONLY - NO EXPLANATIONS."""
}

# EXAMPLE DYNAMIC RESPONSES:

# Prompt: "Buat pie chart distribusi produk"
# → Analisis: distribusi kategorikal
# → Chart: pie dengan groupby=kategori_produk, metrics=count(*)

# Prompt: "Tampilkan trend penjualan bulanan"  
# → Analisis: trend temporal
# → Chart: timeseries_line dengan x_axis=bulan, metrics=sum(penjualan)

# Prompt: "Top 10 customer dengan revenue tertinggi"
# → Analisis: ranking + perbandingan
# → Chart: bar dengan groupby=customer, metrics=sum(revenue), limit=10

# Mapping keyword ke chart type untuk deteksi otomatis
CHART_TYPE_KEYWORDS = {
    "pie": ["pie", "lingkaran", "proporsi", "persentase", "bagian"],
    "table": ["table", "tabel", "list", "daftar", "data mentah"],
    "echarts_timeseries_bar": ["bar", "batang", "kolom", "histogram", "waktu"],
    "echarts_timeseries_line": ["line", "garis", "trend", "tren", "perkembangan"],
    "big_number": ["big number", "angka besar", "kpi", "total", "jumlah"],
    "echarts_funnel": ["funnel", "corong", "konversi", "alur"],
    "echarts_gauge": ["gauge", "speedometer", "meter", "indikator"],
    "pivot_table_v2": ["pivot", "cross tab", "tabulasi silang"],
    "echarts_treemap": ["treemap", "hierarchy", "hierarki"],
    "echarts_radar": ["radar", "spider", "laba-laba"]
}

# Default query context untuk chart
DEFAULT_QUERY_CONTEXT = {
    "datasource": {
        "id": None,
        "type": "table"
    },
    "force": False,
    "queries": [
        {
            "time_range": "No filter",
            "granularity": "ds",
            "filters": [],
            "extras": {
                "having": "",
                "where": ""
            },
            "applied_time_extras": {},
            "columns": [],
            "metrics": [],
            "orderby": [],
            "annotation_layers": [],
            "row_limit": 10000,
            "timeseries_limit": 0,
            "order_desc": True,
            "url_params": {},
            "custom_params": {},
            "custom_form_data": {}
        }
    ],
    "result_format": "json",
    "result_type": "full"
}