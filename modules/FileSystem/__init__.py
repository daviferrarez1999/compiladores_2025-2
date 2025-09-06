from injector import Module, singleton, provider
from .IFileSystem import IFileSystem
from .LocalFileSystem import LocalFileSystem

class FileSystemModule(Module):
    @singleton
    @provider
    def instance_fileSystem(self) -> IFileSystem:
        return LocalFileSystem()
