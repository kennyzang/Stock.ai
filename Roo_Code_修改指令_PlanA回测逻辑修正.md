# Roo Code Instructions: Fix Plan A Backtest — Data Source & Bug Fixes (Post-Validation)

## Context

**The previous instruction (方案A回测逻辑重写.md) was already executed by Roo Code.**
The code changes are IN PLACE in `master_orchestrator.py` and `layer3_analyst.py`.
This document contains **ONLY the fixes and adjustments needed after our data source cross-validation**.

### What Was Done Previously (DO NOT re-do)
- ✅ `get_future_price()` → replaced with `simulate_buy_and_survival()` 
- ✅ `fetch_sina_5min()` added (Sina 5-min K-line fetcher)
- ✅ `fetch_tencent_daily()` added (Tencent daily K-line for date lookup)
- ✅ 4-condition buy detection implemented
- ✅ -2% stop loss Day 1 survival check
- ✅ WIN/LOSS/NO_BUY/DATA_ERROR 4-state outcome
- ✅ Layer3 prompts updated to Plan A definitions
- ✅ Main loop calls `simulate_buy_and_survival()` correctly

### What Needs Fixing NOW (4 issues found during validation)

---

## Issue #1 (🔴 CRITICAL): Sina 5-min datalen too small

**File**: `master_orchestrator.py`, line ~314

**Current code:**
```python
min_data = fetch_sina_5min(stock_code, num_bars=200)
```

**Problem**: 200 bars ≈ only 4 trading days of 5-min data. When running a 20-day backtest, the earliest select_date may be ~20 trading days ago. The buy day + Day 1 could be up to 22 days from "today". With only 4 days of data, most stocks will get DATA_ERROR.

**Verified fact (tested 2026-04-07)**: Sina API with `scale=5` returns **up to 5001 bars** (not 1000 as previously assumed). That's ~104 trading days (~3.5 months). More than enough for any realistic backtest.

**Fix to:**
```python
min_data = fetch_sina_5min(stock_code, num_bars=1500)
```
1500 bars ≈ 31 trading days (~1.5 months). Safe margin for 20-day backtests. You can also go higher (up to 5000) if you want more buffer, but 1500 is a good balance between speed and coverage.

Also update the docstring comment in `fetch_sina_5min()`:
```python
# OLD (line ~173):
#   num_bars: number of 5-min bars to fetch (max ~1000)

# NEW:
#   num_bars: number of 5-min bars to fetch (max ~5000, ~104 trading days verified)
```

---

## Issue #2 (🟡 MEDIUM): Tencent daily range may be too small for long backtests

**File**: `master_orchestrator.py`, line ~289

**Current code:**
```python
daily_data = fetch_tencent_daily(stock_code, num_days=60)
```

**Problem**: When running a 20-day backtest, the first select_date is ~20 trading days ago. We need to find this date in the daily data to get its close price as prev_close. 60 days of calendar time ≈ ~43 trading days, which should cover 20 days... BUT we also need data AFTER select_date (for the next trading day). And Tencent returns data newest-first, so we need enough range.

The current value of 60 should work for short backtests but may fail on longer ones (30+ days). To be safe:

**Fix to:**
```python
daily_data = fetch_tencent_daily(stock_code, num_days=120)
```

This gives ~86 trading days of cushion — more than enough even for 40-day backtests.

---

## Issue #3 (🟡 MEDIUM): Day 1 bar collection logic is fragile

**File**: `master_orchestrator.py`, lines ~329-349

**Current code uses a state machine approach:**
```python
current_day = None
day_count = 0

for bar in min_data:
    bar_date = bar['day'].split(' ')[0].replace("-", "")
    if bar_date == next_day_date_normalized:
        buy_day_bars.append(bar)
        if current_day is None:
            current_day = bar_date
            day_count = 1
    elif current_day and bar_date != current_day:
        if day_count == 1:
            day1_bars.append(bar)     # First bar after buy day → start of Day 1?
            current_day = bar_date
            day_count = 2
        elif day_count == 2:
            day1_bars.append(bar)       # Continue adding to Day 1
        if day_count >= 2:
            break
```

**Problem**: This state-machine logic is hard to read and has edge case risks:
1. If there are non-trading-day gaps in the 5-min data (unlikely but possible), it misidentifies Day 1
2. The `day_count == 1` check inside `elif` means the FIRST bar of a new day gets added to day1_bars, which is correct but confusing
3. It's fragile if data ordering or date format ever changes

