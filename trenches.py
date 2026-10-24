"""THE TRENCHES — a memecoin war story.

"The trenches" is Solana slang for trading brand-new memecoins in their first minutes and hours
(mostly on launchpads like pump.fun). This short plays the metaphor straight: a soldier with a
small wallet fights through token launches, sniper bots, a KOL's shill, a sandwich attack, a
rug pull and a red-candle barrage, all for a shot at a coin that "graduates" off its bonding curve.

    python3 trenches.py                  # full render -> the_trenches.mp4
    python3 trenches.py --still 24.5     # one frame -> still.png
    python3 trenches.py --sheet 6,12,20  # contact sheet -> sheet.png
"""

import argparse
import random

from stickanim import Scene
from stickanim import poses as P
from stickanim.battlefield import Battlefield

B = Battlefield(crates=[(1020, "PRIORITY FEES"), (2860, "SLIPPAGE 50%"), (4420, "AMMO"), (5160, "COPE")],
                signs=[(820, "LAUNCHPAD SECTOR"), (3100, "LIQUIDITY ->"), (5580, "BONDING CURVE")])
sc = Scene(duration=60.0, backdrop=B)
FLOOR, TOP = B.FLOOR, B.PARAPET
SIZE = 86
GREEN, DEV, JEET = (40, 205, 110), (78, 46, 100), (150, 150, 158)
RED, GOLD, LIME = (255, 70, 80), (255, 215, 90), (80, 240, 150)

hero = sc.figure(600, FLOOR, size=SIZE, color=GREEN, hat="helmet")
sc.camera.key(0.0, x=760)
wallet = sc.prop("wallet", 30, 30, layer="hud", value=2.0, visible=False)


# ---------------------------------------------------------------- little helpers

def caption(t0, t1, text, source=None):
    """Documentary lower-third, typed out with key clicks."""
    c = sc.prop("caption", 110, 985, layer="hud", text=text, reveal=0.0, source=source, visible=False)
    rate = 0.03
    c.show(t0)
    c.key(t0 + len(text) * rate, ease="linear", reveal=1.0)
    c.key(t1, ease="linear")
    c.key(t1 + 0.35, ease="linear", alpha=0.0)
    c.hide(t1 + 0.36)
    for i in range(0, len(text), 2):
        if text[i] != " ":
            sc.sfx(t0 + i * rate, "type", gain=0.55)


def banner(t, text, color, dur=1.5, sub=None, size=150, y=330):
    b = sc.prop("banner", 960, y, layer="hud", text=text, color=color, sub=sub, size=size,
                visible=False, scale=1.8, alpha=0.0)
    b.show(t)
    b.key(t + 0.14, ease="out", scale=1.0, alpha=1.0)
    b.key(t + dur, ease="linear")
    b.key(t + dur + 0.3, ease="linear", alpha=0.0, scale=1.05)
    b.hide(t + dur + 0.31)


def float_text(t, x, y, text, color, dur=1.1, size=46):
    lab = sc.prop("label", x, y, layer="front", text=text, color=color, size=size, visible=False, scale=0.3)
    lab.show(t)
    lab.move(t + 0.15, x, y - 20, ease="out", scale=1.0, arc=0)
    lab.move(t + dur, x, y - 70, ease="linear", arc=0)
    lab.key(t + dur + 0.25, ease="linear", alpha=0.0)
    lab.hide(t + dur + 0.26)


def pop_coin(t, x, ticker, label, y=730, gain=0.7):
    """A new token launch bursting out of the mud."""
    c = sc.prop("coin", x, FLOOR + 10, layer="front", ticker=ticker, label=label, visible=False,
                scale=0.2, spin=0.0)
    c.show(t)
    c.move(t + 0.4, x, y, ease="back", scale=1.0, spin=360.0, arc=0)
    sc.sfx(t, "pop", x, gain=gain)
    sc.sfx(t + 0.25, "coin", x, gain=0.5 * gain)
    sc.dust(t, x, FLOOR, n=5, power=0.4)
    return c


def bob(c, t0, t1, amp=7):
    x, y = c.pos(t0)
    t, i = t0, 0
    while t + 0.45 < t1:
        t += 0.45
        i += 1
        c.key(t, y=y - (amp if i % 2 else 0))
    c.hold(t1)


def wallet_to(t, value, delta, color=RED):
    wallet.key(t, ease="linear", delta=delta, delta_color=color)
    wallet.key(t + 0.6, ease="out", value=value, color=LIME if value >= 1 else (255, 190, 70))
    wallet.key(t + 2.4, ease="linear", delta=None)


