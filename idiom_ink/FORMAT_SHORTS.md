# Idiom Ink — Shorts format (v3, from episode 10)

Owner decisions (2026-10-19): **no GPU instance**; **videos under 30 s** with a faster pace, to raise the
play-through (完播) rate of a new account; images from **Grok** via email → Google Drive; voices from the owner's
**Alibaba Cloud** API. Look: **ink-wash manhua** (our ink-wash skin + manhua storytelling: full-bleed panels,
expressive faces). This file replaces the 70–85 s structure of `PRODUCTION_GUIDE.md` §4; that guide's content rules
still apply unless changed here.

## 1. What the format optimises

| Metric (TikTok analytics) | Target | If missed |
|---|---|---|
| 2-second retention | ≥ 60 % (red line 30 %) | fix the first 2 s: stronger image + hook text |
| Play-through (完播) | ≥ 30 % pass, 45 %+ good | find the second where viewers drop, cut it |
| Average watch time | ≥ 70 % of length | shorten / speed up the middle |
| Rewatches | > 0 (seamless loop) | make the last frame flow into the first |

Rules taken from the play-through playbook (`/root/.claude/uploads/...完播率...txt`, summarised):
first 2–3 s decide everything (result-first / suspense hook, no intro, no empty shots); **15–30 s** for a new
account; **one idea per video**; **no shot static > 3 s**; cut every pause; speech ~15 % faster than normal; big
high-contrast captions that pop phrase by phrase (most viewers watch muted); voice first, music under it; end with
one crisp line + a short comment question, never "like and follow"; 9:16 full-bleed, no black bars, subject centred.

## 2. Structure (target 22–27 s, hard cap 29.5 s)

| Time | Part | What happens |
|---|---|---|
| 0.0–2.0 | **Hook = result first** | The climax image + 2-line hook text on frame 1 + VO from frame 1 (no silence). A contradiction or twist ("He finished first… and still lost."). |
| 2.0–15 | **Story** | 5–6 stills, **1.6–2.6 s each**, every still moving (push/pull/pan), hard cuts with a whoosh. Narration only the plot beats that build to the twist. |
| 15–18 | **Idiom slam** | Big 成语 card (tone-coloured pinyin + literal gloss) appears with an impact sound; Mandarin VO says the idiom once, narrator gives the literal gloss. |
| 18–23 | **Meaning + modern use** | One-line meaning, then one modern, relatable example (still of a modern scene). |
| 23–25 | **Close + loop** | One-line punch / comment question on screen ("Ever 画蛇添足? 👇" lives in the caption, not burned in with emoji), last frame cuts back to the hook image. |

Moved out of the video (to keep < 30 s) and into the **pinned comment + description**: the character-by-character
breakdown and the 2nd example sentence (Chinese + pinyin + English). On screen we still show all 4 characters with
their glosses on the idiom card (read in 1 glance, not read aloud one by one).

## 3. Visual rules

- **Style: ink-wash manhua.** Bold confident black ink linework, flat muted washes (ochre, rust red, slate blue,
  moss green) on warm aged rice paper; expressive, slightly exaggerated faces (sweat drops, wide eyes, smug grins);
  dynamic angles; one full-bleed panel per image; no panel borders, no speech bubbles.
