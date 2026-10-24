"""STICK vs. CURSOR — a short desktop action animation.

    python3 movie.py                    # full render -> stick_vs_cursor.mp4
    python3 movie.py --still 18.6       # one frame (world time in seconds) -> still.png
    python3 movie.py --sheet 2,9,13     # contact sheet of several times -> sheet.png
"""

import argparse

from stickanim import Desktop, Scene
from stickanim import poses as P
from stickanim.rig import HEAD_R, fk

D = Desktop()
sc = Scene(duration=40.0, backdrop=D)
FLOOR, TASKBAR = D.CANVAS[3], D.TASKBAR_Y
SIZE = 86
R = HEAD_R * SIZE

cur = sc.cursor(1480, 760)
hero = sc.figure(900, FLOOR, size=SIZE, color=(32, 168, 72), visible_from=1e9)

# ---------------------------------------------------------------- 1. open the app, draw a stick figure
cur.move(1.0, *D.APP_ICON, t0=0.3)
cur.click(1.05)
D.open_window(1.1)
sc.sfx(1.1, "pop", 960)
cur.move(1.9, *D.tool_pos("pencil"), t0=1.4)
cur.click(1.95)
D.select_tool(1.95, "pencil")
cur.key(2.0, icon="pencil", ease="linear")
hx, hy = hero.point(2.0, "head")
cur.move(2.6, hx, hy - R, t0=2.1)
t = hero.draw_on(2.6, 5.0, cur)
cur.key(5.1, icon="arrow", ease="linear")
cur.move(5.7, 1260, 430)

# ---------------------------------------------------------------- 2. it comes alive
hero.key(5.75)
hero.key(5.82, pose={"head": 10, "l_arm": 20}, ease="snap")
hero.key(5.95, pose=P.STAND)
hero.key(6.35, pose=P.LOOK_HANDS)
hero.key(6.8)
hero.key(6.92, pose={**P.LOOK_HANDS, "l_elbow": 100, "r_elbow": 105}, ease="snap")
hero.key(7.05, pose=P.LOOK_HANDS)
hero.key(7.35, pose=P.STAND)
hero.turn(7.4)
hero.key(7.6, pose={**P.STAND, "head": -6})
hero.turn(7.95)
hero.key(8.05, pose=P.STAND)
cur.move(8.0, 1230, 455, ease="smooth", arc=0.3)
# notices the cursor: startled hop, then a wary guard
hero.key(8.12, pose=P.STARTLED, lift=16, ease="out")
hero.key(8.26, pose=P.STARTLED, lift=0, ease="in")
sc.sfx(8.12, "swish", 900, gain=0.4)
hero.key(8.6, pose=P.READY)
hero.hold(9.1)

# ---------------------------------------------------------------- 3. poke, poke, punch
hx, hy = hero.point(9.1, "head")
cur.move(9.1, hx + R * 0.8, hy - R * 0.6, t0=8.5, ease="in")
cur.click(9.1)
sc.sfx(9.1, "boop", hx)
x = hero.last["x"]
hero.key(9.18, pose=P.RECOIL, x=x - 26, ease="snap")
hero.key(9.45, pose={**P.RECOIL, "head": -18})
hero.key(9.65, pose=P.ANGRY, x=x - 26)
cur.move(9.45, 1150, 520, t0=9.12, ease="out")
for i, tt in enumerate((9.85, 9.97, 10.09, 10.21)):
    hero.key(tt, pose={**P.FIST_UP, "r_elbow": 40 if i % 2 == 0 else 5}, ease="smooth")
hero.key(10.45, pose=P.ANGRY)
hero.key(10.62, pose=P.PUNCH_WIND, ease="smooth")
x = hero.last["x"]
sc.sfx(10.72, "swish", x)
hero.key(10.84, pose=P.PUNCH, x=x + 20, ease="snap")
target = hero.point(10.84, "r_hand")
cur.move(10.84, target[0] + 4, target[1] - 4, t0=10.45, ease="in")
sc.hit(10.84, *target, power=0.5)
cur.move(11.25, 1330, 300, t0=10.84, ease="out", rot=250)
cur.move(11.7, 1300, 330, ease="smooth", rot=360)
cur.key(11.7001, rot=0.0, ease="linear")
hero.key(11.15, pose=P.READY, x=x + 10)
hero.key(11.45, pose={**P.READY, "head": -12, "lean": 2})
hero.hold(11.9)

