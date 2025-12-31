from .label import LabelGen
from .temp import TempGen

class C3EGenerator:
    def __init__(self,asa):
        self.asa = asa
        self.code = []
        self.temp = TempGen()
        self.label = LabelGen()
        self.loop_end_stack = []
        self.default_value = {
            "int": 0,
            "bool": 0,
            "float": 0.0,
            "char": ' '
        }

        self.aux_params = {}    # Variável auxiliar para identificar argumentos (x = a0, y = a1...)


    def print_code(self):
        print('C3E:')
        for c in self.code:
            print(c)

    def generate_code(self):
        code = []
        try:
            for decl in self.asa["Program"]:
                self.gen(decl)
            code = self.code
        except Exception as e:
            print(f"Erro:{e}")
        finally:
            self.print_code()
            return code

    def gen(self,node):
        method = f"gen_{node['type']}"
        return getattr(self,method)(node)
    
    def emmit(self,inst):
        self.code.append(inst)

    def gen_VarDecl(self,node):
        varType = node["varType"]
        id = node["id"]

        self.emmit(f"LD {id} {self.default_value[varType]}")

    def gen_ArrayDecl(self,node):
        varType = node["varType"]
        id = node["id"]
        size = node["size"]

        self.emmit(
            f"ALLOC {id} {size} {self.default_value[varType]}"
        )

    def gen_FunctionDecl(self,node):
        self.emmit("")   # Espaçamento

        id = node["id"]
        returnType = node["returnType"]
        body = node["body"]
        
        for i,p in enumerate(node["params"]):
            self.aux_params[p["id"]] = f'a{i}'

        self.emmit(f'LABEL {id}')

        for stmt in body:
            self.gen(stmt)

        # Garante que toda função terá um return
        self.emmit(f'RET {self.default_value[returnType]}')
        self.aux_params = {}

    def find_arg(self,id):
        return self.aux_params.get(id,id)

    def gen_Identifier(self,node):
        return self.aux_params.get(node["name"],node["name"])

    def gen_ArrayAccess(self,node):
        index = self.gen(node["index"])
        return f"{node["array"]}${index}"
    
    def gen_Literal(self,node):
        return node["value"]

    def gen_Assign(self,node):
        lvalue = self.gen(node["lvalue"])
        rvalue = self.gen(node["rvalue"])

        self.emmit(f"LD {lvalue} {rvalue}")

    def gen_BinaryOp(self,node):
        pass



        
    
