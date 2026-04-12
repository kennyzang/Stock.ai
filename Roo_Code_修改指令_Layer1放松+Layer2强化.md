# Layer 1 Relax + Layer 2 Strengthen — Combined Instruction

**Context**: Diagnostic test showed `three_highs_two_lows` rejects **96.7%** of candidates. The user has re-calibrated the architecture:

- **Layer 1 (Python)** = loose net, catch ~100+ candidates from 5000 stocks. Only do basic coarse filtering.
- **Layer 2 (DeepSeek V3)** = the REAL selection gate. AI should use "artistic judgment" for pattern recognition — this is where the human eye's expertise lives.
- **Layer 3 (AutoResearch)** = weekly rule iteration based on actual P&L feedback.

**Core principle**: Do NOT put strict pattern-matching in Layer 1. That belongs to Layer 2.

---

## PART A: Layer 1 — Relax Filters (layer1_filter.py)

### Task A1: Replace `three_highs_two_lows()` with a LOOSE version

The current function at line 257 is way too strict:
- Requires `distance=5` between peaks → too wide
- Requires strictly decreasing highs AND strictly increasing lows → binary pass/fail
- Rejects 96.7% of candidates

**Replace it with a much looser version:**

```python
def three_highs_two_lows_loose(recent_20d: pd.DataFrame) -> bool:
    """LOOSE check for convergence structure.
    
    This is NOT a definitive pattern match - that job belongs to Layer 2 AI review.
    We only want to catch stocks that show ANY signs of consolidation/convergence,
    so they can be sent to Layer 2 for detailed visual analysis.
    
    Pass if ANY ONE of these is true:
    1) End zone width < 10% (price compressing at the edge)
    2) At least 2 swing highs found (distance >= 3 bars)
       and at least 1 swing low found
    3) Volume declining (avg_volume_5d / avg_volume_20d < 0.85)
    
    The goal: let through ~100+ candidates for Layer 2 to judge.
    """
    # ... implement ...
```

**Key changes:**
- Rename current `three_highs_two_lows` → `three_highs_two_lows_loose` 
- `MIN_PEAK_DISTANCE`: 5 → **3**
- Remove "strictly decreasing/increasing" requirement entirely
- Only require **at least 2 highs + 1 low** (not 3+2)
- Add volume decline as an alternative pass condition
- Keep end-zone convergence check but relax threshold

### Task A2: Make P2 and P3 SOFT checks (not hard rejection)

Current code: `ma_entanglement_check()` and `convergence_position_check()` are **hard gates** — if they fail, stock is rejected.

**Change them to soft flags:**

In `convergence_prefilter()` (line 450):
```python
# BEFORE (hard rejection):
if not ma_entanglement_check(recent_20d):
    FILTER_REJECT_COUNTS["ma_entanglement"] += 1
    return False

# AFTER (soft flag - just log, don't reject):
ma_ok = ma_entanglement_check(recent_20d)
if not ma_ok:
    # Log but DON'T reject - Layer 2 will evaluate MA entanglement visually
    print(f"[SOFT] ma_entanglement: flag set but passing through")
# No return False here!

# Same for convergence_position_check:
pos_ok = convergence_position_check(history_df)
if not pos_ok:
    print(f"[SOFT] convergence_position: flag set but passing through")
# Don't reject!
```

**Why?** MA entanglement and position (high/low convergence) are VISUAL judgments that humans make with nuance. A programmatic check will either be too strict or miss edge cases. Let Layer 2's DeepSeek V3 decide these.

### Task A3: Update diagnostic counters

Update `print_filter_report()` to show SOFT flags separately:

```
=== CONVERGENCE FILTER DROP ANALYSIS ===
  three_highs_two_lows     :   XX rejected (HARD)
  ma_entanglement          :    X flagged (SOFT - passed through)
  convergence_position     :    X flagged (SOFT - passed through)
  end_zone_width           :   XX rejected (HARD)
  PASS                     :   XX passed
========================================
```

---

## PART B: Layer 2 — Strengthen AI Review (rules/screener_system_prompt.txt)

### Task B1: Rewrite system prompt with "Artificial Eye" philosophy

The current prompt (`rules/screener_system_prompt.txt`) is good but treats rules as rigid checklists. **Rewrite it** with these principles:

**New philosophy for the prompt:**

> You are acting as an expert human technical analyst who looks at candlestick charts with years of experience. Your role is NOT to apply rigid rules mechanically — it's to use JUDGMENT, similar to how a seasoned trader would look at a chart and say "this feels like a setup" even if one criterion isn't perfectly met.

**Key additions to the new prompt:**

1. **"三高两低" (Three Highs Two Lows) — Visual judgment section:**
   ```
   ## 三高两低 STRUCTURAL CHECK (Visual Judgment Required)
   
   A proper 收敛图 (convergence chart) shows roughly 3 descending high points
   and 2 ascending low points over the observation window. However:
   
   ACCEPTABLE VARIATIONS:
   - If only 2 clear highs + 2 clear lows exist BUT the price compression
     at the end zone is very tight (< 5%), this can still qualify
   - One "high" may be a double-top (two similar peaks close together) — count as 1
   - The descent/ascent doesn't need to be perfectly monotonic; small wiggles
     between major swings are normal and acceptable
   - Timing matters more than perfection: if the LAST few days show extreme
     compression while earlier swings show the general structure, favor PASS
   
   REJECT IF:
   - All highs are rising (expanding range, opposite of convergence)
   - All lows are falling (downtrend, not consolidation)
   - No discernible swing structure — looks random or trending
   - End zone is WIDENING (opposite of what we want)
   ```

