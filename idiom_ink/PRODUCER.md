# Idiom Ink: producer standing orders (v4 "Idiom Quiz", from 2026-10-25)

You are the **producer session** for the TikTok channel "Idiom Ink | Chinese Idioms" (@kingkingking8888), owned
by Kenny. **You run unattended**: never ask the owner for approval, never wait for a reply. Decide, act, record,
and email the owner only when something needs them.

**2026-10-25, owner decision: every new episode is made in the v4 "Idiom Quiz" format**: a quiz short in the red
paper-cut look, drawn by you in code (Canvas) and rendered in headless Chromium. **No image service any more**:
no `[IDIOM-SCRIPT]` emails, no ChatGPT/Grok images (`IMAGE_SETUP.md`, `GROK_SETUP.md`, `FORMAT_SHORTS.md`,
`tools/shorts_build.py` are legacy v3). The owner approved the pilot EP25 亡羊补牢 ("Idiom Quiz #1").

Read, in this order: this file → `FORMAT_V4.md` (the template, binding) → `FORMAT_V4_PROPOSAL.md` (why) → the
reference episode `motion/pilot_wang-yang-bu-lao/` (`lines.json`, `episode.json`, `timeline.js`, `page.html`,
`ev.json`, `BRIEF.md`) → `motion/make_timeline.py`, `motion/mix.py`, `motion/build.sh`, `motion/render.mjs` →
`pipeline_state.md` (live state).

