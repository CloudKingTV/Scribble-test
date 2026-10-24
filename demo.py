"""Demo scene: two stick figures meet, say hi, and jump for joy.

    python3 demo.py                 # writes demo.mp4
    python3 demo.py --still 4.0     # writes a single frame at t=4.0s to frame.png
"""

import argparse

from stickanim import Figure, Scene

scene = Scene(width=1280, height=720, fps=24, duration=11.0)

alice = scene.add(Figure(x=-80, seed=1))
bob = scene.add(Figure(x=1360, color=(40, 70, 160), facing=-1, seed=2))

alice.walk(0.0, 3.0, 480)
alice.wave(3.0, 4.6)
scene.say(alice, "Hi!", 3.1, 4.6)

bob.hold(0.0, 3.6)
bob.walk(3.6, 6.2, 800)
bob.wave(6.2, 7.2, arm="l")
scene.say(bob, "Hey there!", 6.2, 7.4)

alice.hold(4.9, 7.4)
alice.jump(7.4)
bob.jump(7.5)
alice.hold(8.6, 11.0)
bob.hold(8.7, 11.0)

scene.title("The End", 9.2, 11.0)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="demo.mp4")
    ap.add_argument("--still", type=float, help="render one frame at this time instead")
    args = ap.parse_args()
    if args.still is not None:
        scene.render_frame(args.still, int(args.still * scene.fps)).save("frame.png")
        print("wrote frame.png")
    else:
        print("wrote", scene.render(args.out))
