from modules.Interpretador.frame import Frame
import sys
import shlex

CODE: list[list[str]] = None                    # Lista de instruções
LABELS: dict[str,int] = None                    # Lista de marcadores
PC = 0                                          # Program Counter
STACK: list[Frame] = []                         # Pilha de frames (chamadas de funções)
GLOBALS = {'$ra': {'value': None, 'type': None}} # Variáveis globais
PARAMETERS = []                                 # Fila de parâmetros usado pela instrução PARAM

def read_code(dir):
    with open(dir, 'r', encoding='utf-8-sig') as file:
        lines = file.readlines()
        
    code = []
    labels = {}
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            code.append([''])
            continue

        parts = shlex.split(line)
        if not parts:
            code.append([''])
            continue

        if '\'' in line:
            parts[1] = f'{parts[1]}'

        code.append(parts)
        
        if parts[0] == 'LABEL':
            labels[parts[1]] = i
            
    return code, labels

def current_frame():
    global STACK
    return STACK[-1] if len(STACK) else None

def code_type(idx):
    return CODE[idx][0]

def get_addresses():
    '''
    Retorna os endereços que estão no comando atual
    '''
    addresses = CODE[PC][1:] # Retorna tudo menos o tipo da instrução
    return addresses

def get_type_name(v):
    if isinstance(v, int): return 'int'
    if isinstance(v, float): return 'float'
    if isinstance(v, str): return 'char'
    if isinstance(v, list): return get_type_name(v[0])
    return None

def is_number(val):
    if not isinstance(val, str): return val
    if '.' in val:
        try: return float(val)
        except ValueError: return None
    try: return int(val)
    except ValueError: return None

def to_value(id):
    global GLOBALS, STACK
    
    val = is_number(id)
    if val is not None: return val
    
    if '.' in id:
        name, pos = id.split('.')
        pos_val = int(to_value(pos))
        
        target = GLOBALS.get(name)
        if target is None and current_frame():
            target = current_frame().get_var(name)

        target=target['value']
        
        item = target[pos_val] if target is not None else None
        return item['value'] if isinstance(item, dict) else item

    # Busca em Globais ou Frames
    res = None
    if id in GLOBALS: 
        res = GLOBALS[id]
    elif current_frame():
        res = current_frame().get_var(id)
    # Se encontramos um dicionário, retornamos apenas o valor bruto
    if isinstance(res, dict):
        return res['value']
    
    # Caso seja um ponteiro (string) ou o próprio literal
    if isinstance(res, str) and res in GLOBALS or (current_frame() and res in current_frame().variables):
        return to_value(res)
        
    return id

def set_value(id, val):
    global GLOBALS, STACK

    # Helper para realizar o casting e manter o dicionário
    def prepare_storage(old_data, new_val):
        if old_data is None or not isinstance(old_data, dict):
            # Criação inicial da variável
            return {'value': new_val, 'type': get_type_name(new_val)}
        
        # Atualização: Mantém o tipo original e faz o cast do novo valor
        t = old_data['type']
        try:
            if t == 'float': final_val = float(new_val)
            elif t == 'int': final_val = int(new_val)
            elif t == 'bool': final_val = bool(new_val)
            elif t == 'char': final_val = chr(new_val)
            else: final_val = new_val
        except:
            final_val = new_val
        
        return {'value': final_val, 'type': t}

    if '.' not in id:
        if id in GLOBALS:
            GLOBALS[id] = prepare_storage(GLOBALS[id], val)
        else:
            frame = current_frame()
            if frame:
                if id not in frame.variables:
                    frame.new_var(id)
                old = frame.get_var(id)
                data = prepare_storage(old, val)
                frame.set_var(id, data)
            else:
                GLOBALS[id] = prepare_storage(None, val)
    else:
        # Para Arrays
        name, pos = id.split('.')
        pos_idx = int(to_value(pos))
        
        target_array = GLOBALS.get(name)
        if target_array is None and current_frame():
            target_array = current_frame().get_var(name)

        target_array = target_array['value']
        
        if target_array is not None:
            # Assume-se que o array guarda dicionários em cada posição
            target_array[pos_idx] = val

