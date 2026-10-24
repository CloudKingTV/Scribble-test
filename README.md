# Scribble stick-figure animation

A small Python setup for making hand-drawn-style stick-figure videos. There's no GUI: you write the scene as code and it renders an MP4.

**Needs:** Python 3, Pillow, NumPy and `ffmpeg` on the PATH.

```bash
python3 demo.py                # render demo.mp4 (11 s, 1280x720, 24 fps)
python3 demo.py --still 4.0    # save one frame at t=4.0s as frame.png, for quick checks
```

## How it works

1. **Rig:** each `Figure` is a skeleton with ten joint angles (torso lean, head, shoulders, elbows, hips, knees). Forward kinematics turns the angles into bone positions. The lowest foot is placed on the ground automatically, so poses never float or sink into the floor.
2. **Keyframes:** `fig.key(t, x=..., lift=..., pose={...}, ease="smooth")` sets a keyframe. Values between keyframes are interpolated using `linear`, `smooth`, `in` or `out` easing.
3. **Scribble look:** every bone is drawn twice as a slightly bowed, jittered stroke. The head is a circle that overshoots where it closes. The jitter seed changes 8 times a second, which makes the lines "boil" like hand-drawn animation. The paper background has grain and a vignette.
4. **Output:** frames are drawn at 2× resolution, downsampled for antialiasing, and piped into `ffmpeg`, which encodes H.264 MP4.

## Writing a scene

```python
from stickanim import Figure, Scene, STAND

scene = Scene(duration=6)
bob = scene.add(Figure(x=-80, color=(40, 70, 160)))

bob.walk(0, 2.5, 600)          # walk on-screen
bob.wave(2.5, 3.5)             # wave
scene.say(bob, "Hello!", 2.5, 3.8)
bob.jump(4.0)                  # squat → leap → land (1.2 s)
bob.key(5.5, pose={**STAND, "lean": 30, "head": 20})   # custom pose: take a bow

scene.render("bob.mp4")
```

Angles are in degrees. 0 means "hanging straight down" and positive values move toward the direction the figure faces. Each joint is relative to its parent. For example, `l_knee: -60` bends the left knee back by 60°.

Main settings: `Figure(size=, color=, width=, facing=)`, `Scene(width=, height=, fps=, boil_fps=, ground_y=)`, and `Pen(wobble=)` for how shaky the lines are.
