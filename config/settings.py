# =============================================================================
# settings.py — Project ke saare settings/constants ek jagah
# =============================================================================
# Koi bhi value change karni ho toh sirf yahan aao.
# Baaki poore project mein yahi settings import hoti hain.
# =============================================================================


# ─────────────────────────────────────────────────────────────────────────────
# CAMERA SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

CAMERA_INDEX = 0        # 0 = default webcam, 1 = external camera
FRAME_WIDTH  = 1280     # Webcam frame width (pixels)
FRAME_HEIGHT = 720      # Webcam frame height (pixels)


# ─────────────────────────────────────────────────────────────────────────────
# HAND DETECTION SETTINGS (MediaPipe)
# ─────────────────────────────────────────────────────────────────────────────

MAX_HANDS            = 1    # Ek waqt mein kitne haath detect karne hain
DETECTION_CONFIDENCE = 0.8  # Hand detection ki accuracy (0.0 to 1.0)
TRACKING_CONFIDENCE  = 0.8  # Hand tracking ki accuracy (0.0 to 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# MODE SWITCHING SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

# "Thumbs Up" gesture ko kitne seconds hold karna hai mode switch ke liye
MODE_SWITCH_HOLD_SECONDS = 2.0

# "Mode Selection" screen mein koi mode select karne ke liye kitne seconds hold
MODE_SELECT_HOLD_SECONDS = 1.5


# ─────────────────────────────────────────────────────────────────────────────
# AVAILABLE MODES
# ─────────────────────────────────────────────────────────────────────────────
# Key = mode number (finger count se select hoga)
# Value = mode ka naam

MODES = {
    0: "No Mode",          # Koi mode active nahi
    1: "Virtual Mouse",
    2: "Volume Control",
    3: "Brightness Control",
    4: "Scroll Mode",
    5: "Gaming Mode",
}

# Abhi sirf gaming mode build hua hai, baaki baad mein add honge
ACTIVE_MODES = [0, 5]   # Yeh modes actually kaam karte hain


# ─────────────────────────────────────────────────────────────────────────────
# GAMING MODE SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

# Gesture → Action mapping
# Tuple mein order hai: (thumb, index, middle, ring, pinky)
# 1 = finger up, 0 = finger down

GAMING_GESTURES = {
    (0, 0, 0, 0, 0): "idle",        # Mutthi band = koi action nahi
    (0, 1, 0, 0, 0): "forward",     # Sirf index = W (aage chalo)
    (0, 1, 1, 0, 0): "backward",    # Index + Middle = S (peechhe)
    (0, 1, 1, 1, 0): "move_left",   # 3 ungli = A (left)
    (0, 1, 1, 1, 1): "move_right",  # 4 ungli = D (right)
    (1, 1, 1, 1, 1): "jump",        # Khula haath = Space (jump)
    (1, 0, 0, 0, 0): "action",      # Sirf thumb = F (interact)
    (1, 0, 0, 0, 1): "reload",      # Thumb + Pinky = R (reload)
    (0, 0, 0, 0, 1): "crouch",      # Sirf pinky = C (crouch)
}

# Action → Keyboard key mapping
GAMING_ACTION_KEYS = {
    "idle":       None,     # Koi key press nahi
    "forward":    "w",
    "backward":   "s",
    "move_left":  "a",
    "move_right": "d",
    "jump":       "space",  # Space bar
    "action":     "f",
    "reload":     "r",
    "crouch":     "c",
}

# Gaming mode mein gesture kitni frames stable rahni chahiye action ke liye
# (prevents accidental key presses from shaky hands)
GAMING_STABILITY_FRAMES = 3


# ─────────────────────────────────────────────────────────────────────────────
# COLORS — OpenCV BGR format mein hote hain (Blue, Green, Red)
# ─────────────────────────────────────────────────────────────────────────────

COLOR_GREEN  = (0,   255, 0)
COLOR_RED    = (0,   0,   255)
COLOR_BLUE   = (255, 0,   0)
COLOR_WHITE  = (255, 255, 255)
COLOR_BLACK  = (0,   0,   0)
COLOR_YELLOW = (0,   255, 255)
COLOR_CYAN   = (255, 255, 0)
COLOR_ORANGE = (0,   165, 255)
COLOR_PURPLE = (255, 0,   255)

# HUD overlay ka background color (thodi transparent effect ke liye)
HUD_BG_COLOR = (20, 20, 20)
