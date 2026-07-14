# =============================================================================
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
# =============================================================================
# main.py — AI Gesture Controller ka entry point (yahan se program shuru hota hai)
# =============================================================================
#
# PROGRAM FLOW (Program kaise chalta hai):
#
#   1. Camera kholo
#   2. HandDetector ready karo
#   3. Loop shuru karo:
#       a. Camera se frame lo
#       b. Frame mein haath dhundho
#       c. Fingers up check karo
#       d. Mode switch gesture check karo (Thumbs Up hold)
#       e. Active mode ka run() call karo
#       f. Screen par frame dikhao
#       g. ESC press → loop band
#   4. Camera release karo
#
# ── MODE SWITCHING (Gesture se) ───────────────────────────────────────────────
#
#   "Thumbs Up" 👍 gesture ko 2 seconds hold karo → Mode Selector screen aayegi
#   Jab Mode Selector active ho:
#       - 5 fingers (Open Palm) = Gaming Mode select
#       - 0 fingers (Fist)      = No Mode (sirf hand tracking)
#   Is gesture ko 1.5 seconds hold karo → Mode confirm
#
# ── KEYBOARD SHORTCUTS ────────────────────────────────────────────────────────
#   ESC  = Program band karo
#   'q'  = Program band karo (alternative)
#
# =============================================================================

import cv2
import time

# Hamare modules import karo
from camera.camera_handler   import CameraHandler
from gestures.hand_detector  import HandDetector
from modes.gaming_mode       import GamingMode
from modes.music_control     import MusicControlMode
from utils.finger_utils      import (
    is_thumbs_up,
    is_fist,
    is_open_palm,
    count_fingers,
    get_gesture_name,
)
from config.settings import (
    MODE_SWITCH_HOLD_SECONDS,
    MODE_SELECT_HOLD_SECONDS,
    MODES,
    COLOR_GREEN, COLOR_RED, COLOR_WHITE, COLOR_BLACK,
    COLOR_YELLOW, COLOR_CYAN, COLOR_ORANGE,
)


# =============================================================================
# ModeManager — Mode switching ka logic manage karta hai
# =============================================================================

