from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import datetime
import os

doc = Document()

for section in doc.sections:
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2.5)


def set_shading(para, fill_hex):
    pPr = para._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    pPr.append(shd)


def h1(doc, text):
    h = doc.add_heading(text, level=1)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x1B, 0x4F, 0x72)
    return h


def h2(doc, text):
    h = doc.add_heading(text, level=2)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x21, 0x61, 0x8A)
    return h


def h3(doc, text):
    h = doc.add_heading(text, level=3)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x2E, 0x86, 0xC1)
    return h


def p(doc, text, bold=False, size=10.5, color=None):
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    return para


def code(doc, text):
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Cm(0.5)
    run = para.add_run(text)
    run.font.name = 'Courier New'
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x17, 0x20, 0x2A)
    set_shading(para, 'EEEEEE')
    return para


def note(doc, text, kind='info'):
    fills = {
        'info': 'D6EAF8',
        'warn': 'FEF9E7',
        'danger': 'FDEDEC',
        'green': 'EAFAF1'
    }
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.size = Pt(10)
    set_shading(para, fills.get(kind, 'D6EAF8'))
    return para


def bullet(doc, items):
    for item in items:
        para = doc.add_paragraph(style='List Bullet')
        run = para.add_run(item)
        run.font.size = Pt(10.5)


def numbered(doc, items):
    for item in items:
        para = doc.add_paragraph(style='List Number')
        run = para.add_run(item)
        run.font.size = Pt(10.5)


def sep(doc):
    doc.add_paragraph()


# ===================== COVER =====================
title_para = doc.add_paragraph()
title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title_para.add_run('A股纯K线选股 AI 训练完整操作手册')
run.font.size = Pt(22)
run.font.bold = True
run.font.color.rgb = RGBColor(0x1B, 0x4F, 0x72)

sub_para = doc.add_paragraph()
sub_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
run2 = sub_para.add_run(
    '基于 Karpathy AutoResearch + Claude Code + Mac Mini M4\n专为个人A股交易者定制 | 零基础可操作')
run2.font.size = Pt(12)
run2.font.color.rgb = RGBColor(0x55, 0x6B, 0x82)

sep(doc)
note(doc,
     '📌 阅读说明：灰底代码框为终端命令，请原样复制；蓝底为提示；黄底为注意事项；红底为严格禁止；绿底为核心原则。手册分为七大阶段，请按顺序执行。',
     'info')
sep(doc)

# ===================== OVERVIEW =====================
h1(doc, '总览：整体架构与工作流程')
p(doc,
  '本手册将帮助你在 Mac Mini M4（16GB 内存）上，从零搭建「每日自动A股选股系统」，由四层构成：',
  size=11)
sep(doc)
p(doc, '【第一层】数据层：AKShare 免费获取全市场A股真实日K历史数据', bold=True)
p(doc, '【第二层】规则层：你的纯K线图形战法，转化为 Python 可执行的选股规则', bold=True)
p(doc, '【第三层】进化层：Claude Code + AutoResearch 每晚自动回测→发现漏洞→微调规则→沉淀', bold=True)
p(doc, '【第四层】输出层：每天收盘后扫描全市场，输出「今日候选股票清单」，你手动决策买入', bold=True)
sep(doc)
note(
    doc,
    '🎯 核心铁律（全程不得违反）：\n'
    '① 纯K线图形逻辑是唯一主干，永不替换\n'
    '② 优化只做补漏，不重做逻辑\n'
    '③ 禁止引入外来指标（MACD/RSI/KDJ等），禁止将图形战法转为数值量化\n'
    '④ 每次优化只微调细节，禁止大改\n'
    '⑤ 所有结论用「K线图形语言」说明，禁止黑盒输出\n'
    '⑥ 训练/验证严格分集，防止过拟合——历史好看但实盘失效的规则一律废弃',
    'green')

doc.add_page_break()

# ===================== PHASE 0 =====================
h1(doc, '阶段零：理解 AutoResearch 是什么（必读，约15分钟）')
p(doc,
  'Karpathy AutoResearch（github.com/karpathy/autoresearch）是2026年3月由前特斯拉/OpenAI研究员 Andrej Karpathy 开源的项目，一周内获得 35,000+ GitHub Stars。其核心思想极简：',
  size=11)
sep(doc)
p(doc,
  '「让 AI 代理（Claude Code）自动修改训练代码 → 跑实验 → 看结果 → 决定保不保留 → 循环往复」')
sep(doc)
p(doc, '本手册将其移植到你的A股选股研究：')
bullet(doc, [
    '原版：AI 改 train.py → 训练5分钟 → 看 val_loss → 决定保留/回滚 → 循环',
    '你的版本：AI 改 screener_rules.py → 运行回测 → 看 win_rate → 决定保留/回滚 → 循环',
    'Claude Code 扮演「研究助手」，你扮演「战法守护者」',
    '每晚自动跑，早上看报告，满意就保留，不满意就回滚',
])
sep(doc)
note(
    doc,
    '⚠️ AutoResearch 原版需要 NVIDIA GPU。Mac M4 使用社区 fork 版（autoresearch-macos），'
    '已适配 Apple Silicon MPS，无需外接显卡。即使 fork 版无法运行，只用 Claude Code '
    '手动驱动迭代流程，效果完全等价。',
    'warn')

doc.add_page_break()

# ===================== PHASE 1 =====================
h1(doc, '阶段一：Mac 环境搭建（约 60~90 分钟）')
note(doc,
     '📋 本阶段目标：在 Mac Mini 上安装所有必要工具。完成后请对照 1.9 检查清单逐项确认再进入阶段二。',
     'info')
sep(doc)

h2(doc, '1.1 安装 Homebrew（Mac 软件包管理器）')
p(doc, '① 按 Command+空格，搜索 Terminal（终端），回车打开。')
p(doc, '② 粘贴以下命令并回车（约5分钟，需联网）：')
code(doc,
     '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
     )