- **9:16, ≥ 1080×1920, full-frame, edge-to-edge**, never letterboxed (owner's rule, 2026-10-19). Every image
  request carries the FORMAT block and the full-bleed COMPOSITION RULES of `episodes/12_ke-zhou-qiu-jian/
  image_request.txt` (the current template). The builder cuts off any padding bands; landscape art (fallback
  only) is shown enlarged over a blurred copy of itself so the canvas is always illustration. Letterboxed or
  landscape delivery is a blocking problem: ask for a 9:16 re-render (counts as a redo round).
- **TikTok safe zones:** main subject inside the middle 60 % of the height; top 15 % (tabs) and bottom 25 %
  (caption/handle/music) low-detail; right 15 % (buttons) free of key action.
- **≤ 3 recurring characters**, each with a fixed costume/face spec repeated word for word in every request
  (silhouette + colour + one accessory make them distinguishable at thumbnail size).
- **No text in images** — no letters, calligraphy, seals, signatures, watermarks, UI text. All text is ours, burned
  in with our fonts (LXGW WenKai, Selawik, DejaVu Sans for pinyin).
- Image count: **9 per episode** (hook/climax, 5–6 story, idiom background, modern example). The hook reuses the
  climax image so the loop closes.

## 4. Text on screen (ASS, 1080×1920)

| Element | Style |
|---|---|
| Hook text | Selawik Bold 92 px, white, 9 px black outline, top centre (y≈330), 2 lines max, on frame 1 |
| Captions | Selawik Bold 84 px, white + 7 px black outline, one keyword highlighted yellow, **2–4 words per pop**, centred at y≈1180 (above TikTok's bottom UI) |
| Idiom card | 成语 in LXGW WenKai 220 px on a soft paper panel; pinyin 76 px tone-coloured (1 red · 2 orange · 3 green · 4 blue); gloss chips "画 draw · 蛇 snake · 添 add · 足 feet" 54 px |
| Meaning line | Selawik Bold 70 px under the card ("= ruining it by overdoing it") |
| Corner tag | 成语 48 px top-left, from second 2 onward (not on the hook frame) |

## 5. Audio

- **Narrator (English)**: one natural, warm, slightly playful voice from Alibaba Cloud (DashScope TTS), speed
  ≈ 1.15×, lines back-to-back (gap 0.06–0.12 s), loudness normalised to −14 LUFS.
- **Mandarin**: only the idiom (and only once); same provider, a clear standard-Mandarin voice.
- **SFX** (synthesised by our script, no licensing): whoosh on every cut (quiet), one impact "boom" on the idiom
  slam, a short "pop" when the meaning line lands. No music in the pilot (TikTok trending sounds can be added in the
  app later; any music must stay ≥ 12 dB under the voice).
- Every line is checked by transcription before editing (English and Mandarin), as before.
- **Fixed voices (verified 2026-10-19, keep for every episode):** TTS `qwen3-tts-flash` (DashScope native
  `/api/v1/services/aigc/multimodal-generation/generation`), English narrator voice **Ethan**
  (`language_type: English`), Mandarin voice **Cherry** (`language_type: Chinese`); speed-up 1.15× and
  silence trim (80 ms kept) done locally with ffmpeg. ASR `qwen3-asr-flash` (`/compatible-mode/v1/chat/completions`,
  no context prompt). Tool: `tools/alitts.py EPISODE/shorts.json --outdir DIR` (TTS → ASR check → retries).

## 6. Pipeline (no server)

Runs inside a Claude cloud session (ffmpeg + libass + Python are in the container).

1. **Script** → `episodes/NN_slug/script.md`: story beats, VO lines with target seconds, image list.
2. **Image request email** (Gmail, from/to kennytseng4@gmail.com), subject `[IDIOM-SCRIPT] EPNN · YYYY-MM-DD`,
   body = delivery rules + story context + character continuity + one block per image. Drive target:
   `Idiom-Ink-images/EPNN_YYYY-MM-DD/EPNN_I1.png …` (we create the folder first). Grok replies in the thread with
   `[IDIOM-IMAGES] EPNN · YYYY-MM-DD`. Redo requests: reply `[IDIOM-REDO] EPNN` listing image ids + reason.
3. **Image QC** (every image, full size): style, character continuity, hands/anatomy, extra or missing people,
   any text/marks, safe-zone composition. Redo at most twice, then re-plan the shot.
4. **Voices** via Alibaba Cloud, then ASR check of every line.
5. **Edit** with `tools/shorts_build.py <episode spec>` → `epNN_slug.mp4` (1080×1920, 30 fps, H.264, AAC, +faststart).
6. **QC**: length < 30 s; no shot static > 3 s; frame grid of hook, every caption type, the card, the ending;
   content logic (everyday meaning, twist clear, ending agrees with the lesson).
7. **Publish** via SocialEcho (`is_ai_generated: true`), caption + pinned comment from `posting.md`.

Daily automation (later): one routine per day does (a) assemble + QC + schedule the episodes whose images arrived,
(b) send image requests for the next day's episodes — a one-day lag so Grok has time. Routines need the **Gmail +
Google Drive connectors**, so they must be created in the claude.ai routines UI with those connectors on (routines
created from a session here get no connectors).

## 7. Topics for a new account

Prefer idioms whose story has an **absurd, visual twist** that a stranger gets in 2 seconds:
画蛇添足, 掩耳盗铃, 刻舟求剑, 自相矛盾, 杞人忧天, 狐假虎威, 叶公好龙, 拔苗助长, 买椟还珠, 南辕北辙, 指鹿为马,
滥竽充数, 削足适履, 邯郸学步. Skip slow, abstract or dark ones for now.

## 8. Iterate on data

After each post: read 2-second retention and the drop-off curve. < 30 % at 2 s → rewrite hooks (test result-first
vs question hooks). A cliff in the middle → that beat is too slow or unclear; cut it in the next episodes.
