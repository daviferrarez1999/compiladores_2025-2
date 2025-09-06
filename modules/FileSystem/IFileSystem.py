from abc import ABC, abstractmethod
from typing import Literal

class IFileSystem(ABC):
        @abstractmethod
        def downloadFile(self, path: str):
            ...    
        
        @abstractmethod
        def uploadFile(self, path: str, fileName: str, mode: Literal['wb', 'w'], data):
            ...    
        