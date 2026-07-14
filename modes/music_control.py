# =============================================================================
# modes/music_control.py — Gesture se music/media player control karna
# =============================================================================
#
# Yeh mode haath ki ungliyon ki ginti se media keys simulate karta hai.
# Koi bhi media player kaam karta hai — Spotify, YouTube, VLC, Windows Media, etc.
#
# ── GESTURE → ACTION MAPPING ─────────────────────────────────────────────────
#
#   Gesture              Fingers Up          Key           Action
#   ──────────────────── ─────────────────── ───────────── ─────────────────
#   Fist                [0, 0, 0, 0, 0]     (none)        Idle
#   Index only          [0, 1, 0, 0, 0]     Play/Pause    Toggle play
#   Index + Middle      [0, 1, 1, 0, 0]     Next Track    Agla gaana
#   3 Fingers           [0, 1, 1, 1, 0]     Prev Track    Pichla gaana
#   Open Palm           [1, 1, 1, 1, 1]     Volume Up     Awaaz badhao
#   Thumb only          [1, 0, 0, 0, 0]     Volume Down   Awaaz ghataao
#   Thumb + Index       [1, 1, 0, 0, 0]     Mute          Mute toggle
#   Pinky only          [0, 0, 0, 0, 1]     Stop          Band karo
#
# ── KEY BEHAVIOR ─────────────────────────────────────────────────────────────
#   Music mode mein keys "tap" hoti hain (hold nahi) — ek baar press aur release.
#   Ek gesture ek baar action perform karta hai.
#   Dobara action ke liye: pehle fist karo, phir gesture show karo.
#   (Isse accidental repeated skipping nahi hogi)
#
# =============================================================================

import cv2
import time

from pynput.keyboard import Controller, Key

from config.settings import (
    COLOR_GREEN, COLOR_RED, COLOR_WHITE, COLOR_BLACK,
    COLOR_YELLOW, COLOR_CYAN, COLOR_ORANGE, COLOR_PURPLE,
)
from utils.finger_utils import fingers_as_tuple, count_fingers, is_fist


# ── Music Mode ke gesture → action mapping ────────────────────────────────────
# Gaming mode ki tarah, tuple = (thumb, index, middle, ring, pinky)

MUSIC_GESTURES = {
    (0, 0, 0, 0, 0): "idle",           # Fist = koi action nahi
    (0, 1, 0, 0, 0): "play_pause",     # Index = Play / Pause
    (0, 1, 1, 0, 0): "next_track",     # Index + Middle = Next song
    (0, 1, 1, 1, 0): "prev_track",     # 3 fingers = Previous song
    (1, 1, 1, 1, 1): "volume_up",      # Open palm = Volume UP
    (1, 0, 0, 0, 0): "volume_down",    # Thumb only = Volume DOWN
    (1, 1, 0, 0, 0): "mute",           # Thumb + Index = Mute
    (0, 0, 0, 0, 1): "stop",           # Pinky only = Stop
}

# ── Do types ke actions ───────────────────────────────────────────────────────
#
# CONTINUOUS: Jab tak gesture hold hai tab tak baar baar key press hoti hai
#             → Volume ke liye perfect (hold karo = volume barhta rahe)
#
# SINGLE SHOT: Sirf ek baar fire hoti hai, phir fist karke reset karo
#             → Play/Pause, Next/Prev ke liye perfect (accidental repeat se bacho)

CONTINUOUS_ACTIONS  = {"volume_up", "volume_down"}   # Hold = repeat

SINGLE_SHOT_ACTIONS = {"play_pause", "next_track",   # Once = done
                        "prev_track", "mute", "stop"}

# Action → Keyboard key mapping
#
# next_track / prev_track = YouTube shortcuts (Shift+N / Shift+P)
# Yeh media keys se zyada useful hain YouTube ke saath
# (Media keys sirf Spotify/VLC/WMP mein kaam karte hain)

