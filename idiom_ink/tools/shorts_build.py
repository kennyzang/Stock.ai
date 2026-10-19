#!/usr/bin/env python3
"""Build an Idiom Ink short (< 30 s) from still images + voice lines. No GPU. See FORMAT_SHORTS.md.

Usage:  shorts_build.py EPISODE_DIR/shorts.json --images DIR --audio DIR --outdir DIR [--placeholder]
  --placeholder   missing voice files become silence of the estimated length (layout / timing tests)
Media (images, audio, renders) stay out of git: the repo is public and they are large.

Spec (JSON):
  out, idiom, pinyin [[syll, tone]], gloss [[char, english]], tag (optional)
  beats: [{id, img, move, focus:[fx,fy], hook, card, meaning, close, nocap, nosplit, min,
           lines:[{id, voice:"N"|"M", text, cap (None = text, "" = none), hl:[words to highlight]}]}]
  move: push_in | pull_out | pan_left | pan_right | push_in_more | punch      (focus = point to keep centred)
Audio files: <audio_dir>/<line id>.wav|.mp3. Word timings (optional): <line id>.words.json [[start, end, word], ...]
Output: <out> (1080x1920, 30 fps, H.264 + AAC, -14 LUFS, +faststart, <= ~10 MB), <out stem>_cover.png, <out stem>_grid.jpg
Images are always shown full-frame: flat padding bands (letterbox/pillarbox) are cut off first; portrait art is
cover-cropped to 9:16; landscape art (fallback only, ask Grok for 9:16) is enlarged over a blurred copy of itself
so the whole canvas is illustration, never empty paper.
"""
import json, math, re, subprocess, sys, tempfile
from pathlib import Path

W, H, FPS = 1080, 1920, 30
GAP, LEAD, TAIL, M_PAUSE = 0.08, 0.04, 0.10, 0.12   # tight: the playbook says cut every pause
SPLIT_AT, MIN_BEAT = 2.8, 1.2                       # no single framing longer than ~3 s
WPS = 3.1                                           # placeholder speech rate (words/second), ~1.15x
TONE = {1: "&H2B2BD6&", 2: "&H1E8CF0&", 3: "&H3C9A2E&", 4: "&HC86A1E&", 0: "&H404040&"}  # ASS &HBBGGRR&
HL = "&H33DDFF&"                                    # warm yellow keyword highlight
INK, PAPER = "&H00262626", "&H00C6DEE9"
MOVES = {  # (z0, z1, x0, x1) — x as a fraction of the free pan range (0 = left, 1 = right); None = follow focus
    "push_in": (1.00, 1.10, None, None), "pull_out": (1.12, 1.02, None, None),
    "push_in_more": (1.10, 1.22, None, None), "punch": (1.24, 1.32, None, None),
    "pan_left": (1.14, 1.14, 0.85, 0.15), "pan_right": (1.14, 1.14, 0.15, 0.85),
}


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        raise SystemExit(f"command failed: {' '.join(map(str, cmd[:8]))} …\n{r.stderr[-1500:]}")
    return r.stdout


def dur(p):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip())


def est_seconds(line):
    t = line["text"]
    zh = len(re.findall(r"[一-鿿]", t))
    return max(0.5, len(re.findall(r"[A-Za-z']+", t)) / WPS + zh * 0.28)


