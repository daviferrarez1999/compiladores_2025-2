from injector import Module, singleton, provider

from modules.FileSystem import IFileSystem
from .Lexico import Lexico
from .ILexico import ILexico

class LexicoModule(Module):
    @singleton
    @provider
    def instance_complier_lexico(self, fs: IFileSystem) -> ILexico:
        return Lexico(fs)
