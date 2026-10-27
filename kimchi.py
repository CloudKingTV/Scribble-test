"""THE KIMCHI STORY — a memecoin saga, told on a desktop in stick figures.

Based on public reporting as of late October 2026. Claims and allegations are shown as
unverified/unconfirmed, the way the sources report them; nobody is depicted doing anything
the reporting doesn't establish.

    python3 kimchi.py                  # full render -> the_kimchi_story.mp4
    python3 kimchi.py --still 30       # one frame -> still.png
    python3 kimchi.py --sheet 8,20,35  # contact sheet -> sheet.png
"""

import argparse
import random

from stickanim import Desktop, Scene
from stickanim import poses as P
from stickanim.rig import HEAD_R

D = Desktop()
sc = Scene(duration=80.0, backdrop=D)
CANVAS_FLOOR, TASK = D.CANVAS[3], D.TASKBAR_Y
DESK = (-400, -3000, 2320, TASK)          # ragdoll bounds once we're out on the desktop
SIZE = 86
KIMCHI, ALON, CROWD = (228, 64, 48), (40, 170, 205), (150, 150, 162)
RED, GOLD, LIME = (255, 70, 80), (255, 210, 80), (80, 240, 150)
SHRUG = P.P(lean=0, head=14, l_arm=40, l_elbow=-80, r_arm=-30, r_elbow=-70,
            l_leg=10, l_knee=-4, r_leg=-9, r_knee=-2)

cur = sc.cursor(1480, 760)
kim = sc.figure(760, CANVAS_FLOOR, size=SIZE, color=KIMCHI, hat="cap", visible_from=1e9)


# ---------------------------------------------------------------- helpers

CAPTIONS = []


def caption(t0, t1, text, source=None):
    """Queue a typed-out caption; make_captions() trims overlaps so only one shows at a time."""
    CAPTIONS.append((t0, t1, text, source))


def make_captions():
    CAPTIONS.sort()
    for i, (t0, t1, text, source) in enumerate(CAPTIONS):
        if i + 1 < len(CAPTIONS):
            t1 = min(t1, CAPTIONS[i + 1][0] - 0.35)
        c = sc.prop("caption", 170, 52, layer="hud", text=text, reveal=0.0, source=source, visible=False, size=27)
        rate = 0.026
        c.show(t0)
        c.key(min(t1, t0 + len(text) * rate), ease="linear", reveal=1.0)
        c.key(t1, ease="linear")
        c.key(t1 + 0.3, ease="linear", alpha=0.0)
        c.hide(t1 + 0.31)
        for j in range(0, len(text), 2):
            if text[j] != " " and t0 + j * rate < t1:
                sc.sfx(t0 + j * rate, "type", gain=0.45)


def banner(t, text, color, dur=1.4, sub=None, size=140, y=520):
    b = sc.prop("banner", 960, y, layer="hud", text=text, color=color, sub=sub, size=size,
                visible=False, scale=1.8, alpha=0.0)
    b.show(t)
    b.key(t + 0.14, ease="out", scale=1.0, alpha=1.0)
    b.key(t + dur, ease="linear")
    b.key(t + dur + 0.3, ease="linear", alpha=0.0, scale=1.05)
    b.hide(t + dur + 0.31)


def float_text(t, x, y, text, color, dur=1.2, size=46):
    lab = sc.prop("label", x, y, layer="front", text=text, color=color, size=size, visible=False, scale=0.3)
    lab.show(t)
    lab.move(t + 0.15, x, y - 20, ease="out", scale=1.0, arc=0)
    lab.move(t + dur, x, y - 60, ease="linear", arc=0)
    lab.key(t + dur + 0.25, ease="linear", alpha=0.0)
    lab.hide(t + dur + 0.26)
    return lab


def open_win(t, x, y, **params):
    w = sc.prop("window", x, y, layer="back", visible=False, scale=0.82, alpha=0.0, **params)
    w.show(t)
    w.key(t + 0.3, ease="back", scale=1.0, alpha=1.0)
    sc.sfx(t, "pop", x, gain=0.5)
    return w