def shell(t_hit, x, power=0.9):
    """A red candle falling like an artillery shell."""
    c = sc.prop("candle", x + 200, -260, layer="front", color="red", visible=False, rot=22, h=170)
    c.show(t_hit - 0.38)
    c.move(t_hit, x, FLOOR - 80, ease="in", arc=0)
    c.hide(t_hit)
    sc.sfx(t_hit - 0.4, "swoosh_down", x, gain=0.6)
    sc.explosion(t_hit, x, FLOOR, power)


def snipe(t, x, y, n=3, gap=0.09):
    for i in range(n):
        sc.tracer(t + i * gap, x + 900 + 60 * i, -160, x + random.uniform(-14, 14), y + random.uniform(-14, 14))


random.seed(4)

# ---------------------------------------------------------------- 0. title
sc.title(0.7, 3.7, "THE TRENCHES", "a memecoin war story", color=(214, 200, 150))
for i in range(12):
    sc.sfx(0.6 + i * 0.28, "snare", power=1.0 if i % 4 == 0 else 0.55, gain=0.7)
sc.sfx(3.95, "boom", None, gain=0.5)
sc.fade_in(4.0, 5.2)
wallet.show(5.0)

# ---------------------------------------------------------------- 1. deployment
caption(5.4, 9.8, "SOLANA, 2026. ~313,000 new tokens launched in a single week.", "source: Crypto Briefing")
hero.key(5.9, pose={**P.STAND, "head": -24})          # looks up at the chart in the sky
hero.key(6.8, pose={**P.STAND, "head": 8})
hero.turn(7.2)
hero.key(7.5, pose={**P.STAND, "head": -4})
hero.turn(8.0)
t = hero.walk(1150, t0=8.2)

# ---------------------------------------------------------------- 2. launches pop up; snipers get there first
tc = t
c1 = pop_coin(tc - 0.7, 1420, "$GRUNT", "MC $3.1K")
c2 = pop_coin(tc - 0.35, 1680, "$BUNKR", "MC $4.8K")
c3 = pop_coin(tc, 1950, "$MORTAR", "MC $2.2K")
caption(tc + 0.2, tc + 4.4, "Fewer than 1 in 100 ever 'graduate' to a real DEX.", "source: Solana Compass (pump.fun launch data)")
hero.key(tc + 0.25, pose=P.STARTLED, lift=12, ease="out")
hero.key(tc + 0.4, pose=P.STARTLED, lift=0, ease="in")
hero.key(tc + 0.75, pose=P.READY)
t_run = hero.walk(1575, t0=tc + 0.85, run=True)
for c in (c1, c2, c3):
    bob(c, c.now, t_run - 0.1)
cx, cy = c2.pos(t_run - 0.1)
lasers = [sc.prop("laser", cx, cy, layer="front", x2=cx + ox_, y2=-200, visible=False) for ox_ in (700, 1100)]
for i, lz in enumerate(lasers):
    lz.show(tc + 1.0 + 0.2 * i)
    lz.key(t_run - 0.15 + 0.01 * i, ease="linear")
    lz.hide(t_run - 0.1 + 0.01 * i)
snipe(t_run - 0.12, cx, cy)
hero.reach(t_run + 0.08, "r", (cx, cy + 10), pose=P.READY)
c2.key(t_run - 0.12, ease="linear", label="MC $4.8K")
c2.move(t_run + 0.45, cx, 160, ease="out", spin=1080.0, arc=0, label="MC $61K")
float_text(t_run + 0.1, cx, 520, "+1170%", LIME)
hero.key(t_run + 0.3, pose={**P.HOLD_UP, "head": -35}, lift=70, ease="out")
hero.key(t_run + 0.55, pose=P.CROUCH, lift=0, ease="in")
sc.sfx(t_run + 0.55, "land", cx)
t_dump = t_run + 0.9
c2.move(t_dump + 0.35, cx + 40, FLOOR - 36, ease="in", spin=1440.0, arc=0)
c2.key(t_dump + 0.36, ease="linear", label="MC $0.3K", label_color=RED, cracked=True)
sc.sfx(t_dump + 0.35, "thud", cx, gain=0.7)
sc.impact(t_dump + 0.35, cx + 40, FLOOR - 30, 0.5)
float_text(t_dump + 0.4, cx + 40, FLOOR - 120, "-94%", RED)
banner(t_dump + 0.45, "SNIPED", GOLD, dur=1.1, size=130, sub="bots bought in the first block")
c2.key(t_dump + 2.0, ease="linear")
c2.key(t_dump + 2.4, ease="linear", alpha=0.0)
c2.hide(t_dump + 2.41)
for c, dt_, txt in ((c1, 0.5, "-100%"), (c3, 0.9, "-100%")):
    x, y = c.pos(t_dump + dt_)
    c.key(t_dump + dt_, ease="linear", label="MC $0", label_color=RED)
    c.move(t_dump + dt_ + 0.5, x, FLOOR + 20, ease="in", scale=0.2, arc=0)
    c.hide(t_dump + dt_ + 0.51)
    float_text(t_dump + dt_, x, y - 60, txt, RED, size=34)
