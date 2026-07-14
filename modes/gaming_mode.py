# =============================================================================
# modes/gaming_mode.py — Gesture se keyboard keys control karne wala mode
# =============================================================================
#
# Yeh mode haath ke gestures ko game ke keyboard controls mein convert karta hai.
#
# ── GESTURE → KEY MAPPING ────────────────────────────────────────────────────
#
#   Gesture                     Fingers Up          Key      Action
#   ─────────────────────────── ──────────────────── ──────── ──────────────
#   Mutthi (Fist)              [0, 0, 0, 0, 0]      (none)   Idle / Stop
#   Sirf Index                 [0, 1, 0, 0, 0]      W        Move Forward
#   Index + Middle             [0, 1, 1, 0, 0]      S        Move Backward
#   Index + Middle + Ring      [0, 1, 1, 1, 0]      A        Move Left
#   Index + Middle + Ring + P  [0, 1, 1, 1, 1]      D        Move Right
#   Khula Haath (Open Palm)    [1, 1, 1, 1, 1]      Space    Jump
#   Sirf Thumb                 [1, 0, 0, 0, 0]      F        Action/Interact
#   Thumb + Pinky (Shaka 🤙)   [1, 0, 0, 0, 1]      R        Reload
#   Sirf Pinky                 [0, 0, 0, 0, 1]      C        Crouch
#
# ── KEY BEHAVIOR ─────────────────────────────────────────────────────────────
#   Keys "hold" hoti hain jab tak gesture stable rahta hai.
#   Gesture change hone par purani key release hoti hai, nayi press hoti hai.
#   Isse W key hold karke chalte rehna possible hai.
#
# =============================================================================

import cv2
import time

from pynput.keyboard import Controller, Key

from config.settings import (
    GAMING_GESTURES,
    GAMING_ACTION_KEYS,
    GAMING_STABILITY_FRAMES,
    COLOR_GREEN, COLOR_RED, COLOR_WHITE, COLOR_BLACK,
    COLOR_YELLOW, COLOR_ORANGE, COLOR_CYAN,
)
from utils.finger_utils import fingers_as_tuple, get_gesture_name


