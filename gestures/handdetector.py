import cv2
import mediapipe as mp
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)
while True:
    (success, frame) = cap.read()
    if not success:
        print('Camera Error!')
        break
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            landmarks = hand_landmarks.landmark
            finger_count = 0
            if landmarks[8].y < landmarks[6].y:
                finger_count += 1
            if landmarks[12].y < landmarks[10].y:
                finger_count += 1
            if landmarks[16].y < landmarks[14].y:
                finger_count += 1
            if landmarks[20].y < landmarks[18].y:
                finger_count += 1
            cv2.putText(frame, f'Fingers : {finger_count}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            for (landmark_id, landmark) in enumerate(landmarks):
                (h, w, c) = frame.shape
                cx = int(landmark.x * w)
                cy = int(landmark.y * h)
                if landmark_id == 8:
                    cv2.circle(frame, (cx, cy), 12, (0, 0, 255), cv2.FILLED)
    cv2.imshow('Hand Detection', frame)
    if cv2.waitKey(1) == 27:
        break
cap.release()
cv2.destroyAllWindows()