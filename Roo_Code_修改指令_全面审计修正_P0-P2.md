# Roo Code 修正指令：全面代码审计修正 (P0-P2)

**日期**: 2026-04-11
**触发原因**: 战法文档 vs 代码逐行对照审计，发现 6 个问题（2个P0 + 1个P1 + 3个P2）

---

## ⚠️ 核心原则（不可违反）

1. **只修改本指令明确指定的内容**，不要顺便"优化"其他地方
2. **每次只改一个逻辑点**，改完确认能跑再改下一个
3. **所有注释保持英文**，战法术语保留中文原文（如"三高两低"、"收敛图"、"二踩图"）
4. 改完后在对应位置加一行注释：`# [AUDIT FIX 2026-04-11] 原因简述`
5. 修改完成后运行一次 `python layer1_filter.py --dry-run` 确认无语法错误

---

## 🔴 P0-1：`convergence_position_check` 低位判断公式完全重写

### 问题诊断

**文件**: `layer1_filter.py`
**函数**: `convergence_position_check()`
**当前代码** (约第529-531行):

```python
price_range_20d = max_price_20d - min_price_20d     # e.g. 103 - 100 = 3
low_ratio = min_price_20d / price_range_20d          # 100 / 3 = 33.3
if low_ratio < 0.15:
    reasons.append(f"Convergence zone at bottom of range ({low_ratio:.2f} < 0.15)")
    return False
```

### 为什么这是错的

这个公式算的不是"位置比例"，而是 `绝对价格 / 价格区间`。对于正常A股：

| 股价范围 | min_price | range | low_ratio | 结果 |
|----------|-----------|-------|-----------|------|
| 100-103 | 100 | 3 | **33.3** | 通过 ❌ 应拒绝 |
| 10-12 | 10 | 2 | **5.0** | 通过 ❌ 应拒绝 |
| 3-4 | 3 | 1 | **3.0** | 通过 ❌ 应拒绝 |

**只有股价<1元时才会触发拒绝。对99%A股这是完全失效的死代码。**

### 正确做法

应该用更大的时间窗口(60天)作为参照系，判断20天收敛区在其中的相对位置。

### 修改要求

将 `convergence_position_check()` 函数中的低位检测部分替换为以下逻辑：

```python
# [AUDIT FIX 2026-04-11] Fixed dead-code formula: was using abs_price/range instead of relative position
# Use 60-day window as reference frame for position judgment
wider_df = history_df.tail(60)
if len(wider_df) < 30:
    # Not enough data for wider context — skip position check (conservative: allow)
    return True, reasons

wider_low = wider_df["low"].min()
wider_high = wider_df["high"].max()
wider_range = wider_high - wider_low

if wider_range <= 0:
    return True, reasons

# Position of convergence zone's lowest point within the 60-day range
# low_position = 0 means at absolute bottom, = 1 means at absolute top
low_position = (min_price_20d - wider_low) / wider_range

# Also check high position — reject if convergence is at extreme top too
high_position = (max_price_20d - wider_low) / wider_range

if low_position < 0.15:
    reasons.append(
        f"Convergence zone at bottom of 60-day range "
        f"(position={low_position:.3f} < 0.15)"
    )
    return False, reasons

if high_position > 0.90:
    reasons.append(
        f"Convergence zone at top of 60-day range "
        f"(position={high_position:.3f} > 0.90)"
    )
    return False, reasons
```

**关键要点**：
- 用60天K线的高低价差作为参照系
- 计算的是**相对位置比例**（0~1之间），不是绝对价格比
- 同时检查极端高位（>90%），因为顶部横盘突破失败的风险也很大
- 数据不足时保守放行（返回 True），而不是错误地拒绝

---

## 🔴 P0-2：System Prompt "已突破就跳过"规则与胜例矛盾

### 问题诊断

**文件**: `rules/screener_system_prompt.txt`（或同级的 system prompt 文件）

**当前文字**（约第144-146行）:

```
## MANDATORY EXCLUSION RULES:
2. SKIP any stock that has already broken above and moved away 
   from the convergence/pullback pattern (pattern already played out)
```

### 为什么这是错的

手工选股 WIN 案例直接与此规则矛盾——你选入股票的时机恰恰就是**刚突破或即将突破**的时候：

