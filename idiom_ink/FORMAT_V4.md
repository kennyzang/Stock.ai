# Idiom Ink v4: "Idiom Quiz" template (fixed by the owner, 2026-10-25)

Code-animated shorts in the **red paper-cut look with quiz mechanics**, drawn by Claude in Canvas and rendered in
headless Chromium (`motion/`). No image service. Background and rationale: `FORMAT_V4_PROPOSAL.md`. Reference
episode: `motion/pilot_wang-yang-bu-lao/` (亡羊补牢).

## Fixed voice and scene order (every episode)
| Scene | Voice line | What the viewer sees |
|---|---|---|
| quiz | `Q1_N` "Guess what this Chinese idiom means:" | quiz card = frame 1 = cover: "IDIOM QUIZ #N", "What does this / Chinese idiom mean?" / "Pick A, B or C", 4 tiles (character + pinyin + cut clue + gloss), answers A/B/C |
| quiz | `Q_M` the idiom in Mandarin, once | **each tile lights up exactly while its syllable is spoken** (`TL.lines[Q_M].chars`) |
| quiz | `Q2_N` "A, B, or C?" | chips pulse A → B → C |
| lock | (story voice starts while they settle) | the three options **glide slowly and smoothly (~1.3 s) to the top-left**, shrinking into the bar that stays visible through the story |
| S1…Sn | one narrator line per beat | animated story, captions 2–4 words; optional ~0.6 s near-silence ("turn") before the twist |
| reveal | — | the right option lights up with a check seal; the wrong ones fall |
| slam | `R_M` the idiom in Mandarin | big idiom card, tiles slam per syllable, tone-coloured pinyin, glosses |
| answer | `A_N` **the correct option read aloud** (around 0:18) | the correct chip moves centre and grows |
| usage | `U_M` a short Mandarin saying/sentence with the idiom | speech bubble: Chinese + pinyin + big English (literal sense, not a repeat of the answer) |
| close | `C_N` "Did you get it right? A, B, or C?" | title + chips + "Comment A, B or C!" → hard cut back to the quiz frame (loop) |

Timing is generated, not hand-set: `motion/make_timeline.py EPISODE_DIR VO_DIR` (gaps, lock length, turn, answer
placement). Total target 24–27 s, hard cap 29.5 s.

## Rules
- The opening line never states what is already on screen ("four characters") and never teases vaguely ("one
  costly mistake"): it is the challenge itself, then the idiom's sound.
- Correct answer = the everyday meaning in plain English; one wrong option tempting, one funny. Shuffle which
  letter is correct across episodes (not always A).
- Chinese glyphs: Noto Serif SC Black subset per episode (fonts.googleapis.com `css2?family=Noto+Serif+SC:wght@900&text=`),
  checked at tile size (LXGW WenKai drew 亡 like 七). Pinyin: DejaVu Sans, tones coloured (1 red, 2 orange, 3 green, 4 blue).
- Voices: `tools/alitts.py` (Jennifer EN at ×1.12 via ffmpeg atempo, Cherry ZH), every line ASR-checked; syllable
  times for the idiom measured from the wav's energy envelope into `episode.json`.
- Sound: `motion/mix.py` (synthesized foley from `ev.json` + pentatonic pluck score, muted in the turn); master
  with `motion/build.sh` (−14 LUFS, peaks ≤ −1.5 dBFS, ~3 Mbit/s, ≤ 10 MB).
- Recurring cast (Wang the shepherd, Old Liu, …) and paper pieces are reused across episodes.
