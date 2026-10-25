#!/usr/bin/env python3
"""Sound for a code-animated Idiom Ink short: voice + synthesized foley + a light pentatonic score.

  mix.py EPISODE_DIR VO_DIR OUT.wav

EPISODE_DIR holds timeline.json (DUR, lines[id,t0,t1], scenes{name:{t0,t1}}) and ev.json ([{t,type,gain?}]).
VO_DIR holds <line id>.wav. Everything else is synthesized here (numpy only), so there is nothing to license.
Levels: voice on top; music ~20 dB under the voice and ducked further while someone speaks; the final loudness
(-14 LUFS) is set by ffmpeg when muxing.
"""
import json, sys, wave
from pathlib import Path
import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def read_wav(p):
    with wave.open(str(p)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2:
            a = a.reshape(-1, 2).mean(1)
        assert w.getframerate() == SR, p
    return a


def write_wav(p, a):
    a = np.clip(a, -1, 1)
    st = (np.stack([a, a], 1) * 32767).astype(np.int16)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())


def tt(d):
    return np.arange(int(d * SR)) / SR


def env(d, a=0.004, k=8.0):
    t = tt(d)
    return np.minimum(1, t / a) * np.exp(-k * t)


def lp(x, fc):  # one-pole low-pass
    if np.isscalar(fc):
        fc = np.full(len(x), fc)
    al = 1 - np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s += al[i] * (x[i] - s); y[i] = s
    return y


def bp(x, lo, hi):
    return lp(x, hi) - lp(x, lo)


def reson(x, f, q=8):  # two-pole resonator
    r = np.exp(-np.pi * f / q / SR); c = 2 * r * np.cos(2 * np.pi * f / SR)
    y = np.zeros_like(x); y1 = y2 = 0.0
    for i in range(len(x)):
        y0 = x[i] + c * y1 - r * r * y2; y[i] = y0; y2, y1 = y1, y0
    return y * (1 - r)


def noise(d):
    return rng.standard_normal(int(d * SR)).astype(np.float32)


def norm(x, peak=1.0):
    m = np.abs(x).max() or 1
    return x / m * peak


# ---------------- foley ----------------
def s_pop():
    n = bp(noise(.05), 900, 5000) * env(.05, .001, 90)
    th = np.sin(2 * np.pi * 160 * tt(.05)) * env(.05, .001, 60) * .5
    return norm(n + th, .5)


def s_rustle(d=.22):
    n = bp(noise(d), 1500, 7000)
    crack = (rng.random(len(n)) > .996) * rng.standard_normal(len(n)) * 3
    e = np.sin(np.pi * np.clip(tt(d) / d, 0, 1)) ** 1.5
    return norm((n + bp(crack, 800, 6000)) * e, .35)


def s_whoosh(d=.34):
    t = tt(d); fc = 400 + 3600 * np.sin(np.pi * t / d)
    return norm(lp(noise(d), fc) * np.sin(np.pi * t / d) ** 2, .45)


def s_wipe(d=.4):
    return s_whoosh(d) * .8 + s_rustle(d) * .6


def s_tick():
    t = tt(.07)
    return norm((np.sin(2 * np.pi * 1850 * t) + .6 * np.sin(2 * np.pi * 920 * t)) * env(.07, .0005, 70), .35)


def s_knock():
    t = tt(.14)
    body = np.sin(2 * np.pi * (190 - 60 * t / .14) * t) * env(.14, .0008, 35)
    click = bp(noise(.14), 1500, 6000) * env(.14, .0005, 160)
    return norm(body + .5 * click, .7)


def s_stamp():
    t = tt(.2)
    return norm(np.sin(2 * np.pi * (120 - 40 * t / .2) * t) * env(.2, .001, 22) + .3 * bp(noise(.2), 600, 4000) * env(.2, .001, 60), .7)


def s_ding():
    t = tt(1.4); e = env(1.4, .002, 3.2)
    x = sum(a * np.sin(2 * np.pi * 1046 * m * t) * np.exp(-t * (2 + 2 * m)) for m, a in [(1, 1), (2.76, .5), (5.4, .25), (8.9, .1)])
    return norm(x * e, .45)


def s_drop():
    t = tt(.55); f = 700 * np.exp(-2.4 * t)
    whist = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / .55) * .25
    thud = np.pad(np.sin(2 * np.pi * 70 * tt(.15)) * env(.15, .001, 30), (int(.4 * SR), 0))[:len(t)]
    return norm(whist + thud * .6, .45)


def s_boom():
    t = tt(1.6)
    drum = np.sin(2 * np.pi * np.cumsum(58 + 50 * np.exp(-t * 18)) / SR) * env(1.6, .002, 3.5)
    skin = bp(noise(1.6), 200, 2500) * env(1.6, .001, 30) * .4
    gong = sum(a * np.sin(2 * np.pi * f * t) for f, a in [(196, .5), (311, .3), (467, .2), (622, .12)]) * np.exp(-t * 1.8) * np.minimum(1, t / .05) * .35
    return norm(drum + skin + gong, .9)


