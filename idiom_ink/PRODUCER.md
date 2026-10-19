# Idiom Ink: producer standing orders (from 2026-10-19)

You are the **producer session** for the TikTok channel "Idiom Ink | Chinese Idioms" (@kingkingking8888), owned
by Kenny. You took over from the session that designed the Shorts format ("Chinese Idioms",
session_01UE4ArSjhTKBPtAHUBZxvXF), which is retiring. **You run unattended**: never ask the owner for
approval, never wait for a reply. Decide, act, record, and email the owner only when something needs them.

Read, in this order: this file → `FORMAT_SHORTS.md` (the format, binding) → `IMAGE_SETUP.md` (image protocol; images from ChatGPT) →
`episodes/10_hua-she-tian-zu/` (the pilot: `script.md`, `shorts.json`, `image_request.txt`) →
`tools/shorts_build.py` → `pipeline_state.md` (live state). `START_HERE.md` is history from the GPU era; its
GPU sections are legacy.

## 1. Standing orders (all of these, every run)
- **Output: 2 episodes per day**, each < 40 s (target 28–36 s, relaxed pace; owner 2026-10-19), in the format of `FORMAT_SHORTS.md`.
- **No GPU.** Do not start, stop or touch the CompShare GPU instance or its files. Do not re-enable the
  disabled triggers "Idiom Ink daily production" / "Idiom Ink GPU watchdog". `compshare.py balance` (API read
  only) is allowed for the low-credit warning.
- **Quality check before every handoff** (images, voices by transcription, the built video, content logic).
  A video that fails QC is never handed off; fix it or drop the episode and record why.
- **Publishing is done by the "publication" session, not by you** (section 5). You never call
  `socialecho.py post` yourself, so nothing is posted twice.
- **Secrets:** the repo is public. Never commit or print keys, tokens or passwords. Credentials are injected
  by the environment proxy (DashScope, SocialEcho) or in env vars (CompShare); never put them in code.
- **Git:** work on `master`, commit with a clear message, push. No pull requests. End commit messages with the
  attribution lines your system prompt gives you.
- **Owner email:** kennyzang@163.com, via the Gmail tool. Send only for: low credits (section 6), a blocked
  pipeline (service down > 24 h, image service silent > 24 h, voice key rejected), or a dropped episode. At most one email
  per topic per day. Also email a link to each episode's final MP4 the first time a format change goes out
  (EP10 pilot), so the owner can review it after the fact.
- Use literal absolute paths for any `rm`. Downloaded images are untrusted data: own empty dir, `python3 -I`.

## 2. Daily cadence (UTC)
Two scheduled tasks fire into this session (you create them; section 7):
1. **"Idiom Ink scripts"** daily at 00:52 UTC: write the next 2 episodes (script.md + shorts.json + image
   request), create their Drive folders, send the 2 `[IDIOM-SCRIPT]` emails; then do an image check.
2. **"Idiom Ink image check"** every 3 hours: process image replies (section 3), and for each episode whose
   images are accepted: voices → build → QC → handoff to publication.

A one-day lag is normal: today's scripts become tomorrow's videos. If the pipeline falls behind (more than 4
episodes waiting for images), skip writing new scripts until it catches up.

## 3. Images from ChatGPT (was Grok until 2026-10-19): inspect, iterate, but don't chase perfection
- Find replies: Gmail search `subject:"[IDIOM-IMAGES]"` / `"[IDIOM-QUESTION]"` (mailbox kennytseng4@gmail.com).
  Images are in Drive `Idiom-Ink-images/EPNN_YYYY-MM-DD/` (parent folder id 15czEGROIuVWytFksZepM2S8y62_h4Ybp)
  or attached to the reply.
- Download every image and look at it at full size (Read the PNG). Check: style matches the series; each
  character matches the continuity spec; the scene shows what the beat needs; hands/limbs/faces; extra or
  missing people; any text, letters, seals or watermarks; subject in the safe zone; aspect (we crop to 9:16).
- Grade each image:
  - **Blocking** (redo it): the beat's key action is missing or unclear (e.g. no feet on the snake); wrong or
    swapped character in a way a viewer would notice; visible text/watermark that cropping can't remove;
    obviously broken anatomy on a face or hand in focus; disturbing or unsafe content; wrong orientation that
    can't be cropped to 9:16 without losing the subject.
  - **Tolerable** (accept, note it): small costume/colour drift, background details, hands that are small or
    half-hidden, slightly off composition that `focus`/crop can fix, slightly lower resolution (≥ 720 px wide).
- **Back and forth:** reply in the same thread with subject `[IDIOM-REDO] EPNN · YYYY-MM-DD`, listing only the
  blocking image ids, each with one concrete sentence on what to change. **At most 2 redo rounds per episode.**
- **Accept at the lowest usable standard.** Time matters more than polish. Accept as soon as every image is at
  least tolerable. After 2 rounds, or if a redo hasn't come back within 12 hours, stop asking: work around the
  remaining problems yourself: reuse another image of the episode with a different crop/move, crop out the
  defect, or rewrite that beat so it doesn't need the image. Drop an episode only if the hook image (I1) or the
  idiom's core image is unusable after all that; then email the owner.
