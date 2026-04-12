# Roo Code Instructions: Implement Layer 3 — Autonomous Overnight Backtest & Iteration

## Goal

Run a fully autonomous overnight backtest loop:
- 10 trading days, one day at a time
- After each day completes → immediately run Autoresearch iteration → record findings
- Repeat continuously until all 10 days are done
- Estimated total time: **~3-4 hours** (10 days × ~20 min/day)

## Architecture

```
master_orchestrator.py   ← NEW: the one script to rule them all
    │
    ├── For each trading day:
    │     ├── layer1_filter.py --date YYYY-MM-DD   → candidates for that day
    │     ├── layer2_screener.py                   → AI scores for those candidates
    │     ├── Check 5-day forward price             → WIN/LOSS/FLAT
    │     └── Append to backtest_results CSV        ← saved AFTER each day (not at the end)
    │
    └── After each day's data is saved:
          ├── layer3_analyst.py                    → analyze what's collected so far
          ├── record insights to rules/*.md         ← findings update incrementally
          └── sleep 30s → next day
```

---

## Step 1: Create Directory Structure

```bash
cd ~/stock_ai/autoresearch
mkdir -p backtest_results
mkdir -p trade_tracker
mkdir -p reports
touch rules/backtest_findings.md
touch rules/live_findings.md
touch rules/iteration_log.md
```

Initialize each file with a header:

```bash
# rules/backtest_findings.md
echo "# Backtest Findings

(Updated after each day's iteration)
" > rules/backtest_findings.md

# rules/live_findings.md
echo "# Live Trading Findings

(Updated as real positions close)
" > rules/live_findings.md

# rules/iteration_log.md
echo "# Iteration Log

Each entry records what the AI learned after each day's backtest + analysis.
Max 1 rule change per iteration.
" > rules/iteration_log.md
```

---

## Step 2: Check Existing Scripts for `--date` Support

Before writing the orchestrator, check if the existing scripts support `--date`:

```bash
cd ~/stock_ai/autoresearch

# Check layer1_filter.py
grep -n "argparse\|--date\|sys.argv" layer1_filter.py | head -20

# Check layer2_screener.py
grep -n "argparse\|--date\|sys.argv" layer2_screener.py | head -20
```

### If `--date` is NOT supported (likely):

Add argparse support to `layer1_filter.py`. Find the main block and add:

```python
# Near the bottom of layer1_filter.py, find main() and add:
import argparse

def main():
    parser = argparse.ArgumentParser(description="Layer 1 stock filter")
    parser.add_argument("--date", type=str, default=None,
                        help="Backtest date in YYYY-MM-DD format (default: today)")
    args = parser.parse_args()
    target_date = args.date  # Use this in your existing logic
    ...
```

### If `--date` is supported:

Great. Just note the parameter name for use in the orchestrator.

---

## Step 3: Create master_orchestrator.py

This is the MOST IMPORTANT file. Write it to `~/stock_ai/autoresearch/master_orchestrator.py`:

