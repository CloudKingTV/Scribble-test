"""Scene: holds actors, effects and sounds; bakes everything and renders to MP4 with ffmpeg."""

import math
import os
import random
import subprocess
import tempfile
from multiprocessing import Pool

from PIL import Image, ImageDraw

from . import audio
from .actors import Cursor, Figure, Prop, Sprite, partial
from .desktop import Desktop, draw_cursor, font
from .props import draw_hud, draw_world
from .rig import HEAD_R

LIMBS = [("neck", "l_elbow"), ("l_elbow", "l_hand"), ("neck", "r_elbow"), ("r_elbow", "r_hand"),
         ("hip", "l_knee"), ("l_knee", "l_foot"), ("hip", "r_knee"), ("r_knee", "r_foot"), ("hip", "neck")]
BODY = [("hip", "neck"), ("neck", "head")] + LIMBS[:-1]


class Scene:
    def __init__(self, duration, width=1920, height=1080, fps=30, ss=2, backdrop=None):
        self.duration, self.W, self.H, self.fps, self.ss = duration, width, height, fps, ss
        self.backdrop = backdrop or Desktop()
        self.bounds = self.backdrop.CANVAS
        self.world_w = getattr(self.backdrop, "WORLD_W", width)
        self.figures, self.cursors, self.props = [], [], []
        self.fx, self.sounds, self.hitstops, self.overlays = [], [], [], []
        self.camera = Sprite(self, width / 2, height / 2)   # camera centre in world x

    # ------------------------------------------------------------------ actors

    def figure(self, x, floor, **kw):
        fig = Figure(self, x, floor, **kw)
        self.figures.append(fig)
        return fig

    def cursor(self, x, y, **kw):
        cur = Cursor(self, x, y, **kw)
        self.cursors.append(cur)
        return cur

    def prop(self, kind, x, y, layer="back", **params):
        p = Prop(self, kind, x, y, layer=layer, **params)
        self.props.append(p)
        return p

    # ------------------------------------------------------------------ camera

    def pan(self, t1, x, t0=None, ease="smooth"):
        """Move the camera so world x is centred on screen, arriving at t1."""
        return self.camera.move(t1, x, self.H / 2, t0=t0, ease=ease, arc=0)

    def follow(self, fig, t0, t1, lead=120.0, stiffness=3.0):
        """Smoothly track a figure (with some look-ahead in the direction it faces)."""
        self.camera.hold(t0)
        x = self.camera.pos(t0)[0]
        for k in range(round(t0 * self.fps) + 1, round(t1 * self.fps) + 1):
            t = k / self.fps
            target = fig.point(t, "hip")[0] + lead * fig.facing(t)
            x += (target - x) * (1 - math.exp(-stiffness / self.fps))
            self.camera.key(t, ease="linear", x=x)
        return t1

    # ------------------------------------------------------------------ effects & sound

    def sfx(self, t, name, x=None, gain=1.0, **params):
        self.sounds.append((t, name, x, gain, params))

    def ring(self, t, x, y):
        self.fx.append(dict(kind="ring", t=t, x=x, y=y))

    def dust(self, t, x, y, n=8, power=1.0, normal=(0, -1)):
        self.fx.append(dict(kind="dust", t=t, x=x, y=y, n=n, power=power, normal=normal,
                            seed=len(self.fx)))

    def impact(self, t, x, y, power=1.0):
        self.fx.append(dict(kind="impact", t=t, x=x, y=y, power=power, seed=len(self.fx)))

    def shake(self, t, amp, dur=0.35):
        self.fx.append(dict(kind="shake", t=t, amp=amp, dur=dur, seed=len(self.fx)))

    def flash(self, t, strength=0.6):
        self.fx.append(dict(kind="flash", t=t, strength=strength))

    def zoom(self, t, z, x, y, hold=0.1, release=0.5):
        self.fx.append(dict(kind="zoom", t=t, z=z, x=x, y=y, hold=hold, release=release))

    def explosion(self, t, x, y, power=1.0, sound=True):
        """Fireball, smoke, flying dirt, shake and a boom."""
        self.fx.append(dict(kind="explosion", t=t, x=x, y=y, power=power, seed=len(self.fx)))
        self.dust(t, x, y, n=10, power=power)
        self.shake(t, 10 + 22 * power, 0.45)
        if sound:
            self.sfx(t, "boom", x, gain=0.55 + 0.45 * power)

    def tracer(self, t, x0, y0, x1, y1, sound=True):
        """A bullet streak from (x0, y0) to (x1, y1)."""
        self.fx.append(dict(kind="tracer", t=t, x=x1, y=y1, x0=x0, y0=y0))
        if sound:
            self.sfx(t, "gunshot", x1, gain=0.5)

    def hitstop(self, t, dur):
        """Freeze the world for `dur` seconds at t (effects and camera keep moving)."""
        self.hitstops.append((t, dur))

    def hit(self, t, x, y, power=1.0, sound=None):
        """Everything a good hit needs: sound, burst, shake, freeze-frame (and flash/zoom when big)."""
        self.sfx(t, sound or ("big_hit" if power > 0.85 else "hit"), x, gain=0.6 + 0.4 * power, power=power)
        self.impact(t, x, y, power)
        self.shake(t, 6 + 22 * power, 0.25 + 0.3 * power)
        self.hitstop(t, 0.04 + 0.13 * power)
        if power > 0.85:
            self.flash(t, 0.45)
            self.zoom(t, 1 + 0.12 * power, x, y, hold=0.1 + 0.1 * power)

    def fade_out(self, t0, t1):
        self.overlays.append(dict(kind="fade", t0=t0, t1=t1))

    def fade_in(self, t0, t1):
        """Black until t0, then fade up to the picture by t1."""
        self.overlays.append(dict(kind="fade_in", t0=t0, t1=t1))

    def title(self, t0, t1, text, sub="", color=(255, 255, 255), size=130, y=None):
        self.overlays.append(dict(kind="title", t0=t0, t1=t1, text=text, sub=sub, color=color, size=size, y=y))

    # ------------------------------------------------------------------ baking

    def bake(self):
        fps = self.fps
        K = int(round(self.duration * fps))
        stops = {}
        for t, d in self.hitstops:
            k = round(t * fps)
            stops[k] = max(stops.get(k, 0), round(d * fps))
        kmap, first = [], []
        for k in range(K):
            first.append(len(kmap))
            kmap.extend([k] * (1 + stops.get(k, 0)))

        def rt(t):
            k = max(0, min(K - 1, round(t * fps)))
            return first[k] / fps + (t - k / fps)

        figs = []
        for fig in self.figures:
            frames = []
            for k in range(K):
                t = k / fps
                if t < fig.visible_from or t > fig.visible_until:
                    frames.append(None)
                elif fig.strokes and t < fig.strokes[-1][2]:
                    lines = [(partial(pts, min(1.0, (t - ta) / (tb - ta))), i == 0, t >= tb)
                             for i, (pts, ta, tb) in enumerate(fig.strokes) if t >= ta]
                    frames.append(("strokes", lines))
                else:
                    frames.append(fig.points(t))
            figs.append(dict(color=fig.color, width=fig.width, size=fig.size, frames=frames, hat=fig.hat,
                             facing=[fig.facing(k / fps) for k in range(K)]))
        curs = [[c.look(k / fps) for k in range(K)] for c in self.cursors]
        props = [dict(layer=p.layer, frames=[p.look(k / fps) for k in range(K)]) for p in self.props]
        cam = [min(max(self.camera.pos(k / fps)[0] - self.W / 2, 0), max(0, self.world_w - self.W)) for k in range(K)]
        fx = [dict(e, T=rt(e["t"])) for e in self.fx]
        overlays = [dict(o, T0=rt(o["t0"]), T1=rt(o["t1"])) for o in self.overlays]
        sounds = [(rt(t), n, x, g, p) for t, n, x, g, p in self.sounds if t < self.duration]
        return dict(W=self.W, H=self.H, fps=fps, ss=self.ss, backdrop=self.backdrop, kmap=kmap,
                    figs=figs, curs=curs, props=props, cam=cam, fx=fx, overlays=overlays, sounds=sounds)

    # ------------------------------------------------------------------ output

    def still(self, t, path, data=None):
        data = data or self.bake()
        k = round(t * self.fps)
        i = data["kmap"].index(min(k, data["kmap"][-1]))
        _init(data)
        Image.frombytes("RGB", (self.W, self.H), _render(i)).save(path)
        return path

    def render(self, path, workers=None, crf=18):
        data = self.bake()
        n = len(data["kmap"])
        wav = os.path.join(tempfile.mkdtemp(), "audio.wav")
        audio.mix(data["sounds"], n / self.fps, self.W, wav)
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{self.W}x{self.H}", "-r", str(self.fps), "-i", "-",
               "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", path]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(workers or os.cpu_count(), initializer=_init, initargs=(data,)) as pool:
            for i, buf in enumerate(pool.imap(_render, range(n), chunksize=4)):
                proc.stdin.write(buf)
                if i % 60 == 0:
                    print(f"\rframe {i}/{n}", end="", flush=True)
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("ffmpeg failed")
        print(f"\rwrote {path} ({n} frames)")
        return path


