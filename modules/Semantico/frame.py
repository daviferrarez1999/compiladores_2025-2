class Undefined:
    '''
    Classe que representa modelo apra variáveis sem valor atribuído
    '''
    pass

UNDEFINED = Undefined()

class Frame():
    def __init__(   
        self, 
        static_link=None,
        args={}
    ):
        self.static_link = static_link
        self.args = args
        self.variables = {}

    def new_var(self, id):
        if id in self.variables:
            raise Exception("ID de variável já existente no escopo.")
        self.variables[id] = UNDEFINED

    def get_var(self, id):
        val = self.variables.get(id,None)

        if val is None:
            return self.args.get(id,None)
        return val
    
    def set_var(self, id, val, pos=None):
        if id in self.args:
            if pos == None:
                self.args[id] = val
            else:
                self.args[id][pos] = val
        elif id in self.variables:
            if pos == None:
                self.variables[id] = val
            else:
                self.variables[id][pos] = val
