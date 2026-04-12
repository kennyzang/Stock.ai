# Roo Code 指令：全量切换到 DeepSeek V3（国内模型）

> **Date:** 2026-04-05
> **Goal:** Replace OpenAI with DeepSeek V3 across all Layer2 code. Remove all VPN dependencies. Full domestic China deployment.
> **Estimated Cost:** ~¥0.5/day (DeepSeek V3) vs ~$1.5/day (GPT-4o)

---


## 修改文件清单

| 文件 | 操作 |
|---|---|
| `layer2_gpt_screener.py` | 重命名 + 内容修改 |
| `rules/layer2_system_prompt.txt` | 内容修改 |
| `rules/layer2_user_prompt_template.txt` | 内容修改 |

---

## Modification 1: Rename `layer2_gpt_screener.py`

Rename the file (in your IDE or with shell):

```bash
mv layer2_gpt_screener.py layer2_screener.py
```

Or in the IDE: right-click → Rename → `layer2_screener.py`

---

## Modification 2: Update `layer2_screener.py`

Find and replace the following sections:

### 2a. Update the file header / constants (around top of file)

**Find:**
```python
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
MODEL_NAME = "gpt-4o"
```

**Replace with:**
```python
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_NAME = "deepseek-chat"
```

### 2b. Update the API call function

**Find the entire `call_openai` function (around line 196), including its signature:**

```python
def call_openai(system_prompt: str, user_prompt: str) -> dict[str, object]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    request_body = {
        "model": MODEL_NAME,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }
    request = Request(
        OPENAI_URL,
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    content = payload["choices"][0]["message"]["content"]
    return json.loads(content)
```

**Replace with:**

```python
def call_model(system_prompt: str, user_prompt: str) -> dict[str, object]:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set. Get your key at https://platform.deepseek.com")

    request_body = {
        "model": MODEL_NAME,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }
    request = Request(
        DEEPSEEK_URL,
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    content = payload["choices"][0]["message"]["content"]
    return json.loads(content)
```

**Important:** Also update the call site where `call_openai` is invoked (around line 276 in the main loop):

**Find:**
```python
response_json = call_openai(system_prompt, user_prompt)
```

**Replace with:**
```python
response_json = call_model(system_prompt, user_prompt)
```

### 2c. Remove VPN bypass code

Since DeepSeek is domestic and needs no VPN, remove the VPN bypass code from `fetch_daily_history`. The Tencent data source still needs bypass, but the environment variables approach is fine to keep.

Actually, **keep the Tencent VPN bypass code as-is** — it's still needed for Tencent K-line data. Only remove/change the parts that reference `OPENAI_API_KEY`.

### 2d. Update output filename date (optional)

Update the output path to today's date if needed:
```python
OUTPUT_PATH = Path("layer2_results_20260405.csv")
LAYER1_INPUT = Path("layer1_candidates_20260405.csv")
```

---

## Modification 3: Update `rules/layer2_system_prompt.txt`

The system prompt content stays the same (it describes the K-line pattern rules). No text changes needed.

---

## Modification 4: Update `rules/layer2_user_prompt_template.txt`

No text changes needed for the template file itself.

---

## Modification 5: Rename rules directory files (optional but recommended)

```bash
cd ~/stock_ai/autoresearch/rules
mv layer2_system_prompt.txt screener_system_prompt.txt
mv layer2_user_prompt_template.txt screener_user_prompt_template.txt
```

And update the references in `layer2_screener.py`:

**Find:**
```python
SYSTEM_PROMPT_PATH = Path("rules/layer2_system_prompt.txt")
USER_PROMPT_TEMPLATE_PATH = Path("rules/layer2_user_prompt_template.txt")
```

**Replace with:**
```python
SYSTEM_PROMPT_PATH = Path("rules/screener_system_prompt.txt")
USER_PROMPT_TEMPLATE_PATH = Path("rules/screener_user_prompt_template.txt")
```

---

## Step 6: Get DeepSeek API Key

1. Visit https://platform.deepseek.com
2. Sign up (手机号/邮箱)
3. Go to API Keys → Create new key
4. Copy the key

Set the environment variable:

```bash
# Add to ~/.zshrc or ~/.bashrc for persistence:
echo 'export DEEPSEEK_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc

# Verify:
echo $DEEPSEEK_API_KEY
```

---

## Step 7: Remove VPN bypass for OpenAI (cleanup)

Since we're no longer using OpenAI, clean up any VPN-related environment variables that were set for OpenAI:

```bash
unset HTTPS_PROXY  # Only if it was set for OpenAI
unset OPENAI_API_KEY  # Optional, can keep this
```

Or edit your shell profile (`~/.zshrc`) to remove OpenAI VPN lines if any were added.

---

