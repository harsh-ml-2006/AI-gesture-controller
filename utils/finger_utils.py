# =============================================================================
# utils/finger_utils.py — Finger state se related helper functions
# =============================================================================
# Yeh file fingers_up list ko easy-to-use form mein convert karne mein help karti hai.
# fingers_up list ka order: [thumb, index, middle, ring, pinky]
#   1 = finger upar (up)
#   0 = finger neeche (down/bent)
# =============================================================================


def count_fingers(fingers_up):
    """
    Kitni ungliyan upar hain yeh count karta hai.

    Parameters:
        fingers_up : list of 5 values — [thumb, index, middle, ring, pinky]

    Returns:
        int : 0 se 5 ke beech finger count
    """
    return sum(fingers_up)   # sum() list ke saare values add karta hai


def fingers_as_tuple(fingers_up):
    """
    fingers_up list ko tuple mein convert karta hai.
    Tuple ko dictionary key ke taur par use kar sakte hain (list nahi hoti key).

    Example:
        [1, 0, 1, 0, 0]  →  (1, 0, 1, 0, 0)
    """
    return tuple(fingers_up)


def is_fist(fingers_up):
    """
    Kya haath mutthi ki tarah band hai?
    Matlab saari ungliyan neeche hain.
    """
    return all(f == 0 for f in fingers_up)


def is_open_palm(fingers_up):
    """
    Kya haath khula hua hai (saari ungliyan upar)?
    """
    return all(f == 1 for f in fingers_up)


def is_thumbs_up(fingers_up):
    """
    Kya sirf thumb upar hai baaki sab neeche?
    Yeh gesture mode switching ke liye use hoti hai.
    """
    thumb, index, middle, ring, pinky = fingers_up
    return thumb == 1 and index == 0 and middle == 0 and ring == 0 and pinky == 0


def is_peace_sign(fingers_up):
    """
    Kya index aur middle upar hain, baaki neeche? (Peace ✌️ sign)
    """
    thumb, index, middle, ring, pinky = fingers_up
    return index == 1 and middle == 1 and thumb == 0 and ring == 0 and pinky == 0


def get_gesture_name(fingers_up):
    """
    fingers_up list dekh kar ek readable gesture naam return karta hai.
    Debugging aur screen display ke liye useful hai.
    """

    finger_count = count_fingers(fingers_up)

    if is_fist(fingers_up):
        return "Fist"
    elif is_open_palm(fingers_up):
        return "Open Palm"
    elif is_thumbs_up(fingers_up):
        return "Thumbs Up"
    elif is_peace_sign(fingers_up):
        return "Peace Sign"
    else:
        return f"{finger_count} Finger(s)"