2. **MA Entanglement — Visual judgment:**
   ```
   ## 均线缠绕 (MA Entanglement) — Visual Check
   
   In a proper convergence pattern, short-term MAs (5/10/20-day) should be
   bundled tightly together, showing the market is in indecision/consolidation.
   
   VISUAL STANDARD:
   - On a chart, the three lines should look like they're "hugging" each other
   - Occasional minor crossings are OK — even desirable (shows active entanglement)
   - What's BAD: MAs fanning out upward (strong uptrend already started) or
     downward (downtrend in progress)
   
   TOLERANCE:
   - If MA5 is slightly above MA10-MA20 bundle by 1-3%, that's borderline OK
     (stock might be starting to break out — could be a good timing signal)
   - If all 3 MAs are within a 4% band of the close price → definitely entangled
   ```

3. **High/Low Position Convergence — Visual judgment:**
   ```
   ## 收敛位置 (Convergence Position) — Context Matters
   
   低位收敛 (Low-position convergence): The consolidation zone sits near
   the BOTTOM of recent trading range. This means there are trapped buyers
   above who will sell into any rally → avoid.
   
   高位收敛 (High-position convergence): Near recent highs. Limited upside
   room, overhead supply risk → avoid unless breakout is imminent.
   
   IDEAL POSITION: Middle-to-upper-middle of recent range (40th-80th percentile).
   There's room above for profit-taking and support below from previous structure.
   
   EXCEPTIONS (use judgment):
   - Low position + extremely tight convergence + strong volume dry-up
     MAY still work if the stock appears to be forming a bottoming base
   - High position + about to break above resistance with expanding volume
     CAN work as momentum play (but higher risk)
   ```

4. **"瑕疵容忍度" (Imperfection Tolerance) scoring guide:**
   ```
   ## IMPERFECTION TOLERANCE — How generous to be
   
   Not every 收敛图 is textbook-perfect. When scoring (0-10), consider:
   
   SCORE 8-10 (select): Textbook quality, multiple confirmations align
   SCORE 6-7 (watch): Minor flaws but core structure solid, likely candidate
   SCORE 4-5 (monitor): Several issues but interesting, keep watching
   SCORE 1-3 (skip): Major structural problems or wrong pattern type
   
   GENEROUS FACTORS (+1 to score):
   - End zone extremely tight (< 4%) — shows market compression regardless of earlier structure
   - Volume clearly declining in final days — smart money waiting for direction
   - Stock in hot sector/theme — liquidity and interest favor breakouts
   - Previous successful 收敛图 on same stock (repeatable behavior)
   
   STRICT FACTORS (-1 to score):
   - End zone widening — pattern deteriorating, not improving
   - Volume spiking without price movement — distribution (smart money exiting)
   - ST/*ST or known problem stock
   - Already broken out and extended >5% from consolidation zone
   ```

5. **Update the decision tree:**

Change the recommendation thresholds to reflect that Layer 1 now sends MORE candidates:
- `select`: score >= 7 (unchanged, keep bar high)
- `watch`: score >= 5 (was 5, keep)
- `monitor`: score >= 4 (keep)
- But add: **when uncertain, prefer "watch" over "skip"** for scores 4-6

---

## Execution Order

1. **First**: Implement Part A (Layer 1 relaxation) in `layer1_filter.py`
2. **Test Part A**: Run `uv run python layer1_filter.py --mode convergence --limit 200`
   - Target: **30-150 candidates** passing (not 0-1!)
   - If still < 20: loosen further
   - If > 300: tighten slightly  
3. **Second**: After Part A test passes, rewrite `rules/screener_system_prompt.txt` (Part B)
4. **Test Part B**: Run layer2 on the new candidate list
   - Target: 10-20 stocks get "select" or "watch"

## Files to modify

| File | Change |
|------|--------|
| `autoresearch/layer1_filter.py` | Relax P1/P2/P3 as described |
| `autoresearch/rules/screener_system_prompt.txt` | Complete rewrite with artistic judgment |

## What NOT to change

- Do NOT touch `weekly_trend_not_declining()` — this stays as a hard filter (周线不向下 is non-negotiable)
- Do NOT touch `CONVERGENCE_END_ZONE = 5` constant — the 5-day window is correct
- Do NOT touch the ST exclusion logic (core iron rule / 核心铁律)
- Do NOT change `layer2_screener.py` code itself — only the prompt text file
- Do NOT touch `layer3_analyst.py` — that's separate work

## Testing commands

```bash
cd /Users/kennytseng/stock_ai/autoresearch

# Test Layer 1 relaxation
uv run python layer1_filter.py --mode convergence --limit 200

# Expected: 30-150 candidates (diagnostic report should show most pass through)

# Then test Layer 2 with strengthened prompt
uv run python layer2_screener.py --input layer1_candidates_$(date +%Y%m%d).csv --limit 50

# Expected: 10-20 select/watch recommendations
```
