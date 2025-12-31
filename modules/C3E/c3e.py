'''
    Módulo que processa a ASA e gerar um código de três endereços.
'''

import json

ASA = {}

def read_asa(filedir):
    global ASA
    with open(filedir, 'r', encoding='utf-8-sig') as file:
        ASA = json.load(file)

def process():
    global ASA
    ASA = read_asa('asa.json')