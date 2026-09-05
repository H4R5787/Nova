"""
Nova Lexical Environment System
Implements hierarchical scope chains, mutability checking, and frame isolation.
"""
from typing import Dict, Any, Optional, List
from nova.tokens import Token
from nova.errors import NovaRuntimeError


class Environment:
    def __init__(self, parent: Optional['Environment'] = None, name: str = "block"):
        self.values: Dict[str, Any] = {}
        self.mutability: Dict[str, bool] = {}
        self.parent: Optional['Environment'] = parent
        self.name = name

    def define(self, name: str, value: Any, is_mutable: bool = False, token: Optional[Token] = None):
        """Define a variable binding in the immediate scope frame."""
        if name in self.values:
            line = token.line if token else 1
            col = token.column if token else 1
            raise NovaRuntimeError(f"Variable '{name}' is already defined in the current scope.", line, col)

        self.values[name] = value
        self.mutability[name] = is_mutable

    def get(self, token: Token) -> Any:
        """Resolve a variable by traversing up the lexical parent chain."""
        name = token.lexeme
        if name in self.values:
            return self.values[name]

        if self.parent is not None:
            return self.parent.get(token)

        raise NovaRuntimeError(f"Undefined variable '{name}'.", token.line, token.column)

    def get_by_name(self, name: str) -> Any:
        """Lookup by string name directly (useful for runtime built-ins)."""
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get_by_name(name)
        raise NovaRuntimeError(f"Undefined variable '{name}'.")

    def assign(self, token: Token, value: Any):
        """
        Assign a new value to an existing variable in the frame where it was defined.
        Rejects mutations to immutable bindings (declared without 'mut').
        """
        name = token.lexeme
        if name in self.values:
            if not self.mutability.get(name, False):
                raise NovaRuntimeError(
                    f"Cannot reassign immutable variable '{name}'. Declare with 'let mut {name}' to allow mutation.",
                    token.line,
                    token.column
                )
            self.values[name] = value
            return

        if self.parent is not None:
            self.parent.assign(token, value)
            return

        raise NovaRuntimeError(
            f"Cannot assign to undefined variable '{name}'. Did you forget to declare it with 'let'?",
            token.line,
            token.column
        )

    def fork(self, name: str = "child") -> 'Environment':
        """Spawn a child lexical frame that points back to this environment."""
        return Environment(parent=self, name=name)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize current frame and its parent chain for REPL scope inspection."""
        frame_vars = {}
        for k, v in self.values.items():
            # Format value for display
            if callable(v):
                v_repr = "<native function>"
            else:
                v_repr = repr(v)
            frame_vars[k] = {
                "value": v_repr,
                "mutable": self.mutability.get(k, False)
            }

        return {
            "scope_name": self.name,
            "bindings": frame_vars,
            "parent": self.parent.to_dict() if self.parent is not None else None
        }

    def __repr__(self) -> str:
        return f"Environment(name={self.name}, values={list(self.values.keys())}, has_parent={self.parent is not None})"
