from modules import lexico
import sys

def main():
    if len(sys.argv) < 2:
        print("Nome do arquivo precisa ser fornecido")
        sys.exit(1)
    arquivo = sys.argv[1]
    print('Arquivo de entrda:',arquivo)
    print('Iniciando Léxico')
    lexico.input(arquivo)
    lexico.output()
    print('Léxico finalizado')

if __name__ == "__main__":
    main()