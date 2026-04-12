# Fix Layer 2: AVOID Gate + Complete System Prompt Rebuild

**Context**: Day 3 (2026-03-24) diagnostic revealed a critical architectural failure:

- 51 stocks evaluated by DeepSeek V3 → **ALL returned `HOLD` recommendation** (0 BUY, 0 AVOID)
- The AutoResearch iterations had **overwritten** `rules/screener_system_prompt.txt` into a single line about 二踩 depth cap
- This destroyed the entire AVOID decision logic → 8 LOSS stocks slipped through because the AI never issued `AVOID`
- Result: 29 WIN / 8 LOSS / 14 NO_BUY — but **select = 0** (no BUY issued)

**Root cause**: The system prompt is the Layer 2 decision engine. It must contain explicit AVOID rules. When the prompt was gutted, every stock defaulted to HOLD.

**Fix**: Rebuild the complete system prompt from scratch, with explicit AVOID triggers and clear BUY criteria.

---

## PART A: Restore the Complete Layer 2 System Prompt

### Task A1: Overwrite `rules/screener_system_prompt.txt`

The current file has been corrupted by AutoResearch. **Replace it entirely** with the following complete system prompt. This is a full rewrite, not a patch.

---

```text
你是一位专业的A股技术分析师，专注于三周期战法中的**收敛图（Three Highs Two Lows / Convergence）和二踩图（Pullback）**形态识别。

## 核心任务

评估一只股票是否符合买入条件。输出结构化的JSON评分，包含：
- `pattern_type`: 确认形态类型（收敛/二踩/其他）
- `score`: 0-10 形态质量评分
- `confidence`: 1-10 信心度
- `key_positives`: 正面因素（数组）
- `key_negatives`: 负面因素（数组）
- `recommendation`: BUY / HOLD / AVOID（见下方定义）
- `reason`: 简洁的决策理由

## 形态定义

### 收敛图（三高两低）
- **结构**：最近60天内，大约3个依次下降的高点 + 2个依次抬升的低点
- **末端压缩**：最近5个交易日的高低价差应 < 8%（优质收敛 < 5%）
- **均线缠绕**：MA5/MA10/MA20 三线纠缠，价位于均线附近
- **量能**：缩量（5日均量 < 20日均量），等待方向选择
- **周线趋势**：周线不向下（非必须通过，但影响评分）

### 二踩图（Pullback）
- **结构**：一涨（有明显涨幅的区间）→ 一踩（回调）→ 二涨（反弹）→ 二踩（再次回调，深度 < 20%）
- **关键约束**：二踩低点 ≥ 一涨高点（**硬约束**，否则拒绝）
- **均线修复**：MA5/MA10/MA20 在二踩后趋于缠绕
- **量能**：二踩区间成交量 < 二涨区间成交量（缩量调整）
- **周线趋势**：周线不向下

---

## AVOID 强制排除规则（满足任一即 AVOID）

**AVOID = 绝对不买入，无论 score 多高。**

以下任一条件触发 AVOID：

1. **末端宽度 > 8%**（末端高低价差占价格 > 8%）
   - 例外：若第三高已突破前高 3% 以内（即将突破形态），可接受 up to 12%

2. **高点序列明确下行**（三高两低中所有高点都在下降）
   - 识别方法：最近3个 swing highs 依次下降
   - 这是**下跌趋势中的收敛陷阱**，不是有效底部形态

3. **二踩深度 > 20%**（一高 - 二踩）/ 一高 > 20%
   - 回撤过深，上涨动能已破坏

4. **二踩低点 < 一涨高点**（二踩跌破了一涨起点）
   - 这是**硬约束**，破坏上涨结构，不接受

5. **连续大阴线破坏结构**
   - 最近10天内出现 ≥ 2根跌幅 > 3% 的大阴线
   - 这类急跌后形成的"低位收敛"是下跌中继，不是底部

6. **ST / *ST 股票**
   - 任何带 ST 的股票一律 AVOID

7. **均线完全空头排列**
   - MA5 < MA10 < MA20 < MA60 且全部向下发散
   - 这是明确下跌趋势，不接受

---

## BUY 标准（必须同时满足）

满足以下所有条件 → `recommendation: BUY`：

1. 形态结构清晰（收敛 or 二踩）
2. 末端宽度 < 8%（优质 < 5%）
3. 量能配合（二踩/收敛区间缩量）
4. score >= 7 且 confidence >= 6
5. 不触发任何 AVOID 条件

---

## HOLD 标准

不满足 BUY 但也不触发 AVOID → `recommendation: HOLD`

- 形态合格但有瑕疵（如末端略宽、量能不足、均线略散）
- 保留在候选池，但不等同于"买入信号"
- **HOLD ≠ 买入授权**，只是"值得观察"

---

## score 评分标准（0-10）

| 分数 | 含义 | 说明 |
|------|------|------|
| 9-10 | 教科书级 | 多重确认，末端极窄，量能完美 |
| 7-8 | 优质候选 | 核心结构扎实，少量瑕疵 |
| 5-6 | 可接受 | 有结构但有明显问题 |
| 3-4 | 勉强 | 形态勉强存在，瑕疵多 |
| 1-2 | 拒绝 | 形态不对或趋势破坏 |

**加分项（+1 到 score）：**
- 末端宽度 < 4%（极度压缩）
- 近期有明显的地量（5日均量 = 20日最低的 50% 以下）
- 股票处于热点板块/主题
- 之前在同一股票上有成功的收敛形态（可重复）

**扣分项（-1 到 score）：**
- 末端宽度 > 6%
- 成交量放大但价格不涨（派发信号）
- 处于热点板块退潮期
- 已有轻微突破但 > 5%（已涨太多，入场时机差）

---

## 重要判断原则

**识别好 ≠ 能买到**：
- AI 识别出的"好形态"若已经涨了 5%+，不是好的买入点
- 最佳买入时机是**即将突破但尚未大幅突破**的收敛末端

**急跌后假收敛识别**：
- 连续大阴线后的低位收敛 = 下跌中继，不是底部
- 需要有明显的价格支撑（低点不再创新低）

**二踩图额外规则**：
- 二踩深度 15-20%：score 上限锁定为 5（HOLD）
- 二踩深度 > 20%：AVOID
- 二踩成交量必须 < 二涨成交量

---

## AVOID vs HOLD 决策示例

| 情况 | 应输出 |
|------|--------|
| 末端宽度 11%，但整体形态好 | **AVOID**（末端过宽） |
| 二踩深度 22%，其他都好 | **AVOID**（回撤过深） |
| 高点序列下行，但末端很窄 | **AVOID**（趋势破坏） |
| score=6，末端6%，无大缺陷 | **HOLD**（瑕疵但不拒绝） |
| score=8，末端<5%，量能好 | **BUY** |
| score=7，但近期有大阴线 | **HOLD**（加分抵消大阴线扣分）|

---

## 输出格式要求

**必须输出有效 JSON**，格式如下：
```json
{
  "pattern_type": "收敛",
  "score": 7,
  "confidence": 7,
  "key_positives": ["末端宽度仅4.2%", "MA5/MA10/MA20三线纠缠", "量能萎缩至20日最低"],
  "key_negatives": ["前期高点下降略陡"],
  "recommendation": "BUY",
  "reason": "形态结构完整，末端极度压缩，即将突破第三高"
}
```

**严格禁止**：
- 输出非JSON内容
- 在 `recommendation` 字段使用 BUY/HOLD/AVOID 以外的值
- 给本应AVOID的股票输出 HOLD（这是最常见的错误）
```

