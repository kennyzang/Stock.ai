# Layer1 Pullback Branch — Add Mild Tightening

**File to modify**: `autoresearch/layer1_filter.py`

**Context**: The pullback (二踩) branch currently outputs 464 candidates — too many for Layer2.
The existing filters are too loose, especially `low_point_rising` which only checks that recent
lows aren't making new lows. Missing are the core 二踩 pattern requirements from the strategy.

**IMPORTANT**: Keep this MILD — we want to reduce from ~464 to ~100-200, not to zero.

---

## What the 二踩 (Pullback) pattern actually means (per strategy):

The ideal 二踩图 has TWO clear waves:
- **Wave 1 (一涨)**: A rally of roughly +5-10% with EXPANDING volume (volume > average)
- **Wave 2 (二踩)**: A pullback that CONTRACTS volume (volume < wave-1 volume) 
- Price stays ABOVE the Wave 1 starting point (don't give back all gains)
- Time symmetry: Wave 2 duration is roughly 30-70% of Wave 1 duration

Current code ONLY checks:
1. Weekly trend not declining ✅
2. Low point rising (5d low > 20d low) ← TOO LOOSE
3. Volume declining (5d vol < 20d vol) ✅ but vague
4. Liquidity > 1M ✅
5. Above/near MA250 ✅

Missing: No check for "did a real rally actually happen before this pullback?"

---

## Task: Add ONE new filter function and insert it into pullback_steps

### New function: `first_rally_check()` (一涨确认)

Add this function after `above_or_recently_crossed_ma250()` (around line 540):

```python
def first_rally_check(history_df: pd.DataFrame) -> bool:
    """Check if there's evidence of a first rally (一涨) before current consolidation.
    
    This is a LOOSE check for the 二踩 pattern's first wave.
    We're NOT looking for perfect patterns — just confirming that:
    - Price moved up meaningfully at some point in the last ~15 days
    - There was at least one high-volume day during that move
    
    Pass if ANY ONE condition is true:
    1) There exists at least one day in the last 15 trading days where:
       - (close - open) / open > 2%  (meaningful up-day)
       AND volume > avg_volume_20d * 1.2  (above-average volume on that up-day)
       
    2) The maximum close price in the last 15 days is at least 4% higher than
       the minimum close price in the 15-25 day range (shows a rally then pullback structure)
    
    Reasoning: A 二踩 without any prior rally is just a flat/downtrending stock,
    not a pullback-from-rally setup. This mild check eliminates pure sideways or
    declining stocks while keeping genuine pullback candidates.
    """
    # ... implement ...
```

### Insert into pullback_steps

In the `main()` function, change `pullback_steps` from:

```python
pullback_steps = [
    ("weekly trend not declining", weekly_trend_not_declining),
    ("low point rising", low_point_rising),
    ("volume declining", volume_declining),
    ("liquidity", liquidity_ok),
    ("above or crossed MA250", above_or_recently_crossed_ma250),
]
```

To:

```python
pullback_steps = [
    ("weekly trend not declining", weekly_trend_not_declining),
    ("low point rising", low_point_rising),
    ("first rally check", first_rally_check),        # ← NEW insert here
    ("volume declining", volume_declining),
    ("liquidity", liquidity_ok),
    ("above or crossed MA250", above_or_recently_crossed_ma250),
]
```

Insert it AFTER low_point_rising but BEFORE volume_declining — because:
- First confirm the basic structure exists (low points OK)
- Then confirm there WAS an actual rally (new check)
- Then check volume behavior during the pullback
- Finally liquidity and trend position

---

## Expected effect

This should reject stocks that are:
- Flat/sideways with no meaningful rally ever happened
- Pure downtrend stocks that happen to have "low point rising" by coincidence
- Dead money stocks with no volatility

Target: reduce pullback output from ~464 to ~150-300 range.

---

## Also update diagnostic counters

Add `"first_rally": 0` to `FILTER_REJECT_COUNTS` dict (line ~46).
Add counter increment in the new function's False return path.
Update `print_filter_report()` if needed (it should auto-handle new keys).

---

## Testing

```bash
cd /Users/kennytseng/stock_ai/autoresearch
uv run python layer1_filter.py --mode all
```

Compare pullback output count before (~464) vs after. Target: 150-300.
Convergence output should be UNCHANGED (~1578).

## What NOT to do

- Do NOT touch convergence_steps or convergence_prefilter()
- Do NOT make first_rally_check too strict (no strict percentage requirements)
- Do NOT add time-symmetry check yet (that's Layer 2 visual judgment territory)
- Do NOT change any other pullback filter functions
