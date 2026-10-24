"""Drawings for Prop kinds. World props get (draw, look, ss, ox); HUD props get (draw, look, W, H)."""

import math

from .desktop import font

INK = (24, 22, 28)
MONO = ["/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/System/Library/Fonts/Menlo.ttc", "C:/Windows/Fonts/consolab.ttf"]


def mono(size):
    from PIL import ImageFont
    for p in MONO:
        try:
            return ImageFont.truetype(p, int(size))
        except OSError:
            pass
    return font(size, bold=True)


def _a(col, alpha):
    return tuple(col[:3]) + (int(255 * max(0.0, min(1.0, alpha))),)


def _xf(look, ss, ox):
    """Local (unscaled, unrotated) coords -> supersampled screen coords."""
    c, s = math.cos(math.radians(look["rot"])), math.sin(math.radians(look["rot"]))
    sc, x0, y0 = look["scale"], look["x"] - ox, look["y"]

    def f(px, py):
        return (x0 + (px * c - py * s) * sc) * ss, (y0 + (px * s + py * c) * sc) * ss
    return f


def _ellipse(f, cx, cy, rx, ry, n=36):
    return [f(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _text(d, xy, text, size, fill, ss, anchor="mm", fnt=None, stroke=0, stroke_fill=INK):
    d.text(xy, text, font=fnt or font(size * ss, bold=True), fill=fill, anchor=anchor,
           stroke_width=round(stroke * ss), stroke_fill=stroke_fill)


# ---------------------------------------------------------------------- world props

def coin(d, L, ss, ox):
    """A token: gold disc with its ticker; spin squashes it, `label` floats a market-cap tag above."""
    a, r = L["alpha"], L.get("r", 38)
    f = _xf(L, ss, ox)
    sq = max(0.08, abs(math.cos(math.radians(L.get("spin", 0.0)))))
    gold, rim = L.get("color", (246, 196, 60)), L.get("rim", (190, 130, 20))
    d.polygon(_ellipse(f, 3, 4, r * sq, r), fill=_a((0, 0, 0), 0.25 * a))
    d.polygon(_ellipse(f, 0, 0, r * sq, r), fill=_a(rim, a), outline=_a(INK, a), width=round(2 * ss))
    d.polygon(_ellipse(f, 0, 0, r * 0.8 * sq, r * 0.8), fill=_a(gold, a))
    if L.get("cracked"):
        d.line([f(-r * 0.2 * sq, -r * 0.9), f(r * 0.1 * sq, -r * 0.2), f(-r * 0.15 * sq, r * 0.3),
                f(r * 0.2 * sq, r * 0.9)], fill=_a(INK, a), width=round(3 * ss))
    if sq > 0.55 and L.get("ticker"):
        x, y = f(0, 0)
        size = r * 0.55 * L["scale"]
        fnt = font(size * ss, bold=True)
        fit = 1.35 * r * L["scale"] * sq * ss / max(1, d.textlength(L["ticker"], font=fnt))
        if fit < 1:
            size *= fit
        _text(d, (x, y), L["ticker"], size, _a((120, 70, 0), a), ss)
    if L.get("label"):
        x, y = f(0, -r - 22)
        fnt = mono(15 * ss)
        w = d.textlength(L["label"], font=fnt) / 2 + 8 * ss
        d.rounded_rectangle([x - w, y - 13 * ss, x + w, y + 13 * ss], 5 * ss, fill=_a((18, 18, 24), 0.85 * a))
        d.text((x, y), L["label"], font=fnt, fill=_a(L.get("label_color", (80, 240, 150)), a), anchor="mm")


def rug(d, L, ss, ox):
    """A patterned rug lying on the floor. `wave` ripples it (for the yank), `length` sets size."""
    a, n = L["alpha"], 28
    length, depth = L.get("length", 420), 26
    wave, ph = L.get("wave", 0.0), L.get("phase", 0.0)
    x0, y0 = L["x"] - ox, L["y"]
    top, bot = [], []
    for i in range(n + 1):
        u = i / n
        dy = -wave * math.sin(math.pi * u * 3 + ph) * math.sin(math.pi * u)
        top.append(((x0 + length * u + 18) * ss, (y0 - depth + dy) * ss))
        bot.append(((x0 + length * u) * ss, (y0 + dy) * ss))
    body = L.get("color", (150, 30, 45))
    d.polygon(top + bot[::-1], fill=_a(body, a), outline=_a(INK, a), width=round(2 * ss))
    inner_t = [(x + 8 * ss, y + 6 * ss) for x, y in top[1:-1]]
    inner_b = [(x + 8 * ss, y - 6 * ss) for x, y in bot[1:-1]]
    d.line(inner_t, fill=_a((235, 190, 90), a), width=round(3 * ss))
    d.line(inner_b, fill=_a((235, 190, 90), a), width=round(3 * ss))
    for j in range(1, 6):  # diamond medallions
        i = int(n * j / 6)
        mx, my = (top[i][0] + bot[i][0]) / 2, (top[i][1] + bot[i][1]) / 2
        s = 7 * ss
        d.polygon([(mx, my - s), (mx + s * 1.6, my), (mx, my + s), (mx - s * 1.6, my)], fill=_a((40, 60, 140), a))
    for end in (0, n):
        for k in range(5):
            u = k / 4
            px, py = top[end][0] * (1 - u) + bot[end][0] * u, top[end][1] * (1 - u) + bot[end][1] * u
            dx = (-1 if end == 0 else 1) * 9 * ss
            d.line([px, py, px + dx, py], fill=_a((235, 220, 190), a), width=round(2 * ss))
    if L.get("text"):
        i = n // 2
        mx, my = (top[i][0] + bot[i][0]) / 2, (top[i][1] + bot[i][1]) / 2
        d.text((mx, my), L["text"], font=mono(13 * ss), fill=_a((255, 235, 200), a), anchor="mm")


def bread(d, L, ss, ox):
    """A standing slice of bread (half of a sandwich attack)."""
    a = L["alpha"]
    f = _xf(L, ss, ox)
    w, h = 110, 250
    crust = []
    for i in range(41):
        th = math.pi + math.pi * i / 40
        crust.append((w / 2 * math.cos(th) * 1.08, -h / 2 + 30 + 42 * math.sin(th)))
    shape = crust + [(w / 2, h / 2 - 10), (w / 2 - 10, h / 2), (-w / 2 + 10, h / 2), (-w / 2, h / 2 - 10)]
    d.polygon([f(*p) for p in shape], fill=_a((176, 112, 50), a), outline=_a(INK, a), width=round(3 * ss))
    inner = [(x * 0.82, y * 0.9 + 6) for x, y in shape]
    d.polygon([f(*p) for p in inner], fill=_a((248, 226, 170), a))
    if L.get("text"):
        x, y = f(0, 40)
        size = 17 * L["scale"]
        lines = L["text"].split("\n")
        for i, line in enumerate(lines):
            _text(d, (x, y + (i - (len(lines) - 1) / 2) * size * 1.2 * ss), line, size, _a((120, 60, 20), a), ss)


def candle(d, L, ss, ox):
    """A candlestick: red ones fall like shells, green ones are steps out of the trench."""
    a = L["alpha"]
    f = _xf(L, ss, ox)
    w, h, wick = L.get("w", 46), L.get("h", 160), L.get("wick", 36)
    col = (226, 52, 62) if L.get("color", "red") == "red" else (40, 205, 120)
    d.line([f(0, -h / 2 - wick), f(0, h / 2 + wick)], fill=_a(INK, a), width=round(4 * ss))
    d.polygon([f(-w / 2, -h / 2), f(w / 2, -h / 2), f(w / 2, h / 2), f(-w / 2, h / 2)],
              fill=_a(col, a), outline=_a(INK, a), width=round(3 * ss))
    d.polygon([f(-w / 2 + 6, -h / 2 + 6), f(-w / 2 + 14, -h / 2 + 6), f(-w / 2 + 14, h / 2 - 6),
               f(-w / 2 + 6, h / 2 - 6)], fill=_a((255, 255, 255), 0.25 * a))
    if L.get("text"):
        x, y = f(0, 0)
        _text(d, (x, y), L["text"], 15 * L["scale"], _a((255, 255, 255), a), ss)


def megaphone(d, L, ss, ox):
    """A loudspeaker on a pole (the KOL shill tower)."""
    a = L["alpha"]
    f = _xf(L, ss, ox)
    face = L.get("facing", 1)
    pole = (95, 80, 60)
    d.line([f(0, 0), f(0, -170)], fill=_a(pole, a), width=round(8 * ss))
    d.line([f(-30, -150), f(30, -150)], fill=_a(pole, a), width=round(6 * ss))
    horn = [(0, -185), (0, -205), (face * 70, -232), (face * 70, -158)]
    d.polygon([f(*p) for p in horn], fill=_a((210, 210, 200), a), outline=_a(INK, a), width=round(3 * ss))
    d.polygon(_ellipse(f, face * 70, -195, 9, 37), fill=_a((120, 120, 115), a), outline=_a(INK, a))
    d.rectangle([f(-16, -210)[0], f(-16, -210)[1], f(0, -180)[0], f(0, -180)[1]] if face > 0 else
                [f(0, -210)[0], f(0, -210)[1], f(16, -180)[0], f(16, -180)[1]], fill=_a((70, 70, 70), a))
    if L.get("text"):
        x, y = f(face * 60, -268)
        _text(d, (x, y), L["text"], 15, _a((255, 230, 120), a), ss, stroke=3)


def bubble(d, L, ss, ox):
    """Speech bubble with a tail pointing at (tx, ty)."""
    a, text = L["alpha"], L["text"]
    size = L.get("size", 26) * L["scale"]
    fnt = font(size * ss, bold=True)
    lines = text.split("\n")
    w = max(d.textlength(t, font=fnt) for t in lines) / ss + 36
    h = len(lines) * size * 1.25 + 26
    x, y = L["x"] - ox, L["y"]
    box = [(x - w / 2) * ss, (y - h / 2) * ss, (x + w / 2) * ss, (y + h / 2) * ss]
    tx = L["tx"] - ox if "tx" in L else x + L.get("tail_dx", 0)
    ty = L.get("ty", y + h / 2 + L.get("tail", 34))
    base = min(max(tx, x - w / 2 + 25), x + w / 2 - 25)
    d.polygon([((base - 14) * ss, (y + h / 2 - 4) * ss), ((base + 14) * ss, (y + h / 2 - 4) * ss), (tx * ss, ty * ss)],
              fill=_a((255, 255, 255), a), outline=_a(INK, a), width=round(3 * ss))
    d.rounded_rectangle(box, 14 * ss, fill=_a((255, 255, 255), a), outline=_a(INK, a), width=round(3 * ss))
    d.rectangle([(base - 11) * ss, (y + h / 2 - 7) * ss, (base + 11) * ss, (y + h / 2 + 1) * ss], fill=_a((255, 255, 255), a))
    for i, t in enumerate(lines):
        d.text((x * ss, (y + (i - (len(lines) - 1) / 2) * size * 1.25) * ss), t, font=fnt,
               fill=_a(L.get("color", INK), a), anchor="mm")


def laser(d, L, ss, ox):
    """Sniper laser sight from (x2, y2) to the target (x, y)."""
    a = L["alpha"]
    x, y, sx, sy = L["x"] - ox, L["y"], L["x2"] - ox, L["y2"]
    d.line([sx * ss, sy * ss, x * ss, y * ss], fill=_a((255, 40, 40), 0.55 * a), width=round(2 * ss))
    for r, al in ((9, 0.25), (5, 0.6), (2.5, 1.0)):
        d.ellipse([(x - r) * ss, (y - r) * ss, (x + r) * ss, (y + r) * ss], fill=_a((255, 40, 40), al * a))


def label(d, L, ss, ox):
    """Floating world text, e.g. '-92%' or 'SNIPED'."""
    x, y = L["x"] - ox, L["y"]
    _text(d, (x * ss, y * ss), L["text"], L.get("size", 40) * L["scale"], _a(L.get("color", (255, 255, 255)), L["alpha"]),
          ss, stroke=L.get("stroke", 4))


def sign(d, L, ss, ox):
    """A crooked wooden sign on a post."""
    a = L["alpha"]
    f = _xf(L, ss, ox)
    wood = (120, 85, 50)
    d.line([f(0, 0), f(0, -120)], fill=_a(wood, a), width=round(9 * ss))
    fnt = font(20 * ss * L["scale"], bold=True)
    w = d.textlength(L["text"], font=fnt) / ss / L["scale"] / 2 + 16
    d.polygon([f(-w, -150), f(w, -150), f(w, -112), f(-w, -112)], fill=_a((165, 120, 70), a), outline=_a(INK, a),
              width=round(3 * ss))
    x, y = f(0, -131)
    d.text((x, y), L["text"], font=fnt, fill=_a((40, 25, 10), a), anchor="mm")


WORLD = dict(coin=coin, rug=rug, bread=bread, candle=candle, megaphone=megaphone, bubble=bubble,
             laser=laser, label=label, sign=sign)


# ---------------------------------------------------------------------- HUD (screen space)

def wallet(d, L, W, H):
    a = L["alpha"]
    x, y = L["x"], L["y"]
    v = L.get("value", 0.0)
    d.rounded_rectangle([x, y, x + 300, y + 74], 10, fill=_a((12, 12, 18), 0.78 * a), outline=_a((120, 90, 220), a), width=2)
    d.text((x + 16, y + 20), L.get("title", "WALLET"), font=mono(17), fill=_a((160, 150, 190), a), anchor="lm")
    col = L.get("color", (80, 240, 150))
    d.text((x + 16, y + 50), f"{v:,.2f} SOL", font=mono(30), fill=_a(col, a), anchor="lm")
    if L.get("delta"):
        d.text((x + 284, y + 50), L["delta"], font=mono(20), fill=_a(L.get("delta_color", (255, 80, 90)), a), anchor="rm")


def banner(d, L, W, H):
    """Big slam-in text across the screen ('DEV SOLD', 'RUGGED')."""
    a = L["alpha"]
    size = L.get("size", 150) * L["scale"]
    fnt = font(size, bold=True)
    x, y = L["x"], L["y"]
    if L.get("band", True):
        d.rectangle([0, y - size * 0.62, W, y + size * 0.62], fill=_a((10, 8, 12), 0.6 * a))
    d.text((x, y), L["text"], font=fnt, fill=_a(L.get("color", (240, 40, 50)), a), anchor="mm",
           stroke_width=round(size * 0.05), stroke_fill=_a((0, 0, 0), a))
    if L.get("sub"):
        d.text((x, y + size * 0.72), L["sub"], font=mono(30), fill=_a((235, 235, 240), a), anchor="mm")


def caption(d, L, W, H):
    """Documentary lower-third with a typewriter reveal (reveal: 0..1)."""
    a = L["alpha"]
    text = L["text"]
    shown = text[: int(round(len(text) * min(1.0, L.get("reveal", 1.0))))]
    fnt = mono(L.get("size", 30))
    x, y = L["x"], L["y"]
    w = d.textlength(text, font=fnt)
    d.rectangle([x - 18, y - 30, x + w + 18, y + 30], fill=_a((8, 8, 10), 0.72 * a))
    d.rectangle([x - 18, y - 30, x - 12, y + 30], fill=_a((153, 69, 255), a))
    d.text((x, y), shown, font=fnt, fill=_a((235, 232, 220), a), anchor="lm")
    if L.get("source"):
        d.text((x, y + 46), L["source"], font=mono(16), fill=_a((170, 170, 160), a), anchor="lm")


def bar(d, L, W, H):
    """Bonding-curve progress bar (value 0..1)."""
    a, v = L["alpha"], max(0.0, min(1.0, L.get("value", 0.0)))
    x, y, w = L["x"], L["y"], L.get("w", 420)
    d.text((x, y - 22), L.get("title", "BONDING CURVE"), font=mono(18), fill=_a((200, 200, 210), a), anchor="lm")
    d.text((x + w, y - 22), f"{v * 100:4.0f}%", font=mono(22), fill=_a((80, 240, 150), a), anchor="rm")
    d.rounded_rectangle([x, y, x + w, y + 26], 6, fill=_a((15, 15, 22), 0.85 * a), outline=_a((200, 200, 210), a), width=2)
    if v > 0.01:
        d.rounded_rectangle([x + 4, y + 4, x + 4 + (w - 8) * v, y + 22], 4, fill=_a((60, 220, 140), a))
    if L.get("ticker"):
        d.text((x, y + 48), L["ticker"], font=mono(20), fill=_a((246, 196, 60), a), anchor="lm")


HUD = dict(wallet=wallet, banner=banner, caption=caption, bar=bar)


def draw_world(d, L, ss, ox):
    WORLD[L["kind"]](d, L, ss, ox)


def draw_hud(d, L, W, H):
    HUD[L["kind"]](d, L, W, H)
