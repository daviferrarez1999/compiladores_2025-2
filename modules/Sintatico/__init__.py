from injector import Module, singleton, provider

from modules.FileSystem import IFileSystem
from .Sintatico import Sintatico
from .ISintatico import ISintatico

class SintaticoModule(Module):
    @singleton
    @provider
    def instance_complier_sintatico(self, fs: IFileSystem) -> ISintatico:
        return Sintatico(fs)
