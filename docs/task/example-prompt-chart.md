DATASET SAVING
Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Pie Chart
- dengan dataset: saving account
- dengan dimension column: type_product
- dengan metrics: SUM dari column saldo
- dengan row limit: 1000
- nama chart: Komposisi Saldo Berdasarkan Jenis Tabungan

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Donut Chart
- dengan dataset: saving account
- dengan dimension column: product_name
- dengan metrics: SUM dari column saldo
- dengan row limit: 1000
- nama chart: Komposisi Saldo per Produk

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: line
- dengan dataset: saving account
- dengan time axis column: active_date
- dengan time grain: month
- dengan metrics: SUM dari column saldo
- dengan dimension groupby: product_name
- dengan row limit: 1000
- nama chart: Trend Pertumbuhan Saldo per Produk

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Bar Chart
- dengan dataset: saving account
- dengan dimension column: debitur_name
- dengan metrics: SUM dari column saldo
- dengan row limit: 20
- nama chart: Top 20 Debitur Berdasarkan Saldo

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: area
- dengan dataset: saving account
- dengan time axis column: active_date
- dengan time grain: month
- dengan metrics: SUM dari column saldo
- dengan dimension groupby: product_name
- dengan row limit: 1000
- nama chart: Area Pertumbuhan Saldo per Produk

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Funnel Chart
- dengan dataset: saving account
- dengan dimension column: product_name
- dengan metrics: SUM dari column saldo
- dengan row limit: 1000
- nama chart: Funnel Distribusi Saldo per Produk

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: big number total
- dengan dataset: saving account
- dengan metrics: SUM dari column saldo
- nama chart: Total Seluruh Saldo Tabungan

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: big number
- dengan dataset: saving account
- dengan time axis column: active_date
- dengan time grain: month
- dengan metrics: SUM dari column saldo
- nama chart: Trend Total Saldo Tabungan

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Table
- dengan dataset: saving account
- query mode: aggregate
- dengan dimension column: product_name
- dengan metrics: SUM dari column saldo
- dengan row limit: 1000
- nama chart: Total Saldo per Produk

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Table
- dengan dataset: saving account
- query mode: raw
- dengan columns: account_no, account_name, debitur_name, product_name, saldo, type_product, active_date
- dengan row limit: 1000
- nama chart: Daftar Rekening Tabungan

===================================================================================
LOAN
Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Pie Chart
- dengan dataset: loan order
- dengan dimension column: order_status
- dengan metrics: COUNT dari column order_no
- dengan row limit: 1000
- nama chart: Komposisi Status Order Pinjaman

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Pie Chart
- dengan dataset: loan order
- dengan dimension column: product_name
- dengan metrics: SUM dari column loan_amount
- dengan row limit: 1000
- format: donut
- nama chart: Komposisi Pinjaman per Produk

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: line
- dengan dataset: loan order
- dengan time axis column: order_date
- dengan time grain: month
- dengan metrics: SUM dari column loan_amount
- dengan row limit: 1000
- nama chart: Trend Total Pinjaman Bulanan

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Bar Chart
- dengan dataset: loan order
- dengan dimension column: customer_name
- dengan metrics: SUM dari column loan_amount
- dengan row limit: 20
- nama chart: Top 20 Customer Pinjaman

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: area
- dengan dataset: loan order
- dengan time axis column: order_date
- dengan time grain: month
- dengan metrics: SUM dari column loan_amount
- dengan dimension groupby: product_name
- dengan row limit: 1000
- nama chart: Area Pertumbuhan Pinjaman per Produk

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Funnel Chart
- dengan dataset: loan order
- dengan dimension column: order_status
- dengan metrics: COUNT dari column order_no
- dengan row limit: 1000
- nama chart: Funnel Distribusi Status Order

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: big number total
- dengan dataset: loan order
- dengan metrics: SUM dari column loan_amount
- nama chart: Total Seluruh Pinjaman

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: big number
- dengan dataset: loan order
- dengan time axis column: order_date
- dengan time grain: month
- dengan metrics: SUM dari column loan_amount
- nama chart: Trend Total Pinjaman Bulanan

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Table
- dengan dataset: loan order
- query mode: aggregate
- dengan dimension column: order_status
- dengan metrics: SUM dari column loan_amount
- dengan row limit: 1000
- nama chart: Total Pinjaman per Status Order

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Table
- dengan dataset: loan order
- query mode: raw
- dengan columns: order_no, order_date, customer_name, product_name, loan_amount, down_payment, installment_amount, installment_count, interest_margin, order_status, currency
- dengan row limit: 1000
- nama chart: Daftar Order Pinjaman

===================================================================================
COLLATERAL

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Pie
- dengan dataset: collateral
- dengan dimension column: nama_tipe_jaminan
- dengan metrics: COUNT dari column id_jaminan
- dengan row limit: 1000
- nama chart: Distribusi Jaminan per Tipe

---

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Donut
- dengan dataset: collateral
- dengan dimension column: nama_kota
- dengan metrics: COUNT dari column id_jaminan
- dengan row limit: 1000
- nama chart: Distribusi Jaminan per Kota

---

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: line
- dengan dataset: collateral
- dengan time axis column: tanggal_dibuat
- dengan time grain: month
- dengan metrics: COUNT dari column id_jaminan
- dengan dimension groupby: nama_tipe_jaminan
- dengan row limit: 1000
- nama chart: Trend Penambahan Jaminan per Tipe

---

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Bar
- dengan dataset: collateral
- dengan dimension column: nama_nasabah
- dengan metrics: COUNT dari column id_jaminan
- dengan row limit: 20
- nama chart: Top 20 Nasabah dengan Jumlah Jaminan Terbanyak

---

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: area
- dengan dataset: collateral
- dengan time axis column: tanggal_dibuat
- dengan time grain: month
- dengan metrics: COUNT dari column id_jaminan
- dengan dimension groupby: nama_kota
- dengan row limit: 1000
- nama chart: Area Pertumbuhan Jaminan per Kota

---

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Funnel
- dengan dataset: collateral
- dengan dimension column: status_asuransi
- dengan metrics: COUNT dari column id_jaminan
- dengan row limit: 1000
- nama chart: Funnel Status Asuransi Jaminan

---

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Big Number Total
- dengan dataset: collateral
- dengan metrics: COUNT dari column id_jaminan
- nama chart: Total Jaminan

---

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Big Number with Trendline
- dengan dataset: collateral
- dengan time axis column: tanggal_dibuat
- dengan metrics: COUNT dari column id_jaminan
- nama chart: Pertumbuhan Jaminan

---

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Table
- dengan dataset: collateral
- query mode: aggregate
- dengan groupby: nama_tipe_jaminan, nama_kota
- dengan metrics: COUNT dari column id_jaminan
- dengan row limit: 1000
- nama chart: Ringkasan Jaminan per Tipe dan Kota

---

Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: Table
- dengan dataset: collateral
- query mode: raw
- dengan columns: id_jaminan, nomor_jaminan, nama_tipe_jaminan, nama_nasabah, nama_pemilik, alamat_jaminan, nama_kota, nomor_dokumen, penerbit_dokumen, tanggal_terima_dokumen, status_asuransi, tanggal_dibuat, tanggal_diubah, dibuat_oleh, diubah_oleh
- dengan row limit: 1000
- nama chart: Daftar Detail Jaminan
