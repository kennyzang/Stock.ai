# Roo Code 修改指令：里程碑回测 v1.0 执行方案

**日期**: 2026-04-11
**目标**: 跑通三层闭环回测，产出可回滚的里程碑版本
**触发原因**: 前面6项审计修正已完成验证通过(6/6)，进入实际回测阶段

---

## ⚠️ 核心原则（不可违反）

1. **所有注释保持英文**，战法术语保留中文原文（收敛图、二踩、三高两低等）
2. **禁止引入 MACD/RSI/KDJ 等指标**
3. **禁止将图形战法改为纯数值量化**
4. 每次只改一个功能点，改完确认能跑再改下一个
5. 改完后在对应位置加注释：`# [MILESTONE v1.0] 原因简述`

---

## 📋 总体架构：三步走

```
Step 0: 新增"人机交互迭代"功能（Phase 1 必需的基础设施）
    ↓
Step 1: 2天测试（验证三层闭环跑通）
    ↓  通过后
Step 2: Phase 1 — 5天带教模式（每天停等用户点评）
    ↓  通过后  
Step 3: Phase 2 — 15天全自动自我进化
    ↓  完成
里程碑版本打Tag: milestone-v1.0
```

---

## 🔧 Step 0：新增"人机交互迭代"功能

### 问题诊断

当前 `master_orchestrator.py` 的主循环是：
```
for each day:
    Layer1 → Layer2 → Backtest → Layer3 Analyst → sleep → next day
```

**它永远不会停下来等你！** 但你的 Phase 1 需要的是：
```
for each day (Phase 1):
    Layer1 → Layer2 → Backtest → Layer3 Analyst → 输出报告 → ⏸️ PAUSE
    用户阅读报告 → 写入点评 → AI 吸收点评 → 继续下一天
```

### 需要做的改动

#### 改动 A：`master_orchestrator.py` — 新增 `--interactive` 模式

在 `main()` 函数的配置区（约第26-36行），新增一个标志：

```python
# After line 33 (AUTO_APPLY = ...)
INTERACTIVE_MODE = "--interactive" in sys.argv  # NEW: Phase 1 human-in-the-loop
USER_FEEDBACK_FILE = AUTO_DIR / "user_feedback.md"  # NEW: where user writes comments
```

在主循环中（约第515-598行），修改每天的结束逻辑：

**当前代码**（约第585-598行）：
```python
# Step 5: Run Autoresearch iteration immediately
success = run_analyst()

# Check elapsed time...
if elapsed > 6:
    break

if day_num < len(trading_days):
    print(f"\n  Sleeping {ANALYSIS_DELAY}s before next day...")
    time.sleep(ANALYSIS_DELAY)
```

**替换为**：
```python
# Step 5: Run Autoresearch iteration immediately
success = run_analyst()

# [MILESTONE v1.0] Interactive mode: pause for user feedback each day
if INTERACTIVE_MODE:
    print(f"\n{'='*60}")
    print(f"⏸️  DAY {day_num} COMPLETE — WAITING FOR USER FEEDBACK")
    print(f"{'='*60}")
    print(f"\nPlease review the report at:")
    print(f"  {AUTO_DIR / 'reports'}/")
    print(f"\nThen write your feedback to:")
    print(f"  {USER_FEEDBACK_FILE}")
    print(f"\nFeedback format (Markdown):")
    print(f"  ## Day {day_num} User Feedback")
    print(f"  ### 我同意的点")
    print(f"  - ...")
    print(f"  ### 我不同意或要修正的点")
    print(f"  - ...")
    print(f"  ### 我的补充观察")
    print(f"  - ...")
    print(f"\nWhen done, press ENTER to continue to next day...")
    
    # Wait for user to press Enter
    input()
    
    # Check if feedback file exists and pass it to analyst for re-analysis
    if USER_FEEDBACK_FILE.exists():
        print(f"\n>>> Re-running Layer 3 with user feedback...")
        _run_analyst_with_feedback(USER_FEEDBACK_FILE)

# Check elapsed time — stop if running too long (market open soon)
elapsed = (datetime.now() - start_time).total_seconds() / 3600
if elapsed > 6:
    print(f"\n[STOP] Runtime exceeded 6 hours. Saving state and exiting.")
    print(f"  Completed: {day_num}/{BACKTEST_DAYS} days")
    print(f"  Results saved to: {RESULTS_FILE}")
    break

if day_num < len(trading_days) and not INTERACTIVE_MODE:
    print(f"\n  Sleeping {ANALYSIS_DELAY}s before next day...")
    time.sleep(ANALYSIS_DELAY)
elif INTERACTIVE_MODE and day_num < len(trading_days):
    print(f"\n  [Interactive mode] Ready for next day when you press ENTER above")
```

