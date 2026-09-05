"""
Nova Programming Language Engine
"""
from typing import Optional, List, Any
from nova.tokens import Token, TokenType
from nova.lexer import Lexer
from nova.parser import Parser
from nova.ast_nodes import Program
from nova.evaluator import Evaluator
from nova.environment import Environment
from nova.errors import NovaError, NovaSyntaxError, NovaRuntimeError


def tokenize(source: str, filename: str = "<stdin>") -> List[Token]:
    """Scan source code into tokens."""
    lexer = Lexer(source, filename=filename)
    return lexer.scan_tokens()


def parse(source: str, filename: str = "<stdin>") -> Program:
    """Parse source code into an Abstract Syntax Tree."""
    tokens = tokenize(source, filename=filename)
    parser = Parser(tokens, source=source, filename=filename)
    return parser.parse()


def run(source: str, filename: str = "<stdin>", stdout_capture: Optional[List[str]] = None) -> Any:
    """Execute Nova source code end-to-end."""
    ast = parse(source, filename=filename)
    evaluator = Evaluator(stdout_capture=stdout_capture)
    return evaluator.evaluate_program(ast)


__all__ = [
    "tokenize",
    "parse",
    "run",
    "Lexer",
    "Parser",
    "Evaluator",
    "Environment",
    "Token",
    "TokenType",
    "Program",
    "NovaError",
    "NovaSyntaxError",
    "NovaRuntimeError",
]