# ---------------------------------------------------------------------- frame rendering (worker side)

_G = {}


def _init(data):
    _G["d"] = data


def _render(i):
    return render_frame(_G["d"], i).tobytes()


def render_frame(D, i):
    fps, ss, W, H = D["fps"], D["ss"], D["W"], D["H"]
    k = D["kmap"][i]
    t, T = k / fps, i / fps
    ox = D["cam"][k]
    bd = D["backdrop"]
    img = bd.base(t, ss, ox) if getattr(bd, "SCROLLS", False) else bd.base(t, ss)
    d = ImageDraw.Draw(img, "RGBA")
    bd.overlay(d, t, ss)
    shift = lambda P: {n: (x - ox, y) for n, (x, y) in P.items()}

    def props(layer):
        for p in D["props"]:
            look = p["frames"][k]
            if p["layer"] == layer and look["visible"] and look["alpha"] > 0.01:
                draw_world(d, look, ss, ox)

    props("back")
    for fig in D["figs"]:
        cur = fig["frames"][k]
        if cur is None:
            continue
        if isinstance(cur, tuple):
            _draw_strokes(d, [([(x - ox, y) for x, y in p], h, done) for p, h, done in cur[1]], fig, ss)
            continue
        prev = [fig["frames"][j] if j >= 0 else None for j in (k - 1, k - 2)]
        prev = [shift(p) for p in prev if isinstance(p, dict)]
        P = shift(cur)
        _draw_smears(d, P, prev, fig, ss)
        _draw_body(d, P, fig, ss, fig["facing"][k])
    props("front")
    if hasattr(bd, "foreground"):
        bd.foreground(d, t, ss, ox)

    active = [dict(e, x=e["x"] - ox, x0=e.get("x0", 0) - ox) if "x" in e else e
              for e in D["fx"] if 0 <= T - e["T"] < 2.0]
    for e in active:
        if e["kind"] == "dust":
            _draw_dust(d, e, T - e["T"], ss)
        elif e["kind"] == "explosion":
            _draw_explosion(d, e, T - e["T"], ss)
    for e in active:
        if e["kind"] == "impact":
            _draw_impact(d, e, T - e["T"], ss)
        elif e["kind"] == "ring":
            _draw_ring(d, e, T - e["T"], ss)
        elif e["kind"] == "tracer":
            _draw_tracer(d, e, T - e["T"], ss)
    for frames in D["curs"]:
        look = frames[k]
        if look["visible"]:
            draw_cursor(d, dict(look, x=look["x"] - ox), ss)

    out = _camera(img, active, T, W, H, ss)
    hud = ImageDraw.Draw(out, "RGBA")
    for p in D["props"]:
        look = p["frames"][k]
        if p["layer"] == "hud" and look["visible"] and look["alpha"] > 0.01:
            draw_hud(hud, look, W, H)
    _draw_overlays(out, D, active, T)
    return out


