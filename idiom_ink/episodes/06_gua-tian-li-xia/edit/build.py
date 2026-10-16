"""Assemble episode 06 (瓜田李下) in the 70-second structure: hook → story → quote → payoff → 2 examples → loop.

Copied from episode 05. Runs ON the GPU server (cloud sessions can't SSH): voices come from MOSS-TTS directly
via tools/moss_local.py, fonts are the open replacements installed in ~/.fonts/idiom_ink
(LXGW WenKai for LXGW WenKai, Selawik for Segoe UI; DejaVu Sans for pinyin, Selawik lacks ǎ ǐ ǒ ǔ ǚ).

Run:  python build.py          (ComfyUI must have freed its VRAM before the voices are generated)
"""

import json
import subprocess
from pathlib import Path

EP = Path(__file__).resolve().parent.parent
CLIPS = EP / "clips"
WORK = Path(__file__).resolve().parent / "work"
OUT = EP / "ep06_gua-tian-li-xia.mp4"
WORK.mkdir(exist_ok=True)

W, H, FPS = 1080, 1920, 24
PAPER = "0xE9DEC6"

CHARACTER_VOICES = set()
# The breakdown is read character by character: tight gaps so it stays quick.
FAST = {"P2": dict(gap=0.10, m_pause=0.05)}

CLIP = {
    "H1": "H1_hook.mp4", "S02": "S02_road.mp4", "S03": "S03_strap.mp4", "S04": "S04_tie.mp4",
    "S05": "S05_farmer_sees.mp4", "S06": "S06_run.mp4", "S07": "S07_hands.mp4", "S08": "S08_wind_v2.mp4",
    "S09": "S09_cap.mp4", "S10": "S10_granny.mp4", "S11": "S11_sunset_v2.mp4", "S11q": "P1_still.mp4",
    # H3's P1 grew a glowing sun + lens flares: a slow zoom on the clean style frame instead
    "P1": "P1_still.mp4", "P2": "P1_still.mp4",
    # FLUX stills + slow zoom: two H3 rounds of the cat gave ink blobs, fake calligraphy, a see-through desk
    "U1": "U1_still.mp4", "U2": "U2_still.mp4",
    "L1": "H1_hook.mp4",
}
# from the clip review (contact sheets): skip standing/empty openings and identity glitches, cut before artifacts
CLIP_START = {"H1": 1.5, "L1": 1.5, "S02": 0.8, "S03": 2.2, "S04": 1.6, "S05": 1.5, "S07": 1.2, "S08": 2.0,
              "S09": 2.9, "S10": 2.5}
CLIP_MAX = {"S06": 3.8}
# quote → payoff → breakdown play as ONE continuous slow zoom: each starts where the previous one ended
CHAIN = ["S11q", "P1", "P2"]
PINGPONG = set()
STORY = set()
TITLE_CARD = None
SFX_MUTE = {"U1", "U2"}

IDIOM = "瓜田李下"
IDIOM_PY = [("guā", 1), ("tián", 2), ("lǐ", 3), ("xià", 4)]
BREAKDOWN = [("瓜", "melon"), ("田", "field"), ("李", "plum"), ("下", "under")]
GLOSS_X = (175, 410, 650, 890)
MEANING = "= a spot where innocent acts look guilty"
HOOK_TEXT = "He didn't steal anything…\\Nso why call him a thief?"
# The old poem the idiom comes from, as clean on-screen text (never drawn by the video model).
QUOTE_SHOT = "S11q"
QUOTE = ("瓜田不纳履，李下不正冠", "Guā tián bù nà lǚ, lǐ xià bù zhèng guān.")
# The metaphor made concrete: what he did vs. what others saw.
LABELS = {"S04": "innocent", "S05": "looks guilty", "S09": "innocent", "S10": "looks guilty"}

