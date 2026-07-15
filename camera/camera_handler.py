import cv2
import time
from config.settings import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT

class CameraHandler:

    def __init__(self, camera_index=CAMERA_INDEX):
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        if not self.cap.isOpened():
            raise RuntimeError(f'❌ Camera {camera_index} open nahi hua! Check karo kya webcam connected hai.')
        self._prev_time = time.time()
        self._fps = 0
        print(f'✅ Camera {camera_index} successfully open hua.')

    def get_frame(self, flip=True):
        (success, frame) = self.cap.read()
        if not success:
            print('⚠️ Frame nahi aaya camera se!')
            return None
        if flip:
            frame = cv2.flip(frame, 1)
        self._update_fps()
        return frame

    def get_fps(self):
        return int(self._fps)

    def _update_fps(self):
        current_time = time.time()
        time_elapsed = current_time - self._prev_time
        if time_elapsed > 0:
            self._fps = 1 / time_elapsed
        self._prev_time = current_time

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
        print('📷 Camera released.')