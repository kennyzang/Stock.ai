# Pipeline state (producer keeps this current; newest first)

| EP | Idiom | Image request sent (UTC) | Gmail thread | Drive folder | Images | Redo rounds | Voices + ASR | Built + QC | Handed to publication | Scheduled / live |
|---|---|---|---|---|---|---|---|---|---|---|
| 12 | 刻舟求剑 | 2026-10-19 13:54 (re-sent 14:19) | 1a154728680561ae | EP12_2026-10-19 (1-Duuc97MvlPtai2cBL436gRGizsy5scf) | accepted 18:25 (ChatGPT 9/9, 1024×1536) | 0 | Jennifer, all pass ASR | ✅ 30.9 s, −15.2 LUFS, 8.5 MB | Publication 2026-10-19 18:40 (sha256 OK) | queued: 11–13 h after EP11 |
| 11 | 掩耳盗铃 | 2026-10-19 13:54 (re-sent 14:19) | 1a15472834836262 | EP11_2026-10-19 (18Yx7hxtpKfC4rXGOsyX4sA4Y4jKXIOds) | accepted 18:25 (ChatGPT 9/9, 1440×2560) | 0 | Jennifer, all pass ASR | ✅ 30.8 s, −14.9 LUFS, 8.7 MB | Publication 2026-10-19 18:40 (sha256 OK) | queued: ~2026-10-20 03:55 UTC (music 星漢倦歌) |
| 10 | 画蛇添足 (pilot) | 2026-10-19 13:16 | 1a1544e512a376a9 | EP10_2026-10-19 (18CjDMHd4jKOcPxdFDPoxvNTP2CiqKyOO) | accepted 15:50 (ChatGPT, 9/9 1024×1536) | 1 | Jennifer, all pass ASR | ✅ v2 30.6 s, −15.1 LUFS, 8.5 MB | Publication 2026-10-19 16:40 (releases/EP10) | ✅ live 2026-10-19 16:44 UTC: https://www.tiktok.com/@kingkingking8888/video/7698420789376224533 |

## Notes
- 2026-10-19: producer handed over from session_01UE4ArSjhTKBPtAHUBZxvXF. DashScope key verified reachable on
  dashscope.aliyuncs.com (HTTP 200 on /compatible-mode/v1/models); dashscope-intl returns 401.
- 2026-10-19: voices fixed: qwen3-tts-flash (Ethan EN / Cherry ZH) + qwen3-asr-flash; `tools/alitts.py` tested on
  EP10 lines B01_N, B05_N, B07_N, B08_M: all matched by ASR first try.
- 2026-10-19: scheduled tasks created (fire into session_012aqyfmSd4Tyh5Nfg1GvSZr): "Idiom Ink scripts"
  trig_01JJJfHHCP4RNZ9NRU8akTTW `52 0 * * *`; "Idiom Ink image check" trig_01QJzmhfB3kWNNbVkLyeUavh `23 */3 * * *`.
- 2026-10-19 13:54: EP11 掩耳盗铃 and EP12 刻舟求剑 image requests sent. EP10: no Grok reply yet, Drive folder empty (13:50).
- 2026-10-19 14:10: EP10 images checked: style/continuity good, no text; snake "feet" drawn as many tick-legs
  (tolerable); I3 snake already has feet, Old Wei has hair in I4 (tolerable). All frames are 1280×720 landscape
  art letterboxed into 1080×1920 with paper bands, so the art fills ~1/3 of the screen. Test build 24.2 s
  (18 MB, needs re-encode to ≤ 10 MB). GROK_SETUP.md updated: render portrait natively, never pad; owner to
  re-paste into Grok. Not handed off yet.
- 2026-10-19 14:21: owner rule: every image vertical 9:16, full-frame, edge-to-edge, no margins/bands. Sent EP10
  [IDIOM-REDO] round 1 (all 9 at native 9:16 + small fixes: 4 feet, bald Wei, modern jacket for Li) and re-sent
  EP11/EP12 requests with the FORMAT block in their threads. shorts_build.py now strips padding bands and never
  shows empty paper (landscape fallback = enlarged art over blurred copy); output capped ~2.8 Mbit/s (≤ 10 MB).
  If the EP10 redo isn't back by 2026-10-20 02:30 UTC, ship EP10 with the fallback layout.
- 2026-10-19: images switched from Grok to ChatGPT (Grok only renders 1280×720). Setup prompt now
  `IMAGE_SETUP.md` (3 runs/day, portrait 9:16 or 2:3 1024×1536, no padding); owner pastes it into ChatGPT.
  ChatGPT picks up the open EP10 redo and the EP11/EP12 requests from Gmail. Future request template FORMAT
  block accepts 2:3. (Note: the EP11/EP12 requests already sent ask for 9:16 ≥ 1080×1920; IMAGE_SETUP allows
  2:3 instead, so no re-send needed.)
- 2026-10-19 15:50: EP10 redo from ChatGPT accepted: full-frame 1024×1536, four feet, Wei bald, Li modern jacket,
  no text. Style is more detailed/painterly than the Grok set (consistent within the episode; it's now the series
  reference). Builder: added per-beat `hook_y`/`close_y` (EP10 hook and end line at y=1220 to clear faces), B07
  changed to push_in (focus 0.4,0.3) so Zhang's head isn't cropped. Final QC passed. Handed to publication
  (send_message 16:00) and review email sent to owner. EP11/EP12 still waiting for ChatGPT.
- 2026-10-19 16:30: owner: Ethan sounds Chinese-accented and v1 is too fast; duration < 40 s is fine. Changes:
  narrator Jennifer (American English) at 1.0× speed, inner pauses capped at 0.3 s, GAP 0.30 / TAIL 0.35 /
  M_PAUSE 0.35, framings up to ~4 s, cap 39.5 s, bitrate 2.1 Mbit/s. EP10 v2 = 30.6 s, 8.5 MB, −15.1 LUFS,
  all lines pass ASR. MiniMax speech voices are on the key's model list but "not activated".
- 2026-10-19: the EP10 v1 handoff went to "TikTok video publishing integration" (session_0137AuLDHVLLchAGLeDSoz1e)
  by mistake; it did nothing (no download, no SocialEcho call) and the owner told it to ignore us. The right
  session is "Publication", session_014Ei81gE1W46shqwc9gMyUz (PRODUCER.md §5 fixed).
- 2026-10-19 16:40: owner picked Jennifer. EP10 v2 committed to releases/EP10 (with posting.md) and handed to
  Publication (session_014Ei81gE1W46shqwc9gMyUz).
- 2026-10-19 16:41: Publication confirmed EP10: sha256 OK, SocialEcho record 555073, scheduled 16:57:49 UTC, music
  东方既白 at 18, pinned-comment text appended to the description; 270 points left. It will report the live link.
- 2026-10-19 17:05: EP10 live (posted 16:44 UTC, ~13 min before scheduled_at). Music audibility unverified (owner to check).
- 2026-10-19 18:25: EP11/EP12 images accepted (no redo). EP11 is lighter/more manga-like than EP10/EP12 and Gou
  looks younger than 30; I9 phone held upright (noted by ChatGPT); all tolerable. Fixed a builder bug: a calm
  plain sky at the top of a portrait image was mistaken for letterbox padding (EP11 I8 got the blurred fallback);
  bands now count only when both sides are flat and the art between is landscape. EP11 end line at y=1220.
  Both handed to Publication 18:40.
- 2026-10-19 18:38: Publication has EP11/EP12 queued (own timer; scheduled_at unreliable). Asked us to send each
  episode only about a day ahead; PRODUCER §5 updated.