```python
"""
master_orchestrator.py
Fully autonomous overnight backtest + Autoresearch iteration loop.
Runs one trading day → analyzes it → records findings → moves to next day.

Usage:
  # Set API key first:
  export DEEPSEEK_API_KEY="your-key-here"

  # Run the full 10-day backtest + iteration loop:
  uv run python master_orchestrator.py

  # Or run just 3 days for testing:
  uv run python master_orchestrator.py --days 3
"""

import os
import sys
import json
import time
import csv
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ========== CONFIG ==========
BACKTEST_DAYS = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 10
MIN_HOLDING_DAYS = 5
MAX_STOCKS_PER_DAY = 20
ANALYSIS_DELAY = 30  # seconds to wait after each day's analysis before next day
AUTO_DIR = Path("~/stock_ai/autoresearch").expanduser()
RESULTS_FILE = AUTO_DIR / "backtest_results" / "all_days_backtest.csv"
# ============================

# Ensure DEEPSEEK_API_KEY is set
if not os.environ.get("DEEPSEEK_API_KEY"):
    print("ERROR: DEEPSEEK_API_KEY not set. Run: export DEEPSEEK_API_KEY='your-key'")
    sys.exit(1)

def get_trading_days(n=30):
    """Get the last N trading days (Mon-Fri, skipping today if market is still open)."""
    days = []
    d = datetime.now()
    # Skip today if before 16:00 (market may still be trading)
    if d.hour < 16:
        d -= timedelta(days=1)
    while len(days) < n:
        if d.weekday() < 5:  # Mon=0, ..., Fri=4
            days.append(d)
        d -= timedelta(days=1)
    return days

def run_command(cmd, cwd, description):
    """Run a subprocess command, print output, return stdout."""
    print(f"\n>>> {description}")
    result = subprocess.run(
        cmd, capture_output=True, text=True,
        cwd=str(cwd), shell=sys.platform == "darwin" or True
    )
    if result.stdout:
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    if result.stderr and "warning" not in result.stderr.lower():
        print(f"[STDERR] {result.stderr[-300:]}")
    return result.stdout, result.returncode

def run_layer1_for_date(date_str):
    """
    Run layer1_filter.py for a specific date.
    Returns list of candidate stock codes from the generated CSV.
    """
    # Try with --date flag first
    stdout, code = run_command(
        ["uv", "run", "python", "layer1_filter.py", "--date", date_str],
        cwd=AUTO_DIR,
        description=f"Layer 1 for {date_str}"
    )

    # Parse candidates from the latest layer1 CSV
    candidates = []
    csv_files = sorted(AUTO_DIR.glob("layer1_candidates_*.csv"), key=lambda f: f.stat().st_mtime)
    if csv_files:
        latest = csv_files[-1]
        # Prefer the file that matches the date
        for f in reversed(csv_files):
            if date_str.replace("-", "") in f.name:
                latest = f
                break
        with open(latest, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                code_val = row.get("stock_code") or row.get("code") or row.get("代码") or row.get("股票代码")
                if code_val:
                    candidates.append(str(code_val).strip())

    # Fallback: if layer1 doesn't support --date, try running without it
    # and use the latest candidates (limitation: will be today's candidates)
    if not candidates:
        print(f"  [WARN] Layer 1 --date not supported or returned empty. Using today's candidates.")
        stdout, _ = run_command(
            ["uv", "run", "python", "layer1_filter.py"],
            cwd=AUTO_DIR,
            description=f"Layer 1 (today's candidates)"
        )
        csv_files = sorted(AUTO_DIR.glob("layer1_candidates_*.csv"), key=lambda f: f.stat().st_mtime)
        if csv_files:
            with open(csv_files[-1], encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code_val = row.get("stock_code") or row.get("code") or row.get("代码")
                    if code_val:
                        candidates.append(str(code_val).strip())

    return candidates[:MAX_STOCKS_PER_DAY]

def run_layer2_for_candidates(candidates):
    """
    Run layer2_screener.py for a list of candidates.
    Captures the JSON output and returns parsed results.
    """
    # layer2_screener.py processes all candidates in its layer1 CSV by default.
    # We need to run it and capture the stdout JSON.
    # If it outputs results to a CSV file, read that CSV.
    stdout, _ = run_command(
        ["uv", "run", "python", "layer2_screener.py"],
        cwd=AUTO_DIR,
        description="Layer 2 (DeepSeek V3 screening)"
    )

    results = []
    # Try to parse JSON from stdout
    for line in stdout.split("\n"):
        line = line.strip()
        if line.startswith("{") or line.startswith("["):
            try:
                results = json.loads(line)
                if isinstance(results, dict):
                    results = [results]
                break
            except json.JSONDecodeError:
                continue

    # Fallback: read from layer2_results CSV
    if not results:
        csv_files = sorted(AUTO_DIR.glob("layer2_results_*.csv"), key=lambda f: f.stat().st_mtime)
        if csv_files:
            with open(csv_files[-1], encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    results.append(dict(row))

    return results

def get_future_price(stock_code, future_days=5):
    """Fetch historical prices from Tencent and get price N days from 'today'."""
    # For backtesting, we simulate looking forward in time.
    # The layer1 CSV may have already pre-filtered candidates using historical data.
    # For price lookup, we use a rolling window from the backtest date.
    NO_PROXY = "ifzq.gtimg.cn,stock.gtimg.cn,qt.gtimg.cn,qq.com,gtimg.cn"
    env_backup = os.environ.get("NO_PROXY", "")
    os.environ["NO_PROXY"] = NO_PROXY
    os.environ["no_proxy"] = NO_PROXY

    import urllib.request
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    # Fetch enough history to get future prices
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={stock_code},day,,,{future_days + 20},qfq"
    try:
        with opener.open(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        prices = data["data"][stock_code]["day"]
        # prices is a list of [date, open, close, high, low, volume]
        # We want the price `future_days` trading bars from "today"
        # In backtest context: today's close = prices[0][2], future = prices[future_days][2]
        if len(prices) >= future_days + 1:
            base_price = float(prices[0][2])
            future_price = float(prices[future_days][2])
            pct = (future_price - base_price) / base_price * 100
            return base_price, future_price, pct
    except Exception as e:
        print(f"  [WARN] Price fetch failed for {stock_code}: {e}")
    finally:
        os.environ["NO_PROXY"] = env_backup
    return None, None, None

def append_to_results_csv(all_results, new_results):
    """Append new results to the CSV file (no duplicates by date+code)."""
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    existing = set()
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing.add((row.get("date", ""), row.get("code", "")))

    keys = new_results[0].keys() if new_results else []
    file_exists = RESULTS_FILE.exists()

    with open(RESULTS_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        if not file_exists:
            writer.writeheader()
        for r in new_results:
            key = (r.get("date", ""), r.get("code", ""))
            if key not in existing:
                writer.writerow(r)
                existing.add(key)

def run_analyst():
    """Run layer3_analyst.py to analyze accumulated results and update rules."""
    print("\n>>> Running Autoresearch iteration...")
    stdout, code = run_command(
        ["uv", "run", "python", "layer3_analyst.py"],
        cwd=AUTO_DIR,
        description="Layer 3 Analyst (Autoresearch iteration)"
    )
    return code == 0

def main():
    start_time = datetime.now()
    print(f"{'='*60}")
    print(f"AUTONOMOUS BACKTEST + ITERATION LOOP")
    print(f"  Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Target: {BACKTEST_DAYS} trading days")
    print(f"  Estimated time: ~{BACKTEST_DAYS * 20 // 60}h {BACKTEST_DAYS * 20 % 60}min")
    print(f"{'='*60}")

    trading_days = get_trading_days(BACKTEST_DAYS)
    print(f"\nTrading days to backtest:")
    for d in trading_days:
        print(f"  {d.strftime('%Y-%m-%d (%A)')}")

    total_picks = 0

    for i, day in enumerate(trading_days):
        day_num = i + 1
        date_str = day.strftime("%Y-%m-%d")
        print(f"\n{'#'*60}")
        print(f"# DAY {day_num}/{BACKTEST_DAYS}: {date_str}")
        print(f"{'#'*60}")

        # Step 1: Layer 1 - get candidates for this day
        candidates = run_layer1_for_date(date_str)
        print(f"  Layer 1 → {len(candidates)} candidates")
        if not candidates:
            print(f"  [SKIP] No candidates for {date_str}")
            time.sleep(ANALYSIS_DELAY)
            continue

        # Step 2: Layer 2 - AI scoring
        picks = run_layer2_for_candidates(candidates)
        print(f"  Layer 2 → {len(picks)} AI-evaluated")

        # Step 3: Get forward price and determine WIN/LOSS/FLAT
        day_results = []
        for pick in picks:
            code = (pick.get("stock_code") or pick.get("code") or
                    pick.get("股票代码") or "").strip()
            if not code:
                continue

            base_p, future_p, pct = get_future_price(code, MIN_HOLDING_DAYS)
            if base_p is None:
                continue

            if pct >= 5.0:
                outcome = "WIN"
            elif pct <= -2.0:
                outcome = "LOSS"
            else:
                outcome = "FLAT"

            day_results.append({
                "date": date_str,
                "code": code,
                "pattern": pick.get("pattern_type", ""),
                "score": pick.get("score", ""),
                "confidence": pick.get("confidence", ""),
                "recommendation": pick.get("recommendation", ""),
                "reason": pick.get("reason", ""),
                "key_positives": pick.get("key_positives", ""),
                "key_negatives": pick.get("key_negatives", ""),
                "base_price": base_p,
                "future_price": future_p,
                "pct_change": round(pct, 2),
                "outcome": outcome
            })
            print(f"  {code}: {pick.get('pattern_type','')} | score={pick.get('score','')} "
                  f"| {pct:+.1f}% → {outcome}")

        # Step 4: Save this day's results to CSV
        if day_results:
            append_to_results_csv([], day_results)
            total_picks += len(day_results)

        wins = len([r for r in day_results if r["outcome"] == "WIN"])
        losses = len([r for r in day_results if r["outcome"] == "LOSS"])
        print(f"\n  Day {day_num} summary: {wins}W/{losses}L/{len(day_results)-wins-losses}F "
              f"| Total picks so far: {total_picks}")

        # Step 5: Run Autoresearch iteration immediately
        success = run_analyst()

        # Check elapsed time — stop if running too long (market open soon)
        elapsed = (datetime.now() - start_time).total_seconds() / 3600
        if elapsed > 6:
            print(f"\n[STOP] Runtime exceeded 6 hours. Saving state and exiting.")
            print(f"  Completed: {day_num}/{BACKTEST_DAYS} days")
            print(f"  Results saved to: {RESULTS_FILE}")
            break

        if day_num < len(trading_days):
            print(f"\n  Sleeping {ANALYSIS_DELAY}s before next day...")
            time.sleep(ANALYSIS_DELAY)

    # Final summary
    print(f"\n{'='*60}")
    print(f"COMPLETED ALL {BACKTEST_DAYS} DAYS")
    print(f"  End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total picks: {total_picks}")
    print(f"{'='*60}")

    # Run final analyst pass
    print("\nRunning final analysis on all accumulated data...")
    run_analyst()

if __name__ == "__main__":
    main()
```