# Segment = (shot, [(voice, spoken text, subtitle or None)], min_seconds)
SEGMENTS = [
    ("H1", [("N", "He didn't steal a thing. So why did the whole village call him a thief?", None)], 3.0),
    ("S02", [("N", "A young scholar was walking home on a hot summer day.", None)], 0),
    ("S03", [("N", "His sandal strap broke, right next to a melon field.", None)], 0),
    ("S04", [("N", "So he bent down to fix it.", None)], 0),
    ("S05", [("N", "But the farmer only saw a man crouching in his melons.", None)], 0),
    ("S06", [("N", "He ran over, shouting: thief! Thief!", "He ran over, shouting: “Thief! Thief!”")], 0),
    ("S07", [("N", "The scholar showed his empty hands. The farmer didn't believe him.", None)], 0),
    ("S08", [("N", "Later, the wind knocked his hat crooked, right under a plum tree.", None)], 0),
    ("S09", [("N", "He reached up to fix it.", None)], 0),
    ("S10", [("N", "And an old woman cried: he's picking my plums!", "And an old woman cried: “He's picking my plums!”")], 0),
    ("S11", [("N", "That night, he remembered an old poem.", None)], 0),
    ("S11q", [("M", "瓜田不纳履，李下不正冠。", ""),
              ("N", "In a melon field, don't tie your shoe. Under a plum tree, don't fix your hat.",
               "“In a melon field, don't tie your shoe. Under a plum tree, don't fix your hat.”")], 0),
    ("P1", [("N", "That's the saying…", None), ("M", "瓜田李下。", "")], 0),
    ("P2", [("M", "瓜。", ""), ("NF", "Melon.", None), ("M", "田。", ""), ("NF", "Field.", None),
            ("M", "李。", ""), ("NF", "Plum.", None), ("M", "下。", ""), ("NF", "Under.", None),
            ("N", "Stay out of spots where innocent things look guilty.", None)], 0),
    ("U1", [("M", "你表弟来应聘，你最好回避，瓜田李下。", ""),
            ("N", "Your cousin applied for the job? Stay out of the hiring.",
             "“Your cousin applied for the job? Stay out of the hiring.”")], 0),
    ("U2", [("M", "考试时别碰手机，哪怕只看时间，瓜田李下嘛。", ""),
            ("N", "Don't touch your phone in an exam. Not even to check the time.",
             "“Don't touch your phone in an exam. Not even to check the time.”")], 0),
    ("L1", [("N", "Being innocent isn't enough. Sometimes you have to look innocent, too.", None)], 0),
]
EXAMPLES = {
    "U1": ("你表弟来应聘，\\N你最好回避，\\N瓜田李下。", "Nǐ biǎodì lái yìngpìn,\\Nnǐ zuìhǎo huíbì,\\Nguā tián lǐ xià."),
    "U2": ("考试时别碰手机，\\N哪怕只看时间，\\N瓜田李下嘛。", "Kǎoshì shí bié pèng shǒujī,\\Nnǎpà zhǐ kàn shíjiān,\\Nguā tián lǐ xià ma."),
}

GAP = 0.10    # silence between lines
LEAD = 0.1    # silence at segment start
TAIL = 0.20   # silence at segment end (fast cuts)
M_PAUSE = 0.35  # extra pause after Mandarin so viewers can repeat

# Tone colors (ASS uses &HBBGGRR&): 1 red, 2 orange, 3 green, 4 blue
TONE = {1: "&H2B2BD6&", 2: "&H1E8CF0&", 3: "&H3C9A2E&", 4: "&HC86A1E&", 0: "&H404040&"}


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         check=True, capture_output=True, text=True).stdout
    return float(out.strip())


SUB_MAX = 56  # characters per caption; one line fits ~45 at 66px Segoe UI, so this stays within 2 lines


