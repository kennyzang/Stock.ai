# Idiom Ink v4 proposal: code-animated "Guess the Idiom" shorts (2026-10-25)

Status: proposal; the owner picks a style. Until then the producer keeps the v3 image format running.

## Why v3 stalls at ~500 views
- **Nothing to do for the viewer.** The video narrates a stranger's story over stills, so there's no reason to stay.
  TikTok's first test pool (~300–500 viewers) leaves early, and the video is never pushed further.
- **The payoff comes late.** The idiom and its meaning arrive at ~15 s, after most viewers have already decided.
- **Too long.** Recent episodes run 31–37 s, over the 30 s cap in FORMAT_SHORTS.md.
- **No series identity.** Every episode looks like the same generic AI illustration, so nothing becomes recognisable.
- **Weak comment prompt.** "Ever done that?" asks for a confession; few people answer.

## New structure (20–24 s, hard cap 25 s)
| Time | Beat | What happens |
|---|---|---|
| 0–1.5 s | **Quiz card = frame 1 = cover** | The 4 characters, each with a drawn picture clue + gloss, and "4 characters. 1 crazy story. Guess the meaning", with A/B/C options. VO: "Four characters, one crazy story. Can you guess it?" This opens a question the viewer wants closed. |
| 1.5–3 s | **Lock in** | The options shrink to a bar along the top and stay there while the story plays, so the viewer keeps their guess in mind. A ticking sound. |
| 3–14 s | **Story in 4 animated beats** | About 2.5 s per beat, one action per beat, characters actually moving (not stills), a sound on every action, 2–4-word captions. |
| 14–17 s | **Reveal** | The right option flashes, the wrong ones drop away, then the idiom slams in: tone-coloured pinyin and the Mandarin voice once. |
| 17–21 s | **Say it like a native** | One modern sentence as a chat bubble: Chinese + pinyin + English (e.g. 我改了十遍简历，结果画蛇添足了). This is the "save this" value. |
| 21–23 s | **Loop + comment** | "Did you get it right? A, B or C?" Hard cut back to the quiz card, so the loop invites a rewatch. |

Other levers:
- **Comment bait that's easy to answer:** a single letter. Make wrong answer B tempting or funny. Pin a comment with the answer.
- **Recurring cast:** the same two mascots (e.g. "Zhang & Li") play every role in every episode. It's cheap to build and makes viewers recognise the series.
- **Series card:** "Idiom Quiz #N" on every cover, so a profile visitor sees a set to binge.
- **Test on data:** post 6 v4 episodes and compare 2-s retention, average watch time and completion with the last 6 v3 posts.
  Alternatives to test later: "What it says vs what it means" (literal joke first), and "3 ways natives use it".

## Visual: drawn in code by Claude (no image service)
The approach of `lemomo-ai/lemo-opuscar` and the Opus 5.5 video list: each episode is a page with `render(t)`
(Canvas 2D). It's rendered frame by frame in headless Chromium (`motion/render.mjs`), voiced through DashScope, and
mixed with ffmpeg. Characters are reusable code rigs, so after the first episode a new idiom means new poses and
props, not new characters. There's no image round-trip, and ChatGPT/Grok are no longer needed.

Style samples (same idiom, Frame A = quiz hook, Frame B = story climax), sources in `motion/style_samples/<style>/page.html`,
comparison sheets `motion/style_samples/style_samples_A.jpg` and `_B.jpg`:

| # | Style | For | Against | Effort |
|---|---|---|---|---|
| 1 | Game-show quiz | boldest and most readable; the quiz is the star; mascots are very reusable | generic, little Chinese flavour | low |
| 2 | Red paper-cut | striking on a phone, unmistakably Chinese, festive | each pose hand-placed; same look scene to scene | medium |
| 3 | Mid-century cartoon | best comedy and faces; warm | gentler hook energy | low–medium |
| 4 | Pixel RPG "Idiom Quest" | gamified series hook ("NEW IDIOM UNLOCKED") | may skew young/gimmicky; sprite animation work | medium–high |
| 5 | Shadow puppet | most distinctive and authentic | calm; new jointed puppet per character | high |
| 6 | Ink wash | keeps the "Idiom Ink" brand | quietest; needs motion to stay lively | medium |

Sample frames load fonts from the session scratchpad (lemo-opuscar `core/fonts`, OFL). A production page must
bundle its fonts.
