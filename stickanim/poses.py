"""A small library of key poses. Combine and tweak them: {**READY, "head": -20}."""

from .rig import JOINTS

ZERO = {j: 0.0 for j in JOINTS}


def P(**kw):
    return {**ZERO, **kw}


STAND = P(l_arm=12, l_elbow=10, r_arm=-10, r_elbow=8, l_leg=8, l_knee=-4, r_leg=-7, r_knee=-2)
READY = P(lean=8, head=5, l_arm=55, l_elbow=105, r_arm=25, r_elbow=115,
          l_leg=20, l_knee=-28, r_leg=-18, r_knee=-20)
LOOK_HANDS = P(lean=6, head=38, l_arm=42, l_elbow=72, r_arm=30, r_elbow=80,
               l_leg=8, l_knee=-4, r_leg=-7, r_knee=-2)
STARTLED = P(lean=-14, head=-12, l_arm=125, l_elbow=40, r_arm=100, r_elbow=55,
             l_leg=16, l_knee=-30, r_leg=-12, r_knee=-12)
RECOIL = P(lean=-24, head=-28, l_arm=70, l_elbow=20, r_arm=-45, r_elbow=35,
           l_leg=22, l_knee=-10, r_leg=-20, r_knee=-6)
ANGRY = P(lean=16, head=14, l_arm=-22, l_elbow=65, r_arm=-14, r_elbow=75,
          l_leg=14, l_knee=-18, r_leg=-14, r_knee=-12)
FIST_UP = {**ANGRY, "r_arm": 150, "r_elbow": 40, "head": -5}
PUNCH_WIND = P(lean=-4, head=8, l_arm=60, l_elbow=95, r_arm=-45, r_elbow=125,
               l_leg=26, l_knee=-30, r_leg=-22, r_knee=-14)
PUNCH = P(lean=18, head=6, l_arm=-25, l_elbow=100, r_arm=92, r_elbow=0,
          l_leg=32, l_knee=-34, r_leg=-28, r_knee=-4)
HANDS_KNEES = P(lean=72, head=-25, l_arm=72, l_elbow=0, r_arm=66, r_elbow=0,
                l_leg=2, l_knee=-92, r_leg=-4, r_knee=-88)
CROUCH = P(lean=32, head=-8, l_arm=35, l_elbow=25, r_arm=20, r_elbow=30,
           l_leg=75, l_knee=-135, r_leg=50, r_knee=-110)
HERO_LAND = P(lean=48, head=-28, l_arm=58, l_elbow=8, r_arm=-55, r_elbow=15,
              l_leg=85, l_knee=-145, r_leg=-25, r_knee=-105)
DUCK = P(lean=38, head=22, l_arm=140, l_elbow=85, r_arm=130, r_elbow=95,
         l_leg=75, l_knee=-135, r_leg=45, r_knee=-115)
TUCK = P(lean=40, head=30, l_arm=60, l_elbow=95, r_arm=50, r_elbow=105,
         l_leg=115, l_knee=-150, r_leg=105, r_knee=-145)
FLY_KICK = P(lean=-48, head=38, l_arm=-100, l_elbow=15, r_arm=45, r_elbow=110,
             l_leg=48, l_knee=-150, r_leg=96, r_knee=0)
UPPERCUT = P(lean=-6, head=-28, l_arm=-35, l_elbow=40, r_arm=178, r_elbow=0,
             l_leg=24, l_knee=-45, r_leg=-12, r_knee=-65)
OVERHEAD = P(lean=-12, head=-12, l_arm=172, l_elbow=12, r_arm=166, r_elbow=16,
             l_leg=20, l_knee=-12, r_leg=-18, r_knee=-8)
SLAM = P(lean=52, head=22, l_arm=82, l_elbow=0, r_arm=76, r_elbow=0,
         l_leg=42, l_knee=-62, r_leg=-22, r_knee=-30)
THROW_WIND = P(lean=-18, head=-6, l_arm=60, l_elbow=40, r_arm=-150, r_elbow=30,
               l_leg=28, l_knee=-12, r_leg=-22, r_knee=-25)
THROW = P(lean=26, head=8, l_arm=-40, l_elbow=50, r_arm=105, r_elbow=0,
          l_leg=30, l_knee=-36, r_leg=-28, r_knee=-6)
CLAP_OPEN = P(lean=4, head=24, l_arm=48, l_elbow=72, r_arm=80, r_elbow=28,
              l_leg=8, l_knee=-4, r_leg=-7, r_knee=-2)
CLAP_SHUT = P(lean=4, head=24, l_arm=62, l_elbow=50, r_arm=62, r_elbow=50,
              l_leg=8, l_knee=-4, r_leg=-7, r_knee=-2)
POINT_UP = P(lean=-6, head=-38, l_arm=-8, l_elbow=20, r_arm=150, r_elbow=0,
             l_leg=8, l_knee=-4, r_leg=-7, r_knee=-2)
CROSSED = P(lean=-4, head=-10, l_arm=26, l_elbow=112, r_arm=20, r_elbow=118,
            l_leg=14, l_knee=-3, r_leg=-13, r_knee=-2)
LOOK_UP = {**STAND, "head": -35, "lean": -5}
CHEER = P(lean=-6, head=-22, l_arm=165, l_elbow=18, r_arm=150, r_elbow=25,
          l_leg=16, l_knee=-8, r_leg=-14, r_knee=-6)
SQUISH = P(lean=12, head=28, l_arm=22, l_elbow=150, r_arm=14, r_elbow=150,
           l_leg=36, l_knee=-72, r_leg=24, r_knee=-62)
HOLD_UP = P(lean=-4, head=-26, l_arm=-16, l_elbow=40, r_arm=172, r_elbow=6,
            l_leg=16, l_knee=-6, r_leg=-15, r_knee=-4)
GRAB_LOW = P(lean=72, head=-32, l_arm=82, l_elbow=12, r_arm=72, r_elbow=12,
             l_leg=42, l_knee=-64, r_leg=-14, r_knee=-30)
PULL = P(lean=-30, head=12, l_arm=-62, l_elbow=22, r_arm=-72, r_elbow=12,
         l_leg=36, l_knee=-30, r_leg=-26, r_knee=-10)