p(doc, '③ 安装完成后，终端会提示你运行2行命令将 Homebrew 加入 PATH，原样复制执行即可。')
p(doc, '④ 验证：')
code(doc, 'brew --version')
note(doc, '✅ 看到类似 Homebrew 4.x.x 即成功', 'green')
sep(doc)

h2(doc, '1.2 安装 Python 3.11')
code(doc, 'brew install python@3.11\npython3.11 --version')
note(doc, '✅ 看到 Python 3.11.x 即成功', 'green')
sep(doc)

h2(doc, '1.3 安装 uv（AutoResearch 官方要求的包管理器，比 pip 快10倍）')
code(doc, 'curl -LsSf https://astral.sh/uv/install.sh | sh')
p(doc, '安装完成后关掉终端重新打开，验证：')
code(doc, 'uv --version')
note(doc, '✅ 看到 uv 0.x.x 即成功', 'green')
sep(doc)

h2(doc, '1.4 安装 Git（版本控制）')
code(doc, 'brew install git\ngit --version')
sep(doc)

h2(doc, '1.5 安装 VS Code（代码编辑器）')
bullet(doc, [
    '访问 https://code.visualstudio.com/ 下载 Mac 版（选 Apple Silicon / arm64 版）',
    '将 VS Code 拖入 Applications 文件夹',
    '打开 VS Code → 按 Command+Shift+P → 搜索「Shell Command: Install code command in PATH」→ 点击安装',
    '验证：在终端运行 code --version',
])
p(doc, '安装以下 VS Code 插件（左侧扩展图标搜索）：', bold=True)
bullet(doc, [
    'Python（微软官方）',
    'Jupyter（运行 .ipynb 笔记本）',
    'GitLens（可视化 Git 历史）',
    'Chinese (Simplified) Language Pack（中文界面，可选）',
])
sep(doc)

h2(doc, '1.6 安装 Claude Code（终端 AI 编程助手——本系统的大脑）')
p(doc, '① 安装 Node.js：')
code(doc, 'brew install node\nnode --version')
p(doc, '② 安装 Claude Code：')
code(doc, 'npm install -g @anthropic-ai/claude-code')
p(doc, '③ 验证并登录（需要 Claude Pro 订阅，月费约 $20）：')
code(doc, 'claude --version\nclaude login')
p(doc, '④ 执行 claude login 后，浏览器会自动弹出登录页，用你的 Anthropic 账户授权即可。')
note(
    doc,
    '💡 费用说明：Claude Pro 订阅 $20/月，包含 Claude Code 使用权。'
    '这是本套系统唯一的付费项目，其他工具全部免费。',
    'info')
sep(doc)

h2(doc, '1.7 创建项目目录结构')
code(doc,
     'mkdir -p ~/stock_ai/data/kline\n'
     'mkdir -p ~/stock_ai/rules\n'
     'mkdir -p ~/stock_ai/backtest\n'
     'mkdir -p ~/stock_ai/results\n'
     'mkdir -p ~/stock_ai/teaching/05_example_trades\n'
     'mkdir -p ~/stock_ai/teaching/images\n'
     'mkdir -p ~/stock_ai/logs\n'
     'cd ~/stock_ai\n'
     'git init')
sep(doc)

h2(doc, '1.8 安装 Python 数据科学核心库')
code(doc,
     'pip3.11 install akshare pandas numpy matplotlib mplfinance ta-lib-bin '
     'backtesting scikit-learn jupyter ipykernel openpyxl xlrd '
     'python-docx tqdm rich schedule')
note(
    doc,
    '⚠️ ta-lib-bin 是 Mac ARM 原生预编译版，无需额外编译。如安装失败，改用：\n'
    'brew install ta-lib && pip3.11 install TA-Lib',
    'warn')
sep(doc)

h2(doc, '1.9 下载 AutoResearch macOS 适配版')
code(doc, 'cd ~/stock_ai\n'
     'git clone https://github.com/miolini/autoresearch-macos.git autoresearch\n'
     'cd autoresearch\n'
     'uv sync\n'
     'uv run prepare.py\n'
     'uv run train.py')
note(doc, '✅ 看到训练开始打印 loss 数值即成功。Ctrl+C 可中断测试。', 'green')
sep(doc)

h2(doc, '1.10 阶段一完成检查清单')
p(doc, '运行以下命令，全部通过才进入阶段二：', bold=True)
code(doc, 'brew --version          # Homebrew\n'
     'python3.11 --version   # Python 3.11\n'
     'uv --version           # uv 包管理器\n'
     'git --version          # Git\n'
     'code --version         # VS Code\n'
     'claude --version       # Claude Code\n'
     'python3.11 -c "import akshare, pandas, numpy, matplotlib; print(\'ALL OK\')"')

doc.add_page_break()

# ===================== PHASE 2 =====================
h1(doc, '阶段二：上传你的战法知识库（约 2~4 小时）')
note(doc,
     '📋 本阶段目标：把你的纯K线战法，转化成 AI 可理解的「知识库文件」。这是整个系统的灵魂，越详细越好。',
     'info')
sep(doc)

h2(doc, '2.1 知识库文件夹结构')
code(doc, '~/stock_ai/teaching/\n'
     '├── 01_core_rules.md          # 核心K线图形规则（文字描述，最重要）\n'
     '├── 02_buy_conditions.md      # 买入触发条件\n'
     '├── 03_stop_loss_profit.md    # 止盈止损规则\n'
     '├── 04_blacklist_patterns.md  # 黑名单形态（必亏形态强制过滤）\n'
     '├── 05_example_trades/        # 历史交易案例（胜/败各若干）\n'
     '│   ├── win_001.md\n'
     '│   ├── win_002.md\n'
     '│   └── loss_001.md\n'
     '└── images/                   # K线图截图（用于辅助说明）')
sep(doc)