class ModeManager:
    """
    Yeh class mode switching ka pura logic sambhalta hai.

    States (Avasthayen):
        "normal"    → Koi mode active hai, normally chal raha hai
        "selecting" → Mode selection screen show ho rahi hai
    """

    # Available modes (filhaal sirf gaming mode ready hai)
    # Format: { mode_number: (mode_name, mode_object_ya_None) }

    def __init__(self):

        # Abhi konsa mode active hai
        self.current_mode_id   = 0           # 0 = No Mode
        self.current_mode_name = MODES[0]    # "No Mode"
        self.current_mode_obj  = None        # Active mode ka object

        # Mode selector screen ki state
        self.state = "normal"   # "normal" ya "selecting"

        # Thumbs up gesture kitne seconds se hold hai
        self.thumbs_up_start_time = None

        # Selection screen par konsa mode highlight ho raha hai
        self.selected_mode_id        = 0
        self.selection_confirm_start = None   # Tab se hold kar rahe hain selection ke liye

        # Jab selecting state mein gaye tab ka time
        # Isse pata chalta hai ki thumbs-up cancel gesture allow karna hai ya nahi
        # (Pehle 1.5 sec mein cancel nahi hoga — warna jo gesture trigger kiya wahi cancel kar dega)
        self.selection_entered_time  = None
        self.SELECTION_CANCEL_DELAY  = 1.5    # Seconds — itne baad hi thumbs up cancel karega

        # Saare available mode objects yahan store honge
        # (Jab mode activate hoga tab object banana)
        self._mode_objects = {}

        print(f"Starting in: {self.current_mode_name}")

    # ─────────────────────────────────────────────────────────────────────────
    def update(self, fingers_up, frame):
        """
        Har frame par call hota hai.
        Mode switching logic run karta hai.

        Parameters:
            fingers_up : [thumb, index, middle, ring, pinky]
            frame      : Current frame (HUD draw karne ke liye)

        Returns:
            frame : Updated frame (HUD ke saath)
        """

        if self.state == "normal":
            frame = self._handle_normal_state(fingers_up, frame)

        elif self.state == "selecting":
            frame = self._handle_selecting_state(fingers_up, frame)

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    def _handle_normal_state(self, fingers_up, frame):
        """
        Normal state mein mode switch trigger check karta hai.
        Fist (mutthi) gesture ko 2 seconds hold karo → Mode Selector khulega.

        Fist choose kiya kyunki:
        - Gaming mode mein fist = idle (koi key press nahi)
        - Music mode mein fist = reset (sirf flag clear, koi action nahi)
        - Dono modes se conflict nahi!
        """

        # ── Fist (mutthi) detect karo ─────────────────────────────────────────
        if is_fist(fingers_up):

            if self.thumbs_up_start_time is None:
                # Pehli baar detect hua → timer shuru karo
                self.thumbs_up_start_time = time.time()

            # Kitna time hold ho gaya
            held_for = time.time() - self.thumbs_up_start_time

            # Progress bar dikhao (kitna hold bacha hai)
            frame = self._draw_switch_progress(frame, held_for, MODE_SWITCH_HOLD_SECONDS)

            # Agar enough time hold kiya toh mode selection screen kholo
            if held_for >= MODE_SWITCH_HOLD_SECONDS:
                self.state                = "selecting"
                self.thumbs_up_start_time = None
                self.selected_mode_id     = self.current_mode_id
                self.selection_entered_time = time.time()
                print("Mode Selector opened!")

        else:
            # Fist chhor diya → timer reset
            self.thumbs_up_start_time = None

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    def _handle_selecting_state(self, fingers_up, frame):
        """
        Mode selection screen handle karta hai.

        Gesture → Mode selection:
            Fist (0 fingers)  → Mode 0: No Mode
            5 fingers (Palm)  → Mode 5: Gaming Mode
            1-4 fingers       → Future modes (abhi available nahi)

        Selection ko hold karo → Mode activate hota hai.
        """

        finger_count      = count_fingers(fingers_up)
        detected_mode_id  = finger_count   # Finger count = mode number

        # ── Mode highlight karo ───────────────────────────────────────────────
        if detected_mode_id != self.selected_mode_id:
            # Naya mode gesture show ho raha hai → timer reset
            self.selected_mode_id        = detected_mode_id
            self.selection_confirm_start = None

        # ── Hold timer ───────────────────────────────────────────────────────
        if self.selection_confirm_start is None:
            self.selection_confirm_start = time.time()

        hold_time = time.time() - self.selection_confirm_start

        # ── Mode selection screen draw karo ──────────────────────────────────
        frame = self._draw_mode_selector(frame, self.selected_mode_id, hold_time)

        # ── Mode confirm: hold karo MODE_SELECT_HOLD_SECONDS seconds ─────────
        if hold_time >= MODE_SELECT_HOLD_SECONDS:
            self._activate_mode(self.selected_mode_id)
            self.state = "normal"
            self.selection_confirm_start = None

        # ── Mode selector cancel: Open Palm dikhao → selector band ──────────────
        # Fist se cancel nahi karenge (wahi trigger gesture hai)
        # Open Palm = cancel / dismiss
        time_in_selector = time.time() - (self.selection_entered_time or time.time())
        if is_open_palm(fingers_up) and time_in_selector > self.SELECTION_CANCEL_DELAY:
            self.state = "normal"
            print("Mode selection cancelled.")

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    def _activate_mode(self, mode_id):
        """
        Kisi mode ko activate karta hai.
        Pehle purana mode stop karta hai, phir naya shuru karta hai.
        """

        # Purana mode band karo
        if self.current_mode_obj is not None:
            self.current_mode_obj.stop()
            self.current_mode_obj = None

        self.current_mode_id   = mode_id
        self.current_mode_name = MODES.get(mode_id, "Unknown Mode")

        # Mode ID ke hisab se correct mode object banana
        if mode_id == 5:
            # Gaming Mode
            self.current_mode_obj = GamingMode()
            print("[GAMING] Gaming Mode started!")

        elif mode_id == 4:
            # Music Control Mode
            self.current_mode_obj = MusicControlMode()

        elif mode_id == 0:
            # No Mode
            self.current_mode_obj = None
            print("No Mode selected — hand tracking only.")

        else:
            # Yeh modes abhi build nahi hue
            print(f"Mode '{self.current_mode_name}' abhi available nahi hai. Coming soon!")
            self.current_mode_obj = None

        print(f"Mode changed to: {self.current_mode_name}")

    # ─────────────────────────────────────────────────────────────────────────
    def run_current_mode(self, frame, fingers_up, landmark_list, hand_present=True):
        """
        Jo mode abhi active hai uska run() call karta hai.

        Parameters:
            hand_present : bool
                True  = haath detect hua hai → gesture processing + HUD draw
                False = haath nahi mila    → sirf HUD draw, koi action nahi

        Returns:
            frame : Mode ka HUD add hone ke baad frame
        """

        if self.current_mode_obj is not None:
            frame = self.current_mode_obj.run(
                frame, fingers_up, landmark_list,
                hand_present=hand_present
            )

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    def _draw_switch_progress(self, frame, held_for, total_time):
        """
        Thumbs up hold karte waqt ek progress bar dikhata hai.
        Isse user ko pata chalta hai kitna aur hold karna hai.
        """

        h, w, _ = frame.shape
        progress = min(held_for / total_time, 1.0)   # 0.0 to 1.0

        # Text
        cv2.putText(
            frame, "Hold FIST for Mode Switch...",
            (w // 2 - 210, h - 70),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8,
            COLOR_YELLOW, 2,
        )

        # Progress bar background
        bar_x, bar_y = w // 2 - 200, h - 50
        bar_w, bar_h = 400, 20
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (80, 80, 80), cv2.FILLED)

        # Progress bar fill
        fill_w = int(bar_w * progress)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), COLOR_YELLOW, cv2.FILLED)

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    def _draw_mode_selector(self, frame, selected_mode_id, hold_time):
        """
        Mode selection screen draw karta hai.
        Saare available modes dikhata hai.
        Selected mode highlight hota hai.
        """

        h, w, _ = frame.shape

        # ── Semi-transparent background ───────────────────────────────────────
        overlay = frame.copy()
        cv2.rectangle(overlay, (w // 2 - 250, 50), (w // 2 + 250, h - 50), (10, 10, 10), cv2.FILLED)
        frame = cv2.addWeighted(overlay, 0.75, frame, 0.25, 0)   # Blend: 75% dark, 25% original

        # ── Title ─────────────────────────────────────────────────────────────
        cv2.putText(
            frame, "SELECT MODE",
            (w // 2 - 120, 100),
            cv2.FONT_HERSHEY_SIMPLEX, 1.2,
            COLOR_CYAN, 3,
        )
        cv2.putText(
            frame, "Show fingers = Mode Number | Hold to Confirm",
            (w // 2 - 240, 135),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            COLOR_WHITE, 1,
        )

        # ── Mode list ─────────────────────────────────────────────────────────
        mode_list = [
            (0, "Fist (0 fingers)",      "No Mode"),
            (5, "Open Palm (5 fingers)", "Gaming Mode   [READY]"),
            (4, "4 fingers",             "Music Control [READY]"),
            (1, "1 finger",              "Virtual Mouse  - Coming Soon"),
            (2, "2 fingers",             "Volume Control - Coming Soon"),
            (3, "3 fingers",             "Brightness     - Coming Soon"),
        ]

        start_y = 170
        for i, (mode_id, gesture_hint, mode_name) in enumerate(mode_list):

            y = start_y + i * 65

            # Selected mode = highlight color
            is_selected = (mode_id == selected_mode_id)
            bg_color    = COLOR_GREEN if is_selected else (40, 40, 40)
            text_color  = COLOR_BLACK if is_selected else COLOR_WHITE

            # Mode ka box
            cv2.rectangle(frame, (w // 2 - 240, y - 30), (w // 2 + 240, y + 25), bg_color, cv2.FILLED)

            cv2.putText(
                frame, gesture_hint,
                (w // 2 - 230, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                text_color, 2,
            )
            cv2.putText(
                frame, f"→ {mode_name}",
                (w // 2 - 230, y + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                text_color, 1,
            )

        # ── Confirmation progress bar ──────────────────────────────────────────
        if hold_time > 0:
            progress = min(hold_time / MODE_SELECT_HOLD_SECONDS, 1.0)

            bar_x = w // 2 - 240
            bar_y = h - 120
            bar_w = 480
            bar_h = 20

            cv2.putText(
                frame, "Hold gesture to confirm...",
                (bar_x, bar_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                COLOR_WHITE, 1,
            )
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (80, 80, 80), cv2.FILLED)
            fill_w = int(bar_w * progress)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), COLOR_GREEN, cv2.FILLED)

        return frame


# =============================================================================
# draw_status_bar() — Upar wali status bar draw karta hai (FPS + current mode)
# =============================================================================

def draw_status_bar(frame, fps, mode_name):
    """
    Frame ke upar ek status bar draw karta hai.
    FPS aur current mode naam dikhata hai.
    """
    h, w, _ = frame.shape

    # Status bar ka background
    cv2.rectangle(frame, (0, 0), (w, 45), (15, 15, 15), cv2.FILLED)

    # FPS (left side)
    fps_color = COLOR_GREEN if fps > 20 else COLOR_RED
    cv2.putText(
        frame, f"FPS: {fps}",
        (10, 32),
        cv2.FONT_HERSHEY_SIMPLEX, 0.9,
        fps_color, 2,
    )

    # App naam (center)
    cv2.putText(
        frame, "AI Gesture Controller",
        (w // 2 - 130, 32),
        cv2.FONT_HERSHEY_SIMPLEX, 0.9,
        COLOR_WHITE, 2,
    )

    # Current mode (right side)
    cv2.putText(
        frame, f"Mode: {mode_name}",
        (w - 280, 32),
        cv2.FONT_HERSHEY_SIMPLEX, 0.75,
        COLOR_CYAN, 2,
    )

    return frame


# =============================================================================
# draw_no_hand_message() — Haath nahi mila toh message dikhao
# =============================================================================

def draw_no_hand_message(frame):
    """
    Jab koi haath detect nahi hota tab screen par message dikhata hai.
    """
    h, w, _ = frame.shape
    cv2.putText(
        frame, "No Hand Detected",
        (w // 2 - 150, h // 2),
        cv2.FONT_HERSHEY_SIMPLEX, 1.2,
        (100, 100, 100), 2,
    )
    return frame


# =============================================================================
# MAIN PROGRAM — Yahan se sab kuch shuru hota hai
# =============================================================================

def main():
    print("=" * 55)
    print("   AI Gesture Controller -- Starting...")
    print("=" * 55)
    print("   Press ESC or 'q' to quit")
    print("   Hold FIST (mutthi) for 2 sec --> Mode Selector")
    print("=" * 55)

    # ── Objects banana ────────────────────────────────────────────────────────
    camera       = CameraHandler()        # Webcam handler
    detector     = HandDetector()         # Hand detection
    mode_manager = ModeManager()          # Mode switching manager

    # ── Main Loop ─────────────────────────────────────────────────────────────
    while True:

        # ── Step 1: Camera se frame lo ────────────────────────────────────────
        frame = camera.get_frame()

        if frame is None:
            # Frame nahi aaya → skip karo
            continue

        # ── Step 2: Haath dhundho ─────────────────────────────────────────────
        frame = detector.find_hands(frame)
        landmark_list = detector.get_landmark_list(frame)

        # ── Step 3: Gesture processing (sirf haath milne par) ─────────────────
        if detector.is_hand_detected():
            fingers_up = detector.fingers_up()

            # Mode switching check karo (Fist gesture)
            frame = mode_manager.update(fingers_up, frame)

            # Active mode ka logic + HUD
            frame = mode_manager.run_current_mode(
                frame, fingers_up, landmark_list, hand_present=True
            )

        else:
            # Haath nahi mila — sirf HUD draw karo, koi action nahi
            # fingers_up=[0,0,0,0,0] pass karo taaki HUD draw ho sake
            draw_no_hand_message(frame)
            frame = mode_manager.run_current_mode(
                frame, [0, 0, 0, 0, 0], [], hand_present=False
            )

        # ── Step 4: Status bar draw karo ──────────────────────────────────────
        frame = draw_status_bar(frame, camera.get_fps(), mode_manager.current_mode_name)

        # ── Step 5: Screen par dikhao ─────────────────────────────────────────
        cv2.imshow("AI Gesture Controller", frame)

        # ── Step 6: ESC ya 'q' press karo band karne ke liye ─────────────────
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord("q"):  # 27 = ESC key ka ASCII code
            print("\n👋 Exiting AI Gesture Controller...")
            break

    # ── Cleanup ───────────────────────────────────────────────────────────────
    # Agar koi mode active tha toh usse band karo (keys release karo)
    if mode_manager.current_mode_obj is not None:
        mode_manager.current_mode_obj.stop()

    camera.release()
    print("✅ Program band ho gaya.")


# ── Python convention: Seedha run hone par main() call karo ──────────────────
# Agar yeh file kisi doosri file ne import kiya toh main() automatically nahi chalega
if __name__ == "__main__":
    main()