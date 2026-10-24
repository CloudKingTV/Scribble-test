"""stickanim — a tiny keyframe engine for hand-drawn ("scribble") stick-figure videos.

Pipeline:  Figure keyframes  ->  forward kinematics  ->  wobbly strokes (PIL)  ->  ffmpeg  ->  .mp4

Angles are in degrees. 0 means "pointing straight down", positive values swing
the limb toward the direction the figure is facing. Every joint is relative to
its parent, so a pose reads like instructions to a puppet:

    lean      torso tilt (positive = lean forward)
    head      head tilt, relative to the torso
    l_arm     upper arm, relative to hanging straight down the torso
    l_elbow   forearm, relative to the upper arm (positive = bend forward)
    l_leg     thigh, relative to hanging straight down
    l_knee    shin, relative to the thigh (negative = normal knee bend)
    (same for r_*)
"""

import math
import random
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

JOINTS = ["lean", "head", "l_arm", "l_elbow", "r_arm", "r_elbow",
          "l_leg", "l_knee", "r_leg", "r_knee"]
STAND = {**{j: 0.0 for j in JOINTS},
         # slight splay so limbs don't hide behind each other in profile
         "l_arm": 10, "r_arm": -8, "l_elbow": 12, "r_elbow": 6, "l_leg": 7, "r_leg": -6}

# Bone lengths as fractions of the figure's `size` (torso length).
TORSO, NECK, HEAD_R = 1.0, 0.12, 0.30
UPPER_ARM, FOREARM = 0.55, 0.50
THIGH, SHIN = 0.62, 0.62


# --------------------------------------------------------------------------- easing

EASINGS = {
    "linear": lambda u: u,
    "smooth": lambda u: u * u * (3 - 2 * u),
    "in": lambda u: u * u,
    "out": lambda u: 1 - (1 - u) * (1 - u),
}


# --------------------------------------------------------------------------- poses

def walk_pose(phase, stride=28):
    """One frame of a walk cycle; `phase` runs 0..1 per two steps."""
    s = math.sin(2 * math.pi * phase)
    c = math.cos(2 * math.pi * phase)
    return {
        "lean": 4, "head": -3,
        "l_leg": stride * s, "r_leg": -stride * s,
        "l_knee": -max(0.0, 45 * c), "r_knee": -max(0.0, -45 * c),
        "l_arm": -stride * 0.8 * s, "r_arm": stride * 0.8 * s,
        "l_elbow": 20, "r_elbow": 20,
    }


def wave_pose(t, arm="r"):
    """Standing and waving one arm overhead; call with a time in seconds."""
    p = dict(STAND)
    p[f"{arm}_arm"] = 135
    p[f"{arm}_elbow"] = 25 * math.sin(t * 2 * math.pi * 2.5)
    other = "l" if arm == "r" else "r"
    p[f"{other}_arm"] = -10
    p["head"] = 6
    return p


SQUAT = {**STAND, "lean": 20, "l_leg": 50, "r_leg": 45, "l_knee": -95, "r_knee": -90,
         "l_arm": -40, "r_arm": -35, "l_elbow": 30, "r_elbow": 30}
CHEER = {**STAND, "lean": -5, "head": -10, "l_arm": 150, "r_arm": -150,
         "l_elbow": 10, "r_elbow": -10, "l_leg": 10, "r_leg": -10,
         "l_knee": -20, "r_knee": -20}


# --------------------------------------------------------------------------- figure

