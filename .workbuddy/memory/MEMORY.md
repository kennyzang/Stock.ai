# MEMORY.md — 长期记忆

## 用户信息
- 设备：Mac Mini M4，16GB 内存
- 背景：A股个人投资者，有一套纯K线图形选股战法（收敛、回踩等），当前胜率约60%
- 目标：用 AI 迭代优化选股胜率，但核心纯K线逻辑永远不可替换

## 核心项目：A股选股AI系统（三周期战法）

### 战法核心结构（2026-04-05 读取原始文档后确认）
- **大周期**：周线不向下（排除下跌趋势）
- **中周期**：收敛图（三高两低、末端宽度<8%、低点抬高、缩量）或 二踩图（一涨放量+均线修复、二踩缩量、时间对称）
- **小周期**：分时图切入点（平盘以上+3分钟涨速>1%+放量），已由量化软件自动执行
- **量化软件已做**：买入触发、动态止盈、硬性止损（**-2%**）、时间止损（**4天**，持仓≥4天有浮盈则卖或14:55强制卖）→ AI 不需要干预
  - 硬止损精确值：`stop_loss = -0.02`（以实际代码1030-1.txt第33行为准），触碰立即全仓卖出
  - 动态止盈：`get_profit_ratio_B()` 函数，按浮盈区间回撤比例递减（0~2%→100%, 2~4%→75%, 4~10%→50%...）
  - 时间止损：持仓**4天**（max_hold_days=4），有浮盈则卖；或14:55强制卖
  - WIN定义（Plan A简化版）：选入→隔天触发买入条件→买入后第一天不碰-2%止损线
  - WIN定义（完整版）：触发买入后不触发任何止损，盈利出场；N/A = 买入条件未触发，不计入胜率
  - WIN定义：触发买入后不触发任何止损，盈利出场；N/A = 买入条件未触发，不计入胜率
- **AI 只做**：选股（每日从5000支过滤到10-20支候选给人工最终确认）

### 架构 v4.0：三层选股架构（2026-04-05 设计）
- **第一层**：Python + AKShare 硬条件筛选（免费，5000→50-100支）
  - 周线趋势、收敛末端宽度<8%、低点抬高、成交量缩量、流动性>3000万、价格在年线上
- **第二层**：DeepSeek V3 图形语言审核（¥0.5/天，50-100→10-20支 select/watch）
  - K线数据转文字描述 → DeepSeek V3 用英文 system prompt 按三周期规则打分
- **第三层**：AutoResearch 规则迭代（每周一次，用实际盈亏反馈优化 rules/ 文件）
- **蓝图文档**：已保存到 brain artifact 目录（三周期AI选股系统_三层架构蓝图.md）
- **月成本**：约 ¥30/月（Layer 1 免费，Layer 2 约¥15，Layer 3 约¥15）
  - 切换到 DeepSeek V3 后：Layer 2 ¥10/月（比 GPT-4o 方案便宜 80%）

### 技术栈
- Python 3.11 + AKShare（数据）
- GPT-4o（第二层审核）+ GPT-4.1（第三层规则迭代）
- Roo Code（代码生成）
- AutoResearch 框架（规则迭代驱动）
- 数据源：**方案B变体（已确认2026-04-11）**
  - **Layer1 筛选**：保持腾讯日线不变（前复权 qfq，ifzq.gtimg.cn）
  - **Plan A 回测**：新浪5分钟K线（money.finance.sina.com.cn，scale=5，不复权）
    - 实测最大5001条≈104天（3.5个月），足够回测
    - 新浪60分钟线可拉3519条≈880天（3.5年）— 未来可作为Layer1备用数据源
    - 新浪不支持复权，但对收敛/回踩形态判断（相对比例）影响极小
  - 网易财经(quotes.money.163.com)：当前502挂了，即使恢复也仅日线无分钟数据
  - BaoStock：免费但查询太慢（QPS≈20），暂不采用
  - 腾讯/新浪均对VPN敏感，需 NO_PROXY + ProxyHandler({}) 强制直连
  - **内部一致性验证通过**：新浪60min衍生日线 vs 5min衍生日线 = 差异0.000%（20组对比全完美）
- Layer2 模型：DeepSeek V3（2026-04-05 切换）
  - 主方案：DeepSeek V3 via https://api.deepseek.com（国内直连，不需要VPN）
  - 价格：¥1/百万tokens，约¥0.5/天，比GPT-4o便宜90%
  - 环境变量：`DEEPSEEK_API_KEY`
  - 备选：Kimi K2.5（¥2/百万tokens）
  - **⚠️ screener_system_prompt.txt 不得被 AutoResearch 整体覆盖**（Day 3、Day 6两次被覆盖）
    - **已修复**（2026-04-12）：直接修改 `layer3_analyst.py` 的 `write_rules()` 函数，对该文件强制追加模式（`"a"`），其他文件保持覆盖模式（`"w"`）
    - 用户反馈（NO_BUY不重要、恒源煤电应选入、泸州老窖不应选入）已写入 `user_feedback.md`