def close_win(w, t):
    w.key(t, ease="linear")
    w.key(t + 0.25, ease="in", scale=0.88, alpha=0.0)
    w.hide(t + 0.26)
    sc.sfx(t, "swish", w.pos(t)[0], gain=0.35)


def slam_stamp(t, x, y, text, color=(220, 40, 50), rot=-12, size=44, until=None):
    s = sc.prop("stamp", x, y, layer="front", text=text, color=color, rot=rot, size=size, visible=False,
                scale=2.2, alpha=0.0)
    s.show(t)
    s.key(t + 0.12, ease="in", scale=1.0, alpha=1.0)
    sc.sfx(t + 0.12, "thud", x, gain=0.6)
    sc.shake(t + 0.12, 6, 0.2)
    if until:
        s.key(until, ease="linear")
        s.key(until + 0.3, ease="linear", alpha=0.0)
        s.hide(until + 0.31)
    return s


def flashes(t0, t1, x0, x1, y0, y1, n):
    rng = random.Random(int(t0 * 100))
    for i in range(n):
        tt = t0 + (t1 - t0) * i / n + rng.uniform(0, 0.08)
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        sc.impact(tt, x, y, 0.15)
        sc.sfx(tt, "click", x, gain=0.8)
    sc.flash(t0, 0.25)


random.seed(5)

# ---------------------------------------------------------------- 0. title
sc.title(0.6, 3.6, "THE KIMCHI STORY", "a memecoin saga in stick figures", color=(255, 120, 90))
sc.title(0.6, 3.6, "", "based on public reporting, October 2026", y=700, size=1)
sc.sfx(0.6, "big_hit", None, gain=0.5)
sc.fade_in(3.7, 4.6)

# ---------------------------------------------------------------- 1. the animator draws Kimchi
cur.move(5.2, *D.APP_ICON, t0=4.6)
cur.click(5.25)
D.open_window(5.3)
sc.sfx(5.3, "pop", 960)
cur.move(5.9, *D.tool_pos("pencil"), t0=5.5)
cur.click(5.95)
D.select_tool(5.95, "pencil")
cur.key(6.0, icon="pencil", ease="linear")
hx, hy = kim.point(6.0, "head")
cur.move(6.4, hx, hy - HEAD_R * SIZE, t0=6.05)
caption(6.4, 10.4, "Meet Kimchi: a pseudonymous Solana memecoin trader.")
t = kim.draw_on(6.4, 8.4, cur)
cur.key(8.45, icon="arrow", ease="linear")
cur.move(8.9, 1350, 300)
kim.key(8.7, pose={**P.STAND, "head": 10, "l_arm": 20}, ease="snap")
kim.key(8.9, pose=P.STAND)
t = kim.key(9.4, pose=P.CROSSED)

# ---------------------------------------------------------------- 2. the TRUMP trade claim
c_tr = sc.prop("coin", 1060, CANVAS_FLOOR + 10, layer="front", ticker="$TRUMP", label="Jan 2025", visible=False,
               scale=0.2, spin=0.0)
t_coin = 9.8
c_tr.show(t_coin)
c_tr.move(t_coin + 0.4, 1060, 740, ease="back", scale=1.0, spin=360.0, arc=0)
sc.sfx(t_coin, "pop", 1060)
sc.sfx(t_coin + 0.2, "coin", 1060, gain=0.5)
caption(10.6, 14.6, "January 2025: the official TRUMP memecoin launches.", "Kimchi says he traded it early.")
kim.key(10.2, pose={**P.STAND, "head": -10})
t = kim.walk(960, t0=10.6)
cx, cy = c_tr.pos(t + 0.1)
kim.reach(t + 0.1, "r", (cx - 6, cy), pose=P.READY)
c_tr.attach(t + 0.1, None, kim, "r_hand", (0.0, -34.0))
sc.sfx(t + 0.1, "coin", cx, gain=0.7)
t = kim.key(t + 0.4, pose=P.HOLD_UP)
# a giant green candle carries him up
t_up = t + 0.2
kx = kim.last["x"]
cand = sc.prop("candle", kx, CANVAS_FLOOR, layer="back", color="green", w=110, h=1.0, wick=14, visible=False)
cand.show(t_up)
cand.move(t_up + 1.0, kx, CANVAS_FLOOR - 220, ease="out", arc=0, h=440.0)
sc.sfx(t_up, "whoosh", kx, dur=0.6)
for k in range(round(t_up * sc.fps) + 1, round((t_up + 1.0) * sc.fps) + 1):
    tt = k / sc.fps
    kim.key(tt, ease="linear", ground=CANVAS_FLOOR - cand.look(tt)["h"], pose=P.HOLD_UP)