def _line(d, a, b, color, w, ss):
    d.line([a[0] * ss, a[1] * ss, b[0] * ss, b[1] * ss], fill=color, width=round(w * ss))
    r = w * ss / 2
    for x, y in (a, b):
        d.ellipse([x * ss - r, y * ss - r, x * ss + r, y * ss + r], fill=color)


def _draw_body(d, P, fig, ss, facing=1):
    c, w = fig["color"], fig["width"]
    for a, b in BODY:
        _line(d, P[a], P[b], c, w, ss)
    r = HEAD_R * fig["size"]
    hx, hy = P["head"]
    nx, ny = P["neck"]
    ln = math.hypot(hx - nx, hy - ny) or 1
    up = ((hx - nx) / ln, (hy - ny) / ln)
    side = (-up[1], up[0])
    fwd = (side[0] * facing, side[1] * facing)
    at = lambda u, s_, rr=1.0: ((hx + (up[0] * u + side[0] * s_) * r * rr) * ss, (hy + (up[1] * u + side[1] * s_) * r * rr) * ss)
    if fig["hat"] == "hood":
        tip = ((hx + (-fwd[0] * 1.9 - up[0] * 0.2) * r) * ss, (hy + (-fwd[1] * 1.9 - up[1] * 0.2) * r) * ss)
        dome = [at(math.cos(a), math.sin(a), 1.3) for a in (math.radians(d_) for d_ in range(-120, 121, 10))]
        d.polygon(dome + [tip], fill=(34, 22, 44))
    d.ellipse([(hx - r) * ss, (hy - r) * ss, (hx + r) * ss, (hy + r) * ss], fill=c)
    if fig["hat"] == "hood":
        for dx in (0.25, 0.62):
            ex, ey = (hx + fwd[0] * r * dx + up[0] * r * 0.1) * ss, (hy + fwd[1] * r * dx + up[1] * r * 0.1) * ss
            er = r * 0.13 * ss
            d.ellipse([ex - er * 2, ey - er * 2, ex + er * 2, ey + er * 2], fill=(255, 40, 60, 70))
            d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(255, 60, 70))
    elif fig["hat"] == "helmet":
        cx, cy = hx + up[0] * r * 0.18, hy + up[1] * r * 0.18
        dome = [((cx + (up[0] * math.cos(a) + side[0] * math.sin(a)) * r * 1.12) * ss,
                 (cy + (up[1] * math.cos(a) + side[1] * math.sin(a)) * r * 1.12) * ss)
                for a in (math.radians(d_) for d_ in range(-92, 93, 8))]
        d.polygon(dome, fill=(88, 102, 58), outline=(36, 42, 26), width=round(2 * ss))
        b0 = ((cx + side[0] * r * 1.45) * ss, (cy + side[1] * r * 1.45) * ss)
        b1 = ((cx - side[0] * r * 1.45) * ss, (cy - side[1] * r * 1.45) * ss)
        d.line([b0, b1], fill=(60, 70, 40), width=round(r * 0.28 * ss))