h2(doc, '2.2 核心规则文件模板（01_core_rules.md）')
p(doc, '在 VS Code 中打开 ~/stock_ai/teaching/ 文件夹，新建 01_core_rules.md，按以下模板填写：')
code(doc, '# My Pure Candlestick Trading System - Core Rules\n\n'
     '## System Philosophy\n'
     'This system selects stocks based ONLY on daily candlestick chart patterns.\n'
     'No technical indicators (MACD, RSI, KDJ, Bollinger Bands, etc.) are used.\n'
     'All decisions come from visual price structure, trend shape, and candle formation.\n\n'
     '## Pattern 1: Converging Pattern (收敛形态)\n'
     '### Visual Description\n'
     '- Price makes lower highs AND higher lows over 5-15 trading days\n'
     '- The trading range narrows, forming a triangle or wedge shape on the chart\n'
     '- Volume typically decreases (dries up) during the converging phase\n\n'
     '### Bullish Criteria\n'
     '- At least 3 touches on upper boundary and 3 touches on lower boundary\n'
     '- Each successive high is lower than the previous; each successive low is higher\n'
     '- Total convergence duration: 5-20 trading days preferred\n\n'
     '### Invalidation\n'
     '- Price breaks below the lowest low of the converging range\n'
     '- A single candle body exceeds the full prior range\n\n'
     '## Pattern 2: Pullback After Breakout (突破后回踩)\n'
     '### Visual Description\n'
     '[请填写你对这个形态的描述...]\n\n'
     '## Pattern 3: [你的其他形态]\n'
     '[继续添加...]')
note(
    doc,
    '💡 越详细越好——把你盯盘时脑子里的每一个判断标准都写出来。'
    'AI 读的是你的文字，写得越精确，规则转化越准确。如果有不确定的描述，'
    '也写进去，后续让 Claude Code 帮你澄清。',
    'info')
sep(doc)

h2(doc, '2.3 买入条件文件（02_buy_conditions.md）')
code(doc, '# Buy Entry Trigger Conditions\n\n'
     '## General Entry Rule\n'
     'I do NOT buy immediately when a pattern is detected.\n'
     'I wait for a specific trigger candle the NEXT trading day.\n\n'
     '## Trigger Condition 1: Volume Breakout\n'
     '- The stock breaks above the pattern boundary with volume > 1.5x the prior 5-day average\n'
     '- The breakout candle closes in the upper 30% of its range (not a shooting star)\n\n'
     '## Trigger Condition 2: Opening Strength\n'
     '- Stock opens flat or slightly up (within +2%) on the next day after pattern\n'
     '- In the first 30 minutes, it moves up and holds above the breakout level\n\n'
     '## Do NOT Enter When:\n'
     '- The stock gaps up more than 5% at open (already extended)\n'
     '- The entry candle is a doji or has a very long upper wick\n'
     '[继续填写你的买入规则...]')
sep(doc)

h2(doc, '2.4 黑名单形态文件（04_blacklist_patterns.md）')
code(doc, '# Blacklist Patterns - Automatic Disqualification\n\n'
     '## BL-001: Three Consecutive Large Red Candles (连续三根大阴线)\n'
     '- Description: 3 or more consecutive red candles with large bodies (>3% each)\n'
     '- Why it fails: Strong selling pressure, downtrend continuation risk\n'
     '- Filter rule: If last 3 candles are all red AND each body > 3%, EXCLUDE\n\n'
     '## BL-002: Gap-Down After Extended Run (高位跳空低开)\n'
     '- Description: Stock gaps down >2% after gaining >30% in prior 20 days\n'
     '- Why it fails: Distribution phase, institutional exit\n'
     '- Filter rule: gap_down > 2% AND prior_20d_gain > 30% → EXCLUDE\n\n'
     '## BL-003: [你总结的必亏形态]\n'
     '[把你所有的亏损经验整理成形态描述...]')
sep(doc)

h2(doc, '2.5 历史案例文件模板（win_001.md）')
code(doc, '# Trade Case: WIN-001\n'
     '## Stock: 600XXX | Date In: 2025-03-15 | Date Out: 2025-03-22\n'
     '## Result: +8.5% WIN\n\n'
     '## Why I Selected This Stock\n'
     'The stock formed a 12-day converging pattern after a prior uptrend.\n'
     'Upper boundary was tested 4 times with decreasing selling pressure each time.\n'
     'Lower boundary showed strong support — long lower wicks with small bodies.\n'
     'Volume dried up to 60% below 20-day average during convergence.\n\n'
     '## Entry Trigger\n'
     'On entry day, price broke above the upper boundary with 1.5x volume surge.\n'
     'Bought within the first 30 minutes after breakout was confirmed.\n\n'
     '## Exit\n'
     'Took profit at +8.5% on Day 7. Hit my prior resistance target.')
note(doc, '📌 建议准备至少 20 个历史案例（胜负各半）。案例越多，AI 学习越精准。', 'warn')
sep(doc)

h2(doc, '2.6 让 Claude Code 学习你的战法并确认理解')
p(doc, '① 在终端进入项目目录，启动 Claude Code：')
code(doc, 'cd ~/stock_ai\nclaude')
p(doc, '② 输入以下英文提示词（直接复制粘贴到 Claude Code 界面）：')
code(doc, 'Please read all files in ./teaching/ directory carefully.\n'
     'This is my personal pure-candlestick stock selection system for A-shares (China mainland).\n\n'
     'After reading, please:\n'
     '1. Summarize my core patterns in your own words\n'
     '2. Identify any ambiguities or gaps in my rules that need clarification\n'
     '3. List patterns you understood clearly vs. those needing more detail\n'
     '4. Do NOT suggest adding any technical indicators (no MACD, RSI, etc.)\n'
     '5. Do NOT suggest converting the system to numerical scoring\n\n'
     'Start with: "I have read your trading system. Here is my understanding..."')
