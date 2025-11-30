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

class Node:

    def __init__(self, name: str, value: Optional[str] = None, children: Optional[List['Node']] = None):
        self.name = name
        self.value = value
        self.children: List[Node] = children or []
        self.parent: Node | None = None

    def add(self, node: Optional['Node']):
        if node is not None:
            node.setParent(self)
            self.children.append(node)

    def prepend(self, node: Optional['Node']):
        if node is not None:
            self.children.insert(0, node)

    def getParent(self):
        if self.parent:
            return self.parent
        
    def setParent(self, node: None):
        self.parent = node

    def is_leaf(self):
        return len(self.children) == 0 and self.value is not None
    
    def is_printable(self):
        return self.name in ['ID']

    def __repr__(self):
        if self.is_leaf():
            return f"{self.name}.{self.value}"
        return f"{self.name}"

class Sintatico(ISintatico):
    language: Dict[str, List[List [str]]]
    index: int
    currentToken: str
    buffer: str
    fs: IFileSystem
    dict: Token
    lexicoTokens: Token
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
        self.lexicoTokens = tokens
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

    def print_asa(self,node: Optional[Node], level: int = 0):
        
        if node is None:
            return
        indent = "   " * level
        
        if node.is_leaf():
            print(f"{indent}-{self.convert_to_lexic_token(node.name)}.{node.value}")
        else:
            print(f"{indent}-{self.convert_to_lexic_token(node.name)}")
            for c in node.children:
                self.print_asa(c, level+1)

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
        root = Node("ROOT")
        root.add(self.Program(root))
        self.ast = root

        if self.lookahead != '<EOF>':
            self.errorMessage = "EOF não encontrado"
            raise SyntaxError("EOF não encontrado")
        return self.ast

    def convert(self, symbol):
        if symbol in self.dict:
            return self.dict.get(symbol)
        return symbol

    def convert_to_lexic_token(self, symbol):
        if symbol in self.lexicoTokens:
            return self.lexicoTokens.get(symbol).get('output')[1:-1]
        return symbol

    def _extract_lexeme(self, raw_token: str):
        if not raw_token:
            return (None, None)
        if raw_token.startswith('<') and raw_token.endswith('>'):
            content = raw_token[1:-1]
            if ',' in content:
                parts = content.split(',', 1)
                ttype = parts[0]
                lex = parts[1]
                return (ttype, lex)
            else:
                return (content, None)
        else:
            return (raw_token, None)

    IGNORED_SYMBOLS = {'(', ')', '{', '}'}

    def match(self, tokens: set) -> Optional[Node]:
        lookaheadToken = self.getLookAheadToken()
        if lookaheadToken in list(tokens):
            raw = self.word[self.idx]
            ttype, lex = self._extract_lexeme(raw)
            self.languageStack.append(f"Match: {self.lookahead}")
            self.idx +=1
            self.lookahead = self.convert(self.word[self.idx])

            if lookaheadToken in {'ID', 'NUM', 'LITERAL'}:
                val = lex if lex is not None else ''
                return Node(lookaheadToken, value=val)
            if lookaheadToken in {'true', 'false'}:
                return Node(lookaheadToken, value=lookaheadToken)
            if lookaheadToken in self.IGNORED_SYMBOLS:
                return None
            return Node(lookaheadToken)
        else:
            self.errorMessage = f"ERRO: tokens esperados: {','.join(list(tokens))}. Foi encontrado {lookaheadToken}"
            raise SyntaxError(f"ERRO: tokens esperados: {','.join(list(tokens))}. Foi encontrado {lookaheadToken}")

    def getLookAheadToken(self):
        if ',' in self.lookahead and len(self.lookahead) > 1:
            index = 1
            current = self.lookahead[index]
            token = ""
            while current != ',':
                token+=current
                index+=1
                current=self.lookahead[index]
            return token
        else:
            return self.lookahead          
    
    def computeMatch(self, type: str) -> Optional[Node]:
        self.languageStack.append(type)
        currentSet = self.first.get(type, set())
        return self.match(currentSet)

    def tryComputeMatch(self, type: str):
        currentSet = self.first.get(type, set())
        lookaheadToken = self.getLookAheadToken()
        return lookaheadToken in list(currentSet)

    def Program(self, node: Node | None = None) -> Optional[Node]:
        programNode = Node("Program")
        programNode.setParent(node)
        self.languageStack.append(self.Program.__name__)
        varOrFunc = Node("VarDecl or FunctionDecl")
        varOrFunc.setParent(programNode)
        self.Type(varOrFunc)
        self.Program1(varOrFunc)
        programNode.prepend(varOrFunc)
        return programNode

    def Type(self, node: Node) -> Optional[Node]:
        typeNode = Node("Type")
        typeMatch = self.computeMatch('Type')
        typeNode.add(typeMatch)
        node.add(typeNode)
        return typeNode

    def Program1(self, node: Node) -> Optional[Node]:
        idNode = self.match({"ID"})
        node.add(idNode)
        self.Program2(node)
        return idNode

    def Program2(self, node: Node) -> Optional[Node]:
        self.languageStack.append(self.Program2.__name__)
        if self.lookahead == '(':
            node.name = self.FunctionDecl.__name__
            self.FunctionDecl(node)
        else:
            node.name = self.VarDecl.__name__
            self.Array1(node)
            self.match({";"})
            parentNode = node.getParent().getParent()
            newProgram = self.Program(parentNode)
            parentNode.prepend(newProgram)

        return node
        
    def IdList(self, node: Node) -> Optional[Node]:
        self.languageStack.append(self.IdList.__name__)
        node.add(self.match({'ID'}))
        self.Array1(node)
        return node

    def FunctionDecl(self, node: Node) -> Optional[Node]:
        self.match({'('})
        self.FormalList(node)
        self.match({')'})
        self.match({'{'})
        self.VarDecl(node)
        stmtList = self.StmtList()
        for c in stmtList.children:
            node.add(c)
        self.match({'}'})
        self.FunctionDecl1(node.getParent())
        return node
       
    def FormalList(self, node: Node) -> Optional[Node]:
        formalListNode = Node("FormalList")
        self.languageStack.append(self.FormalList.__name__)
        lambdaNode = self.lambdaWrapper('_FormalList')
        if lambdaNode and len(lambdaNode.children):
            for c in lambdaNode.children:
                formalListNode.add(c)
        node.add(formalListNode)
        return node
    
    def _FormalList(self) -> Optional[Node]:
        node = Node("_FormalList")
        self.Type(node)
        node.add(self.match({'ID'}))
        self.Array(node)
        self.FormalRest(node)
        return node

    def lambdaWrapper(self, functionName) -> Optional[Node]:
        currentIndex = self.idx
        try:
            func = getattr(self, functionName)
            return func()
        except Exception:
            self.idx = currentIndex
            self.lookahead = self.convert(self.word[self.idx])
            if self.languageStack:
                try:
                    self.languageStack.pop()
                except Exception:
                    pass
            return None

    def VarDecl(self, node: Node) -> Optional[Node]:
        varDeclNode = Node("VarDecl")
        self.languageStack.append(self.VarDecl.__name__)
        arrayLambdaNode = self.lambdaWrapper('_VarDecl')
        if arrayLambdaNode and len(arrayLambdaNode.children):
            for c in arrayLambdaNode.children:
                varDeclNode.add(c)
            self.match({';'})
            node.add(varDeclNode)
            self.VarDecl(node)
            return node
        return None

    def _VarDecl(self) -> Optional[Node]:
        node = Node("_VarDecl")
        self.Type(node)
        self.IdList(node)
        return node


    def StmtList(self, node: Node | None = None) -> Optional[Node]:
        if not node:
            node = Node("StmtList")
        self.languageStack.append(self.StmtList.__name__)
        node.add(self.Stmt())
        self.StmtList1(node)
        return node

    def Stmt(self) -> Optional[Node]:
        node = Node("Stmt")
        self.languageStack.append(self.Stmt.__name__)
        la = self.lookahead
        match la:
            case 'if':
                ifNode = self.match({'if'})
                self.match({'('})
                ifConditionalNode = Node("CONDITIONAL")
                self.Expr(ifConditionalNode)
                ifNode.add(ifConditionalNode)
                self.match({')'})
                ifStmts = self.Stmt()
                for c in ifStmts.children:
                    ifNode.add(c)
                elseNode = self.match({'else'})
                elseStmts = self.Stmt()
                for c in elseStmts.children:
                    elseNode.add(c)
                node.add(ifNode)
                node.add(elseNode)
            case 'while':
                whileNode = self.match({'while'})
                self.match({'('})
                whileConditional = Node("CONDITIONAL")
                self.Expr(whileConditional)
                whileNode.add(whileConditional)
                self.match({')'})
                whileStmts = self.Stmt()
                for c in whileStmts.children:
                    whileNode.add(c)
                node.add(whileNode)
            case 'break':
                node.add(self.match({'break'}))
                node.add(self.match({';'}))
            case 'print':
                printNode = self.match({'print'})
                self.match({'('})
                printNode.add(self.ExprList())
                self.match({')'})
                self.match({';'})
                node.add(printNode)
            case 'readln':
                readlnNode = self.match({'readln'})
                self.match({'('})
                self.Expr(readlnNode)
                self.match({')'})
                self.match({';'})
                node.add(readlnNode)
            case 'return':
                returnNode = self.match({'return'})
                self.Expr(returnNode)
                self.match({';'})
                node.add(returnNode)
            case '{':
                self.match({'{'})
                self.StmtList(node)
                self.match({'}'})
            case _:
                self.Expr(node)
                self.match({';'})
        return node

    def Expr(self, node: Node) -> Optional[Node]:
        exprNode = Node("Expr")
        self.languageStack.append(self.Expr.__name__)
        if self.tryComputeMatch('Primary'):
            primaryNode = self.Primary()
            exprNode.add(primaryNode)
            self.AltExpr(exprNode)
        else:
            exprNode.add(self.UnaryOp())
            exprNode.add(self.ExtraExpr())
        node.add(exprNode)
        return node

    def Primary(self) -> Optional[Node]:
        node = Node("Primary")
        self.languageStack.append(self.Primary.__name__)
        la = self.getLookAheadToken()
        match la:
            case '(':
                self.match({'('})
                self.Expr(node)
                self.match({')'})
            case 'ID':
                idNode = self.match({'ID'})
                identNode = self.Ident()
                if len(identNode.children):
                    for c in identNode.children:
                        idNode.add(c)
                node.add(idNode)
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

    def AltExpr(self, node: Node) -> Optional[Node]:
        altExpr = Node("AltExpr")
        self.languageStack.append(self.AltExpr.__name__)
        lambdaAltExpr = self.lambdaWrapper('_AltExpr')
        if lambdaAltExpr and len(lambdaAltExpr.children):
            for c in lambdaAltExpr.children:
                altExpr.add(c)
        if len(altExpr.children):
            node.add(altExpr)
        return node

    def _AltExpr(self) -> Optional[Node]:
        node = Node("_AltExpr")
        if self.lookahead == '[':
            self.match({'['})
            self.Expr(node)
            self.match({']'})
            altExpr1 = self.AltExpr1()
            if altExpr1 and len(altExpr1.children):
                for c in altExpr1.children:
                    node.add(c)
            
        else:
            self.CmplExpr(node)
        return node     

    def AltExpr1(self) -> Optional[Node]:
        node = Node("AltExpr1")
        self.languageStack.append(self.AltExpr1.__name__)
        node.add(self.lambdaWrapper('_AltExpr1'))
        return node  

    def _AltExpr1(self) -> Optional[Node]:
        node = Node("_AltExpr1")
        self.CmplExpr(node)
        return node

    def CmplExpr(self, node: Node) -> Optional[Node]:
        self.languageStack.append(self.CmplExpr.__name__)
        if self.lookahead == '=':
            equalsNode = self.match({'='})
            self.Expr(equalsNode)
            node.add(equalsNode)
        else:
            node.add(self.OrExpr())
            self.Expr(node)
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
            self.CmplExpr(node)
        else:
            self.Expr(node)
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
        self.Expr(node)
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

    def StmtList1(self, node: Node) -> Optional[Node]:
        self.languageStack.append(self.StmtList1.__name__)
        lambdaNode = self.lambdaWrapper('_StmtList1')
        if lambdaNode and len(lambdaNode.children):
            for c in lambdaNode.children:
                node.add(c)
        return node

    def _StmtList1(self) -> Optional[Node]:
        node = Node("_StmtList1")
        node.add(self.Stmt())
        self.StmtList1(node)
        return node

    def FunctionDecl1(self, node: Node) -> Optional[Node]:
        self.languageStack.append(self.FunctionDecl1.__name__)
        lambdaNode = self.lambdaWrapper('_FunctionDecl1')
        if lambdaNode and len(lambdaNode.children):
            for c in lambdaNode.children:
                node.add(c)
        return node

    def _FunctionDecl1(self) -> Optional[Node]:
        return self.Program()

    def Array(self, node: Node) -> Optional[Node]:
        self.languageStack.append(self.Array.__name__)
        arrayLambdaNode = self.lambdaWrapper('_Array')
        if arrayLambdaNode and len(arrayLambdaNode.children):
            for c in arrayLambdaNode.children:
                node.add(c)
        return node

    def _Array(self) -> Optional[Node]:
        node = Node("_Array")
        self.match({'['})
        node.add(self.match({'NUM'}))
        self.match({']'})
        return node

    def Array1(self, node: Node) -> Optional[Node]:
        self.languageStack.append(self.Array1.__name__)
        idNode = node.children[len(node.children)-1]
        self.Array(idNode)
        self.Array2(node)
        return node

    def Array2(self, node: Node) -> Optional[Node]:
        self.languageStack.append(self.Array2.__name__)
        arrayLambdaNode = self.lambdaWrapper('_Array2')
        if arrayLambdaNode and len(arrayLambdaNode.children):
            for c in arrayLambdaNode.children:
                node.add(c)
        return node

    def _Array2(self) -> Optional[Node]:
        node = Node("IdList")
        self.match({','})
        node.add(self.match({'ID'}))
        self.Array1(node)
        return node

    def FormalRest(self, node: Node) -> Optional[Node]:
        self.languageStack.append(self.FormalRest.__name__)
        arrayLambdaNode = self.lambdaWrapper('_FormalRest')
        if arrayLambdaNode and len(arrayLambdaNode.children):
            for c in arrayLambdaNode.children:
                node.add(c)
        return node

    def _FormalRest(self) -> Optional[Node]:
        node = Node("_FormalRest")
        self.match({','})
        self.Type(node)
        node.add(self.match({'ID'}))
        self.Array(node)
        self.FormalRest(node)
        return node        

    def generateOutput(self):
        return self.buffer

    def input(self, buffer):
        self.buffer = buffer
        
    def output(self) -> Optional[Node]:
        hasError = False
        generatedAst = self.parse() 
        try:
            self.print_asa(generatedAst)
        except Exception:
            hasError = True       
            generatedAst = None
            
        if hasError:
            print(f"{self.errorMessage}")
        return generatedAst