def LOAD():
    global PC
    a, b = get_addresses()
    val = to_value(b)
    set_value(a, val)
    PC += 1

def LABEL():
    global PC
    PC += 1

def JUMP():
    global PC
    label = get_addresses()[0]
    PC = LABELS[label]

def PARAM():
    global PC, PARAMETERS
    a = get_addresses()[0]

    val = to_value(a)
    
    type = 'float' if isinstance(val, float) else 'int'
    if isinstance(val, str): type = 'char'
    
    PARAMETERS.append({'value': val, 'type': type})
    
    PC += 1

def CALL():
    global PC, PARAMETERS, STACK, LABELS
    a, b = get_addresses()
    
    num_params = int(to_value(b))
    
    params = {}
    for i in range(num_params):
        if PARAMETERS:
            params[f'a{i}'] = PARAMETERS.pop(0)
    
    PARAMETERS.clear()
    
    STACK.append(Frame(PC, params))
    PC = LABELS.get(a, None)

def IF():
    global PC
    cond,label = get_addresses()
    if to_value(cond) != 0:
        PC = LABELS[label]
    else:
        PC += 1

def ADD():
    BinaryOp('+')

def SUB():
    BinaryOp('-')

def MULT():
    BinaryOp('*')

def DIV():
    BinaryOp('/')

def MOD():
    BinaryOp('%')

def EQ():
    return BinaryOp('==')

def NE():
    return BinaryOp('!=')

def GT():
    return BinaryOp('>')

def LT():
    return BinaryOp('<')

def GE():
    return BinaryOp('>=')

def LE():
    return BinaryOp('<=')

def OR():
    return BinaryOp('||')

def AND():
    return BinaryOp('&&')

def BinaryOp(op):
    global PC

    a, b, c = get_addresses()
    b = to_value(b)
    c = to_value(c)

    if op == '+':
        value = b + c
    elif op == '-':
        value = b - c
    elif op == '*':
        value = b * c
    elif op == '/':
        try:
            value = b / c
        except ZeroDivisionError:
            value = 0
    elif op == '%':
        value = int(b % c)
    elif op == '==':
        value = int(b == c)
    elif op == '!=':
        value = int(b != c)
    elif op == '>':
        value = int(b > c)
    elif op == '<':
        value = int(b < c)
    elif op == '>=':
        value = int(b >= c)
    elif op == '<=':
        value = int(b <= c)
    elif op == '||':
        value = int(b == 1 or c == 1)
    elif op == '&&':
        value = int(b == 1 and c == 1)
    else:
        raise ValueError(f'Operador binário desconhecido: {op}')

    set_value(a, value)
    PC += 1

def RETURN():
    global PC, STACK, GLOBALS
    a = get_addresses()[0]
    
    val = to_value(a)
    type = 'float' if isinstance(val, float) else 'int'
    if isinstance(val, str): type = 'char'
    
    GLOBALS['$ra'] = {'value': val, 'type': type}

    static_link = current_frame().static_link
    if static_link:
        static_link+=1  
    PC = static_link
    STACK.pop()

def PRINT():
    global PC
    a = get_addresses()[0]
    text = str(to_value(a))

    if text[0] == '\'':
        text = text[1:-1]
    print(text.replace('\\n','\n'),end='')

    PC += 1

def READLN():
    global PC
    addresses = get_addresses()
    a = addresses[0]
    b = input()
    val = (b) if is_number(b) is not None else b
    set_value(a, val)
    PC += 1

