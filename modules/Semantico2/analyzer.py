from .symbol_table import SymbolTable

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
    
    def analyze_body(self,decl):
        returnType = decl["returnType"]

        for stmt in decl["body"]:
            pass

    def analyze_Identifier(self,node):
        id = node["name"]
        res = self.table.lookup(id)
        if not res:
            self.errors.append(f"id {id} não declarado.")
            return None
        return res["data_type"]

    def analyze_ArrayAccess(self,node):
        array = node["array"]
        res = self.table.lookup(array)
        if not res:
            self.errors.append(f"array {id} não declarado.")
            return None
        index = res["index"]
        return self.analyze(index)
        
