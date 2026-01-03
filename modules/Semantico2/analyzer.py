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
                self.errors.append(f"{self.table.get_scope_name()} id {decl["id"]} já declarado.")

    def print_erros(self):
        if len(self.errors):
            for e in self.errors:
                print(e)
        else:
            print("Nenhum erro semântico encontrado.")

    def analyze_functions(self):
        for decl in self.asa["Program"]:
            if decl["type"] == "FunctionDecl":
                self.table.enter_scope(f"{decl["type"]}:{decl["id"]}")
                
                for p in decl["params"]:
                    if not self.table.define(p):
                        self.errors.append(f"{self.table.get_scope_name()} id {p["id"]} já declarado antes de {decl["id"]}.")
                
                self.analyze_Body(decl)
                self.table.exit_scope()

    def analyze_Call(self,node):
        id = node["id"]
        std = f"em Call {id}"
        res = self.table.lookup(id)
        if not res:
            self.errors.append(f"{self.table.get_scope_name()} id {id} não declarado {std}.")
            return None
        if res.sym_type != 'func':
            self.errors.append(f"{self.table.get_scope_name()} id {id} não é uma função {std}.")
            return None
        for i, arg in enumerate(node["args"]):
            paramType = self.analyze(arg)
            expectedParamType = 'number' if res.params[i]["varType"] in ['int','float','bool'] else 'char'
            if paramType != expectedParamType:
                self.errors.append(f"{self.table.get_scope_name()} parâmetro de tipo {paramType} diferente do tipo esperado {expectedParamType} {std}.")
                return None
        if res.data_type in ['int','float','bool']:
            return 'number'
        return 'char'

    def analyze_Return(self,node):
        global expectedType
        value = node["value"]
        returnType = self.analyze(value)
        if expectedType != returnType:
            self.errors.append(f"{self.table.get_scope_name()} retorno de tipo {returnType} diferente do tipo esperado {expectedType}.")
            return None
        return returnType

    def analyze_If(self,node):
        if not self.analyze(node["condition"]):
            self.errors.append(f"{self.table.get_scope_name()} Condição inválida.")
            return None
        
        self.table.enter_scope("If")
        for stmt in node["then"]:
            self.analyze(stmt)
        self.table.exit_scope()

        self.table.enter_scope("Else")
        for stmt in node["else"]:
            self.analyze(stmt)
        self.table.exit_scope()

    def analyze_Print(self,node):
        if not self.analyze(node["value"]):
            self.errors.append(f"{self.table.get_scope_name()} Tipo de valor não pode ser impresso {node["value"]["type"]}")

    def analyze_While(self,node):
        if not self.analyze(node["condition"]):
            self.errors.append(f"{self.table.get_scope_name()} Condição inválida.")
            return None
        
        self.table.enter_scope("While")
        for stmt in node["body"]:
            self.analyze(stmt)
        self.table.exit_scope()

    def analyze_Assign(self,node):
        lvalue = self.analyze(node['lvalue'])
        rvalue = self.analyze(node['rvalue'])
        if lvalue != rvalue:
            self.errors.append(f"{self.table.get_scope_name()} Tipos não são compatíveis no operador Assign.")
    
    def analyze_VarDecl(self,decl):
        if not self.table.define(decl):
            self.errors.append(f"{self.table.get_scope_name()} id {decl["id"]} já declarado.")

    def analyze_Body(self,decl):
        global expectedType
        expectedType = 'number' if decl["returnType"] in ['int','float','bool'] else 'char'

        for stmt in decl["body"]:
            self.analyze(stmt)

    def analyze_Identifier(self,node):
        id = node["name"]
        res = self.table.lookup(id)
        if not res:
            self.errors.append(f"{self.table.get_scope_name()} id {id} não declarado.")
            return None
        if res.sym_type != 'var':
            self.errors.append(f"{self.table.get_scope_name()} id {id} não é uma variável.")
            return None
        if res.data_type in ['int','float','bool']:
            return 'number'
        return 'char'

    def analyze_ArrayAccess(self,node):
        array = node["array"]
        res = self.table.lookup(array)
        if not res:
            self.errors.append(f"{self.table.get_scope_name()} id {array} não declarado.")
            return None
        if res.sym_type != 'array':
            self.errors.append(f"{self.table.get_scope_name()} id {array} não é um array.")
            return None
        index = node["index"]
        return self.analyze(index)
    
    def analyze_BinaryOp(self,node):
        rvalue = self.analyze(node["rvalue"])
        lvalue = self.analyze(node["lvalue"])


        if lvalue in ("string","char",None) or rvalue in ("string","char",None):
            self.errors.append(f"{self.table.get_scope_name()} Operação Inválida com {rvalue} {node["op"]} {lvalue}.")
            return None
        return "number"
    
    def analyze_UnaryOp(self,node):
        id = node["id"]
        if id["type"] == "Literal":
            self.errors.append(f"{self.table.get_scope_name()} Operação {node["op"]} inválida para {id["value"]}.")
            return None
        elif self.analyze(id) is None:
            self.errors.append(f"{self.table.get_scope_name()} Operação {node["op"]} inválida para {id["name"]}.")
            return None
        return "number"
    
    def analyze_Literal(self,node):
        string = str(node["value"])
        if len(string) > 0 and string[0] == "'":
            if len(string) > 3:
                return "string"
            return "char"
        return "number"