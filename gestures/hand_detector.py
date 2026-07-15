import cv2
import mediapipe as mp
import math
from config.settings import MAX_HANDS, DETECTION_CONFIDENCE, TRACKING_CONFIDENCE

class HandDetector:

    def __init__(self, max_hands=MAX_HANDS, detection_confidence=DETECTION_CONFIDENCE, tracking_confidence=TRACKING_CONFIDENCE):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(max_num_hands=max_hands, min_detection_confidence=detection_confidence, min_tracking_confidence=tracking_confidence)
        self.results = None
        self.landmark_list = []

    def find_hands(self, frame, draw=True):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(rgb_frame)
        if self.results.multi_hand_landmarks and draw:
            for hand_landmarks in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
        return frame

    def get_landmark_list(self, frame):
        self.landmark_list = []
        if not self.results or not self.results.multi_hand_landmarks:
            return self.landmark_list
        first_hand = self.results.multi_hand_landmarks[0]
        (h, w, _) = frame.shape
        for (landmark_id, landmark) in enumerate(first_hand.landmark):
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            self.landmark_list.append([landmark_id, x, y])
        return self.landmark_list

    def fingers_up(self):
        if not self.landmark_list:
            return [0, 0, 0, 0, 0]
        fingers = []
        tip_x = self.landmark_list[4][1]
        base_x = self.landmark_list[2][1]
        if tip_x > base_x:
            fingers.append(1)
        else:
            fingers.append(0)
        tips = [8, 12, 16, 20]
        knucks = [6, 10, 14, 18]
        for (tip_id, knuck_id) in zip(tips, knucks):
            tip_y = self.landmark_list[tip_id][2]
            knuck_y = self.landmark_list[knuck_id][2]
            if tip_y < knuck_y:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers

    def get_distance(self, point1_id, point2_id, frame, draw=True):
        if not self.landmark_list:
            return (0, frame, [])
        (x1, y1) = (self.landmark_list[point1_id][1], self.landmark_list[point1_id][2])
        (x2, y2) = (self.landmark_list[point2_id][1], self.landmark_list[point2_id][2])
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        if draw:
            cv2.circle(frame, (x1, y1), 8, (255, 100, 0), cv2.FILLED)
            cv2.circle(frame, (x2, y2), 8, (255, 100, 0), cv2.FILLED)
            cv2.line(frame, (x1, y1), (x2, y2), (255, 100, 0), 2)
            cv2.circle(frame, (mid_x, mid_y), 6, (0, 0, 255), cv2.FILLED)
        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return (distance, frame, [x1, y1, x2, y2, mid_x, mid_y])

    def is_hand_detected(self):
        return bool(self.landmark_list)