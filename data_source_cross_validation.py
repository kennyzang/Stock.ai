"""
Cross-validation: NetEase Daily vs Sina 5-min K-line data alignment test.
Tests multiple stocks, multiple dates, multiple dimensions.
"""
import urllib.request
import csv
import io
import json
from datetime import datetime, timedelta

# ============================================================
# VPN FIX: Bypass proxy for Chinese data sources
# ============================================================
_proxy_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
urllib.request.install_opener(_proxy_opener)

# ============================================================
# Test Configuration
# ============================================================

TEST_STOCKS = [
    # (name, netease_code, sina_code)
    ("平安银行", "000001", "sz000001"),   # 深市大盘股
    ("贵州茅台", "600519", "sh600519"),   # 沪市大盘股
    ("比亚迪", "002594", "sz002594"),     # 深市热门股
    ("中信证券", "600030", "sh600030"),   # 券商股
    ("宁德时代", "300750", "sz300750"),   # 创业板权重
    ("中国石油", "601857", "sh601857"),   # 中字头
]

# Test multiple recent trading days (avoid weekends/holidays)
# 2026-04-03 is Thursday, 2026-04-02 is Wednesday, etc.
TEST_DATES = [
    "2026-04-03",
    "2026-04-02",
    "2026-04-01",
    "2026-03-31",
    "2026-02-28",   # ~1 month ago
    "2026-01-23",   # ~2 months ago  
    "2025-12-31",   # ~3 months ago
    "2025-11-28",   # ~4 months ago
    "2025-10-31",   # ~5 months ago
]


def fetch_netease_daily(code: str, start_date: str, end_date: str) -> list[dict]:
    """Fetch daily OHLCV from NetEase (163) Finance API."""
    # NetEase code format: 0 + 沪市代码 / 1 + 深市代码
    url = f"http://quotes.money.163.com/service/chddata.html?code={code}&start={start_date.replace('-','')}&end={end_date.replace('-','')}"
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode('gb2312', errors='ignore')
        
        reader = csv.DictReader(io.StringIO(raw))
        rows = []
        for row in reader:
            if not row.get('日期') or row['日期'] == '日期':
                continue
            try:
                rows.append({
                    'date': row['日期'].strip(),
                    'open': float(row['开盘价']),
                    'high': float(row['最高价']),
                    'low': float(row['最低价']),
                    'close': float(row['收盘价']),
                    'volume': float(row['成交量']),       # 手 (lots)
                    'turnover': float(row['成交金额']),     # 元 (yuan)
                })
            except (ValueError, KeyError):
                continue
        
        # Reverse to chronological order (NetEase returns newest first)
        rows.reverse()
        return rows
    except Exception as e:
        print(f"  [ERROR] NetEase fetch failed: {e}")
        return []


def fetch_sina_5min(sina_code: str, num_bars: int = 1500) -> list[dict]:
    """Fetch 5-minute bars from Sina Finance API."""
    url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina_code}&scale=5&ma=no&datalen={num_bars}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            raw = resp.read().decode('utf-8', errors='ignore')
        
        if not raw or raw.strip() == '' or 'null' in raw.lower():
            return []
        
        # Sina returns JSON array
        data = json.loads(raw)
        bars = []
        for item in data:
            try:
                bars.append({
                    'day': item['day'],           # e.g., "2026-04-03"
                    'open': float(item['open']),
                    'high': float(item['high']),
                    'low': float(item['low']),
                    'close': float(item['close']),
                    'volume': float(item['volume']),
                })
            except (ValueError, KeyError, TypeError):
                continue
        return bars
    except Exception as e:
        print(f"  [ERROR] Sina fetch failed: {e}")
        return []


def group_sina_bars_by_day(bars: list[dict]) -> dict[str, dict]:
    """Group 5-min bars into daily candles + track prev_close."""
    from collections import defaultdict
    
    day_groups = defaultdict(list)
    for bar in bars:
        day_groups[bar['day']].append(bar)
    
    daily = {}
    sorted_days = sorted(day_groups.keys())
    
    for i, day in enumerate(sorted_days):
        day_bars = day_groups[day]
        
        # Build daily OHLC from 5-min bars
        day_open = day_bars[0]['open']
        day_close = day_bars[-1]['close']
        day_high = max(b['high'] for b in day_bars)
        day_low = min(b['low'] for b in day_bars)
        day_volume = sum(b['volume'] for b in day_bars)
        
        # Previous day's close (for gap calculation)
        if i > 0:
            prev_day = sorted_days[i - 1]
            prev_close = day_groups[prev_day][-1]['close']
        else:
            prev_close = day_open  # No previous data
        
        daily[day] = {
            'open': day_open,
            'close': day_close,
            'high': day_high,
            'low': day_low,
            'volume': day_volume,
            'prev_close': prev_close,
            'num_bars': len(day_bars),
        }
    
    return daily


