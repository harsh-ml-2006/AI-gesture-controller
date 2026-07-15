import math

def get_distance(x1, y1, x2, y2):
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance

def get_midpoint(x1, y1, x2, y2):
    mx = (x1 + x2) // 2
    my = (y1 + y2) // 2
    return (mx, my)