def _draw_strokes(d, lines, fig, ss):
    c, w = fig["color"], fig["width"]
    for pts, is_head, done in lines:
        if is_head and done:
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
            r = HEAD_R * fig["size"] * ss
            d.ellipse([cx * ss - r, cy * ss - r, cx * ss + r, cy * ss + r], fill=c)
            continue
        if len(pts) > 1:
            d.line([(x * ss, y * ss) for x, y in pts], fill=c, width=round(w * ss), joint="curve")
        r = w * ss / 2
        for x, y in (pts[0], pts[-1]):
            d.ellipse([x * ss - r, y * ss - r, x * ss + r, y * ss + r], fill=c)


def _draw_smears(d, P, prev, fig, ss):
    """Smear frames for fast limbs, speed lines when the whole body is flying."""
    c = fig["color"]
    if not prev:
        return
    Q = prev[0]
    vx, vy = P["hip"][0] - Q["hip"][0], P["hip"][1] - Q["hip"][1]
    body_speed = math.hypot(vx, vy)
    for a, b in LIMBS:
        # how fast the limb tip moves relative to the body, not just travelling with it
        rel = math.hypot(P[b][0] - Q[b][0] - vx, P[b][1] - Q[b][1] - vy)
        if rel < 20:
            continue
        alpha = min(1.0, (rel - 20) / 50) * 0.32
        poly = [(Q[a][0] + vx, Q[a][1] + vy), (Q[b][0] + vx, Q[b][1] + vy), P[b], P[a]]
        d.polygon([(x * ss, y * ss) for x, y in poly], fill=c + (int(255 * alpha),))
    if body_speed > 34:
        ux, uy = vx / body_speed, vy / body_speed
        length = min(body_speed * 2.2, 260)
        alpha = int(150 * min(1.0, (body_speed - 34) / 40))
        for i, name in enumerate(("head", "neck", "hip", "l_foot", "r_hand")):
            x, y = P[name]
            off = (i - 2) * 9
            x, y = x - ux * 30 - uy * off, y - uy * 30 + ux * off
            ln = length * (0.6 + 0.4 * ((i * 7) % 3) / 2)
            d.line([x * ss, y * ss, (x - ux * ln) * ss, (y - uy * ln) * ss], fill=(40, 40, 50, alpha),
                   width=round(2 * ss))


