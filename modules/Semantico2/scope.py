class Scope:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent    # parent = None se escopo é global
        self.symbols = {}
