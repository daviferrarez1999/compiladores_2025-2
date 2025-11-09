import os
from injector import inject
import yaml

from modules.FileSystem import IFileSystem
from .ISintatico import ISintatico
from .types import LexicoModes, Token, Identifier
from typing import List, cast, Dict

LANGUAGE = 'language.yml'
TOKENS_FILE = 'private_tokens.yml'
EPSILON = "LAMBDA"

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
        tokens = self.loadTokens()
        self.dict = {}
        for key in tokens:
            value = tokens.get(key).get('output')
            self.dict.update({value: key})
        self.dict.update({'$':'$'})
        self.first = self.computeFirst(self.language)
        print(self.first)
        self.follow = self.computeFollow(self.language,self.first)
        self.word = ''

        print("Configurações do sintático carregadas")

    def loadTokens(self):
        print("Carregando tokens do léxico para o sintático")
        file = self.fs.downloadFile(os.path.join('config', 'lexico', TOKENS_FILE))
        data = yaml.safe_load(file)
        return cast(List[Token], data)

    def printDict(self,dict):
        for k,v in dict.items():
            print(f'{k}:{v}')

    def isTerminal(self,s,grammar):
        return s not in grammar
    
    def computeFirst(self,grammar):
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
        initial = 'Program'
        follow = {nt: set() for nt in grammar}
        follow[initial] = {'$'}
        aux = True
        while aux:
            aux = False
            vis = set()
            fila = [initial]
            while len(fila):
                nt = fila.pop(0)
                for prod in grammar[nt]:
                    for idx in range(len(prod)):
                        s = prod[idx]
                        if not self.isTerminal(s,grammar):
                            if s not in vis:
                                vis.add(s)
                                fila.append(s)
                            next = idx+1
                            while -1 < next < len(prod):
                                if self.isTerminal(prod[next],grammar) and prod[next] != EPSILON:
                                    before = len(follow[s])
                                    follow[s].add(prod[next])
                                    if len(follow[s]) != before:
                                        aux = True
                                    next = -1
                                else:
                                    if prod[next] != EPSILON:
                                        before = len(follow[s])
                                        follow[s].update(first[prod[next]]-{EPSILON})
                                        if len(follow[s]) != before:
                                            aux = True
                                    if prod[next] == EPSILON or EPSILON in first[prod[next]]:
                                        next+=1
                                    else:
                                        next=-1
                            if next >= len(prod):
                                before = len(follow[s])
                                follow[s].update(follow[nt])
                                if len(follow[s]) != before:
                                    aux = True
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
        #print(self.word)
        self.word.append('$')

        self.idx = 0
        self.lookahead = self.convert(self.word[0])
        self.resp = False

        self.Program()

        return self.resp

    def computeMatchTest(self, type: str):
        print(type)
        currentSet = self.first.get(type, set())
        self.match(currentSet)

    def convert(self, symbol):
        if symbol in self.dict:
            return self.dict.get(symbol)
        return symbol

    def match(self, tokens: set):
        lookaheadToken = self.getLookAheadToken()
        if lookaheadToken in list(tokens):
            print(f"Match: {self.lookahead}")
            self.idx+=1 # avança o índice de leitura
            self.lookahead = self.convert(self.word[self.idx])
        else:
            raise SyntaxError(f"ERRO: tokens esperados: {','.join(list(tokens))}. Foi encontrado {lookaheadToken}")

    def getLookAheadToken(self):
        if ',' in self.lookahead:
            # Caso em que é um token interno Precisamos realizar o split do token
            #<ID,main> precisamos extrair o ID
            index = 1
            current = self.lookahead[index] # vamos pular o <
            token = ""
            while current != ',':
                token+=current
                index+=1
                current=self.lookahead[index]
            return token
        else:
            return self.lookahead          
    
    def computeMatch(self, type: str):
        print(type)
        currentSet = self.first.get(type, set())
        self.match(currentSet)

    def tryComputeMatch(self, type: str):
        currentSet = self.first.get(type, set())
        lookaheadToken = self.getLookAheadToken()
        return lookaheadToken in list(currentSet)

    def Program(self):
        print(self.Program.__name__)
        self.Type()
        self.Program1()

    def Type(self):
        self.computeMatch('Type')

    def Program1(self):
        self.computeMatch('Program1')
        self.Program2()

    def Program2(self):
        print(self.Program2.__name__)
        if self.lookahead == '(':
            self.FunctionDecl()
        else:
            self.IdList()
            self.Program()
        
    def IdList(self):
        print(self.IdList.__name__)
        self.match({'ID'})
        self.Array1()

    def FunctionDecl(self):
        self.computeMatch('FunctionDecl')
        self.FormalList()
        self.match({')'})
        self.match({'{'})
        self.VarDecl()
        self.StmtList()
        self.match({'}'})
        self.FunctionDecl1()
       
    def FormalList(self):
        print(self.FormalList.__name__)
        self.lambdaWrapper('_FormalList')
    
    def _FormalList(self):
        self.Type()
        self.match({'ID'})
        self.Array()
        self.FormalRest()

    def lambdaWrapper(self, functionName):
        currentIndex = self.idx
        try:
            func = getattr(self, functionName)
            func()
        except:
            print("LAMBDA")
            self.idx = currentIndex
            self.lookahead = self.convert(self.word[self.idx])

    def VarDecl(self):
        print(self.VarDecl.__name__)
        self.lambdaWrapper('_VarDecl')

    def _VarDecl(self):
        self.Type()
        self.IdList()
        self.match({';'})
        self.VarDecl()


    def StmtList(self):
        print(self.StmtList.__name__)
        self.Stmt()
        self.StmtList1()

    def Stmt(self):
        print(self.Stmt.__name__)
        match self.lookahead:
            case 'if':
                self.match({'if'})
                self.match({'('})
                self.Expr()
                self.match({')'})
                self.Stmt()
                self.match({'else'})
                self.Stmt()
            case 'while':
                self.match({'while'})
                self.match({'('})
                self.Expr()
                self.match({')'})
                self.Stmt()
            case 'break':
                self.match({'break'})
                self.match({';'})
            case 'print':
                self.match({'print'})
                self.match({'('})
                self.ExprList()
                self.match({')'})
                self.match({';'})
            case 'readln':
                self.match({'readln'})
                self.match({'('})
                self.Expr()
                self.match({')'})
                self.match({';'})
            case 'return':
                self.match({'return'})
                self.Expr()
                self.match({';'})
            case '{':
                self.match({'{'})
                self.StmtList()
                self.match({'}'})
            case _:
                self.Expr()
                self.match({';'})

    def Expr(self):
        print(self.Expr.__name__)
        if self.tryComputeMatch('Primary'):
            self.Primary()
            self.AltExpr()
        else:
            self.UnaryOp()
            self.ExtraExpr()

    def Primary(self):
        print(self.Primary.__name__)
        match self.getLookAheadToken():
            case '(':
                self.match({'('})
                self.Expr()
                self.match({')'})
            case 'ID':
                self.match({'ID'})
                self.Ident()
            case 'NUM':
                self.match({'NUM'})
            case 'LITERAL':
                self.match({'LITERAL'})
            case 'true':
                self.match({'true'})
            case 'false':
                self.match({'false'})
            case _:
                raise SyntaxError(f"ERRO: unexpected token {self.lookahead}")

    def Ident(self):
        print(self.Ident.__name__)
        self.lambdaWrapper('_Ident')        
        
    def _Ident(self):
        self.match({'('})
        self.ExprList()
        self.match({')'})

    def AltExpr(self):
        print(self.AltExpr.__name__)
        self.lambdaWrapper('_AltExpr')

    def _AltExpr(self):
        if self.lookahead == '[':
            self.match({'['})
            self.Expr()
            self.match({']'})
            self.AltExpr1()
        else:
            self.CmplExpr()     

    def AltExpr1(self):
        print(self.AltExpr1.__name__)
        self.lambdaWrapper('_AltExpr1')  

    def _AltExpr1(self):
        self.CmplExpr()

    def CmplExpr(self):
        print(self.CmplExpr.__name__)
        if self.lookahead == '=':
            self.match({'='})
            self.Expr()
        else:
            self.OrExpr()
            self.Expr()

    def OrExpr1(self):
        print(self.OrExpr1.__name__)
        self.lambdaWrapper('_OrExpr1')

    def _OrExpr1(self):
        self.match({'||'})
        self.AndExpr()
        self.OrExpr1()

    def OrExpr(self):
        print(self.OrExpr.__name__)
        self.AndExpr()
        self.OrExpr1()

    def AndExpr(self):
        print(self.AndExpr.__name__)
        self.CompExpr()
        self.AndExpr1()

    def AndExpr1(self):
        print(self.AndExpr1.__name__)
        self.lambdaWrapper('_AndExpr1')
    
    def _AndExpr1(self):
        self.match('&&')
        self.CompExpr()
        self.AndExpr1()

    def CompExpr(self):
        print(self.CompExpr.__name__)
        self.AddExpr()
        self.CompExpr1()

    def CompExpr1(self):
        print(self.CompExpr1.__name__)
        self.lambdaWrapper('_CompExpr1')

    def _CompExpr1(self):
        self.CompOp()
        self.AddExpr()
        self.CompExpr1()

    def CompOp(self):
        self.computeMatch('CompOp')

    def AddExpr(self):
        print(self.AddExpr.__name__)
        self.MulExpr()
        self.AddExpr1()

    def AddExpr1(self):
        print(self.AddExpr1.__name__)
        self.lambdaWrapper('_AddExpr1')

    def _AddExpr1(self):
        self.AddOp()
        self.MulExpr()
        self.AddExpr1()

    def AddOp(self):
        self.computeMatch('AddOp')

    def MulExpr(self):
        print(self.MulExpr.__name__)
        self.UnaryExpr()
        self.MulExpr1()

    def MulExpr1(self):
        print(self.MulExpr1.__name__)
        self.lambdaWrapper('_MulExpr1')
    
    def _MulExpr1(self):
        self.MulOp()
        self.UnaryExpr()
        self.MulExpr1()

    def UnaryExpr(self):
        print(self.UnaryExpr.__name__)
        self.lambdaWrapper('_UnaryExpr')

    def _UnaryExpr(self):
        self.computeMatch('UnaryOp')

    def MulOp(self):
        self.computeMatch('MulOp')

    def UnaryOp(self):
        self.computeMatch('UnaryOp')

    def ExtraExpr(self):
        print(self.ExtraExpr.__name__)
        if self.tryComputeMatch('CmplExpr'):
            self.CmplExpr()
        else:
            self.Expr()

    def ExprList(self):
        print(self.ExprList.__name__)
        self.lambdaWrapper('_ExprList')

    def _ExprList(self):
        self.ExprListTail()

    def ExprListTail(self):
        print(self.ExprListTail.__name__)
        self.lambdaWrapper('_ExprListTail')

    def _ExprListTail(self):
        self.Expr()
        self.ExprListTail1()

    def ExprListTail1(self):
        print(self.ExprListTail1.__name__)
        self.lambdaWrapper('_ExprListTail1')

    def _ExprListTail1(self):
        self.match({','})
        self.ExprListTail()

    def StmtList1(self):
        print(self.StmtList1.__name__)
        self.lambdaWrapper('_StmtList1')

    def _StmtList1(self):
        self.Stmt()
        self.StmtList1() 

    def FunctionDecl1(self):
        print(self.FunctionDecl1.__name__)
        self.lambdaWrapper('_FunctionDecl1')

    def _FunctionDecl1(self):
        self.Program()

    def Array(self):
        print(self.Array.__name__)
        self.lambdaWrapper('_Array')

    def _Array(self):
        self.match({'['})
        self.match({'NUM'})
        self.match({']'})

    def Array1(self):
        print(self.Array1.__name__)
        self.Array()
        self.Array2()

    def Array2(self):
        print(self.Array2.__name__)
        self.lambdaWrapper('_Array2')

    def _Array2(self):
        self.match({','})
        self.match({'ID'})
        self.Array1()

    def FormalRest(self):
        print(self.FormalRest.__name__)
        self.lambdaWrapper('_FormalRest')

    def _FormalRest(self):
        self.match({','})
        self.Type()
        self.match({'ID'})
        self.Array()
        self.FormalRest()        

    def generateOutput(self):
        return self.buffer

    def input(self, buffer):
        self.buffer = buffer
        
    def output(self) -> str:
        print("\nFirts:")
        self.printDict(self.first)
        print("\nFollow:")
        self.printDict(self.follow)
        generatedOutput = self.parse()
        #self.fs.uploadFile(os.path.join('tmp','sintatico'), 'saida.txt', 'w', generatedOutput)
        #return generatedOutput
