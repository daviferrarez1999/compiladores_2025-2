from enum import Enum
from typing import TypedDict, List

class Token(TypedDict):
    name: str
    identifier: str
    output: str

class Identifier(TypedDict):
    output: str

class LexicoModes(Enum):
    READING = "READING"
    COMMENT = "COMMENT"
    STRING = "STRING"