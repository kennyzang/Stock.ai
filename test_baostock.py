"""Quick BaoStock capability test."""
import baostock as bs

bs.login()

# Test 1: Daily - just count
print("=== DAILY ===")
rs = bs.query_history_k_data_plus("sh.600519", "date,open,high,low,close,volume",
    start_date="2024-01-01", end_date="2026-04-07", frequency="d", adjustflag="2")
d_cnt = 0
while rs.error_code == "0" and rs.next():
    d_cnt += 1
first_d = rs.get_row_data()
print(f"  2024~today: {d_cnt} daily bars")

rs = bs.query_history_k_data_plus("sh.600519", "date,open,high,low,close,volume",
    start_date="2020-01-01", end_date="2023-12-31", frequency="d", adjustflag="2")
d_old = 0
while rs.error_code == "0" and rs.next():
    d_old += 1
print(f"  2020~2023: {d_old} daily bars")

# Test 2: 5min - short range
print("\n=== 5-MIN ===")
for label, start, end in [
    ("Dec 2025 (1mo)", "2025-12-01", "2026-01-05"),
    ("Jun 2024 (1wk)",  "2024-06-03", "2024-06-10"),
    ("Jan 2023 (1wk)",  "2023-01-03", "2023-01-10"),
    ("Jun 2022 (1wk)",  "2022-06-06", "2022-06-13"),
]:
    rs = bs.query_history_k_data_plus("sh.600519", "date,time,open,high,low,close,volume",
        start_date=start, end_date=end, frequency="5", adjustflag="2")
    cnt = 0
    sample = None
    while rs.error_code == "0" and rs.next():
        cnt += 1
        if sample is None:
            sample = rs.get_row_data()[:7]
    print(f"  {label}: {cnt} bars | {sample}")

# Test 3: Multiple stocks 5min
print("\n=== 5-MIN MULTI-STOCK ===")
for code, name in [("sz.000001", "平安银行"), ("sz.002594", "比亚迪"), ("sh.601857", "中国石油")]:
    rs = bs.query_history_k_data_plus(code, "date,time,open,high,low,close,volume",
        start_date="2026-04-02", end_date="2026-04-03", frequency="5", adjustflag="2")
    cnt = 0
    while rs.error_code == "0" and rs.next():
        cnt += 1
    print(f"  {name}: Apr 2-3 → {cnt} bars ({cnt//2} per day)")

# Test 4: Weekly for Layer1
print("\n=== WEEKLY (Layer1 needs ~52 weeks) ===")
rs = bs.query_history_k_data_plus("sh.600519", "date,open,high,low,close,volume",
    start_date="2023-01-01", end_date="2026-04-07", frequency="w", adjustflag="2")
w_cnt = 0
first_w = last_w = None
while rs.error_code == "0" and rs.next():
    w_cnt += 1
    row = rs.get_row_data()
    if first_w is None:
        first_w = row[0]
    last_w = row[0]
print(f"  2023~today: {w_cnt} weeks | {first_w} -> {last_w}")

bs.logout()
print("\nDone.")
