"""
layer3_analyst.py
Autoresearch analysis engine.
Reads ALL backtest results accumulated so far (from all_days_backtest.csv)
+ live trading results, then uses DeepSeek V3 to analyze WIN/LOSS patterns
and generate rule update suggestions.

Run manually at any time, or automatically by master_orchestrator.py after each day.
"""

import os
import json
import csv
import re  # For regex pattern matching
import shutil
import urllib.request
from pathlib import Path
from datetime import datetime

AUTO_DIR = Path("~/stock_ai/autoresearch").expanduser()
BACKTEST_FILE = AUTO_DIR / "backtest_results" / "all_days_backtest.csv"
LIVE_FILE = AUTO_DIR / "trade_tracker" / "live_results.csv"
LAYER1_FILTER_PATH = AUTO_DIR / "layer1_filter.py"
SYSTEM_PROMPT_PATH = AUTO_DIR / "rules" / "screener_system_prompt.txt"
ITERATION_LOG = AUTO_DIR / "rules" / "iteration_log.md"
BACKTEST_FINDINGS = AUTO_DIR / "rules" / "backtest_findings.md"
LIVE_FINDINGS = AUTO_DIR / "rules" / "live_findings.md"
REPORTS_DIR = AUTO_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
MANUAL_PICKS_FILE = AUTO_DIR / "data" / "manual_picks.csv"
RULES_DIR = AUTO_DIR / "rules"

def write_rules(rule_name: str, new_content: str, backup: bool = True) -> None:
    """Write updated rule content back to the rules directory.
    
    Args:
        rule_name: Name of the rule file (e.g., 'screener_system_prompt.txt')
        new_content: New content to write
        backup: If True, create a backup copy before writing
    """
    rule_path = RULES_DIR / rule_name
    if not rule_path.exists():
        print(f"[AUTORESEARCH] ERROR: Rule file not found: {rule_path}")
        return
    
    if backup:
        backup_path = RULES_DIR / f"{rule_path.stem}.backup{rule_path.suffix}"
        shutil.copy(rule_path, backup_path)
        print(f"[AUTORESEARCH] Backed up {rule_name} -> {backup_path.name}")
    
    with open(rule_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"[AUTORESEARCH] Updated rules/{rule_name}")


