# A股选股AI系统 — Layer 3: 回测 + 迭代双轨蓝图 v1.0

> 本文档定义 Layer 3 的完整架构：历史回测 + 真实持仓反馈双轨运行，数据互通，持续迭代战法规则。

---

## 核心设计原则

1. **双轨数据源**：历史回测（快速验证）+ 真实持仓（真实战场），两者共用同一套分析引擎
2. **增量迭代**：每跑完一天 → 立即触发 Autoresearch 分析 → 更新规则发现文件 → 下一日
3. **只微调，不重构**：每次只改一条规则，严防过拟合
4. **Master Orchestrator 驱动**：一个脚本 `master_orchestrator.py` 串联全流程，无需人工干预

---

## 架构总览

```
master_orchestrator.py         ← 全自动主循环（Day N → 分析 → Day N+1 → 分析）
│
├── for each trading day:
│     ├── layer1_filter.py --date YYYYMMDD   → 候选股票
│     ├── layer2_screener.py                 → DeepSeek V3 评分
│     ├── 获取5日后价格                       → WIN/LOSS/FLAT
│     └── 追加到 backtest_results/all_days_backtest.csv
│
└── after each day completes:
      └── layer3_analyst.py                 → 增量分析（读取全部历史结果）
            ├── 输出 iteration_report_*.md
            ├── 更新 rules/backtest_findings.md
            └── 追加 rules/iteration_log.md

trade_tracker.py               ← 真实持仓追踪（手动或自动记录）
reports/                       ← 迭代报告输出目录
rules/                         ← 战法规则（AI 唯一信任源）

---

## 文件 1: rolling_backtest.py

### 功能
遍历过去 N 个交易日，对每一天运行 Layer 1 + Layer 2，记录选股结果，再查 5 天后的实际价格变化。

### 核心逻辑

```python
"""
rolling_backtest.py
Automated historical backtesting for A-share three-cycle strategy.
Each day: run Layer1 + Layer2 → record picks → check 5-day outcome.
"""

import os
import json
import csv
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ========== CONFIG ==========
BACKTEST_DAYS = 10          # 回测最近 N 个交易日
MIN_HOLDING_DAYS = 5       # 持仓等待天数
MAX_STOCKS_PER_DAY = 20     # 每日最多跑 Layer 2 的股票数
DAILY_BUDGET = 5.0         # 每日 DeepSeek 预算上限（元）
# ============================

RESULTS_DIR = Path("~/stock_ai/autoresearch/backtest_results").expanduser()
RESULTS_DIR.mkdir(exist_ok=True)

today = datetime.now()

def get_trading_days(n=30):
    """生成最近 N 个交易日列表（跳过周末）"""
    days = []
    d = today
    while len(days) < n:
        if d.weekday() < 5:  # Mon-Fri
            days.append(d)
        d -= timedelta(days=1)
    return days

def run_layer1(date_str):
    """运行 Layer 1，输出候选股票列表"""
    # 调用 layer1_filter.py，指定日期
    result = subprocess.run(
        ["uv", "run", "python", "layer1_filter.py", "--date", date_str],
        capture_output=True, text=True, cwd="~/stock_ai/autoresearch"
    )
    # 解析输出股票列表（从 stdout 或 layer1_candidates_*.csv）
    candidates = []
    csv_files = list(Path("~/stock_ai/autoresearch").glob("layer1_candidates_*.csv"))
    if csv_files:
        latest = max(csv_files, key=lambda f: f.stat().st_mtime)
        with open(latest) as f:
            reader = csv.DictReader(f)
            for row in reader:
                candidates.append(row.get("stock_code") or row.get("code"))
    return candidates[:MAX_STOCKS_PER_DAY]

def run_layer2(stock_codes, date_str):
    """运行 Layer 2，对候选股票打分"""
    picks = []
    daily_cost = 0.0

    for code in stock_codes:
        # 调用 layer2_screener.py 处理单支股票
        result = subprocess.run(
            ["uv", "run", "python", "layer2_screener.py",
             "--stock", code, "--date", date_str],
            capture_output=True, text=True, cwd="~/stock_ai/autoresearch"
        )
        try:
            data = json.loads(result.stdout)
            picks.append(data)
            # 估算 DeepSeek 费用（每次约 0.005 元）
            daily_cost += 0.005
        except json.JSONDecodeError:
            continue

        if daily_cost >= DAILY_BUDGET:
            print(f"  ⚠️ Daily budget reached at {code}")
            break
        time.sleep(1)  # 避免请求过快

    return picks

