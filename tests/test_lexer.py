"""
Unit tests for Nova Lexer.
"""
import pytest
from nova.lexer import Lexer
from nova.tokens import TokenType
from nova.errors import NovaSyntaxError


def test_lex_basic_tokens():
    source = "let mut x = 42; let name = \"Nova\";"
    tokens = Lexer(source).scan_tokens()
    types = [t.type for t in tokens]
    assert types == [
        TokenType.LET,
        TokenType.MUT,
        TokenType.IDENTIFIER,
        TokenType.ASSIGN,
        TokenType.NUMBER,
        TokenType.SEMICOLON,
        TokenType.LET,
        TokenType.IDENTIFIER,
        TokenType.ASSIGN,
        TokenType.STRING,
        TokenType.SEMICOLON,
        TokenType.EOF
    ]
    assert tokens[2].lexeme == "x"
    assert tokens[4].literal == 42
    assert tokens[9].literal == "Nova"


def test_lex_operators():
    source = "+ - * / % == != < <= > >= && || ! = ;"
    tokens = Lexer(source).scan_tokens()
    types = [t.type for t in tokens]
    assert types == [
        TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT,
        TokenType.EQ, TokenType.NOT_EQ, TokenType.LT, TokenType.LTE, TokenType.GT, TokenType.GTE,
        TokenType.AND, TokenType.OR, TokenType.BANG, TokenType.ASSIGN, TokenType.SEMICOLON,
        TokenType.EOF
    ]


def test_lex_keywords_and_literals():
    source = "fn if else while for return break continue print true false nil"
    tokens = Lexer(source).scan_tokens()
    types = [t.type for t in tokens]
    assert types == [
        TokenType.FN, TokenType.IF, TokenType.ELSE, TokenType.WHILE, TokenType.FOR,
        TokenType.RETURN, TokenType.BREAK, TokenType.CONTINUE, TokenType.PRINT,
        TokenType.BOOLEAN, TokenType.BOOLEAN, TokenType.NIL,
        TokenType.EOF
    ]
    assert tokens[9].literal is True
    assert tokens[10].literal is False
    assert tokens[11].literal is None


def test_lex_comments_ignored():
    source = """
    // This is a comment
    let x = 10; // Inline comment
    // Another comment
    """
    tokens = Lexer(source).scan_tokens()
    types = [t.type for t in tokens]
    assert types == [
        TokenType.LET, TokenType.IDENTIFIER, TokenType.ASSIGN, TokenType.NUMBER, TokenType.SEMICOLON,
        TokenType.EOF
    ]


def test_lex_string_escapes():
    source = r'"hello\nworld\t\"quoted\""'
    tokens = Lexer(source).scan_tokens()
    assert tokens[0].literal == 'hello\nworld\t"quoted"'


def test_lex_unterminated_string_error():
    source = '"unterminated string'
    with pytest.raises(NovaSyntaxError) as exc_info:
        Lexer(source).scan_tokens()
    assert "Unterminated string literal" in str(exc_info.value)
    assert exc_info.value.line == 1


def test_lex_unexpected_character_error():
    source = "let x = @;"
    with pytest.raises(NovaSyntaxError) as exc_info:
        Lexer(source).scan_tokens()
    assert "Unexpected character '@'" in str(exc_info.value)
