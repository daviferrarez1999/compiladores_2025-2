import os
from injector import inject
import yaml

from modules.FileSystem import IFileSystem
from .ISintatico import ISintatico
from .types import LexicoModes, Token, Identifier
from typing import List, cast, Dict, Optional

LANGUAGE = 'language.yml'
TOKENS_FILE = 'private_tokens.yml'
EPSILON = "LAMBDA"

# ------------------ ASA Node ------------------
class Node:
    def __init__(self, name: str, value: Optional[str] = None, children: Optional[List['Node']] = None):
        self.name = name
        self.value = value
        self.children: List[Node] = children or []

    def add(self, node: Optional['Node']):
        if node is not None:
            self.children.append(node)

    def is_leaf(self):
        return len(self.children) == 0 and self.value is not None

    def __repr__(self):
        if self.is_leaf():
            return f"{self.name}.{self.value}"
        return f"{self.name}"

def print_asa(node: Optional[Node], level: int = 0):
    if node is None:
        return
    indent = "   " * level

    if node.is_leaf():
        print(f"{indent}-{node.name}.{node.value}")
    else:
        print(f"{indent}-{node.name}")
        for c in node.children:
            if node.name == 'Expr':
                print_asa(c, level)
            else:
                print_asa(c, level+1)

# ------------------ Parser ------------------
class Sintatico(ISintatico):
    language: Dict[str, List[List [str]]]
    index: int
    currentToken: str
    buffer: str
    fs: IFileSystem
    dict: Token
    languageStack: List[str]
    errorMessage: str

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
        self.errorMessage = ""
        self.languageStack = []
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
        self.printDict(self.first)
        self.follow = self.computeFollow(self.language,self.first)
        self.printDict(self.follow)
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
        self.word.append('$')

        self.idx = 0
        self.lookahead = self.convert(self.word[0])
        # chama Program e retorna raiz da ASA
        self.ast = self.Program()

        if self.lookahead != '<EOF>':
            self.errorMessage = "EOF não encontrado"
            raise SyntaxError("EOF não encontrado")
        return self.ast

    def convert(self, symbol):
        if symbol in self.dict:
            return self.dict.get(symbol)
        return symbol

    # Helper: extrai lexema do token original (self.word[self.idx])
    def _extract_lexeme(self, raw_token: str):
        """
        raw_token examples: '<ID,main>', '<NUM,1>', '<LITERAL,\"abc\">', '<;>', '<{>'
        Return (type, lexeme) where lexeme for IDs/NUM/LITERAL is the inner lexeme (without <>).
        For simple symbols like '<;>' returns (';', None) or ('{', None).
        """
        if not raw_token:
            return (None, None)
        if raw_token.startswith('<') and raw_token.endswith('>'):
            content = raw_token[1:-1]
            # if contains comma, it's like ID,main
            if ',' in content:
                parts = content.split(',', 1)
                ttype = parts[0]
                lex = parts[1]
                return (ttype, lex)
            else:
                # single symbol inside <>
                return (content, None)
        else:
            return (raw_token, None)

    # Symbols to ignore as nodes (grouping tokens)
    IGNORED_SYMBOLS = {'(', ')', '{', '}', '[', ']'}

    def match(self, tokens: set) -> Optional[Node]:
        """
        Faz o match do próximo token com o conjunto tokens.
        Retorna:
         - Node para folhas semânticas (ID, NUM, LITERAL, true, false) com value=lexema
         - Node para operadores/símbolos relevantes (ex: '+', '||', '&&', '=', '<', '==', ',',';')
         - None para símbolos de agrupamento que não queremos na ASA (parens, braces...)
        """
        lookaheadToken = self.getLookAheadToken()
        if lookaheadToken in list(tokens):
            raw = self.word[self.idx]  # token original, ex '<ID,main>' ou '<;>'
            ttype, lex = self._extract_lexeme(raw)
            self.languageStack.append(f"Match: {self.lookahead}")
            self.idx += 1  # avança o índice de leitura
            self.lookahead = self.convert(self.word[self.idx])

            # Se for ID/NUM/LITERAL -> folha com prefixo
            if lookaheadToken in {'ID', 'NUM', 'LITERAL'}:
                # lex deve existir
                val = lex if lex is not None else ''
                return Node(lookaheadToken, value=val)
            # boolean literals may appear as tokens 'true'/'false'
            if lookaheadToken in {'true', 'false'}:
                return Node(lookaheadToken, value=lookaheadToken)
            # Se for símbolo de agrupamento -> ignorar (None)
            if lookaheadToken in self.IGNORED_SYMBOLS:
                return None
            # Caso seja símbolo/operador (ex: '+', '||', '&&', '=', '<', '>', ',', ';', etc.)
            # tratamos como nó com o próprio símbolo como nome
            return Node(lookaheadToken)
        else:
            self.errorMessage = f"ERRO: tokens esperados: {','.join(list(tokens))}. Foi encontrado {lookaheadToken}"
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
    
    def computeMatch(self, type: str) -> Optional[Node]:
        """
        Faz o computeMatch (usado para tokens compostos no arquivo de linguagem)
        Retorna o Node retornado por match (ou None)
        """
        self.languageStack.append(type)
        currentSet = self.first.get(type, set())
        return self.match(currentSet)

    def tryComputeMatch(self, type: str):
        currentSet = self.first.get(type, set())
        lookaheadToken = self.getLookAheadToken()
        return lookaheadToken in list(currentSet)

    # --- Grammar functions: agora retornam Node (ou None para lambdas) ---
    def Program(self) -> Optional[Node]:
        node = Node("Program")
        self.languageStack.append(self.Program.__name__)
        node.add(self.Type())
        node.add(self.Program1())
        return node

    def Type(self) -> Optional[Node]:
        node = Node("Type")
        node.add(self.computeMatch('Type'))
        return node

    def Program1(self) -> Optional[Node]:
        node = Node("Program1")
        node.add(self.computeMatch('Program1'))
        node.add(self.Program2())
        return node

    def Program2(self) -> Optional[Node]:
        node = Node("Program2")
        self.languageStack.append(self.Program2.__name__)
        if self.lookahead == '(':
            node.add(self.FunctionDecl())
        else:
            node.add(self.IdList())
            node.add(self.Program())
        return node
        
    def IdList(self) -> Optional[Node]:
        node = Node("IdList")
        self.languageStack.append(self.IdList.__name__)
        node.add(self.match({'ID'}))
        node.add(self.Array1())
        return node

    def FunctionDecl(self) -> Optional[Node]:
        node = Node("FunctionDecl")
        node.add(self.computeMatch('FunctionDecl'))
        node.add(self.FormalList())
        node.add(self.match({')'}))
        node.add(self.match({'{'}))
        node.add(self.VarDecl())
        node.add(self.StmtList())
        node.add(self.match({'}'}))
        node.add(self.FunctionDecl1())
        return node
       
    def FormalList(self) -> Optional[Node]:
        node = Node("FormalList")
        self.languageStack.append(self.FormalList.__name__)
        node.add(self.lambdaWrapper('_FormalList'))
        return node
    
    def _FormalList(self) -> Optional[Node]:
        node = Node("_FormalList")
        node.add(self.Type())
        node.add(self.match({'ID'}))
        node.add(self.Array())
        node.add(self.FormalRest())
        return node

    def lambdaWrapper(self, functionName) -> Optional[Node]:
        """
        Executa produções opcionais. Se a produção falhar, restaura índice e retorna None.
        """
        currentIndex = self.idx
        try:
            func = getattr(self, functionName)
            return func()
        except Exception:
            # restaura estado se falhar
            self.idx = currentIndex
            self.lookahead = self.convert(self.word[self.idx])
            # remove o último registro do languageStack se presente
            if self.languageStack:
                try:
                    self.languageStack.pop()
                except Exception:
                    pass
            return None

    def VarDecl(self) -> Optional[Node]:
        node = Node("VarDecl")
        self.languageStack.append(self.VarDecl.__name__)
        node.add(self.lambdaWrapper('_VarDecl'))
        return node

    def _VarDecl(self) -> Optional[Node]:
        node = Node("_VarDecl")
        node.add(self.Type())
        node.add(self.IdList())
        node.add(self.match({';'}))
        node.add(self.VarDecl())
        return node


    def StmtList(self) -> Optional[Node]:
        node = Node("StmtList")
        self.languageStack.append(self.StmtList.__name__)
        node.add(self.Stmt())
        node.add(self.StmtList1())
        return node

    def Stmt(self) -> Optional[Node]:
        node = Node("Stmt")
        self.languageStack.append(self.Stmt.__name__)
        la = self.lookahead
        match la:
            case 'if':
                node.add(self.match({'if'}))
                node.add(self.match({'('}))
                node.add(self.Expr())
                node.add(self.match({')'}))
                node.add(self.Stmt())
                node.add(self.match({'else'}))
                node.add(self.Stmt())
            case 'while':
                node.add(self.match({'while'}))
                node.add(self.match({'('}))
                node.add(self.Expr())
                node.add(self.match({')'}))
                node.add(self.Stmt())
            case 'break':
                node.add(self.match({'break'}))
                node.add(self.match({';'}))
            case 'print':
                node.add(self.match({'print'}))
                node.add(self.match({'('}))
                node.add(self.ExprList())
                node.add(self.match({')'}))
                node.add(self.match({';'}))
            case 'readln':
                node.add(self.match({'readln'}))
                node.add(self.match({'('}))
                node.add(self.Expr())
                node.add(self.match({')'}))
                node.add(self.match({';'}))
            case 'return':
                node.add(self.match({'return'}))
                node.add(self.Expr())
                node.add(self.match({';'}))
            case '{':
                node.add(self.match({'{'}))
                node.add(self.StmtList())
                node.add(self.match({'}'}))
            case _:
                node.add(self.Expr())
                node.add(self.match({';'}))
        return node

    def Expr(self) -> Optional[Node]:
        node = Node("Expr")
        self.languageStack.append(self.Expr.__name__)
        if self.tryComputeMatch('Primary'):
            node.add(self.Primary())
            node.add(self.AltExpr())
        else:
            node.add(self.UnaryOp())
            node.add(self.ExtraExpr())
        return node

    def Primary(self) -> Optional[Node]:
        node = Node("Primary")
        self.languageStack.append(self.Primary.__name__)
        la = self.getLookAheadToken()
        match la:
            case '(':
                node.add(self.match({'('}))
                node.add(self.Expr())
                node.add(self.match({')'}))
            case 'ID':
                node.add(self.match({'ID'}))
                node.add(self.Ident())
            case 'NUM':
                node.add(self.match({'NUM'}))
            case 'LITERAL':
                node.add(self.match({'LITERAL'}))
            case 'true':
                node.add(self.match({'true'}))
            case 'false':
                node.add(self.match({'false'}))
            case _:
                self.errorMessage = f"ERRO: unexpected token {self.lookahead}"
                raise SyntaxError(self.errorMessage)
        return node

    def Ident(self) -> Optional[Node]:
        node = Node("Ident")
        self.languageStack.append(self.Ident.__name__)
        node.add(self.lambdaWrapper('_Ident'))
        return node        
        
    def _Ident(self) -> Optional[Node]:
        node = Node("_Ident")
        node.add(self.match({'('}))
        node.add(self.ExprList())
        node.add(self.match({')'}))
        return node

    def AltExpr(self) -> Optional[Node]:
        node = Node("AltExpr")
        self.languageStack.append(self.AltExpr.__name__)
        node.add(self.lambdaWrapper('_AltExpr'))
        return node

    def _AltExpr(self) -> Optional[Node]:
        node = Node("_AltExpr")
        if self.lookahead == '[':
            node.add(self.match({'['}))
            node.add(self.Expr())
            node.add(self.match({']'}))
            node.add(self.AltExpr1())
        else:
            node.add(self.CmplExpr())
        return node     

    def AltExpr1(self) -> Optional[Node]:
        node = Node("AltExpr1")
        self.languageStack.append(self.AltExpr1.__name__)
        node.add(self.lambdaWrapper('_AltExpr1'))
        return node  

    def _AltExpr1(self) -> Optional[Node]:
        node = Node("_AltExpr1")
        node.add(self.CmplExpr())
        return node

    def CmplExpr(self) -> Optional[Node]:
        node = Node("CmplExpr")
        self.languageStack.append(self.CmplExpr.__name__)
        if self.lookahead == '=':
            node.add(self.match({'='}))
            node.add(self.Expr())
        else:
            node.add(self.OrExpr())
            node.add(self.Expr())
        return node

    def OrExpr1(self) -> Optional[Node]:
        node = Node("OrExpr1")
        self.languageStack.append(self.OrExpr1.__name__)
        node.add(self.lambdaWrapper('_OrExpr1'))
        return node

    def _OrExpr1(self) -> Optional[Node]:
        node = Node("_OrExpr1")
        node.add(self.match({'||'}))
        node.add(self.AndExpr())
        node.add(self.OrExpr1())
        return node

    def OrExpr(self) -> Optional[Node]:
        node = Node("OrExpr")
        self.languageStack.append(self.OrExpr.__name__)
        node.add(self.AndExpr())
        node.add(self.OrExpr1())
        return node

    def AndExpr(self) -> Optional[Node]:
        node = Node("AndExpr")
        self.languageStack.append(self.AndExpr.__name__)
        node.add(self.CompExpr())
        node.add(self.AndExpr1())
        return node

    def AndExpr1(self) -> Optional[Node]:
        node = Node("AndExpr1")
        self.languageStack.append(self.AndExpr1.__name__)
        node.add(self.lambdaWrapper('_AndExpr1'))
        return node
    
    def _AndExpr1(self) -> Optional[Node]:
        node = Node("_AndExpr1")
        node.add(self.match({'&&'}))
        node.add(self.CompExpr())
        node.add(self.AndExpr1())
        return node

    def CompExpr(self) -> Optional[Node]:
        node = Node("CompExpr")
        self.languageStack.append(self.CompExpr.__name__)
        node.add(self.AddExpr())
        node.add(self.CompExpr1())
        return node

    def CompExpr1(self) -> Optional[Node]:
        node = Node("CompExpr1")
        self.languageStack.append(self.CompExpr1.__name__)
        node.add(self.lambdaWrapper('_CompExpr1'))
        return node

    def _CompExpr1(self) -> Optional[Node]:
        node = Node("_CompExpr1")
        node.add(self.CompOp())
        node.add(self.AddExpr())
        node.add(self.CompExpr1())
        return node

    def CompOp(self) -> Optional[Node]:
        node = Node("CompOp")
        node.add(self.computeMatch('CompOp'))
        return node

    def AddExpr(self) -> Optional[Node]:
        node = Node("AddExpr")
        self.languageStack.append(self.AddExpr.__name__)
        node.add(self.MulExpr())
        node.add(self.AddExpr1())
        return node

    def AddExpr1(self) -> Optional[Node]:
        node = Node("AddExpr1")
        self.languageStack.append(self.AddExpr1.__name__)
        node.add(self.lambdaWrapper('_AddExpr1'))
        return node

    def _AddExpr1(self) -> Optional[Node]:
        node = Node("_AddExpr1")
        node.add(self.AddOp())
        node.add(self.MulExpr())
        node.add(self.AddExpr1())
        return node

    def AddOp(self) -> Optional[Node]:
        node = Node("AddOp")
        node.add(self.computeMatch('AddOp'))
        return node

    def MulExpr(self) -> Optional[Node]:
        node = Node("MulExpr")
        self.languageStack.append(self.MulExpr.__name__)
        node.add(self.UnaryExpr())
        node.add(self.MulExpr1())
        return node

    def MulExpr1(self) -> Optional[Node]:
        node = Node("MulExpr1")
        self.languageStack.append(self.MulExpr1.__name__)
        node.add(self.lambdaWrapper('_MulExpr1'))
        return node
    
    def _MulExpr1(self) -> Optional[Node]:
        node = Node("_MulExpr1")
        node.add(self.MulOp())
        node.add(self.UnaryExpr())
        node.add(self.MulExpr1())
        return node

    def UnaryExpr(self) -> Optional[Node]:
        node = Node("UnaryExpr")
        self.languageStack.append(self.UnaryExpr.__name__)
        node.add(self.lambdaWrapper('_UnaryExpr'))
        return node

    def _UnaryExpr(self) -> Optional[Node]:
        node = Node("_UnaryExpr")
        node.add(self.computeMatch('UnaryOp'))
        return node

    def MulOp(self) -> Optional[Node]:
        node = Node("MulOp")
        node.add(self.computeMatch('MulOp'))
        return node

    def UnaryOp(self) -> Optional[Node]:
        node = Node("UnaryOp")
        node.add(self.computeMatch('UnaryOp'))
        return node

    def ExtraExpr(self) -> Optional[Node]:
        node = Node("ExtraExpr")
        self.languageStack.append(self.ExtraExpr.__name__)
        if self.tryComputeMatch('CmplExpr'):
            node.add(self.CmplExpr())
        else:
            node.add(self.Expr())
        return node

    def ExprList(self) -> Optional[Node]:
        node = Node("ExprList")
        self.languageStack.append(self.ExprList.__name__)
        node.add(self.lambdaWrapper('_ExprList'))
        return node

    def _ExprList(self) -> Optional[Node]:
        node = Node("_ExprList")
        node.add(self.ExprListTail())
        return node

    def ExprListTail(self) -> Optional[Node]:
        node = Node("ExprListTail")
        self.languageStack.append(self.ExprListTail.__name__)
        node.add(self.Expr())
        node.add(self.ExprListTail1())
        return node

    def ExprListTail1(self) -> Optional[Node]:
        node = Node("ExprListTail1")
        self.languageStack.append(self.ExprListTail1.__name__)
        node.add(self.lambdaWrapper('_ExprListTail1'))
        return node

    def _ExprListTail1(self) -> Optional[Node]:
        node = Node("_ExprListTail1")
        node.add(self.match({','}))
        node.add(self.ExprListTail())
        return node

    def StmtList1(self) -> Optional[Node]:
        node = Node("StmtList1")
        self.languageStack.append(self.StmtList1.__name__)
        node.add(self.lambdaWrapper('_StmtList1'))
        return node

    def _StmtList1(self) -> Optional[Node]:
        node = Node("_StmtList1")
        node.add(self.Stmt())
        node.add(self.StmtList1())
        return node

    def FunctionDecl1(self) -> Optional[Node]:
        node = Node("FunctionDecl1")
        self.languageStack.append(self.FunctionDecl1.__name__)
        node.add(self.lambdaWrapper('_FunctionDecl1'))
        return node

    def _FunctionDecl1(self) -> Optional[Node]:
        node = Node("_FunctionDecl1")
        node.add(self.Program())
        return node

    def Array(self) -> Optional[Node]:
        node = Node("Array")
        self.languageStack.append(self.Array.__name__)
        node.add(self.lambdaWrapper('_Array'))
        return node

    def _Array(self) -> Optional[Node]:
        node = Node("_Array")
        node.add(self.match({'['}))
        node.add(self.match({'NUM'}))
        node.add(self.match({']'}))
        return node

    def Array1(self) -> Optional[Node]:
        node = Node("Array1")
        self.languageStack.append(self.Array1.__name__)
        node.add(self.Array())
        node.add(self.Array2())
        return node

    def Array2(self) -> Optional[Node]:
        node = Node("Array2")
        self.languageStack.append(self.Array2.__name__)
        node.add(self.lambdaWrapper('_Array2'))
        return node

    def _Array2(self) -> Optional[Node]:
        node = Node("_Array2")
        node.add(self.match({','}))
        node.add(self.match({'ID'}))
        node.add(self.Array1())
        return node

    def FormalRest(self) -> Optional[Node]:
        node = Node("FormalRest")
        self.languageStack.append(self.FormalRest.__name__)
        node.add(self.lambdaWrapper('_FormalRest'))
        return node

    def _FormalRest(self) -> Optional[Node]:
        node = Node("_FormalRest")
        node.add(self.match({','}))
        node.add(self.Type())
        node.add(self.match({'ID'}))
        node.add(self.Array())
        node.add(self.FormalRest())
        return node        

    def generateOutput(self):
        return self.buffer

    def input(self, buffer):
        self.buffer = buffer
        
    def output(self) -> Optional[Node]:
        hasError = False
        try:
            generatedAst = self.parse() 
            print_asa(generatedAst)
        except Exception:
            hasError = True       
            generatedAst = None
        finally:
            for token in self.languageStack:
                if token.startswith('Match:'):
                    print(token)
            
        if hasError:
            print(f"{self.errorMessage}")
        # retornamos a AST (ou None se erro)
        return generatedAst