MUSIC_ACTION_KEYS = {
    "idle":         None,
    "play_pause":   Key.media_play_pause,   # Universal media play/pause (works everywhere)
    "next_track":   (Key.shift, 'n'),        # Shift+N = YouTube next video in playlist
    "prev_track":   (Key.shift, 'p'),        # Shift+P = YouTube previous video in playlist
    "volume_up":    Key.media_volume_up,     # System volume up
    "volume_down":  Key.media_volume_down,   # System volume down
    "mute":         Key.media_volume_mute,   # System mute
    "stop":         Key.media_stop,          # Stop (VLC/WMP)
}

# Action ke display name (screen par dikhane ke liye)
ACTION_DISPLAY = {
    "idle":         "⏸  Idle",
    "play_pause":   "⏯  Play / Pause",
    "next_track":   "⏭  Next Track",
    "prev_track":   "⏮  Previous Track",
    "volume_up":    "🔊  Volume Up",
    "volume_down":  "🔉  Volume Down",
    "mute":         "🔇  Mute",
    "stop":         "⏹  Stop",
}


class MusicControlMode:
    """
    Gesture se music/media player control karne wala mode.

    Gaming mode se yeh alag hai:
    - Keys "tap" hoti hain (press + immediately release)
    - Ek gesture ek baar hi action karta hai
    - Dobara fist karo → phir gesture karo → next action
    """

    # Kitne seconds mein ek baar volume key repeat hogi (continuous actions ke liye)
    # 0.15 sec = roughly 6-7 volume steps per second while holding gesture
    VOLUME_REPEAT_INTERVAL = 0.15

    # Single-shot actions ke beech kitna gap chahiye (accidental double press se bacho)
    SINGLE_SHOT_COOLDOWN   = 0.8

    def __init__(self):
        # pynput keyboard controller
        self.keyboard = Controller()

        # Last action ka naam (screen display ke liye)
        self.last_action      = "idle"
        self.last_action_time = 0

        # ── Stability system ──────────────────────────────────────────────────
        # Thodi si haath ki kaamp se gesture change nahi hona chahiye
        # stable_frames = 2: 2 frames tak same gesture aaye toh confirm karo
        # (Zyada rakhne se lag feel hoti hai, kam rakhne se accidental actions)
        self.stable_frames   = 2
        self.candidate       = "idle"
        self.candidate_count = 0

        # ── Single-shot reset system ──────────────────────────────────────────
        # Play/Pause jaise actions ke liye: ek baar fire, phir fist se reset
        self.waiting_for_reset = False

        # ── Continuous action tracking ────────────────────────────────────────
        # Volume ke liye: jab tak gesture stable hai, baar baar press karo
        self.continuous_last_press = 0   # Aakhri baar volume key kab press hui

        print("Music Control Mode started!")

    # ─────────────────────────────────────────────────────────────────────────
    def run(self, frame, fingers_up, landmark_list, hand_present=True):
        """
        Har frame par call hota hai.

        Logic flow:
          1. Gesture identify karo
          2. Stability check karo (jittery haath se bachne ke liye)
          3. Action type check karo:
               - Continuous (volume) → jab tak held, repeat karo
               - Single-shot (play/pause) → ek baar fire, fist se reset
          4. HUD draw karo

        hand_present=False hone par sirf HUD draw hota hai, koi action nahi.
        """

        # Haath nahi hai — sirf HUD draw karo, koi action nahi
        if not hand_present:
            frame = self._draw_hud(frame, [0, 0, 0, 0, 0])
            return frame

        # ── Step 1: Gesture identify karo ─────────────────────────────────────
        finger_tuple     = fingers_as_tuple(fingers_up)
        detected_gesture = MUSIC_GESTURES.get(finger_tuple, "idle")

        # ── Step 2: Stability check ────────────────────────────────────────────
        # Agar same gesture aa raha hai → count badhao
        # Agar alag gesture → counter reset karo
        if detected_gesture == self.candidate:
            self.candidate_count += 1
        else:
            self.candidate       = detected_gesture
            self.candidate_count = 1

        gesture_stable = self.candidate_count >= self.stable_frames
        not_idle       = detected_gesture != "idle"
        now            = time.time()

        # ── Step 3a: CONTINUOUS actions (volume up / volume down) ─────────────
        # Jab tak haath same position mein hai → volume badhta / ghatta rahe
        if gesture_stable and detected_gesture in CONTINUOUS_ACTIONS:
            if now - self.continuous_last_press >= self.VOLUME_REPEAT_INTERVAL:
                self._tap_key(detected_gesture)
                self.last_action           = detected_gesture
                self.continuous_last_press = now
                # IMPORTANT: last_action_time update NAHI karte
                # Warna volume ke baad mute ka cooldown block ho jaata hai

        # ── Step 3b: SINGLE-SHOT actions (play/pause, next, prev, mute, stop) ──
        elif self.waiting_for_reset:
            # Pichla single-shot action hua tha — fist dikhne ka wait
            if is_fist(fingers_up):
                self.waiting_for_reset = False
                self.candidate         = "idle"
                self.candidate_count   = 0

        elif gesture_stable and not_idle and detected_gesture in SINGLE_SHOT_ACTIONS:
            if now - self.last_action_time >= self.SINGLE_SHOT_COOLDOWN:
                self._tap_key(detected_gesture)
                self.last_action       = detected_gesture
                self.last_action_time  = now
                self.waiting_for_reset = True   # Fist se reset karo

        # ── Step 4: HUD draw karo ─────────────────────────────────────────────
        show_reset_msg = (self.waiting_for_reset
                          and detected_gesture not in CONTINUOUS_ACTIONS)
        status_msg = "Fist karo next action ke liye..." if show_reset_msg else None
        frame = self._draw_hud(frame, fingers_up, status_msg)

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    def _focus_browser(self):
        """
        Browser window ko foreground mein laata hai.

        Kyun zaroori hai:
            Shift+N / Shift+P jaise combo keys focused window pe jaate hain.
            Agar OpenCV window focused hai toh key YouTube tak nahi pahunchti.
            Isliye pehle browser focus karo, phir key bhejo.

        Supported browsers: Chrome, Firefox, Edge, Brave, Opera, Arc
        """
        try:
            import pygetwindow as gw

            # Pehle YouTube specifically dhundho, phir generic browsers
            search_keywords = [
                'YouTube',           # YouTube tab open hai
                'Chrome',            # Google Chrome
                'Firefox',           # Mozilla Firefox
                'Edge',              # Microsoft Edge
                'Brave',             # Brave Browser
                'Opera',             # Opera
            ]

            for keyword in search_keywords:
                windows = gw.getWindowsWithTitle(keyword)
                if windows:
                    windows[0].activate()       # Browser ko foreground mein laao
                    time.sleep(0.12)            # Focus settle hone ka thoda wait
                    return True

        except Exception as e:
            print(f"Browser focus error: {e}")

        return False   # Browser nahi mila

    # ─────────────────────────────────────────────────────────────────────────
    def _tap_key(self, gesture_name):
        """
        Ek key ya key combination press aur release karta hai.

        Do types handle karta hai:
          1. Single key   → press + release
             Example: Key.media_play_pause  (system-wide, focus ki zaroorat nahi)

          2. Key combo    → browser focus karo, phir modifier + key bhejo
             Example: (Key.shift, 'n') = Shift+N  (YouTube shortcut)
        """

        key = MUSIC_ACTION_KEYS.get(gesture_name)

        if key is None:
            return

        # ── Combo key (tuple) — jaise (Key.shift, 'n') ───────────────────────
        # Combo keys browser-specific hote hain (Shift+N = YouTube next)
        # Isliye pehle browser window ko focus karo
        if isinstance(key, tuple):
            self._focus_browser()            # Browser ko foreground mein laao
            modifier, main_key = key
            self.keyboard.press(modifier)    # Shift daba ke rakho
            self.keyboard.press(main_key)    # N press karo
            self.keyboard.release(main_key)  # N release karo
            self.keyboard.release(modifier)  # Shift chhor do

        # ── Single key — jaise Key.media_play_pause ──────────────────────────
        # Media keys system-wide hoti hain — focused window matter nahi karta
        else:
            self.keyboard.press(key)
            self.keyboard.release(key)

        display = ACTION_DISPLAY.get(gesture_name, gesture_name)
        print(f"Music Action: {display}")

    # ─────────────────────────────────────────────────────────────────────────
    def _draw_hud(self, frame, fingers_up, status_msg=None):
        """
        Screen par Music Control Mode ka HUD draw karta hai.

        Dikhata hai:
        - Mode naam
        - Last performed action
        - Gesture guide (cheat sheet)
        - Finger state visualizer
        - Status message (agar ho)
        """

        h, w, _ = frame.shape

        # ── Top-left: Mode naam ───────────────────────────────────────────────
        cv2.rectangle(frame, (0, 0), (350, 50), COLOR_BLACK, cv2.FILLED)
        cv2.putText(
            frame, "MODE: MUSIC CONTROL",
            (10, 35),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9,
            COLOR_PURPLE, 2,
        )

        # ── Last action display ───────────────────────────────────────────────
        action_display = ACTION_DISPLAY.get(self.last_action, self.last_action)
        cv2.rectangle(frame, (0, 55), (420, 140), (20, 20, 20), cv2.FILLED)
        cv2.putText(
            frame, "Last Action:",
            (10, 80),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65,
            COLOR_WHITE, 1,
        )
        cv2.putText(
            frame, action_display,
            (10, 125),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0,
            COLOR_YELLOW, 2,
        )

        # ── Status message (jab reset chahiye) ───────────────────────────────
        if status_msg:
            cv2.rectangle(frame, (0, 145), (380, 185), (40, 10, 10), cv2.FILLED)
            cv2.putText(
                frame, status_msg,
                (10, 172),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                COLOR_RED, 2,
            )

        # ── Bottom-right: Gesture Cheat Sheet ────────────────────────────────
        cheat_sheet = [
            ("Index",            "Play / Pause"),
            ("Index + Middle",   "Next Track"),
            ("3 Fingers",        "Previous Track"),
            ("Open Palm (5)",    "Volume Up"),
            ("Thumb Only",       "Volume Down"),
            ("Thumb + Index",    "Mute"),
            ("Pinky Only",       "Stop"),
            ("Fist",             "Reset / Idle"),
        ]

        sheet_x = w - 360
        sheet_y = h - (len(cheat_sheet) * 28 + 40)

        cv2.rectangle(frame, (sheet_x - 10, sheet_y - 28), (w - 5, h - 5), (20, 20, 20), cv2.FILLED)
        cv2.putText(
            frame, "MUSIC GESTURE GUIDE",
            (sheet_x, sheet_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
            COLOR_CYAN, 2,
        )

        for i, (gesture, action) in enumerate(cheat_sheet):
            cv2.putText(
                frame, f"{gesture:<22} {action}",
                (sheet_x, sheet_y + 22 + i * 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                COLOR_WHITE, 1,
            )

        # ── Finger state visualizer (bottom-left) ────────────────────────────
        finger_names = ["T", "I", "M", "R", "P"]
        box_x = 10
        box_y = h - 60

        for i, (name, state) in enumerate(zip(finger_names, fingers_up)):
            x      = box_x + i * 50
            color  = COLOR_GREEN if state == 1 else COLOR_RED
            cv2.rectangle(frame, (x, box_y), (x + 40, box_y + 40), color, cv2.FILLED)
            cv2.putText(
                frame, name,
                (x + 12, box_y + 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                COLOR_BLACK, 2,
            )

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    def stop(self):
        """
        Mode band karna.
        Music mode mein koi key hold nahi hoti, isliye sirf message print karo.
        """
        print("🎵 Music Control Mode stopped.")