#### 改动 B：`layer3_analyst.py` — 新增 `_run_analyst_with_feedback()` 函数

这是一个**新函数**，加在 `apply_rule_updates()` 函数之后（约第400行后）：

```python
def load_user_feedback(feedback_file: Path) -> str:
    """Load user's written feedback from markdown file.
    
    Args:
        feedback_file: Path to user_feedback.md
        
    Returns:
        String content of the feedback, or empty string if not found
    """
    if not feedback_file.exists():
        return ""
    return feedback_file.read_text(encoding="utf-8")


def generate_ai_analysis_with_feedback(
    backtest_summary: str, 
    live_summary: str, 
    all_backtest_results: list,
    manual_picks: list,
    user_feedback: str
) -> dict:
    """Re-analyze with user's expert feedback incorporated.
    
    This is the KEY innovation of Phase 1: the AI doesn't just look at numbers,
    it also absorbs the human expert's pattern recognition intuition and adjusts
    its rule suggestions accordingly.
    
    Args:
        Same as generate_ai_analysis(), plus:
        user_feedback: Raw text of user's written feedback/commentary
        
    Returns:
        Updated AI analysis dict with feedback-absorbed suggestions
    """
    # Start with the base analysis (reuse existing function)
    base_result = generate_ai_analysis(
        backtest_summary, live_summary, all_backtest_results, manual_picks
    )
    
    if "error" in base_result or not user_feedback.strip():
        return base_result
    
    # Now do a SECOND API call specifically to absorb and respond to feedback
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return base_result
    
    feedback_prompt = f"""You are an A-share trading strategy analyst learning from an expert human trader.

## EXPERT USER'S FEEDBACK (this is GOLD — absorb it carefully):

{user_feedback}

## YOUR PREVIOUS ANALYSIS (before reading user feedback):
- Overall win rate: {base_result.get('overall_win_rate', 'N/A')}
- WIN features: {base_result.get('win_features', [])}
- LOSS features: {base_result.get('loss_features', [])}
- Previous suggestion(s):
{chr(10).join(f'  - [{s.get("action")}] {s.get("location", "")}: {s.get("reason", "")[:150]}' for s in base_result.get('rule_suggestions', []))}

## YOUR TASK:

The user is an experienced A-share trader who developed this 三周期 strategy.
Their feedback represents years of pattern recognition experience that CANNOT be
fully captured in quantitative rules.

Please do the following:

1. **Acknowledge** which parts of your previous analysis the user confirmed
2. **Correct** which parts the user disagreed with — update your understanding
3. **Incorporate** any new observations the user made that you missed
4. **Propose UPDATED rule suggestions** that blend data-driven insights with user's expertise
   - Keep suggestions conservative (max 1 change)
   - Reference specific points from the user's feedback as evidence
   - If user said "don't change X" — respect that and don't suggest changing X

Respond ONLY with valid JSON:
{{
  "feedback_acknowledged": "Summary of what you learned from user",
  "analysis_changed": true/false,
  "updated_analysis": "Revised analysis incorporating user feedback (2-3 paragraphs)",
  "rule_suggestions": [
    {{
      "action": "ADD/REMOVE/MODIFY",
      "location": "section name",
      "current": "current text",
      "proposed": "new text based on user feedback + data",
      "reason": "evidence from user feedback + backtest data"
    }}
  ],
  "confidence": "high/medium/low"
}}"""

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": feedback_prompt}],
        "temperature": 0.3
    }

    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            content = result["choices"][0]["message"]["content"]
            start = content.find("{")
            end = content.rfind("}") + 1
            return json.loads(content[start:end])
    except Exception as e:
        print(f"[AUTORESEARCH] Feedback analysis failed: {e}")
        return base_result  # Fall back to original analysis
```

