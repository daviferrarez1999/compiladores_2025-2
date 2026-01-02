class TempGen:
    def __init__(self):
        self.count = 0

    def new(self):
        self.count += 1
        return f"*t{self.count}"
