# Roo Code Instructions: Update screener_system_prompt.txt — Add ST Filter + Stop-Loss Context

## Background

Two important rules were missing from the current system prompt:
1. ST/\*ST stocks must be excluded (these are stocks with delisting risk)
2. The system uses a tight -2.5% hard stop + 3-day time stop — the AI should calibrate its confidence around this

These must be added BEFORE running the overnight backtest so the iteration has a clean starting point.

---

## Change: Add to `rules/screener_system_prompt.txt`

Find the section that contains the output format / Output JSON instructions.
**Insert the following block IMMEDIATELY BEFORE that section** (before any line that says "Output" or "Return JSON"):

```
## MANDATORY EXCLUSION RULES (check these FIRST — instant skip if any apply):
1. SKIP any stock with "ST" or "*ST" in its name — these are stocks flagged by the exchange for financial risk / delisting risk
2. SKIP any stock that has already broken above and moved away from the convergence/pullback pattern (pattern already played out)
3. SKIP any stock showing consecutive lower highs (rapid high-point decline)
4. SKIP any stock in a weekly downtrend (weekly candles consistently declining)

## STOP-LOSS CONTEXT (use this to calibrate your confidence and recommendation):
The trading system uses a TIGHT exit strategy:
- Hard stop loss: exit immediately if price drops -2.5% from buy price
- Time stop: if the position has NEVER shown a peak gain of +4% or more within 3 trading days, exit on Day 4 regardless of price

What this means for your scoring:
- A stock that is "interesting but needs more time to develop" will be time-stopped for a small loss. Do NOT select it.
- Only select stocks that appear to be within 1-2 days of a breakout trigger point, with high probability of a quick +4% move.
- When uncertain between "skip" and "watch", choose "skip". The system would rather miss a winner than absorb a series of small -2.5% losses.
- Prioritize: near-breakout setup + compressed trading range + declining volume = high conviction
```

---

## Verify the change

After editing, the system prompt structure should look like this (in order):

1. Role and background description
2. Three-cycle methodology rules (weekly / pattern / entry)
3. Convergence pattern rules
4. Pullback (二踩) pattern rules
5. Scoring rubric
6. **[NEW] MANDATORY EXCLUSION RULES**
7. **[NEW] STOP-LOSS CONTEXT**
8. Output JSON format

---

## Do NOT change anything else in this file

Only insert the two new sections above. Do not modify any existing rules, scoring criteria, or output format.

---

## After editing

Run a quick test:
```bash
cd ~/stock_ai/autoresearch
uv run python layer2_screener.py 2>&1 | head -50
```

Verify:
- No ST stocks appear in the output
- The `recommendation` field shows more `skip` outputs (expected: 70-85% of input stocks should be skip)
- No crashes or JSON parsing errors
