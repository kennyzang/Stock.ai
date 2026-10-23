# Original synthesized Chinese-pentatonic background loop (guzheng-like plucks + soft pad). No external samples.
import sys, wave, numpy as np
sr = 44100
dur = float(sys.argv[2]) if len(sys.argv) > 2 else 40.0
out = sys.argv[1]
rng = np.random.default_rng(7)

def pluck(freq, length, decay=0.996):
    n = int(sr * length)
    N = int(sr / freq)
    buf = rng.uniform(-1, 1, N)
    buf = np.convolve(buf, np.ones(3) / 3, mode='same')
    y = np.zeros(n)
    for i in range(n):
        y[i] = buf[i % N]
        buf[i % N] = decay * 0.5 * (buf[i % N] + buf[(i + 1) % N])
    env = np.exp(-np.arange(n) / (sr * length * 0.45))
    return y * env

def midi(m): return 440.0 * 2 ** ((m - 69) / 12)
# D major pentatonic: D E F# A B
scale = [62, 64, 66, 69, 71, 74, 76, 78, 81, 83]
bpm = 84
beat = 60 / bpm
n_total = int(sr * dur)
mix = np.zeros(n_total + sr * 4)
# melody pattern over 4-bar phrase (eighth notes), indices into scale; None = rest
phrases = [
  [5,None,7,6, 5,None,3,None, 4,5,4,2, 3,None,None,None],
  [2,3,5,None, 7,6,5,3, 5,None,4,2, 0,None,None,None],
  [5,6,7,None, 9,7,6,5, 7,None,6,5, 3,None,2,None],
  [3,5,6,5, 3,2,3,None, 5,4,2,0, 2,None,None,None],
]
t = 0.0
step = beat / 2
k = 0
while t < dur:
    ph = phrases[(k // 16) % len(phrases)]
    idx = ph[k % 16]
    if idx is not None:
        f = midi(scale[idx])
        y = pluck(f, 1.8)
        s = int(t * sr)
        mix[s:s + len(y)] += y * 0.55
    # soft bass pluck every 2 beats
    if k % 4 == 0:
        bass = [50, 50, 52, 45][(k // 16) % 4]
        y = pluck(midi(bass), 2.2, 0.998)
        s = int(t * sr)
        mix[s:s + len(y)] += y * 0.5
    t += step
    k += 1
# soft pad (open fifth) with slow tremolo
tt = np.arange(len(mix)) / sr
pad = (np.sin(2*np.pi*midi(50)*tt) + 0.6*np.sin(2*np.pi*midi(57)*tt) + 0.4*np.sin(2*np.pi*midi(62)*tt))
pad *= 0.06 * (0.8 + 0.2*np.sin(2*np.pi*0.15*tt))
mix += pad
mix = mix[:n_total]
# gentle fade in/out and normalize
fade = int(sr * 1.5)
mix[:fade] *= np.linspace(0, 1, fade)
mix[-fade:] *= np.linspace(1, 0, fade)
mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.85
pcm = (mix * 32767).astype(np.int16)
with wave.open(out, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
print("wrote", out, dur, "s")
