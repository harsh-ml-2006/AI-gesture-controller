# =============================================================================
# utils/smoother.py — Cursor/value smoothing ke liye
# =============================================================================
# Problem: Haath thoda bhi hile toh cursor bahut zyada kaampega (jittery).
# Solution: Naya value seedha use nahi karte. Pehle wali position ko bhi
#           thoda dhyan dete hain. Isse movement smooth lagti hai.
#
# Technique: Weighted Moving Average
#   smoothed_value = (old_value * weight) + (new_value * (1 - weight))
#   weight = 0.7 matlab 70% old value, 30% new value = zyada smooth
#   weight = 0.3 matlab 30% old value, 70% new value = zyada responsive
# =============================================================================


class Smoother:
    """
    Ek value ko smoothly change karne ke liye.
    Cursor movement ya volume/brightness ke liye useful hai.
    """

    def __init__(self, smoothing_factor=0.7):
        """
        Parameters:
            smoothing_factor : float (0.0 to 1.0)
                - Jitna zyada, utna smooth (but thoda slower response)
                - Recommended: 0.5 to 0.8
        """
        self.smoothing_factor = smoothing_factor
        self.smoothed_x = 0    # X axis ka pehla smoothed value
        self.smoothed_y = 0    # Y axis ka pehla smoothed value

    def smooth(self, new_x, new_y):
        """
        Naye raw coordinates ko smooth karke return karta hai.

        Parameters:
            new_x, new_y : int/float — Camera se aaya raw position

        Returns:
            (smoothed_x, smoothed_y) : int — Smooth position
        """

        # Formula: new_smooth = (old * factor) + (new * (1 - factor))
        self.smoothed_x = int(
            self.smoothed_x * self.smoothing_factor +
            new_x * (1 - self.smoothing_factor)
        )
        self.smoothed_y = int(
            self.smoothed_y * self.smoothing_factor +
            new_y * (1 - self.smoothing_factor)
        )

        return self.smoothed_x, self.smoothed_y

    def smooth_value(self, new_value):
        """
        Sirf ek single value (jaise volume level) ko smooth karta hai.
        """
        self.smoothed_x = int(
            self.smoothed_x * self.smoothing_factor +
            new_value * (1 - self.smoothing_factor)
        )
        return self.smoothed_x

    def reset(self, x=0, y=0):
        """
        Smoother ko reset karta hai — mode change hone par useful hai.
        """
        self.smoothed_x = x
        self.smoothed_y = y
