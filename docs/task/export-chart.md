Aturan Development :

- jika ada perubahan atau penyesuaian dan untuk code nya memang di luar file terkait bisa buat folder dan file baru agar lebih rapih dan bisa di baca dan tidak terlalu panjang kode nya
- jika dalam menuliskan kode terdapat text panjang dan bisa membuat kode menjadi panjang dan sulit untuk di baca maka baca apakah sudah ada data constant/json yang sudah ada dan bisa mengcover mekanisme yang ada maka gunakan jikda tidak ada maka buat file constant saja.

swagger doc untuk GET /chart/export/ superset versi terbaru
http://localhost:8088/api/v1/chart/export/?q=!(747)&token=ic64cnkhI4ByRoFssJAFm
curl -X 'GET' \
 'http://localhost:8088/api/v1/chart/export/?q=%5B%22747%22%5D' \
 -H 'accept: application/zip'

Buat Sebuah /services/chart_exporter
untuk mekanisme export chart

analisa untuk routes_generate
->
setelah prosess create chart berhasil
->
prosess export chart hasil create chart
->
simpan hasil export di folder cache/chart_export/ dengan nama file {chart_id}.zip
->
setelah di simpan export chart nya ekstrak file zip nya