note(
    doc,
    '💡 Claude Code 会列出它理解的内容，以及需要你补充说明的地方。'
    '根据反馈继续完善 teaching 文件，直到 Claude Code 能准确复述你的全部战法为止。',
    'info')

doc.add_page_break()

# ===================== PHASE 3 =====================
h1(doc, '阶段三：获取A股历史数据（约 1 小时 + 隔夜下载）')
note(doc,
     '📋 本阶段目标：用免费的 AKShare 下载全市场A股历史日K数据，建立本地数据库。',
     'info')
sep(doc)

h2(doc, '3.1 认识 AKShare')
bullet(doc, [
    '官网：https://akshare.akfamily.xyz/',
    '完全免费，无需注册，无需 API Token',
    '覆盖全部A股/港股日K线数据（支持后复权）',
    '数据来源：东方财富、新浪财经等正规渠道',
    '在 Mac M4 Apple Silicon 上运行稳定',
])
sep(doc)

h2(doc, '3.2 全量数据下载脚本（download_data.py）')
p(doc, '在 VS Code 中新建 ~/stock_ai/download_data.py，写入以下代码：')
code(doc, '# download_data.py  —  下载全A股历史日K数据\nimport akshare as ak\nimport pandas as pd\nimport os, time\nfrom datetime import datetime\n\nDATA_DIR = os.path.expanduser("~/stock_ai/data/kline")\nos.makedirs(DATA_DIR, exist_ok=True)\n\nSTART_DATE = "20200101"\nEND_DATE   = datetime.now().strftime("%Y%m%d")\n\nprint("Fetching A-share stock list...")\nstock_list = ak.stock_info_a_code_name()\nprint(f"Total stocks: {len(stock_list)}")\n\nfor idx, row in stock_list.iterrows():\n    code = row["code"]\n    save_path = os.path.join(DATA_DIR, f"{code}.csv")\n    if os.path.exists(save_path):\n        continue\n    try:\n        df = ak.stock_zh_a_hist(\n            symbol=code, period="daily",\n            start_date=START_DATE, end_date=END_DATE,\n            adjust="hfq"   # 后复权，推荐\n        )\n        df.to_csv(save_path, index=False)\n        print(f"[{idx+1}/{len(stock_list)}] Saved {code}")\n        time.sleep(0.2)\n    except Exception as e:\n        print(f"Failed {code}: {e}")\n\nprint("Download complete!")')
p(doc, '运行（建议睡前运行，首次需 3~5 小时）：')
code(doc, 'cd ~/stock_ai\npython3.11 download_data.py')
sep(doc)

h2(doc, '3.3 每日增量更新脚本（update_daily.py）')
code(doc, '# update_daily.py  —  每天收盘后运行，增量更新\nimport akshare as ak\nimport pandas as pd\nimport os, time\nfrom datetime import datetime, timedelta\n\nDATA_DIR = os.path.expanduser("~/stock_ai/data/kline")\nTODAY    = datetime.now().strftime("%Y%m%d")\nSTART    = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")\n\nstock_list = ak.stock_info_a_code_name()\nprint(f"Updating {len(stock_list)} stocks...")\n\nupdated = failed = 0\nfor idx, row in stock_list.iterrows():\n    code = row["code"]\n    save_path = os.path.join(DATA_DIR, f"{code}.csv")\n    try:\n        df_new = ak.stock_zh_a_hist(\n            symbol=code, period="daily",\n            start_date=START, end_date=TODAY, adjust="hfq"\n        )\n        if os.path.exists(save_path):\n            df_old = pd.read_csv(save_path)\n            df = pd.concat([df_old, df_new]).drop_duplicates(\n                subset=["日期"]).sort_values("日期")\n        else:\n            df = df_new\n        df.to_csv(save_path, index=False)\n        updated += 1\n        time.sleep(0.15)\n    except Exception:\n        failed += 1\n\nprint(f"Done. Updated: {updated}, Failed: {failed}")')
sep(doc)

h2(doc, '3.4 验证数据质量')
code(doc, '# 在终端运行此命令快速检查\npython3.11 -c "\nimport pandas as pd, os, glob, random\nD = os.path.expanduser(\'~/stock_ai/data/kline\')\nfiles = glob.glob(f\'{D}/*.csv\')\nprint(f\'Total CSV files: {len(files)}\')\nfor f in random.sample(files, 5):\n    df = pd.read_csv(f)\n    print(f\'{os.path.basename(f)}: {len(df)} rows, latest: {df[chr(26085)+chr(26399)].max()}\')\n"')
note(doc,
     '✅ 正常输出：Total CSV files: 5000+，每个文件有 1000+ 行，最新日期为最近交易日',
     'green')

doc.add_page_break()

# ===================== PHASE 4 =====================
h1(doc, '阶段四：战法转化为可执行代码 + 首次回测（核心阶段，约 1~2 天）')
note(doc,
     '📋 本阶段目标：由 Claude Code 将你的K线战法翻译成 Python 选股代码，并进行首次历史回测。这是整个系统最重要的阶段。',
     'info')
sep(doc)

