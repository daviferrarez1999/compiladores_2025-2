from injector import Injector
from modules.FileSystem import FileSystemModule, IFileSystem


injector = Injector([FileSystemModule()])

fileSystem = injector.get(IFileSystem)