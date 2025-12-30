from frame import Frame
import sys
import shlex

CODE: list[list[str]] = None                    # Lista de instruções
LABELS: dict[str,int] = None                    # Lista de marcadores
PC = 0                                          # Program Counter
STACK: list[Frame] = []                         # Pilha de frames (chamadas de funções)
GLOBALS = {'ra': {'value': None, 'type': None}} # Variáveis globais
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
    
    val = is_number(id)
    if val is not None: return val
    
    if '$' in id:
        name, pos = id.split('$')
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
    
    # Helper para definir o nome do tipo
    def get_type_name(v):
        if isinstance(v, float): return 'float'
        if isinstance(v, int): return 'int'
        if isinstance(v, list): return 'array'
        return 'char'

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
            elif t == 'char': final_val = chr(new_val)
            else: final_val = new_val
        except:
            final_val = new_val
            
        return {'value': final_val, 'type': t}

    if '$' not in id:
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
        name, pos = id.split('$')
        pos_idx = int(to_value(pos))
        
        target_array = GLOBALS.get(name)
        if target_array is None and current_frame():
            target_array = current_frame().get_var(name)

        target_array = target_array['value']
        
        if target_array is not None:
            # Assume-se que o array guarda dicionários em cada posição
            target_array[pos_idx] = prepare_storage(target_array[pos_idx], val)

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
    
    STACK.append(Frame(PC+1, params))
    PC = LABELS.get(a, None)

def RETURN():
    global PC, STACK, GLOBALS
    a = get_addresses()[0]
    
    val = to_value(a)
    type = 'float' if isinstance(val, float) else 'int'
    if isinstance(val, str): type = 'char'
    
    GLOBALS['ra'] = {'value': val, 'type': type}
    
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
    
    val = is_number(b) if is_number(b) is not None else b
    set_value(a, val)
    PC += 1

def ALLOC():
    global PC, GLOBALS, STACK
    a, b, c = get_addresses()

    size = int(to_value(b))
    initial_val = to_value(c)
    type_name = 'float' if isinstance(initial_val, float) else 'int'
    
    arr = [{'value': initial_val, 'type': type_name} for _ in range(size)]

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