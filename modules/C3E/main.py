import json
from .generator import C3EGenerator

def main(filedir):
    with open(filedir, 'r', encoding='utf-8-sig') as file:
        asa = json.load(file)

    generator = C3EGenerator(asa)
    code = generator.generate_code()

if __name__ == '__main__':
    main(filedir='modules/C3E/asa.json')