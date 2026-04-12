# Roo Code Instructions: Rewrite Backtest Outcome Logic — Plan A (Survive Day 1)

## Objective

**Replace the current naive 5-day price-change outcome with a realistic simulation of the user's actual trading logic.**

The current `get_future_price()` in `master_orchestrator.py` simply checks if close price is higher/lower after N fixed days. This does NOT match the real trading system at all.

We need to simulate: **After a stock is selected by Layer 1+2, can it be bought the next day (meeting intraday buy conditions), and if bought, does it survive Day 1 without hitting stop-loss?**

---

## User's Actual Trading Rules (from their auto-trading code `1030-1.txt`)

### Buy Conditions (intraday, next trading day after selection)
1. **Current price > previous day's close** (trading above flat/opening)
2. **3-minute velocity > 1%** ((price_now - price_3min_ago) / price_3min_ago > 0.01)
3. **Volume surge**: 1-min OR 3-min OR 5-min amount >= pre-calculated threshold
   - Threshold = mean of top-6 (excluding max) 5-min amounts from past 15 trading days × scale factor
   - We'll simplify: just use a fixed minimum volume ratio or skip volume check for backtest (see simplifications below)
4. **Current gain < 4%** (not already up too much)
5. **Buy at market price when all conditions are met**

### Sell Conditions
1. **Hard Stop Loss: -2%** (`stop_loss = -0.02` in code). If profit <= -2%, sell immediately.
2. **Dynamic Trailing Stop** (not used in Plan A — we only care about Day 1 survival)
3. **Time Stop**: Hold max 4 days; if still held at 14:55 on day 4, force sell.

### Plan A Simplified WIN Definition
- **WIN**: Stock was selected → Next day buy conditions were met (at any point during the day) → Bought at that moment's price → From buy price to Day 1 close (or end of Day 1), the **low of Day 1 never touched stop-loss line (-2% from buy price)**.
- **LOSS**: Buy conditions met → Bought → **Day 1 low hit <= -2% from buy price**.
- **NO_BUY (N/A)**: Buy conditions were NEVER met on the next trading day (stock never went above prev_close with enough velocity). This should NOT be counted in win rate — it means the selection didn't trigger an entry.
- **TIMEOUT / HOLDING**: Edge case where data runs out before we can determine outcome.

---

## Data Sources

### SINGLE SOURCE: Sina Finance 5-Minute K-Line (for EVERYTHING)

We ONLY use Sina Finance's 5-minute K-line API. No need for Tencent at all.

```
Base URL: http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData
Params:   symbol={sina_code}&scale=5&ma=no&datalen={num_bars}

Returns JSON array of dicts:
[
  {"day": "2026-04-03 14:55:00", "open": "4.550", "high": "4.550", "low": "4.540", "close": "4.550", "volume": "485500"},
  {"day": "2026-04-07 09:35:00", "open": "4.540", "high": "4.550", "low": "4.530", "close": "4.540", "volume": "1805500"},
  ...
]
```

**VERIFIED FACTS about Sina API (tested on 2026-04-07):**
- **scale=5**: ✅ WORKS (5-minute bars)
- **scale=1**: ❌ returns null (1-minute not available)
- **scale=15/30/60**: ✅ also work if needed
- **scale=1440 (daily)**: ❌ returns null (Sina does NOT support daily via this endpoint)
- **Max datalen**: ~1000 bars = ~20 trading days of 5-min data (48 bars/day × 20 days)
- Each bar contains: day (timestamp), open, high, low, close, volume (all strings)
- Market hours: 9:30-11:30, 13:00-15:00 (exactly 48 five-min bars per trading day)
- NO_PROXY / ProxyHandler({}) required when VPN is on

**WHY WE DON'T NEED TENCENT ANYMORE FOR THIS FUNCTION:**
All daily-level values can be DERIVED from the 5-min bars:
- **prev_close** = last bar's `close` of the previous trading day
- **day_open** = first bar's `open` of the current day
- **day_high** = max of all bars' `high` on that day
- **day_low** = min of all bars' `low` on that day
- **day_close** = last bar's `close` of the day
- **day_volume** = sum of all bars' `volume` on that day