t = t_up + 1.0
big = float_text(t, kx, 300, "$40,000,000", GOLD, dur=2.8, size=74)
sc.sfx(t, "coin", kx, gain=0.8)
caption(t + 0.2, t + 4.0, "He says one TRUMP run made him ~$40 million.")
kim.key(t + 0.3, pose={**P.CHEER, "r_arm": 165}, ground=CANVAS_FLOOR - 440, ease="back")
# the sleuths
mag = sc.prop("magnifier", 1700, 420, layer="front", visible=False, rot=-20)
mag.show(t + 1.2)
mag.move(t + 1.9, kx + 30, 240, ease="smooth", rot=0.0)
mag.move(t + 2.5, kx - 40, 250, ease="smooth")
mag.move(t + 3.0, kx + 20, 240, ease="smooth")
slam_stamp(t + 3.15, kx, 250, "UNVERIFIED", until=t + 6.0, size=52)
caption(t + 4.3, t + 8.4, "No full wallet trail was ever shown. Analysts reportedly traced ~$6M.",
        "sources: KuCoin News, Crypto Times")
float_text(t + 3.5, kx + 220, 380, "~$6M traced", (200, 230, 255), dur=2.5, size=40)
mag.move(t + 4.4, 1900, 120, ease="in", rot=20.0)
mag.hide(t + 4.41)
kim.key(t + 3.3, pose={**P.HOLD_UP, "head": 20}, ground=CANVAS_FLOOR - 440)
t_down = t + 4.6
cand.move(t_down + 0.8, kx, CANVAS_FLOOR, ease="in", arc=0, h=1.0)
cand.hide(t_down + 0.81)
for k in range(round(t_down * sc.fps) + 1, round((t_down + 0.8) * sc.fps) + 1):
    tt = k / sc.fps
    kim.key(tt, ease="linear", ground=CANVAS_FLOOR - cand.look(tt)["h"], pose=P.STAND)
t = t_down + 0.8

# ---------------------------------------------------------------- 3. fame: out onto the desktop
c_tr.detach(t + 0.4)
c_tr.key(t + 0.4, ease="linear")
c_tr.key(t + 0.7, ease="linear", alpha=0.0, scale=0.3)
c_tr.hide(t + 0.71)
cur.move(t + 0.6, (D.CLOSE[0] + D.CLOSE[2]) / 2, (D.CLOSE[1] + D.CLOSE[3]) / 2, t0=t)
D.hover_close(t + 0.45, t + 0.7)
cur.click(t + 0.65)
D.close_window(t + 0.7)
sc.sfx(t + 0.7, "swoosh_down", 960, gain=0.6)
t = kim.leap(0.45, kim.last["x"], TASK, 20, t0=t + 0.72, land=P.CROUCH)
kim.key(t + 0.3, pose=P.STAND)
cur.move(t + 0.6, 1700, 160)
t_fame = t + 0.4
car = sc.prop("car", -320, TASK, layer="back", facing=1)
car.move(t_fame + 0.9, 560, TASK, t0=t_fame, ease="out", arc=0)
sc.sfx(t_fame, "whoosh", 300, dur=0.8)
sc.sfx(t_fame + 0.9, "thud", 560, gain=0.4)
kim.turn(t_fame + 0.5)
kim.key(t_fame + 1.1, pose=P.CROSSED)
flashes(t_fame + 1.2, t_fame + 2.6, 200, 1300, 600, 950, 9)
prof = open_win(t_fame + 1.4, 1450, 300, w=560, h=250, title="Profile", content="profile", name="Kimchi",
                handle="@kimchi1x", bio="memecoin trader")
