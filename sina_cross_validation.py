"""
Cross-validation: Tencent Daily vs Sina 60min (1-hour) K-line alignment.
Since NetEase is down (502), test if Sina 60min can serve as Layer1 data source.
Also test: Sina 5min derived daily vs Sina 60min derived daily (internal consistency).
"""
import urllib.request, json, io, csv
from collections import defaultdict
from datetime import datetime

_proxy_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
urllib.request.install_opener(_proxy_opener)

TEST_STOCKS = [
    ("贵州茅台", "600519", "sh600519"),
    ("平安银行", "000001", "sz000001"),
    ("比亚迪",   "002594", "sz002594"),
]

TEST_DATES = [
    "2026-04-03", "2026-04-02", "2026-04-01",
    "2026-03-31", "2026-02-28", "2026-01-23",
    "2025-12-31", "2025-11-28", "2025-10-31",
]


def fetch_tencent_daily(tencent_code: str, start: str, end: str):
    """Tencent daily K-line (current Layer1 source)."""
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tencent_code},day,,,500,qfq"
    try:
        with _proxy_opener.open(url, timeout=15) as r:
            payload = json.loads(r.read().decode())
        data = payload.get("data", {}).get(tencent_code, {})
        rows = data.get("qfqday") or data.get("day") or []
        result = []
        for row in rows:
            if len(row) >= 6:
                result.append({
                    'date': str(row[0]).replace('-', '')[:10],
                    'open': float(row[1]), 'close': float(row[2]),
                    'high': float(row[3]), 'low': float(row[4]),
                    'volume': float(row[5]),
                })
        return [r for r in result if start.replace('-','') <= r['date'] <= end.replace('-','')]
    except Exception as e:
        print(f"  Tencent error: {e}")
        return []


def fetch_sina_bars(sina_code: str, scale: str, num_bars: int = 2000):
    """Fetch Sina bars at given scale."""
    url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina_code}&scale={scale}&ma=no&datalen={num_bars}"
    try:
        with _proxy_opener.open(url, timeout=20) as r:
            raw = r.read().decode()
        if not raw.strip() or 'null' in raw.lower():
            return []
        data = json.loads(raw)
        return [{'day': b['day'], 'open': float(b['open']), 'high': float(b['high']),
                 'low': float(b['low']), 'close': float(b['close']), 'volume': float(b['volume'])}
                for b in data]
    except Exception as e:
        print(f"  Sina error scale={scale}: {e}")
        return []


def group_bars_to_daily(bars, date_only=True):
    """Group minute/hourly bars into daily OHLCV."""
    groups = defaultdict(list)
    for bar in bars:
        day_key = bar['day'].split(' ')[0] if date_only else bar['day']
        groups[day_key].append(bar)
    
    sorted_days = sorted(groups.keys())
    daily = {}
    for i, d in enumerate(sorted_days):
        g = groups[d]
        daily[d] = {
            'open': g[0]['open'], 'close': g[-1]['close'],
            'high': max(b['high'] for b in g),
            'low': min(b['low'] for b in g),
            'volume': sum(b['volume'] for b in g),
            'prev_close': groups[sorted_days[i-1]][-1]['close'] if i > 0 else g[0]['open'],
        }
    return daily


def pct_diff(a, b):
    return abs(a - b) / a * 100 if a != 0 else 0


# ============================================================
print("=" * 95)
print("  TENCENT DAILY × SINA 60MIN — CROSS-VALIDATION")
print("  (Plus: SINA 60MIN vs SINA 5MIN internal consistency)")
print("=" * 95)

all_cmp = []

