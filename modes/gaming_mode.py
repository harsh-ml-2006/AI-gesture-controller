import cv2
import time
from pynput.keyboard import Controller, Key
from config.settings import GAMING_GESTURES, GAMING_ACTION_KEYS, GAMING_STABILITY_FRAMES, COLOR_GREEN, COLOR_RED, COLOR_WHITE, COLOR_BLACK, COLOR_YELLOW, COLOR_ORANGE, COLOR_CYAN
from utils.finger_utils import fingers_as_tuple, get_gesture_name

class GamingMode:

    def __init__(self):
        self.keyboard = Controller()
        self.pressed_keys = set()
        self.stability_frames = GAMING_STABILITY_FRAMES
        self.current_gesture = 'idle'
        self.candidate_gesture = 'idle'
        self.stable_count = 0
        self.is_active = True
        print('🎮 Gaming Mode started!')
        print("   Hold 'Thumbs Up' gesture for 2 seconds to switch mode.")

    def run(self, frame, fingers_up, landmark_list, hand_present=True):
        if not hand_present:
            frame = self._draw_hud(frame, [0, 0, 0, 0, 0])
            return frame
        finger_tuple = fingers_as_tuple(fingers_up)
        detected_gesture = GAMING_GESTURES.get(finger_tuple, 'idle')
        if detected_gesture == self.candidate_gesture:
            self.stable_count += 1
        else:
            self.candidate_gesture = detected_gesture
            self.stable_count = 1
        if self.stable_count >= self.stability_frames:
            if detected_gesture != self.current_gesture:
                self._change_action(detected_gesture)
        frame = self._draw_hud(frame, fingers_up)
        return frame

    def _change_action(self, new_gesture):
        self._release_all_keys()
        self.current_gesture = new_gesture
        key = GAMING_ACTION_KEYS.get(new_gesture)
        if key is not None:
            self._press_key(key)
            print(f'🎮 Gesture: {new_gesture:15} → Key: [{key}] PRESSED')
        else:
            print(f'🎮 Gesture: {new_gesture:15} → Idle (no key)')

    def _press_key(self, key):
        actual_key = self._resolve_key(key)
        if actual_key not in self.pressed_keys:
            self.keyboard.press(actual_key)
            self.pressed_keys.add(actual_key)

    def _release_all_keys(self):
        for key in list(self.pressed_keys):
            actual_key = self._resolve_key(key)
            self.keyboard.release(actual_key)
        self.pressed_keys.clear()

    def _resolve_key(self, key):
        special_keys = {'space': Key.space, 'ctrl': Key.ctrl, 'shift': Key.shift, 'alt': Key.alt, 'enter': Key.enter, 'esc': Key.esc, 'tab': Key.tab, 'up': Key.up, 'down': Key.down, 'left': Key.left, 'right': Key.right}
        return special_keys.get(key, key)

    def _draw_hud(self, frame, fingers_up):
        (h, w, _) = frame.shape
        cv2.rectangle(frame, (0, 0), (320, 50), COLOR_BLACK, cv2.FILLED)
        cv2.putText(frame, 'MODE: GAMING', (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, COLOR_GREEN, 2)
        gesture_name = get_gesture_name(fingers_up)
        active_key = GAMING_ACTION_KEYS.get(self.current_gesture, 'none')
        key_display = str(active_key).upper() if active_key else 'IDLE'
        cv2.rectangle(frame, (0, 55), (400, 145), (20, 20, 20), cv2.FILLED)
        cv2.putText(frame, f'Gesture: {gesture_name}', (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.75, COLOR_WHITE, 2)
        cv2.putText(frame, f'Key: [ {key_display} ]', (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 1.0, COLOR_YELLOW if active_key else COLOR_WHITE, 2)
        cheat_sheet = [('Index', 'UP    - Forward'), ('Index+Middle', 'DOWN  - Backward'), ('3 Fingers', 'LEFT  - Left'), ('4 Fingers', 'RIGHT - Right'), ('Open Palm', 'Space - Jump'), ('Thumb Only', 'F  - Action'), ('Thumb+Pinky', 'R  - Reload'), ('Pinky Only', 'C  - Crouch'), ('Fist', 'Idle')]
        sheet_x = w - 350
        sheet_y = h - (len(cheat_sheet) * 28 + 40)
        cv2.rectangle(frame, (sheet_x - 10, sheet_y - 25), (w - 5, h - 5), (20, 20, 20), cv2.FILLED)
        cv2.putText(frame, 'GESTURE GUIDE', (sheet_x, sheet_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_CYAN, 2)
        for (i, (gesture, key_action)) in enumerate(cheat_sheet):
            color = COLOR_ORANGE if GAMING_ACTION_KEYS.get(self.current_gesture) and key_action.startswith(str(GAMING_ACTION_KEYS.get(self.current_gesture, '')).upper()) else COLOR_WHITE
            cv2.putText(frame, f'{gesture:<20} {key_action}', (sheet_x, sheet_y + 22 + i * 26), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        finger_names = ['T', 'I', 'M', 'R', 'P']
        box_start_x = 10
        box_start_y = h - 60
        for (i, (name, state)) in enumerate(zip(finger_names, fingers_up)):
            x = box_start_x + i * 50
            color = COLOR_GREEN if state == 1 else COLOR_RED
            cv2.rectangle(frame, (x, box_start_y), (x + 40, box_start_y + 40), color, cv2.FILLED)
            cv2.putText(frame, name, (x + 12, box_start_y + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_BLACK, 2)
        return frame

    def stop(self):
        self._release_all_keys()
        self.is_active = False
        print('🎮 Gaming Mode stopped. All keys released.')