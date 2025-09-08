from abc import ABC, abstractmethod
from typing import Literal

class IFileSystem(ABC):
        @abstractmethod
        def downloadFile(self, path: str):
            """
            Realiza o download um arquivo.
            Args:
                path: caminho do arquivo.
            """
            ...    
        
        @abstractmethod
        def uploadFile(self, path: str, fileName: str, mode: Literal['wb', 'w'], data):
            """
            Faz o upload de um arquivo.
            Args:
                path: caminho do arquivo.
                fileName: nome do arquivo com a extensão do dado.
                mode: tipo de escrita, wb (binário) ou w (string).
                data: o dado a ser enviado para escrita.
            """
            ...    
        