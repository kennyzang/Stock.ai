# Roo Code 修改指令：Layer1 逻辑错误修正

> 目标文件：`/Users/kennytseng/stock_ai/autoresearch/layer1_filter.py`
> 修改原因：修复两个实际影响选股结果的逻辑错误

---

## 修改一：末端宽度计算分母修正

**问题定位：** `convergence_prefilter` 函数，约第595-599行

**当前错误代码：**
```python
ref_price = min(max_price_20d, max_price_end)
end_zone_width = (max_price_end - min_price_end) / ref_price
```

**问题说明：**
当末端区间不在20天高点时，`ref_price` 取 `max_price_20d`（更大值），导致分母被放大，宽度被低估，**扩张中的股票会被错误放行**。

**修正为：**
```python
ref_price = max_price_end  # 统一用末端高点作为分母
end_zone_width = (max_price_end - min_price_end) / ref_price
```

**效果：** 无论末端在什么位置，分母始终是末端自身高点，保证宽度计算的物理意义一致。

---

## 修改二：高位收敛判断基准统一

**问题定位：** `convergence_position_check` 函数，约第534-545行

**当前错误代码：**
```python
# 用 60天高点 判断 20天收敛区间的高位
convergence_high_in_range = convergence_high / max_price_60d
if convergence_high_in_range > 0.95:
    return False  # 高位收敛 → 拒绝
```

**问题说明：**
低位判断用20天范围，高位判断用60天范围，两者基准不一致。一个在20天中低位收敛的股票（如20天高低100-103），在60天高低90-110的背景下，103/110=93.6%——会被误判为高位收敛而拒绝。

**修正为：**
```python
# 统一用 20天范围 判断高位
convergence_high_in_range = convergence_high / max_price_20d
if convergence_high_in_range > 0.95:
    return False  # 高位收敛 → 拒绝
```

**效果：** 高低位判断都用20天范围，阈值基准一致。

---

## 修改三：MA250对新股不可用时改为 skip

**问题定位：** `above_or_recently_crossed_ma250` 函数，约第260-270行

**当前问题：** 腾讯API只给320天，股票刚好够260天时MA250只有约60个数据点，`rolling(250).mean()` 全是NaN → 函数返回False → 二踩分支错误拒绝该股票。

**修正方向：**
在函数开头加数据充足性检查，如果MA250数据不足（非NaN数量 < 200），直接返回 `None`（表示"不适用，跳过"）而非 `False`。

伪代码：
```python
def above_or_recently_crossed_ma250(df, ...):
    ma250 = df['close'].rolling(window=MA_WINDOW).mean()
    valid_ma250_count = ma250.dropna().count()

    # MA250数据不足 → 不适用，跳过检查
    if valid_ma250_count < 200:
        return None  # 而不是 False

    # ... 以下原有逻辑不变 ...
```

调用处（二踩过滤链）：
```python
ma_ok = above_or_recently_crossed_ma250(history_df)
if ma_ok is False:  # 只有明确返回False才拒绝
    return False
# None 和 True 都通过
```

**效果：** MA250数据不足的股票不会因此被错误过滤。

---

## 修改四（可选）：System Prompt 止损数值对齐

**目标文件：** `/Users/kennytseng/stock_ai/autoresearch/rules/screener_system_prompt.txt`

**问题：** 第152行写 `-2.5%`，但实际代码硬止损是 `-2%`

**修正：** 将 `-2.5%` 改为 `-2%`

---

## 注意事项

1. **只改逻辑，不改阈值**。本次只修复计算基准/分母错误，不调整6%、0.995等阈值。
2. **修改一处重新跑一次测试**，不要一次性改完再测。
3. 修改后运行 `layer1_filter.py` 单元测试（如有）或手动验证：`python -c "from layer1_filter import convergence_prefilter, convergence_position_check; print('OK')"`
4. System Prompt 文件修改后同步到 `/Users/kennytseng/WorkBuddy/20260404161853 2/rules/screener_system_prompt.txt`（如有对应文件）