| 股票 | 你的选股备注 | 结果 |
|------|-------------|------|
| 600513 联环药业 | "已略微突破二高但未突破一高" | ✅ WIN |
| 688205 德科立 | "第三高即将突破第二高"选入 | ✅ WIN |
| 688307 中润光学 | "快要逼近一高"选入 | ✅ WIN |

当前规则等于把你的胜例模式全部杀掉。

### 修改要求

将排除规则第2条替换为：

```
## MANDATORY EXCLUSION RULES:
2. SKIP only if stock has broken out AND extended >8% from the consolidation 
   zone high. A small breakout of 1-5% is actually the IDEAL entry timing 
   for 收敛图/二踩图 patterns — it confirms smart money is stepping in.
   
   Examples of GOOD entry (DO NOT SKIP):
   - Price just pierced through 二高 (2nd peak) by 1-3%
   - Price approaching 一高 (1st peak) within 2%
   - Breakout with moderate volume (shows conviction, not exhaustion)
   
   Examples of SKIP (pattern played out):
   - Already broken above 一高 by >8% and pulled back
   - Breakout followed by 3+ days of decline (failed breakout)
   - Price far above all recent structure (no meaningful pullback zone left)
```

---

## 🟡 P1：成交量缩量规则过严 — 增加"有量能"为正面选项

### 问题诊断

**文件**: `rules/screener_system_prompt.txt`

**当前正面因子中关于成交量的描述**（约第71-72行）:

```
POSITIVE SIGNALS:
- Volume clearly declining in final days — smart money waiting for breakout
- End zone extremely tight (< 4%) — shows market compression
```

### 为什么需要调整

手工WIN案例的成交量特征：

| 股票 | 成交量描述 | 结果 |
|------|-----------|------|
| 601016 节能风电 | "**成交量不低有量能**" | ✅ WIN |
| 688336 三生国健 | "**成交量不低有量能**" | ✅ WIN |
| 600513 联环药业 | 未特别提及缩量 | ✅ WIN |
| 688205 德科立 | 未提及缩量 | ✅ WIN |
| 688307 中润光学 | 二踩模式，缩量符合预期 | ✅ WIN |

**3/5 的收敛图 WIN 案例都是"有量能"而非"缩量"！**

AI 因为"成交量没有萎缩"而扣分 → 有资金活跃度支撑的优质股被低估。

### 修改要求

在 POSITIVE SIGNALS 部分找到成交量相关描述，替换为更平衡的双轨制：

```
POSITIVE SIGNALS (VOLUME — two valid patterns):

Pattern A — Volume Contraction (classic 收敛图):
- Volume clearly declining in final days — smart money waiting for breakout
- Best when combined with end-zone width < 4%

Pattern B — Smart Money Accumulation (equally valid):
- Volume shows sustained interest: average volume of last 5 days >= 80% of 20-day average
- BUT without spiking: no single day volume > 3x the 5-day average
- This indicates institutional accumulation before breakout — also a strong positive signal

IMPORTANT: Both Pattern A and Pattern B are equally valid. Do NOT penalize 
a stock for having "too much volume" unless it shows clear volume exhaustion 
(spike then collapse on next day).
```

同时在 NEGATIVE SIGNALS 部分确保有明确的量能负面信号定义：

```
NEGATIVE SIGNALS (VOLUME):
- Volume exhaustion spike: single day volume > 4x average, followed by sharp price drop
- Complete dry-up: volume near zero with no price movement (dead stock, not consolidation)
```

---

## 🟡 P2-1：`three_highs_two_lows` docstring 过期

### 问题诊断

**文件**: `layer1_filter.py`
**位置**: `three_highs_two_lows()` 函数 docstring（约第386行）

```python
# Docstring 当前写的：
"""Check for 三高两低 pattern...
    Requirements:
    1) End zone width < 10% (price compressing at the edge)   ← 这里写的10%
    ...
"""
# 但实际代码用的是：
if end_zone_width < CONVERGENCE_MAX_RATIO:  # CONVERGENCE_MAX_RATIO = 0.06 = 6%
```

### 修改要求

将 docstring 中所有 `< 10%` 的描述改为 `< 6%`（或引用常量名 `CONVERGENCE_MAX_RATIO`）。

如果 docstring 里还有其他硬编码阈值（如提到具体的 0.85、0.97 等），统一改为引用对应的常量名。