def compare_one_day(netease_row: dict, sina_day: dict) -> dict[str, any]:
    """Compare one day's data between NetEase and derived Sina daily."""
    diffs = {}
    
    for field in ['open', 'close', 'high', 'low']:
        ne_val = netease_row[field]
        si_val = sina_day[field]
        abs_diff = abs(ne_val - si_val)
        pct_diff = abs_diff / ne_val * 100 if ne_val != 0 else 0
        diffs[field] = {
            'netease': round(ne_val, 2),
            'sina_5min_derived': round(si_val, 2),
            'abs_diff': round(abs_diff, 3),
            'pct_diff': round(pct_diff, 4),
        }
    
    # Volume comparison (units differ: NetEase=手, Sina=股 → factor of ~100)
    ne_vol_lots = netease_row['volume']
    si_vol_shares = sina_day['volume']
    vol_ratio = si_vol_shares / ne_vol_lots if ne_vol_lots != 0 else 0
    diffs['volume'] = {
        'netease_lots': int(ne_vol_lots),
        'sina_shares': int(si_vol_shares),
        'ratio': round(vol_ratio, 2),  # Should be close to 100 (1 lot = 100 shares)
    }
    
    # Gap analysis (using sina's prev_close from last 5min bar)
    sina_prev_close = sina_day['prev_close']
    sina_gap = (netease_row['open'] - sina_prev_close) / sina_prev_close * 100 if sina_prev_close > 0 else 0
    
    diffs['gap_analysis'] = {
        'sina_prev_close': round(sina_prev_close, 2),
        'netease_open': round(netease_row['open'], 2),
        'gap_pct': round(sina_gap, 4),
    }
    
    return diffs


