# Roo_Code Instructions: Diagnostic — Add Per-Filter Drop Counters

## Objective

Add debug counters to `convergence_prefilter()` in `layer1_filter.py` so we can see **exactly how many stocks are rejected at each filter stage**. This is critical to understand why 0 candidates pass after P1-P4, before we can tune the thresholds.

---

## What to Do

In `convergence_prefilter()`, add a global (module-level) counter dictionary that tracks rejections at each stage:

```python
# Add at the TOP of the file (near the other constants):
FILTER_REJECT_COUNTS: dict[str, int] = {}

def reset_filter_counts():
    global FILTER_REJECT_COUNTS
    FILTER_REJECT_COUNTS = {
        "three_highs_two_lows": 0,
        "ma_entanglement": 0,
        "convergence_position": 0,
        "end_zone_width": 0,
        "PASS": 0,
    }

def print_filter_report():
    total = sum(FILTER_REJECT_COUNTS.values())
    print("\n=== CONVERGENCE FILTER DROP ANALYSIS ===")
    for stage, count in FILTER_REJECT_COUNTS.items():
        pct = count / total * 100 if total > 0 else 0
        print(f"  {stage:25s}: {count:4d} rejected ({pct:5.1f}%)")
    print(f"  {'PASS':25s}: {FILTER_REJECT_COUNTS['PASS']:4d} passed")
    print(f"  {'TOTAL':25s}: {total + FILTER_REJECT_COUNTS['PASS']:4d} evaluated")
    print("========================================\n")
```

Then modify `convergence_prefilter()` to increment counters:

```python
def convergence_prefilter(history_df: pd.DataFrame, stock_code: str = "") -> bool:
    recent_20d = history_df.tail(CONVERGENCE_WINDOW)

    # P1: 三高两低
    if not three_highs_two_lows(recent_20d):
        FILTER_REJECT_COUNTS["three_highs_two_lows"] += 1
        return False

    # P2: 均线缠绕
    if not ma_entanglement_check(recent_20d):
        FILTER_REJECT_COUNTS["ma_entanglement"] += 1
        return False

    # P3: 高位/低位收敛排除
    if not convergence_position_check(history_df):
        FILTER_REJECT_COUNTS["convergence_position"] += 1
        return False

    # P0: 末端宽度
    end_zone = history_df.tail(CONVERGENCE_END_ZONE)
    max_price_20d = recent_20d["high"].max()
    max_price_end = end_zone["high"].max()
    min_price_end = end_zone["low"].min()

    if pd.isna(max_price_end) or max_price_end <= 0 or pd.isna(min_price_end):
        FILTER_REJECT_COUNTS["end_zone_width"] += 1
        return False

    ref_price = min(max_price_20d, max_price_end)
    end_zone_width = (max_price_end - min_price_end) / ref_price
    if end_zone_width >= CONVERGENCE_MAX_RATIO:
        FILTER_REJECT_COUNTS["end_zone_width"] += 1
        return False

    FILTER_REJECT_COUNTS["PASS"] += 1
    return True
```

Also update the call sites in `run_branch()` to pass `stock_code`:

```python
# In run_branch(), where convergence_prefilter is called:
if not convergence_prefilter(history_df, stock_code=row.stock_code):
    continue
```

And call `reset_filter_counts()` at the start of `run_branch()` and `print_filter_report()` at the end.

---

## Execution

```bash
cd ~/stock_ai
uv run python layer1_filter.py --mode convergence --limit 200
```

The output will show something like:
```
=== CONVERGENCE FILTER DROP ANALYSIS ===
  three_highs_two_lows        :  142 rejected ( 82.1%)
  ma_entanglement             :   20 rejected ( 11.5%)
  convergence_position         :   10 rejected (  5.8%)
  end_zone_width              :    1 rejected (  0.6%)
  PASS                        :    0 passed
  TOTAL                       :  173 evaluated
========================================
```

This tells us exactly which filter is the bottleneck.

---

## Rules

- Do NOT change any filter thresholds yet — this is diagnostic only
- Keep all existing logic unchanged
- Add only the counter tracking code
