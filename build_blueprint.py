from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# ===== 页面设置 =====
section = doc.sections[0]
section.page_width = Inches(8.27)
section.page_height = Inches(11.69)
section.left_margin = Cm(2.5)
section.right_margin = Cm(2.5)
section.top_margin = Cm(2.5)
section.bottom_margin = Cm(2.5)

# ===== 辅助函数 =====
def set_font(run, name='微软雅黑', size=11, bold=False, color=None):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.element.rPr.rFonts.set(qn('w:eastAsia'), name)
    if color:
        run.font.color.rgb = RGBColor(*color)

def add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    sizes = {1: 18, 2: 14, 3: 12}
    colors_map = {1: (31, 73, 125), 2: (21, 96, 130), 3: (47, 117, 181)}
    set_font(run, size=sizes.get(level, 12), bold=True, color=colors_map.get(level, (0, 0, 0)))
    if level == 1:
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '6')
        bottom.set(qn('w:space'), '1')
        bottom.set(qn('w:color'), '1F497D')
        pBdr.append(bottom)
        pPr.append(pBdr)
    return p

def add_body(doc, text, indent=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    if indent:
        p.paragraph_format.left_indent = Cm(0.75)
    run = p.add_run(text)
    set_font(run, size=10.5)
    return p

def add_bullet(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.left_indent = Cm(0.5 * level)
    run = p.add_run('• ' + text)
    set_font(run, size=10.5)
    return p

def add_code_block(doc, text):
    for line in text.split('\n'):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.left_indent = Cm(0.5)
        run = p.add_run(line if line.strip() else ' ')
        run.font.name = 'Courier New'
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(30, 30, 30)
        rPr = run._r.get_or_add_rPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), 'F2F2F2')
        rPr.append(shd)

def add_note(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run('💡 ' + text)
    set_font(run, size=10, color=(102, 102, 102))

def add_table(doc, headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        run = hdr_cells[i].paragraphs[0].runs[0]
        set_font(run, size=10, bold=True, color=(255, 255, 255))
        tc = hdr_cells[i]._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), '1F497D')
        tcPr.append(shd)
    for ri, row in enumerate(rows):
        cells = table.rows[ri + 1].cells
        for i, val in enumerate(row):
            cells[i].text = val
            run = cells[i].paragraphs[0].runs[0]
            set_font(run, size=10)
            fill = 'EEF4FB' if ri % 2 == 0 else 'FFFFFF'
            tc = cells[i]._tc
            tcPr = tc.get_or_add_tcPr()
            shd = OxmlElement('w:shd')
            shd.set(qn('w:val'), 'clear')
            shd.set(qn('w:color'), 'auto')
            shd.set(qn('w:fill'), fill)
            tcPr.append(shd)
    doc.add_paragraph()

# ===== 封面 =====
doc.add_paragraph()
doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('三周期 AI 选股系统')
set_font(run, size=26, bold=True, color=(31, 73, 125))

p2 = doc.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
run2 = p2.add_run('三层架构蓝图  v1.0')
set_font(run2, size=16, color=(47, 117, 181))

doc.add_paragraph()
p3 = doc.add_paragraph()
p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
run3 = p3.add_run('基于「三周期技术分析」战法 × AutoResearch 框架')
set_font(run3, size=11, color=(128, 128, 128))

p4 = doc.add_paragraph()
p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
run4 = p4.add_run('2026-04-05')
set_font(run4, size=10, color=(160, 160, 160))

doc.add_page_break()

# ===== 核心目标 =====
add_heading(doc, '核心目标与铁律', 1)
add_bullet(doc, '目标：用 AI 将 5000 支股票过滤到每日 10 支以内高质量候选，提升选股胜率（目标 >65%）')
add_bullet(doc, '铁律一：不引入 MACD / RSI / KDJ 等任何标准技术指标')
add_bullet(doc, '铁律二：不将图形感知替换为纯数值量化，人工最终视觉确认不可省略')
add_bullet(doc, '铁律三：每次只微调一处规则细节，严防过拟合')
add_bullet(doc, '铁律四：teaching/ 目录的中文材料永远保留原文，不翻译')

