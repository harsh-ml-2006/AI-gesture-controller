import cv2
import mediapipe as mp

# ---------------- MediaPipe Initialization ----------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

# Drawing Utility
mp_draw = mp.solutions.drawing_utils

# ---------------- Webcam ----------------
cap = cv2.VideoCapture(0)

while True:

    # Read frame from webcam
    success, frame = cap.read()

    if not success:
        print("Camera Error!")
        break

    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect Hands
    results = hands.process(rgb_frame)

    # If hand detected
    if results.multi_hand_landmarks:

        # Loop through every detected hand
        for hand_landmarks in results.multi_hand_landmarks:

            # Draw Hand Skeleton
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # ---------------- Day 4 ----------------
            # Finger Counting

            landmarks = hand_landmarks.landmark

            finger_count = 0

            # Index Finger
            if landmarks[8].y < landmarks[6].y:
                finger_count += 1

            # Middle Finger
            if landmarks[12].y < landmarks[10].y:
                finger_count += 1

            # Ring Finger
            if landmarks[16].y < landmarks[14].y:
                finger_count += 1

            # Pinky Finger
            if landmarks[20].y < landmarks[18].y:
                finger_count += 1

            # Display Finger Count
            cv2.putText(
                frame,
                f"Fingers : {finger_count}",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            # ---------------- Day 3 ----------------
            # Print Landmark Coordinates

            for landmark_id, landmark in enumerate(landmarks):

                h, w, c = frame.shape

                cx = int(landmark.x * w)
                cy = int(landmark.y * h)

                # print(landmark_id, cx, cy)

                # Draw Red Circle on Index Finger Tip
                if landmark_id == 8:

                    cv2.circle(
                        frame,
                        (cx, cy),
                        12,
                        (0, 0, 255),
                        cv2.FILLED
                    )

    # Show Output
    cv2.imshow("Hand Detection", frame)

    # Press ESC to Exit
    if cv2.waitKey(1) == 27:
        break

# Release Resources
cap.release()
cv2.destroyAllWindows()