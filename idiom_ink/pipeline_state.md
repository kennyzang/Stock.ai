# Pipeline state (producer keeps this current; newest first)

| EP | Idiom | Image request sent (UTC) | Gmail thread | Drive folder | Images | Redo rounds | Voices + ASR | Built + QC | Handed to publication | Scheduled / live |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 画蛇添足 (pilot) | 2026-10-19 13:16 | 1a1544e512a376a9 | EP10_2026-10-19 (18CjDMHd4jKOcPxdFDPoxvNTP2CiqKyOO) | waiting for Grok | 0 | – | placeholder test only (25.8 s) | – | – |

## Notes
- 2026-10-19: producer handed over from session_01UE4ArSjhTKBPtAHUBZxvXF. DashScope key verified reachable on
  dashscope.aliyuncs.com (HTTP 200 on /compatible-mode/v1/models); dashscope-intl returns 401.
- 2026-10-19: voices fixed: qwen3-tts-flash (Ethan EN / Cherry ZH) + qwen3-asr-flash; `tools/alitts.py` tested on
  EP10 lines B01_N, B05_N, B07_N, B08_M: all matched by ASR first try.