# ===== 系统总览 =====
add_heading(doc, '系统总览', 1)
add_body(doc, '整套系统分三层，逐层过滤，各司其职：')
doc.add_paragraph()
add_code_block(doc, """全市场 ~5000 支股票
        │
        ▼
┌──────────────────────────────────────────┐
│  第一层：硬条件代码筛选器                   │  工具：Python + AKShare（免费）
│  输出：50～100 支候选票                    │  负责人：Roo Code 写代码
└──────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  第二层：GPT 图形语言审核                   │  工具：GPT-4o（约 $0.05/天）
│  输出：10～20 支精选票                     │  负责人：Python 脚本调用 API
└──────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  第三层：AutoResearch 规则迭代闭环          │  工具：AutoResearch + GPT-4.1
│  输出：持续优化的选股规则文件               │  负责人：每周跑一次
└──────────────────────────────────────────┘
        │
        ▼
   你的人眼最终确认（5～10 分钟）
        │
        ▼
   量化软件自动执行买入 / 止盈 / 止损""")
doc.add_paragraph()

# ===== 第一层 =====
add_heading(doc, '第一层：硬条件代码筛选器', 1)
add_body(doc, '职责：用纯数学条件，将 5000 支股票快速过滤到 50～100 支，剔除明显不符合三周期要求的票。')

add_heading(doc, '工具清单', 2)
add_table(doc,
    ['工具', '用途'],
    [
        ['Python 3.11', '主语言'],
        ['AKShare', '获取 A 股日 K、周 K 数据（免费）'],
        ['pandas', '数据计算与筛选'],
        ['Roo Code', '帮你生成这段代码'],
    ]
)

add_heading(doc, '筛选条件（来自三周期规则）', 2)

add_body(doc, '▌ 大周期（周线）')
add_bullet(doc, '近 13 周最低收盘价 > 前 13 周最低收盘价，OR 近 13 周最高价 ≥ 前 13 周最高价（排除周线向下）')

add_body(doc, '▌ 中周期 — 收敛图前置条件')
add_bullet(doc, '末端宽度：近 20 日（最高价 - 最低价）/ 最高价 < 8%')
add_bullet(doc, '低点抬高：近 5 日最低价 > 近 20 日最低价')
add_bullet(doc, '整体缩量：近 5 日均量 < 近 20 日均量')

add_body(doc, '▌ 中周期 — 二踩图前置条件')
add_bullet(doc, '近 60 日内存在至少 +10% 的上涨段（一涨认定）')
add_bullet(doc, '近 20 日存在明显回落段（二踩进行中）')
add_bullet(doc, '近 5 日均量 < 近 20 日均量 × 60%（回踩缩量）')

add_body(doc, '▌ 基础流动性')
add_bullet(doc, '近 20 日日均成交额 > 3000 万（防止流动性不足）')
add_bullet(doc, '股价在 250 日均线（年线）之上，或近 3 日刚突破年线')

add_heading(doc, '对 Roo Code 说的话（用英文）', 2)
add_note(doc, 'Roo Code 底层是英文训练的 LLM，英文指令生成代码质量更高、技术术语更精准。')
add_code_block(doc, """I need you to write a Python script called `layer1_filter.py`
for A-share stock screening.

Requirements:
- Use AKShare to fetch all A-share stock codes (ak.stock_zh_a_spot_em())
- For each stock, fetch daily K-line data (post-adjusted, last 60 trading days)
  using ak.stock_zh_a_hist()
- Apply the following filters, save to layer1_candidates_YYYYMMDD.csv

Filter conditions:
1. Weekly trend not declining: lowest close in last 13 weeks > lowest close
   in weeks 14-26. OR highest in last 13 weeks >= highest in weeks 14-26.
2. Convergence pre-filter:
   (max_price_20d - min_price_20d) / max_price_20d < 0.08
3. Low point rising: min_price_5d > min_price_20d
4. Volume declining: avg_volume_5d < avg_volume_20d * 0.8
5. Liquidity: avg_turnover_20d > 30,000,000 (CNY)
6. Price above or just crossed 250-day MA within last 3 days

Run filters in sequence, print how many stocks pass each step.
Add a --mode flag: convergence / pullback / all
Save output CSV: stock_code, stock_name, close_price, filter_type""")

add_heading(doc, '预期输出', 2)
add_code_block(doc, """layer1_candidates_20260405.csv
  stock_code | stock_name | close_price | filter_type
  000001     | 平安银行   | 12.30       | convergence
  300750     | 宁德时代   | 185.60      | pullback
  ...（约 50-100 行）""")

