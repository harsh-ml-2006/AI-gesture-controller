import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import cv2
import time
from camera.camera_handler import CameraHandler
from gestures.hand_detector import HandDetector
from modes.gaming_mode import GamingMode
from modes.music_control import MusicControlMode
from utils.finger_utils import is_thumbs_up, is_fist, is_open_palm, count_fingers, get_gesture_name
from config.settings import MODE_SWITCH_HOLD_SECONDS, MODE_SELECT_HOLD_SECONDS, MODES, COLOR_GREEN, COLOR_RED, COLOR_WHITE, COLOR_BLACK, COLOR_YELLOW, COLOR_CYAN, COLOR_ORANGE

class ModeManager:

    def __init__(self):
        self.current_mode_id = 0
        self.current_mode_name = MODES[0]
        self.current_mode_obj = None
        self.state = 'normal'
        self.thumbs_up_start_time = None
        self.selected_mode_id = 0
        self.selection_confirm_start = None
        self.selection_entered_time = None
        self.SELECTOR_TIMEOUT = 5.0
        self._mode_objects = {}
        print(f'Starting in: {self.current_mode_name}')

    def update(self, fingers_up, frame):
        if self.state == 'normal':
            frame = self._handle_normal_state(fingers_up, frame)
        elif self.state == 'selecting':
            frame = self._handle_selecting_state(fingers_up, frame)
        return frame

    def _handle_normal_state(self, fingers_up, frame):
        if is_fist(fingers_up):
            if self.thumbs_up_start_time is None:
                self.thumbs_up_start_time = time.time()
            held_for = time.time() - self.thumbs_up_start_time
            frame = self._draw_switch_progress(frame, held_for, MODE_SWITCH_HOLD_SECONDS)
            if held_for >= MODE_SWITCH_HOLD_SECONDS:
                self.state = 'selecting'
                self.thumbs_up_start_time = None
                self.selected_mode_id = self.current_mode_id
                self.selection_entered_time = time.time()
                print('Mode Selector opened!')
        else:
            self.thumbs_up_start_time = None
        return frame

    def _handle_selecting_state(self, fingers_up, frame):
        finger_count = count_fingers(fingers_up)
        detected_mode_id = finger_count
        if detected_mode_id != self.selected_mode_id:
            self.selected_mode_id = detected_mode_id
            self.selection_confirm_start = None
        if self.selection_confirm_start is None:
            self.selection_confirm_start = time.time()
        hold_time = time.time() - self.selection_confirm_start
        frame = self._draw_mode_selector(frame, self.selected_mode_id, hold_time)
        if hold_time >= MODE_SELECT_HOLD_SECONDS:
            self._activate_mode(self.selected_mode_id)
            self.state = 'normal'
            self.selection_confirm_start = None
        time_in_selector = time.time() - (self.selection_entered_time or time.time())
        if time_in_selector > self.SELECTOR_TIMEOUT:
            self.state = 'normal'
            print('Mode selector timed out.')
        return frame

    def _activate_mode(self, mode_id):
        if self.current_mode_obj is not None:
            self.current_mode_obj.stop()
            self.current_mode_obj = None
        self.current_mode_id = mode_id
        self.current_mode_name = MODES.get(mode_id, 'Unknown Mode')
        if mode_id == 5:
            self.current_mode_obj = GamingMode()
            print('[GAMING] Gaming Mode started!')
        elif mode_id == 4:
            self.current_mode_obj = MusicControlMode()
        elif mode_id == 0:
            self.current_mode_obj = None
            print('No Mode selected — hand tracking only.')
        else:
            print(f"Mode '{self.current_mode_name}' abhi available nahi hai. Coming soon!")
            self.current_mode_obj = None
        print(f'Mode changed to: {self.current_mode_name}')

    def run_current_mode(self, frame, fingers_up, landmark_list, hand_present=True):
        if self.current_mode_obj is not None:
            frame = self.current_mode_obj.run(frame, fingers_up, landmark_list, hand_present=hand_present)
        return frame

    def _draw_switch_progress(self, frame, held_for, total_time):
        (h, w, _) = frame.shape
        progress = min(held_for / total_time, 1.0)
        cv2.putText(frame, 'Hold FIST for Mode Switch...', (w // 2 - 210, h - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLOR_YELLOW, 2)
        (bar_x, bar_y) = (w // 2 - 200, h - 50)
        (bar_w, bar_h) = (400, 20)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (80, 80, 80), cv2.FILLED)
        fill_w = int(bar_w * progress)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), COLOR_YELLOW, cv2.FILLED)
        return frame

    def _draw_mode_selector(self, frame, selected_mode_id, hold_time):
        (h, w, _) = frame.shape
        overlay = frame.copy()
        cv2.rectangle(overlay, (w // 2 - 250, 50), (w // 2 + 250, h - 50), (10, 10, 10), cv2.FILLED)
        frame = cv2.addWeighted(overlay, 0.75, frame, 0.25, 0)
        cv2.putText(frame, 'SELECT MODE', (w // 2 - 120, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, COLOR_CYAN, 3)
        cv2.putText(frame, 'Show fingers = Mode Number | Hold to Confirm', (w // 2 - 240, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_WHITE, 1)
        mode_list = [(0, 'Fist (0 fingers)', 'No Mode'), (5, 'Open Palm (5 fingers)', 'Gaming Mode   [READY]'), (4, '4 fingers', 'Music Control [READY]'), (1, '1 finger', 'Virtual Mouse  - Coming Soon'), (2, '2 fingers', 'Volume Control - Coming Soon'), (3, '3 fingers', 'Brightness     - Coming Soon')]
        start_y = 170
        for (i, (mode_id, gesture_hint, mode_name)) in enumerate(mode_list):
            y = start_y + i * 65
            is_selected = mode_id == selected_mode_id
            bg_color = COLOR_GREEN if is_selected else (40, 40, 40)
            text_color = COLOR_BLACK if is_selected else COLOR_WHITE
            cv2.rectangle(frame, (w // 2 - 240, y - 30), (w // 2 + 240, y + 25), bg_color, cv2.FILLED)
            cv2.putText(frame, gesture_hint, (w // 2 - 230, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
            cv2.putText(frame, f'→ {mode_name}', (w // 2 - 230, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
        if hold_time > 0:
            progress = min(hold_time / MODE_SELECT_HOLD_SECONDS, 1.0)
            bar_x = w // 2 - 240
            bar_y = h - 120
            bar_w = 480
            bar_h = 20
            cv2.putText(frame, 'Hold gesture to confirm...', (bar_x, bar_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_WHITE, 1)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (80, 80, 80), cv2.FILLED)
            fill_w = int(bar_w * progress)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), COLOR_GREEN, cv2.FILLED)
        return frame

def draw_status_bar(frame, fps, mode_name):
    (h, w, _) = frame.shape
    cv2.rectangle(frame, (0, 0), (w, 45), (15, 15, 15), cv2.FILLED)
    fps_color = COLOR_GREEN if fps > 20 else COLOR_RED
    cv2.putText(frame, f'FPS: {fps}', (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.9, fps_color, 2)
    cv2.putText(frame, 'AI Gesture Controller', (w // 2 - 130, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.9, COLOR_WHITE, 2)
    cv2.putText(frame, f'Mode: {mode_name}', (w - 280, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.75, COLOR_CYAN, 2)
    return frame

def draw_no_hand_message(frame):
    (h, w, _) = frame.shape
    cv2.putText(frame, 'No Hand Detected', (w // 2 - 150, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (100, 100, 100), 2)
    return frame

def main():
    print('=' * 55)
    print('   AI Gesture Controller -- Starting...')
    print('=' * 55)
    print("   Press ESC or 'q' to quit")
    print('   Hold FIST (mutthi) for 2 sec --> Mode Selector')
    print('=' * 55)
    camera = CameraHandler()
    detector = HandDetector()
    mode_manager = ModeManager()
    while True:
        frame = camera.get_frame()
        if frame is None:
            continue
        frame = detector.find_hands(frame)
        landmark_list = detector.get_landmark_list(frame)
        if detector.is_hand_detected():
            fingers_up = detector.fingers_up()
            frame = mode_manager.update(fingers_up, frame)
            frame = mode_manager.run_current_mode(frame, fingers_up, landmark_list, hand_present=True)
        else:
            draw_no_hand_message(frame)
            frame = mode_manager.run_current_mode(frame, [0, 0, 0, 0, 0], [], hand_present=False)
        frame = draw_status_bar(frame, camera.get_fps(), mode_manager.current_mode_name)
        cv2.imshow('AI Gesture Controller', frame)
        key = cv2.waitKey(1) & 255
        if key == 27 or key == ord('q'):
            print('\n👋 Exiting AI Gesture Controller...')
            break
    if mode_manager.current_mode_obj is not None:
        mode_manager.current_mode_obj.stop()
    camera.release()
    print('✅ Program band ho gaya.')
if __name__ == '__main__':
    main()