h2(doc, '4.1 创建 AutoResearch 指令核心文件（program.md）')
p(doc, '新建 ~/stock_ai/program.md，这个文件控制 AI 的全部行为边界：')
code(doc, '# Stock Selection Research Program\n\n'
     '## Mission\n'
     'You are a stock selection research assistant for A-share (China mainland) stocks.\n'
     'Your mission: improve the win rate of my pure-candlestick screening system.\n\n'
     '## CORE CONSTRAINTS (NEVER VIOLATE)\n'
     '- System is based ONLY on daily candlestick chart patterns\n'
     '- Do NOT add any technical indicators (MACD, RSI, KDJ, Bollinger Bands, etc.)\n'
     '- Do NOT convert visual patterns to numerical scoring systems\n'
     '- Do NOT replace core pattern logic — only add minor supplementary filters\n'
     '- Every rule must be explainable in plain candlestick chart language\n'
     '- Allowed minor supplements ONLY: basic volume ratio comparison,\n'
     '  price range limits, same-direction trend reinforcement\n\n'
     '## Files to Read First\n'
     '- ./teaching/01_core_rules.md        -- Trading system rules\n'
     '- ./teaching/02_buy_conditions.md    -- Entry trigger conditions\n'
     '- ./teaching/03_stop_loss_profit.md  -- Exit rules\n'
     '- ./teaching/04_blacklist_patterns.md -- Patterns to avoid\n'
     '- ./teaching/05_example_trades/      -- Historical trade examples\n\n'
     '## Code You May Modify\n'
     '- ./rules/screener_rules.py          -- Pattern detection (YOU MAY MODIFY)\n'
     '- ./backtest/run_backtest.py         -- Backtesting engine (READ ONLY)\n'
     '- ./results/latest_report.json       -- Latest results (READ to understand performance)\n\n'
     '## Experiment Protocol\n'
     '1. Read program.md and all teaching files\n'
     '2. Read current screener_rules.py\n'
     '3. Read latest_report.json for current win rate and failure modes\n'
     '4. Propose ONE small targeted improvement\n'
     '5. Show the proposed change to user BEFORE applying\n'
     '6. After approval, apply the change to screener_rules.py\n'
     '7. Run: python3.11 backtest/run_backtest.py\n'
     '8. Report new vs old win rate; recommend keep or revert\n\n'
     '## Success Metric\n'
     'Win rate = (profitable_trades / total_trades) * 100\n'
     'Current baseline: ~60%\n'
     'Target: Gradually reach 65-70% without over-fitting\n'
     'Over-fit rule: If train_win_rate > val_win_rate + 5%, REVERT immediately')
sep(doc)

h2(doc, '4.2 生成初始选股规则代码（screener_rules.py）')
p(doc, '① 在终端启动 Claude Code：')
code(doc, 'cd ~/stock_ai\nclaude')
p(doc, '② 输入以下提示词让 Claude Code 生成第一版规则代码：')
code(doc, 'Please read program.md and all files in ./teaching/ directory.\n\n'
     'Then create ./rules/screener_rules.py with the following structure:\n\n'
     '1. detect_patterns(df): takes OHLCV DataFrame, returns dict of detected patterns (True/False)\n'
     '2. is_blacklisted(df): returns True if any blacklist pattern found\n'
     '3. calculate_confidence(df): returns "high"/"medium"/"low" in chart language\n'
     '4. screen_stock(symbol, df): main function that:\n'
     '   - Runs all detections and blacklist checks\n'
     '   - Returns: {"selected": bool, "patterns": [...],\n'
     '               "reason": "chart-language explanation", "confidence": str}\n\n'
     'IMPORTANT:\n'
     '- Use ONLY candlestick price data (open, high, low, close, volume)\n'
     '- No technical indicators whatsoever\n'
     '- Comment every rule with chart-language explanation\n'
     '- Use the exact patterns from my teaching files')
note(doc,
     '💡 Claude Code 会自动读取你所有 teaching 文件，生成 screener_rules.py。约需5~10分钟，耐心等待。',
     'info')
sep(doc)

h2(doc, '4.3 回测引擎脚本（backtest/run_backtest.py）')
p(doc, '新建 ~/stock_ai/backtest/run_backtest.py，写入以下代码：')
code(doc, '# run_backtest.py  —  全市场历史回测引擎\nimport sys, os, json, glob\nsys.path.insert(0, os.path.expanduser("~/stock_ai"))\nimport pandas as pd\nfrom rules.screener_rules import screen_stock\nfrom datetime import datetime\n\nDATA_DIR   = os.path.expanduser("~/stock_ai/data/kline")\nRESULT_DIR = os.path.expanduser("~/stock_ai/results")\nos.makedirs(RESULT_DIR, exist_ok=True)\n\n# ---- 参数（修改这里调整回测范围）----\nTRAIN_START = "2022-01-01"\nTRAIN_END   = "2024-06-30"   # 训练集\nVAL_START   = "2024-07-01"\nVAL_END     = "2025-12-31"   # 验证集（严防过拟合）\nHOLD_DAYS   = 5\nSTOP_LOSS   = -0.05\nTAKE_PROFIT = 0.08\nLOOKBACK    = 60\n\ndef simulate_trade(df_future):\n    if len(df_future) < 2: return None, 0\n    entry = df_future.iloc[0]["收盘"]\n    for i in range(1, min(HOLD_DAYS+1, len(df_future))):\n        ret = (df_future.iloc[i]["收盘"] - entry) / entry\n        if ret <= STOP_LOSS: return "stop_loss", ret\n        if ret >= TAKE_PROFIT: return "take_profit", ret\n    final = (df_future.iloc[min(HOLD_DAYS, len(df_future)-1)]["收盘"] - entry) / entry\n    return "time_exit", final\n\ndef run_period(start, end):\n    files = glob.glob(f"{DATA_DIR}/*.csv")\n    results = []\n    for f in files:\n        try:\n            df = pd.read_csv(f, parse_dates=["日期"]).sort_values("日期").reset_index(drop=True)\n            mask = (df["日期"] >= start) & (df["日期"] <= end)\n            for sig_date in df[mask]["日期"].unique():\n                idx = df[df["日期"] == sig_date].index[0]\n                if idx < LOOKBACK: continue\n                window = df.iloc[idx-LOOKBACK:idx+1]\n                res = screen_stock(os.path.basename(f).replace(".csv",""), window)\n                if res["selected"]:\n                    outcome, ret = simulate_trade(df.iloc[idx:idx+HOLD_DAYS+1])\n                    if outcome:\n                        results.append({\n                            "date": str(sig_date)[:10],\n                            "symbol": os.path.basename(f).replace(".csv",""),\n                            "confidence": res.get("confidence","medium"),\n                            "reason": res.get("reason",""),\n                            "outcome": outcome,\n                            "return_pct": round(ret*100, 2)\n                        })\n        except: continue\n    return results\n\nprint("Running TRAIN backtest...")\ntrain = run_period(TRAIN_START, TRAIN_END)\nprint(f"Train trades: {len(train)}")\nprint("Running VALIDATION backtest...")\nval = run_period(VAL_START, VAL_END)\nprint(f"Val trades: {len(val)}")\n\ndef stats(results, label):\n    if not results: return {"label":label,"total_trades":0,"win_rate":0}\n    import numpy as np\n    df = pd.DataFrame(results)\n    w = df[df["return_pct"] > 0]\n    l = df[df["return_pct"] <= 0]\n    return {\n        "label": label,\n        "total_trades": len(df),\n        "win_rate": round(len(w)/len(df)*100, 2),\n        "avg_win_pct": round(w["return_pct"].mean(), 2) if len(w) else 0,\n        "avg_loss_pct": round(l["return_pct"].mean(), 2) if len(l) else 0,\n        "generated_at": datetime.now().isoformat()\n    }\n\ntr, vr = stats(train,"train"), stats(val,"val")\nreport = {\n    "train": tr, "validation": vr,\n    "overfit_warning": tr.get("win_rate",0) - vr.get("win_rate",0) > 5,\n    "trade_log": train + val\n}\nwith open(f"{RESULT_DIR}/latest_report.json","w") as f:\n    json.dump(report, f, ensure_ascii=False, indent=2)\nprint(f"Train WR: {tr[\'win_rate\']}% | Val WR: {vr[\'win_rate\']}% | Overfit: {report[\'overfit_warning\']}")\nprint(f"Report saved: {RESULT_DIR}/latest_report.json")')
p(doc, '运行首次回测：')
code(doc, 'cd ~/stock_ai\npython3.11 backtest/run_backtest.py')
note(doc,
     '⚠️ 首次全市场回测在 M4 Mac Mini 上约需 30~90 分钟。建议先用 100 只股票小样本测试代码无误后再跑全量。',
     'warn')

