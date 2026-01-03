from injector import Module, singleton, provider

from modules.C3E.generator import C3EGenerator
from modules.FileSystem import IFileSystem

class C3EModule(Module):
    @singleton
    @provider
    def instance_c23(self, fs: IFileSystem) -> C3EGenerator:
        return C3EGenerator(fs)
