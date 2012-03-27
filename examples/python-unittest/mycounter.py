class MyCounter:
    def __init__(self):
        self.value = 0

    def inc(self):
        self.value += 1

    def reset(self):
        # self.value = self.value / self.value - 1
        self.value = 0
    
    def count(self):
        return self.value
