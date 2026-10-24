"""The stage: a computer desktop with a drawing-app window, plus mouse cursor icons."""

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_PATHS = ["/usr/share/fonts/opentype/inter/Inter-Medium.otf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/System/Library/Fonts/Helvetica.ttc", "C:/Windows/Fonts/segoeui.ttf"]
BOLD_PATHS = ["/usr/share/fonts/opentype/inter/Inter-Black.otf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/System/Library/Fonts/Helvetica.ttc", "C:/Windows/Fonts/segoeuib.ttf"]


def font(size, bold=False):
    for p in BOLD_PATHS if bold else FONT_PATHS:
        try:
            return ImageFont.truetype(p, int(size))
        except OSError:
            pass
    return ImageFont.load_default(int(size))


def rrect(x0, y0, x1, y1, r, n=5):
    """Rounded rectangle as a polygon (so it can be rotated)."""
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


class Desktop:
    W, H = 1920, 1080
    WINDOW = (300, 90, 1620, 930)
    TITLE_H, TOOLBAR_W = 46, 74
    CANVAS = (374, 138, 1618, 928)
    TASKBAR_Y = 1016
    CLOSE = (1564, 90, 1620, 136)
    APP_ICON = (150, 1048)
    TOOLS = {"select": 172, "pencil": 234, "eraser": 296, "bucket": 358, "line": 420, "shapes": 482}
    TOOL_X = 337

    def __init__(self, title="Untitled - Sketch"):
        self.title = title
        self.opens, self.closes, self.hovers = [], [], []
        self.tools = [(0.0, "select")]
        self._cache = {}

    # -------------------------------------------------------------- timeline

    def open_window(self, t):
        self.opens.append(t)

    def close_window(self, t):
        self.closes.append(t)

    def select_tool(self, t, tool):
        self.tools.append((t, tool))

    def hover_close(self, t0, t1):
        self.hovers.append((t0, t1))

    def tool_pos(self, tool):
        return self.TOOL_X, self.TOOLS[tool]

    def window_state(self, t):
        """(scale, alpha) of the window, or None when it's hidden."""
        events = sorted([(o, "open") for o in self.opens] + [(c, "close") for c in self.closes])
        state = None
        for te, kind in events:
            if t < te:
                break
            age = t - te
            if kind == "open":
                u = min(1.0, age / 0.32)
                s = 1 + 2.2 * (u - 1) ** 3 + 1.2 * (u - 1) ** 2  # overshoot
                state = (0.82 + 0.18 * s, min(1.0, age / 0.15))
            else:
                u = min(1.0, age / 0.28)
                state = None if u >= 1 else (1 - 0.12 * u * u, 1 - u)
        return state

    def __getstate__(self):
        return {k: v for k, v in self.__dict__.items() if k != "_cache"}

    def __setstate__(self, d):
        self.__dict__.update(d, _cache={})

    # -------------------------------------------------------------- drawing

    def base(self, t, ss):
        """Background image (wallpaper + window) at supersampled resolution."""
        ws = self.window_state(t)
        hover = any(a <= t <= b for a, b in self.hovers)
        if ws is None:
            return self._static("bg", ss).copy()
        if ws == (1.0, 1.0):
            return self._static("hover" if hover else "full", ss).copy()
        img = self._static("bg", ss).copy()
        layer, (lx, ly) = self._window_layer(ss, hover)
        s, a = ws
        w, h = layer.size
        lay = layer.resize((max(1, int(w * s)), max(1, int(h * s))), Image.BILINEAR)
        if a < 1:
            alpha = lay.getchannel("A").point(lambda v: int(v * a))
            lay.putalpha(alpha)
        cx, cy = lx + w / 2, ly + h / 2
        img.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)
        return img

    def overlay(self, draw, t, ss):
        """Per-frame UI bits: selected tool highlight, taskbar indicator."""
        ws = self.window_state(t)
        k = ss
        if ws is not None:
            x, y = self.APP_ICON
            draw.rounded_rectangle([(x - 14) * k, 1074 * k, (x + 14) * k, 1077 * k], 2 * k, fill=(120, 190, 255))
        if ws == (1.0, 1.0):
            tool = [n for tt, n in self.tools if tt <= t][-1]
            ty = self.TOOLS[tool]
            draw.rounded_rectangle([(self.TOOL_X - 24) * k, (ty - 24) * k, (self.TOOL_X + 24) * k, (ty + 24) * k],
                                   7 * k, fill=(60, 120, 230, 60), outline=(60, 120, 230, 200), width=2 * k)

    def _static(self, which, ss):
        key = (which, ss)
        if key not in self._cache:
            if which == "bg":
                self._cache[key] = self._wallpaper(ss)
            else:
                img = self._static("bg", ss).copy()
                layer, pos = self._window_layer(ss, which == "hover")
                img.paste(layer, pos, layer)
                self._cache[key] = img
        return self._cache[key]

    def _wallpaper(self, ss):
        W, H = self.W, self.H
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        u = (xx / W * 0.45 + yy / H * 0.55)[..., None]
        img = np.array([28, 30, 70], np.float32) * (1 - u) + np.array([18, 110, 140], np.float32) * u
        for cx, cy, r, col, a in ((1500, 250, 520, (90, 70, 190), 0.35), (350, 900, 600, (30, 170, 160), 0.3),
                                  (1100, 700, 380, (200, 90, 160), 0.15)):
            g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))[..., None] * a
            img = img * (1 - g) + np.array(col, np.float32) * g
        img = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W * ss, H * ss), Image.BICUBIC)
        d = ImageDraw.Draw(img, "RGBA")
        k = ss
        f = font(15 * k)
        for i, (label, kind) in enumerate([("Projects", "folder"), ("Photos", "folder"),
                                           ("notes.txt", "doc"), ("Trash", "trash")]):
            x, y = 70, 70 + i * 118
            if kind == "folder":
                d.rounded_rectangle([(x - 30) * k, (y - 26) * k, (x - 4) * k, (y - 14) * k], 3 * k, fill=(214, 160, 50))
                d.rounded_rectangle([(x - 30) * k, (y - 20) * k, (x + 30) * k, (y + 22) * k], 4 * k, fill=(246, 196, 72))
            elif kind == "doc":
                d.polygon([((x - 22) * k, (y - 28) * k), ((x + 10) * k, (y - 28) * k), ((x + 22) * k, (y - 16) * k),
                           ((x + 22) * k, (y + 26) * k), ((x - 22) * k, (y + 26) * k)], fill=(245, 245, 250))
                for j in range(4):
                    d.line([(x - 14) * k, (y - 10 + j * 9) * k, (x + 14) * k, (y - 10 + j * 9) * k],
                           fill=(160, 170, 190), width=2 * k)
            else:
                d.rounded_rectangle([(x - 20) * k, (y - 18) * k, (x + 20) * k, (y + 26) * k], 4 * k, fill=(200, 210, 225))
                d.rectangle([(x - 25) * k, (y - 25) * k, (x + 25) * k, (y - 18) * k], fill=(170, 180, 200))
            tw = d.textlength(label, font=f)
            d.text((x * k - tw / 2 + 1 * k, (y + 34) * k + 1 * k), label, font=f, fill=(0, 0, 0, 140))
            d.text((x * k - tw / 2, (y + 34) * k), label, font=f, fill=(255, 255, 255))

        # taskbar
        ty = self.TASKBAR_Y
        d.rectangle([0, ty * k, W * k, H * k], fill=(18, 20, 28, 235))
        d.line([0, ty * k, W * k, ty * k], fill=(70, 74, 90), width=k)
        cy = (ty + H) / 2
        d.rounded_rectangle([28 * k, (cy - 18) * k, 64 * k, (cy + 18) * k], 8 * k, fill=(60, 120, 230))
        for dx in (-7, 7):
            for dy in (-7, 7):
                d.rounded_rectangle([(46 + dx - 5) * k, (cy + dy - 5) * k, (46 + dx + 5) * k, (cy + dy + 5) * k],
                                    2 * k, fill=(255, 255, 255))
        ax, ay = self.APP_ICON
        self._app_icon(d, ax, ay, 20, k)
        d.rounded_rectangle([(212 - 20) * k, (ay - 16) * k, (212 + 20) * k, (ay + 18) * k], 4 * k, fill=(246, 196, 72))
        d.ellipse([(274 - 18) * k, (ay - 18) * k, (274 + 18) * k, (ay + 18) * k], fill=(70, 140, 220))
        d.arc([(274 - 18) * k, (ay - 8) * k, (274 + 18) * k, (ay + 8) * k], 0, 360, fill=(230, 240, 255), width=2 * k)
        d.line([274 * k, (ay - 18) * k, 274 * k, (ay + 18) * k], fill=(230, 240, 255), width=2 * k)
        fs = font(16 * k)
        for txt, yy_ in (("10:24 AM", cy - 11), ("10/24/2026", cy + 11)):
            tw = d.textlength(txt, font=fs)
            d.text(((W - 70) * k - tw / 2, yy_ * k), txt, font=fs, fill=(235, 238, 245), anchor="lm")
        return img

    def _app_icon(self, d, x, y, r, k):
        d.rounded_rectangle([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], 6 * k, fill=(250, 250, 252))
        pts = [(x + r * 0.55, y - r * 0.55), (x + r * 0.75, y - r * 0.35), (x - r * 0.35, y + r * 0.75),
               (x - r * 0.65, y + r * 0.65), (x - r * 0.55, y + r * 0.35)]
        d.polygon([(px * k, py * k) for px, py in pts], fill=(245, 180, 40), outline=(40, 40, 40))

    def _window_layer(self, ss, hover):
        key = ("layer", ss, hover)
        if key in self._cache:
            return self._cache[key]
        k, pad = ss, 50
        x0, y0, x1, y1 = self.WINDOW
        w, h = (x1 - x0 + 2 * pad) * k, (y1 - y0 + 2 * pad) * k
        L = lambda x: (x - x0 + pad) * k
        T = lambda y: (y - y0 + pad) * k
        shadow = Image.new("L", (w, h), 0)
        ImageDraw.Draw(shadow).rounded_rectangle([L(x0 + 6), T(y0 + 16), L(x1 - 6), T(y1 + 14)], 14 * k, fill=150)
        shadow = shadow.filter(ImageFilter.GaussianBlur(18 * k))
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        layer.putalpha(shadow)
        d = ImageDraw.Draw(layer)
        d.rounded_rectangle([L(x0), T(y0), L(x1), T(y1)], 10 * k, fill=(243, 243, 247), outline=(150, 152, 165), width=k)
        # title bar
        ix, iy = x0 + 26, y0 + self.TITLE_H / 2
        d.rounded_rectangle([L(ix - 11), T(iy - 11), L(ix + 11), T(iy + 11)], 4 * k, fill=(255, 255, 255), outline=(200, 200, 210))
        d.line([L(ix - 6), T(iy + 6), L(ix + 6), T(iy - 6)], fill=(245, 170, 30), width=4 * k)
        d.text((L(x0 + 48), T(iy)), self.title, font=font(16 * k), fill=(40, 42, 52), anchor="lm")
        cx0, cy0, cx1, cy1 = self.CLOSE
        if hover:
            d.rounded_rectangle([L(cx0), T(cy0), L(cx1), T(cy1)], 0, fill=(225, 30, 45))
        xc, yc = (cx0 + cx1) / 2, (cy0 + cy1) / 2
        col = (255, 255, 255) if hover else (50, 52, 62)
        d.line([L(xc - 7), T(yc - 7), L(xc + 7), T(yc + 7)], fill=col, width=2 * k)
        d.line([L(xc - 7), T(yc + 7), L(xc + 7), T(yc - 7)], fill=col, width=2 * k)
        mx = xc - 56
        d.rectangle([L(mx - 7), T(yc - 7), L(mx + 7), T(yc + 7)], outline=(50, 52, 62), width=2 * k)
        nx = xc - 112
        d.line([L(nx - 7), T(yc), L(nx + 7), T(yc)], fill=(50, 52, 62), width=2 * k)
        # toolbar
        tx = self.TOOL_X
        d.rectangle([L(x0 + 1), T(y0 + self.TITLE_H), L(x0 + self.TOOLBAR_W), T(y1 - 1)], fill=(229, 230, 237))
        for tool, ty in self.TOOLS.items():
            self._tool_glyph(d, tool, L(tx), T(ty), k)
        # canvas
        cx0, cy0, cx1, cy1 = self.CANVAS
        d.rectangle([L(cx0), T(cy0), L(cx1), T(cy1)], fill=(255, 255, 255), outline=(205, 207, 215), width=k)
        layer_pos = ((x0 - pad) * k, (y0 - pad) * k)
        self._cache[key] = (layer, layer_pos)
        return self._cache[key]

    def _tool_glyph(self, d, tool, x, y, k):
        ink = (55, 58, 70)
        if tool == "select":
            pts = [(0, 0), (0, 17), (4.2, 13.2), (7.2, 19.8), (9.6, 18.8), (6.6, 12.4), (12, 12.2)]
            d.polygon([(x + (px - 5) * k, y + (py - 10) * k) for px, py in pts], fill=(255, 255, 255), outline=ink)
        else:
            for kind, pts, fill in cursor_shapes(tool if tool in ("pencil", "eraser") else "tool_" + tool):
                d.polygon([(x + (px * 0.9) * k, y + (py * 0.9) * k) for px, py in pts], fill=fill, outline=ink)