---

## Step 4: Update layer3_analyst.py

Replace the existing `layer3_analyst.py` content with this version (reads all accumulated CSV results, not just the latest):

```python
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
import urllib.request
from pathlib import Path
from datetime import datetime

AUTO_DIR = Path("~/stock_ai/autoresearch").expanduser()
BACKTEST_FILE = AUTO_DIR / "backtest_results" / "all_days_backtest.csv"
LIVE_FILE = AUTO_DIR / "trade_tracker" / "live_results.csv"
SYSTEM_PROMPT_PATH = AUTO_DIR / "rules" / "screener_system_prompt.txt"
ITERATION_LOG = AUTO_DIR / "rules" / "iteration_log.md"
BACKTEST_FINDINGS = AUTO_DIR / "rules" / "backtest_findings.md"
LIVE_FINDINGS = AUTO_DIR / "rules" / "live_findings.md"
REPORTS_DIR = AUTO_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

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

def generate_ai_analysis(backtest_summary, live_summary, all_backtest_results):
    with open(SYSTEM_PROMPT_PATH) as f:
        current_rules = f.read()

    # Count iterations
    iteration_num = 1
    if ITERATION_LOG.exists():
        with open(ITERATION_LOG) as f:
            iteration_num = f.read().count("## 20") + 1

    prompt = f"""You are an expert A-share trading strategy analyst. Respond in Chinese.
Analyze the backtesting results below and propose concrete rule updates.

## CURRENT SYSTEM PROMPT:
{current_rules}

## BACKTEST DATA ({len(all_backtest_results)} total picks):
{backtest_summary}

## LIVE TRADING DATA:
{live_summary}

## YOUR TASK:
Answer in Chinese. Be specific and data-driven.

1. What is the overall win rate? Which pattern (convergence vs pullback) wins more?
2. What do WIN cases have in common? (specific numbers: end-zone width, volume decline %, score threshold, etc.)
3. What do LOSS cases have in common?
4. Which recommendation level (select/watch) has the best win rate?
5. What specific rule should be ADDED, REMOVED, or MODIFIED? (MAX 1 CHANGE ONLY. Be very conservative.)

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

def main():
    now = datetime.now()
    print(f"Layer 3 Analyst -- {now.strftime('%Y-%m-%d %H:%M:%S')}")

    all_backtest = load_backtest_results()
    all_live = load_live_results()

    backtest_summary = summarize_results(all_backtest, "BACKTEST")
    live_summary = summarize_results(all_live, "LIVE TRADING")

    print(backtest_summary)
    print("\n" + live_summary)

    print("\nCalling DeepSeek V3 for AI analysis...")
    ai_result = generate_ai_analysis(backtest_summary, live_summary, all_backtest)

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

    # Append to iteration_log.md
    log_entry = f"""
## {now.strftime('%Y-%m-%d %H:%M')} -- Iteration #{ai_result.get('_iteration', 1)}
Total picks: {len(all_backtest)} | Win rate: {ai_result.get('overall_win_rate', 'N/A')}
Rule suggestions: {len(ai_result.get('rule_suggestions', []))}
Top WIN feature: {ai_result.get('win_features', [''])[0]}
Top LOSS feature: {ai_result.get('loss_features', [''])[0]}
"""
    with open(ITERATION_LOG, "a", encoding="utf-8") as f:
        f.write(log_entry)

    print("\nRule suggestions:")
    for sug in ai_result.get("rule_suggestions", []):
        print(f"  [{sug['action']}] {sug.get('location', '')}")
        print(f"    Proposed: {sug.get('proposed', '')[:100]}")

if __name__ == "__main__":
    main()
```