def _draw_dust(d, e, age, ss):
    life = 0.6
    if age > life:
        return
    rng = random.Random(e["seed"])
    nx, ny = e["normal"]
    tx, ty = -ny, nx
    p = e["power"]
    for _ in range(e["n"]):
        side = rng.choice((-1, 1))
        th = math.radians(rng.uniform(8, 55))
        dx, dy = tx * side * math.cos(th) + nx * math.sin(th), ty * side * math.cos(th) + ny * math.sin(th)
        v = rng.uniform(90, 260) * (0.5 + p)
        dist = v * age * (1 - age / (2 * life))
        x, y = e["x"] + dx * dist, e["y"] + dy * dist - 25 * age
        r = (5 + 9 * p) * rng.uniform(0.7, 1.3) * (1 + 1.8 * age)
        a = int(170 * (1 - age / life) ** 1.4)
        d.ellipse([(x - r) * ss, (y - r) * ss, (x + r) * ss, (y + r) * ss], fill=(175, 175, 182, a))


def _draw_impact(d, e, age, ss):
    life = 0.22
    if age > life:
        return
    u = age / life
    p = e["power"]
    x, y = e["x"] * ss, e["y"] * ss
    R = (34 + 70 * p) * (0.6 + 1.2 * u ** 0.5) * ss
    rng = random.Random(e["seed"])
    spikes = 11
    rot = rng.uniform(0, 1)
    pts = []
    for i in range(spikes * 2):
        a = 2 * math.pi * (i + rot) / (spikes * 2)
        rr = R * (1 if i % 2 == 0 else 0.45) * rng.uniform(0.8, 1.15)
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    alpha = int(255 * (1 - u) ** 0.7)
    if u < 0.6:
        d.polygon(pts, fill=(255, 236, 120, alpha), outline=(25, 25, 30, alpha), width=round(3 * ss))
        d.polygon([(x + (px - x) * 0.45, y + (py - y) * 0.45) for px, py in pts], fill=(255, 255, 255, alpha))
    rr = R * (0.8 + 1.4 * u)
    d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(25, 25, 30, int(200 * (1 - u))), width=round(4 * ss * (1 - u) + 1))
    for i in range(8):
        a = 2 * math.pi * (i / 8 + rot)
        r1, r2 = R * (1.1 + 1.5 * u), R * (1.5 + 2.6 * u)
        d.line([x + r1 * math.cos(a), y + r1 * math.sin(a), x + r2 * math.cos(a), y + r2 * math.sin(a)],
               fill=(25, 25, 30, int(220 * (1 - u))), width=round(3 * ss))


