class LabelGen:
    def __init__(self):
        self.count = 0

    def new(self, prefix="L"):
        self.count += 1
        return f"{prefix}{self.count}"