story = open_win(t_fame + 2.0, 1450, 640, w=560, h=250, title="Stories", content="blank", size=28,
                 text="@gunna shared @kimchi1x\nin his Instagram story")
caption(t_fame + 1.0, t_fame + 5.2, "Supercar vlogs, a shout-out from rapper Gunna: the trader became a celebrity.",
        "sources: X trending, Bitcoin Foundation")
t = t_fame + 5.4
close_win(prof, t)
close_win(story, t + 0.1)
car.move(t + 1.0, 2300, TASK, t0=t + 0.2, ease="in", arc=0)
sc.sfx(t + 0.2, "whoosh", 900, dur=0.8)
kim.turn(t + 0.3)

# ---------------------------------------------------------------- 4. Pump.fun signs him; $KIMCHI to ~$40M
alon = sc.figure(2100, TASK, size=SIZE, color=ALON, facing=-1, visible_from=t)
alon.hold(t + 0.2)
t_a = alon.walk(1125, t0=t + 0.2)
tag = sc.prop("label", 2100, 700, layer="front", text="pump.fun co-founder", color=(180, 230, 255), size=24,
              visible=False)
tag.show(t + 0.2)
tag.attach(t + 0.2, t_a + 3.0, alon, "head", (0.0, -70.0))
tag.hide(t_a + 3.0)
kim.walk(955, t0=t + 0.6)
ann = open_win(t_a - 0.2, 960, 280, w=820, h=260, title="pump.fun - announcement", content="blank", size=40,
               text="PUMP.FUN  x  KIMCHI\ncreative partner", color=(30, 140, 80))
caption(t_a, t_a + 4.0, "Oct 20, 2026: Pump.fun signs Kimchi as a creative partner.",
        "co-founder Alon calls him the first trader to become a celebrity")
mid = (955 + 1125) / 2
_, ny = kim.point(t_a + 0.3, "neck")
kim.reach(t_a + 0.4, "r", (mid, ny + 70), pose=P.STAND)
alon.reach(t_a + 0.4, "r", (mid, ny + 70), pose=P.STAND)
for i in range(3):
    dy = 18 if i % 2 == 0 else 0
    kim.reach(t_a + 0.55 + i * 0.13, "r", (mid, ny + 70 + dy), pose=P.STAND, ease="smooth")
    alon.reach(t_a + 0.55 + i * 0.13, "r", (mid, ny + 70 + dy), pose=P.STAND, ease="smooth")
sc.sfx(t_a + 0.4, "clap", mid)
banner(t_a + 0.5, "SIGNED", LIME, dur=1.2, y=560)
sc.sfx(t_a + 0.5, "fanfare", None, gain=0.6)
flashes(t_a + 0.5, t_a + 1.5, 700, 1400, 650, 950, 6)
kim.key(t_a + 1.3, pose=P.STAND)
alon.key(t_a + 1.3, pose=P.STAND)
t = t_a + 2.2
close_win(ann, t)
SERIES = [(0.0, 0.08), (0.08, 0.3), (0.3, 0.25), (0.25, 0.62), (0.62, 0.55), (0.55, 0.92), (0.92, 1.0)]
ch1 = open_win(t + 0.2, 960, 330, w=900, h=420, title="Chart - $KIMCHI", content="chart", ticker="$KIMCHI",
               series=SERIES, progress=0.0, mc=0.0)
ch1.key(t + 0.5, ease="linear")
ch1.key(t + 2.6, ease="out", progress=float(len(SERIES)), mc=40_000_000.0)
for i in range(6):
    sc.sfx(t + 0.6 + i * 0.32, "coin", 960, gain=0.4)