hero.key(t_dump + 0.6, pose={**P.STAND, "head": 30})   # stares at the wreck
t = hero.key(t_dump + 1.6, pose={**P.STAND, "head": 30})

# ---------------------------------------------------------------- 3. a KOL shills; the sandwich bot strikes
kol = sc.prop("megaphone", 2700, TOP, layer="back", facing=-1, text="KOL")
t_kol = t + 0.2
bub = sc.prop("bubble", 2470, 225, layer="front", text="THIS ONE IS DIFFERENT.\n100x. SEND IT!!!", size=30,
              tx=2640, ty=318, visible=False, scale=0.6)
bub.show(t_kol)
bub.key(t_kol + 0.15, ease="out", scale=1.0)
bub.key(t_kol + 2.4, ease="linear")
bub.hide(t_kol + 2.45)
sc.sfx(t_kol, "boop", 2700, gain=0.6)
sc.sfx(t_kol + 0.12, "boop", 2700, gain=0.5)
c_send = pop_coin(t_kol + 0.5, 2640, "$SEND", "MC $7K")
hero.key(t_kol + 0.5, pose={**P.STAND, "head": -15})
t = hero.walk(2530, t0=t_kol + 0.9, run=True)
bob(c_send, c_send.now, t + 0.1)
gx, gy = c_send.pos(t + 0.12)
hero.reach(t + 0.12, "r", (gx - 6, gy), pose=P.READY)
sc.sfx(t + 0.12, "coin", gx, gain=0.6)
t_grab = t + 0.12
hx = hero.last["x"]
t_s = t_grab + 0.32
for side, label in ((-1, "FRONT\nRUN"), (1, "BACK\nRUN")):
    br = sc.prop("bread", hx + side * 900, 775, layer="front", text=label, rot=-side * 6, visible=False)
    br.show(t_s - 0.22)
    br.move(t_s, hx + side * 74, 778, ease="in", arc=0, rot=0.0)
    br.key(t_s + 0.45, ease="linear")
    br.move(t_s + 0.85, hx + side * 1000, 760, ease="in", arc=0, rot=side * 25.0)
    br.hide(t_s + 0.86)
    sc.sfx(t_s - 0.2, "whoosh", hx + side * 300, gain=0.5, dur=0.25)
hero.key(t_s, pose=P.SQUISH, ease="snap")
c_send.attach(t_grab, None, hero, "r_hand", (0.0, -6.0))
sc.hit(t_s, hx, 760, power=0.75, sound="squish")
float_text(t_s + 0.1, hx, 560, "SANDWICHED", GOLD, size=52)
wallet_to(t_s + 0.1, 1.62, "-0.38")
caption(t_s + 0.6, t_s + 5.0, "Sandwich bots: an est. $370M-$500M extracted in 16 months.",
        "source: Solana Accelerate 2025 MEV talk, via Solana Compass")
hero.key(t_s + 0.7, pose=P.SQUISH)
hero.key(t_s + 1.0, pose={**P.STAND, "head": 20}, ease="back")
t = hero.key(t_s + 1.5, pose={**P.HOLD_UP, "r_arm": 120, "head": 0})

