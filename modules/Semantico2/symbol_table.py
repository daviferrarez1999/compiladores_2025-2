from .scope import Scope
from .symbol import Symbol

class SymbolTable():
    def __init__(self):
        self.current = Scope()

    def enter_scope(self):
        self.current = Scope(self.current)

    def exit_scope(self):
        self.current = self.current.parent

    def define(self, decl):
        symbol = self.to_symbol(decl)
        if self.lookup(symbol.name) is not None:
            return False
        self.current.symbols[symbol.name] = symbol
        return True

    def lookup(self,name):
        '''
        Busca um nome de forma recursiva na tabela de símbolos
        '''
        scope = self.current
        while scope:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None
    
    def to_symbol(self,decl):
        type = decl["type"]

        if type == "VarDecl" or type == "Param":
            return Symbol(
                name=decl["id"],
                sym_type="var",
                data_type=decl["varType"],
            )
        elif type == "ArrayDecl":
            return Symbol(
                name=decl["id"],
                sym_type="array",
                data_type=decl["varType"],
                size=decl["size"]
            )
        elif type == "FunctionDecl":
            return Symbol(
                name=decl["id"],
                sym_type="func",
                data_type=decl["returnType"],
                params=decl["params"]
            )
