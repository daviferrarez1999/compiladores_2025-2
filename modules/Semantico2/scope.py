class Scope:
    def __init__(self, parent=None):
        self.parent = parent    # parent = None se escopo é global
        self.symbols = {}
