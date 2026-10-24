"""Verlet ragdoll for when a figure gets grabbed, thrown or knocked around."""

import math

from .rig import BONES, HEAD_R, LEG, UPPER_ARM, FOREARM, POINTS

GRAVITY = 2600.0  # px/s^2 — a bit heavier than real life, which reads as snappier


class Ragdoll:
    def __init__(self, P, prev_P, dt_frame, size, width, bounds, substeps=4):
        """P / prev_P: point dicts for this frame and the previous one (gives initial velocity)."""
        self.size, self.bounds, self.sub = size, bounds, substeps
        self.dt = dt_frame / substeps
        self.pos = {k: list(P[k]) for k in POINTS}
        # previous position per substep, so velocity carries over from the animation
        self.prev = {k: [P[k][0] - (P[k][0] - prev_P[k][0]) / substeps,
                         P[k][1] - (P[k][1] - prev_P[k][1]) / substeps] for k in POINTS}
        self.radius = {k: width / 2 for k in POINTS}
        self.radius["head"] = HEAD_R * size
        dist = lambda a, b: math.dist(P[a], P[b])
        self.links = [(a, b, dist(a, b), dist(a, b)) for a, b in BONES]
        self.links.append(("hip", "head", dist("hip", "head"), dist("hip", "head")))  # stiff spine
        for s in "lr":  # stop limbs folding flat onto themselves
            self.links.append(("hip", s + "_foot", 0.35 * LEG * size, 1e9))
            self.links.append(("neck", s + "_hand", 0.35 * (UPPER_ARM + FOREARM) * size, 1e9))
        self.pins = {}
        self.impacts = []  # (substep_time, x, y, speed)

    def push(self, vx, vy, points=None):
        for k in points or POINTS:
            self.prev[k][0] -= vx * self.dt
            self.prev[k][1] -= vy * self.dt

    def step_frame(self, t, pins):
        """Advance one animation frame. pins: {point: (x, y)} targets (positions at end of frame)."""
        for i in range(self.sub):
            u = (i + 1) / self.sub
            self._step(t + u * self.dt * self.sub, {k: self._lerp_pin(k, v, u) for k, v in pins.items()})
        self.pins = dict(pins)
        return {k: tuple(v) for k, v in self.pos.items()}

    def _lerp_pin(self, k, target, u):
        start = self.pins.get(k, self.pos[k])
        return (start[0] + (target[0] - start[0]) * u, start[1] + (target[1] - start[1]) * u)

    def _step(self, t, pins):
        g = GRAVITY * self.dt * self.dt
        for k in POINTS:
            p, q = self.pos[k], self.prev[k]
            vx, vy = (p[0] - q[0]) * 0.998, (p[1] - q[1]) * 0.998
            q[0], q[1] = p[0], p[1]
            p[0] += vx
            p[1] += vy + g
        for _ in range(8):
            for a, b, lo, hi in self.links:
                pa, pb = self.pos[a], self.pos[b]
                dx, dy = pb[0] - pa[0], pb[1] - pa[1]
                d = math.hypot(dx, dy) or 1e-6
                target = lo if d < lo else hi if d > hi else d
                if target == d:
                    continue
                c = (d - target) / d * 0.5
                pa[0] += dx * c; pa[1] += dy * c
                pb[0] -= dx * c; pb[1] -= dy * c
            for k, (x, y) in pins.items():
                self.pos[k][0], self.pos[k][1] = x, y
            self._collide(t)

    def _collide(self, t):
        x0, y0, x1, y1 = self.bounds
        for k in POINTS:
            p, q, r = self.pos[k], self.prev[k], self.radius[k]
            vx, vy = (p[0] - q[0]) / self.dt, (p[1] - q[1]) / self.dt
            if p[1] > y1 - r:          # floor: bounce a little, lots of friction
                p[1] = y1 - r
                q[1] = p[1] + vy * 0.25 * self.dt
                q[0] = p[0] - vx * 0.80 * self.dt
                self._hit(t, p[0], y1, abs(vy))
            elif p[1] < y0 + r:
                p[1] = y0 + r
                q[1] = p[1] + vy * 0.3 * self.dt
                self._hit(t, p[0], y0, abs(vy))
            if p[0] < x0 + r:
                p[0] = x0 + r
                q[0] = p[0] + vx * 0.3 * self.dt
                self._hit(t, x0, p[1], abs(vx))
            elif p[0] > x1 - r:
                p[0] = x1 - r
                q[0] = p[0] + vx * 0.3 * self.dt
                self._hit(t, x1, p[1], abs(vx))

    def _hit(self, t, x, y, speed):
        if speed < 450:
            return
        if self.impacts and t - self.impacts[-1][0] < 0.12:
            last = self.impacts[-1]
            if speed > last[3]:
                self.impacts[-1] = (last[0], x, y, speed)
            return
        self.impacts.append((t, x, y, speed))
