
import os
from injector import inject
import yaml

from modules.FileSystem import IFileSystem
from .ISintatico import ISintatico
from .types import LexicoModes, Token, Identifier
from typing import List, cast, Dict

LANGUAGE = 'language.yml'

class Sintatico(ISintatico):
    language: Dict[str, List[str]]
    index: int
    currentToken: str
    buffer: str
    fs: IFileSystem

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
        return cast(Dict[str, List[str]], data)
    
    def startConfig(self):
        """
        Carrega as configurações
        """
        self.language = self.loadLanguage()
        print("Configurações do sintático carregadas")

    def nextToken(self):
        commentMode = False


    def Program(self):
        self.Type()
        self.Program_1()

    def Type(self):

    def Program_1(self):

    def ID(self):
    
    def IdList(self):

    def FunctionDecl(self):

    def generateOutput(self):
        self.nextToken()
        self.Program()
        if self.currentToken != 'EOF':
            throw error
        return self.buffer

    def input(self, buffer):
        self.buffer = buffer
        
    def output(self) -> str:
        generatedOutput = self.generateOutput()
        self.fs.uploadFile(os.path.join('tmp','sintatico'), 'saida.txt', 'w', generatedOutput)
        return generatedOutput