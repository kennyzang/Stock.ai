# Fix P1: AVOID Gate in Orchestrator + Convergence Trend Check Restore

## Context

Two issues discovered after Day 4 (2026-03-25) execution:

### Issue 1: Orchestrator does NOT filter by recommendation

**Current behavior**: `master_orchestrator.py` runs Plan A backtest on ALL Layer 2 results, including AVOID stocks.
- Day 4 had 64 AVOID + 1 HOLD + 1 BUY = 66 stocks total
- All 66 were sent to backtest simulation
- This wastes API calls and pollutes win rate statistics with stocks that should never be traded

**Expected behavior**: Skip AVOID stocks entirely. Only simulate buys for BUY and (optionally) HOLD recommendations.

### Issue 2: Convergence branch removed daily trend check too aggressively

**Background**: On 2026-04-11, we removed `daily_trend_not_declining` from the convergence branch because some valid patterns form after deep drops (e.g., 联环药业 03-26, 三生国健 03-29).

**Problem**: The removal was too aggressive. Day 4's 000568 (泸州老窖) passed Layer 1 despite:
- MA5 < MA10 < MA20 < MA60 (full bearish alignment)
- All moving averages sloping downward
- Price well below all MAs
- Clear downtrend, NOT a valid convergence bottom

This stock should have been rejected at Layer 1 or at minimum flagged as AVOID at Layer 2.

---

## PART A: Add A Recommendation Filter in Orchestrator

### Task A1: Modify `master_orchestrator.py`

Find this section in the main loop (around line 630):

```python
# Step 3: Get forward price and determine WIN/LOSS/NO_BUY using Plan A logic
day_results = []
for pick in picks:
    code = (pick.get("stock_code") or pick.get("code") or
            pick.get("股票代码") or "").strip()
    if not code:
        continue

    result = simulate_buy_and_survival(code, date_str)
    ...
```

**Add a recommendation filter AFTER the `if not code: continue` line, BEFORE `simulate_buy_and_survival`:**

```python
    # Step 2.5: Filter by Layer 2 recommendation
    # AVOID stocks are excluded from backtest — they should never be traded
    recommendation = (pick.get("recommendation") or "").upper().strip()
    if recommendation == "AVOID":
        print(f"  {code}: SKIPPED (AVOID by Layer 2)")
        continue
    
    # Optional: also skip stocks with very low scores (< 3)
    score = pick.get("score")
    if score is not None:
        try:
            score_val = float(score)
            if score_val < 3:
                print(f"  {code}: SKIPPED (score={score_val} < 3)")
                continue
        except (ValueError, TypeError):
            pass
```

### Task A2: Update summary statistics

After adding the filter, the day summary should reflect filtered counts. Find the summary section (around line 669-677) and update:

```python
    wins = len([r for r in day_results if r["outcome"] == "WIN"])
    losses = len([r for r in day_results if r["outcome"] == "LOSS"])
    no_buys = len([r for r in day_results if r["outcome"] == "NO_BUY"])
    data_errors = len([r for r in day_results if r["outcome"] == "DATA_ERROR"])
    skipped_avoid = len(picks) - len(day_results)  # NEW: count skipped AVOIDs
    
    tradable = wins + losses
    win_rate = (wins / tradable * 100) if tradable > 0 else 0
    print(f"\n  Day {day_num} summary: {wins}W/{losses}L/{no_buys}NO_BUY/{data_errors}ERR "
          f"| Skipped(AVOID): {skipped_avoid} "          # NEW LINE
          f"| Win rate: {win_rate:.0f}% ({tradable} tradable) | Total picks: {total_picks}")
```

### Expected Result After This Change

| Metric | Before | After |
|--------|--------|-------|
| Stocks sent to backtest (Day 4 example) | 66 | 2 (1 BUY + 1 HOLD) |
| Win rate accuracy | Polluted by AVOID stocks | Clean (only tradeable candidates) |
| API cost per day | Higher (66 simulations) | Lower (~2 simulations) |

---

## PART B: Restore Moderate Trend Check for Convergence Branch

### Problem Analysis

The current convergence branch has NO daily trend guard at all. This allows stocks in clear downtrends (like 000568 泸州老窖) to pass through.

We need to add back a **moderate** trend check that:
- ✅ Still allows valid patterns after moderate corrections (联环药业, 三生国健 style)
- ❌ Rejects clear downtrends (MA bearish alignment, price far below MAs)

### Task B1: Add `_is_clear_downtrend()` function to `layer1_filter.py`

Add this new function (place it near other helper functions like `_is_downward_convergence`):

