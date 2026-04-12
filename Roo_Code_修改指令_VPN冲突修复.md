Task: Fix VPN Conflict — Tencent Data Source Bypass for Layer1 & Layer2

Problem: User has VPN enabled. All Tencent K-line data fetch requests (Layer1 & Layer2) are getting Connection reset by peer. Only Tencent API needs to bypass VPN; OpenAI API should keep using the VPN proxy.

Files to modify:

layer1_filter.py
layer2_gpt_screener.py

---

## Modification 1: `layer1_filter.py`

After the import block (e.g., after `import os` and `import urllib.request`), add this block **at the very top of the file** (before any function definitions):

```python
# ============================================================
# VPN FIX: Tencent data source must bypass proxy
# ============================================================
NO_PROXY_LIST = "ifzq.gtimg.cn,stock.gtimg.cn,qt.gtimg.cn,qq.com,gtimg.cn"
os.environ["NO_PROXY"] = NO_PROXY_LIST
os.environ["no_proxy"] = NO_PROXY_LIST
# Force urllib to bypass system proxy for Tencent requests
import urllib.request
_proxy_opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({})
)
urllib.request.install_opener(_proxy_opener)
# ============================================================
```

> **Note:** Only add `import os` and `import urllib.request` if they don't already exist in the file.

---

## Modification 2: `layer2_gpt_screener.py`

Find the `fetch_daily_history()` function (or any function that fetches Tencent K-line data via `urlopen`). At the **very start** of that function, add:

```python
# Force bypass proxy for Tencent data source
if "ifzq.gtimg.cn" not in os.environ.get("NO_PROXY", ""):
    _no_proxy = "ifzq.gtimg.cn,stock.gtimg.cn,qt.gtimg.cn,qq.com,gtimg.cn"
    os.environ["NO_PROXY"] = _no_proxy
    os.environ["no_proxy"] = _no_proxy
    import urllib.request
    _proxy_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    urllib.request.install_opener(_proxy_opener)
```

> **Important:** Leave the OpenAI API call **unchanged** — it should keep using the VPN proxy via the `$HTTPS_PROXY` environment variable.

---

## Verification Steps

### Step 1: Quick connectivity test (VPN ON)

```bash
cd ~/stock_ai/autoresearch
uv run python -c "
import os
os.environ['NO_PROXY'] = 'ifzq.gtimg.cn,stock.gtimg.cn,qt.gtimg.cn,qq.com,gtimg.cn'
import urllib.request
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
urllib.request.install_opener(opener)
url = 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param=000858.day,qfq,240&qfq=1&_=1'
result = opener.open(url).read()
print('OK, bytes received:', len(result))
print(result[:200])
"
```

Expected output:
```
OK, bytes received: 1234
b'kline_dayqfq={"code":0,"data":...
```

If you see `OK, bytes received: ...` with K-line data, the fix works.

### Step 2: Full pipeline run

```bash
uv run python layer1_filter.py
uv run python layer2_gpt_screener.py
```

---

