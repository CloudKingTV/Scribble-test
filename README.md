# stickanim

Procedural stick-figure action animation in the style of the classic "stick figure fights the
mouse cursor on a computer desktop" shorts. You write the choreography as a Python script.
The engine handles the rest: rig, physics, effects, sound, and an MP4 output.

**Needs:** Python 3.9+, Pillow, NumPy, and `ffmpeg` on the PATH.

```bash
python3 movie.py                       # render stick_vs_cursor.mp4 (~40 s, 1080p30, with sound)
python3 movie.py --still 19.4          # one frame at t=19.4 s -> still.png
python3 movie.py --sheet 5,10.8,19.4   # contact sheet of several moments -> sheet.png
```

The full render takes about 40 seconds on 4 cores, because frames render in parallel.

## What's in the box

| Module | What it does |
|---|---|
| `rig.py` | 11-joint skeleton, forward kinematics, two-bone IK, and pose ↔ joint-position conversion |
| `actors.py` | `Figure` and `Cursor` timelines: keyframes with easing (incl. overshoot/snap), walk/run cycles with planted feet, ballistic leaps and flips, ragdoll segments, IK reaches, pencil "draw-on", spring follow-through, idle breathing |
| `physics.py` | Verlet ragdoll with joint limits, wall/floor collisions, and pins (so the cursor can grab the head and fling the figure) |
| `scene.py` | Effects (impact bursts, dust, smear frames, speed lines, screen shake, flash, punch-in zoom, hit-stop freeze frames), baking, and parallel rendering into ffmpeg |
| `desktop.py` | The stage: wallpaper, icons, taskbar, a drawing-app window that opens/closes, tool palette, and cursor icons (arrow, open hand, grab, pencil, eraser) |
| `audio.py` | Synthesised SFX (whooshes, punches, thuds, clicks, pencil scratch, footsteps…) mixed in stereo with room reverb |
| `poses.py` | A pose library: READY, PUNCH, FLY_KICK, UPPERCUT, HERO_LAND, TUCK, … |

## Writing a scene

Authoring is sequential. Each action returns the time it ends, so you can chain them. Physics runs
while you write the script, so you can ask where a body part will be and aim the next beat there.

```python
from stickanim import Desktop, Scene, poses as P

D = Desktop()
sc = Scene(duration=8, backdrop=D)
D.open_window(0.0)
floor = D.CANVAS[3]

hero = sc.figure(700, floor)
cur = sc.cursor(1300, 400)

t = hero.walk(1000, t0=0.5, run=True)                 # planted-foot run
t = hero.leap(0.6, 1150, floor, height=150, t0=t, spin=360,
              poses_=[(0.3, P.TUCK), (0.7, P.TUCK)])  # front flip
hero.key(t + 0.3, pose=P.READY)

t_hit = t + 0.8
hero.key(t_hit, pose=P.PUNCH, ease="snap")
fist = hero.point(t_hit, "r_hand")                    # where will the fist be?
cur.move(t_hit, *fist, t0=t)                          # ...put the cursor there
sc.hit(t_hit, *fist, power=0.8)                       # sound + burst + shake + freeze frame
cur.move(t_hit + 0.4, 1500, 200, rot=400, ease="out") # knocked spinning

sc.render("short.mp4")
```

Angles are in degrees in the figure's own frame: 0 = hanging down, +90 = pointing forward,
180 = up. Each joint is relative to its parent. `spin` rotates the whole body (+ = front flip).
See `rig.py` for the details.
