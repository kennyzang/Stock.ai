# Roo_Code Instructions: P2 + P3 + P4 — Convergence Pattern Refinements + Autoresearch Write Capability

---

## P2 — 均线缠绕检查 (MA Entanglement Check)

### What the strategy says

From the original strategy document (`策略总结-学习笔记.docx`):

> **均线缠绕**: Short-term MAs (5/10/20-day) should be intertwined/near each other with small divergence — a sign the market is consolidating, not trending.

> **不要选的图**: 高点下降太快、收敛区间太宽、**低位收敛（左边套牢盘太多）**、过站（已突破收敛区间）、N型（没有完整的三高两低）

Key insight: **低位收敛要排除** → implies **高位收敛也要排除** (P3).

### Implementation

Add a new function `ma_entanglement_check` in `layer1_filter.py` near the other convergence checks.

**Logic:**
- Compute 5-day MA, 10-day MA, 20-day MA on `close` prices (last 20 days)
- **Entanglement condition**: The spread between the 5-day MA and 10-day MA should be small relative to the stock's volatility
  - Use `std_ma_spread = std(ma5 - ma10)` over the last 10 days
  - Use `avg_price = mean(close)` over the last 10 days
  - Pass if `std_ma_spread / avg_price < 0.01` (1% threshold — MAs are tightly bundled)
  - Alternative simpler check: `abs(ma5[-1] - ma10[-1]) / close.iloc[-1] < 0.02` (2% of price)
- **Direction ambiguity**: All three MAs should be roughly at the same level (not diverging upward or downward)
  - Check `abs(ma5 - ma10) / close < 0.02` AND `abs(ma10 - ma20) / close < 0.03`
  - Both conditions must be true

**Call site:** Insert in `convergence_prefilter()` after `three_highs_two_lows()` and before the end-zone width check:

```python
# P2 FIX: 均线缠绕 — MAs should be tightly intertwined in consolidation
if not ma_entanglement_check(recent_20d):
    return False
```

---

## P3 — 高位收敛排除 + 低位收敛排除 (High/Low Position Convergence Exclusion)

### What the strategy says

From the original strategy document:

> **不要选的图**: 低位收敛（左边套牢盘太多）

"低位收敛" = convergence pattern formed at a low position → lots of selling pressure from previous buyers trapped below.

The inverse is also problematic: **高位收敛** (high-position convergence) — if the entire 20-day range is near the recent high, there's also overhead supply risk.

### Implementation

Add a new function `convergence_position_check` in `layer1_filter.py`.

**Logic — Low Position Exclusion (低位收敛排除):**
- Compute the **position ratio** of the convergence zone within the 20-day range:
  - `low_ratio = (min_price_20d) / (max_price_20d - min_price_20d)`
  - If `low_ratio < 0.15` → convergence zone is near the bottom of the 20-day range → reject ("低位收敛")
  - This means: if the convergence zone sits in the bottom 15% of the 20-day range, there are likely trapped buyers from earlier — they will sell when price approaches.

**Logic — High Position Exclusion (高位收敛排除):**
- Compute the **height** of the convergence zone relative to recent history:
  - `convergence_high_in_range = convergence_high / max_price_60d` (use 60-day data if available)
  - If `convergence_high_in_range > 0.95` → convergence zone is near the 60-day high → reject ("高位收敛")
  - Reason: limited upside room, likely overhead supply from recent buyers

**Combined condition (either one triggers rejection):**
```python
# P3 FIX: 排除高位收敛和低位收敛 — bad convergence position
if not convergence_position_check(history_df):
    return False
```

**Note:** If 60-day data is not readily available, use 20-day max as a proxy (accept slightly less accurate but still useful filtering).

---

## P4 — Enable Autoresearch Write Capability

### Current State
`layer3_analyst.py` currently reads rules from `rules/screener_system_prompt.txt` but does NOT modify them. The Autoresearch loop can only observe and report — it cannot apply changes.

### Goal
Enable `layer3_analyst.py` to **actually write/modify rule files** based on backtest findings.

### Implementation

**Step 1: Read `layer3_analyst.py` and identify where it reads rules**
- Find the `RULES_DIR` / `rules_path` variable
- Find where it currently calls `read()` or `open()` on rule files

**Step 2: Add a `write_rules()` function**
```python
def write_rules(rule_name: str, new_content: str, backup: bool = True) -> None:
    """Write updated rule content back to the rules directory."""
    rules_dir = Path("~/stock_ai/autoresearch/rules").expanduser()
    rule_path = rules_dir / rule_name
    if backup:
        backup_path = rules_dir / f"{rule_path.stem}.backup{rule_path.suffix}"
        shutil.copy(rule_path, backup_path)
    with open(rule_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"[AUTORESEARCH] Updated rules/{rule_name}")
```

**Step 3: Integrate with the analysis logic**
- After the LLM analysis generates recommended rule changes, write the changes to `rules/backtest_findings.md` or the relevant rule file
- Add a flag: `--dry-run` (default=True) so changes are NOT applied automatically — just logged for human review first
- When `--apply` flag is passed, actually write the changes

**Step 4: Add a summary output**
After writing rules, output a markdown summary:
```markdown
## Autoresearch Iteration #[N]

**Date:** YYYY-MM-DD
**Analyzed:** X backtest days, Y live trades
**Win rate:** Z%
**Changes made:**
- [rule file]: [change description]
```

Save this to `rules/iteration_log.md`.

---

## Execution Order

**IMPORTANT: Execute in order. Complete P2 first, test, then P3, then P4.**

```bash
cd ~/stock_ai

# P2: Test MA entanglement check
uv run python layer1_filter.py --mode convergence --limit 50

# P3: Test position exclusion
uv run python layer1_filter.py --mode convergence --limit 50

# P4: Verify layer3_analyst.py write capability
uv run python layer3_analyst.py --dry-run
```

---

## Rules

- **P2, P3, P4 are separate PRs**: Do NOT combine them into one. Finish P2 → test → P3 → test → P4 → test
- **Only modify the specified function**: Each task touches one new function + one call site
- **Preserve all existing logic**: Every existing check in `convergence_prefilter()` stays intact
- **No new dependencies**: Use only `numpy` and standard library
- **Debug logging**: Add print statements for each new function

---

## Reference Files

- `autoresearch/layer1_filter.py` (P2, P3 targets)
- `autoresearch/layer3_analyst.py` (P4 target)
- `autoresearch/rules/` directory (P4 — rule files to read/write)
- `autoresearch/teaching/策略总结-学习笔记.docx` (strategy source of truth)
