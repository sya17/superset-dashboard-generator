Aturan Development :

- jika ada perubahan atau penyesuaian dan untuk code nya memang di luar file terkait bisa buat folder dan file baru agar lebih rapih dan bisa di baca dan tidak terlalu panjang kode nya
- jika dalam menuliskan kode terdapat text panjang dan bisa membuat kode menjadi panjang dan sulit untuk di baca maka baca apakah sudah ada data constant/json yang sudah ada dan bisa mengcover mekanisme yang ada maka gunakan jikda tidak ada maka buat file constant saja.

Buat Sebuah /services/dataset_selector
untuk mekanisme menentukan dataset menggunakan Prosess Model AI

flow
get_datsets dari superset client
->
build intruksi untuk model AI (sesuaikan untuk menjadikan model AI tersebut adalah data analis dashboard enginer superset versi terbaru)
dengan mencantumkan dataset hasil get tersebut dan buat agar lebih ringkas seperti contoh atau bisa lebih baik :
sav_trn_accounts: - savtrn_acct_id - savtrn_acct_active_date
->
model AI memprosess dari intruksi hasil build dan user_prompt(dari parameter yang nanti di panggil di flow lain)
->
result merupakan dataset yang relevan dan akurat dari user_prompt yang di berikan
