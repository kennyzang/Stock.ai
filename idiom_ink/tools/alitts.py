#!/usr/bin/env python3
"""Alibaba Cloud DashScope voices for Idiom Ink Shorts (TTS + ASR check).

Auth: in cloud sessions the environment's proxy injects `Authorization` for dashscope.aliyuncs.com,
so no key is handled here. (Elsewhere set DASHSCOPE_API_KEY and it is sent as a Bearer header.)

Fixed brand voices (FORMAT_SHORTS.md §5): TTS model qwen3-tts-flash, English narrator "Jennifer" (American English; Ethan had a Chinese accent),
Mandarin "Cherry"; ASR model qwen3-asr-flash (no biasing context).

Usage:
  alitts.py EPISODE_DIR/shorts.json --outdir DIR [--only ID,ID] [--retries 3]
      every line -> DIR/<line id>.wav (natural speed, inner pauses capped at ~0.3 s, silence trimmed, >= 80 ms kept), then ASR-checked.
      English must match word for word (punctuation/case ignored); Mandarin must equal the idiom.
      Writes DIR/asr_report.json; exit 1 if any line still fails after the retries.
  alitts.py say "text" OUT.wav [--voice N|M]      one line, no check
  alitts.py asr FILE.wav                          print the transcript
"""
import argparse, base64, json, os, re, ssl, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

HOST = "https://dashscope.aliyuncs.com"
TTS_MODEL, ASR_MODEL = "qwen3-tts-flash", "qwen3-asr-flash"
VOICES = {"N": ("Jennifer", "English"), "M": ("Cherry", "Chinese")}
SPEED, PAD = 1.0, 0.08
CA = "/root/.ccr/ca-bundle.crt"
CTX = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else None


def post(path, body, tries=4):
    h = {"Content-Type": "application/json"}
    if os.environ.get("DASHSCOPE_API_KEY"):
        h["Authorization"] = "Bearer " + os.environ["DASHSCOPE_API_KEY"]
    for i in range(tries):
        r = urllib.request.Request(HOST + path, data=json.dumps(body).encode(), headers=h, method="POST")
        try:
            with urllib.request.urlopen(r, context=CTX, timeout=180) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")
            if e.code in (401, 403) or "Arrearage" in msg or "quota" in msg.lower():
                raise SystemExit(f"DashScope refused ({e.code}): {msg[:300]}")  # owner email (PRODUCER §6)
            err = f"{e.code} {msg[:200]}"
        except Exception as e:  # transient "upstream request failed" etc.
            err = str(e)
        time.sleep(2 ** (i + 1))
    raise RuntimeError(f"DashScope {path} failed: {err}")


def fetch(url, dest, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, context=CTX, timeout=180) as resp:
                Path(dest).write_bytes(resp.read())
            return
        except Exception:  # IncompleteRead / reset on the audio CDN
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))


def tts(text, out, voice="N"):
    name, lang = VOICES[voice]
    d = post("/api/v1/services/aigc/multimodal-generation/generation",
             {"model": TTS_MODEL, "input": {"text": text, "voice": name, "language_type": lang}})
    with tempfile.TemporaryDirectory() as t:
        raw = Path(t) / "raw.wav"
        fetch(d["output"]["audio"]["url"], raw)
        # speed up, trim silence at both ends, then put back PAD s so no consonant is clipped
        trim = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02"
        tempo = f"atempo={SPEED}," if SPEED != 1.0 else ""
        squeeze = "silenceremove=stop_periods=-1:stop_duration=0.4:stop_threshold=-45dB:stop_silence=0.3"  # pauses inside a line <= ~0.3 s
        flt = f"{tempo}{trim},areverse,{trim},areverse,{squeeze},adelay={int(PAD*1000)},apad=pad_dur={PAD}"
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(raw), "-af", flt,
                        "-ar", "48000", "-ac", "1", str(out)], check=True)
    return out


def asr(path):
    b = base64.b64encode(Path(path).read_bytes()).decode()
    d = post("/compatible-mode/v1/chat/completions", {
        "model": ASR_MODEL, "stream": False, "asr_options": {"enable_itn": False},
        "messages": [{"role": "user", "content": [
            {"type": "input_audio", "input_audio": {"data": "data:audio/wav;base64," + b}}]}]})
    return d["choices"][0]["message"]["content"].strip()


CONTRACTIONS = {"i'm": "i am", "you're": "you are", "it's": "it is", "don't": "do not", "can't": "cannot",
                "won't": "will not", "he's": "he is", "she's": "she is", "that's": "that is", "isn't": "is not",
                "doesn't": "does not", "didn't": "did not", "couldn't": "could not", "i'll": "i will", "let's": "let us", "here's": "here is", "there's": "there is", "what's": "what is"}


def norm_en(s):
    s = re.sub(r"[^a-z0-9' ]+", " ", s.lower().replace("’", "'"))
    return " ".join(CONTRACTIONS.get(w, w) for w in s.split()).split()  # ASR may expand or contract


def norm_zh(s):
    return re.sub(r"[^一-鿿]", "", s)


def matches(line, heard, idiom):
    if line["voice"] == "M":
        return norm_zh(heard) == norm_zh(idiom or line["text"])
    return norm_en(heard) == norm_en(line["text"])


def episode(spec_path, outdir, only=None, retries=3):
    spec = json.loads(Path(spec_path).read_text())
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    report, bad = {}, []
    for b in spec["beats"]:
        for li in b.get("lines", []):
            if only and li["id"] not in only:
                continue
            for k in range(1, retries + 1):
                wav = tts(li["text"], out / f"{li['id']}.wav", li["voice"])
                heard = asr(wav)
                ok = matches(li, heard, spec.get("idiom"))
                print(f"{li['id']} try {k}: {'OK ' if ok else 'BAD'} | {li['text']} | heard: {heard}")
                if ok:
                    break
            report[li["id"]] = {"text": li["text"], "heard": heard, "ok": ok, "tries": k}
            if not ok:
                bad.append(li["id"])
    (out / "asr_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    if bad:
        print("FAILED (re-word these):", ",".join(bad)); sys.exit(1)
    print("all lines pass ASR")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "say":
        ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("text"); ap.add_argument("out")
        ap.add_argument("--voice", default="N"); a = ap.parse_args()
        tts(a.text, a.out, a.voice)
    elif len(sys.argv) > 1 and sys.argv[1] == "asr":
        print(asr(sys.argv[2]))
    else:
        ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("--outdir", required=True)
        ap.add_argument("--only"); ap.add_argument("--retries", type=int, default=3); a = ap.parse_args()
        episode(a.spec, a.outdir, set(a.only.split(",")) if a.only else None, a.retries)