#### 改动 C：`master_orchestrator.py` — 新增 `_run_analyst_with_feedback()` 调用函数

在 `run_analyst()` 函数后面（约第490行后），新增：

```python
def _run_analyst_with_feedback(feedback_file: Path):
    """Run Layer 3 analyst with user feedback incorporated (Phase 1 only).
    
    This reads the user's written feedback, sends it to DeepSeek V3 along
    with the backtest data, gets updated rule suggestions, and applies them.
    """
    import sys as _sys
    sys.path.insert(0, str(AUTO_DIR))
    from layer3_analyst import (
        load_user_feedback, generate_ai_analysis_with_feedback,
        load_backtest_results, load_live_results, load_manual_picks,
        summarize_results, apply_rule_updates, write_iteration_log_summary
    )
    
    feedback_text = load_user_feedback(feedback_file)
    if not feedback_text.strip():
        print("[WARN] No feedback found in file, skipping feedback-aware analysis")
        return False
    
    all_backtest = load_backtest_results()
    all_live = load_live_results()
    manual_picks = load_manual_picks()
    backtest_summary = summarize_results(all_backtest, "BACKTEST")
    live_summary = summarize_results(all_live, "LIVE TRADING")
    
    print("\n>>> Running Feedback-Aware Analysis...")
    ai_result = generate_ai_analysis_with_feedback(
        backtest_summary, live_summary, all_backtest, manual_picks, feedback_text
    )
    
    if "error" in ai_result:
        print(f"[ERROR] Feedback analysis failed: {ai_result['error']}")
        return False
    
    # Apply the feedback-updated suggestions
    apply_rule_updates(ai_result, dry_run=not AUTO_APPLY)
    
    # Log this as a special "feedback" iteration
    now = datetime.now()
    fb_summary = f"""
## Autoresearch Iteration (FEEDBACK-ENHANCED)

**Date:** {now.strftime('%Y-%m-%d %H:%M')}
**Type:** Human-in-the-loop (user feedback absorbed)
**Win rate:** {ai_result.get('overall_win_rate', 'N/A')}
**User feedback acknowledged:** {ai_result.get('feedback_acknowledged', 'N/A')[:200]}
**Changes made:**
"""
    for sug in ai_result.get("rule_suggestions", []):
        fb_summary += f"- {sug.get('action')} {sug.get('location', '')}\n"
    
    with open(AUTO_DIR / "rules" / "iteration_log.md", "a", encoding="utf-8") as f:
        f.write(fb_summary)
    
    # Clear feedback file after processing (clean slate for next day)
    feedback_file.write_text("", encoding="utf-8")
    print("[AUTORESEARCH] Feedback processed and file cleared for next day")
    return True
```

### Step 0 完成标准

```bash
cd ~/stock_ai/autoresearch

# Test syntax:
uv run python -c "import master_orchestrator; print('OK')"
uv run python -c "import layer3_analyst; print('OK')"

# Test interactive mode detection (should not crash, should show help):
uv run python master_orchestrator.py --help 2>&1 | head -5
# Or just run with 0 days to see if it initializes correctly:
uv run python master_orchestrator.py 0 2>&1 | head -10
```

---

## 🧪 Step 1：2天测试（验证闭环）

### 目标

**唯一目标**：确认数据流完整跑通。不关注胜率（2天无统计意义）。

### 执行命令

```bash
cd ~/stock_ai/autoresearch

# 确保 API Key 已设置
export DEEPSEEK_API_KEY="your-key-here"

# 运行2天回测（DRY RUN 模式 — 不实际修改规则）
uv run python master_orchestrator.py 2
```

### 验证清单（每项必须 PASS）

