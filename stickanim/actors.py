"""Figures and cursors.

Authoring is sequential: you script each actor forward in time, and every helper
(walk, leap, ragdoll, ...) returns the time it finishes, so you can chain:

    t = fig.walk(900, t)
    t = fig.leap(0.6, 1200, floor, height=120, t0=t)

Because authoring is eager, physics runs while you script, and you can ask
"where is the figure's foot at t=18.6?" to aim the next shot.
"""

import bisect
import math

from . import poses
from .physics import Ragdoll
from .rig import HEAD_R, JOINTS, LEG, arm_ik, fk, leg_ik, lowest, points_to_pose

EASE = {
    "linear": lambda u: u,
    "smooth": lambda u: u * u * (3 - 2 * u),
    "in": lambda u: u * u * u,
    "out": lambda u: 1 - (1 - u) ** 3,
    "back": lambda u: 1 + 2.70158 * (u - 1) ** 3 + 1.70158 * (u - 1) ** 2,  # overshoot
    "snap": lambda u: 1 - (1 - u) ** 5,   # very fast start, long settle
    "hold": lambda u: 0.0,
}


def smooth(u):
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


def lerp_pose(a, b, u):
    return {j: a[j] + (b[j] - a[j]) * u for j in JOINTS}


# Follow-through: these joints chase their keyed angle through a springy filter, so fast
# moves overshoot and settle (frequency Hz, damping ratio). Legs are left exact so feet stay planted.
SPRINGS = {"head": (4.0, 0.42), "l_arm": (5.0, 0.38), "r_arm": (5.0, 0.38),
           "l_elbow": (6.0, 0.4), "r_elbow": (6.0, 0.4)}


