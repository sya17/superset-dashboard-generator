- Collateral Information
  select
  colla.colla_id as id_jaminan,
  colla.colla_no as nomor_jaminan,
  colla.colla_type_id as id_tipe_jaminan,
  cmt.colla_agunan as nama_tipe_jaminan,
  colla.colla_bpid as id_nasabah,
  bp.bizpartner_fullname as nama_nasabah,
  colla.colla_ownership_nameon as nama_pemilik,
  colla.colla_physical_addr as alamat_jaminan,
  colla.colla_kabkotaid as id_kota,
  city.city_name as nama_kota,
  colla.colla_doc_no as nomor_dokumen,
  colla.colla_doc_issuer as penerbit_dokumen,
  colla.colla_doc_recvdate as tanggal_terima_dokumen,
  colla.colla_is_insured as status_asuransi,
  colla.colla_created_date as tanggal_dibuat,
  colla.colla_updated_date as tanggal_diubah,
  colla.colla_created_by as dibuat_oleh,
  colla.colla_updated_by as diubah_oleh
  from coll_collaterals colla
  left join coll_mst_types cmt
  on cmt.colla_type_id = colla.colla_type_id
  left join mst_bizpartner bp
  on bp.bizpartner_id = colla.colla_bpid
  left join mst_kabkota city
  on city.city_id = colla.colla_kabkotaid
  where 1=1;

- Saving Account
  select
  savtrn_acct_no as account_no,
  savtrn_active_date as active_date,
  savtrn_acct_name as account_name,
  mb.bizpartner_fullname as debitur_name,
  smp.savprd_name as product_name,
  "cryptoutil.decrypttonumeric"(sta.savtrn_curr_balance, 'KeepTh1sS3cr3t!@') as saldo,
  (case smp.savprd_saving_type
  when 1 then 'REGULER'
  when 2 then 'CHECKING'
  when 3 then 'DEPOSITO'
  when 4 then 'RENCANA'
  when 5 then 'SIMPANAN POKOK'
  when 6 then 'SIMPANAN WAJIB'
  else ''
  end) as type_product
  from sav_trn_accounts sta
  left join sav_mst_products smp on smp.savprd_id = sta.savtrn_prod_id
  left join mst_bizpartner mb on mb.bizpartner_id = sta.savtrn_bp_id
  where 1=1
  and sta.savtrn_curr_status = 'A'

- Loan Order
  select
  lord.lord_order_no as order_no,
  lord.lord_created_date as created_date,
  lord.lord_date as order_date,
  bp.bizpartner_fullname as customer_name,
  lmp.loanprd_name as product_name,
  lord.lord_loan_amt as loan_amount,
  lord.lord_net_dp as down_payment,
  lord.lord_install_amt as installment_amount,
  lord.lord_jml_angs as installment_count,
  lord.lord_jarak_angs as installment_interval,
  lord.lord_int_or_margin as interest_margin,
  (case lord.lord_order_sts
  when 'N' then 'DRAFT'
  when 'A' then 'ACTIVE'
  when 'S' then 'SUBMIT'
  when 'R' then 'REJECTED'
  when 'C' then 'CANCELLED'
  else lord.lord_order_sts
  end) as order_status,
  lord.lord_currency as currency
  from loan_trn_orders lord
  left join mst_bizpartner bp on bp.bizpartner_id = lord.lord_bpartner_id
  left join loan_mst_products lmp on lmp.loanprd_id = lord.lord_prod_id
