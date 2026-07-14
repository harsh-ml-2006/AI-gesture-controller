# =============================================================================
# utils/distance.py — Do points ke beech ki doori calculate karta hai
# =============================================================================
# Yeh simple math hai:
#   Agar point A = (x1, y1) aur point B = (x2, y2) ho toh
#   Distance = sqrt( (x2-x1)^2 + (y2-y1)^2 )   ← Pythagoras theorem
# =============================================================================

import math


def get_distance(x1, y1, x2, y2):
    """
    Do pixel coordinates ke beech Euclidean distance nikalta hai.

    Parameters:
        x1, y1 : Pehle point ki x aur y position
        x2, y2 : Doosre point ki x aur y position

    Returns:
        float : Dono points ke beech ki doori (pixels mein)
    """

    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance


def get_midpoint(x1, y1, x2, y2):
    """
    Do points ka beech wala point (midpoint) nikalta hai.

    Returns:
        tuple : (mx, my) — midpoint ke pixel coordinates
    """

    mx = (x1 + x2) // 2   # // means integer division (decimal nahi chahiye)
    my = (y1 + y2) // 2

    return mx, my
