def count_fingers(fingers_up):
    return sum(fingers_up)

def fingers_as_tuple(fingers_up):
    return tuple(fingers_up)

def is_fist(fingers_up):
    return all((f == 0 for f in fingers_up))

def is_open_palm(fingers_up):
    return all((f == 1 for f in fingers_up))

def is_thumbs_up(fingers_up):
    (thumb, index, middle, ring, pinky) = fingers_up
    return thumb == 1 and index == 0 and (middle == 0) and (ring == 0) and (pinky == 0)

def is_peace_sign(fingers_up):
    (thumb, index, middle, ring, pinky) = fingers_up
    return index == 1 and middle == 1 and (thumb == 0) and (ring == 0) and (pinky == 0)

def get_gesture_name(fingers_up):
    finger_count = count_fingers(fingers_up)
    if is_fist(fingers_up):
        return 'Fist'
    elif is_open_palm(fingers_up):
        return 'Open Palm'
    elif is_thumbs_up(fingers_up):
        return 'Thumbs Up'
    elif is_peace_sign(fingers_up):
        return 'Peace Sign'
    else:
        return f'{finger_count} Finger(s)'