# ---------------------------------------------------------------- 4. the rug
RUG_X, RUG_L = 3260, 560
rug = sc.prop("rug", RUG_X, FLOOR + 3, layer="back", length=RUG_L, text="LIQUIDITY", wave=0.0, phase=0.0)
dev = sc.figure(RUG_X + RUG_L + 120, FLOOR, size=SIZE, color=DEV, hat="hood", facing=-1, pose=P.CROSSED)
dev.breathe = True
t = hero.walk(3470, t0=t + 0.1)
c_send.key(t + 0.1, ease="linear", label="MC $88K")
float_text(t + 0.15, 3470, 520, "+1157%", LIME)
sc.sfx(t + 0.15, "coin", 3470, gain=0.6)
hero.key(t + 0.3, pose=P.HOLD_UP, lift=50, ease="out")
hero.key(t + 0.5, pose=P.CROUCH, lift=0, ease="in")
hero.key(t + 0.75, pose=P.HOLD_UP, lift=50, ease="out")
hero.key(t + 0.95, pose=P.CROUCH, lift=0, ease="in")
t = hero.key(t + 1.25, pose=P.HOLD_UP)
dev.hold(t - 0.6)
dev.key(t - 0.2, pose={**P.CROSSED, "head": -10})
t_g = dev.key(t + 0.35, pose=P.GRAB_LOW)
t_y = t_g + 0.35
banner(t_y, "DEV SOLD", RED, dur=1.6)
sc.sfx(t_y, "alarm", None, gain=0.55, dur=1.6)
sc.sfx(t_y, "rip", RUG_X + RUG_L, gain=0.9)
dev.key(t_y + 0.12, pose=P.PULL, x=dev.last["x"] + 60, ease="snap")
rug.move(t_y + 0.28, RUG_X + 700, FLOOR + 3, ease="in", arc=0, wave=30.0, phase=10.0)
hero.hold(t_y + 0.04)
t_end = hero.ragdoll(t_y + 0.06, t_y + 2.3, ground=FLOOR,
                     kicks=[(1500, -300, ["l_foot", "r_foot"]), (900, -500, ["l_knee", "r_knee"]),
                            (250, -900, ["hip"]), (-300, -600, ["neck", "head"])])
c_send.detach(t_y + 0.1)
px, py = c_send.pos(t_y + 0.1)
c_send.move(t_y + 0.6, px - 220, 380, ease="out", spin=720.0, arc=0)
c_send.move(t_y + 1.05, px - 300, FLOOR - 36, ease="in", spin=1080.0, arc=0)
c_send.key(t_y + 1.06, ease="linear", label="MC $0.9K", label_color=RED, cracked=True)
sc.sfx(t_y + 1.05, "thud", px - 300, gain=0.6)
float_text(t_y + 1.1, px - 300, FLOOR - 130, "-99%", RED)
c_send.key(t_y + 3.0, ease="linear")
c_send.key(t_y + 3.4, ease="linear", alpha=0.0)
c_send.hide(t_y + 3.41)
wallet_to(t_y + 0.4, 0.30, "-1.32")
shell(t_y + 1.25, px + 420, 0.85)
caption(t_y + 1.6, t_y + 6.0, "Most new memecoins show rug-pull behavior within an hour of launch.",
        "source: 'Catching the Rug', arXiv 2608.20271 (2026 preprint)")
# the dev turns and runs off with the rug
dev.key(t_y + 0.55, pose=P.PULL)
dev.turn(t_y + 0.6)
t_gone = dev.walk(dev.last["x"] + 1700, run=True, t0=t_y + 0.7)
dev.visible_until = t_gone
for k in range(round((t_y + 0.7) * sc.fps), round(t_gone * sc.fps) + 1):
    tt = k / sc.fps
    rug.key(tt, ease="linear", x=dev.point(tt, "hip")[0] - 60 - RUG_L, wave=18.0, phase=tt * 25)
rug.hide(t_gone)
# hero gets up, dazed
xg = hero.last["x"]
hero.key(t_end + 0.5, pose=P.HANDS_KNEES, x=xg, ground=FLOOR)
hero.key(t_end + 0.95, pose=P.CROUCH, x=xg + 10)
hero.key(t_end + 1.3, pose=P.STAND)
if hero.last["facing"] < 0:
    hero.turn(t_end + 1.35)
hero.key(t_end + 1.5, pose={**P.STAND, "head": 16, "lean": 6})
hero.key(t_end + 1.62, pose={**P.STAND, "head": -10})
t = hero.key(t_end + 1.8, pose=P.READY)

