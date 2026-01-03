from injector import Injector
from modules.C3E import C3EModule, C3EGenerator
from modules.FileSystem import FileSystemModule, IFileSystem
from modules.Lexico import LexicoModule, ILexico
from modules.Sintatico import SintaticoModule, ISintatico
from modules.Semantico2 import SemanticAnalyzerModule, SemanticAnalyzer
from modules.Interpretador import InterpreterModule, init


injector = Injector([
    FileSystemModule(),
    LexicoModule(),
    SintaticoModule(),
    SemanticAnalyzerModule(),
    InterpreterModule(),
    C3EModule(),
    ])

fileSystem = injector.get(IFileSystem)
lexico = injector.get(ILexico)
sintatico = injector.get(ISintatico)
semantico = injector.get(SemanticAnalyzer)
interpreter = injector.get(init)
c3e = injector.get(C3EGenerator)