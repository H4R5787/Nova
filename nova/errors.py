"""
Nova Error Reporting System
Provides formatted error diagnostics with source code context and column indicators.
"""
from typing import Optional


class NovaError(Exception):
    def __init__(self, message: str, line: int = 1, column: int = 1, source_line: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.source_line = source_line

    def format(self, filename: str = "<stdin>") -> str:
        header = f"{self.__class__.__name__} in {filename}:{self.line}:{self.column}"
        details = f"  Error: {self.message}"
        if self.source_line is not None:
            snippet = f"\n  {self.line} | {self.source_line}"
            pointer = f"\n  {' ' * len(str(self.line))} | {' ' * (self.column - 1)}^"
            return f"{header}\n{details}{snippet}{pointer}"
        return f"{header}\n{details}"

    def __str__(self) -> str:
        return self.format()


class NovaSyntaxError(NovaError):
    pass


class NovaRuntimeError(NovaError):
    pass


class ReturnException(Exception):
    """Internal control-flow exception for handling function returns."""
    def __init__(self, value):
        self.value = value


class BreakException(Exception):
    """Internal control-flow exception for loop break."""
    pass


class ContinueException(Exception):
    """Internal control-flow exception for loop continue."""
    pass
