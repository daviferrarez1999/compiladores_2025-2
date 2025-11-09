import os
from injector import inject
import yaml

from modules.FileSystem import IFileSystem
from .ISintatico import ISintatico
from .types import LexicoModes, Token, Identifier
from typing import List, cast, Dict

LANGUAGE = 'language.yml'
TOKENS_FILE = 'private_tokens.yml'

class Sintatico(ISintatico):
    language: Dict[str, List[List [str]]]
    index: int
    currentToken: str
    buffer: str
    fs: IFileSystem
    dict: Token

    @inject
    def __init__(self, fs: IFileSystem):
        self.fs = fs
        self.startConfig()

    def loadLanguage(self) -> Token:
        """
        Carrega as configurações dos tokens privados
        """
        print("Carregando linguagem do sintático")
        file = self.fs.downloadFile(os.path.join('config', 'sintatico', LANGUAGE))
        data = yaml.safe_load(file)
        return cast(Dict[str, List[List [str]]], data)
    
    def startConfig(self):
        """
        Carrega as configurações
        """
        self.language = self.loadLanguage()

        for k,v in self.language.items():
            print(f"{k}: {v}")

        #self.dict = tokens
        self.dict = self.loadTokens()
        self.dict.update({'$':'$'})
        self.first = self.computeFirst(self.language)
        self.follow = self.computeFollow(self.language,self.first)
        self.word = ''

        print("Configurações do sintático carregadas")

    def loadTokens(self):
        print("Carregando tokens do sintático")
        file = self.fs.downloadFile(os.path.join('config', 'lexico', TOKENS_FILE))
        data = yaml.safe_load(file)
        return cast(List[Token], data)

    def nextToken(self):
        commentMode = False

    def printDict(self,dict):
        for k,v in dict.items():
            print(f'{k}:{v}')

    def isTerminal(self,s,grammar):
        return s not in grammar
    
    def computeFirst(self,grammar):
        EPSILON = "LAMBDA"
        first = {nt: set() for nt in grammar}

        aux = True
        while aux:
            aux = False
            for nt, productions in grammar.items():
                for prod in productions:
                    if prod == [EPSILON]:
                        if EPSILON not in first[nt]:
                            first[nt].add(EPSILON)
                            aux = True
                        continue
                    for s in prod:
                        if self.isTerminal(s,grammar):
                            if s not in first[nt]:
                                first[nt].add(s)
                                aux = True
                            break
                        before = len(first[nt])
                        first[nt].update(first[s]-{EPSILON})
                        after = len(first[nt])
                        if after > before:
                            aux = True

                        if EPSILON not in first[s]:
                            break
        return first


    def computeFollow(self,grammar,first):
        EPSILON = "LAMBDA"
        follow = {nt: set() for nt in grammar}
        follow['Program'].add(EPSILON)
        
        before = follow
        while True:
            for nt, productions in grammar.items():
                for prod in productions:
                    if not self.isTerminal(prod[-1],grammar):
                        for s in prod:
                            if not self.isTerminal(s,grammar):
                                follow[prod[-1]].update(follow[nt])
                    else:
                        for s in prod:
                            if self.isTerminal(s,grammar) and s != EPSILON:
                                follow[s].update(first[prod[-1]]-{EPSILON})
                        if self.isTerminal(prod[-1],grammar) and prod[-1] != EPSILON:
                            if EPSILON in first[prod[-1]]:
                                follow[s].update(follow[nt])
            if follow != before:
                before = follow
            else:
                break
        print(follow)
        input()
        return follow   
    
    def processInput(self):
        lexico = self.buffer
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
            return self.dict.get(symbol).get('output')
        return -1

    def match(self,token_type):
        if self.lookahead == token_type:
            self.idx+=1 # avança o índice de leitura
            self.lookahead = self.convert(self.word[self.idx])
        else:
            raise SyntaxError(f"ERRO: esperado {token_type}, encontrado {self.lookahead}")

    def Program(self):
        self.Type()
        self.Program_1()

    def Type(self):
        if self.lookahead == 'ID':
            self.match('ID')


    def Program_1(self):
        pass
    def ID(self):
        pass
    def IdList(self):
        pass
    def FunctionDecl(self):
        pass

    def generateOutput(self):
        return self.buffer

    def input(self, buffer):
        self.buffer = buffer
        
    def output(self) -> str:
        generatedOutput = self.parse()
        self.printDict(self.first)
        #self.fs.uploadFile(os.path.join('tmp','sintatico'), 'saida.txt', 'w', generatedOutput)
        #return generatedOutput
