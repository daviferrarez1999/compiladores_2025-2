import os
from modules import semantico, interpreter, c3e
import sys

def main():
    """
    Função principal do compilador

    sys.argv[1]: nome do arquivo de entrada de dados

    Returns:
        None
    """
    if len(sys.argv) < 2:
        print("Nome do arquivo precisa ser fornecido")
        sys.exit(1)
    arquivo = sys.argv[1]
    # print('Arquivo de entrada: ', arquivo)
    # print('Iniciando Léxico')
    # lexico.input(arquivo)
    # buffer = lexico.output()
    # print('Léxico finalizado')
    # sintatico.input(buffer)
    # sintatico.output()

    tempAsaPath = os.path.join('asa', arquivo)
    # semantico 2
    semantico.init(tempAsaPath)
    semantico.analyzeAsa()
    semantico.print_erros()

    if not semantico.has_errors(): 
        # temp > asa.json
        # c3e
        c3e.init(tempAsaPath)
        c3e.generate_code()
        fileC3E = os.path.join('tmp', 'c3e', 'c3e.txt')

        # interpreter
        # temp > saída do c3e
        interpreter(fileC3E)
    return None

if __name__ == "__main__":
    main()