class Figure:
    def __init__(self, scene, x, floor, facing=1, size=72, color=(30, 160, 70), width=None,
                 pose=poses.STAND, visible_from=0.0, hat=None):
        self.scene, self.fps, self.hat = scene, scene.fps, hat
        self.size, self.color = size, color
        self.width = width or round(size * 0.14)
        self.keys, self._times, self.sims = [], [], []
        self.strokes = None
        self.visible_from = visible_from
        self.visible_until = 1e9
        self.breathe = True
        self._springs = []      # per frame: {joint: (offset from keyed angle, velocity)}
        self._push(0.0, dict(x=x, y=0.0, facing=facing, spin=0.0, pose=dict(pose),
                             ground=floor, lift=0.0), "linear")

    # ------------------------------------------------------------------ keys

    @property
    def now(self):
        return self.keys[-1]["t"]

    @property
    def last(self):
        return self.keys[-1]

    def _snap_y(self, k):
        P = fk(k["pose"], 0.0, 0.0, k["facing"], k["spin"], self.size)
        return k["ground"] - k["lift"] - lowest(P, self.size, self.width)

    def _push(self, t, state, ease):
        k = dict(state, t=t, ease=ease)
        if k.get("ground") is not None:
            k["y"] = self._snap_y(k)
        if self.keys:
            self._dirty(min(t, self.now))
        if self.keys and t <= self.now:
            assert abs(t - self.now) < 1e-9, f"keys must be added in time order ({t} < {self.now})"
            self.keys.pop(); self._times.pop()
        self.keys.append(k)
        self._times.append(t)
        return k

    def key(self, t, pose=None, ease="smooth", **fields):
        """Keyframe at time t. Anything not given carries over from the previous key.

        fields: x, y, facing, spin, ground (floor y to stand on, or None for free y), lift
        """
        state = {k: v for k, v in self.last.items() if k not in ("t", "ease")}
        if "y" in fields and "ground" not in fields:
            state["ground"] = None
        state.update(fields)
        state["pose"] = {**self.last["pose"], **(pose or {})}
        self._push(t, state, ease)
        return t

    def hold(self, t):
        if t > self.now:
            self.key(t, ease="linear")
        return t

    def truncate(self, t):
        """Throw away everything scripted after t (e.g. a run that gets interrupted)."""
        if t >= self.now:
            return self.hold(t)
        s = self.state(t)
        self._dirty(t)
        keep = bisect.bisect_right(self._times, t)
        del self.keys[keep:], self._times[keep:]
        self.scene.sounds = [snd for snd in self.scene.sounds
                             if not (snd[4].get("owner") == id(self) and snd[0] > t)]
        self._push(t, dict(x=s["x"], y=s["y"], facing=s["facing"], spin=s["spin"], pose=s["pose"],
                           ground=None, lift=0.0), "linear")
        return t

    def turn(self, t, dur=0.07):
        self.hold(t)
        return self.key(t + dur, facing=-self.last["facing"], ease="linear")

    # ------------------------------------------------------------------ evaluation

    def state(self, t):
        i = bisect.bisect_right(self._times, t)
        if i == 0:
            return self.keys[0]
        if i >= len(self.keys):
            return self.keys[-1]
        a, b = self.keys[i - 1], self.keys[i]
        u = EASE[b["ease"]]((t - a["t"]) / (b["t"] - a["t"]))
        s = dict(x=lerp(a["x"], b["x"], u), spin=lerp(a["spin"], b["spin"], u),
                 lift=lerp(a["lift"], b["lift"], u), facing=b["facing"] if u >= 0.5 else a["facing"],
                 pose=lerp_pose(a["pose"], b["pose"], u), ground=None, y=lerp(a["y"], b["y"], u))
        if a["ground"] is not None and a["ground"] == b["ground"]:
            s["ground"] = a["ground"]
            s["y"] = self._snap_y(s)
        return s

    def _sim_at(self, t):
        for t0, t1, frames in self.sims:
            if t0 <= t <= t1:
                return t0, frames
        return None

    def points(self, t):
        sim = self._sim_at(t)
        if sim:
            t0, frames = sim
            f = (t - t0) * self.fps
            i = min(int(f), len(frames) - 2)
            u = f - i
            A, B = frames[i], frames[i + 1]
            return {k: (lerp(A[k][0], B[k][0], u), lerp(A[k][1], B[k][1], u)) for k in A}
        s = self.state(t)
        pose = dict(s["pose"])
        f = max(0.0, t * self.fps)
        i = int(f)
        a, b = self._spring(i), self._spring(i + 1)
        for j in SPRINGS:
            pose[j] += lerp(a[j], b[j], f - i)
        if self.breathe:
            w = 2 * math.pi * 0.33 * t
            pose["lean"] += 1.2 * math.sin(w)
            pose["head"] += 1.5 * math.sin(w + 0.8)
            pose["l_arm"] += 2.0 * math.sin(w + 1.6)
            pose["r_arm"] += 2.0 * math.sin(w + 2.2)
        return fk(pose, s["x"], s["y"], s["facing"], s["spin"], self.size)

    def _dirty(self, t):
        del self._springs[max(0, math.floor(t * self.fps)):]

    def _spring(self, k):
        """Spring offsets at frame k (computed causally, so later keys never change earlier frames)."""
        sub, dt = 4, 1 / (self.fps * 4)
        while len(self._springs) <= k:
            n = len(self._springs)
            t = n / self.fps
            if n == 0 or self._sim_at(t) or self._sim_at(t - 1 / self.fps):
                self._springs.append({j: (0.0, 0.0) for j in SPRINGS})
                continue
            target, prev_target = self.state(t)["pose"], self.state(t - 1 / self.fps)["pose"]
            out = {}
            for j, (hz, zeta) in SPRINGS.items():
                w = 2 * math.pi * hz
                off, v = self._springs[n - 1][j]
                x = prev_target[j] + off
                for i in range(1, sub + 1):
                    tgt = lerp(prev_target[j], target[j], i / sub)
                    v += (w * w * (tgt - x) - 2 * zeta * w * v) * dt
                    x += v * dt
                out[j] = (x - target[j], v)
            self._springs.append(out)
        return {j: o for j, (o, _) in self._springs[k].items()}

    def facing(self, t):
        sim = self._sim_at(t)
        if sim:
            i = bisect.bisect_right(self._times, sim[0])
            return self.keys[max(0, i - 1)]["facing"]
        return self.state(t)["facing"]

    def point(self, t, name):
        return self.points(t)[name]

    # ------------------------------------------------------------------ actions

    def reach(self, t, side, target, pose=None, ease="snap", bend=-1, **fields):
        """Key a pose where one hand lands exactly on `target` (world xy)."""
        self.key(t, pose=pose, ease=ease, **fields)
        k = self.last
        P = fk(k["pose"], k["x"], k["y"], k["facing"], k["spin"], self.size)
        arm_ik(k["pose"], P["neck"], target, side, k["facing"], self.size, bend)
        if k["ground"] is not None:
            k["y"] = self._snap_y(k)
        return t

    def walk(self, x1, t0=None, run=False, speed=1.0):
        """Walk or run to x1 with planted feet (no foot sliding). Returns the end time."""
        t0 = self.hold(self.now if t0 is None else t0)
        st, size, sc = self.last, self.size, self.scene
        ground = st["ground"]
        assert ground is not None, "walk() needs the figure to be standing on a floor"
        x0 = st["x"]
        f = 1 if x1 >= x0 else -1
        P = fk(st["pose"], x0, st["y"], f, 0, size)
        plant = {"l": P["l_foot"][0], "r": P["r_foot"][0]}
        foot_y = ground - self.width / 2

        step_len = (1.55 if run else 0.95) * size
        step_t = (0.15 if run else 0.29) / speed
        lift = (0.42 if run else 0.16) * size
        n = max(1, round(abs(x1 - x0) / step_len))
        L = abs(x1 - x0) / n
        order = ["l", "r"] if f * plant["l"] < f * plant["r"] else ["r", "l"]
        steps = []  # (foot, start_x, target_x, t_start, t_end)
        t = t0
        for i in range(1, n + 2):
            foot = order[(i - 1) % 2]
            if i <= n:
                target = x0 + f * (L * i + 0.35 * L) if i < n else x1 + f * 0.16 * size
                dur = step_t
            else:
                target, dur = x1 - f * 0.12 * size, step_t * 0.8
            steps.append((foot, plant[foot], target, t, t + dur))
            plant[foot] = target
            t += dur
        t_end, move_end = t, steps[n - 1][4]
        w = min(1.0, 1.5 / n)
        ease_x = lambda u: (1 - w) * u + w * smooth(u)

        base = dict(lean=16 if run else 4, head=-10 if run else -2)
        arm_k, elbow = (1.25, 95) if run else (0.8, 18)
        plant = {"l": P["l_foot"][0], "r": P["r_foot"][0]}
        k0 = math.floor(t0 * self.fps) + 1
        for k in range(k0, math.ceil(t_end * self.fps) + 1):
            tt = min(k / self.fps, t_end)
            hx = x0 + f * abs(x1 - x0) * ease_x(min(1.0, (tt - t0) / (move_end - t0)))
            feet = {}
            swing_u = 0.0
            for foot, sx, tx, ta, tb in steps:
                if tt >= tb:
                    feet[foot] = (tx, foot_y)
                elif tt >= ta:
                    u = (tt - ta) / (tb - ta)
                    swing_u = u
                    feet[foot] = (lerp(sx, tx, smooth(u)), foot_y - lift * math.sin(math.pi * u) ** (0.7 if run else 1))
            for foot in "lr":
                feet.setdefault(foot, (plant[foot], foot_y))
            reach = 0.985 * LEG * size
            h = LEG * size * (0.9 if run else 0.97)
            for foot, (fx_, fy) in feet.items():
                if fy >= foot_y - 1:
                    h = min(h, math.sqrt(max(reach ** 2 - (fx_ - hx) ** 2, 1)))
            if run:
                h += 0.10 * size * math.sin(math.pi * swing_u)
            hy = foot_y - h
            pose = dict(self.last["pose"], **base)
            for foot in "lr":
                leg_ik(pose, (hx, hy), feet[foot], foot, f, size)
            pose["l_arm"] = 10 + arm_k * pose["r_leg"]
            pose["r_arm"] = 10 + arm_k * pose["l_leg"]
            pose["l_elbow"] = pose["r_elbow"] = elbow
            self.key(tt, pose=pose, ease="linear", x=hx, y=hy, facing=f, spin=0.0)
        for foot, sx, tx, ta, tb in steps:
            sc.sfx(tb, "step", tx, gain=0.5 if run else 0.3, owner=id(self))
        self.key(t_end, ease="linear", ground=ground, lift=0.0)
        return t_end

    def leap(self, dur, x1, ground1, height, t0=None, spin=0.0, poses_=(), land=poses.CROUCH,
             facing=None, land_fx=True):
        """Ballistic jump to (x1, ground1). poses_: [(u, pose)] in-air keyframes, u in 0..1."""
        t0 = self.hold(self.now if t0 is None else t0)
        st = self.last
        f = facing or st["facing"]
        x0, y0 = st["x"], st["y"]
        end = dict(st, pose=dict(land), ground=ground1, lift=0.0, facing=f, spin=0.0)
        y1 = self._snap_y(end)
        track = [(0.0, st["pose"])] + [(u, {**st["pose"], **p}) for u, p in poses_] + [(1.0, land)]
        t1 = t0 + dur
        for k in range(math.floor(t0 * self.fps) + 1, math.ceil(t1 * self.fps)):
            tt = k / self.fps
            u = (tt - t0) / dur
            j = max(i for i, (uu, _) in enumerate(track) if uu <= u)
            (ua, pa), (ub, pb) = track[j], track[min(j + 1, len(track) - 1)]
            pu = smooth((u - ua) / (ub - ua)) if ub > ua else 1.0
            self.key(tt, pose=lerp_pose(pa, pb, pu), ease="linear", x=lerp(x0, x1, u),
                     y=(1 - u) * y0 + u * y1 - 4 * height * u * (1 - u), facing=f,
                     spin=spin * (0.5 * u + 0.5 * smooth(u)))
        self.key(t1, pose=land, ease="linear", x=x1, ground=ground1, lift=0.0, facing=f, spin=spin)
        if spin:
            self.key(t1 + 1e-4, ease="linear", spin=0.0)
        if land_fx:
            self.scene.dust(t1, x1, ground1, n=7, power=0.8)
            self.scene.sfx(t1, "land", x1)
        return t1

    def ragdoll(self, t0, t1, push=(0.0, 0.0), pins=(), bounds=None, ground=None, fx=True, kicks=()):
        """Hand the body to physics from t0 to t1.

        pins: [(point, cursor, t_from, t_to, (dx, dy))] — that joint follows the cursor.
        kicks: [(vx, vy, [points])] — extra velocity for particular joints (e.g. feet swept away).
        """
        self.truncate(t0)
        dt = 1 / self.fps
        P0, Pm = self.points(t0), self.points(t0 - dt)
        bounds = bounds or self.scene.bounds
        rd = Ragdoll(P0, Pm, dt, self.size, self.width, bounds)
        rd.push(*push)
        for vx, vy, pts in kicks:
            rd.push(vx, vy, pts)
        k0, k1 = round(t0 * self.fps), round(t1 * self.fps)
        frames = [P0]
        for k in range(k0 + 1, k1 + 1):
            t = k / self.fps
            targets = {}
            for name, cur, ta, tb, off in pins:
                if ta <= t <= tb:
                    cx, cy = cur.pos(t)
                    targets[name] = (cx + off[0], cy + off[1])
            frames.append(rd.step_frame(t - dt, targets))
        self.sims.append((k0 / self.fps, k1 / self.fps, frames))
        self._dirty(t0)
        if fx:
            for t, x, y, speed in rd.impacts:
                power = min(1.0, speed / 2200)
                self.scene.sfx(t, "thud", x, gain=0.4 + 0.6 * power)
                normal = ((1, 0) if x == bounds[0] else (-1, 0) if x == bounds[2]
                          else (0, 1) if y == bounds[1] else (0, -1))
                self.scene.dust(t, x, y, n=int(4 + 6 * power), power=power, normal=normal)
                if power > 0.45:
                    self.scene.shake(t, 14 * power, 0.3)
                if power > 0.6:
                    self.scene.impact(t, x, y, 0.6 * power)
        end = frames[-1]
        f = self.last["facing"]
        self._push(k1 / self.fps, dict(x=end["hip"][0], y=end["hip"][1], facing=f, spin=0.0,
                                       pose=points_to_pose(end, f), ground=ground, lift=0.0), "linear")
        return k1 / self.fps

    def draw_on(self, t0, t1, cursor):
        """Reveal the figure stroke by stroke while `cursor` traces it with a pencil."""
        self.hold(t0)
        self.visible_from = t0
        P = self.points(t0)
        r = HEAD_R * self.size
        hc = P["head"]
        head = [(hc[0] + r * math.sin(a), hc[1] - r * math.cos(a))
                for a in (2 * math.pi * i / 28 for i in range(29))]
        lines = [head, [P["neck"], P["hip"]],
                 [P["neck"], P["l_elbow"], P["l_hand"]], [P["neck"], P["r_elbow"], P["r_hand"]],
                 [P["hip"], P["l_knee"], P["l_foot"]], [P["hip"], P["r_knee"], P["r_foot"]]]
        lens = [sum(math.dist(a, b) for a, b in zip(s, s[1:])) for s in lines]
        gap = 0.12
        rate = sum(lens) / ((t1 - t0) - gap * (len(lines) - 1))
        self.strokes, t = [], t0
        for pts, ln in zip(lines, lens):
            self.strokes.append((pts, t, t + ln / rate))
            self.scene.sfx(t, "pencil", pts[0][0], dur=ln / rate)
            t += ln / rate + gap

        def tip(tt):
            for i, (pts, ta, tb) in enumerate(self.strokes):
                if tt <= tb:
                    if tt < ta:  # pen lifted, travelling to the next stroke
                        prev = self.strokes[i - 1][0][-1]
                        u = smooth((tt - (ta - gap)) / gap)
                        return lerp(prev[0], pts[0][0], u), lerp(prev[1], pts[0][1], u) - 10 * math.sin(math.pi * u)
                    return along(pts, (tt - ta) / (tb - ta))
            return self.strokes[-1][0][-1]

        for k in range(math.ceil(t0 * self.fps), math.floor(t1 * self.fps) + 1):
            x, y = tip(k / self.fps)
            cursor.key(k / self.fps, x=x, y=y, ease="linear")
        return self.hold(t1)


