from abc import ABC, abstractmethod

class ILexico(ABC):
    """
    Interface do código Léxico
    """
    @abstractmethod
    def input(self, path: str):
        """
        Recebe o caminho do arquivo dos dados de entrada.
        """
        ...    
    
    @abstractmethod
    def output(self) -> str:
        """
        Retorna a string de saída
        """
        ...    
        