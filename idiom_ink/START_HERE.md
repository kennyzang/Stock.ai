# Idiom Ink: start here (every new session)

You are continuing an automated TikTok production + publishing project for the owner (Kenny).
Earlier sessions are gone; this folder is the memory. Read this file fully, then the files it points to.
**Before you end a session, update the "Status log" at the bottom and push** (branch `master`).

> This repo (`kennyzang/Stock.ai`) is **public** and is mainly an unrelated stock-picking project.
> Never commit tokens, keys, passwords, hostnames of the GPU server or Jupyter URLs. Only touch `idiom_ink/` and `HANDOVER_SOCIALECHO.md`.

## 1. What we are doing

**"Idiom Ink | Chinese Idioms"**: one Chinese idiom (成语) per video, animated ink-wash story, vertical, 70–85 s.
TikTok account handle `kingkingking8888` (SocialEcho account_id `22788134`).

The owner's standing orders (2026-10-15):
1. **Produce 3 videos per day**, to match publishing (one post every 7–9 h, random gap).
2. **GPU on only to produce.** Each time the GPU instance is started, produce **3 videos in a row**, then **shut it down
   right after the last video and its quality check.** Start it again only the next day for the next 3.
3. **Quality check is very important.** Generation always brings unexpected mistakes. Double-check overall video
   quality AND content logic (meaning, metaphor mapping, ending agrees with lesson) before uploading.
   A video that fails is fixed or dropped, never uploaded.
4. **Reference images:** use whatever is on the GPU server (no ChatGPT/Codex). Decision: FLUX.2 klein 9B, see §4.
5. **Fonts:** Claude decides. Decision: see §4.
6. **Topics:** the owner will NOT add more book pages. After the book topics are used up, choose well-known idioms
   with clear public-domain origin stories yourself (§5).
7. Episodes 01–05 are already posted on TikTok. Do not repost them.

## 2. Read next (in this order)

1. On the GPU server: `/root/autodl-tmp/idiom_handover/README_HANDOVER.md`, then `PRODUCTION_GUIDE.md` (the full
   playbook + ~50 mistakes already made; follow it). Read them through Jupyter (§3).
2. `HANDOVER_SOCIALECHO.md` (repo root): SocialEcho API, points, publish flow, error rules.
   **Correction:** set `extra.is_ai_generated: true` on every post (guide rule 8), not `false` as its example shows.

## 3. Access (how a cloud session reaches things)

| Thing | How | Needs |
|---|---|---|
| GPU server shell | **No SSH** from cloud sessions (raw TCP blocked). Use `tools/jupyter_exec.py 'cmd' [timeout]`, which drives a JupyterLab terminal over HTTPS/WebSocket. Files: Jupyter contents API `GET/PUT $JUPYTER_URL/api/contents/<path>` (`?type=file&format=base64` for binaries). | env `JUPYTER_URL`, `JUPYTER_TOKEN`; `pip install websocket-client` |
| GPU on/off | CompShare API `https://api.compshare.cn` (UCloud-style signed requests: PublicKey + Signature = SHA1 over sorted params + private key). Actions like `DescribeCompShareInstance`, `StartCompShareInstance`, `StopCompShareInstance` (check docs for exact params, zone `cn-sh2-01`, and how to start **with GPU**: it was once started in no-GPU mode). | env `COMPSHARE_PUBLIC_KEY`, `COMPSHARE_PRIVATE_KEY` |
| SocialEcho | `https://api.socialecho.net`; the environment's proxy injects the `Authorization` header, so call it with plain curl and **no** header. Every call costs points. | already configured |

Notes:
- If any env var above is missing, tell the owner which one; never ask for secrets in chat.
- The Jupyter token looked stable across restarts. If it changed, say so.
- `jupyter_exec.py` output: long jobs must run with `setsid nohup … &` and be polled.
- After a GPU start, check `nvidia-smi` shows the RTX 5090. 2 CPUs / 4 GB RAM / empty `nvidia-smi` = started without GPU.
- ComfyUI is down after every restart: `curl -sf http://127.0.0.1:8188/system_stats || bash /root/_h3_start_comfy.sh` (on the server).
- The server is shared with other projects of the owner. Never modify files you didn't create.

## 4. Decisions already made

