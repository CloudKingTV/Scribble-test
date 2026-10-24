"""Procedural sound effects (numpy only) and a little stereo mixer with room reverb."""

import wave

import numpy as np

SR = 48000


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _band(x, lo, hi, soft=0.25):
    """Band-pass with soft (log-frequency) edges, done in the FFT domain."""
    X = np.fft.rfft(x)
    lf = np.log2(np.maximum(np.fft.rfftfreq(len(x), 1 / SR), 1.0))
    g = 1 / (1 + np.exp(-(lf - np.log2(lo)) / soft)) / (1 + np.exp((lf - np.log2(hi)) / soft))
    return np.fft.irfft(X * g, len(x))


def _norm(x, peak=1.0):
    return x / (np.max(np.abs(x)) + 1e-9) * peak


def _glide(f0, f1, dur, rate=4.0):
    t = _t(dur)
    freq = f1 + (f0 - f1) * np.exp(-t * rate / dur)
    return np.sin(2 * np.pi * np.cumsum(freq) / SR)


def whoosh(rng, dur=0.3, lo=350, hi=2800, peak_at=0.6):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    m = 8
    win = n // m * 2
    for i in range(m):
        c = lo * (hi / lo) ** (i / (m - 1))
        start = max(0, min(n - win, int(i * (n - win) / (m - 1))))
        seg = _band(noise[start:start + win], c / 1.8, c * 1.8) * np.hanning(win)
        out[start:start + win] += seg
    u = np.linspace(0, 1, n)
    env = np.where(u < peak_at, (u / peak_at) ** 2, ((1 - u) / (1 - peak_at)) ** 1.5)
    return _norm(out * env, 0.55)


def hit(rng, power=1.0):
    t = _t(0.45)
    thump = _glide(170, 52, 0.45, 5) * np.exp(-t * 16)
    crack = _band(rng.standard_normal(len(t)), 900, 6000) * np.exp(-t * 70)
    body = _band(rng.standard_normal(len(t)), 150, 1400) * np.exp(-t * 26)
    return _norm(thump + _norm(crack, 0.7 * power) + _norm(body, 0.6), 0.9)


def big_hit(rng):
    t = _t(1.3)
    thump = _glide(140, 36, 1.3, 7) * np.exp(-t * 6)
    sub = np.sin(2 * np.pi * 44 * t) * np.exp(-t * 4) * 0.8
    crack = _band(rng.standard_normal(len(t)), 700, 8000) * np.exp(-t * 45)
    tail = _band(rng.standard_normal(len(t)), 200, 3500) * np.exp(-t * 5)
    return _norm(thump + sub + _norm(crack, 0.9) + _norm(tail, 0.35), 1.0)


def thud(rng, power=1.0):
    t = _t(0.4)
    body = _glide(115, 42, 0.4, 5) * np.exp(-t * 15)
    dirt = _band(rng.standard_normal(len(t)), 80, 900) * np.exp(-t * 22)
    return _norm(body + _norm(dirt, 0.6 * power), 0.85)


def click(rng):
    t = _t(0.12)
    tick = lambda: _band(rng.standard_normal(len(t)), 2500, 9000) * np.exp(-t * 900)
    out = tick()
    up = tick() * 0.5
    d = int(0.075 * SR)
    out[d:] += up[:-d]
    return _norm(out, 0.45)


def pencil(rng, dur):
    n = int(dur * SR)
    noise = _band(rng.standard_normal(n), 1300, 7000)
    grains = np.repeat(rng.uniform(0.25, 1.0, n // 480 + 2), 480)[:n]
    k = np.hanning(480)
    grains = np.convolve(grains, k / k.sum(), "same")
    env = np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (0.02 * SR))
    return _norm(noise * grains * env, 0.22)


def pop(rng):
    t = _t(0.25)
    tone = _glide(380, 950, 0.25, 9)
    env = np.minimum(t / 0.004, 1) * np.exp(-t * 18)
    return _norm(tone * env + 0.3 * _glide(760, 1900, 0.25, 9) * env, 0.5)


def boop(rng):
    t = _t(0.16)
    return _norm(_glide(820, 440, 0.16, 3) * np.minimum(t / 0.004, 1) * np.exp(-t * 22), 0.4)


def step(rng, power=1.0):
    t = _t(0.08)
    tap = _band(rng.standard_normal(len(t)), 250, 3200) * np.exp(-t * 110)
    low = np.sin(2 * np.pi * 110 * t) * np.exp(-t * 70)
    return _norm(tap + 0.8 * low, 0.35)


def clap(rng):
    t = _t(0.12)
    return _norm(_band(rng.standard_normal(len(t)), 900, 6500) * np.exp(-t * 60), 0.5)


def land(rng):
    return _norm(thud(rng, 0.8) + 0.4 * np.pad(whoosh(rng, 0.25, 600, 3000, 0.1), (0, int(0.15 * SR))), 0.8)


SOUNDS = {
    "whoosh": lambda rng, **k: whoosh(rng, k.get("dur", 0.3)),
    "swish": lambda rng, **k: whoosh(rng, 0.18, 900, 4200, 0.5),
    "swoosh_down": lambda rng, **k: whoosh(rng, 0.45, 2500, 300, 0.35),
    "hit": lambda rng, **k: hit(rng, k.get("power", 1.0)),
    "big_hit": lambda rng, **k: big_hit(rng),
    "thud": lambda rng, **k: thud(rng),
    "click": lambda rng, **k: click(rng),
    "pencil": lambda rng, **k: pencil(rng, k["dur"]),
    "pop": lambda rng, **k: pop(rng),
    "boop": lambda rng, **k: boop(rng),
    "step": lambda rng, **k: step(rng),
    "clap": lambda rng, **k: clap(rng),
    "land": lambda rng, **k: land(rng),
}


def mix(events, duration, width, path, reverb=0.16, seed=7):
    """events: [(time_s, name, x_px or None, gain, params)] -> 16-bit stereo WAV at path."""
    rng = np.random.default_rng(seed)
    n = int(duration * SR) + SR
    out = np.zeros((2, n))
    for t, name, x, gain, params in events:
        s = SOUNDS[name](rng, **params) * gain
        p = 0.0 if x is None else max(-1.0, min(1.0, (x / width) * 2 - 1)) * 0.7
        gl, gr = np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4)
        i = int(t * SR)
        if i >= n:
            continue
        s = s[: n - i]
        out[0, i:i + len(s)] += s * gl * 1.41
        out[1, i:i + len(s)] += s * gr * 1.41

    # Small-room reverb: convolve with decaying noise, one IR per channel.
    ir_t = _t(0.9)
    for c in range(2):
        ir = _band(rng.standard_normal(len(ir_t)), 200, 6000) * np.exp(-ir_t * 7)
        ir /= np.sqrt(np.sum(ir ** 2))
        m = 1 << int(np.ceil(np.log2(n + len(ir))))
        wet = np.fft.irfft(np.fft.rfft(out[c], m) * np.fft.rfft(ir, m), m)[:n]
        out[c] += wet * reverb

    out += _band(rng.standard_normal((n,)), 60, 400) * 0.002  # faint room tone
    out = out[:, : int(duration * SR)]
    out = np.tanh(_norm(out, 0.95) * 1.3) / np.tanh(1.3)
    data = (out.T * 32000).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    return path
