from abc import abstractmethod

class IFileSystem:
        @abstractmethod
        def downloadFile(self, path: str):
            ...    
        
        @abstractmethod
        def uploadFile(self, path: str):
            ...    
        