- **Reference images:** ComfyUI + **FLUX.2 klein 9B** (multi-reference; weights in the shared library
  `/model/HuggingFace/black-forest-labs/FLUX.2-klein-9b-kv-fp8` and `-nvfp4`). Attach the scholar-cat mascot sheet and a
  previous episode's character sheet as style refs, prompt starts with episode 5's `STYLE` string.
  Fallback: FLUX.1 Kontext dev (`/model/HuggingFace/black-forest-labs/FLUX.1-Kontext-dev`).
  Look at every generated image against episodes 3–5 refs before rendering video (guide step C).
  Not yet set up: wiring these into `/root/autodl-tmp/ComfyUI-H3` (or a separate ComfyUI) = first GPU-day task.
- **Fonts** (install on the server into `~/.fonts`, `fc-cache -f`):
  - Chinese (replaces KaiTi): **LXGW WenKai** (SIL OFL, Kai style).
  - English (replaces Segoe UI Semibold/Black): **Selawik** (SIL OFL, Microsoft's Segoe-UI-metric-compatible font),
    so caption widths and line breaks stay the same. Update `build.py`/`cover.ass` font names accordingly.
- **Editing runs on the GPU server** (ffmpeg is there), so no large file transfers.
- **Publishing runs from a cloud scheduled task** (has the SocialEcho proxy; does not need the GPU on):
  finished videos are uploaded to SocialEcho storage on production day, their `public_url` + caption go in a queue,
  and each publish run posts the next item. First verify how long `public_url` stays valid (one test upload).

## 5. Topics

Order: finish the book's strong ones from `topic_pool.md` (06 瓜田李下, 07 东窗事发 (dark: handle with care), 08 班门弄斧).
Skip the book's ★☆☆ ideas (no story). Then self-chosen idioms with a clear, concrete origin story, e.g.:
守株待兔, 画蛇添足, 刻舟求剑, 亡羊补牢, 掩耳盗铃, 拔苗助长, 狐假虎威, 自相矛盾, 井底之蛙, 叶公好龙, 塞翁失马,
朝三暮四, 滥竽充数, 惊弓之鸟, 卧薪尝胆, 破釜沉舟, 纸上谈兵, 望梅止渴, 草木皆兵, 完璧归赵, 负荆请罪, 三顾茅庐,
画龙点睛, 鹬蚌相争, 杞人忧天, 买椟还珠, 南辕北辙, 闻鸡起舞, 愚公移山, 指鹿为马.
Add each to `topic_pool.md` on the server when used. Retell in our own words (stories are public domain, books are not).

## 6. Daily production cycle (one session per day)

1. Start the GPU instance with GPU → wait for Jupyter → confirm `nvidia-smi` → ComfyUI up.
2. For each of 3 episodes: script → refs (FLUX.2) → H3 jobs → review every clip → MOSS voices (free ComfyUI VRAM first)
   → ASR-check every line → edit → quality check (guide steps F and I + a content-logic read of the script vs video)
   → cover + `posting.md`.
3. Upload passing videos to SocialEcho storage; append to the publish queue.
4. **Stop the GPU instance; confirm it is stopped.** Never leave it running.
5. Update the status log below; push.

Budget: about 3–5 GPU hours per day. After 2 failed re-rolls of a shot, trim/reuse/rewrite (guide P2).

## 7. Still open (as of 2026-10-15)

- [ ] Owner adds env vars `COMPSHARE_PUBLIC_KEY`, `COMPSHARE_PRIVATE_KEY` (new pair, old one leaked), `JUPYTER_URL`, `JUPYTER_TOKEN`.
- [ ] Owner tops up SocialEcho points (97 left on 2026-10-15; ~10+/day needed).
- [ ] Owner rotates the server root password (it was pasted in chat) and considers making this repo private.
- [ ] Build: CompShare start/stop script, SocialEcho uploader + queue, scheduled tasks (daily production; 7–9 h publish chain).
- [ ] First test publish (cost per post, draft vs publish behaviour, `public_url` lifetime).
- [ ] Wire FLUX.2 klein into ComfyUI; install fonts.

## Status log (newest first)

- 2026-10-15: Access proven: Jupyter terminal works from cloud (`tools/jupyter_exec.py`); SSH and the old CompShare
  token do not. Server was in no-GPU mode; owner asked to stop it manually. No episodes 06+ started yet.