def caption_chunks(display, words, start, end):
    """Split a subtitle into <=2-line captions, timed by the spoken word boundaries."""
    toks = display.split()
    # pieces: break before overflowing, preferring sentence/comma ends
    pieces, cur = [], []
    for tok in toks:
        cand = " ".join(cur + [tok])
        if cur and len(cand) > SUB_MAX:
            cut = len(cur)
            for k in range(len(cur) - 1, 0, -1):  # last punctuation that leaves a decent first piece
                if cur[k - 1][-1] in ".,?!…:;”" and len(" ".join(cur[:k])) >= 14:
                    cut = k
                    break
            pieces.append(cur[:cut])
            cur = cur[cut:]
        cur.append(tok)
        if tok[-1] in ".?!…" and len(" ".join(cur)) >= 22:
            pieces.append(cur)
            cur = []
    if cur:
        pieces.append(cur)
    # don't leave a lonely word or two: borrow words from a previous piece that ends mid-sentence
    for n in range(1, len(pieces)):
        prev, nxt = pieces[n - 1], pieces[n]
        if len(" ".join(nxt)) < 15 and prev[-1][-1] not in ".,?!…:;”":
            while len(prev) > 1 and len(" ".join(nxt)) < len(" ".join(prev)) * 0.6 and \
                    len(" ".join([prev[-1]] + nxt)) <= SUB_MAX:
                nxt.insert(0, prev.pop())
    # timing: map by word index when display and speech have the same word count, else by characters
    out, i = [], 0
    total = sum(len(" ".join(p)) for p in pieces)
    acc = 0
    for n, p in enumerate(pieces):
        if len(words) == len(toks):
            a = start + words[i][0]
            b = start + (words[i + len(p)][0] if n + 1 < len(pieces) else words[-1][1] + 0.15)
        else:
            a = start + (end - start) * acc / total
            b = start + (end - start) * (acc + len(" ".join(p))) / total + (0.15 if n + 1 == len(pieces) else 0)
        out.append((a, b, " ".join(p)))
        i += len(p)
        acc += len(" ".join(p))
    return out


# MOSS-TTS voices (designed once on the GPU server, cloned for every line) — edge-tts was shut off in Oct 2026.
MOSS_VOICE = {"N": ("narrator_en", "English", 1.0), "NF": ("narrator_en", "English", 1.08),
              "M": ("mandarin_zh", "Chinese", 1.0)}


BREAKDOWN_LINE = "。[pause 0.8s]".join(c for c, _ in BREAKDOWN) + "。"


def make_breakdown(synth):
    """Speak the four characters in ONE Mandarin take and split it at the silences (single characters
    generated alone come out as other words, guide mistake A3). Writes P2_00/02/04/06_M.mp3."""
    outs = [WORK / f"P2_{i:02d}_M.mp3" for i in (0, 2, 4, 6)]
    if all(p.exists() for p in outs):
        return
    whole = WORK / "P2_ALL_M.mp3"
    synth([(whole, "mandarin_zh", BREAKDOWN_LINE, "Chinese", 1.0)], job=EP.name)
    log = subprocess.run(["ffmpeg", "-i", str(whole), "-af", "silencedetect=noise=-35dB:d=0.35", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(l.split("silence_start: ")[1]) for l in log.splitlines() if "silence_start: " in l]
    ends = [float(l.split("silence_end: ")[1].split()[0]) for l in log.splitlines() if "silence_end: " in l]
    gaps = [(a + b) / 2 for a, b in zip(starts, ends)]
    if len(gaps) != 3:
        raise SystemExit(f"breakdown take has {len(gaps)} pauses, expected 3: delete {whole.name} (and its server wav) to re-roll")
    cuts = [0.0] + gaps + [duration(whole)]
    trim = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
            "silenceremove=start_periods=1:start_threshold=-45dB,areverse")
    for p, a, b in zip(outs, cuts, cuts[1:]):
        run(["ffmpeg", "-y", "-i", str(whole), "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-af", trim, "-ar", "24000", "-b:a", "96k", str(p)])
        p.with_suffix(".json").write_text("[]", encoding="utf-8")


def make_audio():
    import sys
    sys.path.insert(0, "/root/autodl-tmp/idiom_handover/tools")
    from moss_local import synth
    make_breakdown(synth)
    items = []
    for shot, ls, _ in SEGMENTS:
        for li, (vk, text, sub) in enumerate(ls):
            voice, lang, tempo = MOSS_VOICE[vk]
            items.append((WORK / f"{shot}_{li:02d}_{vk}.mp3", voice, text, lang, tempo))
    synth(items, job=EP.name)


