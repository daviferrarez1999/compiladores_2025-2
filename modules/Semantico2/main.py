import json
from .analyzer import SemanticAnalyzer

def main(filedir):
    with open(filedir, 'r', encoding='utf-8-sig') as file:
        asa = json.load(file)

    analyzer = SemanticAnalyzer(asa)
    analyzer.analyze()
    analyzer.print_erros()

if __name__ == '__main__':
    main(filedir='modules/C3E/asa.json')