# =============================================================================
# gestures/hand_detector.py — MediaPipe se haath detect karne wala class
# =============================================================================
#
# MediaPipe ek Google ka AI library hai jo haath ke 21 landmark points
# detect kar sakta hai in real time.
#
# 21 Landmark Points ka map:
#
#   Wrist = 0
#
#   Thumb:  CMC=1, MCP=2, IP=3, Tip=4
#   Index:  MCP=5, PIP=6, DIP=7, Tip=8
#   Middle: MCP=9, PIP=10, DIP=11, Tip=12
#   Ring:   MCP=13, PIP=14, DIP=15, Tip=16
#   Pinky:  MCP=17, PIP=18, DIP=19, Tip=20
#
#   PIP = knuckle near palm
#   Tip = finger ka sabse upar wala point
#
# Finger UP check logic:
#   - Agar finger ka Tip, PIP se upar hai (y value kam hai) → finger UP
#   - Thumb ke liye X axis use hota hai (y nahi) kyunki thumb sideways move karta hai
#
# =============================================================================

import cv2
import mediapipe as mp
import math

from config.settings import MAX_HANDS, DETECTION_CONFIDENCE, TRACKING_CONFIDENCE


class HandDetector:
    """
    Webcam frame se haath detect karta hai aur landmarks provide karta hai.

    Usage:
        detector = HandDetector()
        frame = detector.find_hands(frame)         # Haath draw karo
        landmarks = detector.get_landmark_list(frame)  # Coordinates lo
        fingers = detector.fingers_up()            # Kaunsi ungli upar hai
    """

    def __init__(
        self,
        max_hands=MAX_HANDS,
        detection_confidence=DETECTION_CONFIDENCE,
        tracking_confidence=TRACKING_CONFIDENCE,
    ):
        """
        HandDetector setup karta hai.

        Parameters:
            max_hands            : Ek frame mein kitne haath detect karne hain (default: 1)
            detection_confidence : Haath detect hone ki minimum accuracy (0.0–1.0)
            tracking_confidence  : Haath track hone ki minimum accuracy (0.0–1.0)
        """

        # ── MediaPipe Hands module load karo ──────────────────────────────────
        self.mp_hands = mp.solutions.hands
        self.mp_draw  = mp.solutions.drawing_utils

        # MediaPipe ka main Hands object banana
        self.hands = self.mp_hands.Hands(
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )

        # ── Instance variables — yeh data store karte hain ───────────────────
        self.results       = None   # MediaPipe ka raw output yahan store hoga
        self.landmark_list = []     # 21 landmarks ki list: [[id, x, y], ...]

    # ─────────────────────────────────────────────────────────────────────────
    def find_hands(self, frame, draw=True):
        """
        Frame mein haath dhundho aur optionally skeleton draw karo.

        Parameters:
            frame : OpenCV BGR image (numpy array) — webcam se aaya frame
            draw  : True = haath ke upar skeleton lines draw karo

        Returns:
            frame : Processed frame (drawn landmarks ke saath ya bina)
        """

        # MediaPipe RGB expect karta hai, OpenCV BGR deta hai → convert karo
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # MediaPipe se hand detection karo
        self.results = self.hands.process(rgb_frame)

        # Agar haath mila toh draw karo
        if self.results.multi_hand_landmarks and draw:
            for hand_landmarks in self.results.multi_hand_landmarks:
                # Skeleton (bones) draw karo
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                )

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    def get_landmark_list(self, frame):
        """
        Pehle detect hue haath ke sabhi 21 landmarks ki pixel coordinates lo.

        Landmarks ka format: [[0, x0, y0], [1, x1, y1], ..., [20, x20, y20]]
        Matlab har entry mein: [landmark_id, x_pixel, y_pixel]

        Parameters:
            frame : Current frame (size nikalne ke liye chahiye)

        Returns:
            list : 21 landmarks ki list, ya [] agar haath nahi mila
        """

        self.landmark_list = []

        # Agar koi haath detect nahi hua toh khali list return karo
        if not self.results or not self.results.multi_hand_landmarks:
            return self.landmark_list

        # Pehla haath lo (index 0)
        first_hand = self.results.multi_hand_landmarks[0]

        # Frame ka height aur width lo (landmarks 0–1 range mein hote hain, pixels mein nahi)
        h, w, _ = frame.shape

        for landmark_id, landmark in enumerate(first_hand.landmark):
            # 0.0–1.0 range se pixel coordinates mein convert karo
            x = int(landmark.x * w)
            y = int(landmark.y * h)

            self.landmark_list.append([landmark_id, x, y])

        return self.landmark_list

    # ─────────────────────────────────────────────────────────────────────────
    def fingers_up(self):
        """
        Har ungli ke baare mein batata hai ki woh upar hai ya neeche.

        Returns:
            list : [thumb, index, middle, ring, pinky]
                   1 = finger up (seedhi), 0 = finger down (bendi)
                   Example: [1, 1, 0, 0, 0] = thumb + index up
        """

        # Agar haath nahi mila toh sab 0 return karo
        if not self.landmark_list:
            return [0, 0, 0, 0, 0]

        fingers = []

        # ── THUMB ─────────────────────────────────────────────────────────────
        # Thumb ke liye X axis check karte hain (Y nahi) kyunki thumb
        # horizontally move karta hai, vertically nahi.
        #
        # Frame flip hoti hai (mirror mode), isliye:
        #   Right hand mein thumb up = tip (landmark 4) ka x > base (landmark 2) ka x
        #
        # landmark_list[4][1] = landmark id=4 ka x coordinate
        # landmark_list[2][1] = landmark id=2 ka x coordinate

        tip_x  = self.landmark_list[4][1]    # Thumb tip ki x position
        base_x = self.landmark_list[2][1]    # Thumb base ki x position

        if tip_x > base_x:
            fingers.append(1)   # Thumb up
        else:
            fingers.append(0)   # Thumb down

        # ── FOUR FINGERS (Index, Middle, Ring, Pinky) ─────────────────────────
        # Har finger ke liye: Tip upar hai (y kam) toh finger up
        #
        # (tips)   Index=8,  Middle=12, Ring=16, Pinky=20
        # (knucks) Index=6,  Middle=10, Ring=14, Pinky=18

        tips   = [8,  12, 16, 20]
        knucks = [6,  10, 14, 18]

        for tip_id, knuck_id in zip(tips, knucks):
            tip_y   = self.landmark_list[tip_id][2]    # Finger tip ki y position
            knuck_y = self.landmark_list[knuck_id][2]  # Finger knuckle ki y position

            # Yaad raho: y axis neeche badhta hai, isliye tip_y < knuck_y = finger UP
            if tip_y < knuck_y:
                fingers.append(1)   # Finger up
            else:
                fingers.append(0)   # Finger down

        return fingers   # [thumb, index, middle, ring, pinky]

    # ─────────────────────────────────────────────────────────────────────────
    def get_distance(self, point1_id, point2_id, frame, draw=True):
        """
        Do landmark points ke beech ki doori calculate karta hai.
        Aksar thumb aur index finger ke beech distance ke liye use hota hai.

        Parameters:
            point1_id : Pehle landmark ka ID (0–20)
            point2_id : Doosre landmark ka ID (0–20)
            frame     : Current frame (drawing ke liye)
            draw      : True = points aur line frame par draw karo

        Returns:
            distance  : float — do points ke beech ki distance (pixels)
            frame     : Updated frame
            info      : [x1, y1, x2, y2, mid_x, mid_y] — coordinates
        """

        if not self.landmark_list:
            return 0, frame, []

        # Dono points ki coordinates lo
        x1, y1 = self.landmark_list[point1_id][1], self.landmark_list[point1_id][2]
        x2, y2 = self.landmark_list[point2_id][1], self.landmark_list[point2_id][2]

        # Beech wala point nikalo
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2

        # Frame par draw karo (agar draw=True ho)
        if draw:
            cv2.circle(frame, (x1, y1), 8, (255, 100, 0), cv2.FILLED)   # Point 1
            cv2.circle(frame, (x2, y2), 8, (255, 100, 0), cv2.FILLED)   # Point 2
            cv2.line(frame, (x1, y1), (x2, y2), (255, 100, 0), 2)       # Line
            cv2.circle(frame, (mid_x, mid_y), 6, (0, 0, 255), cv2.FILLED)  # Midpoint

        # Euclidean distance formula: sqrt( (x2-x1)^2 + (y2-y1)^2 )
        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        return distance, frame, [x1, y1, x2, y2, mid_x, mid_y]

    # ─────────────────────────────────────────────────────────────────────────
    def is_hand_detected(self):
        """
        Kya is frame mein koi haath detect hua hai?

        Returns:
            bool : True = haath mila, False = nahi mila
        """
        return bool(self.landmark_list)