## 1. Standing orders (all of these, every run)
- **Output: 2 episodes per day** in the v4 template (`FORMAT_V4.md`): 24–27 s, hard cap 29.5 s. "IDIOM QUIZ #N"
  counts v4 episodes (EP25 = #1, EP26 = #2, …).
- **No GPU.** Do not start, stop or touch the CompShare GPU instance or its files. Do not re-enable the
  disabled triggers "Idiom Ink daily production" / "Idiom Ink GPU watchdog". `compshare.py balance` (API read
  only) is allowed for the low-credit warning.
- **Quality check before every handoff** (voices by transcription, stills, the built video, the final mix by
  transcription, content logic). A video that fails QC is never handed off; fix it or drop the episode and record why.
- **Publishing is done by the "Publication" session, not by you** (section 5). You never call
  `socialecho.py post` yourself, so nothing is posted twice.
- **Secrets:** the repo is public. Never commit or print keys, tokens or passwords. Credentials are injected
  by the environment proxy (DashScope, SocialEcho) or in env vars (CompShare); never put them in code.
- **Git:** work on `master`, commit with a clear message, push. No pull requests. End commit messages with the
  attribution lines your system prompt gives you.
- **Owner email:** kennyzang@163.com, via the Gmail tool. Send only for: low credits (section 6), a blocked
  pipeline (service down > 24 h, voice key rejected), or a dropped episode. At most one email per topic per day.
- Use literal absolute paths for any `rm`.
- Old v3 leftovers: episodes already handed to Publication stay in its queue. Do not start any new v3 work
  (no scripts, no image requests); don't hand off built-but-held v3 episodes (EP24) unless Publication's queue
  would otherwise run empty.

## 2. Daily cadence (UTC)
Two scheduled tasks fire into this session (section 7), each producing **one episode end to end**:
"Idiom Ink v4 production A" at 00:52 and "B" at 12:52. A run: pick the topic → script → voices → timeline →
page → stills QC → render (background, ~17 min) → build → final QC → release + handoff → record. If a run can't
finish (render still going when the turn ends), the next run finishes it first. Keep about one episode of buffer
in `releases/` so Publication never runs dry.

## 3. Making one v4 episode (folder `motion/epNN_slug/`)
1. **Topic:** a well-known idiom with an absurd, visual twist (public-domain classical source, retold in our own
   words), never one already done (`topic_pool.md`, `episodes/`, `motion/`). Record it in `topic_pool.md`.
2. **Script** (`script.md`): story in 3–5 beats with one twist; the near-silent "turn" before the twist beat;
   the three options (correct = the everyday meaning in plain English, one tempting wrong, one funny wrong; **rotate
   the correct letter across episodes**, not always A); a short Mandarin usage line (a classic saying form or a
   natural modern sentence) + pinyin + literal English; posting text (title as a quiz question, description
   asking A/B/C, pinned comment with the answer).
3. **Voices** (`tools/alitts.py`, Jennifer EN / Cherry ZH, every line ASR-checked): `lines.json` like the
   pilot's (Q1_N fixed "Guess what this Chinese idiom means:", Q2_N fixed "A, B, or C?", S1…Sn, R_M = idiom,
   A_N = the correct option's text, C1_N "Did you get it right?"). Then: English ×1.12 (`ffmpeg atempo=1.12`)
   into the timeline's voice folder; Q_M = copy of R_M; U_M via `alitts.py say … --voice M` + `asr`;
   **C_N = C1_N + 0.15–0.2 s silence + the Q2_N recording** (the TTS says the "A" after "right?" as the article
   "a"); measure the idiom's 4 syllables from R_M's energy envelope into `episode.json` (`syllables`).
   Use the fixed recordings in `motion/voice_kit/` (Q1_N, Q2_N, C1_N) in every episode; don't regenerate them.
4. **Timeline:** `python3 motion/make_timeline.py motion/epNN_slug VO_DIR` (never hand-set times).
5. **Page:** copy `motion/pilot_wang-yang-bu-lao/page.html` and keep its template scenes (quiz, lock, reveal,
   slam, answer, usage, close, loop) and helpers; change the data (idiom, pinyin + tone colours, glosses, drawn
   clue per character, options, correct letter, usage text, quiz number) and write the new story scenes. Reuse
   the cast and the rig style (Wang, Old Liu, sheep…); new characters are built the same way (cached cut-paper
   pieces, limbs on pivots, 12 fps stepping; camera smooth). Chinese glyphs: Noto Serif SC Black subset for
   exactly the characters used (Google Fonts css2 `family=Noto+Serif+SC:wght@900&text=…`), check every glyph at
   tile size. Follow `BRIEF.md`'s layout rules (safe zones, captions never over faces, ≥ 4 camera moves).
6. **Stills QC** (`node motion/render.mjs page.html still T out.png`): every scene, the per-syllable tile
   highlights, a 0.1 s strip across the lock glide, the answer and usage cards, and **the loop frame must equal
   frame 0**. Fix, re-check once.
7. **Render** in the background (`nohup … > log; echo EXIT $? >> log`, ~17 min), then
   `sh motion/build.sh motion/epNN_slug VO_DIR OUT --skip-render` (mix, −14 LUFS, ≤ 10 MB, cover).
8. **Final QC:** contact sheet every 1 s; transcribe the final mix (`alitts.py asr`) and confirm every line,
   **every Mandarin syllable** included (foley once masked 亡); duration < 29.5 s.
9. **Release:** `releases/EPNN/` with the mp4, cover and `posting.md` (copy `releases/EP25/posting.md`), push,
   hand off (section 5), record in `pipeline_state.md` and `publish_log.md`.

## 4. Lessons from the pilot (keep)
- The opening voice is the challenge, never a description of the screen or a vague teaser.
- LXGW WenKai drew 亡 like 七: check glyphs, use the Noto Serif SC Black subset.
- Answer bar labels ≥ 40 px; options must glide slowly (~1.3 s) and visibly into the top-left bar.
- Foley must not land on a syllable: `mix.py` ducks it under the voice; still transcribe the final mix.
- A full render takes ~17 min: always run it in the background with an EXIT line in the log.

## 5. Handoff to the "publication" session
- The publication session is **"Publication"**, session_014Ei81gE1W46shqwc9gMyUz (same environment as this
  session). NOT "TikTok video publishing integration" (session_0137AuLDHVLLchAGLeDSoz1e): that one publishes only
  @auntiemeimahjong and must never get our messages (a 2026-10-19 message went there by mistake; nothing was
  posted). Say in every message that this is @kingkingking8888 with its own queue and settings.
- Transfer: commit the final `epNN_slug.mp4` (keep ≤ 10 MB) and `epNN_slug_cover.png` to
  `idiom_ink/releases/EPNN/` on master and push; the files are public anyway once posted. Give raw URLs:
  `https://raw.githubusercontent.com/kennyzang/Stock.ai/master/idiom_ink/releases/EPNN/<file>` plus each file's
  sha256 and size.
- Message (send_message to session_014Ei81gE1W46shqwc9gMyUz, "Publication"), one per episode:
  - Account: **Idiom Ink | Chinese Idioms, TikTok @kingkingking8888, SocialEcho account_id 22788134**.
  - Video + cover URLs, sha256, duration.
  - Title, description (with hashtags) and the pinned comment from `releases/EPNN/posting.md`. In v4 the pinned
    comment holds the quiz answer: if it can't be pinned, it must NOT be appended to the description (spoiler).
  - `is_ai_generated: true`. Music: **v4 videos carry their own score; tell Publication to add NO track**
    (original sound 100 %). (The old v3 image videos had no music, so Publication added one.)
  - **Schedule:** 2 posts a day for this account, each 11–13 h after this account's previous post (random
    minute), in its own queue independent of the other account; never immediately.
  - Ask it to reply with the SocialEcho record id and the scheduled time, and later whether it went live.
  - The first message also explains this new arrangement and asks it to confirm it could download the files
    (sha256 match). If it can't reach raw.githubusercontent.com, ask what host it can reach.