def _draw_explosion(d, e, age, ss):
    rng = random.Random(e["seed"])
    p, x, y = e["power"], e["x"], e["y"]
    for _ in range(14):                     # flying dirt
        vx, vy = rng.uniform(-480, 480) * p, rng.uniform(-1000, -380) * p
        size = rng.uniform(4, 10) * p
        px, py = x + vx * age, y + vy * age + 1800 * age * age
        if age < 1.0 and py < y + 30:
            d.polygon([((px + size * math.cos(a + age * 9)) * ss, (py + size * math.sin(a + age * 9)) * ss)
                       for a in (0, 2.1, 4.2)], fill=(72, 54, 38))
    for _ in range(10):                     # smoke
        delay = rng.uniform(0, 0.18)
        a2 = age - delay
        dx, rise = rng.uniform(-70, 70) * p, rng.uniform(50, 110)
        if 0 < a2 < 1.8:
            r = (28 + 55 * a2) * p * rng.uniform(0.8, 1.2)
            cx, cy = x + dx + 25 * a2, y - 40 * p - rise * a2
            g = rng.randint(45, 75)
            d.ellipse([(cx - r) * ss, (cy - r) * ss, (cx + r) * ss, (cy + r) * ss],
                      fill=(g, g - 5, g, int(190 * (1 - a2 / 1.8))))
    if age < 0.42:                          # fireball
        u = age / 0.42
        col = (255, int(235 - 150 * u), int(140 - 120 * u))
        for _ in range(8):
            fx_, fy_ = rng.uniform(-55, 55) * p, rng.uniform(-90, 5) * p
            r = (24 + 110 * u ** 0.5) * p * rng.uniform(0.55, 1.0)
            d.ellipse([(x + fx_ - r) * ss, (y + fy_ - r) * ss, (x + fx_ + r) * ss, (y + fy_ + r) * ss],
                      fill=col + (int(255 * (1 - u) ** 0.7),))
    if age < 0.07:
        r = 100 * p
        d.ellipse([(x - r) * ss, (y - r - 30) * ss, (x + r) * ss, (y + r - 30) * ss], fill=(255, 255, 240, 230))


def _draw_tracer(d, e, age, ss):
    dur = 0.07
    u = age / dur
    if u > 1.4:
        return
    lerp = lambda a, b, v: a + (b - a) * max(0.0, min(1.0, v))
    hx, hy = lerp(e["x0"], e["x"], u), lerp(e["y0"], e["y"], u)
    tx, ty = lerp(e["x0"], e["x"], u - 0.4), lerp(e["y0"], e["y"], u - 0.4)
    alpha = int(255 * (1 if u < 1 else (1.4 - u) / 0.4))
    d.line([tx * ss, ty * ss, hx * ss, hy * ss], fill=(255, 236, 150, alpha), width=round(3 * ss))
    if u >= 1:
        r = 10 * ss
        d.ellipse([e["x"] * ss - r, e["y"] * ss - r, e["x"] * ss + r, e["y"] * ss + r], fill=(255, 240, 180, alpha))


