#!/usr/bin/env python3
"""Fixed v4 "Idiom Quiz" timeline (owner-approved template, 2026-10-25).

  make_timeline.py EPISODE_DIR VO_DIR

Reads EPISODE_DIR/episode.json and the voice files VO_DIR/<id>.wav, writes EPISODE_DIR/timeline.json and
timeline.js (window.TL). Every episode uses the same order; only the story beats vary:

  quiz    Q1_N "Guess what this Chinese idiom means:"  ->  Q_M idiom in Mandarin (each character lights up as it is
          spoken: TL.lines[Q_M].chars)  ->  Q2_N "A, B, or C?"
  lock    the three options glide slowly (~1.3 s) into the top-left bar, where they stay during the story; the first
          story line starts while they settle
  story   S1..Sn (one line each); an optional near-silence ("turn", ~0.6 s) before the beat named in episode.json
  reveal  the right option lights up, the others fall
  slam    R_M idiom in Mandarin on the big card (chars timed again)
  answer  A_N the correct option read aloud ("It's never too late to fix it."), lands ~18 s
  usage   U_M a short Mandarin sentence/saying with the idiom, pinyin + big English on screen
  close   C_N "Did you get it right? A, B, or C?"  ->  loop: hard cut back to the quiz frame

episode.json: {"story": ["S1_N", ...], "turn_before": "S3_N" | null,
               "syllables": [[t0, t1] x 4] (seconds inside the idiom wav; measure from its energy envelope),
               "usage_zh": "亡羊补牢，为时未晚。"}
"""
import json, subprocess, sys
from pathlib import Path

GAP, STORY_GAP, TURN, REVEAL, SLAM_LEAD, LOCK, LOOP = .12, .15, .6, .5, .2, 1.3, .35


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


def main():
    ep, vo = Path(sys.argv[1]), Path(sys.argv[2])
    E = json.loads((ep / "episode.json").read_text())
    text = {l["id"]: l["text"] for b in json.loads((ep / "lines.json").read_text())["beats"] for l in b["lines"]}
    text["Q_M"] = text["R_M"]
    text["U_M"] = E["usage_zh"]  # spoken by voice M; checked by ASR separately (alitts compares M lines to the idiom)
    syl = E["syllables"]
    lines, sc, t = [], {}, .10

    def add(i, gap, chars=False):
        nonlocal t
        d = dur(vo / f"{i}.wav")
        li = {"id": i, "t0": round(t, 3), "t1": round(t + d, 3), "text": text[i]}
        if chars:
            li["chars"] = [[round(t + a, 3), round(t + b, 3)] for a, b in syl]
        lines.append(li); t += d + gap
        return li

    add("Q1_N", GAP); add("Q_M", GAP, chars=True); q2 = add("Q2_N", 0)
    lock0 = q2["t1"] - .45                      # options start to glide on "...or C?"
    sc["quiz"] = [0, lock0]; sc["lock"] = [lock0, lock0 + LOCK]
    t = lock0 + .75                             # first story line while the options settle
    story = []
    for k, i in enumerate(E["story"]):
        if i == E.get("turn_before"):
            sc["turn"] = [t - STORY_GAP + .05, t + TURN]; t += TURN
        story.append(add(i, STORY_GAP))
    starts = [sc["lock"][1]] + [li["t0"] - .07 for li in story[1:]]
    for k, li in enumerate(story):
        end = starts[k + 1] if k + 1 < len(story) else li["t1"] + STORY_GAP
        if "turn" in sc and k + 1 < len(story) and story[k + 1]["id"] == E.get("turn_before"):
            end = sc["turn"][0]; sc["turn"][1] = starts[k + 1]
        sc[f"S{k + 1}"] = [starts[k], end]
    r0 = story[-1]["t1"] + STORY_GAP; sc["reveal"] = [r0, r0 + REVEAL]
    t = r0 + REVEAL + SLAM_LEAD
    sl = add("R_M", .12, chars=True); sc["slam"] = [r0 + REVEAL, sl["t1"] + .06]
    an = add("A_N", .2); sc["answer"] = [sl["t1"] + .06, an["t1"] + .1]
    us = add("U_M", .15); sc["usage"] = [an["t1"] + .1, us["t1"] + .1]
    cl = add("C_N", 0); sc["close"] = [us["t1"] + .1, cl["t1"] + .15]
    sc["loop"] = [cl["t1"] + .15, cl["t1"] + .15 + LOOP]
    T = round(sc["loop"][1], 3)
    scenes = {k: {"t0": round(a, 3), "t1": round(b, 3)} for k, (a, b) in sc.items()}
    tl = {"DUR": T, "lines": lines, "scenes": scenes}
    (ep / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    (ep / "timeline.js").write_text("window.TL = " + json.dumps(tl, ensure_ascii=False) + ";\n")
    print(f"DUR {T:.2f} s; answer read at {an['t0']:.2f} s")
    for k, v in scenes.items():
        print(f"  {k:8s} {v['t0']:6.2f} - {v['t1']:6.2f}")


if __name__ == "__main__":
    main()
