from .label import LabelGen
from .temp import TempGen

class C3EGenerator:
    def __init__(self,asa):
        self.asa = asa
        self.code: list[str] = []
        self.temp = TempGen()
        self.label = LabelGen()
        self.loop_end_stack = []
        self.default_value = {
            "int": 0,
            "bool": 0,
            "float": 0.0,
            "char": ' '
        }

    def print_code(self):
        print('C3E:')
        for c in self.code:
            print(c)

    def is_number(self,val):
        if not isinstance(val, str): return val
        if '.' in val:
            try: return float(val)
            except ValueError: return None
        try: return int(val)
        except ValueError: return None

    def generate_code(self):
        '''
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
        '''
        for decl in self.asa["Program"]:
                self.gen(decl)
        self.print_code()

    def gen(self,node):
        method = f"gen_{node['type']}"
        return getattr(self,method)(node)
    
    def emit(self,inst):
        self.code.append(inst)

    def gen_VarDecl(self,node):
        varType = node["varType"]
        id = node["id"]

        self.emit(f"LD {id} {self.default_value[varType]}")

    def gen_ArrayDecl(self,node):
        varType = node["varType"]
        id = node["id"]
        size = node["size"]

        self.emit(f"ALLOC {id} {size} {self.default_value[varType]}")

    def gen_FunctionDecl(self,node):
        self.emit("")   # Espaçamento

        id = node["id"]
        returnType = node["returnType"]
        body = node["body"]

        self.emit(f'LABEL {id}')

        for i,p in enumerate(node["params"]):
            self.emit(f"LD {p["id"]} a{i}")

        for stmt in body:
            self.gen(stmt)

        # Garante que toda função terá um return
        if self.code[-1].split(' ')[0] != "RET":
            self.emit(f'RET {self.default_value[returnType]}')

    def gen_Identifier(self,node):
        return node["name"]

    def gen_ArrayAccess(self,node):
        index = self.gen(node["index"])
        return f"{node["array"]}${index}"
    
    def gen_Literal(self,node):
        return node["value"]

    def gen_Assign(self,node):
        lvalue = self.gen(node["lvalue"])
        rvalue = self.gen(node["rvalue"])

        if node["rvalue"]["type"] == "Call":
            self.emit(f"LD {lvalue} ra")
        else:
            self.emit(f"LD {lvalue} {rvalue}")

    def gen_BinaryOp(self,node):
        # Se um valor for um call, então é preciso pegar o valor no ra
        t1 = self.gen(node["lvalue"])
        if node["lvalue"]["type"] == "Call":
            t1 = self.temp.new()
            self.emit(f"LD {t1} ra")

        t2 = self.gen(node["rvalue"])
        if node["rvalue"]["type"] == "Call":
            t2 = self.temp.new()
            self.emit(f"LD {t2} ra")

        t = self.temp.new()
        op = {
            # Aritméticos
            "+":  "ADD",
            "-":  "SUB",
            "*":  "MULT",
            "/":  "DIV",

            # Relacionais
            "==": "EQ",
            "!=": "NEQ",
            "<":  "LT",
            "<=": "LE",
            ">":  "GT",
            ">=": "GE",

            # Lógicos
            "&&": "AND",
            "||": "OR"
        }[node["op"]]

        self.emit(f"{op} {t} {t1} {t2}")
        return t
    
    def gen_Return(self,node):
        self.emit(f"RET {self.gen(node["value"])}")

    def gen_If(self,node):
        label_then = self.label.new('then')
        label_else = self.label.new('else')
        label_endif = self.label.new('endif')

        # Condição
        t_cond = self.gen(node["condition"])
        self.emit(f"IF {t_cond} {label_then}")
        self.emit(f"J {label_else}")
        # Then
        self.emit(f"LABEL {label_then}")
        for stmt in node["then"]:
            self.gen(stmt)
        self.emit(f"J {label_endif}")

        # Else
        self.emit(f"LABEL {label_else}")
        for stmt in node["else"]:
            self.gen(stmt)
        
        self.emit(f"LABEL {label_endif}")
    
    def gen_Call(self,node):
        size = 0
        for arg in node["args"]:
            self.emit(f"PARAM {self.gen(arg)}")
            size+=1

        self.emit(f"CALL {node["id"]} {size}")
        return "ra"

    def gen_Print(self,node):
        value = self.gen(node["value"])
        # Verifica se value é uma string com espaços
        if not self.is_number(value):
            value = f'"{value}"'
        self.emit(f"PRINT {value}")
    
    def gen_Break(self,node):
        self.emit(f"J {self.loop_end_stack[-1]}")   # Vai para o final do último while aberto

    def gen_While(self,node):
        label_cond = self.label.new("while")
        label_body = self.label.new("body")
        label_end  = self.label.new("endwhile")

        self.loop_end_stack.append(label_end)

        self.emit(f"LABEL {label_cond}")
        t_cond = self.gen(node["condition"])
        self.emit(f"IF {t_cond} {label_body}")
        self.emit(f"J {label_end}")

        self.emit(f"LABEL {label_body}")
        for s in node["body"]:
            self.gen(s)
        self.emit(f"J {label_cond}")

        self.emit(f"LABEL {label_end}")

        self.loop_end_stack.pop()