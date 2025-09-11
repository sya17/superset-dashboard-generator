superset

Dataset
Loan Order Query Dataset :
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

Saving Account Query Dataset :
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

contoh prompt:
Buatkan sebuah Chart dengan description seperti berikut:

- tipe chart: echarts_timeseries_line
- dengan dataset: saving account
- dengan time axis column: active_date
- dengan time grain: week
- dengan Contribution Mode Series
- dengan metrics: SUM dari column saldo
- dengan dimension groupby: product_name
- dengan row limit: 1000
- nama chart: Trend Pertumbuhan Saldo

Bisa Berikan saya contoh prompt yang cocok untuk dataset di atas
untuk type chart sesuaikan dengan biasa pembuatan chart untuk user umum
