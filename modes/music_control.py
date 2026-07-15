import cv2
import time
from pynput.keyboard import Controller, Key
from config.settings import COLOR_GREEN, COLOR_RED, COLOR_WHITE, COLOR_BLACK, COLOR_YELLOW, COLOR_CYAN, COLOR_ORANGE, COLOR_PURPLE
from utils.finger_utils import fingers_as_tuple, count_fingers, is_fist
MUSIC_GESTURES = {(0, 0, 0, 0, 0): 'idle', (0, 1, 0, 0, 0): 'play_pause', (0, 1, 1, 0, 0): 'next_track', (0, 1, 1, 1, 0): 'prev_track', (1, 1, 1, 1, 1): 'volume_up', (1, 0, 0, 0, 0): 'volume_down', (1, 1, 0, 0, 0): 'mute', (0, 0, 0, 0, 1): 'stop'}
CONTINUOUS_ACTIONS = {'volume_up', 'volume_down'}
SINGLE_SHOT_ACTIONS = {'play_pause', 'next_track', 'prev_track', 'mute', 'stop'}
MUSIC_ACTION_KEYS = {'idle': None, 'play_pause': Key.media_play_pause, 'next_track': (Key.shift, 'n'), 'prev_track': (Key.shift, 'p'), 'volume_up': Key.media_volume_up, 'volume_down': Key.media_volume_down, 'mute': Key.media_volume_mute, 'stop': Key.media_stop}
ACTION_DISPLAY = {'idle': '⏸  Idle', 'play_pause': '⏯  Play / Pause', 'next_track': '⏭  Next Track', 'prev_track': '⏮  Previous Track', 'volume_up': '🔊  Volume Up', 'volume_down': '🔉  Volume Down', 'mute': '🔇  Mute', 'stop': '⏹  Stop'}

class MusicControlMode:
    VOLUME_REPEAT_INTERVAL = 0.15
    SINGLE_SHOT_COOLDOWN = 0.8

    def __init__(self):
        self.keyboard = Controller()
        self.last_action = 'idle'
        self.last_action_time = 0
        self.stable_frames = 2
        self.candidate = 'idle'
        self.candidate_count = 0
        self.waiting_for_reset = False
        self.continuous_last_press = 0
        print('Music Control Mode started!')

    def run(self, frame, fingers_up, landmark_list, hand_present=True):
        if not hand_present:
            frame = self._draw_hud(frame, [0, 0, 0, 0, 0])
            return frame
        finger_tuple = fingers_as_tuple(fingers_up)
        detected_gesture = MUSIC_GESTURES.get(finger_tuple, 'idle')
        if detected_gesture == self.candidate:
            self.candidate_count += 1
        else:
            self.candidate = detected_gesture
            self.candidate_count = 1
        gesture_stable = self.candidate_count >= self.stable_frames
        not_idle = detected_gesture != 'idle'
        now = time.time()
        if gesture_stable and detected_gesture in CONTINUOUS_ACTIONS:
            if now - self.continuous_last_press >= self.VOLUME_REPEAT_INTERVAL:
                self._tap_key(detected_gesture)
                self.last_action = detected_gesture
                self.continuous_last_press = now
        elif self.waiting_for_reset:
            if is_fist(fingers_up):
                self.waiting_for_reset = False
                self.candidate = 'idle'
                self.candidate_count = 0
        elif gesture_stable and not_idle and (detected_gesture in SINGLE_SHOT_ACTIONS):
            if now - self.last_action_time >= self.SINGLE_SHOT_COOLDOWN:
                self._tap_key(detected_gesture)
                self.last_action = detected_gesture
                self.last_action_time = now
                self.waiting_for_reset = True
        show_reset_msg = self.waiting_for_reset and detected_gesture not in CONTINUOUS_ACTIONS
        status_msg = 'Fist karo next action ke liye...' if show_reset_msg else None
        frame = self._draw_hud(frame, fingers_up, status_msg)
        return frame

    def _focus_browser(self):
        try:
            import pygetwindow as gw
            search_keywords = ['YouTube', 'Chrome', 'Firefox', 'Edge', 'Brave', 'Opera']
            for keyword in search_keywords:
                windows = gw.getWindowsWithTitle(keyword)
                if windows:
                    windows[0].activate()
                    time.sleep(0.12)
                    return True
        except Exception as e:
            print(f'Browser focus error: {e}')
        return False

    def _tap_key(self, gesture_name):
        key = MUSIC_ACTION_KEYS.get(gesture_name)
        if key is None:
            return
        if isinstance(key, tuple):
            self._focus_browser()
            (modifier, main_key) = key
            self.keyboard.press(modifier)
            self.keyboard.press(main_key)
            self.keyboard.release(main_key)
            self.keyboard.release(modifier)
        else:
            self.keyboard.press(key)
            self.keyboard.release(key)
        display = ACTION_DISPLAY.get(gesture_name, gesture_name)
        print(f'Music Action: {display}')

    def _draw_hud(self, frame, fingers_up, status_msg=None):
        (h, w, _) = frame.shape
        cv2.rectangle(frame, (0, 0), (350, 50), COLOR_BLACK, cv2.FILLED)
        cv2.putText(frame, 'MODE: MUSIC CONTROL', (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, COLOR_PURPLE, 2)
        action_display = ACTION_DISPLAY.get(self.last_action, self.last_action)
        cv2.rectangle(frame, (0, 55), (420, 140), (20, 20, 20), cv2.FILLED)
        cv2.putText(frame, 'Last Action:', (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.65, COLOR_WHITE, 1)
        cv2.putText(frame, action_display, (10, 125), cv2.FONT_HERSHEY_SIMPLEX, 1.0, COLOR_YELLOW, 2)
        if status_msg:
            cv2.rectangle(frame, (0, 145), (380, 185), (40, 10, 10), cv2.FILLED)
            cv2.putText(frame, status_msg, (10, 172), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_RED, 2)
        cheat_sheet = [('Index', 'Play / Pause'), ('Index + Middle', 'Next Track'), ('3 Fingers', 'Previous Track'), ('Open Palm (5)', 'Volume Up'), ('Thumb Only', 'Volume Down'), ('Thumb + Index', 'Mute'), ('Pinky Only', 'Stop'), ('Fist', 'Reset / Idle')]
        sheet_x = w - 360
        sheet_y = h - (len(cheat_sheet) * 28 + 40)
        cv2.rectangle(frame, (sheet_x - 10, sheet_y - 28), (w - 5, h - 5), (20, 20, 20), cv2.FILLED)
        cv2.putText(frame, 'MUSIC GESTURE GUIDE', (sheet_x, sheet_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_CYAN, 2)
        for (i, (gesture, action)) in enumerate(cheat_sheet):
            cv2.putText(frame, f'{gesture:<22} {action}', (sheet_x, sheet_y + 22 + i * 26), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_WHITE, 1)
        finger_names = ['T', 'I', 'M', 'R', 'P']
        box_x = 10
        box_y = h - 60
        for (i, (name, state)) in enumerate(zip(finger_names, fingers_up)):
            x = box_x + i * 50
            color = COLOR_GREEN if state == 1 else COLOR_RED
            cv2.rectangle(frame, (x, box_y), (x + 40, box_y + 40), color, cv2.FILLED)
            cv2.putText(frame, name, (x + 12, box_y + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_BLACK, 2)
        return frame

    def stop(self):
        print('🎵 Music Control Mode stopped.')