class GamingMode:
    """
    Gesture-based gaming keyboard controller.

    Har frame mein:
    1. fingers_up list se gesture identify karo
    2. Gesture ko action name mein convert karo
    3. Action ko keyboard key mein convert karo
    4. Key ko hold/release karo
    5. Screen par HUD show karo
    """

    def __init__(self):
        """
        Gaming mode setup karta hai.
        pynput keyboard controller initialize karta hai.
        """

        # pynput ka keyboard controller — yeh keys press/release kar sakta hai
        self.keyboard = Controller()

        # Abhi kaunsi key pressed hai (hold mein)
        # Set use kar rahe hain kyunki ek waqt mein multiple keys ho sakti hain
        self.pressed_keys = set()

        # ── Stability system ─────────────────────────────────────────────────
        # Problem: Haath kaampne se gesture rapidly change ho sakta hai
        # Solution: Ek gesture ko STABILITY_FRAMES frames tak stable rakhna
        #           zaroori hai phir hi key press hogi
        self.stability_frames  = GAMING_STABILITY_FRAMES
        self.current_gesture   = "idle"   # Abhi active gesture
        self.candidate_gesture = "idle"   # Yeh gesture stable ho raha hai
        self.stable_count      = 0        # Kitne frames se stable hai

        # Mode active hai ya nahi (cleanup ke liye)
        self.is_active = True

        print("🎮 Gaming Mode started!")
        print("   Hold 'Thumbs Up' gesture for 2 seconds to switch mode.")

    # ─────────────────────────────────────────────────────────────────────────
    def run(self, frame, fingers_up, landmark_list, hand_present=True):
        """
        Har frame par call hota hai. Main logic yahan hai.

        Parameters:
            frame        : Current webcam frame (numpy array)
            fingers_up   : [thumb, index, middle, ring, pinky]
            landmark_list: 21 landmarks
            hand_present : bool — False hone par sirf HUD draw hoga, keys nahi

        Returns:
            frame : HUD overlay ke saath updated frame
        """

        # Haath nahi hai — sirf HUD draw karo, koi key press mat karo
        if not hand_present:
            frame = self._draw_hud(frame, [0, 0, 0, 0, 0])
            return frame

        # ── Step 1: Gesture identify karo ────────────────────────────────────
        # fingers_up ko tuple banao taaki dictionary mein search kar sakein
        finger_tuple = fingers_as_tuple(fingers_up)

        # settings.py ke GAMING_GESTURES dict mein dhundho
        # Agar gesture nahi mila toh "idle" use karo (koi bhi key press nahi)
        detected_gesture = GAMING_GESTURES.get(finger_tuple, "idle")

        # ── Step 2: Stability check ───────────────────────────────────────────
        # Agar same gesture aa raha hai lagatar → stable_count badhao
        # Agar alag gesture aaya → reset karo aur naya candidate set karo
        if detected_gesture == self.candidate_gesture:
            self.stable_count += 1
        else:
            self.candidate_gesture = detected_gesture
            self.stable_count      = 1   # Reset counter

        # Sirf tab action lo jab gesture stable ho
        if self.stable_count >= self.stability_frames:
            # Gesture confirm hua! Action execute karo
            if detected_gesture != self.current_gesture:
                self._change_action(detected_gesture)

        # ── Step 3: Screen par HUD draw karo ─────────────────────────────────
        frame = self._draw_hud(frame, fingers_up)

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    def _change_action(self, new_gesture):
        """
        Purani key release karo aur nai key press karo.

        Parameters:
            new_gesture : str — Naya gesture naam (GAMING_GESTURES ke values)
        """

        # Pehle saari pressed keys release karo
        self._release_all_keys()

        # Naya gesture set karo
        self.current_gesture = new_gesture

        # Gesture se key nikalo
        key = GAMING_ACTION_KEYS.get(new_gesture)

        if key is not None:
            self._press_key(key)
            print(f"🎮 Gesture: {new_gesture:15} → Key: [{key}] PRESSED")
        else:
            print(f"🎮 Gesture: {new_gesture:15} → Idle (no key)")

    # ─────────────────────────────────────────────────────────────────────────
    def _press_key(self, key):
        """
        Ek key ko hold karta hai (press karke chhodta nahi).

        Parameters:
            key : str ya pynput.Key — Konsi key press karni hai
                  Example: 'w', 'space', Key.space
        """

        # 'space' string ko actual Key.space mein convert karo
        actual_key = self._resolve_key(key)

        # Agar already pressed hai toh dobara mat press karo
        if actual_key not in self.pressed_keys:
            self.keyboard.press(actual_key)
            self.pressed_keys.add(actual_key)

    # ─────────────────────────────────────────────────────────────────────────
    def _release_all_keys(self):
        """
        Jo bhi keys abhi pressed hain unhe release karo.
        Yeh tab call hota hai jab gesture change hota hai.
        """

        for key in list(self.pressed_keys):   # list() isliye kyunki set modify ho rahi hai loop mein
            actual_key = self._resolve_key(key)
            self.keyboard.release(actual_key)

        self.pressed_keys.clear()   # Set khali karo

    # ─────────────────────────────────────────────────────────────────────────
    def _resolve_key(self, key):
        """
        String key name ko pynput Key object mein convert karta hai.

        Examples:
            'space' → Key.space
            'ctrl'  → Key.ctrl
            'w'     → 'w' (already correct)
        """

        # Special keys jo string se convert honi chahiye
        special_keys = {
            "space":  Key.space,
            "ctrl":   Key.ctrl,
            "shift":  Key.shift,
            "alt":    Key.alt,
            "enter":  Key.enter,
            "esc":    Key.esc,
            "tab":    Key.tab,
            "up":     Key.up,
            "down":   Key.down,
            "left":   Key.left,
            "right":  Key.right,
        }

        # Agar special key hai toh convert karo, warna as-is return karo
        return special_keys.get(key, key)

    # ─────────────────────────────────────────────────────────────────────────
    def _draw_hud(self, frame, fingers_up):
        """
        Screen par gaming mode ka HUD (Heads-Up Display) draw karta hai.
        HUD mein dikhta hai:
        - Current gesture naam
        - Kaunsi key press ho rahi hai
        - Gesture cheat sheet (reference ke liye)

        Parameters:
            frame      : Current frame
            fingers_up : Current finger states

        Returns:
            frame : HUD ke saath updated frame
        """

        h, w, _ = frame.shape

        # ── Top-left: Mode naam ───────────────────────────────────────────────
        cv2.rectangle(frame, (0, 0), (320, 50), COLOR_BLACK, cv2.FILLED)
        cv2.putText(
            frame, "MODE: GAMING",
            (10, 35),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0,
            COLOR_GREEN, 2,
        )

        # ── Current gesture aur key ───────────────────────────────────────────
        gesture_name = get_gesture_name(fingers_up)
        active_key   = GAMING_ACTION_KEYS.get(self.current_gesture, "none")
        key_display  = str(active_key).upper() if active_key else "IDLE"

        cv2.rectangle(frame, (0, 55), (400, 145), (20, 20, 20), cv2.FILLED)
        cv2.putText(
            frame, f"Gesture: {gesture_name}",
            (10, 85),
            cv2.FONT_HERSHEY_SIMPLEX, 0.75,
            COLOR_WHITE, 2,
        )
        cv2.putText(
            frame, f"Key: [ {key_display} ]",
            (10, 130),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0,
            COLOR_YELLOW if active_key else COLOR_WHITE, 2,
        )

        # ── Bottom-right: Cheat Sheet (gesture guide) ─────────────────────────
        cheat_sheet = [
            ("Index",              "W  - Forward"),
            ("Index+Middle",       "S  - Backward"),
            ("3 Fingers",          "A  - Left"),
            ("4 Fingers",          "D  - Right"),
            ("Open Palm",          "Space - Jump"),
            ("Thumb Only",         "F  - Action"),
            ("Thumb+Pinky",        "R  - Reload"),
            ("Pinky Only",         "C  - Crouch"),
            ("Fist",               "Idle"),
        ]

        # Cheat sheet ka background box
        sheet_x  = w - 350
        sheet_y  = h - (len(cheat_sheet) * 28 + 40)
        cv2.rectangle(frame, (sheet_x - 10, sheet_y - 25), (w - 5, h - 5), (20, 20, 20), cv2.FILLED)

        cv2.putText(
            frame, "GESTURE GUIDE",
            (sheet_x, sheet_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
            COLOR_CYAN, 2,
        )

        for i, (gesture, key_action) in enumerate(cheat_sheet):
            # Active gesture ko highlight karo
            color = COLOR_ORANGE if GAMING_ACTION_KEYS.get(self.current_gesture) and key_action.startswith(str(GAMING_ACTION_KEYS.get(self.current_gesture, "")).upper()) else COLOR_WHITE

            cv2.putText(
                frame, f"{gesture:<20} {key_action}",
                (sheet_x, sheet_y + 22 + i * 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                color, 1,
            )

        # ── Finger state visualizer ───────────────────────────────────────────
        finger_names  = ["T", "I", "M", "R", "P"]  # Thumb, Index, Middle, Ring, Pinky
        box_start_x   = 10
        box_start_y   = h - 60

        for i, (name, state) in enumerate(zip(finger_names, fingers_up)):
            x = box_start_x + i * 50
            # State ke hisab se color: green = up, red = down
            color = COLOR_GREEN if state == 1 else COLOR_RED
            cv2.rectangle(frame, (x, box_start_y), (x + 40, box_start_y + 40), color, cv2.FILLED)
            cv2.putText(
                frame, name,
                (x + 12, box_start_y + 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                COLOR_BLACK, 2,
            )

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    def stop(self):
        """
        Gaming mode band karta hai.
        Saari pressed keys release karta hai taaki game mein keys stuck na ho.
        Yeh tab call hota hai jab user koi doosra mode select karta hai.
        """
        self._release_all_keys()
        self.is_active = False
        print("🎮 Gaming Mode stopped. All keys released.")
