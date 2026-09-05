"""
Nova Abstract Syntax Tree (AST) Node Hierarchy
Typed nodes for expressions, statements, and program roots.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from nova.tokens import Token


class ASTNode:
    def to_dict(self) -> Dict[str, Any]:
        """Convert AST node to JSON-serializable dictionary for visualizers and debuggers."""
        res = {"_type": self.__class__.__name__}
        for k, v in self.__dict__.items():
            if isinstance(v, ASTNode):
                res[k] = v.to_dict()
            elif isinstance(v, list):
                res[k] = [item.to_dict() if isinstance(item, ASTNode) else (item.lexeme if isinstance(item, Token) else item) for item in v]
            elif isinstance(v, Token):
                res[k] = {"lexeme": v.lexeme, "type": v.type.name, "line": v.line, "col": v.column}
            else:
                res[k] = v
        return res


# ==========================================
# Expressions
# ==========================================
class Expr(ASTNode):
    pass


@dataclass
class LiteralExpr(Expr):
    value: Any


@dataclass
class VariableExpr(Expr):
    name: Token


@dataclass
class AssignExpr(Expr):
    name: Token
    value: Expr


@dataclass
class BinaryExpr(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass
class UnaryExpr(Expr):
    operator: Token
    right: Expr


@dataclass
class LogicalExpr(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass
class CallExpr(Expr):
    callee: Expr
    arguments: List[Expr]
    paren: Token


@dataclass
class FunctionExpr(Expr):
    params: List[Token]
    body: List['Stmt']


@dataclass
class ListExpr(Expr):
    elements: List[Expr]


@dataclass
class IndexExpr(Expr):
    target: Expr
    index: Expr
    bracket: Token


@dataclass
class IndexAssignExpr(Expr):
    target: Expr
    index: Expr
    value: Expr
    bracket: Token


# ==========================================
# Statements
# ==========================================
class Stmt(ASTNode):
    pass


@dataclass
class Program(ASTNode):
    statements: List[Stmt] = field(default_factory=list)


@dataclass
class ExprStmt(Stmt):
    expression: Expr


@dataclass
class PrintStmt(Stmt):
    keyword: Token
    expressions: List[Expr]


@dataclass
class LetStmt(Stmt):
    name: Token
    initializer: Optional[Expr]
    is_mutable: bool


@dataclass
class BlockStmt(Stmt):
    statements: List[Stmt]


@dataclass
class IfStmt(Stmt):
    condition: Expr
    then_branch: BlockStmt
    else_branch: Optional[Stmt]  # BlockStmt or IfStmt (else if)


@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: BlockStmt


@dataclass
class ForStmt(Stmt):
    initializer: Optional[Stmt]
    condition: Optional[Expr]
    increment: Optional[Expr]
    body: BlockStmt


@dataclass
class FunctionStmt(Stmt):
    name: Token
    params: List[Token]
    body: List[Stmt]


@dataclass
class ReturnStmt(Stmt):
    keyword: Token
    value: Optional[Expr]


@dataclass
class BreakStmt(Stmt):
    keyword: Token


@dataclass
class ContinueStmt(Stmt):
    keyword: Token
