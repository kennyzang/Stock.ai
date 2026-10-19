# Pipeline state (producer keeps this current; newest first)

| EP | Idiom | Image request sent (UTC) | Gmail thread | Drive folder | Images | Redo rounds | Voices + ASR | Built + QC | Handed to publication | Scheduled / live |
|---|---|---|---|---|---|---|---|---|---|---|
| 12 | 刻舟求剑 | 2026-10-19 13:54 | 1a154728680561ae | EP12_2026-10-19 (1-Duuc97MvlPtai2cBL436gRGizsy5scf) | waiting for Grok | 0 | – | – | – | – |
| 11 | 掩耳盗铃 | 2026-10-19 13:54 | 1a15472834836262 | EP11_2026-10-19 (18Yx7hxtpKfC4rXGOsyX4sA4Y4jKXIOds) | waiting for Grok | 0 | – | – | – | – |
| 10 | 画蛇添足 (pilot) | 2026-10-19 13:16 | 1a1544e512a376a9 | EP10_2026-10-19 (18CjDMHd4jKOcPxdFDPoxvNTP2CiqKyOO) | delivered 14:00 letterboxed; REDO round 1 sent 14:21 (all 9, native 9:16) | 1 | done, all pass ASR | test build 24.2 s; letterbox issue, see notes | – | – |

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
