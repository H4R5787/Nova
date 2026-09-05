"""
Nova Lexical Analyzer (Scanner)
Converts UTF-8 source string into deterministic stream of Tokens.
"""
from typing import List, Optional, Any
from nova.tokens import Token, TokenType
from nova.errors import NovaSyntaxError


class Lexer:
    KEYWORDS = {
        "let": TokenType.LET,
        "mut": TokenType.MUT,
        "fn": TokenType.FN,
        "if": TokenType.IF,
        "else": TokenType.ELSE,
        "while": TokenType.WHILE,
        "for": TokenType.FOR,
        "return": TokenType.RETURN,
        "break": TokenType.BREAK,
        "continue": TokenType.CONTINUE,
        "print": TokenType.PRINT,
        "true": TokenType.BOOLEAN,
        "false": TokenType.BOOLEAN,
        "nil": TokenType.NIL,
        "and": TokenType.AND,
        "or": TokenType.OR,
    }

    def __init__(self, source: str, filename: str = "<stdin>"):
        self.source = source
        self.filename = filename
        self.tokens: List[Token] = []
        self.start: int = 0
        self.current: int = 0
        self.line: int = 1
        self.column: int = 1
        self.token_start_column: int = 1
        self._lines = source.splitlines()

    def scan_tokens(self) -> List[Token]:
        while not self._is_at_end():
            self.start = self.current
            self.token_start_column = self.column
            self._scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line, self.column))
        return self.tokens

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _advance(self) -> str:
        ch = self.source[self.current]
        self.current += 1
        self.column += 1
        return ch

    def _peek(self) -> str:
        if self._is_at_end():
            return '\0'
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def _get_current_line_text(self) -> Optional[str]:
        if 1 <= self.line <= len(self._lines):
            return self._lines[self.line - 1]
        return None

    def _error(self, message: str) -> NovaSyntaxError:
        return NovaSyntaxError(
            message=message,
            line=self.line,
            column=self.token_start_column,
            source_line=self._get_current_line_text()
        )

    def _scan_token(self):
        ch = self._advance()

        # Whitespace
        if ch in (' ', '\r', '\t'):
            return
        elif ch == '\n':
            self.line += 1
            self.column = 1
            return

        # Single-character tokens
        elif ch == '(':
            self._add_token(TokenType.LPAREN)
        elif ch == ')':
            self._add_token(TokenType.RPAREN)
        elif ch == '{':
            self._add_token(TokenType.LBRACE)
        elif ch == '}':
            self._add_token(TokenType.RBRACE)
        elif ch == '[':
            self._add_token(TokenType.LBRACKET)
        elif ch == ']':
            self._add_token(TokenType.RBRACKET)
        elif ch == ',':
            self._add_token(TokenType.COMMA)
        elif ch == ';':
            self._add_token(TokenType.SEMICOLON)
        elif ch == '.':
            self._add_token(TokenType.DOT)
        elif ch == '+':
            self._add_token(TokenType.PLUS)
        elif ch == '-':
            self._add_token(TokenType.MINUS)
        elif ch == '*':
            self._add_token(TokenType.STAR)
        elif ch == '%':
            self._add_token(TokenType.PERCENT)

        # One or two character tokens
        elif ch == '!':
            self._add_token(TokenType.NOT_EQ if self._match('=') else TokenType.BANG)
        elif ch == '=':
            self._add_token(TokenType.EQ if self._match('=') else TokenType.ASSIGN)
        elif ch == '<':
            self._add_token(TokenType.LTE if self._match('=') else TokenType.LT)
        elif ch == '>':
            self._add_token(TokenType.GTE if self._match('=') else TokenType.GT)
        elif ch == '&':
            if self._match('&'):
                self._add_token(TokenType.AND)
            else:
                raise self._error("Unexpected character '&'. Did you mean '&&'?")
        elif ch == '|':
            if self._match('|'):
                self._add_token(TokenType.OR)
            else:
                raise self._error("Unexpected character '|'. Did you mean '||'?")

        # Slash or comment
        elif ch == '/':
            if self._match('/'):
                # Single-line comment: ignore until newline
                while self._peek() != '\n' and not self._is_at_end():
                    self._advance()
            else:
                self._add_token(TokenType.SLASH)

        # Literals
        elif ch == '"':
            self._scan_string()
        elif ch.isdigit():
            self._scan_number()
        elif ch.isalpha() or ch == '_':
            self._scan_identifier()
        else:
            raise self._error(f"Unexpected character '{ch}'.")

    def _scan_string(self):
        value_chars = []
        start_line = self.line
        start_col = self.token_start_column

        while self._peek() != '"' and not self._is_at_end():
            if self._peek() == '\n':
                self.line += 1
                self.column = 1
                value_chars.append(self._advance())
            elif self._peek() == '\\':
                self._advance()  # Skip backslash
                escaped = self._advance()
                if escaped == 'n':
                    value_chars.append('\n')
                elif escaped == 't':
                    value_chars.append('\t')
                elif escaped == 'r':
                    value_chars.append('\r')
                elif escaped == '"':
                    value_chars.append('"')
                elif escaped == '\\':
                    value_chars.append('\\')
                else:
                    value_chars.append(escaped)
            else:
                value_chars.append(self._advance())

        if self._is_at_end():
            raise NovaSyntaxError(
                message="Unterminated string literal.",
                line=start_line,
                column=start_col,
                source_line=self._lines[start_line - 1] if start_line <= len(self._lines) else None
            )

        self._advance()  # The closing "
        string_val = "".join(value_chars)
        self._add_token(TokenType.STRING, string_val)

    def _scan_number(self):
        while self._peek().isdigit():
            self._advance()

        # Fractional part
        if self._peek() == '.' and self._peek_next().isdigit():
            self._advance()  # Consume '.'
            while self._peek().isdigit():
                self._advance()

        text = self.source[self.start:self.current]
        num_val = float(text) if '.' in text else int(text)
        self._add_token(TokenType.NUMBER, num_val)

    def _scan_identifier(self):
        while self._peek().isalnum() or self._peek() == '_':
            self._advance()

        text = self.source[self.start:self.current]
        token_type = self.KEYWORDS.get(text, TokenType.IDENTIFIER)
        literal = None
        if token_type == TokenType.BOOLEAN:
            literal = True if text == "true" else False
        elif token_type == TokenType.NIL:
            literal = None

        self._add_token(token_type, literal)

    def _add_token(self, token_type: TokenType, literal: Any = None):
        lexeme = self.source[self.start:self.current]
        self.tokens.append(
            Token(
                type=token_type,
                lexeme=lexeme,
                literal=literal,
                line=self.line,
                column=self.token_start_column
            )
        )
