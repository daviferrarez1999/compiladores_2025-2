from injector import Module, singleton, provider

from modules.FileSystem import IFileSystem
from .interpreter import init

class InterpreterModule(Module):
    @singleton
    @provider
    def instance_interpreter(self, fs: IFileSystem) -> init:
        return init
