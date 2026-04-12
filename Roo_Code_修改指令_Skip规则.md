# Roo Code Instructions: Fix System Prompt — Add Skip Rules for DeepSeek V3

## Context

After switching from GPT-4o to DeepSeek V3, the model stopped outputting `skip` for non-qualifying stocks. Out of 141 stocks, it outputs:
- `monitor` / `wait` / `watch` for all 141 stocks
- `skip`: 0 stocks
- `select`: 0 stocks

This means DeepSeek V3 doesn't know when to output `skip` — the system prompt has no explicit skip rules. GPT-4o apparently inferred skip rules from context, but DeepSeek V3 needs them stated explicitly.

## File to Modify

`~/stock_ai/autoresearch/rules/screener_system_prompt.txt`

## Modification

After the existing pattern rules section (after line 18, before the Output JSON line), add the following block:

---

```markdown
## RECOMMENDATION DECISION TREE

Apply these rules **in order**. Stop at the first match:

**→ "skip"** (DO NOT output monitor or watch) if the stock:
- Fails 2 or more of the 7 convergence rules above, OR
- Fails 2 or more of the 5 pullback rules above, OR
- Is already broken out above the consolidation zone, OR
- Is a low-position convergence (fails Rule 7 of convergence), OR
- Shows rapid declining highs (violates Rule 5 of convergence), OR
- Is in a clear downtrend on weekly timeframe

**→ "select"** ONLY if ALL of these are true:
- Pattern type is clearly identifiable (convergence OR pullback)
- At least 5 of 7 convergence rules are satisfied, OR at least 4 of 5 pullback rules
- End-zone width < 8%
- Volume confirmed declining in convergence zone (or confirmed contracting in pullback)
- Price position is mid-to-high (not low-position)
- NOT already broken out

**→ "monitor"** if:
- Pattern mostly forms but 1-2 minor criteria are borderline or not yet confirmed
- e.g., end-zone width is 7-9% (slightly wide), or volume trend is unclear
- The stock shows potential but needs more time to confirm

**→ "watch"** if:
- Pattern clearly passes most criteria and shows a valid setup
- Entry signal may be imminent (within 1-3 days)
- But minor uncertainty remains (volume, timing, or position)

**→ "wait"** if:
- Weekly trend is questionable (slight downward bias)
- Not a clear failure, but not a confident setup either
- Re-evaluate in 1-2 weeks

## Output JSON:
{"pattern_type","score","confidence","key_positives","key_negatives","recommendation","reason"}
```

---

## Find & Replace in the File

**Find this block** (lines 19-20 of the current file):
```
Output JSON: {"pattern_type","score","confidence","key_positives","key_negatives","recommendation","reason"}
```

**Replace it with:**

```
## RECOMMENDATION DECISION TREE

Apply these rules in order. Stop at the first match:

→ "skip" (DO NOT output monitor or watch) if the stock:
- Fails 2 or more of the 7 convergence rules above, OR
- Fails 2 or more of the 5 pullback rules above, OR
- Is already broken out above the consolidation zone, OR
- Is a low-position convergence (fails Rule 7 of convergence), OR
- Shows rapid declining highs (violates Rule 5 of convergence), OR
- Is in a clear downtrend on weekly timeframe

→ "select" ONLY if ALL of these are true:
- Pattern type is clearly identifiable (convergence OR pullback)
- At least 5 of 7 convergence rules are satisfied, OR at least 4 of 5 pullback rules
- End-zone width < 8%
- Volume confirmed declining in convergence zone (or confirmed contracting in pullback)
- Price position is mid-to-high (not low-position)
- NOT already broken out

→ "monitor" if:
- Pattern mostly forms but 1-2 minor criteria are borderline or not yet confirmed
- e.g., end-zone width is 7-9% (slightly wide), or volume trend is unclear
- The stock shows potential but needs more time to confirm

→ "watch" if:
- Pattern clearly passes most criteria and shows a valid setup
- Entry signal may be imminent (within 1-3 days)
- But minor uncertainty remains (volume, timing, or position)

→ "wait" if:
- Weekly trend is questionable (slight downward bias)
- Not a clear failure, but not a confident setup either
- Re-evaluate in 1-2 weeks

## Output JSON:
{"pattern_type","score","confidence","key_positives","key_negatives","recommendation","reason"}
```

