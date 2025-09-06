from abc import ABC, abstractmethod

class ILexico(ABC):
    @abstractmethod
    def input(self, path: str):
        ...    
    
    @abstractmethod
    def output(self) -> str:
        ...    
        