def along(pts, u):
    """Point at fraction u along a polyline."""
    return partial(pts, u)[-1]


def partial(pts, u):
    """The first fraction u of a polyline."""
    if u >= 1:
        return list(pts)
    segs = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    d, out = u * sum(segs), [pts[0]]
    for (a, b), s in zip(zip(pts, pts[1:]), segs):
        if d >= s:
            out.append(b)
            d -= s
        else:
            v = d / s if s else 0
            out.append((lerp(a[0], b[0], v), lerp(a[1], b[1], v)))
            break
    return out


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


class Sprite:
    """Anything with keyed position and properties: cursors, props, HUD text.

    Numeric fields (x, y, rot, scale, alpha, value...) interpolate; everything else steps.
    """

    def __init__(self, scene, x, y, **fields):
        self.scene, self.fps = scene, scene.fps
        self.keys, self._times, self.attached = [], [], []
        self.key(0.0, **{"x": x, "y": y, "rot": 0.0, "visible": True, **fields})

    @property
    def now(self):
        return self.keys[-1]["t"]

    def key(self, t, ease="smooth", **fields):
        state = {k: v for k, v in self.keys[-1].items() if k not in ("t", "ease")} if self.keys else {}
        state.update(fields)
        if self.keys and t <= self.now:
            self.keys.pop(); self._times.pop()
        self.keys.append(dict(state, t=t, ease=ease))
        self._times.append(t)
        return t

    def hold(self, t):
        if t > self.now:
            self.key(t, ease="linear")
        return t

    def show(self, t, **fields):
        return self.key(t, ease="linear", visible=True, **fields)

    def hide(self, t):
        return self.key(t, ease="linear", visible=False)

    def move(self, t1, x, y, t0=None, ease="smooth", arc=0.12, **fields):
        """Curved move to (x, y) arriving at t1; numeric fields given here animate along the way."""
        t0 = self.hold(self.now if t0 is None else t0)
        x0, y0 = self.pos(t0)
        dx, dy = x - x0, y - y0
        cx, cy = (x0 + x) / 2 - dy * arc, (y0 + y) / 2 + dx * arc
        start = self.keys[-1]
        tween = {k: (start[k], v) for k, v in fields.items() if _num(v) and _num(start.get(k))}
        for k in range(math.floor(t0 * self.fps) + 1, math.ceil(t1 * self.fps)):
            tt = k / self.fps
            u = EASE[ease]((tt - t0) / (t1 - t0))
            bx = (1 - u) ** 2 * x0 + 2 * u * (1 - u) * cx + u * u * x
            by = (1 - u) ** 2 * y0 + 2 * u * (1 - u) * cy + u * u * y
            self.key(tt, ease="linear", x=bx, y=by, **{f: lerp(a, b, u) for f, (a, b) in tween.items()})
        return self.key(t1, ease="linear", x=x, y=y, **fields)

    def attach(self, t0, t1, fig, point, offset=(0.0, 0.0)):
        """Glue to a figure's joint from t0 to t1 (e.g. the figure grabs it). t1=None: until detach()."""
        self.hold(t0)
        self.attached.append((t0, 1e18 if t1 is None else t1, fig, point, offset))
        if t1 is None:
            return t0
        x, y = fig.point(t1, point)
        return self.key(t1, ease="linear", x=x + offset[0], y=y + offset[1])

    def detach(self, t):
        """End the current attachment at t; the sprite stays where the joint was."""
        t0, _, fig, point, off = self.attached[-1]
        self.attached[-1] = (t0, t, fig, point, off)
        x, y = fig.point(t, point)
        self.keys = [k for k in self.keys if k["t"] < t]
        self._times = [k["t"] for k in self.keys]
        return self.key(t, ease="linear", x=x + off[0], y=y + off[1])

    def _interp(self, t):
        i = bisect.bisect_right(self._times, t)
        if i == 0:
            return self.keys[0], self.keys[0], 0.0
        if i >= len(self.keys):
            return self.keys[-1], self.keys[-1], 0.0
        a, b = self.keys[i - 1], self.keys[i]
        return a, b, EASE[b["ease"]]((t - a["t"]) / (b["t"] - a["t"]))

    def pos(self, t):
        for t0, t1, fig, point, off in self.attached:
            if t0 <= t <= t1:
                x, y = fig.point(t, point)
                return x + off[0], y + off[1]
        a, b, u = self._interp(t)
        return lerp(a["x"], b["x"], u), lerp(a["y"], b["y"], u)

    def look(self, t):
        a, b, u = self._interp(t)
        out = {}
        for k, v in a.items():
            if k in ("t", "ease"):
                continue
            w = b.get(k, v)
            out[k] = lerp(v, w, u) if _num(v) and _num(w) else (v if u < 1 else w)
        out["visible"] = a["visible"] if u < 1 else b["visible"]
        out["x"], out["y"] = self.pos(t)
        return out


class Cursor(Sprite):
    """The mouse pointer: position, rotation, icon (arrow/open/grab/pencil/eraser), clicks."""

    def __init__(self, scene, x, y, icon="arrow", scale=1.8):
        super().__init__(scene, x, y, icon=icon, scale=scale)

    def click(self, t, sound=True):
        self.hold(t)
        x, y = self.pos(t)
        self.scene.ring(t, x, y)
        if sound:
            self.scene.sfx(t, "click", x)
        return t


class Prop(Sprite):
    """A drawable object (coin, rug, candle, banner...). kind picks the drawing in props.py.

    layer: "back" (behind figures), "front" (in front of figures) or "hud" (screen space,
    unaffected by camera pan, shake and zoom).
    """

    def __init__(self, scene, kind, x, y, layer="back", visible=True, **params):
        self.layer = layer
        super().__init__(scene, x, y, **{"kind": kind, "scale": 1.0, "alpha": 1.0, **params})
        if not visible:
            self.keys[0]["visible"] = False
