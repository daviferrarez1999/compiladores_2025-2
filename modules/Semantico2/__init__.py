from injector import Module, singleton, provider

from modules.FileSystem import IFileSystem
from .analyzer import SemanticAnalyzer

class SemanticAnalyzerModule(Module):
    @singleton
    @provider
    def instance_semantic_analyzer(self, fs: IFileSystem) -> SemanticAnalyzer:
        return SemanticAnalyzer(fs)