def fmt(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def py_colored(pairs, size):
    return " ".join(f"{{\\c{TONE[t]}\\fs{size}}}{s}" for s, t in pairs)


def main():
    make_audio()
    seg_files, events, t0, chain_t = [], [], 0.0, 0.0
    for si, (shot, ls, min_s) in enumerate(SEGMENTS):
        # 1) narration track for this segment
        gap = FAST.get(shot, {}).get("gap", GAP)
        m_pause = FAST.get(shot, {}).get("m_pause", M_PAUSE)
        parts, offs, t = [], [], LEAD
        for li, (vk, text, sub) in enumerate(ls):
            p = WORK / f"{shot}_{li:02d}_{vk}.mp3"
            d = duration(p)
            offs.append((t, t + d, vk, text, sub, json.loads(p.with_suffix(".json").read_text(encoding="utf-8"))))
            parts.append((p, t))
            t += d + gap + (m_pause if vk == "M" else 0)
        seg_len = max(t - gap + TAIL, min_s)
        narr = WORK / f"seg_{si:02d}_narr.wav"
        inputs, filt = [], []
        for k, (p, start) in enumerate(parts):
            inputs += ["-i", str(p)]
            filt.append(f"[{k}:a]aresample=48000,adelay={int(start * 1000)}:all=1[a{k}]")
        filt.append("".join(f"[a{k}]" for k in range(len(parts))) +
                    f"amix=inputs={len(parts)}:normalize=0,apad,atrim=0:{seg_len:.3f}[out]")
        run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filt), "-map", "[out]", "-ac", "2", str(narr)])

        # 2) video for this segment
        seg = WORK / f"seg_{si:02d}.mp4"
        if shot == TITLE_CARD:
            run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={PAPER}:s={W}x{H}:r={FPS}:d={seg_len:.3f}",
                 "-i", str(narr), "-filter_complex",
                 "[0:v]noise=alls=7:allf=t,vignette=PI/9,format=yuv420p[v]",
                 "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
                 "-shortest", str(seg)])
        else:
            src = CLIPS / CLIP[shot]
            s0 = chain_t if shot in CHAIN else CLIP_START.get(shot, 0.0)
            cut = min(duration(src) - s0, CLIP_MAX.get(shot, 99))
            if shot in CHAIN:
                cut = min(cut, seg_len)
                chain_t = s0 + cut
            clen = cut * 2 if shot in PINGPONG else cut
            speed = min(max(seg_len / clen, 1.0), 1.15)  # at most a barely-visible 1.15x slow-down (more looks stuttery)
            hold = max(seg_len - clen * speed, 0)
            grade = "hue=s=0.6," if shot in STORY else ""
            src_v = f"[0:v]trim={s0:.3f}:{s0 + cut:.3f},setpts=PTS-STARTPTS"
            if shot in PINGPONG:
                src_v += ",split[fw][bk];[bk]reverse[rv];[fw][rv]concat=n=2:v=1:a=0"
            v = (f"{src_v},{grade}scale={W}:{H}:flags=lanczos,setpts={speed:.4f}*PTS,fps={FPS},"
                 f"tpad=stop_mode=clone:stop_duration={hold + 0.1:.3f},trim=0:{seg_len:.3f},setpts=PTS-STARTPTS,format=yuv420p[v]")
            # clip sound effects under the voice: quieter while someone is talking
            duck = "+".join(f"between(t,{a - 0.1:.2f},{b + 0.1:.2f})" for a, b, *_ in offs)
            sfx_vol = "0" if shot in SFX_MUTE else f"if({duck},0.28,0.9)"
            a = (f"[0:a]atrim={s0:.3f},asetpts=PTS-STARTPTS,aresample=48000,apad,atrim=0:{seg_len:.3f},volume='{sfx_vol}':eval=frame[sfx];"
                 f"[1:a]aresample=48000[nar];[sfx][nar]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]")
            run(["ffmpeg", "-y", "-i", str(src), "-i", str(narr), "-filter_complex", v + ";" + a,
                 "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-r", str(FPS),
                 "-c:a", "aac", "-b:a", "192k", "-t", f"{seg_len:.3f}", str(seg)])
        seg_files.append(seg)

        # 3) text events (absolute times)
        for a, b, vk, text, sub, words in offs:
            s = text if sub is None else sub
            if s:
                style = "Tiger" if vk in CHARACTER_VOICES else "Sub"  # "Tiger" = italic character-line style
                for ca, cb, ct in caption_chunks(s, words, t0 + a, t0 + b):
                    events.append((ca, cb, style, ct))
        events += overlays(shot, t0, seg_len, offs)
        t0 += seg_len
        print(f"{shot}: {seg_len:5.2f}s")

    # small idiom tag in the top-left corner for the whole video
    events.append((0.0, t0, "Tag", f"{{\\an7\\pos(40,60)}}{IDIOM}"))

    # 4) concat + burn text
    lst = WORK / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in seg_files), encoding="utf-8")
    joined = WORK / "joined.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])
    ass = WORK / "text.ass"
    ass.write_text(ass_file(events), encoding="utf-8-sig")
    # run from WORK so the subtitles filter gets a plain relative path (Windows drive colons break it)
    subprocess.run(["ffmpeg", "-y", "-i", "joined.mp4", "-vf", "subtitles=text.ass", "-c:v", "libx264", "-crf", "18",
                    "-preset", "slow", "-c:a", "copy", "-movflags", "+faststart", str(OUT)],
                   check=True, capture_output=True, cwd=WORK)
    print(f"total {t0:.1f}s -> {OUT}")


