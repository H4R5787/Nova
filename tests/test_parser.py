"""
Unit tests for Nova Parser (Recursive Descent + Pratt expression parsing).
"""
import pytest
import nova
from nova.tokens import TokenType
from nova.ast_nodes import (
    Program, LetStmt, BinaryExpr, LiteralExpr, VariableExpr,
    IfStmt, WhileStmt, ForStmt, FunctionStmt, CallExpr
)
from nova.errors import NovaSyntaxError


def test_parse_variable_declaration():
    ast = nova.parse("let mut counter = 10;")
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, LetStmt)
    assert stmt.is_mutable is True
    assert stmt.name.lexeme == "counter"
    assert isinstance(stmt.initializer, LiteralExpr)
    assert stmt.initializer.value == 10


def test_parse_operator_precedence():
    # 2 + 3 * 4 should parse as 2 + (3 * 4)
    ast = nova.parse("let res = 2 + 3 * 4;")
    stmt = ast.statements[0]
    expr = stmt.initializer
    assert isinstance(expr, BinaryExpr)
    assert expr.operator.type == TokenType.PLUS
    assert isinstance(expr.left, LiteralExpr) and expr.left.value == 2
    assert isinstance(expr.right, BinaryExpr)
    assert expr.right.operator.type == TokenType.STAR
    assert expr.right.left.value == 3
    assert expr.right.right.value == 4


def test_parse_grouped_precedence():
    # (2 + 3) * 4 should parse as (2 + 3) * 4
    ast = nova.parse("let res = (2 + 3) * 4;")
    stmt = ast.statements[0]
    expr = stmt.initializer
    assert isinstance(expr, BinaryExpr)
    assert expr.operator.type == TokenType.STAR
    assert isinstance(expr.left, BinaryExpr)
    assert expr.left.operator.type == TokenType.PLUS


def test_parse_if_else_statement():
    source = """
    if (x > 10) {
        let y = 1;
    } else {
        let y = 2;
    }
    """
    ast = nova.parse(source)
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, IfStmt)
    assert stmt.else_branch is not None


def test_parse_function_declaration_and_call():
    source = """
    fn add(a, b) {
        return a + b;
    }
    let sum = add(5, 10);
    """
    ast = nova.parse(source)
    assert len(ast.statements) == 2
    assert isinstance(ast.statements[0], FunctionStmt)
    assert ast.statements[0].name.lexeme == "add"
    assert len(ast.statements[0].params) == 2

    let_stmt = ast.statements[1]
    assert isinstance(let_stmt.initializer, CallExpr)
    assert len(let_stmt.initializer.arguments) == 2


def test_parse_syntax_error():
    with pytest.raises(NovaSyntaxError) as exc_info:
        nova.parse("let x = ;")
    assert "Unexpected token ';'" in str(exc_info.value)
