class Symbol:
    def __init__(self, name, sym_type, data_type, size=None, params=None):
        self.name = name
        self.sym_type = sym_type      # var | func | array | param
        self.data_type = data_type    # int | float | bool | char
        self.params = params or []
        self.size = size              # arrays
        self.initialized = False
        self.used = False
