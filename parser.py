import json

class LL1Parser():
    def __init__(self,grammar):
        #self.dict = tokens
        self.dict.update({'$':'$'})
        self.first = self.computeFirst(grammar)
        self.word = ''
        #self.follow = self.computeFollow(grammar,self.first)

    def printDict(self,dict):
        for k,v in dict.items():
            print(f'{k}:{v}')

    def isTerminal(self,s,grammar):
        return s not in grammar
    
    def computeFirst(self,grammar):
        EPSILON = "ε"
        first = {nt: set() for nt in grammar}

        aux = True
        while aux:
            aux = False
            for nt, productions in grammar.items():
                for prod in productions:
                    if len(prod) == 0 or prod == [EPSILON]:
                        if EPSILON not in first[nt]:
                            first[nt].add(EPSILON)
                            aux = True
                        continue
                    for s in prod:
                        if self.isTerminal(s, grammar):
                            if s not in first[nt]:
                                first[nt].add(s)
                                aux = True
                            break
                        before = len(first[nt])
                        first[nt].update(first[s] - {EPSILON})
                        after = len(first[nt])
                        if after > before:
                            aux = True

                        if EPSILON not in first[s]:
                            break
                    else:
                        if EPSILON not in first[nt]:
                            first[nt].add(EPSILON)
                            aux = True
        return first


    def computeFollow(self,grammar,first):
        pass
    
    def processInput(self):
        with open("./saida.txt", 'r') as f:
            lexico = f.read()

        tokenlist: list[str] = []

        id = 0
        while True:
            while id < len(lexico) and lexico[id] != '<':
                id+=1
            if id >= len(lexico):
                break
            
            token = lexico[id]
            charstr = False
            while True:
                id+=1
                token += lexico[id]
                if lexico[id] == '>' and not charstr:
                    break
                if (lexico[id] == '\'' or lexico[id] == '\"') and lexico[id-1] != '\\':
                    charstr = not charstr

            tokenlist.append(token)
        return tokenlist


    def parse(self):
        self.word = self.processInput()
        print(self.word)
        self.word.append('$')

        self.idx = 0
        self.lookahead = self.convert(self.word[0])
        self.resp = False

        self.Program()

        return self.resp

    def convert(self,symbol):
        if symbol in self.dict:
            return self.dick[symbol]
        return -1

    def match(self,token_type):
        if self.lookahead == token_type:
            self.idx+=1 # avança o índice de leitura
            self.lookahead = self.convert(self.word[self.idx])
        else:
            raise SyntaxError(f"ERRO: esperado {token_type}, encontrado {self.lookahead}")

    def Program(self):
        # Colocar regras aqui... Program -> Type ID Program2
        '''
            
        '''

        self.resp = True


def main():
    with open('grammar.json','r') as f:
        grammar = json.load(f)
    with open('tokens.json','r') as f:
        tokens = json.load(f)
    

    parser = LL1Parser(grammar,tokens)
    parser.parse()

    #parser.printDict(parser.first)


if __name__ == "__main__":
    main()