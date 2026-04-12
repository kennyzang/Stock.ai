import baostock as bs, sys
bs.login()
rs = bs.query_history_k_data_plus("sh.600519","date,open,high,low,close,volume",
    start_date="2024-06-03",end_date="2024-06-07",frequency="5",adjustflag="2")
c=0
while rs.error_code=="0" and rs.next():
    c+=1
    if c<=2: print(rs.get_row_data())
print(f"TOTAL_5MIN_JUN2024={c}")
bs.logout()
