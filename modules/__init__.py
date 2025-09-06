from injector import Injector
from modules.FileSystem import FileSystemModule, IFileSystem
from modules.Lexico import LexicoModule, ILexico


injector = Injector([
    FileSystemModule(),
    LexicoModule()
    ])

fileSystem = injector.get(IFileSystem)
lexico = injector.get(ILexico)