kim.key(t + 1.2, pose=P.LOOK_UP)
caption(t + 0.6, t + 4.8, "His creator coin $KIMCHI hits ~$40M within an hour...",
        "...with one wallet reportedly holding most of the supply (The Defiant, Solana Floor)")
kim.key(t + 2.7, pose=P.CHEER, ease="back")
alon.key(t + 2.7, pose={**P.STAND, "head": -20})
t = t + 5.0
close_win(ch1, t)
alon.turn(t + 0.2)
t_ag = alon.walk(1500, t0=t + 0.3)
alon.turn(t_ag + 0.1)
tk = kim.walk(250, t0=t + 0.3)
kim.turn(tk + 0.1)

# ---------------------------------------------------------------- 5. Oct 22: the QR post, the repost, the crash
t5 = t + 0.9
post = open_win(t5, 650, 390, w=560, h=540, title="Feed", content="post", text="", qr=True, reposts=0.0,
                likes=0.0, reposted_by=None)
caption(t5 + 0.2, t5 + 4.2, "Oct 22: Kimchi's account posts an image with a QR code.",
        "it links to a brand-new Pump.fun token: 'Project Kimchi'")
cur.move(t5 + 1.6, 520, 470, t0=t5 + 0.6)
cur.click(t5 + 1.7)
sc.sfx(t5 + 1.75, "coin", 520, gain=0.6)
ch2 = open_win(t5 + 1.9, 1430, 330, w=820, h=440, title="Chart - PROJECT KIMCHI", content="chart",
               ticker="PROJECT KIMCHI", series=[(0.0, 0.06), (0.06, 0.2), (0.2, 0.5), (0.5, 0.82), (0.82, 1.0),
                                                (1.0, 0.02)], progress=0.0, mc=900_000.0)
t_rp = t5 + 2.8
alon.key(t_rp, pose=P.POINT_UP, ease="snap")
post.key(t_rp + 0.1, ease="linear", reposted_by="Alon (pump.fun)")
post.key(t_rp + 2.2, ease="out", reposts=1800.0, likes=6400.0)
sc.sfx(t_rp + 0.1, "swish", 1500, gain=0.6)
float_text(t_rp + 0.1, 1500, 760, "repost", LIME, size=36)
caption(t_rp + 0.4, t_rp + 4.4, "A Pump.fun co-founder reposts it. The token rockets to ~$15M in minutes.",
        "sources: crypto.news, Cryptopolitan, FinanceFeeds")
ch2.key(t_rp + 0.3, ease="linear")
ch2.key(t_rp + 2.8, ease="out", progress=5.0, mc=15_000_000.0)
for i in range(7):
    sc.sfx(t_rp + 0.4 + i * 0.3, "coin", 1430, gain=0.35)
alon.key(t_rp + 1.0, pose=P.STAND)
# the crowd piles in
crowd = []
spots = [880, 990, 1100, 1210, 1320, 1700]
for i, x1 in enumerate(spots):
    x0 = -150 - 90 * i if i % 2 == 0 else 2070 + 90 * i
    g = sc.figure(x0, TASK, size=62, color=CROWD, facing=1 if x0 < 0 else -1, visible_from=t_rp + 0.5)
    g.hold(t_rp + 0.5 + 0.15 * i)
    tg = g.walk(x1, run=True)
    g.key(tg + 0.2, pose=P.CHEER if i % 2 else P.LOOK_UP)
    crowd.append(g)
