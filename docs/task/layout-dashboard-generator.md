Aturan Development :

- jika ada perubahan atau penyesuaian dan untuk code nya memang di luar file terkait bisa buat folder dan file baru agar lebih rapih dan bisa di baca dan tidak terlalu panjang kode nya
- jika dalam menuliskan kode terdapat text panjang dan bisa membuat kode menjadi panjang dan sulit untuk di baca maka baca apakah sudah ada data constant/json yang sudah ada dan bisa mengcover mekanisme yang ada maka gunakan jikda tidak ada maka buat file constant saja.

hasil export chart berada di

- /cache/chart_export/{chart_id}.zip
- /cache/chart_export/{chart_id}\_extracted/

buat sebuah /services/layout_dashboard_generator

user prompt example :
"Buatkan Dashboard dengan 3 chart:

1. Bar Chart: dataset loan_order, dimension product_name, metrics COUNT(\*), limit 500
2. Line Chart: dataset loan_order, dimension order_date, metrics SUM loan_amount
3. Pie Chart: dataset loan_order, dimension region, metrics SUM loan_amount
   "
   \*\* Notes Combinasi dari contoh prompt chart di docs/task/example-prompt-chart.md

->
Lakukan prosess pemecahan untuk user prompt baru, yaitu untuk mendapatkan chart apa saja yang akan di buat
->
Lakuakn prosess exsiting chart generation tapi dengan improvement dengan menjadi beberapa kali prosess chart generation berdasarkan user prompt pattern baru dan menghasilkan result list chart hasil generate.
->
mekanisme preparation layout dashboard yang cocok untuk list dashboard yang berhasil di buat dan availabel di superset.
->
build instruction untuk merancang layout dashboard dengan membuat sebuah yaml baru di
/cache/chart_export/{chart_id}\_extracted/dashboards/{id_dashboard}\_dashboard.yaml
->
setelah berhasil membuat yaml layout dashboard maka lakukan prosess compress ke zip di /cache/dashboard_import/{dashboard_id}\_nama_dashboard.zip
->
setelah berhasil membuat zip import dashboard maka lakukan prosess import dashboard ke superset