# ---------------------------------------------------------------- 5. barrage of red candles, jeets fleeing
jeets = []
for i, (x0, msg) in enumerate(((5600, "SELL!! SELL!!"), (5850, "IT'S OVER"))):
    j = sc.figure(x0, FLOOR, size=SIZE * 0.95, color=JEET, hat="helmet", facing=-1, visible_from=t)
    j.hold(t + 0.2 * i)
    tj = j.walk(1800, run=True, speed=1.1)
    j.visible_until = tj
    b = sc.prop("bubble", x0, 560, layer="front", text=msg, size=24, visible=False)
    b.show(t + 0.2 * i)
    b.attach(t + 0.2 * i, tj, j, "head", (10.0, -105.0))
    b.hide(t + 0.2 * i + 2.6)
    jeets.append(j)
t_b = hero.walk(4350, t0=t + 0.2, run=True)
for dt_, dx in ((0.35, -260), (0.9, 380), (1.4, -220)):
    shell(t + 0.2 + dt_, hero.point(t + 0.2 + dt_, "hip")[0] + dx, 0.8)
shell(t_b + 0.05, 4560, 1.0)
t = hero.leap(0.7, 4860, FLOOR, 170, t0=t_b + 0.02, spin=360, poses_=[(0.25, P.TUCK), (0.75, P.TUCK)],
              land=P.HERO_LAND)
sc.sfx(t_b + 0.05, "whoosh", 4560, dur=0.4)
hero.key(t + 0.35, pose=P.HERO_LAND)
t = hero.walk(5480, t0=t + 0.55, run=True)
shell(t - 0.5, 4900, 0.7)
hero.key(t + 0.25, pose=P.READY)

# ---------------------------------------------------------------- 6. one last shot: the bonding curve
t_f = t + 0.4
c_tr = pop_coin(t_f, 5680, "$TRENCH", "MC $5K")
bar = sc.prop("bar", 1450, 70, layer="hud", value=0.08, ticker="$TRENCH", visible=False)
bar.show(t_f + 0.2)
hero.key(t_f + 0.5, pose={**P.LOOK_HANDS, "head": 45})       # looks at what's left in his hand
hero.key(t_f + 1.4, pose={**P.LOOK_HANDS, "head": 45})
hero.key(t_f + 1.7, pose=P.READY)
bob(c_tr, c_tr.now, t_f + 1.95)
gx, gy = c_tr.pos(t_f + 2.0)
hero.reach(t_f + 2.0, "r", (gx - 6, gy), pose=P.READY)
sc.sfx(t_f + 2.0, "coin", gx, gain=0.7)
c_tr.attach(t_f + 2.0, None, hero, "r_hand", (0.0, -6.0))
wallet_to(t_f + 2.1, 0.0, "-0.30", (255, 190, 70))
t_hold = hero.key(t_f + 2.4, pose=P.HOLD_UP, ease="back")
caption(t_f + 2.4, t_f + 6.6, "Bonding curve fills -> the token graduates to a real DEX pool.",
        "how pump.fun launches work (The Block, Bitquery docs)")
steps = [(5810, 110), (5930, 210), (6050, 310), (6170, 400)]
for i, (frac, mc) in enumerate(((0.33, "MC $11K"), (0.58, "MC $23K"), (0.84, "MC $41K"), (1.0, "MC $69K"))):
    tt = t_hold + 0.8 + i * 0.9
    bar.key(tt, ease="out", value=frac)
    c_tr.key(tt, ease="linear", label=mc)
    sc.sfx(tt, "coin", 5700, gain=0.5)
    sx, h = steps[i]
    st = sc.prop("candle", sx, FLOOR, layer="back", color="green", h=1.0, wick=10, visible=False)
    st.show(tt - 0.3)
    st.move(tt, sx, FLOOR - h / 2, ease="back", arc=0, h=float(h))
    sc.sfx(tt - 0.3, "whoosh", sx, gain=0.4, dur=0.3)
    steps[i] = (sx, h, st)
    if i < 3:
        snipe(tt + 0.35, hero.last["x"] + 40, 600, n=2)
        hero.key(tt + 0.42, pose={**P.HOLD_UP, "lean": -14, "head": -10}, ease="snap")
        hero.key(tt + 0.75, pose=P.HOLD_UP)
t_grad = t_hold + 0.8 + 3 * 0.9
banner(t_grad + 0.1, "GRADUATED", LIME, dur=1.8, sub="bonding curve complete -> DEX")
sc.sfx(t_grad + 0.1, "fanfare", None, gain=0.8)
wallet_to(t_grad + 0.4, 2.85, "+2.85", LIME)
float_text(t_grad + 0.2, 5700, 640, "+850%", LIME, size=56)
bar.key(t_grad + 2.6, ease="linear")
bar.key(t_grad + 3.0, ease="linear", alpha=0.0)
bar.hide(t_grad + 3.01)
# climb the green candles out of the trench
t = t_grad + 1.0
for sx, h, st in steps:
    t = hero.leap(0.42, sx, FLOOR - h, 60, t0=t, poses_=[(0.5, P.TUCK)], land=P.CROUCH, land_fx=False)
    sc.sfx(t, "step", sx, gain=0.6)
    t += 0.08