# ---------- audio ----------
def line_audio(spec, line, tmp, placeholder):
    base = Path(spec["audio_dir"]) / line["id"]
    for ext in (".wav", ".mp3"):
        if base.with_suffix(ext).exists():
            return base.with_suffix(ext)
    if not placeholder:
        raise SystemExit(f"missing voice line {base}.wav|.mp3 (use --placeholder for a layout test)")
    p = tmp / f"{line['id']}_ph.wav"
    sh(["ffmpeg", "-nostdin", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{est_seconds(line):.2f}", str(p)])
    return p


def make_sfx(tmp):
    s = {"whoosh": "anoisesrc=d=0.32:c=pink:a=0.6,highpass=f=500,lowpass=f=4000,afade=t=in:d=0.10,afade=t=out:st=0.10:d=0.22,volume=0.35",
         "boom": "sine=f=52:d=0.9,volume=1.6,afade=t=out:st=0.05:d=0.85[a];anoisesrc=d=0.25:c=brown:a=0.8,lowpass=f=300,afade=t=out:d=0.25[b];[a][b]amix=inputs=2:normalize=0",
         "pop": "sine=f=880:d=0.09,afade=t=out:st=0.01:d=0.08,volume=0.5"}
    out = {}
    for k, f in s.items():
        p = tmp / f"sfx_{k}.wav"
        sh(["ffmpeg", "-nostdin", "-y", "-filter_complex", f + ",aresample=48000,aformat=channel_layouts=stereo", str(p)]) if ";" in f else \
            sh(["ffmpeg", "-nostdin", "-y", "-f", "lavfi", "-i", f + ",aresample=48000,aformat=channel_layouts=stereo", str(p)])
        out[k] = p
    return out


# ---------- timeline ----------
def plan(spec, tmp, placeholder):
    t, beats = 0.0, []
    for bi, b in enumerate(spec["beats"]):
        start, cur, lines = t, t + (LEAD if bi == 0 else 0.0), []
        for li in b["lines"]:
            p = line_audio(spec, li, tmp, placeholder)
            d = dur(p)
            wj = Path(spec["audio_dir"]) / f"{li['id']}.words.json"
            words = json.loads(wj.read_text()) if wj.exists() else None
            lines.append(dict(li, path=p, start=cur, end=cur + d, words=words))
            cur += d + GAP + (M_PAUSE if li["voice"] == "M" else 0)
        end = max(cur - GAP + TAIL, start + b.get("min", MIN_BEAT))
        beats.append(dict(b, start=start, end=end, lines=lines))
        t = end
    return beats, t


def shots_for(b):
    """Split a beat into sub-shots so no framing lasts more than ~SPLIT_AT seconds (2nd part: punch-in recrop)."""
    d = b["end"] - b["start"]
    if d <= SPLIT_AT or b.get("nosplit"):
        return [(b["start"], b["end"], b.get("move", "push_in"))]
    n = math.ceil(d / SPLIT_AT)
    edges = [b["start"] + d * k / n for k in range(n + 1)]
    moves = [b.get("move", "push_in")] + ["punch" if k % 2 else "pull_out" for k in range(1, n)]
    return [(edges[k], edges[k + 1], moves[k]) for k in range(n)]


def render_shot(img, move, focus, d, out):
    z0, z1, x0, x1 = MOVES[move]
    n = max(2, round(d * FPS))
    fx, fy = focus
    z = f"{z0}+({z1}-{z0})*on/{n}"
    if x0 is None:
        x = f"min(max({fx}*iw-iw/zoom/2,0),iw-iw/zoom)"
    else:
        x = f"(iw-iw/zoom)*({x0}+({x1}-{x0})*on/{n})"
    y = f"min(max({fy}*ih-ih/zoom/2,0),ih-ih/zoom)"
    vf = (f"scale={2*W}:{2*H}:force_original_aspect_ratio=increase,crop={2*W}:{2*H},"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},format=yuv420p")
    sh(["ffmpeg", "-nostdin", "-y", "-loop", "1", "-i", str(img), "-vf", vf, "-frames:v", str(n),
        "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-r", str(FPS), str(out)])


# ---------- images ----------
def fill_frame(img, focus, tmp):
    """Return a 1080x1920 full-frame version of img (see module doc)."""
    from PIL import Image, ImageFilter, ImageStat, ImageEnhance
    out = tmp / f"full_{Path(img).stem}_{focus[0]:.2f}.png"
    if out.exists():
        return out
    im = Image.open(img).convert("RGB")
    g = im.convert("L")
    busy = lambda box: ImageStat.Stat(g.crop(box)).stddev[0] > 12   # flat paper bands have almost no detail
    w, h = im.size
    t = next((y for y in range(0, h, 2) if busy((0, y, w, y + 2))), 0)
    b = next((y for y in range(h, 0, -2) if busy((0, y - 2, w, y))), h)
    l = next((x for x in range(0, w, 2) if busy((x, t, x + 2, b))), 0)
    r = next((x for x in range(w, 0, -2) if busy((x - 2, t, x, b))), w)
    if (b - t) > h * 0.3 and (r - l) > w * 0.3:
        im = im.crop((l + 4, t + 4, r - 4, b - 4))   # a few px more: the band edge is often a soft fade
    w, h = im.size
    if w / h <= 0.8:   # portrait: cover-crop around the focus point
        k = max(W / w, H / h)
        im = im.resize((round(w * k), round(h * k)), Image.LANCZOS)
        x = min(max(round(focus[0] * im.width - W / 2), 0), im.width - W)
        y = min(max(round(focus[1] * im.height - H / 2), 0), im.height - H)
        im = im.crop((x, y, x + W, y + H))
    else:              # landscape: enlarged art over a blurred, darker copy of itself
        k = max(W / w, H / h)
        bg = im.resize((round(w * k), round(h * k)), Image.LANCZOS)
        x0 = (bg.width - W) // 2
        bg = bg.crop((x0, 0, x0 + W, H)).filter(ImageFilter.GaussianBlur(45))
        bg = ImageEnhance.Brightness(bg).enhance(0.72)
        fw = round(W * 1.25)
        fg = im.resize((fw, round(h * fw / w)), Image.LANCZOS)
        x = min(max(round(focus[0] * fw - W / 2), 0), fw - W)
        fg = fg.crop((x, 0, x + W, fg.height))
        bg.paste(fg, (0, round(H * 0.46 - fg.height / 2)))
        im = bg
    im.save(out)
    return out


# ---------- text ----------
def fmt(t):
    h, r = divmod(max(t, 0), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def chunks(text, start, end, words=None, maxw=4, maxc=20):
    toks = text.split()
    out, cur = [], []
    for tok in toks:
        if cur and (len(cur) >= maxw or len(" ".join(cur + [tok])) > maxc):
            out.append(cur); cur = []
        cur.append(tok)
        if tok[-1] in ".,?!…:;" and len(cur) >= 2:
            out.append(cur); cur = []
    if cur:
        if out and len(cur) == 1 and len(out[-1]) < maxw:
            out[-1] += cur
        else:
            out.append(cur)
    res, i = [], 0
    if words and len(words) == len(toks):
        for k, c in enumerate(out):
            a = start + words[i][0]
            b = start + (words[i + len(c)][0] if k + 1 < len(out) else words[-1][1] + 0.12)
            res.append((a, b, c)); i += len(c)
    else:
        total = sum(len(" ".join(c)) for c in out); acc = 0
        for k, c in enumerate(out):
            a = start + (end - start) * acc / total
            acc += len(" ".join(c)) + 1
            b = start + (end - start) * acc / total if k + 1 < len(out) else end + 0.12
            res.append((a, b, c))
    return res


def styled(words, hl):
    keys = {re.sub(r"[^\w']", "", h).lower() for h in hl or []}
    return " ".join(f"{{\\c{HL}}}{w}{{\\c&HFFFFFF&}}" if re.sub(r"[^\w']", "", w).lower() in keys else w for w in words)


def panel(x, y, w, h, t_in="\\fad(120,0)"):
    return f"{{\\an7\\pos({x},{y})\\blur10{t_in}\\p1}}m 0 0 l {w} 0 {w} {h} 0 {h}{{\\p0}}"


def ass(spec, beats, total):
    ev = []
    idiom, py, gloss = spec["idiom"], spec["pinyin"], spec["gloss"]
    pyline = " ".join(f"{{\\c{TONE[t]}}}{s}" for s, t in py)
    glossline = "   ".join(f"{{\\fnLXGW WenKai\\c&H262626&}}{c}{{\\fnSelawik\\c&H505050&}} {e}" for c, e in gloss)
    card_on = None
    for b in beats:
        s, e = b["start"], b["end"]
        if b.get("hook"):
            ev.append((s, e, "Hook", f"{{\\an5\\pos({W//2},340)\\fscx92\\fscy92\\t(0,90,\\fscx100\\fscy100)}}{b['hook']}"))
        if b.get("card"):
            card_on = s
        if card_on is not None and (b.get("card") or b.get("meaning")):
            fade = "\\fad(90,0)" if b.get("card") else ""
            ev.append((s, e, "Panel", panel(70, 190, W - 140, 600, fade or "")))
            pop = "\\fscx70\\fscy70\\t(0,110,\\fscx104\\fscy104)\\t(110,180,\\fscx100\\fscy100)" if b.get("card") else ""
            ev.append((s, e, "Card", f"{{\\an5\\pos({W//2},380){pop}}}{idiom}"))
            ev.append((s, e, "Pinyin", f"{{\\an5\\pos({W//2},565)}}{pyline}"))
            ev.append((s, e, "Gloss", f"{{\\an5\\pos({W//2},680)}}{glossline}"))
        if b.get("meaning"):
            ev.append((s, e, "Meaning", f"{{\\an5\\pos({W//2},900)\\fad(80,0)\\fscx85\\fscy85\\t(0,90,\\fscx100\\fscy100)}}{b['meaning']}"))
        if b.get("close"):
            ev.append((s, e + 0.05, "End", f"{{\\an5\\pos({W//2},860)\\fscx85\\fscy85\\t(0,90,\\fscx100\\fscy100)}}{b['close']}"))
        if not (b.get("hook") or b.get("card") or b.get("meaning") or b.get("close")):  # corner tag on story beats only
            ev.append((s, e, "Tag", f"{{\\an7\\pos(44,210)}}{spec.get('tag', idiom)}"))
        if not (b.get("hook") or b.get("nocap") or b.get("meaning") or b.get("close")):
            for li in b["lines"]:
                cap = li["text"] if li.get("cap") is None else li["cap"]
                if not cap:
                    continue
                for a, z, ws in chunks(cap, li["start"], li["end"], li.get("words")):
                    ev.append((a, z, "Cap", f"{{\\an5\\pos({W//2},1180)\\fscx88\\fscy88\\t(0,70,\\fscx100\\fscy100)}}{styled(ws, li.get('hl'))}"))
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,Selawik,92,&H00FFFFFF,&H00FFFFFF,&H00141414,&H96000000,1,0,0,0,100,100,0,0,1,9,3,5,40,40,0,1
Style: Cap,Selawik,84,&H00FFFFFF,&H00FFFFFF,&H00141414,&H96000000,1,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1
Style: Card,LXGW WenKai,220,{INK},{INK},{PAPER},&H00000000,0,0,0,0,100,100,8,0,1,6,0,5,0,0,0,134
Style: Pinyin,DejaVu Sans,76,{INK},{INK},{PAPER},&H00000000,1,0,0,0,100,100,4,0,1,4,0,5,0,0,0,1
Style: Gloss,Selawik,54,{INK},{INK},{PAPER},&H00000000,1,0,0,0,100,100,0,0,1,3,0,5,0,0,0,1
Style: Meaning,Selawik,72,&H00FFFFFF,&H00FFFFFF,&H00141414,&H96000000,1,0,0,0,100,100,0,0,1,7,3,5,50,50,0,1
Style: End,Selawik,96,&H0033DDFF,&H0033DDFF,&H00141414,&H96000000,1,0,0,0,100,100,0,0,1,9,3,5,40,40,0,1
Style: Tag,LXGW WenKai,50,{INK},{INK},{PAPER},&H00000000,0,0,0,0,100,100,2,0,1,5,0,7,0,0,0,134
Style: Panel,Arial,20,&H30C6DEE9,&H30C6DEE9,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    body = "".join(f"Dialogue: {0 if st == 'Panel' else 1},{fmt(a)},{fmt(b)},{st},,0,0,0,,{tx}\n" for a, b, st, tx in sorted(ev))
    return hdr + body


# ---------- main ----------
def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--images", required=True); ap.add_argument("--audio", required=True)
    ap.add_argument("--outdir", required=True); ap.add_argument("--placeholder", action="store_true")
    a = ap.parse_args()
    placeholder = a.placeholder
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    spec["images_dir"], spec["audio_dir"] = str(Path(a.images).resolve()), str(Path(a.audio).resolve())
    Path(a.outdir).mkdir(parents=True, exist_ok=True)
    out = (Path(a.outdir) / spec["out"]).resolve()
    tmp = Path(tempfile.mkdtemp(prefix="shorts_"))
    beats, total = plan(spec, tmp, placeholder)
    if total > 29.5:
        print(f"WARNING: {total:.1f} s is over the 29.5 s cap: shorten lines")

    # video: one clip per sub-shot, then concat
    clips, cuts = [], []
    for b in beats:
        img = fill_frame(Path(spec["images_dir"]) / b["img"], b.get("focus", [0.5, 0.45]), tmp)
        for k, (a, z, move) in enumerate(shots_for(b)):
            p = tmp / f"{b['id']}_{k}.mp4"
            render_shot(img, move, b.get("focus", [0.5, 0.45]), z - a, p)
            clips.append(p); cuts.append(a)
    (tmp / "list.txt").write_text("".join(f"file '{c}'\n" for c in clips))
    sh(["ffmpeg", "-nostdin", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"), "-c", "copy", str(tmp / "video.mp4")])

    # audio: voice lines + sfx (whoosh on every cut, boom on the card, pop on the meaning line)
    sfx = make_sfx(tmp)
    ins, flt, k = [], [], 0
    def place(path, t, vol=1.0):
        nonlocal k
        ins.extend(["-i", str(path)])
        flt.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol},adelay={int(t*1000)}:all=1[a{k}]")
        k += 1
    for b in beats:
        for li in b["lines"]:
            place(li["path"], li["start"], 1.0)
    for t in cuts[1:]:
        place(sfx["whoosh"], max(t - 0.12, 0), 0.6)
    for b in beats:
        if b.get("card"):
            place(sfx["boom"], b["start"], 0.9)
        if b.get("meaning"):
            place(sfx["pop"], b["start"] + 0.02, 0.7)
    flt.append("".join(f"[a{i}]" for i in range(k)) + f"amix=inputs={k}:normalize=0,apad,atrim=0:{total:.3f},"
               "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[mix]")
    sh(["ffmpeg", "-nostdin", "-y", *ins, "-filter_complex", ";".join(flt), "-map", "[mix]", "-ac", "2", str(tmp / "audio.wav")])

    # burn text + mux
    (tmp / "text.ass").write_text(ass(spec, beats, total), encoding="utf-8-sig")
    sh(["ffmpeg", "-nostdin", "-y", "-i", "video.mp4", "-i", "audio.wav", "-vf", "subtitles=text.ass",
        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "20", "-maxrate", "2800k", "-bufsize", "5600k", "-preset", "slow", "-pix_fmt", "yuv420p",
        "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)], cwd=tmp)

    # cover (hook image + idiom + hook text) and a QC frame grid
    cover = out.with_name(out.stem + "_cover.png")
    first = fill_frame(Path(spec["images_dir"]) / beats[0]["img"], beats[0].get("focus", [0.5, 0.45]), tmp)
    cass = tmp / "cover.ass"
    pyline = " ".join(f"{{\\c{TONE[t]}}}{s}" for s, t in spec["pinyin"])
    cass.write_text(ass(spec, [], 0).split("[Events]")[0] + "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
                    + f"Dialogue: 0,0:00:00.00,0:00:05.00,Panel,,0,0,0,,{panel(70, 190, W - 140, 470, '')}\n"
                    + f"Dialogue: 1,0:00:00.00,0:00:05.00,Card,,0,0,0,,{{\\an5\\pos({W//2},380)}}{spec['idiom']}\n"
                    + f"Dialogue: 1,0:00:00.00,0:00:05.00,Pinyin,,0,0,0,,{{\\an5\\pos({W//2},565)}}{pyline}\n"
                    + f"Dialogue: 1,0:00:00.00,0:00:05.00,Hook,,0,0,0,,{{\\an5\\pos({W//2},1250)}}{spec.get('cover_text', beats[0].get('hook', ''))}\n",
                    encoding="utf-8-sig")
    sh(["ffmpeg", "-nostdin", "-y", "-i", str(first), "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},subtitles=cover.ass",
        "-frames:v", "1", str(cover)], cwd=tmp)
    grid = out.with_name(out.stem + "_grid.jpg")
    times = [min(b["start"] + 0.6, b["end"] - 0.05) for b in beats]
    sel = "+".join(f"eq(n\\,{round(t*FPS)})" for t in times)
    sh(["ffmpeg", "-nostdin", "-y", "-i", str(out), "-vf", f"select='{sel}',scale=270:480,tile=6x2:padding=4:color=white",
        "-frames:v", "1", "-vsync", "vfr", str(grid)])

    longest = max(z - a for b in beats for a, z, _ in shots_for(b))
    for b in beats:
        print(f"{b['id']:5s} {b['start']:6.2f}–{b['end']:6.2f}  ({b['end']-b['start']:.2f} s)  {b['img']}")
    print(f"TOTAL {total:.2f} s · longest single framing {longest:.2f} s · {len(clips)} shots -> {out}")


if __name__ == "__main__":
    main()