---

## Step 5: Create trade_tracker.py

```python
"""
trade_tracker.py
Records real trades: picks from Layer 2, buy price, P&L, final result.
Usage:
  python trade_tracker.py --record <code> <pattern> <score> <conf> <rec> "<reason>"
  python trade_tracker.py --update <code> <buy_price> <current_price>
  python trade_tracker.py --report
"""

import csv
import sys
from pathlib import Path
from datetime import datetime

TRACKER_DIR = Path("~/stock_ai/autoresearch/trade_tracker")
TRACKER_DIR.mkdir(exist_ok=True)
LIVE_FILE = TRACKER_DIR / "live_results.csv"

FIELDS = ["id", "pick_date", "code", "pattern", "score", "confidence",
          "recommendation", "reason", "buy_price", "current_price",
          "pct_change", "outcome"]

def load_rows():
    if not LIVE_FILE.exists():
        return []
    with open(LIVE_FILE, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def save_rows(rows):
    with open(LIVE_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

def record_pick(code, pattern, score, confidence, rec, reason):
    rows = load_rows()
    row = {
        "id": f"{datetime.now().strftime('%Y%m%d')}_{code}",
        "pick_date": datetime.now().strftime("%Y-%m-%d"),
        "code": code, "pattern": pattern, "score": score,
        "confidence": confidence, "recommendation": rec,
        "reason": reason, "buy_price": "", "current_price": "",
        "pct_change": "", "outcome": "OPEN"
    }
    rows.append(row)
    save_rows(rows)
    print(f"Recorded: {code} ({rec})")

def update_position(code, buy_price, current_price):
    rows = load_rows()
    for row in rows:
        if row["code"] == code and row["outcome"] == "OPEN":
            base = float(buy_price)
            curr = float(current_price)
            pct = (curr - base) / base * 100
            row["buy_price"] = buy_price
            row["current_price"] = current_price
            row["pct_change"] = f"{pct:+.1f}%"
            if pct >= 5.0:
                row["outcome"] = "WIN"
            elif pct <= -2.0:
                row["outcome"] = "LOSS"
            else:
                row["outcome"] = "HOLD"
            print(f"Updated {code}: {pct:+.1f}% -> {row['outcome']}")
    save_rows(rows)

def report():
    rows = load_rows()
    open_pos = [r for r in rows if r["outcome"] == "OPEN"]
    closed = [r for r in rows if r["outcome"] != "OPEN"]
    wins = [r for r in closed if r["outcome"] == "WIN"]
    losses = [r for r in closed if r["outcome"] == "LOSS"]
    total = len(closed)
    wr = len(wins)/total*100 if total else 0
    print(f"\nLive Trading Report ({datetime.now().strftime('%Y-%m-%d')})")
    print(f"Open: {len(open_pos)} | Closed: {total} | Win rate: {wr:.0f}%")
    for r in closed:
        print(f"  {r['code']}: {r['pattern']} | {r['pct_change']} -> {r['outcome']}")

def main():
    if len(sys.argv) < 2:
        report()
    elif sys.argv[1] == "--record" and len(sys.argv) >= 7:
        record_pick(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6],
                    sys.argv[7] if len(sys.argv) > 7 else "")
    elif sys.argv[1] == "--update" and len(sys.argv) >= 4:
        update_position(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "--report":
        report()
    else:
        print("Usage:")
        print("  python trade_tracker.py --record <code> <pattern> <score> <conf> <rec> <reason>")
        print("  python trade_tracker.py --update <code> <buy_price> <current_price>")
        print("  python trade_tracker.py --report")

if __name__ == "__main__":
    main()
```

