# Roo Code 修改指令：周线趋势算法修复

**目标**：修复 `weekly_trend_not_declining()` 的算法设计问题

**问题根因**：

当前逻辑同时检查：
```
recent_low > prior_low  OR  recent_high >= prior_high
```

对于联环药业（600513）：
- Prior Half = 8月~11月底，包含**24.60的高点**（起涨前的峰）
- Prior High = 24.60 → recent_high(22.80) < prior_high → **False**
- 结论：拒绝 ✅

**但这是错的**：prior_half 的 high 不是比较基准——它是那段时间内刚好出现的峰值，不代表什么趋势。用它来比较会让所有"反弹后还没超过前高"的股票都被拒绝。

---

## 修复方案

### Part A：重构 `weekly_trend_not_declining()` 函数

**新逻辑**：不锚定 prior_half，改为锚定"整体窗口的历史最低点"

```
下跌趋势定义：recent 创了历史新低
  → recent_low <= overall_min × 0.97 → 拒绝（下跌趋势）
  → recent_low >  overall_min × 0.97 → 通过（恢复/震荡，非下跌）

容忍 3% 容差：允许轻微刺穿（噪音/轻微假突破）
```

**实现代码**（替换 `weekly_trend_not_declining` 函数）：

```python
def weekly_trend_not_declining(history_df, lookback_weeks=None):
    """Check if weekly trend is NOT declining.

    Downtrend = recent weeks making new lows relative to the entire lookback window.
    Anchor is the overall minimum, NOT the prior_half baseline.

    Args:
        history_df: daily price DataFrame
        lookback_weeks: effective lookback (auto-computed if None)

    Returns:
        True = trend is not declining (PASS), False = declining (REJECT)
    """
    if lookback_weeks is None:
        lb = get_effective_lookback(history_df)
        lookback_weeks = lb['weekly_lookback_weeks']

    weekly_close = history_df.set_index('date')['close'].resample('W-FRI').last().dropna()
    available = len(weekly_close)
    if available < 6:
        return True  # Not enough data, skip

    lookback = min(available, lookback_weeks)
    recent_count = max(2, lookback // 2)

    # Entire lookback window for reference
    lookback_weeks_data = weekly_close.tail(lookback)
    overall_min = lookback_weeks_data.min()

    # Recent half: check if making new lows
    recent_half = weekly_close.tail(recent_count)
    recent_low = recent_half.min()

    # Downtrend = recent_low at or near the historical floor
    # Allow 3% tolerance to avoid rejecting minor retests of the floor
    return recent_low > overall_min * 0.97
```

**注意**：
- 移除原来的 `prior_half` 比较和 `prior_high` 检查
- 不再要求 recent_high >= prior_high
- 只要 recent 没有持续创新低，就通过

### Part B：保留原有 WEEKLY_LOOKBACK_WEEKS = 52 不变

**不要降低 52 周窗口**。窗口本身没问题，是算法锚点错了。

---

## 对立案例验证

| 场景 | 条件 | 旧逻辑 | 新逻辑 |
|------|------|--------|--------|
| **联环药业**（反弹后recent_low≈整体最低） | recent=17.87, overall=17.87 | ❌ 拒绝（prior_high=24.60） | ✅ 通过 |
| **真正下跌**（recent持续创新低） | recent=5.0, overall=5.0 | ❌ 拒绝 | ❌ 拒绝 ✅ |
| **健康上涨**（recent远高于整体最低） | recent=12.3, overall=8.0 | ✅ 通过 | ✅ 通过 |
| **三高两低收敛**（低点抬高+高点收敛） | recent>overall | ❌ 可能拒绝 | ✅ 通过 |

### 验证命令

```bash
cd /Users/kennytseng/stock_ai/autoresearch
uv run python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')
from layer1_filter import *

# Test 1: 联环药业
df = fetch_daily_history('600513', '2025-08-01', '2026-03-25')
result = weekly_trend_not_declining(df)
print(f"联环药业 (600513): {'PASS ✅' if result else 'FAIL ❌'}")

# Test 2: 恒源煤电
df2 = fetch_daily_history('600971', '2025-08-01', '2026-03-25')
result2 = weekly_trend_not_declining(df2)
print(f"恒源煤电 (600971): {'PASS ✅' if result2 else 'FAIL ❌'}")

# Test 3: 收敛+反弹股票（如三生国健）
df3 = fetch_daily_history('600536', '2025-08-01', '2026-03-25')  # 示例
result3 = weekly_trend_not_declining(df3)
print(f"三生国健 (600536): {'PASS ✅' if result3 else 'FAIL ❌'}")
PYEOF
```

---

## 修改文件

1. `layer1_filter.py` — 重写 `weekly_trend_not_declining()` 函数

## 输出要求

- 修改后运行验证命令，确保联环药业通过
- 确认其他已知的好图形（三高两低、收敛回踩）不受影响
