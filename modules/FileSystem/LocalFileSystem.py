from typing import Literal
from .IFileSystem import IFileSystem
import os;

ROOT_PATH = os.getcwd()

class LocalFileSystem(IFileSystem):
    def downloadFile(self, path: str):
        try: 
            pathWithFile = os.path.join(ROOT_PATH, path)
            with open(pathWithFile, 'r', encoding='utf-8') as file:
                return file.read()
        except:
            print("Fail to read file or buffer.")
        
    def uploadFile(self, path: str, mode: Literal['wb', 'w'], data):
        try:      
            rootWithPath = os.path.join(ROOT_PATH, path)
            os.makedirs(rootWithPath, exist_ok=True)
            with open(rootWithPath, mode) as file:
                file.write(data)
        except Exception as e:
            print("Fail to write file or buffer.")