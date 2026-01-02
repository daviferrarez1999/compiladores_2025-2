from .symbol_table import SymbolTable

global expectedType
expectedType = None

class SemanticAnalyzer():
    def __init__(self,asa):
        self.asa = asa
        self.table = SymbolTable()
        self.errors = []

    def analyzeAsa(self):
        self.get_global_scope()
        self.analyze_functions()

    def analyze(self,node):
        method = f"analyze_{node['type']}"
        return getattr(self,method)(node)

    def get_global_scope(self):
        for decl in self.asa["Program"]:
            if not self.table.define(decl):
                self.errors.append(f"id {decl["id"]} já declarado.")

    def print_erros(self):
        if len(self.errors):
            for e in self.errors:
                print(e)
        else:
            print("Nenhum erro semântico encontrado.")

    def analyze_functions(self):
        for decl in self.asa["Program"]:
            if decl["type"] == "FunctionDecl":
                self.table.enter_scope()
                
                for p in decl["params"]:
                    if not self.table.define(p):
                        self.errors.append(f"id {decl["id"]} já declarado.")
                
                self.analyze_body(decl)
                self.table.exit_scope()

    def analyze_Return(self,node):
        global expectedType
        value = node["value"]
        returnType = self.analyze(value)
        if expectedType != returnType:
            self.errors.append(f"return de tipo {returnType} diferente do tipo esperado {expectedType}.")
            return None
        return returnType
    
    def analyze_Body(self,decl):
        global expectedType
        expectedType = decl["returnType"]

        for stmt in decl["body"]:
            self.analyze(stmt)

    def analyze_Identifier(self,node):
        id = node["name"]
        res = self.table.lookup(id)
        if not res:
            self.errors.append(f"id {id} não declarado.")
            return None
        if res["sym_type"] != 'var':
            self.errors.append(f"id {id} não é uma variável.")
            return None
        return res["data_type"]

    def analyze_ArrayAccess(self,node):
        array = node["array"]
        res = self.table.lookup(array)
        if not res:
            self.errors.append(f"id {array} não declarado.")
            return None
        if res["sym_type"] != 'array':
            self.errors.append(f"id {array} não é um array.")
            return None
        index = res["index"]
        return self.analyze(index)
        
    def analyze_BinaryOp(self,node):
        rvalue = self.analyze(node["rvalue"])
        lvalue = self.analyze(node["lvalue"])

        if lvalue in ("string","char",False,None) or rvalue in ("string","char",False,None):
            self.errors(f"Operação Inválida com {rvalue} {node["op"]} {lvalue}.")
            return False
        return True
    
    def analyze_UnaryOp(self,node):
        id = node["id"]
        if id["type"] == "Literal":
            self.errors.append(f"Operação {node["op"]} inválida para {id["value"]}.")
        elif self.analyze(id) is None:
            self.errors.append(f"Operação {node["op"]} inválida para {id["name"]}.")
        return True
    
    def analyze_Literal(self,node):
        str = str(node["value"])
        if str == "'":
            if len(str) > 3:
                return "string"
            return "char"
        return True