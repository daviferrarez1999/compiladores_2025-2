from abc import ABC, abstractmethod

class ISintatico(ABC):
    """
    Interface do código Sintático
    """
    @abstractmethod
    def input(self, buffer: str):
        """
        Recebe o buffer dos dados de entrada.
        """
        ...    
    
    @abstractmethod
    def output(self) -> str:
        """
        Retorna a string de saída
        """
        ...    
        