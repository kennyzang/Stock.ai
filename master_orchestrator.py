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
MAX_STOCKS_PER_DAY = 50  # Increased from 20 to get more candidates per day
ANALYSIS_DELAY = 30  # seconds to wait after each day's analysis before next day
AUTO_APPLY = "--apply" in sys.argv  # NEW: pass --apply to Layer3 to actually write rule changes
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
        cwd=str(cwd)
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
    # Try with --date flag first (limit to 500 for reasonable runtime)
    stdout, code = run_command(
        ["uv", "run", "python", "layer1_filter.py", "--date", date_str, "--limit", "500"],
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
            ["uv", "run", "python", "layer1_filter.py", "--limit", "500"],
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

def run_layer2_for_candidates(candidates, date_str=None):
    """
    Run layer2_screener.py for a list of candidates.
    Captures the JSON output and returns parsed results.
    """
    # layer2_screener.py processes all candidates in its layer1 CSV by default.
    # We need to run it and capture the stdout JSON.
    # If it outputs results to a CSV file, read that CSV.
    cmd = ["uv", "run", "python", "layer2_screener.py"]
    if date_str:
        cmd.extend(["--date", date_str])
    stdout, _ = run_command(
        cmd,
        cwd=AUTO_DIR,
        description=f"Layer 2 (DeepSeek V3 screening) for {date_str}"
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

    # Fallback: read from layer2_results CSV (prefer date-specific file)
    if not results:
        if date_str:
            date_file = AUTO_DIR / f"layer2_results_{date_str.replace('-', '')}.csv"
            if date_file.exists():
                with open(date_file, encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        results.append(dict(row))
                return results
        # Fallback to latest
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

    # Convert raw stock code to Tencent code (sh/sz/bj)
    def convert_to_tencent_code(code: str) -> str:
        code = str(code).zfill(6)
        if code.startswith(("600", "601", "603", "605", "688", "689", "730")):
            return f"sh{code}"
        if code.startswith("8"):
            return f"bj{code}"
        return f"sz{code}"

    tencent_code = convert_to_tencent_code(stock_code)

    # Fetch enough history to get future prices
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tencent_code},day,,,{future_days + 20},qfq"
    try:
        with opener.open(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        data_section = data.get("data", {}).get(tencent_code, {})
        day_rows = data_section.get("qfqday") or data_section.get("day") or []
        # day_rows is a list of [date, open, close, high, low, volume]
        # We want the price `future_days` trading bars from "today"
        # In backtest context: today's close = day_rows[0][2], future = day_rows[future_days][2]
        if len(day_rows) >= future_days + 1:
            base_price = float(day_rows[0][2])
            future_price = float(day_rows[future_days][2])
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
    cmd = ["uv", "run", "python", "layer3_analyst.py"]
    if AUTO_APPLY:
        cmd.append("--apply")
        print("    [AUTO-APPLY MODE: Rule changes WILL be written to files]")
    else:
        print("    [DRY-RUN MODE: Rule changes logged but NOT applied. Use --apply flag to enable]")
    stdout, code = run_command(
        cmd,
        cwd=AUTO_DIR,
        description="Layer 3 Analyst (Autoresearch iteration)"
    )
    return code == 0

def main():
    # Clear old results file to prevent data mixing between runs
    if RESULTS_FILE.exists():
        RESULTS_FILE.unlink()
        print(f"Cleared old results file: {RESULTS_FILE}")

    start_time = datetime.now()
    print(f"{'='*60}")
    print(f"AUTONOMOUS BACKTEST + ITERATION LOOP")
    print(f"  Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Target: {BACKTEST_DAYS} trading days")
    print(f"  Auto-Apply: {'ENABLED (rules WILL change)' if AUTO_APPLY else 'DISABLED (dry-run only)'}")
    print(f"  Estimated time: ~{BACKTEST_DAYS * 20 // 60}h {BACKTEST_DAYS * 20 % 60}min")
    print(f"{'='*60}")

    trading_days = get_trading_days(BACKTEST_DAYS)
    trading_days.reverse()  # Process oldest first (forward in time)
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
        picks = run_layer2_for_candidates(candidates, date_str)
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