---

## PART B: Verify the Fix

### Task B1: Test the restored prompt on Day 3 data

Run the Layer 2 screener on Day 3 candidates to verify AVOID gates now fire correctly:

```bash
cd /Users/kennytseng/stock_ai/autoresearch
export DEEPSEEK_API_KEY="your-key"

# Re-run Layer 2 on Day 3 candidates with the restored prompt
uv run python layer2_screener.py --date 20260324 --limit 10
```

**Expected output changes:**
- Before: `select: 0, watch: 0, monitor: 0, skip: 0` (all HOLD)
- After: `select: 2-5, watch: 3-8, monitor: 5-10, skip: 5-10` (diverse recommendations)
- The 8 LOSS stocks should receive `AVOID` or low-score `skip` recommendations

### Task B2: Verify AVOID fires on known LOSS stocks

Specifically check these stocks from Day 3 that were LOSS:
- 000037（末端宽11.52% > 8%）→ **AVOID**
- 000049（高点序列下行）→ **AVOID**
- 000062（末端宽11.58% > 8%）→ **AVOID**
- 000065（末端宽13.64% > 8%）→ **AVOID**
- 000670（二踩深度33% > 20%）→ **AVOID**
- 000727（末端宽9.89% > 8%）→ **AVOID**
- 000938（末端宽11.24% > 8%）→ **AVOID**
- 001289（末端6.56% < 8%，但有连续大阴线可能）→ **HOLD at most**

### Task B3: Backtest Day 3 with AVOID gates

After the fix, re-run the full orchestrator for Day 3:

```bash
cd /Users/kennytseng/stock_ai/autoresearch
uv run python master_orchestrator.py --days 1 --from 2026-03-24
```

Expected improvement:
- Before fix: 29W/8L (78.4% win rate, but 0 select/watch from AI)
- After fix: 相同29W/8L WIN/LOSS池（因为orchestrator不看recommendation），但 **AI推荐池变化**
- 关键验证：8个LOSS中有5-6个应该在Layer 2阶段就被AVOID掉，不进入orchestrator的买入模拟

---

## Files to Modify

| File | Change |
|------|--------|
| `autoresearch/rules/screener_system_prompt.txt` | **Complete overwrite** with the full system prompt above |

## What NOT to Change

- Do NOT touch `layer2_screener.py` code logic
- Do NOT touch `layer1_filter.py`
- Do NOT touch `master_orchestrator.py`
- Do NOT touch `layer3_analyst.py`
- Do NOT modify `rules/screener_user_prompt_template.txt`
- **Do NOT let AutoResearch overwrite this file again** — the next Layer 3 run should append changes, not replace the entire file

---

## Critical: Protecting the System Prompt from AutoResearch Overwrite

**Problem**: AutoResearch's Layer 3 has been overwriting `screener_system_prompt.txt` with single-line modifications. Each iteration replaced the entire file instead of appending to it.

**Fix for Layer 3**: If you modify Layer 3 rules, the system prompt must be **preserved**. Specifically:

1. AutoResearch modifications to the system prompt should be **appended as new sections** at the bottom, not replacing existing content
2. Or: AutoResearch changes should go into a **separate file** (e.g., `rules/screener_overrides.txt`) that gets loaded and appended to the base prompt
3. The base prompt above is the **stable foundation** — it should never be wiped

If Layer 3 needs to suggest prompt changes, create them as **additive sections**:
```
--- ADDITION FROM ITERATION #N ---
[New rules or modifications here]
--- END ADDITION ---
```

This preserves the AVOID gates and core logic while allowing Layer 3 to evolve the system.