t_crash = t_rp + 4.6
post.key(t_crash, ease="linear", deleted=True)
sc.impact(t_crash, 650, 390, 0.35)
sc.sfx(t_crash, "swoosh_down", 650, gain=0.7)
float_text(t_crash + 0.05, 650, 260, "post deleted", RED, size=38)
post.key(t_crash + 0.6, ease="linear", reposted_by=None)
float_text(t_crash + 0.6, 1500, 760, "repost removed", RED, size=34)
alon.key(t_crash + 0.6, pose=SHRUG)
ch2.key(t_crash + 0.7, ease="linear")
ch2.key(t_crash + 1.4, ease="in", progress=6.0, mc=284_000.0, mc_color=RED)
shell_x = 1100
sh = sc.prop("candle", shell_x + 250, -250, layer="front", color="red", visible=False, rot=25, h=200)
sh.show(t_crash + 1.0)
sh.move(t_crash + 1.4, shell_x, TASK - 90, ease="in", arc=0)
sh.hide(t_crash + 1.4)
sc.sfx(t_crash + 1.0, "swoosh_down", shell_x, gain=0.6)
sc.explosion(t_crash + 1.4, shell_x, TASK, 1.0)
sc.hitstop(t_crash + 1.4, 0.12)
banner(t_crash + 1.5, "-98%", RED, dur=1.6, sub="~$15M -> ~$284K in about 30 minutes", size=170)
for g in crowd:
    gx = g.point(t_crash + 1.4, "hip")[0]
    side = 1 if gx >= shell_x else -1
    pw = max(0.3, 1 - abs(gx - shell_x) / 900)
    g.ragdoll(t_crash + 1.42, t_crash + 3.6, bounds=DESK, ground=TASK,
              kicks=[(side * 1300 * pw, -1500 * pw, ["hip", "neck", "head"]),
                     (side * 900 * pw, -900 * pw, ["l_foot", "r_foot", "l_knee", "r_knee"])])
kim.key(t_crash + 1.5, pose=P.STARTLED, lift=14, ease="out")
kim.key(t_crash + 1.7, pose=P.STARTLED, lift=0, ease="in")
caption(t_crash + 0.3, t_crash + 4.6, "Then the post vanished, and so did the repost. Down ~98%.",
        "Kimchi, Alon and Pump.fun have not publicly explained what happened")

# ---------------------------------------------------------------- 6. hacked? the sleuths
t6 = t_crash + 4.0
close_win(post, t6)
hood = sc.figure(560, TASK, size=SIZE, color=(50, 34, 64), hat="hood", facing=1, visible_from=t6 + 0.4,
                 pose=P.CROSSED)
hood.visible_until = t6 + 4.4
sc.dust(t6 + 0.4, 560, TASK, n=8, power=0.7)
sc.sfx(t6 + 0.4, "boop", 560, gain=0.5)
qb = sc.prop("bubble", 560, 660, layer="front", text="?", size=60, visible=False)
qb.show(t6 + 0.6)
qb.hide(t6 + 4.3)
slam_stamp(t6 + 1.4, 560, 820, "UNCONFIRMED", until=t6 + 4.2, size=40)
sc.dust(t6 + 4.4, 560, TASK, n=8, power=0.7)
kim.key(t6 + 0.6, pose={**P.STAND, "head": 10})
kim.turn(t6 + 0.7)
caption(t6 + 0.5, t6 + 4.6, "Hacked? Early posts blamed a compromised account. Sleuths doubted it.",
        "still unconfirmed")
mag2 = sc.prop("magnifier", 1900, 600, layer="front", visible=False, rot=-20, scale=1.3)
mag2.show(t6 + 3.0)
mag2.move(t6 + 3.8, 1500, 360, ease="smooth", rot=0.0)
mag2.move(t6 + 4.6, 1350, 400, ease="smooth")
float_text(t6 + 4.0, 1420, 600, "early wallets: +$385K", GOLD, dur=2.6, size=44)
caption(t6 + 4.9, t6 + 8.8, "Lookonchain: early wallets sold into the spike for $385K+.",
        "Kimchi's wallet reportedly received ~500M tokens before the promo")
mag2.move(t6 + 8.4, 2100, 200, ease="in")
mag2.hide(t6 + 8.41)
# the crowd picks itself up
for i, g in enumerate(crowd):
    g.key(t6 + 0.6 + 0.2 * i, pose=P.HANDS_KNEES, ground=TASK)
    g.key(t6 + 1.1 + 0.2 * i, pose=P.CROUCH)
    g.key(t6 + 1.5 + 0.2 * i, pose=P.STAND)