def _draw_ring(d, e, age, ss):
    life = 0.3
    if age > life:
        return
    r = (4 + 55 * age / life) * ss
    a = int(220 * (1 - age / life))
    d.ellipse([e["x"] * ss - r, e["y"] * ss - r, e["x"] * ss + r, e["y"] * ss + r],
              outline=(60, 130, 255, a), width=round(3 * ss))


def _camera(img, active, T, W, H, ss):
    z, cx, cy = 1.0, W / 2, H / 2
    for e in active:
        if e["kind"] == "zoom":
            a = T - e["T"]
            if a < 0.05:
                f = a / 0.05
            elif a < 0.05 + e["hold"]:
                f = 1.0
            else:
                u = min(1.0, (a - 0.05 - e["hold"]) / e["release"])
                f = 1 - u * u * (3 - 2 * u)
            if (e["z"] - 1) * f > z - 1:
                z = 1 + (e["z"] - 1) * f
                cx, cy = W / 2 + (e["x"] - W / 2) * f, H / 2 + (e["y"] - H / 2) * f
    sx = sy = 0.0
    for e in active:
        if e["kind"] == "shake":
            a = T - e["T"]
            if a < e["dur"]:
                amp = e["amp"] * (1 - a / e["dur"]) ** 2
                ph = e["seed"] * 1.7
                sx += amp * (math.sin(a * 2 * math.pi * 19 + ph) + 0.6 * math.sin(a * 2 * math.pi * 31 + 2 * ph)) / 1.6
                sy += amp * (math.sin(a * 2 * math.pi * 23 + 3 * ph) + 0.6 * math.sin(a * 2 * math.pi * 37 + ph)) / 1.6
    if z == 1.0 and sx == 0 and sy == 0:
        return img.reduce(ss)
    z = max(z, 1 + 2.2 * max(abs(sx) / W, abs(sy) / H))
    w, h = W / z, H / z
    x0 = min(max(cx - w / 2, 0), W - w) + sx
    y0 = min(max(cy - h / 2, 0), H - h) + sy
    x0, y0 = min(max(x0, 0), W - w), min(max(y0, 0), H - h)
    box = (x0 * ss, y0 * ss, (x0 + w) * ss, (y0 + h) * ss)
    return img.resize((W, H), Image.BOX, box=box)


def _draw_overlays(out, D, active, T):
    W, H = D["W"], D["H"]
    d = ImageDraw.Draw(out, "RGBA")
    for e in active:
        if e["kind"] == "flash":
            a = T - e["T"]
            if a < 0.12:
                d.rectangle([0, 0, W, H], fill=(255, 255, 255, int(255 * e["strength"] * (1 - a / 0.12))))
    for o in D["overlays"]:          # fades first, so title cards sit on top of the black
        if o["kind"] == "fade_in" and T < o["T1"]:
            u = 0.0 if T < o["T0"] else (T - o["T0"]) / max(1e-6, o["T1"] - o["T0"])
            d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * (1 - u))))
        elif o["kind"] == "fade" and T >= o["T0"]:
            u = min(1.0, (T - o["T0"]) / max(1e-6, o["T1"] - o["T0"]))
            d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * u)))
    for o in D["overlays"]:
        if o["kind"] == "title" and o["T0"] <= T <= o["T1"]:
            u = min(1.0, (T - o["T0"]) / 0.35) * min(1.0, (o["T1"] - T) / 0.3)
            s = 1 + 0.25 * (1 - min(1.0, (T - o["T0"]) / 0.35)) ** 3
            f = font(int(o.get("size", 130) * s), bold=True)
            y = o.get("y") or H / 2 - 30
            d.text((W / 2, y), o["text"], font=f, fill=tuple(o.get("color", (255, 255, 255))) + (int(255 * u),),
                   anchor="mm")
            if o["sub"]:
                d.text((W / 2, y + o.get("size", 130) * 0.75), o["sub"], font=font(34),
                       fill=(200, 205, 215, int(255 * u)), anchor="mm")