def run_full_validation():
    """Run comprehensive cross-validation across all stocks and dates."""
    
    print("=" * 90)
    print("  NETEASE DAILY × SINA 5-MIN — CROSS-VALIDATION TEST")
    print(f"  Test date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Stocks: {len(TEST_STOCKS)} | Dates per stock: {len(TEST_DATES)}")
    print("=" * 90)
    
    all_results = []  # List of (stock_name, date, comparison_dict)
    error_log = []
    
    for stock_name, ne_code, sina_code in TEST_STOCKS:
        print(f"\n{'─'*80}")
        print(f"  📊 {stock_name} ({ne_code} / {sina_code})")
        print(f"{'─'*80}")
        
        # Fetch NetEase daily data (wider range for context)
        earliest = min(TEST_DATES)
        latest = max(TEST_DATES)
        plus_buffer = (datetime.strptime(latest, '%Y-%m-%d') + timedelta(days=5)).strftime('%Y-%m-%d')
        
        ne_data = fetch_netease_daily(ne_code, earliest, plus_buffer)
        print(f"  NetEase: fetched {len(ne_data)} daily records")
        
        # Fetch Sina 5-min data (need enough bars to cover all test dates + buffer)
        # ~48 bars/day × (days range + 10 buffer)
        days_span = (datetime.strptime(latest, '%Y-%m-%d') - datetime.strptime(earliest, '%Y-%m-%d')).days
        needed_bars = int(days_span * 50 + 300)
        
        sina_bars = fetch_sina_5min(sina_code, num_bars=max(needed_bars, 2000))
        sina_daily = group_sina_bars_by_day(sina_bars)
        print(f"  Sina 5min: fetched {len(sina_bars)} bars → {len(sina_daily)} trading days")
        
        if not ne_data:
            error_log.append((stock_name, "NetEase returned no data"))
            continue
        if not sina_daily:
            error_log.append((stock_name, "Sina returned no data"))
            continue
        
        # Compare each test date
        print(f"\n  {'Date':<14} {'OpenΔ%':>8} {'CloseΔ%':>9} {'HighΔ%':>8} {'LowΔ%':>8} {'VolRatio':>9} {'Gap%':>7} {'Bars':>5}")
        print(f"  {'─'*80}")
        
        for test_date in TEST_DATES:
            # Find matching NetEase record
            ne_match = None
            for r in ne_data:
                if r['date'] == test_date or r['date'].replace('/', '-') == test_date:
                    ne_match = r
                    break
            
            if not ne_match:
                # Try alternative formats
                for r in ne_data:
                    r_date = r['date'].replace('-', '/').replace('/', '-')
                    if test_date.replace('-', '') in r_date.replace('-', '').replace('/', ''):
                        ne_match = r
                        break
                
            if not ne_match:
                print(f"  {test_date:<14} {'N/A (no NE)':>56}")
                error_log.append((f"{stock_name}@{test_date}", "No NetEase data"))
                continue
            
            if test_date not in sina_daily:
                print(f"  {test_date:<14} {'N/A (no Sina)':>56}")
                error_log.append((f"{stock_name}@{test_date}", "No Sina 5min data for this day"))
                continue
            
            cmp = compare_one_day(ne_match, sina_daily[test_date])
            
            o_pct = cmp['open']['pct_diff']
            c_pct = cmp['close']['pct_diff']
            h_pct = cmp['high']['pct_diff']
            l_pct = cmp['low']['pct_diff']
            v_rat = cmp['volume']['ratio']
            g_pct = cmp['gap_analysis']['gap_pct']
            n_bars = sina_daily[test_date]['num_bars']
            
            flag = " ✅" if all(v < 0.5 for v in [o_pct, c_pct, h_pct, l_pct]) else " ⚠️"
            
            print(f"  {test_date:<14} {o_pct:>7.3f}% {c_pct:>8.3f}% {h_pct:>7.3f}% {l_pct:>7.3f}% {v_rat:>8.0f}x {g_pct:>6.3f}% {n_bars:>5}{flag}")
            
            all_results.append({
                'stock': stock_name,
                'date': test_date,
                'comparison': cmp,
                'num_5min_bars': n_bars,
            })
    
    # ================================================================
    # SUMMARY STATISTICS
    # ================================================================
    print(f"\n\n{'='*90}")
    print(f"  VALIDATION SUMMARY")
    print(f"{'='*90}")
    
    if not all_results:
        print("\n  ❌ NO successful comparisons! All errors:")
        for item, reason in error_log:
            print(f"    - {item}: {reason}")
        return
    
    # Collect all percentage differences
    open_diffs = [r['comparison']['open']['pct_diff'] for r in all_results]
    close_diffs = [r['comparison']['close']['pct_diff'] for r in all_results]
    high_diffs = [r['comparison']['high']['pct_diff'] for r in all_results]
    low_diffs = [r['comparison']['low']['pct_diff'] for r in all_results]
    vol_ratios = [r['comparison']['volume']['ratio'] for r in all_results]
    gaps = [r['comparison']['gap_analysis']['gap_pct'] for r in all_results]
    
    def stats(label, values):
        if not values:
            print(f"\n  {label}: no data")
            return
        avg = sum(values) / len(values)
        mx = max(values)
        mn = min(values)
        outliers = sum(1 for v in values if v >= 0.5)
        print(f"\n  {label}:")
        print(f"    Avg diff: {avg:.4f}%")
        print(f"    Max diff: {mx:.4f}%")
        print(f"    Min diff: {mn:.4f}%")
        print(f"    Outliers (≥0.5%): {outliers}/{len(values)}")
    
    stats("Open price % difference", open_diffs)
    stats("Close price % difference", close_diffs)
    stats("High price % difference", high_diffs)
    stats("Low price % difference", low_diffs)
    
    print(f"\n  Volume ratio (Sina shares / NetEase lots):")
    print(f"    Avg ratio: {sum(vol_ratios)/len(vol_ratios):.1f}x (expected: ~100x)")
    print(f"    Max ratio: {max(vol_ratios):.0f}x, Min ratio: {min(vol_ratios):.0f}x")
    
    print(f"\n  Gap analysis (Sina prev_close → NetEase next open):")
    print(f"    Avg gap: {sum(gaps)/len(gaps):.4f}%")
    print(f"    Max gap: {max(gaps):.4f}%")
    print(f"    Min gap: {min(gaps):.4f}%")
    
    # Overall verdict
    total = len(all_results)
    perfect = sum(1 for r in all_results if all(
        r['comparison'][f]['pct_diff'] < 0.5 
        for f in ['open', 'close', 'high', 'low']
    ))
    
    print(f"\n  {'='*90}")
    print(f"  OVERALL: {perfect}/{total} comparisons within 0.5% tolerance ({perfect/total*100:.0f}%)")
    if error_log:
        print(f"  Errors/missing: {len(error_log)}")
        for item, reason in error_log[:5]:
            print(f"    - {item}: {reason}")
        if len(error_log) > 5:
            print(f"    ... and {len(error_log)-5} more")
    print(f"{'='*90}")


if __name__ == "__main__":
    run_full_validation()
