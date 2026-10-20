#!/usr/bin/env python3
"""Write an Idiom Ink episode's script.md, shorts.json and image_request.txt from episodes/NN_slug/episode.json.

Usage:  make_episode.py episodes/NN_slug/episode.json
episode.json keys (see episodes/13_*/episode.json for a full example):
  n, slug, date (request date, YYYY-MM-DD), folder (Drive subfolder id, create it first), idiom, py, pinyin, gloss,
  literal, meaning_long, source, cover, hook, meaning, close, story, continuity[4], scenes[9] = [title, text],
  lines[11] (B01..B07 story, B08 gloss, B09 meaning, B10 modern, B11 close), hl[11] (null or words), title, desc, pinned
The image request copies HOW TO DELIVER / STYLE from episodes/10_hua-she-tian-zu/image_request.txt and uses the
full-frame FORMAT + COMPOSITION blocks below (owner rule, 2026-10-19). Then: check every line with tools/alitts.py,
send image_request.txt's body as the [IDIOM-SCRIPT] email, and record the thread id.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_t = (ROOT / "episodes/10_hua-she-tian-zu/image_request.txt").read_text()
TPL = _t[_t.index("IDIOM INK SHORTS — IMAGE REQUEST"):]
MOVES = ["push_in", "pull_out", "pan_right", "push_in", "push_in_more", "pan_left", "punch"]
FORMAT = 'FORMAT (most important; applies to every image)\nVertical 9:16 aspect ratio, full-frame composition, edge-to-edge illustration that completely fills the canvas: no top or bottom margins, no borders, no letterbox or padding bands, no empty brown or paper-coloured space. Cinematic framing: wide shots unless a scene asks for a close-up. Render natively in portrait: 9:16 (--ar 9:16, at least 1080x1920) if your tool offers it, otherwise 2:3 portrait (1024x1536); keep faces and key action inside the central 85% of the width. Never render landscape or square, and never pad, upscale or stretch an image into a vertical frame.'
COMPOSITION = 'COMPOSITION RULES (the video is viewed on phones with TikTok buttons on top)\n- The illustration runs to all four edges. Put the main subject in the middle 60% of the height; the top 15% and bottom 25% still contain the scene (wall, sky, ground), just with less detail, because captions go there. Keep key action out of the right-hand 15% (TikTok buttons).\n- Characters large and readable at thumbnail size; faces clearly visible unless said otherwise.\n- Only the people listed for each image. Correct hands (5 fingers), no extra limbs, no duplicate people.'


def section(name, nxt):
    return TPL[TPL.index(name):TPL.index(nxt)]


def build(e):
    n, ep = e["n"], f"EP{e['n']}"
    d = ROOT / f"episodes/{n}_{e['slug']}"
    DATE = e["date"]
    d.mkdir(parents=True, exist_ok=True)
    L = e["lines"]
    beats = []
    for i in range(7):
        b = {"id": f"B{i+1:02d}", "img": f"{ep}_I{i+1}.png", "move": MOVES[i], "focus": [0.5, 0.48 if i == 0 else 0.5]}
        if i == 0:
            b["hook"] = e["hook"]
        li = {"id": f"B{i+1:02d}_N", "voice": "N", "text": L[i]}
        if e["hl"][i]:
            li["hl"] = e["hl"][i]
        b["lines"] = [li]
        beats.append(b)
    beats.append({"id": "B08", "img": f"{ep}_I8.png", "move": "push_in", "focus": [0.5, 0.7], "card": True, "nosplit": True,
                  "lines": [{"id": "B08_M", "voice": "M", "text": e["idiom"] + "。"}, {"id": "B08_N", "voice": "N", "text": L[7]}]})
    beats.append({"id": "B09", "img": f"{ep}_I8.png", "move": "push_in_more", "focus": [0.5, 0.7], "meaning": e["meaning"],
                  "lines": [{"id": "B09_N", "voice": "N", "text": L[8]}]})
    beats.append({"id": "B10", "img": f"{ep}_I9.png", "move": "push_in", "focus": [0.5, 0.5],
                  "lines": [dict({"id": "B10_N", "voice": "N", "text": L[9]}, **({"hl": e["hl"][9]} if e["hl"][9] else {}))]})
    beats.append({"id": "B11", "img": f"{ep}_I1.png", "move": "pull_out", "focus": [0.5, 0.48], "close": e["close"],
                  "lines": [{"id": "B11_N", "voice": "N", "text": L[10]}]})
    spec = {"out": f"ep{n}_{e['slug']}.mp4", "idiom": e["idiom"], "pinyin": e["pinyin"], "gloss": e["gloss"],
            "cover_text": e["cover"], "beats": beats}
    (d / "shorts.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n")

    gl = " · ".join(f"{a} {b}" for a, b in e["gloss"])
    names = ["climax", *[s[0] for s in e["scenes"][1:7]], "card", "modern"]
    rows = []
    for i in range(7):
        rows.append(f"| {i+1} | I{i+1} {e['scenes'][i][0]} | {'Hook text: **' + e['hook'].replace(chr(92)+'N', ' / ') + '**' if i == 0 else 'captions'} | \"{L[i]}\" |")
    rows += [f"| 8 | I8 | **idiom card** {e['idiom']} + {e['py']} + {gl} | ZH: \"{e['idiom']}。\" then \"{L[7]}\" |",
             f"| 9 | I8 (push-in) | meaning line **{e['meaning']}** | \"{L[8]}\" |",
             f"| 10 | I9 modern | captions | \"{L[9]}\" |",
             f"| 11 | I9 → cut to I1 | end line **{e['close']}** | \"{L[10]}\" |"]
    chars = "\n".join("| " + c[2:].split(":", 1)[0] + " | " + c[2:].split(":", 1)[1].strip() + " |" for c in e["continuity"])
    (d / "script.md").write_text(f"""# Episode {n} — {e['idiom']} {e['py']} (Shorts format, see FORMAT_SHORTS.md)