class Figure:
    """A stick figure driven by keyframes of (x, lift, facing, pose)."""

    def __init__(self, x, size=110, color=(25, 25, 30), width=5, facing=1, seed=0):
        self.size, self.color, self.width, self.seed = size, color, width, seed
        self.keys = []          # sorted list of (time, state dict, easing)
        self.key(0, x=x, lift=0, facing=facing, pose=STAND)

    def key(self, t, ease="smooth", pose=None, **state):
        """Add a keyframe at time t. Anything omitted carries over from the previous key."""
        prev = self._state_at_key(t)
        new = {**prev, **state}
        new["pose"] = {**prev.get("pose", STAND), **(pose or {})}
        self.keys = [k for k in self.keys if k[0] != t]
        self.keys.append((t, new, ease))
        self.keys.sort(key=lambda k: k[0])
        return self

    def hold(self, t0, t1):
        """Keep the current state from t0 until t1."""
        return self.key(t1, ease="linear", **self._state_at_key(t0))

    def walk(self, t0, t1, x1, steps_per_sec=1.8):
        """Walk from wherever the figure is at t0 to x1, arriving at t1."""
        start = self._state_at_key(t0)
        x0 = start["x"]
        facing = 1 if x1 >= x0 else -1
        n = max(2, int((t1 - t0) * 24))
        for i in range(n + 1):
            u = i / n
            t = t0 + u * (t1 - t0)
            pose = walk_pose(u * (t1 - t0) * steps_per_sec / 2)
            if i == n:
                pose = STAND
            self.key(t, ease="linear", x=x0 + u * (x1 - x0), facing=facing, pose=pose)
        return self

    def wave(self, t0, t1, arm="r"):
        n = max(2, int((t1 - t0) * 24))
        for i in range(n + 1):
            t = t0 + i * (t1 - t0) / n
            self.key(t, ease="linear", pose=wave_pose(t - t0, arm))
        return self.key(t1 + 0.3, pose=STAND)

    def jump(self, t0, height=140):
        """Squat, leap, land. Takes 1.2 seconds."""
        self.key(t0 + 0.30, pose=SQUAT, lift=0)
        self.key(t0 + 0.65, ease="out", pose=CHEER, lift=height)
        self.key(t0 + 1.00, ease="in", pose={**CHEER, "l_knee": -10, "r_knee": -10}, lift=0)
        self.key(t0 + 1.10, ease="out", pose=SQUAT, lift=0)
        self.key(t0 + 1.20, pose=STAND, lift=0)
        return self

    # ---- evaluation

    def _state_at_key(self, t):
        before = [k for k in self.keys if k[0] <= t]
        return dict(before[-1][1]) if before else {}

    def state(self, t):
        keys = self.keys
        if t <= keys[0][0]:
            return keys[0][1]
        for (ta, a, _), (tb, b, ease) in zip(keys, keys[1:]):
            if ta <= t <= tb:
                u = EASINGS[ease]((t - ta) / (tb - ta) if tb > ta else 1)
                lerp = lambda p, q: p + (q - p) * u
                return {
                    "x": lerp(a["x"], b["x"]),
                    "lift": lerp(a["lift"], b["lift"]),
                    "facing": b["facing"] if u > 0.5 else a["facing"],
                    "pose": {j: lerp(a["pose"][j], b["pose"][j]) for j in JOINTS},
                }
        return keys[-1][1]

    def skeleton(self, t, ground_y):
        """Forward kinematics: returns head (center, radius) and a list of bones."""
        st = self.state(t)
        p, f, s = st["pose"], st["facing"], self.size

        def step(origin, angle, length):
            a = math.radians(angle)
            return (origin[0] + f * math.sin(a) * length * s,
                    origin[1] + math.cos(a) * length * s)

        hip = (0.0, 0.0)
        torso_a = 180 - p["lean"]          # pointing up, tilted forward by lean
        neck = step(hip, torso_a, TORSO)
        head_a = torso_a - p["head"]
        head_c = step(neck, head_a, NECK + HEAD_R)
        down = torso_a - 180                # "hanging" direction along the torso

        bones = [(hip, neck)]
        for side in "lr":
            elbow = step(neck, down + p[f"{side}_arm"], UPPER_ARM)
            hand = step(elbow, down + p[f"{side}_arm"] + p[f"{side}_elbow"], FOREARM)
            bones += [(neck, elbow), (elbow, hand)]
        feet = []
        for side in "lr":
            knee = step(hip, p[f"{side}_leg"], THIGH)
            foot = step(knee, p[f"{side}_leg"] + p[f"{side}_knee"], SHIN)
            bones += [(hip, knee), (knee, foot)]
            feet.append(foot)

        # Plant the lowest foot on the ground, then add jump lift.
        dy = ground_y - max(ft[1] for ft in feet) - st["lift"]
        shift = lambda pt: (pt[0] + st["x"], pt[1] + dy)
        bones = [(shift(a), shift(b)) for a, b in bones]
        return shift(head_c), HEAD_R * s, bones


# --------------------------------------------------------------------------- scribble drawing

class Pen:
    """Draws wobbly, slightly doubled lines that 'boil' like hand-drawn animation."""

    def __init__(self, draw, scale, rng, wobble=2.2):
        self.d, self.k, self.rng, self.wobble = draw, scale, rng, wobble

    def _jit(self, amount=1.0):
        return self.rng.uniform(-1, 1) * self.wobble * amount

    def line(self, a, b, color, width, passes=2):
        length = math.dist(a, b)
        n = max(2, int(length / 18))
        nx, ny = ((b[1] - a[1]) / length, -(b[0] - a[0]) / length) if length else (0, 0)
        for pi in range(passes):
            bow = self._jit(1.5)  # each pass curves a little differently
            pts = []
            for i in range(n + 1):
                u = i / n
                off = bow * math.sin(math.pi * u) + self._jit(0.5)
                pts.append(((a[0] + (b[0] - a[0]) * u + nx * off + self._jit(0.3)) * self.k,
                            (a[1] + (b[1] - a[1]) * u + ny * off + self._jit(0.3)) * self.k))
            w = width if pi == 0 else max(1, width * 0.55)
            self.d.line(pts, fill=color, width=int(w * self.k), joint="curve")
            for x, y in (pts[0], pts[-1]):  # round caps
                r = w * self.k / 2
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=color)

    def circle(self, c, r, color, width, passes=2):
        for pi in range(passes):
            start = self.rng.uniform(0, 2 * math.pi)
            sweep = 2 * math.pi + self.rng.uniform(0.15, 0.5)  # overshoot like a real pen
            n = 28
            rx, ry = r + self._jit(0.8), r + self._jit(0.8)
            pts = [((c[0] + math.cos(start + sweep * i / n) * (rx + self._jit(0.3))) * self.k,
                    (c[1] + math.sin(start + sweep * i / n) * (ry + self._jit(0.3))) * self.k)
                   for i in range(n + 1)]
            w = width if pi == 0 else max(1, width * 0.55)
            self.d.line(pts, fill=color, width=int(w * self.k), joint="curve")