# ---------------------------------------------------------------- 4. the cursor grabs him and throws him
cur.key(11.75, icon="open", ease="linear")
hero.turn(11.95)
hero.walk(hero.last["x"] - 360, run=True)       # tries to run away...
t_grab = 12.3
hx, hy = hero.point(t_grab, "head")
cur.move(t_grab, hx + 4, hy - 8, t0=11.8, ease="in", arc=-0.2)
cur.click(t_grab)
cur.key(t_grab + 0.02, icon="grab", ease="linear")
moves = [(12.7, 900, 440, "smooth"), (12.84, 1040, 420, "smooth"), (12.98, 840, 450, "smooth"),
         (13.12, 1040, 420, "smooth"), (13.26, 880, 445, "smooth"), (13.5, 1180, 380, "smooth"),
         (13.68, 640, 470, "linear")]
for tt, mx, my, ease in moves:
    cur.move(tt, mx, my, ease=ease, arc=0.05)
    sc.sfx(tt - 0.1, "whoosh", mx, gain=0.5, dur=0.22)
t_release = 13.68
cur.key(t_release + 0.01, icon="open", ease="linear")
cur.move(13.95, 560, 500, ease="out")
cur.key(14.1, icon="arrow", ease="linear")
cur.move(14.9, 1180, 470, ease="smooth")
t = hero.ragdoll(t_grab, 15.1, pins=[("head", cur, t_grab, t_release, (0.0, 10.0))], ground=FLOOR)

# ---------------------------------------------------------------- 5. gets up, dodges, flips away
xg = max(hero.last["x"], D.CANVAS[0] + 150)
hero.key(15.55, pose=P.HANDS_KNEES, x=xg, ground=FLOOR)
hero.key(15.95, pose=P.CROUCH, x=xg + 10)
hero.key(16.3, pose=P.STAND)
hero.turn(16.4)
hero.key(16.55, pose={**P.STAND, "head": 16, "lean": 6})
hero.key(16.68, pose={**P.STAND, "head": -10})
hero.key(16.8, pose={**P.STAND, "head": 12})
hero.key(17.0, pose=P.READY)
x = hero.last["x"]
_, hy = hero.point(17.0, "head")
cur.key(17.0, icon="open", ease="linear")
cur.move(17.2, x + 330, hy, t0=17.0)
hero.key(17.3, pose=P.DUCK, ease="snap")
cur.move(17.42, x, hy - 6, ease="in", arc=0)
cur.click(17.42)
cur.key(17.44, icon="grab", ease="linear")
cur.move(17.62, x - 230, hy + 10, ease="out", arc=0)
sc.sfx(17.3, "whoosh", x, dur=0.3)
cur.key(17.7, icon="open", ease="linear")
cur.move(17.95, x - 40, 380, ease="smooth")
t = hero.leap(0.62, x + 320, FLOOR, 170, t0=17.9, spin=360,
              poses_=[(0.22, P.TUCK), (0.75, P.TUCK)], land=P.CROUCH)
sc.sfx(17.92, "whoosh", x, dur=0.35)
cur.move(18.14, x, FLOOR - 14, ease="in", arc=0)
cur.key(18.16, icon="grab", ease="linear")
sc.sfx(18.14, "thud", x, gain=0.6)
sc.dust(18.14, x, FLOOR, n=6, power=0.5)
sc.shake(18.14, 6, 0.2)
x_cur_floor = x
hero.key(t + 0.25, pose=P.READY)