doc.add_page_break()

# ===================== PHASE 5 =====================
h1(doc, '阶段五：启动 AutoResearch 自动迭代优化（每周 1~2 次）')
note(doc,
     '📋 本阶段目标：将 AutoResearch 的「AI自动跑实验」机制接入选股系统，让 Claude Code 自动分析亏损场景、微调规则。',
     'info')
sep(doc)

h2(doc, '5.1 工作原理')
bullet(doc, [
    '原版 AutoResearch：AI 改 train.py → 训练5分钟 → 看 val_loss → 保留/回滚',
    '你的版本：AI 改 screener_rules.py → 运行回测 → 看 win_rate → 保留/回滚',
    '人工审核点：每次 AI 修改前你必须审核一遍，确认符合纯K线逻辑再接受',
    'program.md 文件永远控制 AI 的行为边界，确保永不越界',
])
sep(doc)

h2(doc, '5.2 每次优化的标准提示词（保存备用）')
code(doc, '# ——— 每次优化时，粘贴此提示词到 Claude Code ———\n\n'
     'Please read program.md, then start a new optimization experiment.\n\n'
     'Step 1: Read ./results/latest_report.json\n'
     'Step 2: Identify the top 2-3 LOSING scenarios (patterns selected but resulted in losses)\n'
     'Step 3: Propose ONE small targeted fix:\n'
     '  - Express the fix in candlestick chart language only\n'
     '  - No technical indicators allowed\n'
     '  - Must be a small patch (< 20 lines of code added/changed)\n'
     '  - Addresses ONE specific identified failure mode\n'
     'Step 4: Show me the proposed change BEFORE making it\n'
     'Step 5: After I approve, apply the change to ./rules/screener_rules.py\n'
     'Step 6: Run: python3.11 backtest/run_backtest.py\n'
     'Step 7: Report new win rates vs previous; recommend keep or revert\n\n'
     'REMEMBER: Never make large changes. Never add indicators.\n'
     'Explain everything in chart language.')
sep(doc)

h2(doc, '5.3 审核 AI 修改方案的自检清单（每次必做）')
p(doc, '每次 Claude Code 提出修改前，逐项回答：', bold=True)
numbered(doc, [
    '这个修改是否仍然是「看图」逻辑？（是→通过，否→拒绝）',
    '是否引入了任何计算公式或指标名称？（有→直接拒绝）',
    '这次只改了一处细节吗？（超过3处→要求拆分分批提交）',
    '改的是补漏（排除亏损场景）还是重构逻辑？（重构→拒绝）',
    '它是否用K线图形语言解释了为什么会亏损？（没解释→要求补充）',
])
note(
    doc,
    '🚫 任何一条不满足，回复 Claude Code：\n'
    '"Reject this change. [说明原因]. Propose a simpler chart-language fix instead."',
    'danger')
sep(doc)

h2(doc, '5.4 版本控制——每次优化后立即执行')
code(doc, 'cd ~/stock_ai\ngit add rules/screener_rules.py results/latest_report.json\ngit commit -m "Opt: [简述修改] | Train: XX% | Val: XX%"')
p(doc, '如需回滚到上一版本：')
code(doc, 'git log --oneline                                          # 查看历史\ngit checkout <commit_hash> -- rules/screener_rules.py  # 回滚指定文件')
sep(doc)

h2(doc, '5.5 黑名单自动入库提示词')
code(doc, '# ——— 黑名单分析提示词 ———\n\n'
     'Please analyze ./results/latest_report.json.\n'
     'Find all trades where outcome == "stop_loss".\n\n'
     'For each group of similar losers:\n'
     '1. Describe what the candlestick chart likely looked like at entry\n'
     '2. Identify common VISUAL patterns across multiple losers\n'
     '3. Suggest a blacklist rule in chart language\n'
     '4. Do NOT use indicator values — describe only candle shapes and positions\n'
     '5. Add validated blacklist rules to ./teaching/04_blacklist_patterns.md')

doc.add_page_break()

