# =============================================================================
# camera/camera_handler.py — Webcam handle karne wala class
# =============================================================================
# Yeh class OpenCV ke VideoCapture ko wrap karta hai.
# Iska faida yeh hai ki camera-related saari settings ek jagah hain.
# =============================================================================

import cv2
import time

from config.settings import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT


class CameraHandler:
    """
    Webcam se frames lene ke liye responsible class.
    FPS (frames per second) bhi track karta hai.

    Usage:
        cam = CameraHandler()
        frame = cam.get_frame()
        fps = cam.get_fps()
        cam.release()      ← Program khatam hone par jaroor call karo
    """

    def __init__(self, camera_index=CAMERA_INDEX):
        """
        Camera setup karta hai.

        Parameters:
            camera_index : int — Kaunsa camera use karna hai
                           0 = default/built-in webcam
                           1 = pehla external camera
        """

        # OpenCV se camera open karo
        self.cap = cv2.VideoCapture(camera_index)

        # Camera resolution set karo
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

        # Agar camera open nahi hua toh error do
        if not self.cap.isOpened():
            raise RuntimeError(
                f"❌ Camera {camera_index} open nahi hua! "
                "Check karo kya webcam connected hai."
            )

        # ── FPS Counter ke liye variables ────────────────────────────────────
        self._prev_time = time.time()   # Pichle frame ka time
        self._fps       = 0            # Calculated FPS

        print(f"✅ Camera {camera_index} successfully open hua.")

    # ─────────────────────────────────────────────────────────────────────────
    def get_frame(self, flip=True):
        """
        Camera se ek frame lata hai.

        Parameters:
            flip : bool — True = frame mirror karo (natural/selfie view)
                          False = as-is raho

        Returns:
            frame : numpy array — OpenCV BGR image
                    Ya None agar camera se frame nahi aaya
        """

        success, frame = self.cap.read()

        if not success:
            print("⚠️ Frame nahi aaya camera se!")
            return None

        # Frame mirror karo taaki screen par natural lage (jaise mirror mein dekhte hain)
        if flip:
            frame = cv2.flip(frame, 1)   # 1 = horizontal flip

        # FPS update karo
        self._update_fps()

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    def get_fps(self):
        """
        Current FPS (frames per second) return karta hai.
        FPS = kitne frames ek second mein process ho rahe hain.
        Zyada FPS = smooth experience.
        """
        return int(self._fps)

    # ─────────────────────────────────────────────────────────────────────────
    def _update_fps(self):
        """
        (Internal method) Har frame par FPS calculate karta hai.
        FPS = 1 / (is frame aur pichle frame ke beech ka time)
        """
        current_time  = time.time()
        time_elapsed  = current_time - self._prev_time

        # Division by zero se bachne ke liye check
        if time_elapsed > 0:
            self._fps = 1 / time_elapsed

        self._prev_time = current_time

    # ─────────────────────────────────────────────────────────────────────────
    def release(self):
        """
        Camera aur saari OpenCV windows band karo.
        Program khatam hone par yeh zaroor call karna chahiye.
        """
        self.cap.release()
        cv2.destroyAllWindows()
        print("📷 Camera released.")