| # | 验证项 | 怎么检查 | PASS 标准 |
|---|--------|---------|----------|
| 1 | Layer1 输出 | `ls layer1_candidates_*.csv` | 存在且非空 |
| 2 | Layer2 输出 | `ls layer2_results_*.csv` | 存在且有评分记录 |
| 3 | 回测结果 | `cat backtest_results/all_days_backtest.csv` | 有 outcome 列(WIN/LOSS/NO_BUY) |
| 4 | Layer3 分析 | `ls reports/iteration_report_*.md` | 报告文件存在 |
| 5 | 无 crash | 终端输出最后一行 | 看到 "COMPLETED ALL 2 DAYS" 或正常退出 |
| 6 | Day 2 受影响？ | 对比 Day1 vs Day2 结果 | 如果有规则变化，Day2 应与 Day1 有差异 |

### 如果某项 FAIL

- **Layer1 为空**: 检查 `--date` 参数是否被正确传递、腾讯API是否可达
- **Layer2 为空**: 检查 `DEEPSEEK_API_KEY` 是否设置、layer2_screener.py 是否能读取 Layer1 CSV
- **全是 NO_BUY**: 这是已知问题（之前 iteration_log 显示过），先不管，Step 2 会逐步修复
- **Crash**: 检查终端输出的 traceback，通常是数据格式或网络问题

### 预期输出示例（成功时）

```
============================================================
AUTONOMOUS BACKTEST + ITERATION LOOP
  Start: 2026-04-11 03:00:00
  Target: 2 trading days
  Auto-Apply: DISABLED (dry-run only)
============================================================

Trading days to backtest:
  2026-04-09 (Thursday)
  2026-04-10 (Friday)

############################################################
# DAY 1/2: 2026-04-09
############################################################

>>> Layer 1 for 2026-04-09
... (output) ...
  Layer 1 → XX candidates

>>> Layer 2 (DeepSeek V3 screening) for 2026-04-09
... (output) ...
  Layer 2 → XX AI-evaluated

  600XXX: convergence | score=X | WIN | ...
  ...

  Day 1 summary: XW/XL/X_NO_BUY/X_ERR | Win rate: XX%

>>> Running Autoresearch iteration...
... (analysis output) ...
Report: reports/iteration_report_YYYYMMDD_HHMM.md

############################################################
# DAY 2/2: 2026-04-10
############################################################
... (same structure) ...

============================================================
COMPLETED ALL 2 DAYS
  End: ...
  Total picks: XX
============================================================
```

---

## 🎓 Step 2：Phase 1 — 5天带教模式

### 核心理念

这是你的"AI 徒弟学艺"阶段。每天结束后你查看选股结果，写下你的专家点评，AI 吸收你的直觉和经验，调整自己的判断标准。

### 执行方式

```bash
cd ~/stock_ai/autoresearch
export DEEPSEEK_API_KEY="your-key-here"

# 运行5天交互模式（会每天暂停等你写反馈）
uv run python master_orchestrator.py 5 --interactive
```

### 每日工作流

```
Day N 开始
  │
  ├─→ Layer1 筛选（自动）
  ├─→ Layer2 打分（自动）
  ├─→ 回测模拟（自动）
  ├─→ Layer3 初次分析（自动）
  │
  ├─→ ⏸️  系统暂停，显示：
  │     "请查看报告: reports/iteration_report_XXXX.md"
  │     "请写入反馈: user_feedback.md"
  │     "按 Enter 继续..."
  │
  ├─→ 【你做这些】：
  │     1. 读报告（哪些票被选中了？WIN/LOSS分布？AI建议改什么？）
  │     2. 看 K 线图（用你的量化软件或通达信看当天选出的票）
  │     3. 写反馈到 user_feedback.md：
  │
  │        ## Day N 用户反馈
  │        
  │        ### 我同意的
  │        - AI 说 XXX 是 LOSS 特征，我同意，确实这种形态容易触发止损
  │        
  │        ### 我不同意/要修正的  
  │        - 600XXX 这只票 AI 给了 skip，但我认为应该 watch，
  │          因为它的末端虽然不够紧但量能配合很好，类似之前的节能风电
  │        - AI 建议放宽 CONVERGENCE_MAX_RATIO 到 8%，我认为太宽了，
  │          7% 更合理，否则太多噪音进来
  │        
  │        ### 我的补充观察
  │        - 今天选出的票里，二踩形态明显比收敛图胜率高，
  │          可能当前市场环境下二踩更有效
  │        - 注意到几只票的 MA250 刚好金叉，这个信号可能值得在 Layer2 加权
  │
  ├─→ 你按 Enter
  │
  ├─→ Layer3 重新分析（带着你的反馈）
  │     → AI 输出："我理解了您的意思...更新后的建议..."
  │     → 可能修改规则（如果 --apply 开启）或仅输出建议（dry-run）
  │
  └─→ 进入 Day N+1
```