def paper_texture(w, h, seed=1):
    rng = np.random.default_rng(seed)
    base = np.full((h, w, 3), (250, 247, 238), dtype=np.float32)
    grain = rng.normal(0, 3.5, (h, w, 1))
    yy, xx = np.mgrid[0:h, 0:w]
    vignette = ((xx - w / 2) ** 2 / (w / 2) ** 2 + (yy - h / 2) ** 2 / (h / 2) ** 2) * 10
    img = base + grain - vignette[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


# --------------------------------------------------------------------------- scene + render

class Scene:
    def __init__(self, width=1280, height=720, fps=24, duration=10.0, ground_y=None,
                 boil_fps=8, supersample=2):
        self.w, self.h, self.fps, self.duration = width, height, fps, duration
        self.ground_y = ground_y if ground_y is not None else height * 0.82
        self.boil_fps, self.ss = boil_fps, supersample
        self.figures, self.texts, self.extras = [], [], []
        self.paper = paper_texture(width * supersample, height * supersample)

    def add(self, fig):
        self.figures.append(fig)
        return fig

    def say(self, fig, text, t0, t1, size=40):
        """Speech bubble that follows a figure's head."""
        self.texts.append(("bubble", fig, text, t0, t1, size))

    def title(self, text, t0, t1, size=96, y=None):
        self.texts.append(("title", None, text, t0, t1, size, y))

    def render_frame(self, t, frame_idx):
        ss = self.ss
        img = self.paper.copy()
        d = ImageDraw.Draw(img)
        # Re-seed every 1/boil_fps seconds so lines jitter at a hand-drawn rate.
        boil = int(frame_idx * self.boil_fps / self.fps)
        pen_rng = random.Random(boil * 7919)
        pen = Pen(d, ss, pen_rng)

        pen.line((40, self.ground_y), (self.w - 40, self.ground_y), (60, 60, 70), 3)
        for fig in self.figures:
            fig_pen = Pen(d, ss, random.Random(boil * 7919 + fig.seed * 104729))
            head, r, bones = fig.skeleton(t, self.ground_y)
            for a, b in bones:
                fig_pen.line(a, b, fig.color, fig.width)
            fig_pen.circle(head, r, fig.color, fig.width)
        for item in self.texts:
            self._draw_text(d, pen, item, t)
        return img.resize((self.w, self.h), Image.LANCZOS)

    def _font(self, size):
        for path in ("/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf",
                     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
            try:
                return ImageFont.truetype(path, int(size * self.ss))
            except OSError:
                pass
        return ImageFont.load_default(int(size * self.ss))

    def _draw_text(self, d, pen, item, t):
        kind, fig, text, t0, t1, size = item[:6]
        if not (t0 <= t <= t1):
            return
        font = self._font(size)
        ss = self.ss
        x0, y0, x1, y1 = d.textbbox((0, 0), text, font=font)
        tw, th = (x1 - x0) / ss, (y1 - y0) / ss
        if kind == "title":
            y = item[6] if item[6] is not None else self.h * 0.2
            cx = self.w / 2
            d.text(((cx - tw / 2) * ss - x0, (y - th / 2) * ss - y0), text,
                   font=font, fill=(25, 25, 30))
            pen.line((cx - tw / 2, y + th / 2 + 14), (cx + tw / 2, y + th / 2 + 18), (200, 60, 50), 5)
            return
        head, r, _ = fig.skeleton(t, self.ground_y)
        facing = fig.state(t)["facing"]
        bw, bh = tw + 40, th + 30
        bx = head[0] + facing * (r + 30) + (0 if facing > 0 else -bw)
        by = head[1] - r - bh - 20
        corners = [(bx, by), (bx + bw, by), (bx + bw, by + bh), (bx, by + bh)]
        for a, b in zip(corners, corners[1:] + corners[:1]):
            pen.line(a, b, (25, 25, 30), 3, passes=1)
        tail_x = bx + (25 if facing > 0 else bw - 25)
        pen.line((tail_x, by + bh), (head[0] + facing * r * 0.8, head[1] - r * 0.8), (25, 25, 30), 3, passes=1)
        d.text(((bx + 20) * ss - x0, (by + 15) * ss - y0), text, font=font, fill=(25, 25, 30))

    def render(self, path, crf=18):
        """Pipe raw frames into ffmpeg and write an H.264 mp4."""
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{self.w}x{self.h}",
               "-r", str(self.fps), "-i", "-",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf),
               "-movflags", "+faststart", path]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        total = int(self.duration * self.fps)
        for i in range(total):
            proc.stdin.write(self.render_frame(i / self.fps, i).tobytes())
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("ffmpeg failed")
        return path