**Fix**: Replace with cleaner two-pass approach — group ALL bars by date first, then pick the right buckets:
```python
# Step 2 (revised): Group all 5-min bars by date, then extract buy_day and Day 1
from collections import defaultdict

bars_by_date = defaultdict(list)
for bar in min_data:
    date_key = bar['day'].split(' ')[0].replace("-", "")
    bars_by_date[date_key].append(bar)

sorted_dates = sorted(bars_by_date.keys())

buy_day_bars = bars_by_date.get(next_day_date_normalized, [])
if not buy_day_bars:
    result['reason'] = f'No 5-min data for buy day {next_day_date}'
    return result

# Find Day 1: the NEXT trading day after buy day
day1_bars = []
buy_day_idx = sorted_dates.index(next_day_date_normalized) if next_day_date_normalized in sorted_dates else -1
if buy_day_idx >= 0 and buy_day_idx + 1 < len(sorted_dates):
    day1_date = sorted_dates[buy_day_idx + 1]
    day1_bars = bars_by_date.get(day1_date, [])
```

This is cleaner, easier to debug, and handles edge cases correctly.

---

## Issue #4 (💡 OPTIONAL): Update data source comments to reflect validated facts

**File**: `master_orchestrator.py`, `fetch_sina_5min()` function docstring

Update the docstring to include our validated findings:

```python
def fetch_sina_5min(stock_code: str, num_bars: int = 1500):
    """Fetch 5-minute K-line bars from Sina Finance API.
    
    Args:
        stock_code: 6-digit stock code (e.g., '000088')
        num_bars: number of 5-min bars to fetch (max ~5000, ~104 trading days verified 2026-04-07)
        
    Returns:
        List of dicts: [{'day': '2026-04-07 09:35:00', ...}, ...]
        Or None on error.
    
    VERIFIED FACTS (2026-04-07 cross-validation):
    - scale=5: max ~5001 bars (~104 trading days / 3.5 months)
    - scale=60: max ~3519 bars (~880 trading days / 3.5 years)  
    - scale=1440 (daily): returns null, NOT available
    - Sina does NOT support 复权 (adjustment) — prices are raw/unadjusted
    - Internal consistency: 60min-derived-daily vs 5min-derived-daily = 100% match (0.000% diff)
    - vs Tencent qfq daily: near-term (<6mo) diff <0.01%, older data has ~1.7% divergence due to lack of adjustment
    
    NOTE: This function works alongside fetch_tencent_daily() in Plan B variant:
    - Tencent provides adjusted daily K-line for date resolution & prev_close
    - Sina provides raw 5-min bars for intraday simulation (buy detection + stop loss)
    """
    # ... rest of function unchanged ...
```

---

## Summary of Changes

| # | File | Line Area | Change | Priority |
|---|------|----------|--------|----------|
| 1 | master_orchestrator.py | ~314 | `num_bars=200` → `num_bars=1500` | 🔴 Critical |
| 2 | master_orchestrator.py | ~289 | `num_days=60` → `num_days=120` | 🟡 Medium |
| 3 | master_orchestrator.py | ~329-349 | Replace fragile state-machine with clean `defaultdict` grouping | 🟡 Medium |
| 4 | master_orchestrator.py | ~168-179 | Update docstring with validated data specs | 💡 Optional |

## Files NOT to modify
- `layer1_filter.py` — no changes (still uses Tencent/AKShare as before)
- `layer2_screener.py` — no changes
- `layer3_analyst.py` — already correctly updated in previous round
- `screener_system_prompt.txt` — no changes
- Any rules files — no changes

## Testing After Fixes

Run a quick 2-day test:
```bash
cd ~/stock_ai/autoresearch
uv run python master_orchestrator.py 2 --apply
```

Expected improvements vs. before-fix:
- Fewer DATA_ERROR outcomes (was getting them because 200 bars wasn't enough)
- Day 1 bars correctly identified (no state machine confusion)
- If running >20 day backtest, still safe (1500 bars covers 31 trading days)

## Important Constraints (same as before)
- Do NOT introduce MACD/RSI/KDJ indicators
- Keep changes focused ONLY on the 4 fixes above
- Preserve ALL existing Layer1/Layer2/Layer3 functionality
- Both Sina and Tencent API calls must use ProxyHandler({}) for VPN compatibility
- Error handling: if any API fails for a specific stock, mark as DATA_ERROR and continue
- All instruction text in English (Roo Code uses Qwen3.6 model)