Cross-validated with actual data: Sina 5-min derived close (4.55) vs actual next-day open (4.54) = only 0.22% difference (normal A-share gap).

### Stock Code Format for Sina
- Shanghai: `sh` + 6-digit code (e.g., `sh600519`)
- Shenzhen: `sz` + 6-digit code (e.g., `sz000088`)
- Beijing: `bj` + 6-digit code (e.g., `bj872305`)

---

## What to Modify (File by File)

### File 1: `master_orchestrator.py` — MAIN CHANGES

#### 1A. Replace `get_future_price()` entirely with new functions:

```python
def fetch_sina_5min(stock_code: str, num_bars: int = 500):
    """Fetch 5-minute K-line bars from Sina Finance API — our SINGLE data source.
    
    Args:
        stock_code: 6-digit stock code (e.g., '000088')
        num_bars: number of 5-min bars to fetch (max ~1000, ~20 trading days)
        
    Returns:
        List of dicts with NUMERIC values: 
        [{'day': '2026-04-07 09:35:00', 'open': 4.55, 'high': 4.56, 'low': 4.53, 'close': 4.54, 'volume': 1805500}, ...]
        Or None on error.
        
    IMPORTANT: This replaces ALL data fetching. We no longer need Tencent for this function.
    """
    # Convert to Sina format: sz000088, sh600519, bj872305
    # URL: http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina_code}&scale=5&ma=no&datalen={num_bars}
    # Use ProxyHandler({}) + NO_PROXY (same pattern as existing code)
    # Parse JSON response
    # Convert all string values to float/int before returning
    pass


def group_bars_by_day(bars: list) -> dict:
    """Group 5-minute bars into daily buckets.
    
    Args:
        bars: list of dicts from fetch_sina_5min()
        
    Returns:
        dict mapping date string ('2026-04-07') to {
            'date': '2026-04-07',
            'open': float (first bar open),
            'close': float (last bar close),
            'high': float (max of all highs),
            'low': float (min of all lows),
            'volume': int (sum of all volumes),
            'bars': [list of raw bar dicts for that day]
        }
    Dates are extracted from the 'day' field (format '2026-04-07 09:35:00').
    """
    pass


def simulate_buy_and_survival(stock_code: str, select_date: str):
    """Plan A simulation: Can this stock be bought next day and survive Day 1?
    
    Args:
        stock_code: 6-digit code (e.g., '000088')
        select_date: date string when Layer2 selected this stock ( '2026-03-12'
        
    Returns dict:
        {
            'outcome': 'WIN' | 'LOSS' | 'NO_BUY' | 'DATA_ERROR',
            'buy_price': float or None,
            'buy_time': str or None,
            'exit_price': float or None,
            'pct_change': float or None,  # from buy_price to exit/close
            'reason': str,  # explanation of what happened
            'day1_low_pct': float or None,  # lowest % from buy price on Day 1
        }
    
    Algorithm:
    1. Fetch 5-MIN bars covering select_date through Day+2 (3 trading days total, ~150 bars)
       - Use group_bars_by_day() to split into daily buckets
       - We need: select_date's close (as prev_close for buy day), buy day's bars, Day 1's bars
    
    2. Locate the BUY DAY (first trading day AFTER select_date) and DAY 1 (day after buy day)
       from the grouped daily data.
    
    3. SIMULATE BUY DETECTION on Buy Day:
       Get prev_close = select_date's last bar close (from grouped data)
       For each 5-min bar on Buy Day (in chronological order):
       a. current_price = bar's close
       b. Condition 1: current_price > prev_close (above flat)
       c. Condition 2: Estimate 3-min velocity from 5-min bars
          - APPROXIMATION: (this_bar_close - prev_bar_close) / prev_bar_close > 0.005
          - Skip velocity check for the first bar of the day (no prev bar)
          - (This is simplified since we don't have true 1-min data)
       d. Condition 3: Simple volume check
          - This bar's volume > average volume per bar on buy_day * 2.0
          - (Simplified: just check if this bar has above-average volume)
       e. Condition 4: (current_price - prev_close) / prev_close < 0.04 (< 4% gain)
       
       If ALL conditions met at ANY bar → BUY at this bar's close price
       Record buy_price and buy_time, then BREAK (buy only once)
    
    4. If NO buy triggered all day → return {'outcome': 'NO_BUY', ...}
    
    5. If BOUGHT → Check Day 1 survival:
       From the Day 1 bucket, find the LOWEST price across all bars: day1_lowest
       day1_low_pct = (day1_lowest - buy_price) / buy_price
       
       If day1_low_pct <= STOP_LOSS_PCT (-0.02) → LOSS (hit stop loss)
       Otherwise → WIN (survived Day 1 without hitting stop loss)
    
    6. EDGE CASES:
       - If 5-min data doesn't cover the needed date range → DATA_ERROR
       - If buy happens on the last available data day (can't check Day 1) → DATA_ERROR  
       - If stock is suspended (no bars for a day) → treat as NO_BUY
    """
    pass  # Implement the full algorithm
```