# ---------------------------------------------------------------- 6. flying kick
t = hero.turn(t + 0.35)
cur.key(t, icon="arrow", ease="linear")
cur.move(t + 0.3, x_cur_floor + 30, 560, ease="smooth")
hero.walk(hero.last["x"] - 130, run=True, t0=t + 0.05)
t = hero.truncate(hero.now - 0.08)
x0 = hero.last["x"]
t_land = hero.leap(0.6, x0 - 280, FLOOR, 190, poses_=[(0.22, P.FLY_KICK), (0.7, P.FLY_KICK)], land=P.HERO_LAND)
t_hit = t + 0.6 * 0.4
foot = hero.point(t_hit, "r_foot")
cur.move(t_hit, foot[0] - 6, foot[1] - 8, ease="in")
sc.sfx(t_hit - 0.12, "swish", foot[0])
sc.hit(t_hit, *foot, power=1.0)
corner = (D.CANVAS[0] + 20, D.CANVAS[1] + 30)
cur.move(t_hit + 0.3, *corner, ease="out", rot=-520)
sc.sfx(t_hit + 0.3, "thud", corner[0], gain=0.6)
sc.impact(t_hit + 0.3, corner[0] - 10, corner[1] - 10, 0.4)
cur.move(t_hit + 0.8, D.CANVAS[0] + 40, FLOOR - 14, ease="in", rot=-630)
sc.sfx(t_hit + 0.8, "thud", D.CANVAS[0] + 40, gain=0.5)
sc.dust(t_hit + 0.8, D.CANVAS[0] + 40, FLOOR, n=5, power=0.4)
sc.shake(t_land, 10, 0.25)
hero.hold(t_land + 0.3)
t = hero.key(t_land + 0.6, pose=P.STAND)
for i in range(4):
    t = hero.key(t + 0.12, pose=P.CLAP_SHUT if i % 2 == 0 else P.CLAP_OPEN, ease="snap")
    if i % 2 == 0:
        sc.sfx(t, "clap", hero.last["x"])
t = hero.key(t + 0.2, pose=P.STAND)
t_walked = hero.walk(820, t0=t + 0.2)                  # strolls back to the middle

# ---------------------------------------------------------------- 7. the eraser
cur.key(t - 0.2, rot=-630)
cur.key(t + 0.1, rot=-720, ease="smooth")
cur.key(t + 0.1001, rot=0.0, ease="linear")
for i, rr in enumerate((18, -14, 8, 0)):
    cur.key(t + 0.2 + i * 0.07, rot=rr)
t = cur.move(t + 0.9, *D.tool_pos("eraser"), t0=t + 0.5)
cur.click(t)
D.select_tool(t, "eraser")
cur.key(t + 0.05, icon="eraser", ease="linear")
t = cur.move(t + 0.5, D.CANVAS[0] + 60, FLOOR - 20, t0=t + 0.1)
t_sweep = max(t, t_walked + 0.5)
hx = hero.last["x"]
cur.move(t_sweep + 0.55, D.CANVAS[2] - 80, FLOOR - 20, t0=t_sweep, ease="smooth", arc=0)
sc.sfx(t_sweep + 0.1, "whoosh", hx, dur=0.4)
hero.key(t_sweep + 0.05, pose=P.CROUCH)
t = hero.leap(0.5, hx, FLOOR, 150, t0=t_sweep + 0.15, poses_=[(0.3, P.TUCK), (0.7, P.TUCK)], land=P.CROUCH)
t = hero.key(t + 0.2, pose=P.READY)
_, hy = hero.point(t, "head")
t_catch = t + 0.45
cur.move(t + 0.2, D.CANVAS[2] - 120, hy - 60, t0=t_sweep + 0.6)
hand_target = (hx + 70, hy - 30)
cur.move(t_catch, *hand_target, ease="in")
hero.reach(t_catch, "r", hand_target, pose=P.READY)
sc.sfx(t_catch, "clap", hx)
sc.impact(t_catch, *hand_target, 0.25)
t = t_catch
for i in range(2):
    hero.key(t + 0.25, pose=P.OVERHEAD, ease="smooth")
    t = hero.key(t + 0.42, pose=P.SLAM, ease="in")
    p = hero.point(t, "r_hand")
    sc.hit(t, p[0], FLOOR - 10, power=0.55, sound="hit")
    sc.dust(t, p[0], FLOOR, n=8, power=0.7)
    t += 0.08
hero.key(t + 0.3, pose=P.THROW_WIND, ease="smooth")
t_rel = hero.key(t + 0.45, pose=P.THROW, ease="in")
sc.sfx(t_rel - 0.1, "whoosh", hx, dur=0.25)
cur.attach(t_catch, t_rel, hero, "r_hand")
cur.move(t_rel + 0.22, D.CANVAS[2] - 18, 560, ease="linear", rot=380, arc=0)
sc.hit(t_rel + 0.22, D.CANVAS[2] - 10, 560, power=0.6, sound="hit")
cur.move(t_rel + 0.7, D.CANVAS[2] - 60, FLOOR - 14, ease="in", rot=450)
cur.key(t_rel + 0.72, icon="arrow", ease="linear")
sc.sfx(t_rel + 0.7, "thud", D.CANVAS[2] - 60, gain=0.6)
hero.key(t_rel + 0.35, pose=P.STAND)