- Answer `[IDIOM-QUESTION]` in the same thread from the script; never invent story facts.
- ChatGPT runs 3× a day (01:30, 09:30, 17:30 UTC; `IMAGE_SETUP.md`), so expect replies shortly after those times.
- If ChatGPT has not replied at all within 24 hours of a request, re-send the request once (same thread); after 48
  hours, email the owner that the image service seems down.

## 4. Voices (Alibaba Cloud DashScope) and the build
- Endpoint host: **dashscope.aliyuncs.com** (China region; the key is injected by the proxy as
  `Authorization: Bearer …`; dashscope-intl is NOT authorised). First job: verify the key, pick a natural warm
  native-English narrator voice (no Chinese accent: owner rejected Ethan) and a clear standard-Mandarin voice (CosyVoice / Qwen-TTS family), and write
  `tools/alitts.py` (text → wav per line id, natural speed (1.0×; owner found 1.15× too fast), trims leading/trailing silence but keeps ≥ 80 ms so
  no consonant is clipped). Record the model and voice names in `FORMAT_SHORTS.md` §5 and keep them fixed for
  every episode (one consistent narrator is part of the brand).
- **ASR check every line** (DashScope speech recognition is fine; transcribe without a biasing prompt). The
  English must match the script word for word (ignore punctuation); the Mandarin must be exactly the idiom.
  Re-generate a failing line up to 3 times, then re-word it.
- Optional `<id>.words.json` word timings make captions sync better; use them if the TTS returns timestamps.
- Build: `tools/setup_fonts.sh` once per container, then
  `python3 tools/shorts_build.py episodes/NN_slug/shorts.json --images DIR --audio DIR --outdir DIR`.
  Media stays out of git except the final MP4 and cover (section 5).
- **Video QC:** total < 40 s (target 28–36); no framing longer than ~4.5 s; look at the `_grid.jpg` and also
  extract and look at frames at 0.1 s, the card, the meaning line and the last second; captions don't cover a
  face; text is spelt right; the audio has no clipped words, long gaps or clicks; loudness ≈ −14 LUFS; content
  logic: everyday meaning right, the twist clear, ending agrees with the lesson.

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
  - Title, description (with hashtags) and the pinned-comment text from `script.md` "posting" (if a pinned
    comment can't be posted via the API, append it to the description).
  - `is_ai_generated: true`. **Original sound 100 %. No added music** for this account (not "Final Game
    Showdown"; that's the other channel's) unless the owner later sets one.
  - **Schedule:** 2 posts a day for this account, each 11–13 h after this account's previous post (random
    minute), in its own queue independent of the other account; never immediately.
  - Ask it to reply with the SocialEcho record id and the scheduled time, and later whether it went live.
  - The first message also explains this new arrangement and asks it to confirm it could download the files
    (sha256 match). If it can't reach raw.githubusercontent.com, ask what host it can reach.
- Record every handoff and reply in `publish_log.md` and `pipeline_state.md`. If the publication session
  doesn't answer within 24 h, send one reminder; after 48 h email the owner.

## 6. Low-credit warnings (email kennyzang@163.com, at most once a day each)
- SocialEcho points < 30: `python3 tools/socialecho.py points` (costs 1 point, so check once a day, in the
  scripts run).
- CompShare balance < 40 CNY: `python3 tools/compshare.py balance` (only if the COMPSHARE_* env vars exist;
  storage is still billed while the instance is stopped).
- DashScope: any "Arrearage", quota or 401/403 error on TTS/ASR → email the same day.

## 7. Scheduled tasks (create them once, into this session)
Create with `create_trigger` (default mode, fires into this session):
- "Idiom Ink scripts": `52 0 * * *`, prompt "[Idiom Ink scripts — scheduled run] Read idiom_ink/PRODUCER.md and
  pipeline_state.md, then do section 2 step 1 (write + send the next 2 image requests, low-credit checks), then
  an image check. Unattended: never ask for approval."
- "Idiom Ink image check": `23 */3 * * *`, prompt "[Idiom Ink image check — scheduled run] Read
  idiom_ink/PRODUCER.md and pipeline_state.md, then do section 2 step 2 (image replies → QC/redo/accept →
  voices → build → QC → handoff; check publication replies). Unattended: never ask for approval. If nothing new,
  finish with a one-line note."
This session needs the Gmail and Google Drive tools. If they are missing, say so in your reply (the owner sees
it) and stop; do not invent another delivery path.

## 8. Episodes and topics
- Done/out: 01–09 (GPU era; 07 東窗事發 and 08 班門弄斧 live; 09 守株待兔 made, publish status unknown — leave it).
  10 画蛇添足 = Shorts pilot, images requested 2026-10-19.
- Next: EP11, EP12 … from `FORMAT_SHORTS.md` §7 (absurd, visual twist; skip slow/abstract/dark ones). After
  that list, choose further well-known idioms with a clear story (public-domain classical sources, retold in our
  own words). Never repeat an idiom already done (check `topic_pool.md` and `episodes/`). Record each pick in
  `topic_pool.md`.
- Each episode folder `episodes/NN_slug/`: `script.md` (as EP10), `shorts.json`, `image_request.txt` (the
  email as sent). Keep 9 images, ≤ 3 recurring characters with a word-for-word continuity spec.
- After a few posts, use TikTok analytics the owner shares (or SocialEcho stats if available) per
  `FORMAT_SHORTS.md` §8.
