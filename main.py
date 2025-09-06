from modules import fileSystem
from lexico import Lexico

def main():
    print("Iniciando código....")
    print("Começando a geração do código léxico")
    lexico = Lexico()
    output = lexico.generateOutput()
    print('Imprimindo saída')
    print(output)
    print('Léxico finalizado')



if __name__ == "__main__":
    main()