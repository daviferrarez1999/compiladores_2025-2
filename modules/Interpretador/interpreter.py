from frame import Frame
import sys
import shlex

CODE: list[list[str]] = None  # Lista de instruções
LABELS: dict[str,int] = None  # Lista de marcadores
PC = 0                        # Program Counter
STACK: list[Frame] = []       # Pilha de frames (chamadas de funções)
GLOBALS = {'ra': None}        # Variáveis globais
PARAMETERS = []               # Fila de parâmetros usado pela instrução PARAM

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

def is_number(val):
    if not isinstance(val, str): return val
    if '.' in val:
        try: return float(val)
        except ValueError: return None
    try: return int(val)
    except ValueError: return None

def to_value(id):
    global GLOBALS, STACK
    
    # id é número?
    val = is_number(id)
    if val is not None: 
        return val
        
    # id é uma posição de array?
    if '$' in id:
        name, pos = id.split('$')
        pos_val = int(to_value(pos))
        
        target = GLOBALS.get(name)
        if target is None and current_frame():
            target = current_frame().get_var(name)
        
        return target[pos_val] if target is not None else None

    # id é uma váriável global?
    if id in GLOBALS: 
        return GLOBALS[id]
    
    frame = current_frame()
    if frame:
        val = frame.get_var(id)
        if val is not None:
            # Se a variável guarda o nome de outra (alias/ponteiro), resolve recursivo
            return to_value(val) if isinstance(val, str) and val != id else val
    
    return id

def set_value(id, val):
    global GLOBALS, STACK
    
    def cast_value(old_val, new_val):
        if old_val is None: return new_val
        try:
            if isinstance(old_val, float): return float(new_val)
            
            if isinstance(old_val, int): return int(new_val)
            
            return type(old_val)(new_val)
        except (ValueError, TypeError):
            return new_val

    if '$' not in id:
        if id in GLOBALS:
            GLOBALS[id] = cast_value(GLOBALS[id], val)
        else:
            frame = current_frame()
            if frame:
                if id not in frame.variables:
                    frame.new_var(id)

                old_val = frame.get_var(id)
                GLOBALS[id] = cast_value(old_val, val) if old_val is not None else val
                frame.set_var(id, GLOBALS[id])
            else:
                GLOBALS[id] = val
    else:
        name, pos = id.split('$')
        pos = int(to_value(pos))
        
        target_array = GLOBALS.get(name)
        if target_array is None and current_frame():
            target_array = current_frame().get_var(name)
        
        if target_array is not None:
            target_array[pos] = cast_value(target_array[0], val)

def LOAD():
    global PC
    a, b = get_addresses()
    val = to_value(b)
    set_value(a, val)
    PC += 1

def ADD():
    global PC
    a, b, c = get_addresses()
    val = to_value(b) + to_value(c)
    set_value(a, val)
    PC += 1

def SUB():
    global PC
    a, b, c = get_addresses()
    val = to_value(b) - to_value(c)
    set_value(a, val)
    PC += 1

def MULT():
    global PC
    a, b, c = get_addresses()
    val = to_value(b) * to_value(c)
    set_value(a, val)
    PC += 1

def DIV():
    global PC
    a, b, c = get_addresses()
    try:
        val = to_value(b) / to_value(c)
    except ZeroDivisionError:
        val = 0
    set_value(a, val)
    PC += 1

def LABEL():
    global PC
    PC += 1

def JUMP():
    global PC
    label = get_addresses()[0]
    PC = LABELS[label]

def BEQ():
    global PC
    a,b,label = get_addresses()

    if to_value(a) == to_value(b):
        PC = LABELS[label]
    else:
        PC += 1

def BNE():
    global PC
    a,b,label = get_addresses()

    if to_value(a) != to_value(b):
        PC = LABELS[label]
    else:
        PC += 1

def BGT():
    global PC
    a,b,label = get_addresses()

    if to_value(a) > to_value(b):
        PC = LABELS[label]
    else:
        PC += 1

def BGE():
    global PC
    a,b,label = get_addresses()
    if to_value(a) >= to_value(b):
        PC = LABELS[label]
    else:
        PC += 1

def BLT():
    global PC
    a,b,label = get_addresses()
    if to_value(a) < to_value(b):
        PC = LABELS[label]
    else:
        PC += 1

def BLE():
    global PC
    a,b,label = get_addresses()
    if to_value(a) <= to_value(b):
        PC = LABELS[label]
    else:
        PC += 1

def PARAM():
    global PC, PARAMETERS
    a = get_addresses()[0]
    PARAMETERS.append(to_value(a))
    
    PC += 1

def CALL():
    global PC, PARAMETERS, STACK, LABELS
    a, b = get_addresses()
    params = {}
    for i in range(to_value(b)):
        aux = PARAMETERS.pop(0)
        params[f'a{i}'] = to_value(aux)
    PARAMETERS.clear()
    
    STACK.append(Frame(PC+1,params))
    PC = LABELS.get(a,None)

def RETURN():
    global PC, STACK, GLOBALS
    a = get_addresses()[0]
    GLOBALS['ra'] = to_value(a)
    PC = current_frame().static_link
    STACK.pop()

def PRINT():
    global PC
    a = get_addresses()[0]
    print(to_value(a))

    PC += 1

def READLN():
    global PC
    addresses = get_addresses()
    a = addresses[0]
    b = input()
    # Tenta converter input para número se aplicável
    val = is_number(b) if is_number(b) is not None else b
    set_value(a, val)
    PC += 1

def ALLOC():
    global PC, GLOBALS, STACK
    a, b, c = get_addresses()

    b = int(to_value(b))
    c = to_value(c)

    arr = [c]*b

    set_value(a, arr)
    
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
        'BEQ': BEQ,
        'BNE': BNE,
        'BGT': BGT,
        'BGE': BGE, 
        'BLT': BLT,
        'BLE': BLE,
        'PARAM': PARAM,
        'CALL': CALL,
        'RET': RETURN,
        'PRINT': PRINT,
        'READLN': READLN,
        'ALLOC': ALLOC,
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

if __name__ == "__main__":
    main()