for name, tc_code, sina_code in TEST_STOCKS:
    print(f"\n{'─'*90}")
    print(f"  📊 {name} ({tc_code}/{sina_code})")
    print(f"{'─'*90}")
    
    # Fetch all three sources
    tencent = fetch_tencent_daily(tc_code, "2025-10-01", "2026-04-07")
    sina_60m = fetch_sina_bars(sina_code, "60", 3000)
    sina_5m = fetch_sina_bars(sina_code, "5", 1500)
    
    print(f"  Tencent daily: {len(tencent)} bars")
    print(f"  Sina 60min:     {len(sina_60m)} bars")
    print(f"  Sina 5min:      {len(sina_5m)} bars")
    
    # Group to daily
    daily_60m = group_bars_to_daily(sina_60m)
    daily_5m = group_bars_to_daily(sina_5m)
    
    print(f"  → 60min-derived daily: {len(daily_60m)} days | range: {min(daily_60m.keys())}~{max(daily_60m.keys())}")
    print(f"  → 5min-derived daily:  {len(daily_5m)} days | range: {min(daily_5m.keys())}~{max(daily_5m.keys())}")
    
    if not tencent or not daily_60m:
        continue
    
    # Build lookup by date (normalize format)
    def norm_date(d): 
        s = d.replace('-','')
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    
    tenc_lookup = {norm_date(r['date']): r for r in tencent}
    
    print(f"\n  {'Date':<12} {'TCvs60_O%':>9} {'TCvs60_C%':>9} {'TCvs60_H%':>9} {'TCvs60_L%':>9} │ {'60vs5_O%':>9} {'60vs5_C%':>9} │ {'Gap(60m)%':>9}")
    print(f"  {'─'*90}")
    
    for td in TEST_DATES:
        # Normalize test date
        tkey = td.replace('-','')
        
        tc = tenc_lookup.get(td) or tenc_lookup.get(tkey)
        d60 = daily_60m.get(td) or daily_60m.get(tkey)
        d5 = daily_5m.get(td) or daily_5m.get(tkey)
        
        if not tc:
            print(f"  {td:<12} {'NO_TENCENT':>67}")
            continue
        if not d60:
            print(f"  {td:<12} {'NO_SINA60M':>67}")
            continue
        
        # Tencent vs 60min
        o1 = pct_diff(tc['open'], d60['open'])
        c1 = pct_diff(tc['close'], d60['close'])
        h1 = pct_diff(tc['high'], d60['high'])
        l1 = pct_diff(tc['low'], d60['low'])
        
        # 60min vs 5min (if both available)
        o2 = c2 = -1
        gap = -1
        if d5:
            o2 = pct_diff(d60['open'], d5['open'])
            c2 = pct_diff(d60['close'], d5['close'])
        gap_val = ((tc['open'] - d60['prev_close']) / d60['prev_close'] * 100) if d60.get('prev_close') and d60['prev_close'] > 0 else -1
        
        flag1 = "" if all(v < 0.3 for v in [o1,c1,h1,l1]) else " ⚠️"
        flag2 = "" if o2 >= 0 and c2 >= 0 and o2 < 0.3 and c2 < 0.3 else ("—" if o2<0 else " ⚠️")
        gap_s = f"{gap_val:.3f}" if gap_val >= 0 else "—"
        
        print(f"  {td:<12} {o1:>8.3f}%{flag1} {c1:>8.3f}%{flag1} {h1:>8.3f}%{flag1} {l1:>8.3f}%{flag1} │ {o2:>8.3f}%{flag2} {c2:>8.3f}%{flag2} │ {gap_s:>8}{flag1}")
        
        all_cmp.append({'stock': name, 'date': td, 
                        'tc_vs_60_o': o1, 'tc_vs_60_c': c1, 'tc_vs_60_h': h1, 'tc_vs_60_l': l1,
                        '60_vs_5_o': o2, '60_vs_5_c': c2, 'gap': gap_val})

# SUMMARY
print(f"\n\n{'='*95}")
print(f"  VALIDATION SUMMARY")
print(f"{'='*95}")

if all_cmp:
    for label, key in [("Open (TC vs 60m)", 'tc_vs_60_o'), ("Close (TC vs 60m)", 'tc_vs_60_c'),
                        ("High (TC vs 60m)", 'tc_vs_60_h'), ("Low (TC vs 60m)", 'tc_vs_60_l'),
                        ("Open (60m vs 5m)", '60_vs_5_o'), ("Close (60m vs 5m)", '60_vs_5_c')]:
        vals = [r[key] for r in all_cmp if r[key] >= 0]
        if vals:
            print(f"  {label}: avg={sum(vals)/len(vals):.4f}%  max={max(vals):.4f}%  min={min(vals):.4f}%  n={len(vals)}")
    
    gaps = [r['gap'] for r in all_cmp if r['gap'] >= 0]
    if gaps:
        print(f"  Gap analysis (prev_close→next_open via 60m): avg={sum(gaps)/len(gaps):.4f}%  max={abs(max(gaps)):.4f}%  n={len(gaps)}")
    
    ok = sum(1 for r in all_cmp if all(r[f'tc_vs_60_{f}'] < 0.3 for f in ['o','c','h','l']))
    print(f"\n  ✅ TC-vs-60m within 0.3%: {ok}/{len(all_cmp)} ({ok/len(all_cmp)*100:.0f}%)")
