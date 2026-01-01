import sys
import json
from frame import Frame

'''
    Código da analisador semântico
'''

ASA = {}
STACK = [Frame()]
LEVEL_IF = -1

def current_frame() -> Frame:
    global STACK
    return STACK[-1] if len(STACK) else None

def get_var(id):
    global STACK
    for i in reversed(STACK):
        var = i.get_var(id)
        if var:
            return var
    return None

def valid_id(id):
    existing_previous_id = get_var(id)

    if existing_previous_id:
        raise Exception(f"Indentificador único encontrado anteriormente - {id}")

def functionDecl(id,returntype,params,body):
    global STACK

    frame = current_frame()
    
    valid_id(id)
    
    frame.new_var(id)
    frame.set_var(id,{'returnType': returntype, 'params': params})

def IF():
    
    IS_IF+=1
    # LOCALS_IDS['stack'] = []
    #
    ... 
    pass

def set_var(vartype,id,size=None):
    valid_id(id)

    frame = current_frame()
    if frame:
        if id not in frame.variables:
            frame.new_var(id)
        value = None
        match vartype:
            case 'int':
                value = 0
            case 'float':
                value = 0.0
            case 'bool':
                value = 0
            case 'char':
                value = ''

        if size:
            value = [{'value': value, 'type': vartype} for _ in range(size)]
        frame.set_var(id,value)

def computefunctionbody(id,body):
    global STACK
    func = get_var(id)
    STACK.append(Frame())
    params = func.get('params',None)
    for i in params:
        type = i.get('varType',None)
        parid = i.get('id',None)
        set_var(type,parid)

    # Adicionar parâmetros como varíaveis e chamar função statmentlist para o body
    # Após execução do statmentlist, remover o frame

    # Nova função será criada para computador o body e será executada do program

    STACK.pop()

def read_asa(filedir):
    global ASA
    with open(filedir, 'r', encoding='utf-8-sig') as file:
        ASA = json.load(file)

def Program(program):
    global GLOBAL
    for i in range(len(program)):
        print(program[i])
        
        type = program[i].get('type',None)
        match type: 
            case 'VarDecl':
                vartype = program[i].get('varType',None)
                id = program[i].get('id',None)
                set_var(vartype,id)
            case 'ArrayDecl':
                vartype = program[i].get('varType',None)
                id = program[i].get('id',None)
                size = program[i].get('size',None)
                set_var(vartype,id,size)

    for i in range(len(program)):
        print(program[i])
        
        type = program[i].get('type',None)
        match type: 
            case 'FunctionDecl':
                id = program[i].get('id',None)
                returntype = program[i].get('returnType',None)
                params = program[i].get('params',None)
                functionDecl(id,returntype,params)

    for i in range(len(program)):
        print(program[i])
        
        type = program[i].get('type',None)
        match type: 
            case 'FunctionDecl':
                id = program[i].get('id',None)
                body = program[i].get('body',None)
                computefunctionbody(id,body)

def process():
    global ASA, STACK
    args = sys.argv
    if len(args)<=1:
        return -1
    
    read_asa(args[1])

    Program(ASA.get('Program',[]))

    print(STACK)

def ret():
    pass

if __name__ == '__main__':
    process()