### 反馈写作指南（给未来的自己）

好的反馈能让 AI 快速学到你的直觉模式：

| ✅ 好的反馈 | ❌ 无效的反馈 |
|---|---|
| 具体到某只股票为什么该选/不该选 | "感觉不对"（无法操作化）|
| 引用历史胜例作为类比（"像之前的联环药业"） | 全盘否定（"AI 选的都是垃圾"）|
| 给出具体数值建议（"7% 比 8% 更好"） | 与战法铁律矛盾（"MACD 金叉的也可以考虑"）|
| 解释**为什么**（"因为这种量能结构说明有主力在建仓"） | 复制粘贴同样的反馈每天 |

### Phase 1 结束时的预期状态

- 5 天全部跑完 ✓
- `rules/screener_system_prompt.txt` 可能有 2-4 处微调
- `layer1_filter.py` 的常量可能有 1-2 处微调
- `rules/iteration_log.md` 有 10 条记录（5天 × 每天2次：初分析+反馈分析）
- **最重要的是**：AI 的判断标准已经向你的直觉对齐

---

## 🚀 Step 3：Phase 2 — 15天全自动进化

### 执行方式

```bash
cd ~/stock_ai/autoresearch
export DEEPSEEK_API_KEY="your-key-here"

# 先创建里程碑备份（手动执行一次）
cp rules/screener_system_prompt.txt rules/screener_system_prompt.phase1_end.txt
cp layer1_filter.py layer1_filter.py.phase1_end.backup

# 运行15天全自动模式（不需要 --interactive，不需要暂停）
uv run python master_orchestrator.py 15 --apply
```

### 关键区别于 Phase 1

| | Phase 1 (5天) | Phase 2 (15天) |
|---|---|---|
| 人工参与 | 每天 | 无 |
| 规则修改 | 经用户批准后生效 | AI 自动提议并应用（受±50%护栏约束）|
| 学习来源 | 数据 + 用户专家点评 | 纯数据驱动 |
| 目标 | 让 AI 学会你的判断风格 | 让 AI 发现你没注意到的细节 |
| 风险 | 低（有人把关）| 中（但有护栏）|

### 安全保障（已有代码实现，无需额外开发）

- **±50% 单次变化上限** (`layer3_analyst.py` 第452行)：防止参数漂移
- **每次只改1条规则** (`apply_rule_updates` 第358行)：保守迭代
- **只改常量不改逻辑** (`_apply_l1_update` 第405-406行)：保护核心检测逻辑
- **自动备份** (`write_rules` 第47-49行)：每次修改前备份原文件
- **6小时超时** (`master_orchestrator.py` 第590行)：防止无限运行

### 建议增加的总变化上限

当前代码只有单次变化限制（±50%），但没有**累积变化限制**。建议 Roo Code 在 `_apply_l1_update()` 中增加：

```python
# [MILESTONE v1.0] Add cumulative drift protection
# Track total change from initial value across all iterations
INIT_VALUES_FILE = AUTO_DIR / "rules" / "_initial_param_values.json"

def _load_initial_values() -> dict:
    """Load or create initial parameter baseline."""
    if INIT_VALUES_FILE.exists():
        import json
        return json.loads(INIT_VALUES_FILE.read_text())
    # First run: snapshot current values as baseline
    initial = {}
    content = LAYER1_FILTER_PATH.read_text(encoding="utf-8")
    for param_name in ALLOWED_PARAM_NAMES:
        match = re.search(rf'^{param_name}\s*=\s*([\d.]+)', content, re.MULTILINE)
        if match:
            initial[param_name] = float(match.group(1))
    INIT_VALUES_FILE.write_text(json.dumps(initial, indent=2))
    return initial

# In _apply_l1_update(), after the single-change check (around line 452),
# ADD this cumulative check:
initial_vals = _load_initial_values()
if param_name in initial_vals:
    init_val = initial_vals[param_name]
    cumulative_change = abs(new_num - init_val) / init_val if init_val > 0 else 0
    if cumulative_change > 0.50:  # Total drift never exceeds ±50% from baseline
        print(f"[AUTORESEARCH] [BLOCKED] Cumulative drift too large: "
              f"{param_name} {init_val} → {new_value} "
              f"(total drift: {cumulative_change*100:.0f}%. Max allowed: ±50%)")
        return
```

