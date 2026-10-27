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


def _usd(v):
    v = float(v)
    if v >= 1e6:
        return f"${v / 1e6:.1f}M"
    if v >= 1e3:
        return f"${v / 1e3:.0f}K"
    return f"${v:.0f}"


def _qr(d, x0, y0, size, seed, col):
    """A QR-looking block (random modules plus the three finder squares)."""
    import random as _r
    rng = _r.Random(seed)
    n = 21
    m = size / n
    for i in range(n):
        for j in range(n):
            finder = any(fi <= i < fi + 7 and fj <= j < fj + 7 for fi, fj in ((0, 0), (0, 14), (14, 0)))
            if finder:
                fi, fj = (0 if i < 7 else 14), (0 if j < 7 else 14)
                ii, jj = i - fi, j - fj
                on = ii in (0, 6) or jj in (0, 6) or (2 <= ii <= 4 and 2 <= jj <= 4)
            else:
                on = rng.random() < 0.5
            if on:
                d.rectangle([x0 + j * m, y0 + i * m, x0 + (j + 1) * m, y0 + (i + 1) * m], fill=col)


def window(d, L, ss, ox):
    """An app window (centre x, y). content: chart | post | profile | blank."""
    a, s = L["alpha"], L["scale"]
    if a <= 0.01 or s <= 0.02:
        return
    w, h = L.get("w", 640), L.get("h", 420)
    k = ss * s
    cx, cy = (L["x"] - ox) * ss, L["y"] * ss
    X = lambda u: cx + u * k
    Y = lambda v: cy + v * k
    x0, y0, x1, y1 = -w / 2, -h / 2, w / 2, h / 2
    d.rounded_rectangle([X(x0 + 8), Y(y0 + 14), X(x1 + 8), Y(y1 + 16)], 12 * k, fill=_a((0, 0, 0), 0.28 * a))
    d.rounded_rectangle([X(x0), Y(y0), X(x1), Y(y1)], 10 * k, fill=_a((243, 243, 247), a),
                        outline=_a((140, 142, 156), a), width=max(1, round(k)))
    d.text((X(x0 + 18), Y(y0 + 20)), L.get("title", ""), font=font(16 * k), fill=_a((40, 42, 52), a), anchor="lm")
    bx = x1 - 28
    if L.get("x_hover"):
        d.rectangle([X(x1 - 52), Y(y0 + 1), X(x1 - 1), Y(y0 + 39)], fill=_a((225, 30, 45), a))
    xc = (255, 255, 255) if L.get("x_hover") else (60, 62, 72)
    d.line([X(bx - 6), Y(y0 + 14), X(bx + 6), Y(y0 + 26)], fill=_a(xc, a), width=max(1, round(2 * k)))
    d.line([X(bx - 6), Y(y0 + 26), X(bx + 6), Y(y0 + 14)], fill=_a(xc, a), width=max(1, round(2 * k)))
    c0, c1, c2, c3 = x0 + 10, y0 + 40, x1 - 10, y1 - 10
    content = L.get("content", "blank")
    if content == "chart":
        d.rectangle([X(c0), Y(c1), X(c2), Y(c3)], fill=_a((16, 18, 26), a))
        for gy in range(1, 5):
            yy = c1 + (c3 - c1) * gy / 5
            d.line([X(c0), Y(yy), X(c2), Y(yy)], fill=_a((40, 44, 58), a), width=max(1, round(k)))
        series = L.get("series", [])
        prog = L.get("progress", len(series))
        n = max(1, len(series))
        cw = (c2 - c0 - 20) / n
        val = lambda v: c3 - 14 - v * (c3 - c1 - 90)
        for i, (o, c) in enumerate(series):
            if i >= prog:
                break
            if i + 1 > prog:
                c = o + (c - o) * (prog - i)
            col = (60, 220, 140) if c >= o else (240, 70, 80)
            xm = c0 + 10 + cw * (i + 0.5)
            hi, lo = max(o, c), min(o, c)
            d.line([X(xm), Y(val(hi) - 8), X(xm), Y(val(lo) + 8)], fill=_a(col, a), width=max(1, round(2 * k)))
            d.rectangle([X(xm - cw * 0.32), Y(val(hi)), X(xm + cw * 0.32), Y(max(val(lo), val(hi) + 2))],
                        fill=_a(col, a))
        d.text((X(c0 + 16), Y(c1 + 26)), L.get("ticker", ""), font=mono(20 * k), fill=_a((246, 196, 60), a), anchor="lm")
        if "mc" in L:
            d.text((X(c0 + 16), Y(c1 + 62)), "MC " + _usd(L["mc"]), font=mono(34 * k),
                   fill=_a(L.get("mc_color", (80, 240, 150)), a), anchor="lm")
    elif content in ("post", "profile"):
        d.rectangle([X(c0), Y(c1), X(c2), Y(c3)], fill=_a((255, 255, 255), a))
        top = c1 + 12
        if content == "post" and L.get("reposted_by"):
            d.text((X(c0 + 70), Y(top + 8)), "\u21bb " + L["reposted_by"] + " reposted", font=font(15 * k, bold=True),
                   fill=_a((40, 160, 90), a), anchor="lm")
            top += 26
        av = L.get("avatar", (230, 70, 50))
        d.ellipse([X(c0 + 16), Y(top), X(c0 + 64), Y(top + 48)], fill=_a(av, a))
        d.text((X(c0 + 76), Y(top + 14)), L.get("name", "Kimchi"), font=font(20 * k, bold=True),
               fill=_a((20, 20, 26), a), anchor="lm")
        d.text((X(c0 + 76), Y(top + 36)), L.get("handle", "@kimchi1x"), font=font(15 * k),
               fill=_a((110, 112, 125), a), anchor="lm")
        ty = top + 70
        for line in L.get("text", "").split("\n"):
            d.text((X(c0 + 20), Y(ty)), line, font=font(19 * k), fill=_a((25, 25, 30), a), anchor="lm")
            ty += 27
        if content == "profile":
            d.text((X(c0 + 20), Y(ty + 6)), L.get("bio", ""), font=mono(19 * k), fill=_a((40, 40, 50), a), anchor="lm")
            if "followers" in L:
                d.text((X(c0 + 20), Y(ty + 40)), f"{L['followers'] / 1000:.0f}K followers", font=font(16 * k, bold=True),
                       fill=_a((90, 92, 105), a), anchor="lm")
        if L.get("qr"):
            iy0, iy1 = ty + 6, c3 - 46
            d.rounded_rectangle([X(c0 + 20), Y(iy0), X(c2 - 20), Y(iy1)], 10 * k, fill=_a((40, 22, 56), a))
            q = min(iy1 - iy0 - 30, 170)
            _qr(d, X(c0 + 40), Y(iy0 + 15), q * k, 7, _a((255, 255, 255), a))
            d.text((X((c0 + 60 + q + c2) / 2), Y((iy0 + iy1) / 2 - 14)), "PROJECT", font=font(30 * k, bold=True),
                   fill=_a((255, 90, 70), a), anchor="mm")
            d.text((X((c0 + 60 + q + c2) / 2), Y((iy0 + iy1) / 2 + 22)), "KIMCHI", font=font(30 * k, bold=True),
                   fill=_a((255, 90, 70), a), anchor="mm")
        if content == "post":
            col = (40, 170, 90) if L.get("reposted_by") else (110, 112, 125)
            d.text((X(c0 + 20), Y(c3 - 22)), f"\u21bb {L.get('reposts', 0):.0f}", font=font(17 * k, bold=True),
                   fill=_a(col, a), anchor="lm")
            d.text((X(c0 + 130), Y(c3 - 22)), f"\u2665 {L.get('likes', 0):.0f}", font=font(17 * k, bold=True),
                   fill=_a((110, 112, 125), a), anchor="lm")
        if L.get("deleted"):
            d.rectangle([X(c0), Y(c1), X(c2), Y(c3)], fill=_a((236, 236, 240), a))
            d.text((X((c0 + c2) / 2), Y((c1 + c3) / 2)), "This post has been deleted.", font=font(22 * k, bold=True),
                   fill=_a((120, 122, 135), a), anchor="mm")
    else:
        d.rectangle([X(c0), Y(c1), X(c2), Y(c3)], fill=_a((255, 255, 255), a))
        lines = L.get("text", "").split("\n")
        for i, line in enumerate(lines):
            d.text((X((c0 + c2) / 2), Y((c1 + c3) / 2 + (i - (len(lines) - 1) / 2) * 40 * 1.0)), line,
                   font=font(L.get("size", 30) * k, bold=True), fill=_a(L.get("color", (25, 25, 30)), a), anchor="mm")