def panel(x, y, w, h):
    """Soft rice-paper box drawn behind on-screen text so busy backgrounds don't fight it."""
    return f"{{\\an7\\pos({x},{y})\\blur12\\fad(300,0)\\p1}}m 0 0 l {w} 0 {w} {h} 0 {h}{{\\p0}}"


def overlays(shot, t0, seg_len, offs):
    """On-screen text for the hook, payoff and examples (70-second structure)."""
    ev = []
    end = t0 + seg_len
    m_lines = [o for o in offs if o[2] == "M"]
    if shot == "H1":
        # big hook text from the very first frame, readable with the sound off
        ev.append((t0, end, "Hook", f"{{\\pos({W // 2},330)}}{HOOK_TEXT}"))
    elif shot in ("P1", "P2"):
        # P1: the idiom appears as it's spoken; P2 continues the same card while each character
        # and its English meaning are read aloud, then the meaning line.
        st = t0 + m_lines[0][0] - 0.1 if shot == "P1" else t0
        fade = "\\fad(250,0)" if shot == "P1" else ""
        ev.append((st, end, "Panel", panel(90, 170, W - 180, 640)))
        ev.append((st, end, "Card", f"{{\\pos({W // 2},300){fade}\\fs150}}{IDIOM}"))
        ev.append((st, end, "Pinyin", f"{{\\pos({W // 2},450){fade}}}" + py_colored(IDIOM_PY, 70)))
        if shot == "P2":
            for i, (c, en) in enumerate(BREAKDOWN):
                x = GLOSS_X[i]
                ev.append((t0 + m_lines[i][0], end, "Gloss", f"{{\\an5\\pos({x},560)\\fad(200,0)}}{c} {en}"))
            meaning_at = t0 + [o for o in offs if o[2] == "N"][-1][0]
            ev.append((meaning_at, end, "CardEn", f"{{\\pos({W // 2},650)\\fad(250,0)\\fs60}}{MEANING}"))
    elif shot in EXAMPLES:
        zh, py = EXAMPLES[shot]
        st = t0 + m_lines[0][0]
        zh_lines, py_lines = zh.count("\\N") + 1, py.count("\\N") + 1
        top = 230
        zh_y = top + zh_lines * 100 // 2
        py_y = top + zh_lines * 100 + 30 + py_lines * 66 // 2
        bottom = py_y + py_lines * 66 // 2 + 40
        ev.append((st - 0.1, end, "Panel", panel(50, top - 50, W - 100, bottom - top + 50)))
        ev.append((st, end, "Example", f"{{\\pos({W // 2},{zh_y})\\fad(300,0)}}{zh}"))
        ev.append((st, end, "ExamplePy", f"{{\\pos({W // 2},{py_y})\\fad(300,0)}}{py}"))
    elif shot == QUOTE_SHOT:
        # the words the character wrote, as clean text (the video model never draws writing)
        zh, py = QUOTE
        st = t0 + m_lines[0][0] - 0.1
        ev.append((st, end, "Panel", panel(70, 190, W - 140, 300)))
        ev.append((st, end, "Example", f"{{\\pos({W // 2},300)\\fad(300,0)\\fs96}}{zh}"))
        ev.append((st, end, "ExamplePy", f"{{\\pos({W // 2},420)\\fad(300,0)}}{py}"))
    if shot in LABELS:
        ev.append((t0 + 0.3, end, "Label", f"{{\\pos({W // 2},300)\\fad(200,0)}}{LABELS[shot]}"))
    return ev


