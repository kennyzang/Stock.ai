> **Goal:** Add 3-retry logic to Tencent K-line fetch to handle VPN network jitter

---

## Task

Modify `layer2_gpt_screener.py` — specifically the `fetch_daily_history()` function — to add automatic retry with exponential backoff when Tencent K-line data fetch fails.

**Current problem:** 8 out of 141 stocks fail with `Connection reset by peer` due to VPN routing instability. Adding retry logic will recover most of these failures.

---

## What to change

In `layer2_gpt_screener.py`, locate the `fetch_daily_history()` function (around line 61). Replace the section from line 72 through line 75 with the retry-wrapped version below.

**Find this section (lines 72-75):**

```python
    tencent_code = convert_to_tencent_code(stock_code)
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tencent_code},day,,,{KLINE_DAYS},qfq"
    with urlopen(url, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
```

**Replace it with:**

```python
    tencent_code = convert_to_tencent_code(stock_code)
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tencent_code},day,,,{KLINE_DAYS},qfq"

    # ── Retry logic: up to 3 attempts with backoff ──
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with _proxy_opener.open(url, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break  # success — exit retry loop
        except Exception as e:
            last_error = e
            if attempt < 2:
                time.sleep(1 + attempt)  # 1s, then 2s backoff
            else:
                raise last_error  # 3rd attempt failed — propagate error
    # ─────────────────────────────────────────────────
```

**Important:** Ensure `import time` is present at the top of the file. If it is not, add it to the import block. Also ensure `_proxy_opener` (the no-proxy opener built at line 69) is available — it should already exist since you added the VPN bypass code in the previous step.

---

## Verification

After the change, run:

```bash
cd ~/stock_ai/autoresearch
uv run python layer2_gpt_screener.py
```

Expected outcome:
- Previously failing 8 stocks should now succeed (or mostly succeed)
- Any remaining failures should be genuinely bad data (empty response, etc.), not `Connection reset`
- Total run time will increase by ~3-5 seconds per failed stock due to retry delays

---

## Alternative: Retry in `call_openai` too (optional)

If you also see intermittent OpenAI API failures during the run, the same retry pattern can be applied to `call_openai()` (line 276). Let me know if you want that added too.
