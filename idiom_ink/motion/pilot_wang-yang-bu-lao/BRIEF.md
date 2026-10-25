# Pilot brief: 亡羊补牢 · quiz mechanics in the red paper-cut look (v4)

Owner's choice: the quiz mechanics of the game-show sample, drawn in the red paper-cut look of
`motion/style_samples/papercut-red/page.html` (reuse its helpers: grain, wob/cut/crescent/saw cuts, piece/finish/put,
textPiece, banner, tuanhua, cornerFlower, scraps, stars). Proposal and structure: `idiom_ink/FORMAT_V4_PROPOSAL.md`.

**Output:** `page.html` in this folder (one self-contained Canvas 2D page, 1080×1920) that loads `timeline.js`
(`window.TL`: DUR, lines with t0/t1/text, scenes with t0/t1). Every time below comes from `TL`; never hard-code
times that the timeline defines. Contract: `window.DUR = TL.DUR`, `window.render(t)` (deterministic, seeded),
`window.READY`, plus `window.EV = [{t, type, gain?}]` for every sound event (the mixer reads it). Event types:
`pop` (paper piece lands), `whoosh` (fast move or cut), `wipe` (paper wipe transition), `tick` (quiz clock),
`knock` (hammer), `ding` (right answer), `drop` (wrong answers fall), `boom` (idiom slam), `baa` (a sheep bleats),
`wolf` (low growl in the dark), `rustle` (paper flutter), `stamp` (seal/tile slam).

**Fonts:** load from files with @font-face, not the scratchpad CSS: `../../tools`-independent copies live in
`fonts/` in this folder (copy the OFL woff2s you use there, e.g. Lilita One from lemo-opuscar core/fonts; their
OFL licence travels with them). LXGW WenKai and DejaVu Sans are system fonts (use by name).

**Performance:** ~710 frames are rendered with `node ../render.mjs page.html video out.mp4 30`. Build every paper
piece ONCE (cache) and only transform/place pieces per frame. Characters are cut-out puppets: each limb/head is its
own cached piece placed with rotation about a pivot. Characters and props move **on twos (12 fps stepping)**,
camera moves and the background stay smooth.

## Cast (fixed for the series; reuse later)
- **WANG, the shepherd:** middle-aged, round face, thin black mustache, wide round straw hat (cream paper with
  cut weave), rust-red short jacket, brown trousers, straw sandals. Very readable expressions: puzzled, lazy-smug
  shrug, shocked (wide eyes, O mouth, sweat drop), relieved smile.
- **OLD LIU, the neighbor:** tall, thin, slate-blue robe, long white beard, walking stick; urgent pointing.
- **SHEEP:** chunky cream paper sheep with cut curl patterns, black faces/legs, cute. 4 at the start.
- **WOLF:** never fully shown: two gold eyes and a dark grey silhouette/tail at the hole.
- **THE PEN:** a woven wicker/wooden paling fence in a curve, with one ragged HOLE (wool tufts caught on it).

## Scenes (names = `TL.scenes` keys)
1. **quiz** — frame 1 = cover = loop target. Must be complete and readable at t = 0 (no build-up from empty).
   Layout like the papercut Frame A: "IDIOM QUIZ #1" small badge; "4 characters." / red banner "1 costly mistake." /
   gold "Guess the meaning ↓"; 2×2 red-paper tiles 亡 羊 补 牢 with pinyin + cut clue + gloss:
   亡 wáng "lose" (a sheep outline made of dashed cuts = missing), 羊 yáng "sheep" (sheep head), 补 bǔ "mend"
   (needle and thread), 牢 láo "pen" (little fence). Answer chips:
   **A) It's never too late to fix it · B) Always count your sheep · C) Never trust your neighbor**.
   Motion: idle breathing, scraps drift, arrow bobs; while "Four characters" is spoken each tile does a quick
   stamp pulse (`stamp` events), chips pulse once at "Can you guess" (`tick`).
