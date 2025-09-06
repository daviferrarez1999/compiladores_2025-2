
import os
import yaml
from .types import Token, Identifier
from typing import List, cast, Dict
from modules import fileSystem
import sys

PRIVATE_TOKENS = 'private_tokens.yml'
IDENTIFIERS = 'identifiers.yml'

class Lexico:
    privateTokens: List[Token]
    identifiers: Dict[str, Identifier]
    inputDataFile: str

    def __init__(self):
        self.startConfig()

    def loadPrivateTokens(self) -> Token:
        file = fileSystem.downloadFile(os.path.join('lexico', 'config', PRIVATE_TOKENS))
        data = yaml.safe_load(file)
        return cast(List[Token], data)
    
    def loadIdentifiers(self) -> Token:
        file = fileSystem.downloadFile(os.path.join('lexico', 'config', IDENTIFIERS))
        data = yaml.safe_load(file)
        return data
    
    def loadInputFile(self):
        if len(sys.argv) < 2:
            print("Por favor, informe o nome do arquivo.")
            sys.exit(1)            
        fileName = sys.argv[1]
        return fileSystem.downloadFile(fileName)
    
    def startConfig(self):
        print("Carregando configurações do Léxico")
        self.privateTokens = self.loadPrivateTokens()
        self.inputDataFile = self.loadInputFile()
        self.identifiers = self.loadIdentifiers()
        print(self.identifiers)
        print("Configurações carregadas")

    def generateOutput(self):
        output = ""
        word = ""
        for char in self.inputDataFile:
            if self.isBreakPoint(char):
                if(self.isPrivateToken(word)):
                    output += self.outputPrivateToken(word)
                else:
                    output += self.loadtIdentifier(word)
                output+= char
                word = ""
            else:
                word += char
        return output            
    
    def isBreakPoint(self, char: str):
        return char == '\n' or char == ' ' or char == ';'
    
    def isPrivateToken(self, token) -> str:
        for privateToken in self.privateTokens:
            if(privateToken.get('identifier', '') == token):
                return True
        return False
    
    def outputPrivateToken(self, token) -> str:
        for privateToken in self.privateTokens:
            if(privateToken.get('identifier', '') == token):
                return privateToken.get('output', '')
        return ''
    
    def loadtIdentifier(self, word):
        if word:
            number = self.parseInt(word)
            if number:
                return self.identifiers.get('number', '').get('output') +word+">"
            else:
                return self.identifiers.get('id', '').get('output') +word+">"
        else:
            return ''
    
    def parseInt(self, number) -> int | None:
        try:
            return int(number)
        except ValueError:
            return None