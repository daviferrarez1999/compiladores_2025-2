
import os
from injector import inject
import yaml

from modules.FileSystem import IFileSystem
from .ILexico import ILexico
from .types import Token, Identifier
from typing import List, cast, Dict

PRIVATE_TOKENS = 'private_tokens.yml'
IDENTIFIERS = 'identifiers.yml'

class Lexico(ILexico):
    privateTokens: List[Token]
    identifiers: Dict[str, Identifier]
    inputDataFile: str
    fs: IFileSystem

    @inject
    def __init__(self, fs: IFileSystem):
        self.fs = fs
        self.startConfig()

    def loadPrivateTokens(self) -> Token:
        file = self.fs.downloadFile(os.path.join('modules', 'Lexico','config', PRIVATE_TOKENS))
        data = yaml.safe_load(file)
        return cast(List[Token], data)
    
    def loadIdentifiers(self) -> Token:
        file = self.fs.downloadFile(os.path.join('modules', 'Lexico', 'config', IDENTIFIERS))
        data = yaml.safe_load(file)
        return data
    
    def startConfig(self):
        print("Carregando configurações do Léxico")
        self.privateTokens = self.loadPrivateTokens()
        self.identifiers = self.loadIdentifiers()
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
        
        
    def input(self, path):
        self.inputDataFile = self.fs.downloadFile(path)
        
    def output(self) -> str:
        generatedOutput = self.generateOutput()
        self.fs.uploadFile(os.path.join('tmp','lexico'), 'saida.txt', 'w', generatedOutput)
        return generatedOutput