# ---------------------------------------------------------------- 7. aftermath
t7 = t6 + 8.6
close_win(ch2, t7 - 0.4)
prof2 = open_win(t7, 760, 330, w=640, h=260, title="Profile", content="profile", name="Kimchi",
                 handle="@kimchi1x", bio="trader | pumpfun")
caption(t7 + 0.3, t7 + 4.0, "He scrubbed Pump.fun from his X bio and deleted posts about the deal.")
cur.key(t7 + 0.4, icon="eraser", ease="linear")
cur.move(t7 + 1.2, 760, 470, t0=t7 + 0.4)
bio = "trader | pumpfun"
for j, n in enumerate(range(len(bio), len("trader") - 1, -1)):
    tt = t7 + 1.3 + j * 0.09
    prof2.key(tt, ease="linear", bio=bio[:n])
    cur.key(tt, ease="linear", x=700 + 11 * n + (8 if j % 2 else -8), y=470 + (6 if j % 2 else 0))
    if j % 2 == 0:
        sc.sfx(tt, "pencil", 760, dur=0.08, gain=0.6)
t_er = t7 + 1.3 + (len(bio) - len("trader")) * 0.09
cur.key(t_er + 0.2, icon="arrow", ease="linear")
cur.move(t_er + 0.8, 1750, 200)
signs = [("BOYCOTT", 0), ("WHERE'S THE\nAIRDROP?", 2), ("WHAT\nHAPPENED?", 4)]
t_b = t_er + 0.6
for txt, gi in signs:
    g = crowd[gi]
    b = sc.prop("bubble", 0, 0, layer="front", text=txt, size=22, visible=False)
    b.show(t_b + 0.2 * gi)
    b.attach(t_b + 0.2 * gi, t_b + 4.2, g, "head", (0.0, -90.0))
    b.hide(t_b + 4.2)
    g.key(t_b + 0.2 * gi, pose=P.FIST_UP if gi != 2 else SHRUG, ease="snap")
caption(t_b + 0.2, t_b + 4.4, "Traders called for a Pump.fun boycott. As of Oct 27, no one has explained it.",
        "sources: Protos, IcoBench, Bitcoin.com News")
close_win(prof2, t_b + 3.6)

# ---------------------------------------------------------------- 8. ending
t8 = t_b + 4.6
for i, g in enumerate(crowd):
    g.turn(t8 + 0.1 * i)
    tg = g.walk(2200 if i % 2 else -300, run=True, t0=t8 + 0.15 + 0.1 * i)
    g.visible_until = tg
alon.turn(t8 + 0.3)
ta = alon.walk(2300, t0=t8 + 0.4)
alon.visible_until = ta
kim.key(t8 + 0.4, pose={**P.STAND, "head": 15})
kim.turn(t8 + 1.6)
kim.key(t8 + 2.0, pose=SHRUG, ease="back")
cur.move(t8 + 2.4, kim.last["x"] + 120, 760, t0=t8 + 1.2)
kim.key(t8 + 2.8, pose={**SHRUG, "head": -10})
t_end = kim.hold(t8 + 3.6)
sc.fade_out(t_end, t_end + 1.0)
sc.title(t_end + 1.2, t_end + 6.0, "THE KIMCHI STORY", "Still unfolding. Allegations unproven. Not financial advice.",
         color=(255, 120, 90))
sc.title(t_end + 1.2, t_end + 6.0, "", "Sources: KuCoin News, Crypto Times, Cryptopolitan, crypto.news, FinanceFeeds,",
         y=860, size=1)
sc.title(t_end + 1.2, t_end + 6.0, "", "Bitcoin.com News, Protos, Solana Floor, The Defiant", y=905, size=1)
sc.sfx(t_end + 1.2, "big_hit", None, gain=0.5)
make_captions()
END = t_end + 6.3
sc.duration = END
sc.sfx(0.0, "drone", None, gain=0.22, dur=END + 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="the_kimchi_story.mp4")
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
