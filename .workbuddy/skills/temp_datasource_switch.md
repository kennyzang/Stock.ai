# 数据源切换指令

layer1_filter.py 当前使用 AKShare 的默认数据源（东方财富 eastmoney），
在当前网络环境下无法访问，需要切换到腾讯数据源。

## 任务

修改 layer1_filter.py 的以下两个函数，使用腾讯数据源替代 eastmoney：

### 1. fetch_stock_universe()

当前：使用 ak.stock_zh_a_spot_em()
改为：使用腾讯股票列表 API

腾讯接口（无需认证，直接访问）：
- 沪深A股完整列表：
  https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh000001,day,,,320,qfq
  （这个接口返回单支股票历史数据，但可以用这个先测试连通性）

更好的方式是直接用腾讯的股票列表接口：
- https://qt.gtimg.cn/q=s_sh000001,s_sh600519,s_sz399001
  （腾讯实时行情接口，可批量查询，用 "s_" 前缀）

或者用 AKShare 的另一个函数：
- ak.stock_info_a_code_name() 返回沪深全市场股票代码和名称

### 2. fetch_daily_history()

当前：使用 ak.stock_zh_a_hist() （东方财富接口）
改为：使用腾讯历史 K 线接口

腾讯日 K 接口：
- 单支股票：https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,320,qfq
- code 格式：sh600519（上证）、sz000001（深证）
- 返回 JSON，包含日 K 数据（日期、开、高、低、收、成交量）

## 具体修改要求

1. 修改 fetch_stock_universe()：
   - 使用 ak.stock_info_a_code_name() 获取全市场股票列表
   - 或直接调用腾讯 API 获取股票列表
   - 确保返回 stock_code, stock_name 两个字段

2. 修改 fetch_daily_history(symbol, name)：
   - 改为调用腾讯日 K 接口：https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,320,qfq
   - 解析返回的 JSON，提取 day 数组中的 [日期, 开, 收, 高, 低, 成交量] 数据
   - 返回 pandas DataFrame，列名为：date, open, close, high, low, volume
   - 注意处理上交所（sh）和深交所（sz）的代码前缀转换
   - 如果腾讯接口失败，fallback 到 ak.stock_zh_a_hist()

3. 保持其他所有筛选逻辑不变
4. 保持 --mode convergence/pulldown/all 参数不变
5. 保持输出 CSV 格式不变

## 验证要求

修改完成后，运行以下命令验证：
uv run python layer1_filter.py --mode convergence --limit 10

应该能成功输出约 10 支候选股，验证数据源切换成功。
