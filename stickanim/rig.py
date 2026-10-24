"""Skeleton math: forward kinematics, inverse kinematics, and pose <-> points.

Angle convention (degrees, in the figure's own frame, so it works for either facing):
    0 = pointing straight down, +90 = pointing forward, 180 = up, -90 = backward.

Pose joints, each relative to its parent:
    lean      torso tilt (+ = lean forward)
    head      head tilt relative to the torso (+ = chin down / look down)
    l_arm     upper arm relative to hanging down the torso (+ = swing forward)
    l_elbow   forearm relative to the upper arm (+ = bend forward/up)
    l_leg     thigh relative to straight down (+ = forward)
    l_knee    shin relative to the thigh (- = normal knee bend)
    (same for r_*)

`spin` rotates the whole body around its centre (+ = front flip direction).
"""

import math

JOINTS = ["lean", "head", "l_arm", "l_elbow", "r_arm", "r_elbow",
          "l_leg", "l_knee", "r_leg", "r_knee"]
POINTS = ["hip", "neck", "head", "l_elbow", "l_hand", "r_elbow", "r_hand",
          "l_knee", "l_foot", "r_knee", "r_foot"]
BONES = [("hip", "neck"), ("neck", "head"),
         ("neck", "l_elbow"), ("l_elbow", "l_hand"),
         ("neck", "r_elbow"), ("r_elbow", "r_hand"),
         ("hip", "l_knee"), ("l_knee", "l_foot"),
         ("hip", "r_knee"), ("r_knee", "r_foot")]

# Bone lengths as multiples of the figure's `size`.
TORSO, NECK, HEAD_R = 1.0, 0.16, 0.34
UPPER_ARM, FOREARM = 0.58, 0.55
THIGH, SHIN = 0.66, 0.66
LEG = THIGH + SHIN
LENGTHS = {
    ("hip", "neck"): TORSO, ("neck", "head"): NECK + HEAD_R,
    ("neck", "l_elbow"): UPPER_ARM, ("l_elbow", "l_hand"): FOREARM,
    ("neck", "r_elbow"): UPPER_ARM, ("r_elbow", "r_hand"): FOREARM,
    ("hip", "l_knee"): THIGH, ("l_knee", "l_foot"): SHIN,
    ("hip", "r_knee"): THIGH, ("r_knee", "r_foot"): SHIN,
}


def wrap(a):
    """Wrap an angle to (-180, 180]."""
    a = (a + 180.0) % 360.0 - 180.0
    return 180.0 if a == -180.0 else a


def fk(pose, x, y, facing=1, spin=0.0, size=72.0):
    """Joint positions in world space. (x, y) is the hip before spin is applied."""
    f = facing

    def d(a, length):
        r = math.radians(a)
        return math.sin(r) * length * size, math.cos(r) * length * size

    local = {"hip": (0.0, 0.0)}

    def put(name, parent, a, length):
        dx, dy = d(a, length)
        px, py = local[parent]
        local[name] = (px + dx, py + dy)

    torso = 180.0 - pose["lean"]
    put("neck", "hip", torso, TORSO)
    put("head", "neck", torso - pose["head"], NECK + HEAD_R)
    down = -pose["lean"]
    for s in "lr":
        ua = down + pose[s + "_arm"]
        put(s + "_elbow", "neck", ua, UPPER_ARM)
        put(s + "_hand", s + "_elbow", ua + pose[s + "_elbow"], FOREARM)
        th = pose[s + "_leg"]
        put(s + "_knee", "hip", th, THIGH)
        put(s + "_foot", s + "_knee", th + pose[s + "_knee"], SHIN)

    if spin:
        cx = sum(p[0] for p in local.values()) / len(local)
        cy = sum(p[1] for p in local.values()) / len(local)
        c, s_ = math.cos(math.radians(spin)), math.sin(math.radians(spin))
        for k, (u, v) in local.items():
            u, v = u - cx, v - cy
            local[k] = (cx + u * c - v * s_, cy + v * c + u * s_)

    return {k: (x + f * u, y + v) for k, (u, v) in local.items()}


def angle_of(a, b, facing):
    """Absolute angle of the vector a->b in the facing frame."""
    return math.degrees(math.atan2((b[0] - a[0]) * facing, b[1] - a[1]))


def points_to_pose(P, facing):
    """Inverse of fk (with spin = 0): recover joint angles from positions."""
    ang = lambda a, b: angle_of(P[a], P[b], facing)
    torso = ang("hip", "neck")
    lean = wrap(180.0 - torso)
    pose = {"lean": lean, "head": wrap(torso - ang("neck", "head"))}
    for s in "lr":
        ua = ang("neck", s + "_elbow")
        pose[s + "_arm"] = wrap(ua + lean)
        pose[s + "_elbow"] = wrap(ang(s + "_elbow", s + "_hand") - ua)
        th = ang("hip", s + "_knee")
        pose[s + "_leg"] = wrap(th)
        pose[s + "_knee"] = wrap(ang(s + "_knee", s + "_foot") - th)
    return pose


def two_bone_ik(root, target, l1, l2, facing, bend=1):
    """Solve a two-bone chain. Returns (absolute angle of bone 1, relative angle of bone 2).

    bend=+1 puts the middle joint forward (knees), bend=-1 puts it back/down (elbows).
    """
    dx, dy = (target[0] - root[0]) * facing, target[1] - root[1]
    dist = min(max(math.hypot(dx, dy), abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3)
    at = math.degrees(math.atan2(dx, dy))
    alpha = math.degrees(math.acos((l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)))
    beta = math.degrees(math.acos((l1 * l1 + l2 * l2 - dist * dist) / (2 * l1 * l2)))
    return at + bend * alpha, -bend * (180.0 - beta)


def leg_ik(pose, hip, foot, side, facing, size):
    a1, rel = two_bone_ik(hip, foot, THIGH * size, SHIN * size, facing, bend=1)
    pose[side + "_leg"], pose[side + "_knee"] = a1, rel


def arm_ik(pose, neck, hand, side, facing, size, bend=-1):
    a1, rel = two_bone_ik(neck, hand, UPPER_ARM * size, FOREARM * size, facing, bend=bend)
    pose[side + "_arm"], pose[side + "_elbow"] = a1 + pose["lean"], rel


def lowest(P, size, width):
    """Lowest y of the drawn figure (head is a disc, limbs have stroke width)."""
    y = P["head"][1] + HEAD_R * size
    for k, (px, py) in P.items():
        if k != "head":
            y = max(y, py + width / 2)
    return y