# ===== 第二层 =====
add_heading(doc, '第二层：GPT 图形语言审核', 1)
add_body(doc, '职责：对第一层候选票，用 K 线数据生成结构化描述，让 GPT 模拟你的「看图逻辑」给出评分和推荐。')

add_heading(doc, '工具清单', 2)
add_table(doc,
    ['工具', '用途'],
    [
        ['Python 脚本', 'K 线数据转文字描述 + 调用 OpenAI API'],
        ['GPT-4o', '图形语言审核，约 $0.05/天'],
        ['layer2_gpt_screener.py', 'Roo Code 帮你生成'],
    ]
)

add_heading(doc, '数据转文字示例（K 线数字 → GPT 可理解的摘要）', 2)
add_code_block(doc, """股票 000001（平安银行）近 30 日 K 线摘要：
- 周线方向：最近 13 周低点 10.1 > 前 13 周低点 9.8，呈上升趋势 ✓
- 高低点序列：高点 [12.8, 12.6, 12.5, 12.4]，低点 [11.2, 11.5, 11.8, 12.0]
- 末端收敛宽度：近 5 日区间 0.45 / 最高价 12.5 = 3.6%（< 8% ✓）
- 量能变化：近 5 日均量 4200 万，近 20 日均量 8100 万，量比 = 0.52（缩量 ✓）
- 均线排列：5日 12.2，10日 12.0，20日 11.8，60日 11.2（多头排列 ✓）
- 距年线：当前价 12.3，250 日均线 11.9，高出 3.4%""")

add_heading(doc, 'GPT System Prompt（英文，存入 rules/layer2_system_prompt.txt）', 2)
add_code_block(doc, """You are an expert A-share technical analyst specializing in the
"Three-Cycle" (三周期) trading system.

=== CONVERGENCE PATTERN (收敛图) CRITERIA ===
A valid convergence pattern requires ALL of the following:
1. At least 3 swing highs and 2 swing lows, alternating in orderly manner
2. Highs: flat, slightly rising, or slightly declining (NOT rapidly declining)
3. Lows: consistently rising overall
4. End-zone width: (highest - lowest) / highest < 8%, ideally < 5%
5. Volume: declining or low during the convergence zone
6. NOT already broken out (price still within convergence zone)
7. NOT a low-position convergence (large overhead supply pressure)

=== PULLBACK PATTERN (二踩图) CRITERIA ===
1. Clear first rally (一涨): at least +10%, expanding volume, MAs turning upward
2. First pullback (一踩): volume contraction to < 50% of rally volume
3. Second rally started (二涨): upward move with volume expansion
4. Second pullback in progress (二踩): volume contracting, not below first rally top
5. Time symmetry: each up/down wave roughly equal in duration

=== OUTPUT FORMAT (JSON) ===
{
  "stock_code": "000001",
  "pattern_type": "convergence" | "pullback" | "neither",
  "score": 0-10,
  "confidence": "high" | "medium" | "low",
  "key_positives": ["point1", "point2"],
  "key_negatives": ["point1", "point2"],
  "recommendation": "select" | "watch" | "skip",
  "reason": "一句话总结（中文）"
}""")

add_heading(doc, '对 Roo Code 说的话（用英文）', 2)
add_code_block(doc, """Write a Python script called `layer2_gpt_screener.py`:

1. Read input from `layer1_candidates_YYYYMMDD.csv`
2. For each stock, fetch 60-day daily K-line data using AKShare
3. Calculate metrics:
   - Swing highs and lows (local maxima/minima, window=3)
   - End-zone width % = (max_close_5d - min_close_5d) / max_close_5d
   - Volume ratio = avg_volume_5d / avg_volume_20d
   - MA values: 5, 10, 20, 60, 250 day
   - Distance to 250-day MA in %
4. Format metrics into structured text prompt
5. Call OpenAI API (model: gpt-4o) with system + user prompt
6. Parse JSON response
7. Save all results to `layer2_results_YYYYMMDD.csv`
8. Print summary: count of select / watch / skip
9. Add 1-second rate limiting between API calls
10. Error handling: if API fails, mark as "error" and continue""")

add_heading(doc, '预期输出', 2)
add_code_block(doc, """layer2_results_20260405.csv
  stock_code | stock_name  | pattern_type | score | recommendation | reason
  000001     | 平安银行    | convergence  | 7.5   | select  | 收敛末端3.6%，缩量明显，低点持续抬高
  300750     | 宁德时代    | pullback     | 8.0   | select  | 二踩缩量到位，时间比例对称
  ...（约 10-20 行）""")