def car(d, L, ss, ox):
    """A low red supercar, side view (x, y = middle of the ground line)."""
    a = L["alpha"]
    f = _xf(L, ss, ox)
    face = L.get("facing", 1)
    q = lambda pts: [f(px * face, py) for px, py in pts]
    body = [(-190, -20), (-185, -55), (-120, -70), (-60, -112), (50, -114), (120, -78), (185, -66), (195, -30), (190, -20)]
    d.polygon(q(body), fill=_a(L.get("color", (220, 30, 40)), a), outline=_a(INK, a), width=round(3 * ss))
    d.polygon(q([(-50, -102), (40, -104), (95, -76), (-95, -74)]), fill=_a((150, 200, 230), a), outline=_a(INK, a),
              width=round(2 * ss))
    d.line(q([(-10, -104), (-14, -74)]), fill=_a(INK, a), width=round(3 * ss))
    for wx in (-115, 120):
        d.polygon(_ellipse(lambda u, v: f(u * face, v), wx, -20, 34, 34), fill=_a((22, 22, 26), a))
        d.polygon(_ellipse(lambda u, v: f(u * face, v), wx, -20, 16, 16), fill=_a((190, 190, 200), a))
    d.line(q([(150, -60), (185, -58)]), fill=_a((255, 240, 160), a), width=round(5 * ss))