### 全市场覆盖修复（2026-04-12）
- **全量运行**：orchestrator 已去掉 `--limit 500`，改为全量5502支股票
- **三市场分层采样**（`_stratified_sample()`）：szse(52%) + sse(40%) + bjse(8%)
- **北京所纳入**：`classify_market()` 新增92xxxx识别（之前只认8xxxx漏掉305支北交所）
- **腾讯API代码转换**：92xxxx → bj前缀
- **Orchestrator P1+P2修复**：推荐过滤(reject跳过) + 标签标准化(intercept/monitor→BUY, hold→HOLD)
  - **流动性阈值 = 3000万**：成交额计算 = 收盘价 × 成交量(手) × 100（已修正，腾讯volume单位是手）

### 核心铁律
- 禁止引入 MACD/RSI/KDJ 等指标
- 禁止将图形战法改为纯数值量化（高低点形态判断仍需人眼最终确认）
- 每次只微调一处规则细节，严防过拟合
- teaching/ 目录保留中文原文不翻译
- **ST/\*ST 股票必须排除**（Layer2 system prompt 已加入强制排除规则）
- **买入条件未触发（N/A）的记录不计入胜率**
- **急跌后不降低标准凑数**：选不出票时空仓等待才是正确操作；急跌反弹期可放宽周线要求但收敛标准要更严（末端<4%而非8%）；持续阴跌无条件空仓
- **get_trading_days() 已加6天安全偏移**：确保选股日期有完整后续5分钟数据，避免 DATA_ERROR
- **Layer1 四项修复已实施（2026-04-11）**：
  1. 向下收敛 HARD 排除（`_is_downward_convergence()`）：高点下移+低点下移→拒绝
  2. 低位/高位收敛 SOFT→HARD（`convergence_position_check`），但 breakout 豁免
  3. 第三高突破形态（`_has_breakout_pattern()`）：最新高≥前高97%→突破形态，末端宽可达12%
  4. 二踩分支去掉 `daily_trend_not_declining`（二踩本身是回调，日线向下正常）
- **用户明确**：二踩≥一高是硬指标不改；选不出票时空仓等待；急跌反弹期收敛标准要更严而非更松
- **convergence 分支去掉 daily_trend_not_declining**（2026-04-11）：收敛图经常在深跌后形成（联环药业03-26、三生国健03-29），日线趋势不好但形态有效；pullback分支保留strict模式
- **convergence_position_check 改用 core_price**（最近5-10天收盘价中位数）：20天窗口含起涨低点导致误判"低位收敛"（节能风电 case）
- **convergence_prefilter 改用 close_range**（收盘价范围）替代 end_zone_width（high/low范围）：三档阈值 5%/8%/12%，解决暴跌日拉宽high/low range问题
- **二踩图节点检测改用 zigzag 算法**（2026-04-11）：`_find_pullback_nodes()` 用5%阈值zigzag找一高/一踩/二高/二踩，替代固定窗口`rally_zone[-35:-10]`/`recent_dip_zone[-10:]`。修复中润光学case（二涨17天导致固定窗口包含二涨中途回调）
- **pullback_volume_check 替代 volume_declining**（pullback分支）：对比二踩/二涨区间成交量（排除二高当天），阈值1.0（宽松）
- **Manual Picks 通过率 8/8**（2026-04-11）：中润光学✅pullback, 法尔胜✅convergence, 恒源煤电LOSS不通过=正确

### 操作规范（每次对话都要检查）
- **给 Roo Code 的指令文件** → 写完后同步复制到 `/Users/kennytseng/stock_ai/autoresearch/` 目录下（Roo Code 只读这个目录，不会自动看到工作区其他位置的文件）
- 对 Roo Code / GPT system prompt / rules 目录 → **英文**（实测 Roo Code 用 Qwen3.6 时内部推理仍是英文，中文指令会被翻译两次，造成技术术语损耗）
- teaching/ 战法材料 → 保留中文原文（中文术语如"三高两低"直接夹在英文注释里，确保精度）
- 与 WorkBuddy 讨论 → 中文
- 选股日志 → 中文即可

## 用户偏好
- 与 AI 沟通用英文，用户阅读的指引文字用中文
- 最少成本原则
- 希望手册非常详细，包括所有命令、提示词、工具链接
- 查看了 YouTube 频道 @OnchainAIGarage（约60个视频，主题：OpenClaw/Hermes Agent/AutoResearch/本地LLM）