- **Everyday meaning:** {e['meaning_long']}.
- **Literal:** {e['literal']}.
- **Source:** {e['source']}
- **Target length:** ~30 s (cap 39.5 s).

## Characters and props (repeat these exact specs in every image request)
| Who | Spec |
|---|---|
{chars}

## Beats, voice-over and images
| # | Image | On screen | VO (EN unless marked) |
|---|---|---|---|
{chr(10).join(rows)}

Content check: everyday meaning ✔ · the twist is the hook ✔ · metaphor explicit ("{e['literal']}") ✔ ·
ending agrees with the lesson ✔ · no real people ✔.

## posting (draft)
- Title: {e['title']}
- Description: {e['desc']}
  #learnchinese #chineseidioms #mandarin #chengyu #learnmandarin #chineselanguage
- Pinned comment: {e['pinned']}
""")

    deliver = section("HOW TO DELIVER", "STYLE (").replace("2026-10-19", DATE).replace("EP10", ep)
    deliver = deliver.replace("18CjDMHd4jKOcPxdFDPoxvNTP2CiqKyOO", e["folder"])
    style = section("STYLE (", "COMPOSITION RULES").replace(
        "This episode's images become the style reference for all later episodes, so please lock the look carefully.\n",
        "Match the look of the earlier Idiom Ink episodes (EP10 画蛇添足) exactly.\n").replace(
        "lots of calm empty space", "calm, uncluttered backgrounds that still fill the whole frame")
    fmt, comp = FORMAT + "\n\n", COMPOSITION + "\n\n"
    scenes = "\n".join(f"{ep}_I{i+1} — {t}\n{s}\n" for i, (t, s) in enumerate(e["scenes"]))
    body = (f"IDIOM INK SHORTS — IMAGE REQUEST\nEPISODE: {ep}\nDATE: {DATE}\n"
            f"IDIOM: {e['idiom']} ({e['py']}) — \"{e['literal']}\" = {e['meaning_long']}\n"
            "SERIES: Idiom Ink | Chinese Idioms (TikTok @kingkingking8888). A 30-second vertical short: still images, cut fast, with narration.\n"
            f"IMAGES NEEDED: 9 ({ep}_I1 ... {ep}_I9)\n\n{fmt}{deliver}{style}{comp}"
            f"STORY CONTEXT (so the images make sense)\n{e['story']}\n\n"
            "CONTINUITY (keep these exactly the same in every image they appear in)\n" + "\n".join(e["continuity"]) +
            f"\n\nSCENES\n\n{scenes}\nTHANK YOU. Any question: reply in this thread with subject starting [IDIOM-QUESTION] {ep}.\n")
    subj = f"[IDIOM-SCRIPT] {ep} · {DATE}"
    (d / "image_request.txt").write_text(f"Subject: {subj}\nFrom/To: kennytseng4@gmail.com   (to send {DATE}; fill in the Gmail thread id after sending)\n\n{body}")
    print(d, subj)



if __name__ == "__main__":
    e = json.loads(Path(sys.argv[1]).read_text())
    assert len(e["lines"]) == 11 and len(e["hl"]) == 11 and len(e["scenes"]) == 9, "need 11 lines/hl and 9 scenes"
    build(e)