```python
def _is_clear_downtrend(df):
    """
    Check if the stock is in a clear downtrend that should reject convergence patterns.
    
    This is a MODERATE check — less strict than the old daily_trend_not_declining,
    but still catches obvious downtrends.
    
    Returns True if the stock is in a clear downtrend (should be REJECTED).
    
    Criteria for clear downtrend:
    1. MA5 < MA10 < MA20 < MA60 (full bearish alignment)
    2. Latest close is below MA60 by more than 5%
    3. MA60 itself is declining (slope negative over last 20 periods)
    
    If ANY of these conditions fails, it's NOT a clear downtrend → return False (allow).
    """
    recent = df.tail(20)
    
    # Need at least 60 periods for MA60
    if len(df) < 60:
        return False  # Can't determine, allow through
    
    ma5 = df['close'].rolling(window=5).mean().iloc[-1]
    ma10 = df['close'].rolling(window=10).mean().iloc[-1]
    ma20 = df['close'].rolling(window=20).mean().iloc[-1]
    ma60 = df['close'].rolling(window=60).mean().iloc[-1]
    latest_close = df['close'].iloc[-1]
    
    # Condition 1: Full bearish alignment
    bearish_alignment = (ma5 < ma10) and (ma10 < ma20) and (ma20 < ma60)
    
    # Condition 2: Close significantly below MA60
    below_ma60 = (latest_close < ma60 * 0.95)  # More than 5% below
    
    # Condition 3: MA60 declining
    ma60_series = df['close'].rolling(window=60).mean()
    if len(ma60_series.dropna()) >= 20:
        ma60_now = ma60_series.iloc[-1]
        ma60_20d_ago = ma60_series.iloc[-20]
        ma60_declining = (ma60_now < ma60_20d_ago * 0.98)  # MA60 dropped >2% in 20 days
    else:
        ma60_declining = False
    
    # ALL three conditions must be true for "clear downtrend"
    is_downtrend = bearish_alignment and below_ma60 and ma60_declining
    
    return is_downtrend
```

### Task B2: Apply trend check in the convergence branch

Find the convergence screening section where candidates pass all checks. Look for where the function returns True for convergence patterns.

**Insert this check right BEFORE the final acceptance decision in the convergence branch:**

```python
        # === CONVERGENCE BRANCH ===
        if has_convergence:
            # ... existing convergence checks (end_zone_width, lows_rising, etc.) ...
            
            # [NEW] Moderate trend check — reject only CLEAR downtrends
            if _is_clear_downtrend(daily_df):
                debug_log.append("clear_downtrend: 1")
                # Do NOT count as liquidity/trend pass — this is a rejection
                # Log but don't add to results
                return []
            
            # ... rest of existing convergence logic ...
```

**Important placement note**: Put this check AFTER the structural convergence tests (width, lows rising, etc.) but BEFORE the final acceptance. This way:
- We first confirm it IS a convergence pattern
- Then check if the trend context makes it invalid
- Only accept if both structure AND trend context pass

### Task B3: Verify with known cases

After implementing, verify these cases:

| Stock | Date | Expected Result | Reason |
|-------|------|----------------|--------|
| 000568 泸州老窖 | 2026-03-25 | **REJECTED** | MA5<MA10<MA20<MA60, close << MA60, MA60 declining |
| 联环药业 | ~2026-03-26 | **ACCEPTED** | May fail one of 3 conditions (likely MA60 not clearly declining) |
| 三生国健 | ~2026-03-29 | **ACCEPTED** | Similar — deep drop but not sustained downtrend |
| 法尔胜 | known good case | **ACCEPTED** | Should pass fine |
| 节能风电 | known case | **ACCEPTED** | Should pass fine |

### Design Rationale: Why 3 conditions instead of 1?

Using ALL 3 conditions (AND logic) instead of any single condition:

| Approach | False Positive Rate | False Negative Rate |
|----------|--------------------|--------------------|
| Single condition (e.g., just MA5<MA10<MA20) | High (many healthy pullbacks trigger this) | Low |
| **All 3 conditions (AND)** | **Low (only genuine downtrends)** | **Moderate** |
| Any condition (OR) | Very Low | High (rejects too many good setups) |

We chose AND because:
- We'd rather let a borderline case through (Layer 2 can catch it with AVOID) than reject a valid setup
- The goal is to catch **obvious** downtrends like 泸州老窖, not every minor dip
- Layer 2 still has the final say via its own AVOID rules (which include bearish MA alignment)

---

## Files to Modify

| File | Changes |
|------|---------|
| `master_orchestrator.py` | Add AVOID/score filter before `simulate_buy_and_survival()`. Update summary stats. |
| `layer1_filter.py` | Add `_is_clear_downtrend()` function. Call it in convergence branch before final acceptance. |

## What NOT to Change

- Do NOT touch `rules/screener_system_prompt.txt` (already fixed in previous iteration)
- Do NOT touch `layer2_screener.py`
- Do NOT touch `layer3_analyst.py`
- Do NOT modify `rules/screener_user_prompt_template.txt`
- Do NOT make the trend check TOO strict — remember the lesson from 联环药业/三生国健

## Testing

After making changes:

```bash
cd /Users/kennytseng/stock_ai/autoresearch

# Test 1: Run Day 4 again and verify AVOID stocks are skipped
uv run python master_orchestrator.py --days 1 --from 2026-03-25
# Expect: Only 2 stocks go to backtest (BUY + HOLD), 64 skipped as AVOID

# Test 2: Verify 泸州老窖 is rejected by new trend check
uv run python -c "
from layer1_filter import _is_clear_downtrend
import akshare as ak
df = ak.stock_zh_a_hist(symbol='000568', period='daily', start_date='20250801', end_date='20260325', adjust='qfq')
print(f'000568 clear_downtrend = {_is_clear_downtrend(df)}')  # Should be True
"

# Test 3: Verify known good stocks still pass
uv run python -c "
from layer1_filter import _is_clear_downtrend
import akshare as ak
# Test with a known good convergence stock (e.g., 联环药业 around 03-26)
df = ak.stock_zh_a_hist(symbol='600867', period='daily', start_date='20250801', end_date='20260326', adjust='qfq')
print(f'600867 clear_downtrend = {_is_clear_downtrend(df)}')  # Should be False
"
```