# ===================== PHASE 6 =====================
h1(doc, '阶段六：每日自动选股工作流（日常使用）')
note(doc,
     '📋 本阶段目标：建立每天收盘后的标准作业流程，AI 自动扫描全市场输出候选清单，你只需看清单做决策。',
     'info')
sep(doc)

h2(doc, '6.1 每日选股脚本（daily_screen.py）')
code(doc, '# daily_screen.py  —  每日收盘后运行，扫描全市场输出候选\nimport sys, os, glob, json\nsys.path.insert(0, os.path.expanduser("~/stock_ai"))\nimport pandas as pd\nfrom rules.screener_rules import screen_stock\nfrom datetime import datetime\n\nDATA_DIR   = os.path.expanduser("~/stock_ai/data/kline")\nRESULT_DIR = os.path.expanduser("~/stock_ai/results")\nLOOKBACK   = 60\n\nprint(f"Daily screen: {datetime.now().strftime(\'%Y-%m-%d %H:%M\')}")\ncandidates = []\nfor f in glob.glob(f"{DATA_DIR}/*.csv"):\n    try:\n        df = pd.read_csv(f, parse_dates=["日期"]).sort_values("日期").reset_index(drop=True)\n        if len(df) < LOOKBACK: continue\n        window = df.tail(LOOKBACK + 1)\n        sym = os.path.basename(f).replace(".csv","")\n        res = screen_stock(sym, window)\n        if res["selected"]:\n            latest = df.iloc[-1]\n            candidates.append({\n                "symbol": sym,\n                "date": str(latest["日期"])[:10],\n                "close": latest["收盘"],\n                "patterns": res.get("patterns",[]),\n                "confidence": res.get("confidence","medium"),\n                "reason": res.get("reason","")\n            })\n    except: continue\n\ncandidates.sort(key=lambda x: ["high","medium","low"].index(x["confidence"]))\ntoday = datetime.now().strftime("%Y%m%d")\npath  = f"{RESULT_DIR}/daily_{today}.json"\nwith open(path,"w",encoding="utf-8") as f:\n    json.dump(candidates, f, ensure_ascii=False, indent=2)\n\nprint(f"\\n===== CANDIDATES {today} =====")\nprint(f"Total: {len(candidates)}")\nfor c in candidates:\n    print(f"  [{c[\'confidence\'].upper():6}] {c[\'symbol\']} | {c[\'reason\'][:70]}")\nprint(f"\\nReport: {path}")')
p(doc, '每天运行两步：')
code(doc, 'cd ~/stock_ai\npython3.11 update_daily.py     # 第一步：更新今日数据\npython3.11 daily_screen.py     # 第二步：运行选股')
sep(doc)

h2(doc, '6.2 候选股票人话解读提示词')
code(doc, '# ——— 每日候选股解读提示词 ———\n'
     '# 将 [DATE] 替换为今天日期，如 20260404\n\n'
     'Please read ./results/daily_[DATE].json\n\n'
     'For each candidate stock, provide a brief explanation in plain chart language:\n'
     '1. What specific pattern was detected?\n'
     '2. Where is the key support/resistance level?\n'
     '3. What is the ideal entry trigger condition tomorrow?\n'
     '4. What would invalidate this setup?\n'
     '5. Confidence level and visual reason\n\n'
     'Format: A brief trading brief I can read in 2 minutes.\n'
     'No indicators. Chart and candle language only.\n'
     'Max 10 candidates. HIGH confidence first.')
sep(doc)

h2(doc, '6.3 日常标准作业流程 SOP')
p(doc, '每个交易日的完整操作：', bold=True)
numbered(doc, [
    '【15:30 收盘后】运行：python3.11 update_daily.py（更新今日数据，约5分钟）',
    '【15:40】运行：python3.11 daily_screen.py（全市场扫描，约5~15分钟）',
    '【16:00】打开终端运行 claude，粘贴「每日候选股解读提示词」，获取人话解读',
    '【16:15】阅读候选清单，用自己的眼睛对照原始K线图确认，决定哪些进入观察名单',
    '【次日开盘】严密监控候选股，满足买入条件时手动下单，套用止盈止损规则',
    '【每周一次，晚上】运行「每次优化提示词」，让 Claude Code 分析本周亏损并微调规则',
    '【每次优化后】立刻 git commit 保存版本快照',
    '【每月一次】重新运行完整回测，检查 train vs val 胜率，确认无过拟合',
])

doc.add_page_break()

# ===================== PHASE 7 =====================
h1(doc, '阶段七：高级技巧与进阶指引')

h2(doc, '7.1 工具与资源清单')
p(doc, '免费工具：', bold=True)
bullet(doc, [
    'AKShare（A股数据）：https://akshare.akfamily.xyz/',
    'Baostock（备用数据，注册免费）：http://baostock.com',
    'mplfinance（K线图绘制）：pip install mplfinance',
    'Backtesting.py（策略回测框架）：https://kernc.github.io/backtesting.py/',
    'TA-Lib（K线形态名称参考用，不用于指标计算）：pip install ta-lib-bin',
    'Jupyter Notebook（数据可视化分析）：pip install jupyter',
    'AutoResearch macOS：https://github.com/miolini/autoresearch-macos',
    'AutoResearch MLX 版：https://github.com/trevin-creator/autoresearch-mlsx',
    'VS Code：https://code.visualstudio.com/',
    'Git：brew install git',
])
p(doc, '唯一付费工具：', bold=True)
bullet(doc, [
    'Claude Pro 订阅（$20/月）：https://claude.ai  →  包含 Claude Code 使用权',
])
sep(doc)