---

## Step 6: Run Everything

```bash
cd ~/stock_ai/autoresearch

# Make sure DeepSeek API key is set
export DEEPSEEK_API_KEY="sk-xxxxxxxxxxxx"

# Run the FULL autonomous loop (10 days, ~3-4 hours)
uv run python master_orchestrator.py

# Test with only 3 days first
uv run python master_orchestrator.py 3
```

---

## What Gets Saved Where

| What | Where |
|---|---|
| All backtest picks (incremental) | `backtest_results/all_days_backtest.csv` |
| Iteration report (each day) | `reports/iteration_report_YYYYMMDD_HHMM.md` |
| Updated findings | `rules/backtest_findings.md` |
| Iteration history | `rules/iteration_log.md` |
| Real trades | `trade_tracker/live_results.csv` |

---

## Time Estimate

- Each day cycle: ~20 minutes
- 10 days: **~3-4 hours**
- Safe to start before sleep, done by morning
- The orchestrator checks elapsed time and stops after 6 hours to avoid market open

---

## Key Design Points

1. **Incremental CSV**: Results are appended to `all_days_backtest.csv` after EACH day — no data is lost if the script is interrupted.
2. **Per-day Autoresearch**: After each day completes, `layer3_analyst.py` runs immediately, updating findings and log files.
3. **No duplicate entries**: The CSV append function checks `(date, code)` to avoid writing the same stock twice.
4. **Safety stop**: Script stops automatically after 6 hours to avoid running into market hours.
5. **Resume capability**: If interrupted, running again will continue from where it left off (existing CSV entries are skipped).