def cursor_shapes(icon):
    """List of (kind, polygon points relative to the hotspot, fill colour)."""
    W, K = (255, 255, 255), (20, 20, 24)
    if icon == "arrow":
        return [("poly", [(0, 0), (0, 17), (4.2, 13.2), (7.2, 19.8), (9.6, 18.8), (6.6, 12.4), (12, 12.2)], W)]
    if icon == "open":
        fingers = [rrect(-8, -12, -4, 2, 2), rrect(-4, -15, 0, 2, 2), rrect(0, -14, 4, 2, 2), rrect(4, -11, 8, 2, 2)]
        return [("poly", f, W) for f in fingers] + [
            ("poly", [(-8, 2), (-13, -4), (-15, -1), (-9, 8)], W),
            ("poly", rrect(-9, -2, 9, 12, 4), W)]
    if icon == "grab":
        knuckles = [rrect(-8, -8, -4, 0, 2), rrect(-4, -9, 0, 0, 2), rrect(0, -9, 4, 0, 2), rrect(4, -8, 8, 0, 2)]
        return [("poly", f, W) for f in knuckles] + [
            ("poly", [(-8, 0), (-12, -4), (-13, 1), (-8, 6)], W),
            ("poly", rrect(-9, -3, 9, 10, 4), W)]
    if icon == "pencil":
        d, n, w = (0.643, -0.766), (0.766, 0.643), 3.6
        at = lambda s, o: (d[0] * s + n[0] * o, d[1] * s + n[1] * o)
        return [("poly", [at(8, w), at(26, w), at(26, -w), at(8, -w)], (250, 200, 40)),
                ("poly", [at(26, w), at(29, w), at(29, -w), at(26, -w)], (180, 185, 195)),
                ("poly", [at(29, w), at(33, w), at(33, -w), at(29, -w)], (240, 130, 150)),
                ("poly", [(0, 0), at(8, w), at(8, -w)], (240, 205, 160)),
                ("poly", [(0, 0), at(3, w * 0.38), at(3, -w * 0.38)], (50, 50, 55))]
    if icon == "eraser":
        c, s = math.cos(math.radians(-35)), math.sin(math.radians(-35))
        rot = lambda pts: [(px * c - py * s, px * s + py * c) for px, py in pts]
        return [("poly", rot([(0, -6), (10, -6), (10, 6), (0, 6)]), (240, 130, 150)),
                ("poly", rot([(10, -6), (24, -6), (24, 6), (10, 6)]), (80, 130, 220))]
    if icon == "tool_bucket":
        return [("poly", [(-8, -4), (4, -10), (10, 2), (-2, 8)], (160, 200, 240)),
                ("poly", [(8, 0), (12, 6), (10, 10), (8, 6)], (60, 120, 230))]
    if icon == "tool_line":
        return [("poly", [(-9, 8), (8, -9), (10, -7), (-7, 10)], (55, 58, 70))]
    if icon == "tool_shapes":
        return [("poly", rrect(-11, -3, 3, 11, 1), (255, 255, 255)),
                ("poly", [(4 + 7 * math.cos(a), -4 + 7 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 20)],
                 (255, 255, 255))]
    raise ValueError(icon)


def draw_cursor(d, look, k):
    """Draw a cursor (with a soft drop shadow) at look = {x, y, rot, icon, scale}."""
    c, s = math.cos(math.radians(look["rot"])), math.sin(math.radians(look["rot"]))
    sc = look["scale"]

    def tf(pts, ox=0.0, oy=0.0):
        return [((look["x"] + (px * c - py * s) * sc + ox) * k, (look["y"] + (px * s + py * c) * sc + oy) * k)
                for px, py in pts]

    shapes = cursor_shapes(look["icon"])
    for _, pts, _ in shapes:
        d.polygon(tf(pts, 2, 3), fill=(0, 0, 0, 55))
    for _, pts, fill in shapes:
        d.polygon(tf(pts), fill=fill, outline=(20, 20, 24), width=max(1, round(1.3 * k)))
