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
| GPU server shell | **No SSH** from cloud sessions (raw TCP blocked). Use `tools/jupyter_exec.py 'cmd' [timeout]`, which drives a JupyterLab terminal over HTTPS/WebSocket. Files: Jupyter contents API `GET/PUT $JUPYTER_URL/api/contents/<path>` (`?type=file&format=base64` for binaries). | `JUPYTER_URL`/`JUPYTER_TOKEN` from `compshare.py jupyter`; `pip install websocket-client` |
| GPU on/off, balance | `tools/compshare.py status / start / stop / wait Running|Stopped / balance / jupyter`. Signed CompShare API calls (verified 2026-10-15). `start` always passes `WithoutGpu=false`. `eval $(python3 tools/compshare.py jupyter)` sets `JUPYTER_URL`/`JUPYTER_TOKEN` from the API (only while Running). | env `COMPSHARE_PUBLIC_KEY`, `COMPSHARE_PRIVATE_KEY` |
| SocialEcho | `tools/socialecho.py points / post VIDEO CAPTION WHEN / posts`. The environment's proxy injects the `Authorization` header (no key in code). Every call costs points. `post` is written from the docs but **not yet tested**: the first real use must check the result carefully. | already configured |
| Email to Kenny | Gmail tool `mcp__Gmail__send_message` to **kennyzang@163.com**. Scheduled sessions may not have Gmail; then put the message at the top of the final reply (the task's push/email notification delivers it). | Gmail connector |

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
- **Publishing uses SocialEcho's own scheduling** (`scheduled_at`), so no session has to wake up per post:
  on production day each passing video is uploaded and scheduled at *previous scheduled post + random 7–9 h*
  (never earlier than now + 30 min). 3 videos/day × ~8 h ≈ 24 h, matching the daily production.
  Every post: `is_ai_generated: true`. Record each one in `publish_log.md`. Next day, verify they actually published.
- **Thresholds (owner asked for warning emails):** CompShare `AmountAvailable` < ¥40 → warning email;
  < ¥15 → skip production (don't start the GPU). SocialEcho points < 30 → warning email; < 10 → don't schedule posts.

## 5. Topics

Order: finish the book's strong ones from `topic_pool.md` (06 瓜田李下, 07 东窗事发 (dark: handle with care), 08 班门弄斧).
Skip the book's ★☆☆ ideas (no story). Then self-chosen idioms with a clear, concrete origin story, e.g.:
守株待兔, 画蛇添足, 刻舟求剑, 亡羊补牢, 掩耳盗铃, 拔苗助长, 狐假虎威, 自相矛盾, 井底之蛙, 叶公好龙, 塞翁失马,
朝三暮四, 滥竽充数, 惊弓之鸟, 卧薪尝胆, 破釜沉舟, 纸上谈兵, 望梅止渴, 草木皆兵, 完璧归赵, 负荆请罪, 三顾茅庐,
画龙点睛, 鹬蚌相争, 杞人忧天, 买椟还珠, 南辕北辙, 闻鸡起舞, 愚公移山, 指鹿为马.
Add each to `topic_pool.md` on the server when used. Retell in our own words (stories are public domain, books are not).

## 6. Daily production cycle (one session per day)

Scheduled tasks (fresh session each time, environment's env vars + SocialEcho proxy, no Gmail connector):
- **"Idiom Ink daily production"** `trig_01ExjP1vcZApwMpyjAFJyCaX`, daily 15:48 UTC (00:48 Beijing).
- **"Idiom Ink GPU watchdog"** `trig_012AKRimu75ZjcbrwvBuQ9tM`, daily 01:52 UTC: stops the GPU if a production run
  died and left it on; also warns on low balance.


1. Start the GPU instance with GPU → wait for Jupyter → confirm `nvidia-smi` → ComfyUI up.
2. For each of 3 episodes: script → refs (FLUX.2) → H3 jobs → review every clip → MOSS voices (free ComfyUI VRAM first)
   → ASR-check every line → edit → quality check (guide steps F and I + a content-logic read of the script vs video)
   → cover + `posting.md`.
3. Upload passing videos to SocialEcho storage; append to the publish queue.
4. **Stop the GPU instance; confirm it is stopped.** Never leave it running.
5. Update the status log below; push.

Budget: about 3–5 GPU hours per day. After 2 failed re-rolls of a shot, trim/reuse/rewrite (guide P2).

## 7. Still open (as of 2026-10-15)

- [ ] Owner adds env vars `COMPSHARE_PUBLIC_KEY`, `COMPSHARE_PRIVATE_KEY` to the cloud environment (needed by every scheduled run).
- [ ] Owner tops up CompShare (¥15.45 on 2026-10-15, ≈ one production day) and SocialEcho (97 points; ~10+/day).
- [ ] Owner may add the Gmail connector to the two scheduled tasks in the claude.ai routines UI (else warnings come as task notifications).
- [ ] Owner rotates the server root password (pasted in chat) and considers making this repo private.
- [x] CompShare start/stop/balance script, SocialEcho scheduler script, scheduled tasks.
- [ ] First real post: check points cost, scheduled_at behaviour, the record in `posts`. Log the results here.
- [ ] Wire FLUX.2 klein into ComfyUI; install fonts (first GPU day, before episode 06).
- [ ] Measure real GPU cost per episode (`balance` before/after) and adjust the ¥ thresholds.

## 8. Lessons from episode 06 (first fully cloud-run episode, 2026-10-16)

Pipeline that worked (copy `episodes/06_gua-tian-li-xia/`): script.md → `references/make_refs.py` (FLUX.2 klein jobs)
→ `h3/make_jobs.py` → `/root/run_episode.sh` → `tools/collect_clips.sh ep06 06_slug` (clips + contact sheets on the
server; download the jpgs with `jupyter_files.py get` and LOOK at them) → `edit/build.py --audio-only` (MOSS via
`moss_local.py`) → ASR check → `edit/build.py` → freezedetect + frame grid → cover → `socialecho.py post` → stop GPU.
The episode folder on the server is `/root/autodl-tmp/idiom_handover/NN_slug/`; keep the repo copy in sync.

- **GPU start:** "This GPU type is currently out of resources" (226604) is common. Keep retrying every 2 min; CompShare
  then migrates the disk to a free host (226621 "System disk migration in progress", then 226622 "Pod is starting").
- **Cost:** ¥3.84/h for the RTX 5090; episode 06 took ~1 h 55 min = ¥7.46 including one-time setup. Storage keeps
  billing while stopped (~¥1.3/day).
- **Reference images (FLUX.2 klein 9B, ~5 s each):** never attach another episode's character sheet or the cat sheet
  to a human character sheet: figures leak in (a bearded old man, cat ears/tails). Use the new style frame plus at most
  the main character sheet. Render 2 seeds; if stray figures appear, crop the clean ones and pad with the paper colour.
  Red seal stamps can appear: reject.
- **H3:** multi-character story shots were fine. Single-person shots sometimes grow a duplicate/ghost: say "Exactly one
  person in the whole scene … stays one single solid figure". Shots with only the cat sheet produced floating ink blobs,
  fake calligraphy/text and see-through desks in 6 of 6 tries → make "Use it" shots as **FLUX stills + slow zoom**
  (bottom-anchored so the cat sits mid-frame under the text panel). "Golden hour" in a landscape gave a glowing sun +
  lens flares → payoff background = **slow zoom on the clean style frame** (P1/P2 chained on one still, see CHAIN).
- **Voices:** the old silence trim (-45 dB, no margin) cut the plosive off lines starting with 瓜 (ASR heard 花);
  `moss_local.py` now keeps 80 ms. Lines of ~3 words can come out as junk (A2): write ≥6-word lines.
- **ASR:** `asr_check.py`'s zh prompt "以下是普通话的句子" biases Whisper to write 以下 for 李下. Check Mandarin with no
  initial prompt (`beam_size=5, condition_on_previous_text=False`), see the snippet in this session's history.
- **Length:** first cut was 93.7 s; tightening the examples and merging a bridge line gave 89.3 s. Budget the script
  for ~80 s: short example sentences (≤12 characters), loop line ≤10 words.
- **Tools:** `jupyter_exec.py` runs commands with stdin=/dev/null (ffmpeg used to swallow the end marker and hang the
  client); use `ffmpeg -nostdin` in server scripts anyway. Jupyter can't write hidden dirs (`~/.fonts`): upload
  elsewhere and `cp`. `pkill -f` patterns can kill your own command (I4).
- **SocialEcho:** upload URL 1 point + publish 1 point per post; `GET /v1/article` lists only already-published TikTok
  videos (scheduled records appear after they publish).

## Status log (newest first)

- **2026-10-19 HANDOVER:** production moves to a dedicated unattended producer session; its standing orders
  are `PRODUCER.md` (2 episodes/day, Grok images, Alibaba voices, publishing via the "publication" session).
  Image service (ChatGPT, was Grok) setup prompt: `IMAGE_SETUP.md`. Live state: `pipeline_state.md`.

- 2026-10-19: **NEW FORMAT from episode 10: read `FORMAT_SHORTS.md` first.** Owner decisions: no GPU instance,
  videos < 30 s with a faster pace (play-through rate for a new account), images from **Grok** via email
  (`[IDIOM-SCRIPT] EPNN · date` to kennytseng4@gmail.com → PNGs in Drive `Idiom-Ink-images/EPNN_date/` → reply
  `[IDIOM-IMAGES]`), voices from the owner's **Alibaba Cloud** API. Editing runs in the cloud session with
  `tools/shorts_build.py` (fonts: `tools/setup_fonts.sh`). EP10 画蛇添足 is the pilot: image request sent 13:2x UTC;
  the GPU sections above (H3, FLUX, MOSS, Jupyter, CompShare start/stop) are legacy. The Alibaba key is not
  connected yet.

- 2026-10-18: **GPU disk cleanup (owner-approved).** Freed ~38 GB: `/` went 153 GB used / 28 GB free → 115 GB / 65 GB.
  Deleted: pip cache (12.7 GB), model `minimax_h3_fl2va_pruned_int8_convrot.safetensors` (19.5 GB; the idiom pipeline
  only uses ref2va; last used by the owner's `human-intern-ep01` jobs on 2026-09-12) and `ace_step_1.5_turbo_aio`
  (9.3 GB; unused by any job), a stale 467 MB /tmp file, the 417 MB failed-login log (`btmp`, shows the server is
  being brute-forced), and my regenerable episode intermediates (`joined.mp4` of 06-09, ep06 replaced voice takes).
  Verified the ref2va model, H3 text encoder/VAEs/4-step LoRA, FLUX.2 klein, MOSS, fonts and the venv are intact.
  Checked the 22 GB `hf_cache/hub/blobs` store: NOT duplicated, no orphans, all used by MOSS-TTS v1.5 /
  Audio-Tokenizer / VoiceGenerator. Optional: MOSS-VoiceGenerator (3.9 GB) is only needed to design new voices.
  Facts for later: the Oct 17 15:48 UTC scheduled run produced episodes 07 東窗事發 (live 10-17 19:21 UTC),
  08 班門弄斧 (live 10-18 03:21 UTC) and 09 守株待兔 (finished; not yet published as of 04:41 UTC), but did NOT
  commit/log them: `publish_log.md` is missing rows for 07-09. (The GPU was left running at the owner's request.)

- 2026-10-18: **Production schedule PAUSED by the owner.** Both scheduled tasks are disabled (not deleted):
  "Idiom Ink daily production" `trig_01ExjP1vcZApwMpyjAFJyCaX` (15:48 UTC) and "Idiom Ink GPU watchdog"
  `trig_012AKRimu75ZjcbrwvBuQ9tM` (01:52 UTC; paused too because it stops a running GPU, which would kill another
  agent's work). The owner is letting another agent use the GPU. **Do not start, stop or otherwise touch the GPU
  instance, and do not re-enable the tasks, until the owner says so.** To resume: `update_trigger` with
  `enabled: true` on both ids (plus the COMPSHARE_* env vars must be set, see section 7).

- 2026-10-16: **Episode 06 瓜田李下 produced** (89.4 s, all checks passed; audio ASR-verified, not listened to) and
  scheduled on SocialEcho for 2026-10-16 18:34 UTC (record 543997). GPU stopped 16:11 UTC; balance ¥56.67;
  SocialEcho 92 points. Env vars COMPSHARE_* still NOT set in the environment → scheduled runs will fail until added.
  Next topic: 07 东窗事发 (dark story: keep it non-violent), then 08 班门弄斧.

- 2026-10-15 (later): CompShare signed API works (`compshare.py`); GPU stopped via API. Balance ¥15.45 → warning
  email sent to kennyzang@163.com. Created the daily production + watchdog scheduled tasks (first run 2026-10-16).
- 2026-10-15: Access proven: Jupyter terminal works from cloud (`tools/jupyter_exec.py`); SSH and the old CompShare
  token do not. Server was in no-GPU mode; owner asked to stop it manually. No episodes 06+ started yet.