def magnifier(d, L, ss, ox):
    """An on-chain sleuth's magnifying glass."""
    a = L["alpha"]
    f = _xf(L, ss, ox)
    d.line([f(42, 42), f(105, 105)], fill=_a((80, 50, 30), a), width=round(14 * ss * L["scale"]))
    d.polygon(_ellipse(f, 0, 0, 60, 60), fill=_a((190, 230, 255), 0.35 * a), outline=_a(INK, a), width=round(6 * ss))
    d.arc([*f(-40, -40), *f(40, 40)], 200, 250, fill=_a((255, 255, 255), 0.8 * a), width=round(5 * ss))
    if L.get("text"):
        x, y = f(0, 0)
        _text(d, (x, y), L["text"], 20 * L["scale"], _a(L.get("color", INK), a), ss)


def stamp(d, L, ss, ox):
    """A rubber stamp, e.g. UNVERIFIED."""
    a = L["alpha"]
    f = _xf(L, ss, ox)
    col = L.get("color", (220, 40, 50))
    size = L.get("size", 44)
    fnt = font(size * ss * L["scale"], bold=True)
    w = d.textlength(L["text"], font=fnt) / (ss * L["scale"]) / 2 + 22
    hgt = size * 0.75
    d.polygon([f(-w, -hgt), f(w, -hgt), f(w, hgt), f(-w, hgt)], outline=_a(col, a), width=round(6 * ss * L["scale"]))
    x, y = f(0, 0)
    c, s_ = math.cos(math.radians(L["rot"])), math.sin(math.radians(L["rot"]))
    from PIL import Image as _I, ImageDraw as _D
    tw, th = int(2 * w * ss * L["scale"]), int(2 * hgt * ss * L["scale"])
    im = _I.new("L", (tw, th), 0)
    _D.Draw(im).text((tw / 2, th / 2), L["text"], font=fnt, fill=int(255 * a), anchor="mm")
    im = im.rotate(-L["rot"], expand=True, resample=_I.BICUBIC)
    d._image.paste(_I.new("RGB", im.size, col), (int(x - im.width / 2), int(y - im.height / 2)), im)


WORLD.update(window=window, car=car, magnifier=magnifier, stamp=stamp)


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
