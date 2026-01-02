from .symbol_table import SymbolTable

class SemanticAnalyzer():
    def __init__(self,asa):
        self.asa = asa
        self.table = SymbolTable()
        self.errors = []

    def analyze(self):
        self.get_global_scope()
        self.analyze_functions()

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
        
