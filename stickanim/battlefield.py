"""A side-scrolling WW1-style trench, re-dressed for the Solana memecoin trenches.

Layers: a far layer (sky, smoke, candlestick-chart skyline, no-man's land) that scrolls slower
than the camera, the trench itself (back wall, sandbags, revetment, duckboards) at camera speed,
and drifting ash in front.
"""

import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .props import mono


class Battlefield:
    SCROLLS = True
    W, H = 1920, 1080
    WORLD_W = 9000
    FLOOR = 905            # duckboards the figures stand on
    PARAPET = 545          # top of the back wall
    MID_TOP = 440
    HORIZON = 470
    PARALLAX = 0.3
    CANVAS = (-400, -4000, WORLD_W + 400, FLOOR)   # ragdoll bounds: open sky, solid floor

    def __init__(self, seed=3, crates=(), signs=()):
        self.seed, self.crates, self.signs = seed, list(crates), list(signs)
        self.flashes = []
        self._cache = {}

    def flash(self, t, x, power=1.0):
        """A distant artillery flash on the horizon near world x."""
        self.flashes.append((t, x, power))

    def __getstate__(self):
        return {k: v for k, v in self.__dict__.items() if k != "_cache"}

    def __setstate__(self, d):
        self.__dict__.update(d, _cache={})

    # ------------------------------------------------------------------ per frame

    def base(self, t, ss, ox):
        far, mid = self._far(ss), self._mid(ss)
        fx = int(round(ox * self.PARALLAX * ss))
        img = far.crop((fx, 0, fx + self.W * ss, self.H * ss))
        d = ImageDraw.Draw(img, "RGBA")
        for tf, x, p in self.flashes:
            age = t - tf
            if 0 <= age < 0.6:
                sx = (x - ox) * self.PARALLAX + self.W / 2 * (1 - self.PARALLAX)
                a = (1 - age / 0.6) ** 2
                for r, al in ((420, 0.18), (220, 0.35), (90, 0.6)):
                    rr = r * p
                    d.ellipse([(sx - rr) * ss, (self.HORIZON - rr * 0.55) * ss, (sx + rr) * ss,
                               (self.HORIZON + rr * 0.35) * ss], fill=(255, 170, 90, int(255 * al * a)))
        mx = int(round(ox * ss))
        layer = mid.crop((mx, 0, mx + self.W * ss, mid.height))
        img.paste(layer, (0, self.MID_TOP * ss), layer)
        return img

    def overlay(self, d, t, ss):
        pass

    def foreground(self, d, t, ss, ox):
        """Drifting ash and embers (slight parallax in front of everything)."""
        rng = random.Random(11)
        for i in range(70):
            x0, y0 = rng.uniform(0, 1), rng.uniform(0, 1)
            speed, size = rng.uniform(20, 60), rng.uniform(1.5, 3.5)
            ember = i % 9 == 0
            x = (x0 * (self.W + 200) - ox * 1.15 - 18 * t * (1 + i % 3)) % (self.W + 200) - 100
            y = (y0 * self.H + speed * t + 12 * math.sin(t * 0.8 + i)) % self.H
            col = (255, 150, 60, 200) if ember else (200, 195, 200, 110)
            d.ellipse([(x - size) * ss, (y - size) * ss, (x + size) * ss, (y + size) * ss], fill=col)

    # ------------------------------------------------------------------ static layers

    def _far(self, ss):
        key = ("far", ss)
        if key in self._cache:
            return self._cache[key]
        W = int(self.W + self.WORLD_W * self.PARALLAX) + 4
        H = self.H
        rng = np.random.default_rng(self.seed)
        y = np.linspace(0, 1, H)[:, None]
        stops = [(0.0, (12, 8, 24)), (0.25, (44, 20, 74)), (0.38, (96, 40, 112)), (0.44, (40, 130, 112)),
                 (0.5, (22, 40, 44)), (1.0, (14, 14, 18))]
        sky = np.zeros((H, 1, 3), np.float32)
        for (u0, c0), (u1, c1) in zip(stops, stops[1:]):
            m = (y >= u0) & (y <= u1)
            v = np.clip((y - u0) / (u1 - u0), 0, 1)
            col = np.array(c0, np.float32) * (1 - v) + np.array(c1, np.float32) * v
            sky = np.where(m[..., None], col[:, None, :], sky)
        img = np.repeat(sky, W, axis=1)
        # smoke clouds: low-frequency noise, darker where dense
        small = rng.random((H // 40 + 2, W // 40 + 2)).astype(np.float32)
        clouds = np.array(Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC),
                          np.float32) / 255
        clouds = np.clip((clouds - 0.45) * 2.2, 0, 1) * (y < 0.6)
        img = img * (1 - 0.45 * clouds[..., None]) + np.array((30, 22, 36), np.float32) * 0.45 * clouds[..., None]
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im, "RGBA")

        # candlestick-chart skyline along the horizon: pumps, then cliffs, over and over
        r = random.Random(self.seed)
        price, x, base = 60.0, 0, self.HORIZON + 4
        while x < W:
            dx = 44
            phase = (x // 900) % 3
            move = r.gauss(9, 10) if phase < 2 else r.gauss(-14, 12)
            o, c = price, max(20.0, min(300.0, price + move))
            price = c
            hi, lo = max(o, c) + r.uniform(4, 22), min(o, c) - r.uniform(4, 22)
            col = (40, 150, 110, 120) if c >= o else (170, 50, 75, 120)
            d.line([x + dx / 2, base - hi, x + dx / 2, base - lo], fill=col, width=3)
            d.rectangle([x + 8, base - max(o, c), x + dx - 8, base - min(o, c) + 3], fill=col)
            x += dx
        im = im.filter(ImageFilter.GaussianBlur(1.2))
        d = ImageDraw.Draw(im, "RGBA")
        # no-man's land: dark ground with craters, dead trees and wire posts
        pts = [(0, H)]
        for xx in range(0, W + 40, 40):
            pts.append((xx, self.HORIZON + 8 * math.sin(xx / 170) + 5 * math.sin(xx / 53)))
        pts.append((W, H))
        d.polygon(pts, fill=(26, 24, 26))
        for _ in range(W // 260):
            cx = r.uniform(0, W)
            cy = self.HORIZON + r.uniform(20, 60)
            rw = r.uniform(40, 110)
            d.ellipse([cx - rw, cy - rw * 0.18, cx + rw, cy + rw * 0.18], fill=(16, 15, 17))
        for _ in range(W // 380):
            tx = r.uniform(0, W)
            ty = self.HORIZON + r.uniform(-4, 10)
            h = r.uniform(60, 130)
            d.line([tx, ty, tx + r.uniform(-10, 10), ty - h], fill=(20, 18, 20), width=5)
            for _ in range(3):
                by = ty - h * r.uniform(0.4, 0.9)
                d.line([tx, by, tx + r.uniform(-40, 40), by - r.uniform(10, 35)], fill=(20, 18, 20), width=3)
        for xx in range(0, W, 120):
            d.line([xx, self.HORIZON + 30, xx + 6, self.HORIZON + 2], fill=(24, 22, 24), width=3)
        far = im.resize((W * ss, H * ss), Image.BICUBIC)
        self._cache[key] = far
        return far

    def _mid(self, ss):
        key = ("mid", ss)
        if key in self._cache:
            return self._cache[key]
        k = ss
        W, top = self.WORLD_W, self.MID_TOP
        Hm = self.H - top
        Y = lambda y: (y - top) * k
        r = random.Random(self.seed + 1)
        im = Image.new("RGBA", (W * k, Hm * k), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)

        # barbed wire beyond the parapet
        wy = self.PARAPET - 46
        for x in range(0, W, 230):
            px = x + r.uniform(-30, 30)
            d.line([px * k, Y(wy - 40), (px + 18) * k, Y(self.PARAPET)], fill=(40, 34, 30), width=4 * k)
            d.line([(px + 18) * k, Y(wy - 40), px * k, Y(self.PARAPET)], fill=(40, 34, 30), width=4 * k)
        for x in range(0, W, 26):
            d.arc([x * k, Y(wy - 22), (x + 40) * k, Y(wy + 12)], 0, 360, fill=(70, 66, 64), width=2 * k)
            for bx in range(x, x + 26, 9):
                d.line([bx * k, Y(wy - 8), (bx + 4) * k, Y(wy - 3)], fill=(90, 86, 84), width=k)

        # back wall: irregular dirt top, filled down to the floor
        edge = [(0, Y(self.H))]
        for x in range(0, W + 40, 40):
            edge.append((x * k, Y(self.PARAPET + 6 * math.sin(x / 97) + r.uniform(-3, 3))))
        edge.append((W * k, Y(self.H)))
        d.polygon(edge, fill=(70, 52, 38, 255))

        # sandbags along the parapet, two staggered rows
        for row, yy in enumerate((self.PARAPET - 4, self.PARAPET + 22)):
            x = -40 + row * 30
            while x < W:
                w = r.uniform(58, 70)
                c = r.randint(-12, 12)
                d.rounded_rectangle([x * k, Y(yy - 15), (x + w) * k, Y(yy + 15)], 13 * k,
                                    fill=(146 + c, 130 + c, 96 + c), outline=(70, 60, 44), width=2 * k)
                d.line([(x + 8) * k, Y(yy), (x + w - 8) * k, Y(yy + 2)], fill=(120 + c, 105 + c, 76 + c), width=k)
                x += w - 2

        # wooden revetment planks and posts
        for yy in range(self.PARAPET + 50, self.FLOOR - 4, 27):
            x = 0
            while x < W:
                w = r.uniform(180, 320)
                c = r.randint(-10, 10)
                if r.random() > 0.06:
                    d.rectangle([x * k, Y(yy), (x + w - 3) * k, Y(yy + 23)], fill=(100 + c, 74 + c, 48 + c))
                    d.line([x * k, Y(yy + 23), (x + w - 3) * k, Y(yy + 23)], fill=(52, 38, 26), width=2 * k)
                    for _ in range(2):
                        gx = x + r.uniform(10, w - 20)
                        d.line([gx * k, Y(yy + 6), (gx + 30) * k, Y(yy + 7)], fill=(84 + c, 62 + c, 40 + c), width=k)
                x += w
        for x in range(60, W, 270):
            d.rectangle([x * k, Y(self.PARAPET + 20), (x + 18) * k, Y(self.FLOOR)], fill=(64, 46, 30),
                        outline=(40, 28, 18), width=k)

        # duckboards and mud
        d.rectangle([0, Y(self.FLOOR), W * k, Y(self.H)], fill=(48, 38, 30))
        for x in range(0, W, 120):
            d.rectangle([x * k, Y(self.FLOOR), (x + 116) * k, Y(self.FLOOR + 14)], fill=(118, 90, 58),
                        outline=(60, 44, 28), width=k)
            for sx in range(x + 12, x + 116, 22):
                d.line([sx * k, Y(self.FLOOR), sx * k, Y(self.FLOOR + 14)], fill=(80, 60, 38), width=k)
        for _ in range(W // 300):
            px, pw = r.uniform(0, W), r.uniform(60, 160)
            py = r.uniform(self.FLOOR + 40, self.H - 30)
            d.ellipse([(px - pw) * k, Y(py - 8), (px + pw) * k, Y(py + 8)], fill=(40, 60, 70))
            d.ellipse([(px - pw * 0.6) * k, Y(py - 3), (px + pw * 0.2) * k, Y(py + 1)], fill=(80, 70, 110))

        for x, label in self.crates:
            y = self.FLOOR
            d.rectangle([x * k, Y(y - 70), (x + 110) * k, Y(y)], fill=(112, 96, 56), outline=(50, 40, 24), width=3 * k)
            d.line([x * k, Y(y - 70), (x + 110) * k, Y(y)], fill=(80, 66, 36), width=4 * k)
            d.text(((x + 55) * k, Y(y - 35)), label, font=mono(13 * k), fill=(30, 26, 16), anchor="mm")
        for x, label in self.signs:
            d.line([x * k, Y(self.PARAPET + 40), x * k, Y(self.PARAPET + 150)], fill=(70, 50, 30), width=6 * k)
            fnt = mono(17 * k)
            tw = d.textlength(label, font=fnt) / k / 2 + 14
            d.polygon([((x - tw) * k, Y(self.PARAPET + 50)), ((x + tw) * k, Y(self.PARAPET + 44)),
                       ((x + tw) * k, Y(self.PARAPET + 78)), ((x - tw) * k, Y(self.PARAPET + 84))],
                      fill=(170, 130, 80), outline=(60, 40, 20), width=2 * k)
            d.text((x * k, Y(self.PARAPET + 64)), label, font=fnt, fill=(40, 24, 10), anchor="mm")

        # dirt texture over everything opaque
        arr = np.array(im)
        noise = np.random.default_rng(self.seed).normal(0, 9, arr.shape[:2]).astype(np.float32)
        solid = arr[..., 3] > 0
        for c in range(3):
            ch = arr[..., c].astype(np.float32)
            ch[solid] += noise[solid]
            arr[..., c] = np.clip(ch, 0, 255).astype(np.uint8)
        im = Image.fromarray(arr)
        self._cache[key] = im
        return im