---

## Step 7: Integrate Manual Ground-Truth Picks (DO THIS BEFORE RUNNING THE BACKTEST)

The user has provided real historical picks with verified outcomes. These are ground-truth examples of correct pattern recognition. They must be loaded into the analysis engine so `layer3_analyst.py` can compare AI rule output against human judgment.

### 7.1 Copy the manual picks file

Copy `manual_picks.csv` (provided separately) to:

```
~/stock_ai/autoresearch/data/manual_picks.csv
```

The file has these columns:

```
股票代码, 股票名称, 选股日期, 买入日期, 结果, 图形类型, 备注
```

**Important notes about the data:**
- `选股日期` = the evening when the user reviewed charts (after market close); stocks are candidates for the NEXT day
- `买入日期` = the actual buy date (usually 选股日期 + 1 trading day). If empty → buy trigger was NOT hit (no position taken)
- `结果` values: `WIN` = profitable exit without hitting stop loss; `LOSS` = stop loss triggered; `N/A` = never bought (no buy trigger)
- **603098 森特股份** (20260330) = NOT bought, 结果 = N/A. Include in the dataset but label as "no_entry" not WIN/LOSS.
- **601016 节能风电** (20260324→20260325): original file had 买入日期 one day BEFORE 选股日期 — corrected to 20260325.

### 7.2 User's actual stop-loss rules (use these in layer3_analyst.py and system prompt)

```
Stop-loss rule 1 (Hard): Stop price = buy_price × (1 - 2.5%)
  → If current_price <= stop_price, exit immediately (full position)

Stop-loss rule 2 (Time): If position held >= 3 trading days AND
  intraday max profit has NEVER exceeded +4%,
  → On Day 4 open, sell at floating profit price.
  → If that price is unreachable by 14:55, sell at market price.
```

**For backtest WIN/LOSS classification:**
- `WIN` = buy triggered → did NOT hit either stop-loss condition → profitable exit
- `LOSS` = buy triggered → hit hard stop (-2.5%) OR time stop (3 days, never reached +4%)
- `FLAT` = small gain/loss that doesn't clearly meet WIN or LOSS definition
- `N/A` (no_entry) = buy trigger was never hit; exclude from win rate calculation

