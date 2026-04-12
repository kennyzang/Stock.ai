# Layer2 Prompt Enhancement — True Resistance & Reversal Signal

**File to modify**: `autoresearch/rules/screener_system_prompt.txt`

**Context**: Layer 2 is now the primary selection gate (Layer 1 is a loose net). After reviewing today's results (36 candidates → 4 watch / 0 select), two gaps were identified in the AI's judgment:

1. **True resistance level**: The AI treats `high` price as the real swing high, but experienced traders know the "true high" is where volume concentrated — not necessarily the absolute peak
2. **Reversal signal confirmation**: A stock like 东阿阿胶 scored 7 (watch) but shows 2 highs + 2 lows with ZERO reversal signal after the 2nd low. This should be penalized more

**IMPORTANT**: Do NOT make these new rules too strict! We already get very few candidates. These should be **nuance adjustments** that affect scoring by ±1 point, NOT hard gates that reject stocks.

---

## Task: Append TWO new sections to `screener_system_prompt.txt`

Add these sections **after** the existing "IMPERFECTION TOLERANCE" section and **before** the Output JSON section.

### Section A: True Resistance Level — Visual Judgment (真实压力位)

```
## TRUE RESISTANCE LEVEL — Where Traders Actually React

The absolute daily `high` price is often NOT the real resistance/support level.
Experienced traders look at WHERE the volume actually traded, not just how far
price spiked.

### How to identify true swing-high from daily candle data:

1) **Long upper shadow** (上影线):
   - If (high - close) / (high - low) > 0.4 → long upper shadow
   - The real resistance is likely NEAR THE CLOSE or MID-BODY, not at the high
   - Example: high=58.36, close=57.50, open=57.80 → real pressure zone ≈ 57.80-58.00
   - Reason: price was REJECTED from that zone, most trading happened below the spike

2) **High-volume rejection candle**:
   - If a day has BOTH high volume AND long upper shadow
   - The real resistance is even stronger at the body/close area
   - This indicates smart money sold into the rally at that level

3) **Doji/narrow-range at swing point**:
   - If the swing-high day has very narrow range (open ≈ close ≈ high)
   - Then the high IS likely the real resistance (no rejection pattern)

### Why this matters for 收敛图:
- When identifying "High1", "High2" of the 三高两低 structure,
  consider whether the TRUE resistance might be slightly lower than the reported `high`
- A stock that appears to have "broken above High1" may actually still be BELOW
  the true resistance if High1 had a long upper shadow
- Conversely, a stock that hasn't broken the absolute high may have already cleared
  the real resistance zone

### Scoring impact:
- If you notice the key swing highs have long upper shadows → be SLIGHTLY MORE OPTIMISTIC
  about breakout potential (real barrier is lower than it looks): +0.5 to score
- If swing highs are clean (no shadows, solid bodies) → the stated high IS the real
  barrier → no adjustment
```

### Section B: Reversal Signal Requirement (反转信号确认)

```
## REVERSAL SIGNAL — Is the Stock Ready to Move?

A proper 收敛图 candidate should show AT LEAST ONE early sign that the
consolidation may be ending and a directional move is imminent.

### What counts as a reversal/trigger signal (ANY one of these):

POSITIVE signals (pattern is "coiled and ready"):
1) Most recent 1-2 candles show SMALL body with TIGHT range (< 3% of close)
   → extreme compression before breakout
2) Last candle has HIGHER low than previous day's low (even by 0.1%)
   → first sign of拒绝 further decline
3) Volume on the most recent day is the LOWEST in the entire 20-day window
   → complete dry-up, everyone waiting
4) Price is hugging MA5 closely (within 0.5%) → indecision at extreme
5) A bullish engulfing or hammer candle appeared in last 2 days
   (only if visible in the OHLCV data)

NEGATIVE signals (pattern is still deteriorating):
1) Last 2 days show NEW LOWER LOWS (not just flat, actually declining)
2) Volume is INCREASING while price is FLAT or FALLING → distribution
3) Price has broken below the most recent swing LOW → consolidation failing
4) Recent candle shows LONG LOWER SHADOW with lower close → selling pressure continues

### How this affects recommendation:

The presence/absence of reversal signal should tip the balance on BORDERLINE cases:
- Score 6 + NO reversal signal → consider downgrading to monitor instead of watch
- Score 5 + CLEAR reversal signal → can stay at watch or even promote
- Score 4 + strong reversal signal + tight end-zone → can upgrade to monitor
- Score 7 but NO reversal signal and declining recent action → downgrade to watch
  (example: 东阿阿胶 scenario — structure looks good but no trigger yet)

### Key principle:
A 收敛图 without ANY reversal signal is like a compressed spring that hasn't
been released yet. It MAY break out soon, but we cannot confirm WHEN.
For our trading system (tight stop-loss, 3-day time limit), timing matters.
Prefer setups where the trigger is IMMINENT (1-2 days away).
```

---

## Also update the STRICT FACTORS section

In the existing "STRICT FACTORS (-1 to score)" list, add one entry:

```
- NO reversal signal detected AND last 2 days show declining price action → -1
```

And in "GENEROUS FACTORS (+1 to score)" add:

```
- Clear reversal signal present (compression dry-up, higher low, hammer candle) → +1
- Key swing highs have long upper shadows (true resistance lower than apparent) → +0.5
```

---

## Testing

After modifying the prompt file, run:

```bash
cd /Users/kennytseng/stock_ai/autoresearch
uv run python layer2_screener.py --limit 50
```

Compare results with previous run:
- Total candidates should remain similar (~30-40)
- Watch count may shift (some promoted due to reversal signals, some demoted)
- The 東阿阿胶 case specifically: should score LOWER than before (was 7/watch,
  should drop to ~5-6 or change to monitor) because it lacks reversal signal
- DO NOT expect a dramatic drop in total recommendations — these are ±1 adjustments

## What NOT to do

- Do NOT turn these into hard reject rules (if X then skip)
- Do NOT modify any Python code — only edit the prompt text file
- Do NOT touch layer1_filter.py, layer2_screener.py code, or any other .py files
- Do NOT remove or rewrite existing sections of the prompt — only APPEND new ones
