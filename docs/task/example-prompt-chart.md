Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: echarts_timeseries_line
- dengan dataset: saving account
- dengan time axis column: active_date
- dengan time grain: month
- dengan metrics: SUM dari column saldo
- dengan dimension groupby: product_name
- dengan row limit: 1000
- nama chart: Trend Pertumbuhan Saldo per Produk

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Pie Chart
- dengan dataset: saving account
- dengan dimension column: type_product
- dengan metrics: SUM dari column saldo
- dengan row limit: 1000
- nama chart: Komposisi Saldo Berdasarkan Jenis Tabungan

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Bar Chart
- dengan dataset: saving account
- dengan dimension column: debitur_name
- dengan metrics: SUM dari column saldo
- dengan row limit: 20
- nama chart: Top 20 Debitur Berdasarkan Saldo

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: echarts_timeseries_bar
- dengan dataset: loan order
- dengan time axis column: order_date
- dengan time grain: month
- dengan metrics: SUM dari column loan_amount
- dengan row limit: 1000
- nama chart: Total Pinjaman per Bulan

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Pie Chart
- dengan dataset: loan order
- dengan dimension column: order_status
- dengan metrics: COUNT dari column order_no
- dengan row limit: 1000
- nama chart: Komposisi Status Order Pinjaman

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: echarts_timeseries_line
- dengan dataset: loan order
- dengan time axis column: order_date
- dengan time grain: quarter
- dengan metrics:
  - AVG dari column down_payment
  - AVG dari column loan_amount
- dengan row limit: 1000
- nama chart: Perbandingan Rata-rata DP dan Pinjaman
