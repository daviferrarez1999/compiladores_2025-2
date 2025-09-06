from typing import TypedDict, List

class Token(TypedDict):
    name: str
    identifier: str
    output: str

class Identifier(TypedDict):
    output: str