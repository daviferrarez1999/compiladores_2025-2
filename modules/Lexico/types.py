from enum import Enum
from typing import TypedDict

class Token(TypedDict):
    output: str

class Identifier(TypedDict):
    output: str

class LexicoModes(Enum):
    READING = "READING"
    COMMENT = "COMMENT"
    STRING = "STRING"
    NUMBER = "NUMBER"
    FLOAT = "FLOAT"
    LOGIC = "LOGIC"