def ALLOC():
    global PC, GLOBALS, STACK
    id, b, c = get_addresses()

    size = int(to_value(b))
    initial_val = to_value(c)

    arr = [initial_val]*size
    
    if id in GLOBALS:
        GLOBALS[id] = {'value': arr, 'type': get_type_name(arr)}
    else:
        frame = current_frame()
        if frame:
            if id not in frame.variables:
                frame.new_var(id)
            data = {'value': arr, 'type': get_type_name(arr)}
            frame.set_var(id, data)
        else:
            GLOBALS[id] = {'value': arr, 'type': get_type_name(arr)}

    PC += 1

def DFB():
    global PC, GLOBALS, STACK
    id = get_addresses()[0]

    if id in GLOBALS:
        GLOBALS[id]['type'] = 'bool'
    else:
        frame = current_frame()
        if frame:
            frame.variables[id]['type'] = 'bool'
        else:
            GLOBALS[id]['type'] = 'bool'

    PC += 1

def DECL():
    global PC

    id, val = get_addresses()
    val = to_value(val)
    
    if id in GLOBALS:
        GLOBALS[id] = {'value': val, 'type': get_type_name(val)}
    else:
        frame = current_frame()
        if frame:
            if id not in frame.variables:
                frame.new_var(id)
            data = {'value': val, 'type': get_type_name(val)}
            frame.set_var(id, data)
        else:
            GLOBALS[id] = {'value': val, 'type': get_type_name(val)}

    PC += 1
    
def main():
    HANDLER = {
        'LD': LOAD,
        'ADD': ADD,
        'SUB': SUB,
        'MULT': MULT,
        'DIV': DIV,
        'LABEL': LABEL,
        'J': JUMP,
        'EQ' : EQ,
        'NE' : NE,
        'GT' : GT,
        'LT' : LT,
        'GE' : GE,
        'LE' : LE,
        'OR' : OR,
        'AND': AND,
        'IF' : IF,
        'MOD': MOD,
        'PARAM': PARAM,
        'CALL': CALL,
        'RET': RETURN,
        'PRINT': PRINT,
        'READLN': READLN,
        'ALLOC': ALLOC,
        'DFB': DFB,
        'DECL': DECL,
        '': None
    }
    args = sys.argv
    if len(args)<=1:
        return
    global CODE, LABELS, PC
    CODE, LABELS = read_code(args[1])
    PC = 0

    while PC < len(CODE) and code_type(PC) != 'LABEL':
        func = code_type(PC)
        if func:
            HANDLER[code_type(PC)]()
        else:
            PC += 1

    STACK.append(Frame())
    PC = LABELS.get('main',None)

    while PC is not None and PC < len(CODE):
        func = code_type(PC)
        if func:
            HANDLER[code_type(PC)]()
        else:
            PC += 1

def init(asaPath):

    HANDLER = {
        'LD': LOAD,
        'ADD': ADD,
        'SUB': SUB,
        'MULT': MULT,
        'DIV': DIV,
        'LABEL': LABEL,
        'J': JUMP,
        'EQ' : EQ,
        'NE' : NE,
        'GT' : GT,
        'LT' : LT,
        'GE' : GE,
        'LE' : LE,
        'OR' : OR,
        'AND': AND,
        'IF' : IF,
        'MOD': MOD,
        'PARAM': PARAM,
        'CALL': CALL,
        'RET': RETURN,
        'PRINT': PRINT,
        'READLN': READLN,
        'ALLOC': ALLOC,
        'DFB': DFB,
        'DECL': DECL,
        '': None
    }

    global CODE, LABELS, PC
    CODE, LABELS = read_code(asaPath)
    PC = 0

    while PC < len(CODE) and code_type(PC) != 'LABEL':
        func = code_type(PC)
        if func:
            HANDLER[code_type(PC)]()
        else:
            PC += 1

    STACK.append(Frame())
    PC = LABELS.get('main',None)

    while PC is not None and PC < len(CODE):
        func = code_type(PC)
        if func:
            HANDLER[code_type(PC)]()
        else:
            PC += 1

if __name__ == "__main__":
    main()