# ===== 第三层 =====
add_heading(doc, '第三层：AutoResearch 规则迭代闭环', 1)
add_body(doc, '职责：每周把真实交易结果反馈给 GPT，分析「什么样的图赢了、什么样的图输了」，生成规则更新建议。')

add_heading(doc, '工具清单', 2)
add_table(doc,
    ['工具', '用途'],
    [
        ['AutoResearch 框架', '驱动整个闭环循环'],
        ['GPT-4.1（高推理）', '规则分析与更新建议生成'],
        ['Ollama 本地模型', '数据预处理等轻量任务（免费）'],
        ['你的交易日志 Excel', '反馈来源（手动填写盈亏）'],
    ]
)

add_heading(doc, '闭环流程', 2)
add_code_block(doc, """① 每日选股结果  →  daily_output/YYYYMMDD_selections.csv
        │
        ▼
② 量化软件完成交易  →  daily_output/YYYYMMDD_results.csv
   （包含：买入价、卖出价、盈亏%、持有天数、止损类型）
        │
        ▼
③ 每周日运行 layer3_rule_updater.py
   → 汇总过去 4 周选股结果
   → 分类：胜率高的图 vs 胜率低的图
   → 调用 GPT-4.1 分析规律
        │
        ▼
④ GPT 输出规则修改建议（JSON 格式，存入 rules/pending_updates/）
        │
        ▼
⑤ 你审核建议  →  确认后手动更新 rules/ 目录""")

add_heading(doc, '对 Roo Code 说的话（用英文）', 2)
add_code_block(doc, """Write a Python script called `layer3_rule_updater.py`:

1. Read all files: daily_output/*_selections.csv and *_results.csv
2. Merge by stock_code and date
3. Calculate win rate by pattern_type (convergence vs pullback)
4. Identify top 5 winning and top 5 losing trades by return %
5. Retrieve original GPT assessment from layer2 results for each trade
6. Build feedback prompt:
   - Winning trades: pattern_type, score, key_positives, actual_return
   - Losing trades: pattern_type, score, key_negatives, actual_return
   - Current rules (from rules/layer2_system_prompt.txt)
7. Call GPT-4.1 asking for specific rule changes
8. Save suggestion to rules/pending_updates_YYYYMMDD.txt
9. DO NOT auto-update rules - require manual confirmation""")

add_heading(doc, 'GPT 规则迭代约束 Prompt（英文，存入 rules/layer3_iteration_prompt.txt）', 2)
add_code_block(doc, """You are a trading rules optimizer for the Three-Cycle (三周期) system.

CRITICAL CONSTRAINTS (never violate):
- Never suggest MACD, RSI, KDJ, Bollinger Bands, or standard indicators
- Never convert visual pattern recognition into pure numeric thresholds
- Never make rules overly specific to recent conditions (overfitting)
- Only suggest ONE or TWO changes per iteration

OUTPUT FORMAT:
{
  "analysis_period": "YYYY-MM-DD to YYYY-MM-DD",
  "total_trades": N,
  "current_win_rate": "XX%",
  "convergence_win_rate": "XX%",
  "pullback_win_rate": "XX%",
  "key_finding": "one sentence",
  "suggested_changes": [{
    "type": "strengthen|relax|add|remove",
    "rule": "exact rule text",
    "reason": "data-backed reason",
    "expected_impact": "estimated win rate change"
  }],
  "next_experiment": "single variable to test next 4 weeks"
}""")

# ===== 语言策略 =====
add_heading(doc, '语言使用策略', 1)
add_body(doc, '按「对象」和「场景」分类，一张表总结全部：')
doc.add_paragraph()
add_table(doc,
    ['场景 / 对象', '语言', '原因'],
    [
        ['对 Roo Code / Cursor 写代码', '英文', '代码生成英文优先，技术术语精准，token 效率高'],
        ['rules/ 目录的 System Prompt', '英文', 'GPT 处理英文逻辑指令更精准，AND/OR/NOT 歧义少'],
        ['teaching/ 目录的战法材料', '保留中文原文', 'GPT 读中文原文理解更完整，语感词不可翻译'],
        ['选股日志 / 交易记录', '中文即可', '供自己查阅，无需翻译'],
        ['跟 WorkBuddy 讨论架构', '中文', 'WorkBuddy 中英文皆通，中文效率更高'],
        ['喂给 GPT 的战略分析问题', '建议英文', '英文能激活 GPT 更强的推理模式'],
    ]
)
add_note(doc, '最简单记法：Roo Code + GPT rules = 英文；你的材料 + 日常讨论 = 中文原文。')