2. **lock** — the three chips shrink and fly into a slim persistent bar at y ≈ 300–380 ("A · B · C" mini chips with
   short labels), tiles fold away; a red sawtooth paper wipe opens S1 (`wipe`). The bar stays visible through S1–S4.
3. **S1** — dawn (lighter indigo + pale paper sun). Wide: the pen with 3 sheep and one dashed-outline empty spot;
   Wang counts, finger tapping each sheep (`baa` once), then scratches his head ("?"). Camera pushes in to the
   ragged hole with wool tufts when "hole in the pen" is spoken (find the word time proportionally in the line).
4. **S2** — two shots. First half ("Fix it!"): Old Liu points urgently at the hole, stick raised. Second half:
   cut (`whoosh`) to Wang, close, lazy shrug with palms up, smug half-closed eyes, turning away.
5. **wolf_silence** — near-silence beat before the turn: the sky drops to night, two gold eyes open in the hole
   (`wolf`, low). Hold. No captions.
6. **S3** — morning: Wang shocked (punch-in on his face at "another one"), now 2 sheep + 2 dashed empty spots,
   a grey wolf tail vanishing through the hole.
7. **S4** — the native move: Wang hammers (3–4 `knock`s) and a cut-paper plank patch UNFOLDS over the hole like
   a paper-cut opening; the sheep cheer (`baa`), the wolf eyes in the dark turn away; Wang wipes his brow, smiles.
8. **reveal** — the top bar drops back to the three big chips mid-screen; **A** lights gold with a cut-paper
   check seal (`ding`), B and C fall off screen tumbling (`drop`).
9. **slam** — the idiom card: four big red-paper tiles 亡 羊 补 牢 slam in one by one (`stamp` each, `boom` on
   the first), pinyin **wáng yáng bǔ láo** in tone colours (2nd tone orange #F08C1E, 3rd tone green #2E9A3C; make
   them readable on the card: cream panel or light outline), gloss "lose · sheep · mend · pen". The Mandarin voice
   says the idiom here.
10. **usage** — card moves up and shrinks; a cut-paper speech bubble pops (`pop`): **亡羊补牢，为时未晚。** with
    pinyin *wáng yáng bǔ láo, wéi shí wèi wǎn* and the big English line **"Mend the pen now: it's not too late!"**
    (this is the meaning; it must be large and readable — the narrator doesn't say it).
11. **close** — "Did you get it right?" big, the A/B/C chips again with a small "comment A, B or C" hint.
12. **loop** — hard cut to exactly the quiz frame (render(TL.scenes.loop.t0) must look like render(0)).

## Captions (S1–S4 and close; not in quiz, wolf_silence, slam, usage)
From `TL.lines` text: chunks of 2–4 words, timed proportionally by character count across t0..t1, each chunk pops
(12 fps step). Style like the papercut sample caption: cream Lilita One ≥ 76 px on a red banner, keywords gold:
missing, hole, Fix it!, bother?, another, fixed, never. Band y ≈ 1150–1320; never over a face.

## Layout rules
Safe zones: key action in y 380–1540; top 15 % and bottom 25 % low detail; nothing important at x > 920.
Every shot changes framing; at least 4 distinct camera moves (push, pull, pan, punch-in). No shot static > 2.5 s.

## Check before handing back
Render stills every 1 s (`node ../render.mjs page.html still T out.png`) and LOOK at them: faces, hands, the hole
and patch readable, captions not covering faces, text inside safe zones, the loop frame equals frame 0. Fix in one
round, then render the video: `node ../render.mjs page.html video /tmp/claude-0/-home-user-Stock-ai/bcb7fc1b-9dba-5aaf-9469-b8b3664e0f24/scratchpad/pilot/video.mp4 30`.
Also write `ev.json` (window.EV) next to page.html: `node -e` or a tiny page dump is fine.
Report: what's done, stills you checked, anything weak.
