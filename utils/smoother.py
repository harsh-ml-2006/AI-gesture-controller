class Smoother:

    def __init__(self, smoothing_factor=0.7):
        self.smoothing_factor = smoothing_factor
        self.smoothed_x = 0
        self.smoothed_y = 0

    def smooth(self, new_x, new_y):
        self.smoothed_x = int(self.smoothed_x * self.smoothing_factor + new_x * (1 - self.smoothing_factor))
        self.smoothed_y = int(self.smoothed_y * self.smoothing_factor + new_y * (1 - self.smoothing_factor))
        return (self.smoothed_x, self.smoothed_y)

    def smooth_value(self, new_value):
        self.smoothed_x = int(self.smoothed_x * self.smoothing_factor + new_value * (1 - self.smoothing_factor))
        return self.smoothed_x

    def reset(self, x=0, y=0):
        self.smoothed_x = x
        self.smoothed_y = y