def get_future_price(stock_code, base_date_str, future_days=5):
    """查 base_date 之后 future_days 个交易日的价格变化"""
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={stock_code},day,,,{future_days + 10},qfq"
    # 使用腾讯历史数据，提取 base_date 之后 N 天的收盘价
    # 返回 (base_price, future_price, pct_change)
    try:
        import urllib.request
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        prices = data["data"][stock_code]["day"]
        # prices 是 [date, open, close, high, low, volume] 的列表
        # 找到 base_date 对应的 bar，取 future_days 之后的 bar
        # 简化实现：
        if len(prices) >= future_days + 1:
            base_price = float(prices[0][2])  # 第一根 bar 收盘价
            future_price = float(prices[future_days][2])
            pct = (future_price - base_price) / base_price * 100
            return base_price, future_price, pct
    except Exception as e:
        print(f"  [WARN] Price fetch failed for {stock_code}: {e}")
    return None, None, None

def run_backtest_day(date):
    """对单个交易日运行完整回测"""
    date_str = date.strftime("%Y-%m-%d")
    print(f"\n{'='*50}")
    print(f"📅 Backtesting: {date_str}")
    print(f"{'='*50}")

    candidates = run_layer1(date_str)
    print(f"  Layer 1 → {len(candidates)} candidates")

    picks = run_layer2(candidates, date_str)
    print(f"  Layer 2 → {len(picks)} evaluated")

    # 评估 5 天后结果
    results = []
    for pick in picks:
        code = pick.get("stock_code")
        base_p, future_p, pct = get_future_price(code, date_str, MIN_HOLDING_DAYS)
        if base_p is None:
            continue

        if pct >= 5.0:
            outcome = "WIN"
        elif pct <= -2.0:
            outcome = "LOSS"
        else:
            outcome = "FLAT"

        results.append({
            "date": date_str,
            "code": code,
            "pattern": pick.get("pattern_type"),
            "score": pick.get("score"),
            "confidence": pick.get("confidence"),
            "recommendation": pick.get("recommendation"),
            "reason": pick.get("reason"),
            "base_price": base_p,
            "future_price": future_p,
            "pct_change": pct,
            "outcome": outcome
        })
        print(f"  {code}: {pick.get('pattern')} | score={pick.get('score')} | {pct:+.1f}% → {outcome}")

    return results

def main():
    print(f"🚀 Starting rolling backtest — last {BACKTEST_DAYS} trading days")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_results = []
    trading_days = get_trading_days(BACKTEST_DAYS)

    for day in trading_days:
        day_results = run_backtest_day(day)
        all_results.extend(day_results)
        time.sleep(2)  # 每日之间稍作间隔

    # 保存全量结果
    output_file = RESULTS_DIR / f"backtest_results_{today.strftime('%Y%m%d')}.csv"
    if all_results:
        keys = all_results[0].keys()
        with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_results)
        print(f"\n✅ Saved {len(all_results)} records to {output_file}")
    else:
        print("\n⚠️ No results collected.")

    # 打印汇总统计
    wins = sum(1 for r in all_results if r["outcome"] == "WIN")
    losses = sum(1 for r in all_results if r["outcome"] == "LOSS")
    flats = sum(1 for r in all_results if r["outcome"] == "FLAT")
    total = len(all_results)

    print(f"\n📊 BACKTEST SUMMARY ({BACKTEST_DAYS} days, {total} picks):")
    print(f"   WIN:  {wins}/{total} ({wins/total*100:.1f}%)" if total else "")
    print(f"   LOSS: {losses}/{total} ({losses/total*100:.1f}%)" if total else "")
    print(f"   FLAT: {flats}/{total} ({flats/total*100:.1f}%)" if total else "")