h2(doc, '7.2 K线图可视化代码（帮助理解 AI 识别结果）')
code(doc, 'import mplfinance as mpf\nimport pandas as pd\n\ndf = pd.read_csv(\n    "~/stock_ai/data/kline/600519.csv",\n    parse_dates=["日期"]\n).set_index("日期").rename(columns={\n    "开盘":"Open","收盘":"Close","最高":"High","最低":"Low","成交量":"Volume"\n})\n\nmpf.plot(\n    df.tail(60), type="candle", volume=True,\n    title="最近60日K线",\n    savefig="~/stock_ai/teaching/images/sample.png"\n)\nprint("Chart saved")')
sep(doc)

h2(doc, '7.3 买入条件精化提示词')
code(doc, '# ——— 买入条件精化提示词 ———\n\n'
     'Pattern [PATTERN_NAME] shows inconsistent win rate.\n'
     'Please analyze ./results/latest_report.json:\n\n'
     '1. Find all trades involving [PATTERN_NAME]\n'
     '2. Compare winning trades vs losing trades visually (candle shapes only)\n'
     '3. Identify what was visually DIFFERENT between winners and losers\n'
     '4. Propose a more precise entry trigger:\n'
     '   "I will only enter when I see [specific candle visual description]"\n'
     '5. No indicators. Pure chart description.')
sep(doc)

h2(doc, '7.4 常见问题解决')
p(doc, 'Q: AKShare 报错「请求过于频繁」？', bold=True)
p(doc, 'A: 把 update_daily.py 中的 time.sleep(0.15) 改为 time.sleep(0.5)。')
sep(doc)
p(doc, 'Q: Claude Code 提出的修改包含了技术指标（如 MACD、RSI）？', bold=True)
p(doc, 'A: 直接回复：「Reject. You added [indicator name] which violates core constraints. '
   'Remove it and propose a pure price/candle-based alternative.」')
sep(doc)
p(doc, 'Q: 回测胜率比实盘差很多（过拟合）？', bold=True)
p(doc,
  'A: 检查 train win rate vs val win rate。如相差 >5%，用 git revert 回滚到上一个均衡版本，并告诉 Claude Code 本次改动导致过拟合，要求简化。'
  )
sep(doc)
p(doc, 'Q: Mac M4 运行回测较慢？', bold=True)
p(doc, 'A: 在 run_backtest.py 中加入 Python 多进程（multiprocessing.Pool），并行处理多只股票，速度可提升 4~8 倍。')
sep(doc)
p(doc, 'Q: screener_rules.py 越来越复杂，逻辑混乱？', bold=True)
code(doc, '# 输入此提示词让 Claude Code 整理代码（不改逻辑）\n'
     'Please refactor screener_rules.py for readability ONLY.\n'
     'No logic changes allowed. Add comments explaining each rule in chart language.')

doc.add_page_break()

# ===================== APPENDIX =====================
h1(doc, '附录：完整英文提示词速查表')
note(doc,
     '以下是本手册所有英文提示词的汇总。建议保存为文本片段（Mac 可用 Raycast 或 Alfred），方便日常快速调用。',
     'info')
sep(doc)

h2(doc, 'A. 战法学习提示词（首次使用）')
code(doc, 'Please read all files in ./teaching/ directory carefully.\n'
     'This is my personal pure-candlestick stock selection system for A-shares.\n'
     'Summarize my core patterns, identify ambiguities, and list what you\n'
     'understood clearly vs. what needs more detail.\n'
     'Do NOT suggest adding indicators or numerical scoring systems.')

h2(doc, 'B. 每次优化提示词（每周1~2次）')
code(doc, 'Please read program.md, then start a new optimization experiment.\n'
     'Read ./results/latest_report.json, identify top losing scenarios,\n'
     'propose ONE small targeted fix in screener_rules.py.\n'
     'Fix must be: chart-language only, <20 lines, no indicators, one failure mode.\n'
     'Show me the change BEFORE applying. Explain in candlestick language.')

h2(doc, 'C. 每日候选股解读提示词')
code(doc, 'Please read ./results/daily_[DATE].json.\n'
     'For each candidate, explain in plain chart language:\n'
     '1. Pattern detected  2. Key support level\n'
     '3. Ideal entry trigger tomorrow  4. What invalidates the setup\n'
     '5. Confidence and visual reason\n'
     'Max 10 stocks. High confidence first. No indicators.')

h2(doc, 'D. 黑名单分析提示词')
code(doc, 'Analyze ./results/latest_report.json, find all stop_loss trades.\n'
     'Describe what the candlestick chart looked like at entry for each loser.\n'
     'Identify common visual patterns across multiple losers.\n'
     'Suggest blacklist rules in chart language.\n'
     'Add validated rules to ./teaching/04_blacklist_patterns.md')

h2(doc, 'E. 买入条件精化提示词')
code(doc, 'Pattern [NAME] shows inconsistent win rate.\n'
     'Analyze trade log, compare winners vs losers visually (candle shapes only).\n'
     'Propose precise entry trigger:\n'
     '"I will only enter when I see [specific candle visual description]"')

h2(doc, 'F. 拒绝修改提示词')
code(doc, 'Reject this change.\n'
     '[说明原因，如：You added RSI which violates core constraints.]\n'
     'Remove it and propose a pure price/candle-based alternative\n'
     'that achieves the same filtering goal using only visual chart patterns.')

h2(doc, 'G. 防过拟合回滚提示词')
code(doc, 'The last change caused over-fitting:\n'
     'Train win rate increased but Val win rate decreased.\n'
     'Please revert the last change to screener_rules.py.\n'
     'Explain why the change over-fitted and propose a simpler, more general version.')

sep(doc)
sep(doc)
p(doc, '— 文档结束 —', bold=True)
p(doc,
  f'生成时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M")}  |  基于 Karpathy AutoResearch + Claude Code + AKShare + Mac M4',
  size=9)
p(doc, '⚠️ 本手册仅供个人学习研究使用，不构成任何投资建议。股市有风险，投资需谨慎。', size=9)

out_path = r'C:/Users/Kenny/WorkBuddy/20260404161853/A股选股AI训练操作手册.docx'
doc.save(out_path)
print(f'Saved: {out_path}')
