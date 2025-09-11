Aturan Development :

- jika ada perubahan atau penyesuaian dan untuk code nya memang di luar file terkait bisa buat folder dan file baru agar lebih rapih dan bisa di baca dan tidak terlalu panjang kode nya
- jika dalam menuliskan kode terdapat text panjang dan bisa membuat kode menjadi panjang dan sulit untuk di baca maka baca apakah sudah ada data constant/json yang sudah ada dan bisa mengcover mekanisme yang ada maka gunakan jikda tidak ada maka buat file constant saja.

swagger doc untuk POST /chart/ superset versi terbaru
{
"cache_timeout": 0,
"certification_details": "string",
"certified_by": "string",
"dashboards": [
0
],
"datasource_id": 0,
"datasource_name": "string",
"datasource_type": "table",
"description": "string",
"external_url": "string",
"is_managed_externally": true,
"owners": [
0
],
"params": "string",
"query_context": "string",
"query_context_generation": true,
"slice_name": "string",
"viz_type": [
"echarts_timeseries_bar",
"big_number",
"big_number_total",
"funnel",
"echarts_gauge",
"pie",
"pivot_table_v2",
"table",
"echarts_treemap",
"mixed_timeseries",
"echarts_area",
"echarts_timeseries_line",
"echarts_timeseries_scatter",
"echarts_timeseries_smooth",
"echarts_timeseries_step",
"echarts_graph",
"echarts_radar",
"echarts_sankey",
"echarts_tree"
]
}

Buat Sebuah /services/chart_generator
untuk mekanisme generate chart

flow:

contoh prompt user : "Buat Dashboard Pie Simpanan status"
dataset_selected hasil dari dataset_selector
nanti nya di panggil di routes generator setelah prosess dataset selector
->
build intruksi untuk model AI (sesuaikan untuk menjadikan model AI tersebut adalah data analis dashboard enginer superset versi terbaru)
dengan mencantumkan detail dataset hasil dataset_selector
untuk aturan/setting pembuatan chart sesuaikan dengan type chart yang di gunakan dengan aturan/setting versi superset terbaru, sesuaikan untuk detail seperti x-axis, x-axis sorty by, y-axis, Dimension, metrics, Percentage metrics, filters, row limit , sort, Sort query by, sort-x-axis, sort-y-axis, series limit, Truncate Metric, Show empty columns
berikut contoh swagger create /chart
dan masukan contoh swagger doc post /chart/ (jika di perlukan)
\*\* sesuaikan agar nanti nya dynamic
->
model AI memprosess dari intruksi hasil build dan user_prompt(dari parameter yang nanti di panggil di flow lain)
->
result merupakan format seperti swagger doc post /chart/ setting untuk create chart yang relevan dan akurat dari user_prompt yang di berikan
->
create chart menggunakan superset client POST /chart/
