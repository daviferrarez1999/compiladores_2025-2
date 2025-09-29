
import os
from injector import inject
import yaml

from modules.FileSystem import IFileSystem
from .ILexico import ILexico
from .types import LexicoModes, Token, Identifier
from typing import List, cast, Dict

PRIVATE_TOKENS = 'private_tokens.yml'
IDENTIFIERS = 'identifiers.yml'

class Lexico(ILexico):
    line: int = 1
    column: int = 0
    privateTokens: Token
    """
    Tokens privados da linguagem
    """
    identifiers: Dict[str, Identifier]
    """
    Tokens identificadores
    """
    inputDataFile: str = ""
    """
    Dados de entrada
    """
    mode: LexicoModes
    fs: IFileSystem

    @inject
    def __init__(self, fs: IFileSystem):
        self.fs = fs
        self.startConfig()

    def loadPrivateTokens(self) -> Token:
        """
        Carrega as configurações dos tokens privados
        """
        file = self.fs.downloadFile(os.path.join('config', 'lexico', PRIVATE_TOKENS))
        data = yaml.safe_load(file)
        return cast(List[Token], data)
    
    def loadIdentifiers(self) -> Token:
        """
        Carrega as configurações dos tokens identificadores
        """
        file = self.fs.downloadFile(os.path.join('config', 'lexico', IDENTIFIERS))
        data = yaml.safe_load(file)
        return data
    
    def startConfig(self):
        """
        Carrega as configurações
        """
        print("Carregando configurações do Léxico")
        self.privateTokens = self.loadPrivateTokens()
        self.identifiers = self.loadIdentifiers()
        print("Configurações carregadas")

    def setReadingMode(self):
        self.mode = LexicoModes.READING

    def setCommentMode(self):
        self.mode = LexicoModes.COMMENT

    def setStringMode(self):
        self.mode = LexicoModes.STRING

    def setNumberMode(self):
        self.mode = LexicoModes.NUMBER

    def setFloatMode(self):
        self.mode = LexicoModes.FLOAT
        
    def setCharMode(self):
        self.mode = LexicoModes.CHAR

    def generateOutput(self):
        """
        Gera o output de acordo com os dados de entrada
        """
        output = ""
        word = ""
        self.mode = LexicoModes.READING
        index = 0
        while(index < len(self.inputDataFile)):
            char = self.inputDataFile[index]
            self.computeLine(char)

            if char == '"' and self.mode == LexicoModes.READING:
                output+=word
                word=""
                self.evenCountBars = True
                self.setStringMode()

            if char == "'" and self.mode == LexicoModes.READING:
                if self.isPrivateToken(word):
                    output += self.outputPrivateToken(word)
                else:
                    output += self.loadIdentifier(word)
                word = ""
                self.setCharMode()

            if word + char == "/*" and self.mode == LexicoModes.READING:
                self.setCommentMode()
            
            if word == "!" and self.isPrivateToken(word+char) and self.mode == LexicoModes.READING:
                index+=1
                output+= self.outputPrivateToken(word+char)
                word="" 
                continue

            if len(word) == 0 and self.isDot(char) and self.mode == LexicoModes.READING:
                word += self.computeChar(char)
                self.setFloatMode()
                index+=1
                continue

            if len(word) == 0 and self.isNumber(char) and self.mode == LexicoModes.READING:
                word += self.computeChar(char)
                self.setNumberMode()
                index+=1
                continue
            
            if self.mode == LexicoModes.FLOAT:
                if self.isNumber(char):
                    word += self.computeChar(char)
                elif len(word) == 1 or word[-1] == '.':
                    # ERRO
                    output+= self.printError(word)
                    word=self.computeChar(char)
                    self.setReadingMode()
                else:
                    output+= self.identifiers.get('float', '').get('output').replace('{VALUE}', word)
                    word = self.computeChar(char)
                    self.setReadingMode()
            elif self.mode == LexicoModes.NUMBER:
                if self.isNumber(char):
                    word+=self.computeChar(char)
                elif self.isDot(char):
                    word+=self.computeChar(char)
                    self.setFloatMode()
                else:
                    output+= self.identifiers.get('number', '').get('output').replace('{VALUE}', word)
                    word=self.computeChar(char)
                    self.setReadingMode()
            elif self.mode == LexicoModes.COMMENT:
                if word[-2:] == "*/":
                    word=self.computeChar(char)
                    self.setReadingMode()
                else:
                    word+=self.computeChar(char)
            elif self.mode == LexicoModes.CHAR:
                word += char
                if(char == "'"):
                    if len(word) >= 2:
                        # terminando a leitura de caractere
                        output += self.validateCharWord(word)
                        word=""
                        self.setReadingMode()
            elif self.mode == LexicoModes.STRING:
                word+=self.computeChar(char)
                if char == '\\':
                    self.evenCountBars = not self.evenCountBars
                if len(word) > 1 and char == '"':
                    if self.evenCountBars:
                        output += self.identifiers.get("string", '').get('output').replace('{VALUE}', word)
                        word = ""
                        self.setReadingMode()
                    self.evenCountBars = True
            elif self.mode == LexicoModes.READING:
                if not (self.isLetter(char) or char == '_' or self.isNumber(char)):
                    if self.isPrivateToken(word):
                        if not self.isPrivateToken(word+char):
                            output += self.outputPrivateToken(word)
                            word=self.computeChar(char)
                        else:
                            word+=self.computeChar(char)
                    else:
                        output += self.loadIdentifier(word)
                        word=self.computeChar(char)
                else:
                    if self.isPrivateToken(word):
                        output += self.outputPrivateToken(word)
                        index-=1
                        word = ""
                    else:
                        word+=self.computeChar(char)
            if self.mode == LexicoModes.READING and (char == '\n' or char == ' '):
                output+=char
            
            index+=1

        if self.mode == LexicoModes.READING:
            if(self.isPrivateToken(word)):
                output += self.outputPrivateToken(word)
            else:
                output += self.loadIdentifier(word)
        elif self.mode == LexicoModes.CHAR:
            output += self.validateCharWord(word)
        elif self.mode == LexicoModes.COMMENT:
            if word[-2:] != '*/':
                output+=self.printError(word)
        elif self.mode == LexicoModes.FLOAT:
            if len(word) == 1 or word[-1] == '.':
                output+=self.printError(word)
                word=self.computeChar(char)
                self.setReadingMode()
            else:
                output+= self.identifiers.get('float', '').get('output').replace('{VALUE}', word)
                word=self.computeChar(char)
        elif self.mode == LexicoModes.NUMBER:
            output+= self.identifiers.get('number', '').get('output').replace('{VALUE}', word)
        elif self.mode == LexicoModes.STRING:
            output+=self.printError(word)
        word = ""
        return output+"<EOF>"
    
    def printError(self, word: str) -> str:
        if len(word) > 0:
            print(f"Erro ao ler token \"{word}\" na linha {self.line} e coluna {self.column}")
            return self.identifiers.get('error', '').get('output').replace('{VALUE}', word)
        return ""
    
    def computeLine(self, char):
        if char == '\n':
            self.line+=1
            self.column=1
        else:
            self.column+=1
    
    def isValidIdentifier(self, word: str) -> bool:
        if len(word) > 0:
            if not (word[0] == '_' or self.isLetter(word[0])):
                return False
        else:
            return False
        return [True if self.isLetter(i) or i == '_' else False for i in word]
    
    def validateCharWord(self, word: str) -> str:
        lenWord = len(word)
        if lenWord > 4:
            return self.printError(word)
        else:
            if lenWord == 4 :
                if word[1] == "\\":
                    return self.identifiers.get('char', '').get('output').replace('{VALUE}', word)
                else:
                    return self.printError(word)
            else:
                if(lenWord > 2):
                    if word[1] == '\\':
                        return self.printError(word)
                return self.identifiers.get('char', '').get('output').replace('{VALUE}', word)
                
    def isLetter(self, char: str) -> bool:
        numberOfChar = ord(char)
        return ((numberOfChar >= ord("a") and numberOfChar <= ord("z")) 
                or (numberOfChar >= ord("A") and numberOfChar <= ord("Z")))
    
    def isNumber(self, char: str) -> bool:
        numberOfChar = ord(char)
        return (numberOfChar >= ord("0") and numberOfChar <= ord("9"))
    
    def isDot(self, char: str) -> bool:
        return char == '.'
    
    def computeChar(self, char: str) -> str:
        if char == '\n' or char == ' ':
            return ''
        else:
            return char

    def isPrivateToken(self, token) -> str:
        """
        Verifica se é um token privado.
        """
        return True if self.privateTokens.get(token, None) else False

    
    def outputPrivateToken(self, token) -> str:
        """
        Transforma o valor do token pelo valor de saída adequado.
        """
        privateToken = self.privateTokens.get(token, None)
        if privateToken:
            return privateToken.get('output', '')
        return ''
    
    def loadIdentifier(self, word):
        """
        Transforma o valor do token pelo valor de saída adequado.
        """ 
        if self.isValidIdentifier(word):
            return self.identifiers.get('id', '').get('output').replace('{VALUE}', word)
        else:
            return self.printError(word)  
        
    def input(self, path):
        self.inputDataFile = self.fs.downloadFile(path)
        
    def output(self) -> str:
        generatedOutput = self.generateOutput()
        self.fs.uploadFile(os.path.join('tmp','lexico'), 'saida.txt', 'w', generatedOutput)
        return generatedOutput