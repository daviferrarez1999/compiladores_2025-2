'''
    Código da analisador semântico
'''

GLOBALS_IDS = {}
LOCALS_IDS = {}
LEVEL_IF = -1

def functionDelc(no):
    global LOCALS_IDS
    LOCALS_IDS['func'] = no

    # process
    LOCALS_IDS = {}

def IF():
    IS_IF+=1
    LOCALS_IDS['stack'] = []
    #
    ... 
    pass

def var_decl(no,scope=None):
    pass

def read_asa(filedir):
    pass

def process():
    asa = read_asa('asa.json')

    handler = {
        'VarDecl': var_decl
    }

    for no in asa:
        handler[no['type']]

    pass

def ret():
    pass