### 7.3 Update `layer3_analyst.py` to load and use manual picks

Add a new function `load_manual_picks()` in `layer3_analyst.py`:

```python
MANUAL_PICKS_FILE = AUTO_DIR / "data" / "manual_picks.csv"

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
```

Then update `main()` in `layer3_analyst.py` to pass manual picks to the AI analysis:

```python
def main():
    # ... existing code ...
    all_backtest = load_backtest_results()
    all_live = load_live_results()
    manual_picks = load_manual_picks()  # ADD THIS LINE

    # Pass manual_picks into generate_ai_analysis:
    ai_result = generate_ai_analysis(backtest_summary, live_summary, all_backtest, manual_picks)
```

Update `generate_ai_analysis()` signature to accept manual_picks and include them in the prompt:

```python
def generate_ai_analysis(backtest_summary, live_summary, all_backtest_results, manual_picks=None):
    # ... existing code ...
    
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
...
{manual_section}
...
"""
```

### 7.4 Also update `layer3_analyst.py` prompt to add cross-reference analysis

Add this to the `## YOUR TASK:` section in the prompt:

```
6. Cross-reference with human ground-truth picks:
   - Which human WIN picks did the AI rules correctly identify?
   - Which human WIN picks did the AI rules MISS? (This is the most important gap to fix)
   - Which human LOSS picks did the AI rules fail to filter out?
   - Based on the human WIN examples, what pattern features are currently underdefined in the rules?
```

---

## Step 8: Update `screener_system_prompt.txt` — Add ST Filter and Stop-Loss Context

Add the following to `screener_system_prompt.txt` **before** the Output JSON section:

```
## MANDATORY EXCLUSION RULES (check these FIRST — instant skip):
- SKIP any stock with "ST" or "*ST" in its name (these are delisted-risk stocks)
- SKIP any stock that has already broken above the convergence pattern (pattern destroyed)
- SKIP any stock showing rapid high-point decline (consecutive lower highs)
- SKIP any stock in a weekly downtrend

## STOP-LOSS CONTEXT (use this to calibrate your confidence scores):
The trading system uses these exit rules:
- Hard stop: -2.5% from buy price (tight)
- Time stop: if no +4% intraday peak within 3 days, exit on Day 4 regardless
This means the stock MUST be near a breakout point with high probability of a quick +4%+ move.
Stocks that are "interesting but need more time" will be time-stopped.
When in doubt, output "skip" — the system needs high-conviction, near-breakout setups only.
```

---

## Execution Order (Final Checklist)

Run these in order, ONE TIME, before starting the overnight backtest:

```bash
cd ~/stock_ai/autoresearch

# 1. Create data directory
mkdir -p data

# 2. Copy manual picks (copy from WorkBuddy project folder to here)
cp /path/to/manual_picks.csv data/manual_picks.csv

# 3. Verify it loaded correctly
uv run python -c "
import csv
with open('data/manual_picks.csv', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
    print(f'Loaded {len(rows)} rows')
    for r in rows:
        print(f'  {r[\"股票代码\"]} {r[\"股票名称\"]} → {r[\"结果\"]}')
"

# 4. Run the full overnight backtest
export DEEPSEEK_API_KEY="sk-xxxxxxxxxxxx"
uv run python master_orchestrator.py
```

**Before sleeping:**
- [ ] Mac Mini power adapter plugged in
- [ ] Sleep/screensaver disabled (`System Settings → Lock Screen → Never`)
- [ ] VPN OFF (Tencent data source needs direct connection)
- [ ] Terminal window visible (not minimized) — some macOS power management kills background terminals
- [ ] `DEEPSEEK_API_KEY` confirmed set (`echo $DEEPSEEK_API_KEY`)

**What you'll find in the morning:**
- `backtest_results/all_days_backtest.csv` — all 10 days of AI picks with outcomes
- `reports/iteration_report_*.md` — 10 iteration analysis reports
- `rules/backtest_findings.md` — final consolidated findings
- `rules/iteration_log.md` — full history of each iteration's key insight
- Win rate, best-performing pattern type, and 1 concrete rule improvement suggestion
