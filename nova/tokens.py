"""
Nova Token Definitions
Enum token types and immutable token dataclass.
"""
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional


class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()
    NIL = auto()
    IDENTIFIER = auto()

    # Keywords
    LET = auto()
    MUT = auto()
    FN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    RETURN = auto()
    BREAK = auto()
    CONTINUE = auto()
    PRINT = auto()

    # Operators
    ASSIGN = auto()       # =
    PLUS = auto()         # +
    MINUS = auto()        # -
    STAR = auto()         # *
    SLASH = auto()        # /
    PERCENT = auto()      # %
    BANG = auto()         # !
    EQ = auto()           # ==
    NOT_EQ = auto()       # !=
    LT = auto()           # <
    LTE = auto()          # <=
    GT = auto()           # >
    GTE = auto()          # >=
    AND = auto()          # && or 'and'
    OR = auto()           # || or 'or'

    # Delimiters
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    LBRACE = auto()       # {
    RBRACE = auto()       # }
    LBRACKET = auto()     # [
    RBRACKET = auto()     # ]
    SEMICOLON = auto()    # ;
    COMMA = auto()        # ,
    DOT = auto()          # .

    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    literal: Any
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, '{self.lexeme}', lit={self.literal}, {self.line}:{self.column})"
