
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

    def

    def generateOutput(self):
        """
        Gera o output de acordo com os dados de entrada
        """
        output = ""
        word = ""
        self.mode = LexicoModes.READING
        for index in range(len(self.inputDataFile)):
            char = self.inputDataFile[index]

            if self.isBreakPoint(char):
                if(self.isPrivateToken(word)):
                    output += self.outputPrivateToken(word)
                else:
                    output += self.loadtIdentifier(word)
                if char == "(":
                    output += self.outputPrivateToken("(")
                    index = index+1
                elif char == ")":
                    output += self.outputPrivateToken(")")
                    index = index+1
                else:
                    output += char
                # if index + 1 < len(self.inputDataFile):
                #     if self.inputDataFile[index+1] != ' ':
                #         output += ' '
                word = ""
            else:
                word += char

        if(self.isPrivateToken(word)):
            output += self.outputPrivateToken(word)
        else:
            output += self.loadtIdentifier(word)
        word = ""
        return output
    
    def isBreakPoint(self, char: str) -> bool:
        """
        Verifica se é um caractere de quebra.
        """
        return char == '\n' or char == ' ' or char == ';' or char == '(' or char == ')'
    
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
    
    def loadtIdentifier(self, word):
        """
        Transforma o valor do token pelo valor de saída adequado.
        """ 
        if word:
            number = self.parseInt(word)
            if number:
                return self.identifiers.get('number', '').get('output').replace('{VALUE}', word)
            else:
                return self.identifiers.get('id', '').get('output').replace('{VALUE}', word)
        else:
            return ''
    
    def parseInt(self, number) -> float | None:
        """
        Transforma o valor em numérico com "safe parse".
        """
        try:
            return float(number)
        except ValueError:
            return None
        
        
    def input(self, path):
        self.inputDataFile = self.fs.downloadFile(path)
        
    def output(self) -> str:
        generatedOutput = self.generateOutput()
        self.fs.uploadFile(os.path.join('tmp','lexico'), 'saida.txt', 'w', generatedOutput)
        return generatedOutput