def ass_file(events):
    ink, paper = "&H00262626", "&H00C6DEE9"
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Selawik Semibold,66,&H00FFFFFF,&H00FFFFFF,&H00202020,&H64000000,0,0,0,0,100,100,0,0,1,5,1,2,70,70,400,1
Style: Tiger,Selawik Semibold,68,&H0084E8FF,&H00FFFFFF,&H00202020,&H64000000,0,1,0,0,100,100,0,0,1,5,1,2,70,70,400,1
Style: Big,LXGW WenKai,210,{ink},{ink},{paper},&H00000000,1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,134
Style: Big2,LXGW WenKai,170,{ink},{ink},{paper},&H00000000,1,0,0,0,100,100,0,0,1,6,0,5,0,0,0,134
Style: Pinyin,DejaVu Sans,72,{ink},{ink},{paper},&H00000000,0,0,0,0,100,100,6,0,1,5,0,5,0,0,0,1
Style: Trad,LXGW WenKai,80,&H00606060,&H00606060,{paper},&H00000000,0,0,0,0,100,100,8,0,1,0,0,5,0,0,0,134
Style: Mid,LXGW WenKai,150,{ink},{ink},{paper},&H00000000,1,0,0,0,100,100,0,0,1,6,0,5,0,0,0,134
Style: Gloss,Selawik Semibold,72,{ink},{ink},{paper},&H00000000,0,0,0,0,100,100,0,0,1,5,0,4,0,0,0,1
Style: Card,LXGW WenKai,92,{ink},{ink},{paper},&H00000000,1,0,0,0,100,100,0,0,1,7,0,5,0,0,0,134
Style: Hook,Selawik,78,&H00FFFFFF,&H00FFFFFF,&H00262626,&H00000000,1,0,0,0,100,100,0,0,1,8,0,5,0,0,0,1
Style: Label,Selawik,96,&H002B2BD6,&H002B2BD6,&H00FFFFFF,&H00000000,1,0,0,0,100,100,2,0,1,7,0,5,0,0,0,1
Style: Tag,LXGW WenKai,64,&H00262626,&H00262626,&H00C6DEE9,&H00000000,1,0,0,0,100,100,2,0,1,5,0,7,0,0,0,134
Style: Panel,Arial,20,&H28C6DEE9,&H28C6DEE9,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: CardEn,Selawik Semibold,76,{ink},{ink},{paper},&H00000000,0,0,0,0,100,100,0,0,1,6,0,5,0,0,0,1
Style: Example,LXGW WenKai,84,{ink},{ink},{paper},&H00000000,1,0,0,0,100,100,0,0,1,7,0,5,0,0,0,134
Style: ExamplePy,DejaVu Sans,58,&H00404040,&H00404040,{paper},&H00000000,0,0,0,0,100,100,0,0,1,5,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    # panels on layer 0, all text above them on layer 1
    body = "".join(f"Dialogue: {0 if st == 'Panel' else 1},{fmt(a)},{fmt(b)},{st},,0,0,0,,{tx}\n"
                   for a, b, st, tx in sorted(events))
    return hdr + body


if __name__ == "__main__":
    import sys
    if "--audio-only" in sys.argv:  # make the voices, then ASR-check them before editing
        make_audio()
    else:
        main()
