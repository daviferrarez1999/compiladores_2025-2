from modules import lexico, sintatico
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
    print('Arquivo de entrada: ', arquivo)
    print('Iniciando Léxico')
    lexico.input(arquivo)
    buffer = lexico.output()
    print('Léxico finalizado')
    sintatico.input(buffer)
    sintatico.output()
    return None

if __name__ == "__main__":
    main()