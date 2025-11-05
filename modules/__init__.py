from injector import Injector
from modules.FileSystem import FileSystemModule, IFileSystem
from modules.Lexico import LexicoModule, ILexico
from modules.Sintatico import SintaticoModule, ISintatico


injector = Injector([
    FileSystemModule(),
    LexicoModule(),
    SintaticoModule(),
    ])

fileSystem = injector.get(IFileSystem)
lexico = injector.get(ILexico)
sintatico = injector.get(ISintatico)