---

## 🟡 P2-2：时间止损描述消除歧义

### 问题诊断

**文件**: `rules/screener_system_prompt.txt`

**当前描述**（约第153行）:

```
Time stop: if the position has NEVER shown a peak gain of +4% or more 
within 3 trading days, exit on Day 4 regardless of price
```

这里说"3天内"但在"第4天退出"。实际代码 `max_hold_days=4` 表示最多持有4天。表述容易让AI误解。

### 修改要求

替换为：

```
Time Stop Rule (exactly as coded):
- max_hold_days = 4 (can hold Day 1, 2, 3, and 4; forced exit at close on Day 4)
- Exception: if peak gain reaches >= +4% on any day, switch to dynamic trailing stop
- This means: you get 3 full days (Day 1-3) to show a +4% peak gain
- If Day 4 arrives with no +4% peak ever achieved → force sell at market close
- Additional rule: if holding >= 4 days AND currently profitable (any amount), also sell
```

---

## 🟡 P2-3：Layer2 end_zone_width 单位标注

### 问题诊断

**文件**: `layer2_screener.py` 或负责构建 Layer2 prompt 的模块

**Layer1 计算** (`layer1_filter.py` 第598行):
```python
end_zone_width = (max_price_end - min_price_end) / ref_price  # 返回小数如 0.05
# 但传给 Layer2 时可能乘了100变成百分比数值
```

**Layer2 prompt template** 中展示给 AI 的格式如果不带 `%` 符号，AI 看到 `5.23` 可能混淆是 `5.23%` 还是 `0.0523`。

### 修改要求

1. 在构建传给 Layer2 的数据字典时，确认 `end_zone_width_pct` 的值确实是百分比数（即 0-100 的范围，不是 0-1 的范围）
2. 在 prompt template 中该字段显示的地方，加上 `%` 符号：

```
Before:
End-zone width: {end_zone_width_pct} (threshold: < 8)

After:  
End-zone width: {end_zone_width_pct}% (threshold: < 8%)
```

同样检查 System Prompt 中所有涉及 end_zone_width 的阈值描述，确保单位一致。

---

## ✅ 修改后验证清单

完成以上所有修改后，按顺序执行以下验证：

### Step 1: 语法检查
```bash
cd /Users/kennytseng/stock_ai/autoresearch
python -c "import layer1_filter; print('Layer1 OK')"
python -c "import layer2_screener; print('Layer2 OK')" 
```

### Step 2: Dry Run（使用最近一个交易日数据）
```bash
python layer1_filter.py --dry-run
```
确认：
- 输出正常，没有 crash
- 被过滤掉的股票数量在合理范围内（不是全部通过或全部拒绝）
- 如果有 `--debug` 参数，开启后查看 `convergence_position_check` 的输出，确认低位股被正确拒绝

### Step 3: System Prompt 一致性检查
```bash
grep -n "broken above\|breakout\|SKIP\|volume\|Volume" rules/screener_system_prompt.txt
```
确认修改后的措辞与上述要求一致。

### Step 4: 回归测试
如果项目中有测试文件（如 `test_layer1.py` 或类似），运行它们：
```bash
python -m pytest test/ -v 2>/dev/null || echo "No pytest tests found"
```

---

## 📋 修改总结表

| # | 优先级 | 文件 | 问题 | 修复类型 |
|---|--------|------|------|----------|
| P0-1 | 🔴 严重 | `layer1_filter.py` | `convergence_position_check` 公式是死代码 | **公式重写**（用60天参照系） |
| P0-2 | 🔴 严重 | `screener_system_prompt.txt` | "已突破就跳过"杀死WIN模式 | **规则重写**（允许1-5%小型突破） |
| P1 | 🟡 中等 | `screener_system_prompt.txt` | 成交量必须缩量才加分，与胜例矛盾 | **增加双轨制**（缩量OR有量能均可） |
| P2-1 | 🟢 低 | `layer1_filter.py` | docstring 写10%但代码用6% | **文字修正** |
| P2-2 | 🟢 低 | `screener_system_prompt.txt` | 时间止损描述有歧义 | **文字精确化** |
| P2-3 | 🟢 低 | `layer2_screener.py` | end_zone_width 缺少 % 单位标注 | **格式修正** |