# ---------------------------------------------------------------- 8. escape through the close button
t = hero.key(t_rel + 0.9, pose=P.LOOK_UP)
t = hero.key(t + 0.45, pose=P.POINT_UP, ease="snap")
hero.key(t + 0.5, pose=P.STAND)
ux = (D.CLOSE[0] + D.CLOSE[2]) / 2
hand = fk(P.UPPERCUT, 0, 0, 1, 0, SIZE)["r_hand"]
x_take = ux - hand[0]
t = hero.walk(x_take, run=True, t0=t + 0.55)
t = hero.key(t + 0.15, pose=P.CROUCH, ease="smooth")
u_hit, dur = 0.42, 0.95
y0 = hero.last["y"]
end_y = hero._snap_y(dict(hero.last, pose=P.HERO_LAND, ground=TASKBAR, lift=0.0, spin=0.0))
want = D.CLOSE[3] - 6 - hand[1]                         # hip y that puts the fist on the button
H = ((1 - u_hit) * y0 + u_hit * end_y - want) / (4 * u_hit * (1 - u_hit))
t0 = t
t_land = hero.leap(dur, x_take, TASKBAR, H, poses_=[(0.25, P.UPPERCUT), (0.55, P.UPPERCUT), (0.8, P.TUCK)],
                   land=P.HERO_LAND)
t_hit = t0 + dur * u_hit
D.hover_close(t_hit - 0.25, t_hit + 0.05)
sc.hit(t_hit, ux, D.CLOSE[3], power=0.9)
D.close_window(t_hit + 0.02)
sc.sfx(t_hit + 0.05, "swoosh_down", ux, gain=0.7)
cur.key(t_hit + 0.02, visible=False, ease="linear")
sc.shake(t_land, 16, 0.35)
sc.dust(t_land, x_take, TASKBAR, n=10, power=1.0)

# ---------------------------------------------------------------- 9. alone on the desktop
t = hero.key(t_land + 0.5, pose=P.STAND)
t = hero.key(t + 0.35, pose={**P.STAND, "head": -14})
t = hero.turn(t + 0.3)
t = hero.key(t + 0.4, pose={**P.STAND, "head": 8})
cur.key(t, x=-40, y=760, visible=True, rot=-15, icon="arrow", ease="linear")
t2 = cur.move(t + 1.4, 1250, 860, ease="smooth", arc=0.1)
t = hero.key(t + 1.1, pose={**P.STAND, "head": -4})
t = hero.key(t + 0.15, pose=P.READY, ease="snap")
sc.sfx(t, "swish", hero.last["x"], gain=0.5)
t = hero.walk(hero.last["x"] - 70, t0=t + 0.05)
hero.key(t + 0.05, pose=P.READY)
cur.hold(t - 0.1)
cur.move(t + 0.3, -80, 600, ease="in", rot=-40)
sc.sfx(t + 0.05, "whoosh", 600, dur=0.3)
cur.key(t + 0.3, visible=False, ease="linear")
t = hero.key(t + 0.7, pose=P.STAND)
t = hero.turn(t + 0.25)
t = hero.key(t + 0.4, pose=P.CROSSED)
hero.hold(t + 1.4)
sc.fade_out(t + 1.0, t + 2.0)
sc.title(t + 2.1, t + 4.6, "STICK vs. CURSOR", "a stickanim short")
sc.sfx(t + 2.1, "big_hit", None, gain=0.7)
sc.duration = t + 5.0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="stick_vs_cursor.mp4")
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
        tiles = [Image.open(sc.still(tt, os.path.join(tmp, f"{i}.png"), data)).resize((640, 360)) for i, tt in enumerate(times)]
        cols = 3
        sheet = Image.new("RGB", (640 * cols, 360 * ((len(tiles) + cols - 1) // cols)))
        for i, tile in enumerate(tiles):
            sheet.paste(tile, ((i % cols) * 640, (i // cols) * 360))
        sheet.save("sheet.png")
        print("sheet.png")
    else:
        print(f"duration {sc.duration:.1f}s")
        sc.render(args.out)