def s_baa():
    d = .62; t = tt(d)
    f0 = 330 * (1 + .03 * np.sin(2 * np.pi * 6.5 * t)) * (1 - .12 * t / d)
    saw = 2 * ((np.cumsum(f0) / SR) % 1) - 1
    trem = .55 + .45 * np.sin(2 * np.pi * 11 * t) ** 2
    x = reson(saw, 900, 5) + .7 * reson(saw, 2300, 6) + .3 * reson(saw, 3400, 8)
    e = np.minimum(1, t / .04) * np.minimum(1, (d - t) / .18)
    return norm(x * trem * e, .32)


def s_wolf():
    d = 1.1; t = tt(d)
    x = reson(noise(d), 110, 6) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t))
    return norm(x * np.sin(np.pi * t / d) ** 1.2, .4)


FOLEY = {"pop": s_pop, "rustle": s_rustle, "whoosh": s_whoosh, "wipe": s_wipe, "tick": s_tick, "knock": s_knock,
         "stamp": s_stamp, "ding": s_ding, "drop": s_drop, "boom": s_boom, "baa": s_baa, "wolf": s_wolf}
LEVEL = {"pop": .5, "rustle": .5, "whoosh": .55, "wipe": .6, "tick": .5, "knock": .75, "stamp": .6, "ding": .7,
         "drop": .55, "boom": .9, "baa": .55, "wolf": .7}


# ---------------- score ----------------
def pluck(f, d, bright=.5):
    """Karplus-Strong string (guzheng-ish), computed one period at a time."""
    N = max(2, int(SR / f)); n = int(d * SR)
    buf = lp(rng.uniform(-1, 1, N).astype(np.float32), 2000 + 6000 * bright)
    out = np.empty(n + N, np.float32); out[:N] = buf; dec = .996
    for s in range(N, n + N, N):
        prev = out[s - N:s]
        nxt = .5 * (prev + np.roll(prev, 1)) * dec
        m = min(N, n + N - s); out[s:s + m] = nxt[:m]
    return out[N:] * np.minimum(1, tt(d) / .002)


PENTA = [0, 2, 4, 7, 9]


def note(deg, octave=0, root=62):  # D pentatonic
    o, k = divmod(deg, 5)
    return 440 * 2 ** ((root + 12 * (o + octave) + PENTA[k] - 69) / 12)


def score(T, sc):
    out = np.zeros(int(T * SR) + SR)
    beat = 60 / 104

    def put(x, at, g):
        i = int(at * SR); out[i:i + len(x)] += x[:len(out) - i] * g

    patt = [0, 2, 4, 2, 5, 4, 2, 1]  # bouncy, playful
    t = 0.0; k = 0
    story = sorted((v["t0"], k) for k, v in sc.items() if k[0] == "S" and k[1:].isdigit())
    turn = sc.get("turn")  # near-silence before the turn; the beat after it plays tense, until the last story beat
    mute0, mute1 = (turn["t0"] - .15, turn["t1"]) if turn else (-1, -1)
    tense0, tense1 = (turn["t1"], story[-1][0]) if turn else (-1, -1)
    while t < T - .4:
        if not (mute0 <= t < mute1):
            tense = tense0 <= t < tense1
            deg = (patt[k % 8] - (3 if tense else 0))
            put(pluck(note(deg, 0 if not tense else -1), .9, .45), t, .5 if k % 2 == 0 else .35)
            if k % 4 == 0:  # bass + woodblock on the beat
                put(pluck(note(0 if not tense else -2, -1), 1.4, .25), t, .55)
            if k % 2 == 0:
                put(s_tick() * .5, t, .35)
        t += beat / 2; k += 1
    # gong swell into the slam, and a short sparkle run on the reveal
    for i, d in enumerate([0, 2, 4, 5, 7]):
        put(pluck(note(d, 1), .7, .7), sc["reveal"]["t0"] + .06 * i, .45)
    return out


def main():
    ep, vo, outp = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    tl = json.loads((ep / "timeline.json").read_text()); ev = json.loads((ep / "ev.json").read_text())
    T = tl["DUR"]; n = int(T * SR) + SR
    voice = np.zeros(n); fx = np.zeros(n)
    for li in tl["lines"]:
        a = read_wav(vo / f"{li['id']}.wav"); i = int(li["t0"] * SR); voice[i:i + len(a)] += a[:n - i]
    cache = {}
    for e in ev:
        typ = e["type"]
        if typ not in FOLEY:
            print("unknown event", typ); continue
        if typ not in cache:
            cache[typ] = FOLEY[typ]()
        x = cache[typ]; i = int(e["t"] * SR)
        if i < n:
            fx[i:i + len(x)] += x[:n - i] * LEVEL[typ] * e.get("gain", 1)
    mus = score(T, tl["scenes"])[:n]
    # duck music under the voice (smoothed envelope)
    venv = lp(np.abs(voice), 8); duck = 1 - .55 * np.clip(venv / (venv.max() * .25 + 1e-9), 0, 1)
    vr = np.sqrt(np.mean(voice[voice != 0] ** 2)); mr = np.sqrt(np.mean(mus ** 2)) or 1
    mus = mus / mr * vr * 10 ** (-17 / 20) * duck
    mix = voice + fx * .55 + mus
    mix = mix[:int(T * SR)]
    write_wav(outp, mix / max(1, np.abs(mix).max() / .95))
    print(f"wrote {outp}: {T:.2f} s, {len(ev)} events")


if __name__ == "__main__":
    main()