这确保即使跑了 20 轮迭代，任何参数都不会偏离初始值超过 50%。**这是防止过拟合的最后一道防线。**

---

## 🏁 里程碑完成 & 打 Tag

Phase 2 跑完后，手动执行：

```bash
cd ~/stock_ai/autoresearch

# 1. 记录最终参数快照
echo "# Milestone v1.0 Final State $(date)" > MILESTONE_v1.0_README.md
grep -E "^(CONVERGENCE_MAX_RATIO|MIN_TURNOVER|VOLUME_DECLINE)" layer1_filter.py >> MILESTONE_v1.0_README.md
echo "" >> MILESTONE_v1.0_README.md
echo "## Final Win Rate:" >> MILESTONE_v1.0_README.md
tail -5 rules/backtest_findings.md >> MILESTONE_v1.0_README.md

# 2. Git tag（如果使用 git）
git add -A
git commit -m "milestone-v1.0: 20-day backtest complete, auto-iterated rules"
git tag -a milestone-v1.0 -m "Stable baseline for future rollback"

# 3. 汇总最终胜率
echo "=== FINAL RESULTS ==="
python -c "
import csv
with open('backtest_results/all_days_backtest.csv') as f:
    rows = list(csv.DictReader(f))
wins = [r for r in rows if r['outcome']=='WIN']
losses = [r for r in rows if r['outcome']=='LOSS']
tradable = wins+losses
print(f'Total picks: {len(rows)}')
print(f'WIN: {len(wins)} | LOSS: {len(losses)}')
print(f'NO_BUY: {len([r for r in rows if r[\"outcome\"]==\"NO_BUY\"])}')
if tradable:
    print(f'Win rate: {len(wins)/len(tradable)*100:.1f}%')
"
```

---

## 📊 完整时间预估

| 阶段 | 天数 | 预估耗时 | 说明 |
|------|------|---------|------|
| Step 0 开发 | - | Roo Code 执行 ~30min | 新增交互模式代码 |
| Step 1 测试 | 2天 | ~10-20min | 主要是网络延迟(Layer2调API) |
| Phase 1 带教 | 5天 | ~1-2小时（含你写反馈的时间）| 每天约10-15min自动化 + 你的审阅时间 |
| Phase 2 自动 | 15天 | ~2-3小时 | 全自动，无需干预 |
| **合计** | **22天** | **~3-5小时** | |

成本估算（DeepSeek API）：
- 每次 Layer3 分析约 ¥0.01-0.05（取决于 prompt 长度）
- Phase 1: 5天 × 2次/天(初析+反馈) = 10次 ≈ ¥0.1-0.5
- Phase 2: 15天 × 1次/天 = 15次 ≈ ¥0.15-0.75
- Layer2 成本更高（每支股票一次API调用）：约 ¥0.5-2/天
- **总成本预估**: 约 ¥15-50（主要花在 Layer2，不是 Layer3）

---

## 📋 修改总结表

| Step | 文件 | 改动类型 | 核心内容 |
|------|------|----------|----------|
| **0A** | `master_orchestrator.py` | 新增 `--interactive` 模式 | 主循环中增加暂停+等待用户反馈逻辑 |
| **0B** | `layer3_analyst.py` | 新增2个函数 | `load_user_feedback()` + `generate_ai_analysis_with_feedback()` |
| **0C** | `master_orchestrator.py` | 新增1个函数 | `_run_analyst_with_feedback()` — 桥接用户反馈到 Layer3 |
| **0D** | `layer3_analyst.py` | 增强 | `_apply_l1_update()` 中增加累积漂移保护(±50%总上限) |

**共 4 个改动点，全部是新增代码，不修改现有逻辑。**