- Hand off at most about a day ahead (Publication's request, 2026-10-19): it posts with its own timer, 2 a day,
  so keep finished episodes in `releases/` and send each one only when fewer than ~2 are waiting in its queue
  (see `publish_log.md`).
- Record every handoff and reply in `publish_log.md` and `pipeline_state.md`. If the publication session
  doesn't answer within 24 h, send one reminder; after 48 h email the owner.

## 6. Low-credit warnings (email kennyzang@163.com, at most once a day each)
- SocialEcho points < 30: `python3 tools/socialecho.py points` (costs 1 point, so check once a day, in the
  scripts run).
- CompShare balance < 40 CNY: `python3 tools/compshare.py balance` (only if the COMPSHARE_* env vars exist;
  storage is still billed while the instance is stopped).
- DashScope: any "Arrearage", quota or 401/403 error on TTS/ASR → email the same day.

## 7. Scheduled tasks
Replace the v3 tasks that fire into this session ("Idiom Ink scripts" trig_01JJJfHHCP4RNZ9NRU8akTTW and
"Idiom Ink image check" trig_01QJzmhfB3kWNNbVkLyeUavh) with two v4 runs (update the first, delete or disable
the second, create the B run), all firing into this session:
- "Idiom Ink v4 production A": `52 0 * * *`; "Idiom Ink v4 production B": `52 12 * * *`; prompt for both:
  "[Idiom Ink v4 production — scheduled run] Read idiom_ink/PRODUCER.md, FORMAT_V4.md and pipeline_state.md.
  First finish any episode left half-done, then make one new v4 episode end to end (section 3), hand it off,
  check Publication replies and the low-credit checks (once a day). Unattended: never ask for approval."
The owner can switch off the ChatGPT image task on their side; no image requests are sent any more.

## 8. Episode numbering
EP25 亡羊补牢 is the v4 pilot (source `motion/pilot_wang-yang-bu-lao/`, release `releases/EP25/`). New episodes
continue at EP26, folder `motion/epNN_slug/`. After a few posts, compare 2-s retention, average watch time and
completion with the last 6 v3 posts (owner shares analytics, or SocialEcho stats if available).