# ===== 目录结构 =====
add_heading(doc, '项目目录结构', 1)
add_code_block(doc, """~/stock_ai/autoresearch/
├── layer1_filter.py               ← 第一层硬筛选
├── layer2_gpt_screener.py         ← 第二层 GPT 审核
├── layer3_rule_updater.py         ← 第三层规则迭代
├── run_daily.sh                   ← 每日运行（layer1 + layer2）
├── run_weekly.sh                  ← 每周运行（layer3）
│
├── rules/
│   ├── layer2_system_prompt.txt        ← GPT 图形审核规则（英文）
│   ├── layer2_user_prompt_template.txt ← User Prompt 模板（英文）
│   ├── layer3_iteration_prompt.txt     ← 规则迭代 Prompt（英文）
│   └── pending_updates/                ← 待审核的规则更新建议
│
├── teaching/                      ← 你的原始中文材料（保留原文）
│   ├── 三周期技术分析.pdf
│   ├── 策略总结-学习笔记.docx
│   ├── 图形示例.docx
│   └── 交易策略自动化执行v4.docx
│
├── daily_output/
│   ├── YYYYMMDD_layer1.csv        ← 第一层筛选结果
│   ├── YYYYMMDD_layer2.csv        ← 第二层 GPT 审核结果
│   └── YYYYMMDD_results.csv       ← 实际交易结果（手动填写）
│
├── data/                          ← AKShare 数据缓存
└── logs/                          ← 运行日志""")

# ===== 启动步骤 =====
add_heading(doc, '启动步骤（按序执行）', 1)

add_heading(doc, '步骤 1：把战法材料复制到 teaching/ 目录（5 分钟，自己做）', 2)
add_code_block(doc, """cp ~/Desktop/交易方法/*.pdf ~/stock_ai/autoresearch/teaching/
cp ~/Desktop/交易方法/*.docx ~/stock_ai/autoresearch/teaching/""")

add_heading(doc, '步骤 2：让 Roo Code 写 layer1_filter.py', 2)
add_body(doc, '把第一层「对 Roo Code 说的话」那段英文指令直接粘贴进 Roo Code，让它生成代码。')

add_heading(doc, '步骤 3：跑一次第一层，验证数据管道（完全免费）', 2)
add_code_block(doc, """cd ~/stock_ai/autoresearch
python3 layer1_filter.py --mode all""")
add_body(doc, '预期输出 50～150 支候选票为正常。先确认数据管道通畅，再进入第二层。')

add_heading(doc, '步骤 4：让 Roo Code 写 layer2_gpt_screener.py', 2)
add_body(doc, '把第二层「对 Roo Code 说的话」那段英文指令粘贴进 Roo Code。')

add_heading(doc, '步骤 5：第一次完整跑通整个流程', 2)
add_code_block(doc, """python3 layer1_filter.py --mode all
python3 layer2_gpt_screener.py""")
add_body(doc, '拿到候选股列表，人工看图确认，加入量化软件「待买入池」开始实盘。')

# ===== 成本 =====
add_heading(doc, '月度成本估算', 1)
add_table(doc,
    ['层级', '工具', '月费用'],
    [
        ['第一层', 'Python + AKShare', '免费'],
        ['第二层', 'GPT-4o（约100支/天 × 500 tokens）', '约 $1.5 / 月'],
        ['第三层', 'GPT-4.1（每周一次）', '约 $0.4 / 月'],
        ['合计', '—', '约 $2 / 月'],
    ]
)
add_note(doc, '第一层不调用 AI，第二层只用轻量 GPT-4o，是目前最低成本的可行方案。')

# ===== 页脚 =====
doc.add_paragraph()
p_footer = doc.add_paragraph()
p_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
run_f = p_footer.add_run('文档版本：v1.0  |  2026-04-05  |  基于三周期技术分析战法设计')
set_font(run_f, size=9, color=(160, 160, 160))

# ===== 保存 =====
output_path = r'C:/Users/Kenny/WorkBuddy/20260404161853/三周期AI选股系统_三层架构蓝图_v1.0.docx'
doc.save(output_path)
print('saved:', output_path)