t = hero.leap(0.55, 6380, TOP - 16, 90, t0=t, poses_=[(0.5, P.TUCK)], land=P.CROUCH)
t = hero.key(t + 0.3, pose=P.HOLD_UP)
caption(t, t + 3.0, "Over the top. You made it out of the trenches.")

# ---------------------------------------------------------------- 7. ...or did you
t_new = t + 1.6
c_new = pop_coin(t_new, 6050, "$TRENCH2", "MC $1K", y=760)
nb = sc.prop("bubble", 6050, 600, layer="front", text="NEW LAUNCH JUST DROPPED!!", size=26, visible=False, scale=0.6)
nb.show(t_new + 0.3)
nb.key(t_new + 0.45, ease="out", scale=1.0)
nb.hide(t_new + 2.6)
bob(c_new, c_new.now, t_new + 3.5)
hero.key(t_new + 0.3, pose={**P.HOLD_UP, "head": 15})
t = hero.turn(t_new + 0.6)
hero.key(t + 0.25, pose={**P.HOLD_UP, "head": 40})
hero.key(t + 1.2, pose={**P.HOLD_UP, "head": 40})
for sx, h, st in steps:
    st.move(t + 1.4, sx, FLOOR, ease="in", arc=0, h=1.0)
    st.hide(t + 1.41)
t = hero.leap(0.75, 6120, FLOOR, 120, t0=t + 1.3, poses_=[(0.5, P.TUCK)], land=P.CROUCH)
caption(t - 0.5, t + 2.6, "Back to the trenches.")
t = hero.key(t + 0.4, pose=P.READY)
nx, ny = c_new.pos(t + 0.3)
hero.reach(t + 0.3, "l", (nx + 6, ny), pose=P.READY)       # a bag in each hand
c_new.attach(t + 0.3, None, hero, "l_hand", (0.0, -6.0))
sc.sfx(t + 0.3, "coin", nx, gain=0.7)
t = hero.key(t + 0.8, pose={**P.CHEER, "l_arm": 128, "l_elbow": 12, "r_arm": -138, "r_elbow": -12, "head": -18}, ease="back")
hero.hold(t + 1.8)
sc.fade_out(t + 1.4, t + 2.4)
sc.title(t + 2.6, t + 6.6, "THE TRENCHES", "~99% of new tokens never graduate. Not financial advice.",
         color=(214, 200, 150))
sc.sfx(t + 2.6, "boom", None, gain=0.5)
END = t + 7.0
sc.duration = END

# ---------------------------------------------------------------- camera, ambience
sc.follow(hero, 5.0, END, lead=170)
sc.sfx(0.0, "drone", None, gain=0.55, dur=END + 1)
rng = random.Random(9)
tt = 4.5
while tt < END - 6:
    x = sc.camera.pos(tt)[0] + rng.uniform(-1500, 1500)
    B.flash(tt, x, rng.uniform(0.6, 1.2))
    sc.sfx(tt + rng.uniform(0.2, 0.5), "distant_boom", None, gain=0.3)
    tt += rng.uniform(1.8, 3.4)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="the_trenches.mp4")
    ap.add_argument("--still", type=float)
    ap.add_argument("--sheet")
    args = ap.parse_args()
    if args.still is not None:
        print(sc.still(args.still, "still.png"))
    elif args.sheet:
        import os
        import tempfile
        from PIL import Image
        tmp = tempfile.mkdtemp()
        times = [float(s) for s in args.sheet.split(",")]
        data = sc.bake()
        tiles = [Image.open(sc.still(tt, os.path.join(tmp, f"{i}.png"), data)).resize((640, 360))
                 for i, tt in enumerate(times)]
        cols = 3
        sheet = Image.new("RGB", (640 * cols, 360 * ((len(tiles) + cols - 1) // cols)))
        for i, tile in enumerate(tiles):
            sheet.paste(tile, ((i % cols) * 640, (i // cols) * 360))
        sheet.save("sheet.png")
        print("sheet.png")
    else:
        print(f"duration {sc.duration:.1f}s")
        sc.render(args.out)