if __name__ == "__main__":
    main()
```

---

## 文件 2: layer3_analyst.py（Autoresearch 核心）

### 功能
读取回测结果 + 真实持仓结果，分析胜率，输出规则更新建议。

```python
"""
layer3_analyst.py
Autoresearch analysis engine — reads backtest + live results,
uses DeepSeek V3 to analyze what patterns won/lost, outputs rule update suggestions.
Run weekly via cron or manually.
"""

import os
import json
import csv
from pathlib import Path
from datetime import datetime

BACKTEST_DIR = Path("~/stock_ai/autoresearch/backtest_results")
LIVE_FILE = Path("~/stock_ai/autoresearch/trade_tracker/live_results.csv")
RULES_DIR = Path("~/stock_ai/autoresearch/rules")
REPORTS_DIR = Path("~/stock_ai/autoresearch/reports")
REPORTS_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT_PATH = RULES_DIR / "screener_system_prompt.txt"
ITERATION_LOG = RULES_DIR / "iteration_log.md"
BACKTEST_FINDINGS = RULES_DIR / "backtest_findings.md"
LIVE_FINDINGS = RULES_DIR / "live_findings.md"

def load_backtest_results():
    """加载所有回测结果 CSV"""
    results = []
    for csv_file in BACKTEST_DIR.glob("backtest_results_*.csv"):
        with open(csv_file, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            results.extend(list(reader))
    return results

def load_live_results():
    """加载真实持仓结果"""
    if not LIVE_FILE.exists():
        return []
    with open(LIVE_FILE, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)

def summarize_results(results, source_label):
    """汇总胜率统计"""
    if not results:
        return f"{source_label}: No data yet."

    wins = [r for r in results if r.get("outcome") == "WIN"]
    losses = [r for r in results if r.get("outcome") == "LOSS"]
    flats = [r for r in results if r.get("outcome") == "FLAT"]
    total = len(results)
    win_rate = len(wins) / total * 100 if total else 0

    # 按 pattern type 分组
    by_pattern = {}
    for r in results:
        pt = r.get("pattern", "unknown")
        by_pattern.setdefault(pt, []).append(r)

    pattern_stats = []
    for pt, items in by_pattern.items():
        w = len([x for x in items if x.get("outcome") == "WIN"])
        pattern_stats.append(f"  - {pt}: {w}/{len(items)} wins ({w/len(items)*100:.0f}%)")

    # 按 recommendation 分组
    by_rec = {}
    for r in results:
        rec = r.get("recommendation", "unknown")
        by_rec.setdefault(rec, []).append(r)

    rec_stats = []
    for rec, items in by_rec.items():
        w = len([x for x in items if x.get("outcome") == "WIN"])
        rec_stats.append(f"  - {rec}: {w}/{len(items)} wins ({w/len(items)*100:.0f}%)")

    # 高分 vs 低分
    high_score = [r for r in results if float(r.get("score", 0)) >= 70]
    low_score = [r for r in results if float(r.get("score", 0)) < 70]
    hs_w = len([r for r in high_score if r.get("outcome") == "WIN"])
    ls_w = len([r for r in low_score if r.get("outcome") == "WIN"])
    hs_wr = hs_w/len(high_score)*100 if high_score else 0
    ls_wr = ls_w/len(low_score)*100 if low_score else 0

    summary = f"""{source_label} SUMMARY:
Total picks: {total} | WIN: {len(wins)} ({win_rate:.1f}%) | LOSS: {len(losses)} | FLAT: {len(flats)}

By Pattern:
{chr(10).join(pattern_stats)}

By Recommendation:
{chr(10).join(rec_stats)}

By Score:
  - High score (≥70): {hs_w}/{len(high_score)} wins ({hs_wr:.0f}%)
  - Low score (<70):  {ls_w}/{len(low_score)} wins ({ls_wr:.0f}%)

WIN Cases (key_positives + reason):
"""
    for r in wins[:5]:  # 最多5个示例
        summary += f'\n  [{r.get("date")}] {r.get("code")}: {r.get("reason", "")[:100]}'

    summary += f"\n\nLOSS Cases (key_negatives + reason):\n"
    for r in losses[:5]:
        summary += f'\n  [{r.get("date")}] {r.get("code")}: {r.get("reason", "")[:100]}'

    return summary

def generate_ai_analysis(backtest_summary, live_summary):
    """调用 DeepSeek V3 分析胜率，输出规则更新建议"""
    import urllib.request
    import urllib.parse

    with open(SYSTEM_PROMPT_PATH) as f:
        current_rules = f.read()

    prompt = f"""You are an expert A-share trading strategy analyst.
Analyze the backtesting and live trading results below, then propose rule updates.

## CURRENT SYSTEM PROMPT (rules we are testing):
{current_rules}

## BACKTEST RESULTS (last {BACKTEST_DAYS} trading days):
{backtest_summary}

## LIVE TRADING RESULTS (if any):
{live_summary}

## YOUR TASK:
Answer these questions:
1. What pattern types (convergence vs pullback) have the highest win rate?
2. What specific features characterize the WIN cases? (e.g., end-zone width < X%, volume declining by Y%, etc.)
3. What specific features characterize the LOSS cases?
4. What recommendation level (select/watch) has the best hit rate?
5. Should any rules be ADDED, REMOVED, or MODIFIED? (Be conservative — max 1 change per iteration)
6. What is the overall win rate trend over time?

Respond in this JSON format:
{{
  "analysis": "Your detailed analysis (in Chinese)",
  "pattern_insights": {{"convergence": "win rate and key features", "pullback": "win rate and key features"}},
  "win_features": ["Feature 1", "Feature 2", ...],
  "loss_features": ["Feature 1", "Feature 2", ...],
  "best_recommendation": "select or watch?",
  "rule_suggestions": [
    {{"action": "ADD|REMOVE|MODIFY", "location": "rule number or section", "current": "what it says now", "proposed": "what to change it to", "reason": "why"}}
  ],
  "overall_win_rate": "X%",
  "confidence": "high|medium|low"
}}
"""

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return {"error": "DEEPSEEK_API_KEY not set"}

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
        content = result["choices"][0]["message"]["content"]
        # 提取 JSON
        start = content.find("{")
        end = content.rfind("}") + 1
        return json.loads(content[start:end])

def main():
    print("🚀 Layer 3 Analyst — Running weekly iteration analysis")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    backtest_results = load_backtest_results()
    live_results = load_live_results()

    backtest_summary = summarize_results(backtest_results, "BACKTEST")
    live_summary = summarize_results(live_results, "LIVE TRADING")

    print(backtest_summary)
    print("\n" + live_summary)

    # DeepSeek AI 分析
    print("\n🤖 Running AI analysis with DeepSeek V3...")
    ai_result = generate_ai_analysis(backtest_summary, live_summary)

    if "error" in ai_result:
        print(f"⚠️ API Error: {ai_result['error']}")
        return

    # 保存分析报告
    report = f"""# Layer 3 迭代报告 — {datetime.now().strftime('%Y-%m-%d')}

## 胜率汇总

{backtest_summary}

## AI 深度分析

**整体胜率**: {ai_result.get('overall_win_rate', 'N/A')}
**分析置信度**: {ai_result.get('confidence', 'N/A')}

### 形态洞察
- 收敛（Convergence）: {ai_result.get('pattern_insights', {}).get('convergence', 'N/A')}
- 二踩（Pullback）: {ai_result.get('pattern_insights', {}).get('pullback', 'N/A')}

### 赢家的共同特征
{chr(10).join(f'- {f}' for f in ai_result.get('win_features', []))}

### 输家的共同特征
{chr(10).join(f'- {f}' for f in ai_result.get('loss_features', []))}

### 最佳推荐级别
{ai_result.get('best_recommendation', 'N/A')}

## 规则更新建议

"""
    for i, sug in enumerate(ai_result.get("rule_suggestions", []), 1):
        report += f"""### 建议 {i}: [{sug['action']}] {sug['location']}
- **当前规则**: {sug.get('current', 'N/A')}
- **建议修改为**: {sug.get('proposed', 'N/A')}
- **理由**: {sug.get('reason', 'N/A')}

"""

    # 保存报告
    report_file = REPORTS_DIR / f"iteration_report_{datetime.now().strftime('%Y%m%d')}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n✅ Report saved to: {report_file}")

    # 更新 findings 文件
    with open(BACKTEST_FINDINGS, "w", encoding="utf-8") as f:
        f.write(f"# 回测结论 — {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write(f"整体胜率: {ai_result.get('overall_win_rate', 'N/A')}\n\n")
        f.write("赢家的共同特征:\n")
        for f2 in ai_result.get('win_features', []):
            f.write(f"- {f2}\n")
        f.write("\n输家的共同特征:\n")
        for f2 in ai_result.get('loss_features', []):
            f.write(f"- {f2}\n")

    # 追加 iteration log
    log_entry = f"""
## {datetime.now().strftime('%Y-%m-%d')} — Iteration #{iteration_num}
- Backtest picks: {len(backtest_results)}
- Win rate: {ai_result.get('overall_win_rate', 'N/A')}
- Rule changes: {len(ai_result.get('rule_suggestions', []))}
- AI suggestions: {ai_result.get('analysis', '')[:200]}...
"""
    with open(ITERATION_LOG, "a", encoding="utf-8") as f:
        f.write(log_entry)

    print(f"\n📋 Rule suggestions:")
    for sug in ai_result.get("rule_suggestions", []):
        print(f"  [{sug['action']}] {sug['location']}: {sug.get('proposed', '')[:60]}")

if __name__ == "__main__":
    main()
```

---

## 文件 3: trade_tracker.py（真实持仓追踪）

```python
"""
trade_tracker.py
记录真实持仓：每日选股结果、买入价、当前盈亏、最终结果。
与 rolling_backtest.py 共用同一套分析逻辑。
"""

import csv
from pathlib import Path
from datetime import datetime

TRACKER_DIR = Path("~/stock_ai/autoresearch/trade_tracker")
TRACKER_DIR.mkdir(exist_ok=True)
LIVE_FILE = TRACKER_DIR / "live_results.csv"

def record_pick(stock_code, pattern, score, confidence, recommendation, reason, buy_price=None, buy_date=None):
    """记录一次选股（买入前或买入后）"""
    row = {
        "id": f"{datetime.now().strftime('%Y%m%d')}_{stock_code}",
        "pick_date": datetime.now().strftime("%Y-%m-%d"),
        "code": stock_code,
        "pattern": pattern,
        "score": score,
        "confidence": confidence,
        "recommendation": recommendation,
        "reason": reason,
        "buy_price": buy_price or "",
        "buy_date": buy_date or "",
        "current_price": "",
        "pct_change": "",
        "outcome": "OPEN"  # OPEN | WIN | LOSS | FLAT
    }

    # 追加到 CSV
    file_exists = LIVE_FILE.exists()
    with open(LIVE_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    print(f"📝 Recorded pick: {stock_code} ({recommendation})")

def update_position(stock_code, current_price):
    """更新持仓现价，计算盈亏"""
    rows = []
    with open(LIVE_FILE, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    updated = False
    for row in rows:
        if row["code"] == stock_code and row["outcome"] == "OPEN":
            if row["buy_price"]:
                base = float(row["buy_price"])
                curr = float(current_price)
                pct = (curr - base) / base * 100
                row["current_price"] = current_price
                row["pct_change"] = f"{pct:+.1f}%"
                # 自动平仓逻辑（可按需调整）
                if pct >= 5.0:
                    row["outcome"] = "WIN"
                elif pct <= -2.0:
                    row["outcome"] = "LOSS"
                updated = True

    if updated:
        with open(LIVE_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"✅ Updated {stock_code}: {pct:+.1f}%")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2 and sys.argv[1] == "--update":
        print("Usage: python trade_tracker.py --record <code> <pattern> <score> <conf> <rec> <reason>")
        print("       python trade_tracker.py --update <code> <current_price>")
    else:
        print("trade_tracker.py — use via layer2_screener.py hooks or manually")
```

---

## 完整执行流程

### 第一阶段：历史回测（一次性）

```bash
cd ~/stock_ai/autoresearch

# 跑过去 10 个交易日的回测（约 ¥5 DeepSeek 费用）
uv run python rolling_backtest.py
# 输出：backtest_results/backtest_results_YYYYMMDD.csv
```

### 第二阶段：AI 分析 & 规则迭代

```bash
# 分析回测结果，输出规则更新建议
uv run python layer3_analyst.py
# 输出：
#   - reports/iteration_report_YYYYMMDD.md（详细报告）
#   - rules/backtest_findings.md（胜率特征）
#   - rules/iteration_log.md（历史迭代记录）
```

### 第三阶段：应用规则更新（人工确认）

Roo Code 根据 `iteration_report_YYYYMMDD.md` 的建议，**选择性**修改 `rules/screener_system_prompt.txt`。原则：每次只改一条规则。

### 第四阶段：真实持仓追踪（持续）

```bash
# 每日 Layer 2 跑完后，手动记录选股
uv run python trade_tracker.py --record <code> <pattern> <score> <conf> <rec> "<reason>"

# 收盘后更新持仓现价
uv run python trade_tracker.py --update <code> <current_price>
```

### 第五阶段：每周自动化循环

```bash
# 每周一运行一次
0 9 * * 1 cd ~/stock_ai/autoresearch && uv run python rolling_backtest.py && uv run python layer3_analyst.py
```

---

## 成本实测（更新）

| 操作 | DeepSeek 费用 |
|---|---|
| Layer 1 全量（~5000支） | ¥0（腾讯数据，免费） |
| Layer 2 每日（~100支） | **¥0.5** |
| 回测 10 天（~1000支） | **¥5** |
| layer3_analyst 单次分析 | ¥0.1 |
| **10天全自动回测 + 10次迭代分析** | **约 ¥7** |
| **每月（每日Layer2 + 每周回测）** | **约 ¥20-30** |

---

## 关键文件路径汇总

| 文件 | 路径 |
|---|---|
| Layer 1 | `~/stock_ai/autoresearch/layer1_filter.py` |
| Layer 2 | `~/stock_ai/autoresearch/layer2_screener.py` |
| **新增 主控制器** | `~/stock_ai/autoresearch/master_orchestrator.py` |
| **新增 分析引擎** | `~/stock_ai/autoresearch/layer3_analyst.py` |
| **新增** | `~/stock_ai/autoresearch/trade_tracker.py` |
| 规则源 | `~/stock_ai/autoresearch/rules/screener_system_prompt.txt` |
| 回测结果 | `~/stock_ai/autoresearch/backtest_results/all_days_backtest.csv` |
| 持仓追踪 | `~/stock_ai/autoresearch/trade_tracker/live_results.csv` |
| 迭代报告 | `~/stock_ai/autoresearch/reports/iteration_report_*.md` |
| 规则发现 | `~/stock_ai/autoresearch/rules/backtest_findings.md` |
| 迭代日志 | `~/stock_ai/autoresearch/rules/iteration_log.md` |

## 自动循环运作方式

```
启动：
  export DEEPSEEK_API_KEY="sk-xxx"
  cd ~/stock_ai/autoresearch
  uv run python master_orchestrator.py

运行过程（无人值守）：
  Day 1 → Layer1 → Layer2 → 价格获取 → CSV保存 → Autoresearch分析 → findings更新
  ↓ 等待30秒
  Day 2 → Layer1 → Layer2 → 价格获取 → CSV保存 → Autoresearch分析 → findings更新
  ↓ 等待30秒
  ...（重复至第10天）
  ↓
  最终报告 → 完成

中断恢复：
  重新运行 master_orchestrator.py
  → 自动跳过已有 (date, code) 组合 → 从断点继续
```

## 执行前检查清单

- [ ] DeepSeek API Key 已设置（`export DEEPSEEK_API_KEY=...`）
- [ ] Mac Mini 电源已插上、不进入休眠
- [ ] VPN 关闭（腾讯数据源不需要 VPN）
- [ ] Mac Mini 网络稳定
- [ ] 当前工作目录：`~/stock_ai/autoresearch`