#### 1B. Update the main loop where outcomes are determined:

In the main loop (around line 293-320), REPLACE:
```python
base_p, future_p, pct = get_future_price(code, MIN_HOLDING_DAYS)
if pct >= 5.0: outcome = "WIN"
elif pct <= -2.0: outcome = "LOSS"
else: outcome = "FLAT"
```

WITH:
```python
result = simulate_buy_and_survival(code, date_str)
outcome = result['outcome']  # 'WIN', 'LOSS', 'NO_BUY', or 'DATA_ERROR'
pct_change = result.get('pct_change')  # use for display
buy_price = result.get('buy_price')
reason = result.get('reason', '')
```

Also update the CSV output columns to include new fields:
- `buy_price`, `buy_time`, `day1_low_pct`, `exit_reason`

And update the Day summary print to show:
- How many WIN / LOSS / NO_BUY / DATA_ERROR
- NO_BUY should NOT count toward win rate calculation

#### 1C. Update constants section:
```python
# Remove or rename: MIN_HOLDING_DAYS = 5  (no longer used for fixed-period check)
# Add:
STOP_LOSS_PCT = -0.02      # -2% hard stop loss (from user's actual code)
BUY_VELOCITY_MIN = 0.01     # 1% min 3-min speed (approximated with 5-min bars)
BUY_MAX_GAIN = 0.04         # 4% max gain allowed at buy moment
```

### File 2: `layer3_analyst.py` — Minor Updates

Update the system prompt or analysis text that explains WIN/LOSS definitions to Layer3 AI. Search for any text like "WIN: +5%" or "LOSS: -2%" and update to reflect new definitions:
- **WIN**: Survived Day 1 without hitting -2% stop loss after buy conditions were met
- **LOSS**: Hit -2% stop loss on Day 1 after buy
- **NO_BUY**: Buy conditions never triggered on next day (excluded from win rate)

Look for these strings in layer3_analyst.py:
- The prompt/instruction text that tells AI what WIN and LOSS mean
- The analysis report template
- Update them to match Plan A definitions

### Files NOT to modify:
- `layer1_filter.py` — No changes needed
- `layer2_screener.py` — No changes needed  
- `screener_system_prompt.txt` — No changes (this is about chart patterns, not trade execution)

---

## Testing After Changes

After implementing, run a quick test:
```bash
cd ~/stock_ai/autoresearch
uv run python master_orchestrator.py 2 --apply
```

Expected behavior:
- Day 1 should show some stocks as NO_BUY (buy conditions never triggered)
- Some stocks as WIN (bought and survived)
- Some stocks as LOSS (bought but hit -2% stop)
- The summary line should separate NO_BUY from WIN/LOSS counts

Verify the CSV output has correct new columns and outcomes make sense.

---

## Important Constraints
- Do NOT introduce MACD/RSI/KDJ indicators
- Keep changes focused ONLY on the outcome determination logic
- Preserve ALL existing Layer1/Layer2/prompt functionality
- The Sina API call must use ProxyHandler({}) for VPN compatibility
- Error handling: if Sina API fails for a specific stock, mark it as DATA_ERROR and continue (don't crash the whole backtest)
- All instruction text for Roo Code/GPT must be in English