def load_backtest_results():
    if not BACKTEST_FILE.exists():
        return []
    with open(BACKTEST_FILE, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_live_results():
    if not LIVE_FILE.exists():
        return []
    with open(LIVE_FILE, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)

def summarize_results(results, label):
    if not results:
        return f"{label}: No data yet."

    wins = [r for r in results if r.get("outcome") == "WIN"]
    losses = [r for r in results if r.get("outcome") == "LOSS"]
    flats = [r for r in results if r.get("outcome") == "FLAT"]
    total = len(results)
    win_rate = len(wins) / total * 100 if total else 0

    by_pattern = {}
    for r in results:
        pt = r.get("pattern", "unknown")
        by_pattern.setdefault(pt, []).append(r)
    pattern_stats = []
    for pt, items in by_pattern.items():
        w = len([x for x in items if x.get("outcome") == "WIN"])
        pattern_stats.append(f"  - {pt}: {w}/{len(items)} wins ({w/len(items)*100:.0f}%)")

    by_rec = {}
    for r in results:
        rec = r.get("recommendation", "unknown")
        by_rec.setdefault(rec, []).append(r)
    rec_stats = []
    for rec, items in by_rec.items():
        w = len([x for x in items if x.get("outcome") == "WIN"])
        rec_stats.append(f"  - {rec}: {w}/{len(items)} wins ({w/len(items)*100:.0f}%)")

    high_score = [r for r in results if float(r.get("score", 0)) >= 70]
    low_score = [r for r in results if float(r.get("score", 0)) < 70]
    hs_w = len([r for r in high_score if r.get("outcome") == "WIN"])
    ls_w = len([r for r in low_score if r.get("outcome") == "WIN"])
    hs_wr = hs_w/len(high_score)*100 if high_score else 0
    ls_wr = ls_w/len(low_score)*100 if low_score else 0

    summary = f"""{label} SUMMARY:
Total: {total} | WIN: {len(wins)} ({win_rate:.1f}%) | LOSS: {len(losses)} | FLAT: {len(flats)}

By Pattern:
{chr(10).join(pattern_stats)}

By Recommendation:
{chr(10).join(rec_stats)}

By Score:
  - High score (>=70): {hs_w}/{len(high_score)} wins ({hs_wr:.0f}%)
  - Low score (<70):   {ls_w}/{len(low_score)} wins ({ls_wr:.0f}%)

WIN Examples (top 5):
"""
    for r in wins[:5]:
        summary += f"\n  [{r.get('date')}] {r.get('code')}: score={r.get('score')} | {r.get('reason','')[:120]}"

    summary += f"\n\nLOSS Examples (top 5):\n"
    for r in losses[:5]:
        summary += f"\n  [{r.get('date')}] {r.get('code')}: score={r.get('score')} | {r.get('reason','')[:120]}"

    return summary

def load_manual_picks():
    """Load user's manually selected historical picks as ground-truth training data."""
    if not MANUAL_PICKS_FILE.exists():
        print(f"  [INFO] No manual picks file found at {MANUAL_PICKS_FILE}")
        return []
    
    picks = []
    with open(MANUAL_PICKS_FILE, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            result = row.get("结果", "").strip().upper()
            if result == "N/A" or result == "":
                continue  # Skip stocks where buy trigger was never hit
            picks.append({
                "date": row.get("选股日期", "").strip(),
                "code": row.get("股票代码", "").strip(),
                "name": row.get("股票名称", "").strip(),
                "buy_date": row.get("买入日期", "").strip(),
                "outcome": result,  # WIN / LOSS
                "pattern": row.get("图形类型", "").strip(),
                "note": row.get("备注", "").strip(),
                "source": "manual_human"  # mark as human-selected ground truth
            })
    print(f"  Loaded {len(picks)} manual picks ({sum(1 for p in picks if p['outcome']=='WIN')} WIN, "
          f"{sum(1 for p in picks if p['outcome']=='LOSS')} LOSS)")
    return picks

def _extract_layer1_tunable_params() -> str:
    """Extract tunable constants from layer1_filter.py for Layer3 to consider.
    
    ONLY parameters that are safe to tune (constants at module level, not core logic).
    Returns a formatted string describing current values.
    """
    if not LAYER1_FILTER_PATH.exists():
        return "(layer1_filter.py not found)"
    
    content = LAYER1_FILTER_PATH.read_text(encoding="utf-8")
    params = []
    
    # Extract key tunable constants (pattern: NAME = value # comment)
    import re
    tunable_patterns = [
        r'(CONVERGENCE_MAX_RATIO)\s*=\s*([\d.]+)\s*(#.*)?',
        r'(CONVERGENCE_END_ZONE)\s*=\s*([\d]+)\s*(#.*)?',
        r'(MIN_TURNOVER_20D)\s*=\s*([\d_]+)\s*(#.*)?',
        r'(VOLUME_DECLINE_RATIO)\s*=\s*([\d.]+)\s*(#.*)?',
        r'(REQUIRED_HISTORY_DAYS)\s*=\s*([\d]+)\s*(#.*)?',
        r'(MA_CROSS_LOOKBACK)\s*=\s*([\d]+)\s*(#.*)?',
    ]
    
    for pattern in tunable_patterns:
        match = re.search(pattern, content)
        if match:
            name, value, comment = match.groups()
            comment = comment or ""
            params.append(f"  - {name} = {value} {comment}")
    
    if not params:
        return "(No tunable constants found in layer1_filter.py)"
    
    return "\n".join(params)


def generate_ai_analysis(backtest_summary, live_summary, all_backtest_results, manual_picks=None):
    with open(SYSTEM_PROMPT_PATH) as f:
        current_rules = f.read()
    
    # Also load L1 tunable params for the AI to consider
    l1_tunable = _extract_layer1_tunable_params()

    # Count iterations
    iteration_num = 1
    if ITERATION_LOG.exists():
        with open(ITERATION_LOG) as f:
            iteration_num = f.read().count("## 20") + 1

    # Build manual picks section
    manual_section = ""
    if manual_picks:
        wins = [p for p in manual_picks if p["outcome"] == "WIN"]
        losses = [p for p in manual_picks if p["outcome"] == "LOSS"]
        manual_section = f"""
## HUMAN GROUND-TRUTH PICKS ({len(manual_picks)} total, {len(wins)} WIN, {len(losses)} LOSS):
These are stocks the user manually selected using their pattern recognition expertise.
They are the gold standard for what correct pattern selection looks like.

WIN examples (human correctly identified):
{chr(10).join(f'  [{p["date"]}→{p["buy_date"]}] {p["code"]} {p["name"]}: {p["pattern"]} | {p["note"][:100]}' for p in wins)}

LOSS examples (human selected but hit stop-loss):
{chr(10).join(f'  [{p["date"]}→{p["buy_date"]}] {p["code"]} {p["name"]}: {p["pattern"]} | {p["note"][:100]}' for p in losses)}

Cross-reference questions:
- Did the AI rules correctly identify these WIN stocks?
- Did the AI rules incorrectly filter OUT any of these WIN stocks? (false negatives = rules too strict)
- Did the AI rules include any of these LOSS stocks? (rules not catching the failure signal)
"""

    prompt = f"""You are an expert A-share trading strategy analyst. Respond in Chinese.
Analyze the backtesting results below and propose concrete rule updates.

## CURRENT LAYER2 SYSTEM PROMPT (screener_system_prompt.txt):
{current_rules}

## CURRENT LAYER1 TUNABLE PARAMETERS (layer1_filter.py constants):
These are numeric thresholds that control how loose/tight the coarse filter is.
They are SAFE to adjust — changing them does NOT alter core pattern detection logic.
{l1_tunable}

IMPORTANT: Layer 1 parameters (thresholds like CONVERGENCE_MAX_RATIO, MIN_TURNEVER_20D, etc.)
can be tuned based on win-rate evidence. These are NOT core logic — they are knobs
that control the "looseness" of each filter stage. As more test data accumulates,
these should gradually converge to optimal values.

## BACKTEST DATA ({len(all_backtest_results)} total picks):
{backtest_summary}

## LIVE TRADING DATA:
{live_summary}
{manual_section}

## YOUR TASK:
Answer in Chinese. Be specific and data-driven.

1. What is the overall win rate? Which pattern (convergence vs pullback) wins more?
2. What do WIN cases have in common? (specific numbers: end-zone width, volume decline %, score threshold, etc.)
3. What do LOSS cases have in common?
4. Which recommendation level (select/watch) has the best win rate?
5. What specific rule should be ADDED, REMOVED, or MODIFIED? (MAX 1 CHANGE ONLY. Be very conservative.)
   - You may suggest changes to Layer2 system prompt (scoring criteria, thresholds)
   - You may also suggest tuning Layer1 numeric parameters (CONVERGENCE_MAX_RATIO, MIN_TURNOVER_20D, etc.)
   - For L1 parameter changes: specify the param name, current value, proposed value, and evidence
   - IMPORTANT: Never suggest changing core detection logic in layer1_filter.py — only the constant values
6. Cross-reference with human ground-truth picks:
   - Which human WIN picks did the AI rules correctly identify?
   - Which human WIN picks did the AI rules MISS? (This is the most important gap to fix)
   - Which human LOSS picks did the AI rules fail to filter out?
   - Based on the human WIN examples, what pattern features are currently underdefined in the rules?

Respond ONLY with valid JSON (no markdown, no explanation around it):
{{
  "analysis": "Detailed Chinese analysis, 2-3 paragraphs, citing specific numbers from the data above",
  "overall_win_rate": "e.g. 62%",
  "convergence_win_rate": "e.g. 58%",
  "pullback_win_rate": "e.g. 67%",
  "best_recommendation": "select or watch",
  "win_features": ["Feature 1", "Feature 2", "Feature 3"],
  "loss_features": ["Feature 1", "Feature 2", "Feature 3"],
  "rule_suggestions": [
    {{
      "action": "ADD or REMOVE or MODIFY",
      "location": "rule number or section name in the system prompt",
      "current": "exact text of the current rule (copy from above)",
      "proposed": "exact new text",
      "reason": "why this specific change would improve the win rate, citing evidence from the data"
    }}
  ],
  "confidence": "high if {len(all_backtest_results)} > 30, else medium"
}}"""

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return {"error": "DEEPSEEK_API_KEY not set"}

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
        content = result["choices"][0]["message"]["content"]
        start = content.find("{")
        end = content.rfind("}") + 1
        return json.loads(content[start:end])

def apply_rule_updates(ai_result: dict, dry_run: bool = True) -> None:
    """Apply rule updates suggested by AI analysis.
    
    Supports two types of updates:
    1. Layer 2: Modify rules/screener_system_prompt.txt (full text replacement)
    2. Layer 1: Modify tunable constants in layer1_filter.py (safe parameter tweaks only)
    
    Args:
        ai_result: The AI analysis result containing rule_suggestions
        dry_run: If True, only log what would be changed without writing
    """
    import re
    
    suggestions = ai_result.get("rule_suggestions", [])
    if not suggestions:
        print("[AUTORESEARCH] No rule suggestions to apply")
        return
    
    # Only apply the top 1 suggestion (conservative approach)
    top_suggestion = suggestions[0]
    action = top_suggestion.get("action", "")
    location = top_suggestion.get("location", "")
    proposed = top_suggestion.get("proposed", "")
    
    # Determine target file and method
    is_l1_param = any(
        keyword in location.upper() 
        for keyword in ["CONVERGENCE_MAX_RATIO", "CONVERGENCE_END_ZONE", "MIN_TURNOVER",
                        "VOLUME_DECLINE", "REQUIRED_HISTORY", "LAYER1", "END_ZONE_WIDTH",
                        "FIRST_RALLY", "layer1_filter"]
    )
    
    if is_l1_param:
        # === LAYER 1: Tunable constant update ===
        _apply_l1_update(location, proposed, action, dry_run)
    else:
        # === LAYER 2: System prompt modification (original logic) ===
        if action == "MODIFY" and location and proposed:
            # Layer2 system prompt is stored in screener_system_prompt.txt
            # (layer2_system_prompt.txt does not exist - this is the correct file)
            if "screener_system_prompt" in location.lower() or "system prompt" in location.lower() or "layer2" in location.lower():
                rule_file = "screener_system_prompt.txt"
            else:
                rule_file = "screener_system_prompt.txt"  # default
            
            rule_path = RULES_DIR / rule_file
            if not rule_path.exists():
                print(f"[AUTORESEARCH] ERROR: Rule file not found: {rule_path}")
                return
            
            if dry_run:
                print(f"\n[AUTORESEARCH] [DRY-RUN] Would modify {rule_file}:")
                print(f"  Action: {action}")
                print(f"  Location: {location}")
                print(f"  Proposed change (first 200 chars): {proposed[:200]}")
            else:
                print(f"\n[AUTORESEARCH] Applying rule update to {rule_file}...")
                write_rules(rule_file, proposed, backup=True)
                print(f"[AUTORESEARCH] Rule update applied successfully")
        else:
            print(f"[AUTORESEARCH] Cannot apply suggestion: action={action}, location={location}")


def _apply_l1_update(location: str, proposed: str, action: str, dry_run: bool) -> None:
    """Apply a safe parameter update to layer1_filter.py.
    
    SAFETY GUARD: Only allows changing numeric constants at module level.
    Will NOT modify function bodies, class definitions, or control flow.
    """
    ALLOWED_PARAM_NAMES = {
        "CONVERGENCE_MAX_RATIO", "CONVERGENCE_END_ZONE", "MIN_TURNOVER_20D",
        "VOLUME_DECLINE_RATIO", "REQUIRED_HISTORY_DAYS", "MA_CROSS_LOOKBACK",
    }
    
    if not LAYER1_FILTER_PATH.exists():
        print(f"[AUTORESEARCH] ERROR: layer1_filter.py not found at {LAYER1_FILTER_PATH}")
        return
    
    content = LAYER1_FILTER_PATH.read_text(encoding="utf-8")
    
    # Extract the parameter name from location
    param_name = None
    for name in ALLOWED_PARAM_NAMES:
        if name.upper() in location.upper():
            param_name = name
            break
    
    if not param_name:
        print(f"[AUTORESEARCH] [BLOCKED] Location '{location}' does not match any allowed L1 parameter.")
        print(f"  Allowed params: {', '.join(sorted(ALLOWED_PARAM_NAMES))}")
        print(f"  Layer3 CANNOT modify core logic — only these tunable constants are safe to adjust.")
        return
    
    # Find the current value
    pattern = re.compile(rf'^{param_name}\s*=\s*([\d.]+)', re.MULTILINE)
    match = pattern.search(content)
    if not match:
        print(f"[AUTORESEARCH] ERROR: Could not find '{param_name}' in layer1_filter.py")
        return
    
    old_value = match.group(1)
    
    # Parse the new value from proposed text
    new_value_match = re.search(r'[\d.]+', proposed)
    if not new_value_match:
        print(f"[AUTORESEARCH] ERROR: Could not extract numeric value from proposed: {proposed[:100]}")
        return
    new_value = new_value_match.group()
    
    # Sanity check: reject changes that are too drastic (>50% relative change)
    try:
        old_num = float(old_value)
        new_num = float(new_value)
        if old_num > 0 and abs(new_num - old_num) / old_num > 0.5:
            print(f"[AUTORESEARCH] [BLOCKED] Change too drastic: {param_name} {old_value} → {new_value} "
                  f"({abs(new_num-old_num)/old_num*100:.0f}% change). Max allowed: ±50%")
            return
    except ValueError:
        pass
    
    new_line = f"{param_name} = {new_value}"
    
    if dry_run:
        print(f"\n[AUTORESEARCH] [DRY-RUN] Would modify layer1_filter.py:")
        print(f"  Parameter: {param_name}")
        print(f"  Current:   {old_value}")
        print(f"  Proposed:  {new_value}")
        print(f"  Line would be: {new_line}")
    else:
        # Perform the replacement
        new_content = pattern.sub(new_line, content)
        LAYER1_FILTER_PATH.write_text(new_content, encoding="utf-8")
        # Also create backup of original
        backup_path = LAYER1_FILTER_PATH.with_suffix(".py.backup")
        shutil.copy(LAYER1_FILTER_PATH, backup_path)
        print(f"\n[AUTORESEARCH] Updated layer1_filter.py:")
        print(f"  {param_name}: {old_value} → {new_value}")
        print(f"  Backup saved to: {backup_path.name}")


def write_iteration_log_summary(ai_result: dict, all_backtest: list, all_live: list, now: datetime) -> None:
    """Write a structured iteration log summary to iteration_log.md."""
    iteration_num = 1
    if ITERATION_LOG.exists():
        with open(ITERATION_LOG) as f:
            iteration_num = f.read().count("## 20") + 1
    
    changes_made = []
    for sug in ai_result.get("rule_suggestions", []):
        changes_made.append(f"- {sug.get('action', '')} {sug.get('location', '')}: {sug.get('reason', '')[:100]}")
    
    changes_md = "\n".join(changes_made) if changes_made else "- No changes applied (dry-run mode)"
    
    summary = f"""
## Autoresearch Iteration #{iteration_num}

**Date:** {now.strftime('%Y-%m-%d')}
**Analyzed:** {len(all_backtest)} backtest days, {len(all_live)} live trades
**Win rate:** {ai_result.get('overall_win_rate', 'N/A')}
**Changes made:**
{changes_md}
"""
    
    with open(ITERATION_LOG, "a", encoding="utf-8") as f:
        f.write(summary)
    print(f"[AUTORESEARCH] Iteration log updated: iteration #{iteration_num}")


def parse_args():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description="Layer 3 Analyst: Analyze backtest results and suggest rule updates")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Only analyze and log, do NOT apply rule changes (default: True)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Actually apply the suggested rule changes to rule files"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    now = datetime.now()
    dry_run = not args.apply  # Default to dry-run unless --apply is passed
    print(f"Layer 3 Analyst -- {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'APPLY' if not dry_run else 'DRY-RUN'} (use --apply to write changes)")

    all_backtest = load_backtest_results()
    all_live = load_live_results()
    manual_picks = load_manual_picks()

    backtest_summary = summarize_results(all_backtest, "BACKTEST")
    live_summary = summarize_results(all_live, "LIVE TRADING")

    print(backtest_summary)
    print("\n" + live_summary)

    print("\nCalling DeepSeek V3 for AI analysis...")
    ai_result = generate_ai_analysis(backtest_summary, live_summary, all_backtest, manual_picks)

    if "error" in ai_result:
        print(f"API Error: {ai_result['error']}")
        return

    # Save iteration report
    suggestions_md = ""
    for i, sug in enumerate(ai_result.get("rule_suggestions", []), 1):
        suggestions_md += f"""### 建议 {i}: [{sug['action']}] {sug.get('location', '')}
- 当前规则: {sug.get('current', 'N/A')}
- 建议修改: {sug.get('proposed', 'N/A')}
- 理由: {sug.get('reason', 'N/A')}

"""

    report = f"""# Layer 3 迭代报告 -- {now.strftime('%Y-%m-%d %H:%M')}

## 数据概览
- 回测总 picks: {len(all_backtest)}
- 真实持仓: {len(all_live)}
- 整体胜率: {ai_result.get('overall_win_rate', 'N/A')}

## 形态胜率
- 收敛（Convergence）: {ai_result.get('convergence_win_rate', 'N/A')}
- 二踩（Pullback）: {ai_result.get('pullback_win_rate', 'N/A')}

## WIN 赢家共同特征
{chr(10).join(f'- {f}' for f in ai_result.get('win_features', []))}

## LOSS 输家共同特征
{chr(10).join(f'- {f}' for f in ai_result.get('loss_features', []))}

## 最佳推荐级别
{ai_result.get('best_recommendation', 'N/A')}

## AI 深度分析
{ai_result.get('analysis', '')}

## 规则更新建议（最多应用1条）
{suggestions_md}
## 操作步骤
1. 阅读以上建议
2. 选择最影响胜率的1条进行修改（不要贪多）
3. 修改 rules/screener_system_prompt.txt
4. 重新跑 master_orchestrator.py 验证效果
"""

    report_file = REPORTS_DIR / f"iteration_report_{now.strftime('%Y%m%d_%H%M')}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport: {report_file}")

    # Update backtest_findings.md
    findings = f"""# Backtest Findings -- {now.strftime('%Y-%m-%d')}

Total picks: {len(all_backtest)} | Win rate: {ai_result.get('overall_win_rate', 'N/A')}
Convergence: {ai_result.get('convergence_win_rate', 'N/A')} | Pullback: {ai_result.get('pullback_win_rate', 'N/A')}

## WIN Features
{chr(10).join(f'- {f}' for f in ai_result.get('win_features', []))}

## LOSS Features
{chr(10).join(f'- {f}' for f in ai_result.get('loss_features', []))}
"""
    with open(BACKTEST_FINDINGS, "w", encoding="utf-8") as f:
        f.write(findings)

    # P4: Apply rule updates (if --apply flag is passed)
    apply_rule_updates(ai_result, dry_run=dry_run)

    # P4: Write iteration log summary
    write_iteration_log_summary(ai_result, all_backtest, all_live, now)

    print("\nRule suggestions:")
    for sug in ai_result.get("rule_suggestions", []):
        print(f"  [{sug['action']}] {sug.get('location', '')}")
        print(f"    Proposed: {sug.get('proposed', '')[:100]}")

if __name__ == "__main__":
    main()
