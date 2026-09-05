"""
Nova Parser
Combines Recursive Descent for statements and Pratt Parsing for expressions.
"""
from typing import List, Optional, Callable, Dict, Any
from nova.tokens import Token, TokenType
from nova.errors import NovaSyntaxError
from nova.ast_nodes import (
    Program, Stmt, Expr, LetStmt, ExprStmt, PrintStmt, BlockStmt,
    IfStmt, WhileStmt, ForStmt, FunctionStmt, ReturnStmt, BreakStmt, ContinueStmt,
    LiteralExpr, VariableExpr, AssignExpr, BinaryExpr, UnaryExpr, LogicalExpr,
    CallExpr, FunctionExpr, ListExpr, IndexExpr, IndexAssignExpr
)


# Operator Precedence hierarchy
PREC_NONE = 0
PREC_ASSIGNMENT = 1  # =
PREC_OR = 2          # ||, or
PREC_AND = 3         # &&, and
PREC_EQUALITY = 4    # ==, !=
PREC_COMPARISON = 5  # <, <=, >, >=
PREC_TERM = 6        # +, -
PREC_FACTOR = 7      # *, /, %
PREC_UNARY = 8       # !, -
PREC_CALL = 9        # (), []


class Parser:
    def __init__(self, tokens: List[Token], source: str = "", filename: str = "<stdin>"):
        self.tokens = tokens
        self.source = source
        self.filename = filename
        self.current = 0
        self._lines = source.splitlines()

        # Infix precedence table
        self.precedences: Dict[TokenType, int] = {
            TokenType.ASSIGN: PREC_ASSIGNMENT,
            TokenType.OR: PREC_OR,
            TokenType.AND: PREC_AND,
            TokenType.EQ: PREC_EQUALITY,
            TokenType.NOT_EQ: PREC_EQUALITY,
            TokenType.LT: PREC_COMPARISON,
            TokenType.LTE: PREC_COMPARISON,
            TokenType.GT: PREC_COMPARISON,
            TokenType.GTE: PREC_COMPARISON,
            TokenType.PLUS: PREC_TERM,
            TokenType.MINUS: PREC_TERM,
            TokenType.STAR: PREC_FACTOR,
            TokenType.SLASH: PREC_FACTOR,
            TokenType.PERCENT: PREC_FACTOR,
            TokenType.LPAREN: PREC_CALL,
            TokenType.LBRACKET: PREC_CALL,
        }

    # ==========================================
    # Top-Level & Statement Parsing
    # ==========================================
    def parse(self) -> Program:
        statements: List[Stmt] = []
        while not self._is_at_end():
            stmt = self._declaration()
            if stmt is not None:
                statements.append(stmt)
        return Program(statements)

    def _declaration(self) -> Optional[Stmt]:
        try:
            if self._match(TokenType.LET):
                return self._var_declaration()
            if self._match(TokenType.FN):
                # Check if this is a function declaration: fn name(...) { ... }
                if self._check(TokenType.IDENTIFIER):
                    return self._function_declaration()
                else:
                    # Anonymous function expression as statement: back up
                    self.current -= 1
            return self._statement()
        except NovaSyntaxError as e:
            self._synchronize()
            raise e

    def _var_declaration(self) -> Stmt:
        is_mutable = self._match(TokenType.MUT)
        name = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'let'.")

        initializer: Optional[Expr] = None
        if self._match(TokenType.ASSIGN):
            initializer = self._expression()

        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration.")
        return LetStmt(name=name, initializer=initializer, is_mutable=is_mutable)

    def _function_declaration(self) -> Stmt:
        name = self._consume(TokenType.IDENTIFIER, "Expected function name.")
        self._consume(TokenType.LPAREN, "Expected '(' after function name.")
        parameters: List[Token] = []
        if not self._check(TokenType.RPAREN):
            while True:
                param = self._consume(TokenType.IDENTIFIER, "Expected parameter name.")
                parameters.append(param)
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RPAREN, "Expected ')' after parameters.")
        self._consume(TokenType.LBRACE, "Expected '{' before function body.")
        body = self._block_statements()
        return FunctionStmt(name=name, params=parameters, body=body)

    def _statement(self) -> Stmt:
        if self._match(TokenType.PRINT):
            return self._print_statement()
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.WHILE):
            return self._while_statement()
        if self._match(TokenType.FOR):
            return self._for_statement()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._match(TokenType.BREAK):
            keyword = self._previous()
            self._consume(TokenType.SEMICOLON, "Expected ';' after 'break'.")
            return BreakStmt(keyword=keyword)
        if self._match(TokenType.CONTINUE):
            keyword = self._previous()
            self._consume(TokenType.SEMICOLON, "Expected ';' after 'continue'.")
            return ContinueStmt(keyword=keyword)
        if self._match(TokenType.LBRACE):
            return BlockStmt(statements=self._block_statements())

        return self._expression_statement()

    def _print_statement(self) -> Stmt:
        keyword = self._previous()
        has_paren = self._match(TokenType.LPAREN)
        expressions: List[Expr] = []
        if not (has_paren and self._check(TokenType.RPAREN)):
            while True:
                expressions.append(self._expression())
                if not self._match(TokenType.COMMA):
                    break
        if has_paren:
            self._consume(TokenType.RPAREN, "Expected ')' after print arguments.")
        self._consume(TokenType.SEMICOLON, "Expected ';' after print statement.")
        return PrintStmt(keyword=keyword, expressions=expressions)

    def _if_statement(self) -> Stmt:
        has_paren = self._match(TokenType.LPAREN)
        condition = self._expression()
        if has_paren:
            self._consume(TokenType.RPAREN, "Expected ')' after if condition.")

        self._consume(TokenType.LBRACE, "Expected '{' after if condition.")
        then_branch = BlockStmt(statements=self._block_statements())

        else_branch: Optional[Stmt] = None
        if self._match(TokenType.ELSE):
            if self._match(TokenType.IF):
                else_branch = self._if_statement()
            else:
                self._consume(TokenType.LBRACE, "Expected '{' after 'else'.")
                else_branch = BlockStmt(statements=self._block_statements())

        return IfStmt(condition=condition, then_branch=then_branch, else_branch=else_branch)

    def _while_statement(self) -> Stmt:
        has_paren = self._match(TokenType.LPAREN)
        condition = self._expression()
        if has_paren:
            self._consume(TokenType.RPAREN, "Expected ')' after while condition.")

        self._consume(TokenType.LBRACE, "Expected '{' after while condition.")
        body = BlockStmt(statements=self._block_statements())
        return WhileStmt(condition=condition, body=body)

    def _for_statement(self) -> Stmt:
        self._consume(TokenType.LPAREN, "Expected '(' after 'for'.")

        initializer: Optional[Stmt] = None
        if self._match(TokenType.SEMICOLON):
            initializer = None
        elif self._match(TokenType.LET):
            initializer = self._var_declaration()
        else:
            initializer = self._expression_statement()

        condition: Optional[Expr] = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after loop condition.")

        increment: Optional[Expr] = None
        if not self._check(TokenType.RPAREN):
            increment = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after for clauses.")

        self._consume(TokenType.LBRACE, "Expected '{' before loop body.")
        body = BlockStmt(statements=self._block_statements())

        return ForStmt(initializer=initializer, condition=condition, increment=increment, body=body)

    def _return_statement(self) -> Stmt:
        keyword = self._previous()
        value: Optional[Expr] = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after return statement.")
        return ReturnStmt(keyword=keyword, value=value)

    def _block_statements(self) -> List[Stmt]:
        statements: List[Stmt] = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            stmt = self._declaration()
            if stmt is not None:
                statements.append(stmt)
        self._consume(TokenType.RBRACE, "Expected '}' after block.")
        return statements

    def _expression_statement(self) -> Stmt:
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression.")
        return ExprStmt(expression=expr)

    # ==========================================
    # Pratt Parsing for Expressions
    # ==========================================
    def _expression(self, precedence: int = PREC_NONE) -> Expr:
        if self._is_at_end():
            raise self._error(self._peek(), "Unexpected end of input while parsing expression.")

        token = self._advance()
        left = self._prefix_parse(token)

        while precedence < self._current_precedence():
            op_token = self._advance()
            left = self._infix_parse(left, op_token)

        return left

    def _current_precedence(self) -> int:
        if self._is_at_end():
            return PREC_NONE
        return self.precedences.get(self._peek().type, PREC_NONE)

    def _prefix_parse(self, token: Token) -> Expr:
        # Literals
        if token.type == TokenType.NUMBER or token.type == TokenType.STRING or token.type == TokenType.BOOLEAN:
            return LiteralExpr(value=token.literal)
        if token.type == TokenType.NIL:
            return LiteralExpr(value=None)
        if token.type == TokenType.IDENTIFIER:
            return VariableExpr(name=token)

        # Prefix Unary (!, -)
        if token.type in (TokenType.BANG, TokenType.MINUS):
            right = self._expression(PREC_UNARY)
            return UnaryExpr(operator=token, right=right)

        # Grouping ( expr )
        if token.type == TokenType.LPAREN:
            expr = self._expression(PREC_NONE)
            self._consume(TokenType.RPAREN, "Expected ')' after grouped expression.")
            return expr

        # List Literal [ a, b, c ]
        if token.type == TokenType.LBRACKET:
            elements: List[Expr] = []
            if not self._check(TokenType.RBRACKET):
                while True:
                    elements.append(self._expression(PREC_NONE))
                    if not self._match(TokenType.COMMA):
                        break
            self._consume(TokenType.RBRACKET, "Expected ']' after list elements.")
            return ListExpr(elements=elements)

        # Anonymous Function / Lambda: fn(params) { body }
        if token.type == TokenType.FN:
            self._consume(TokenType.LPAREN, "Expected '(' after 'fn'.")
            params: List[Token] = []
            if not self._check(TokenType.RPAREN):
                while True:
                    p = self._consume(TokenType.IDENTIFIER, "Expected parameter name.")
                    params.append(p)
                    if not self._match(TokenType.COMMA):
                        break
            self._consume(TokenType.RPAREN, "Expected ')' after parameter list.")
            self._consume(TokenType.LBRACE, "Expected '{' before function body.")
            body = self._block_statements()
            return FunctionExpr(params=params, body=body)

        raise self._error(token, f"Unexpected token '{token.lexeme}' in expression.")

    def _infix_parse(self, left: Expr, token: Token) -> Expr:
        # Assignment (=)
        if token.type == TokenType.ASSIGN:
            # Assignment is right-associative (PREC_ASSIGNMENT - 1)
            right = self._expression(PREC_ASSIGNMENT - 1)
            if isinstance(left, VariableExpr):
                return AssignExpr(name=left.name, value=right)
            elif isinstance(left, IndexExpr):
                return IndexAssignExpr(target=left.target, index=left.index, value=right, bracket=left.bracket)
            raise self._error(token, "Invalid assignment target.")

        # Function Call: expr(...)
        if token.type == TokenType.LPAREN:
            arguments: List[Expr] = []
            if not self._check(TokenType.RPAREN):
                while True:
                    arguments.append(self._expression(PREC_NONE))
                    if not self._match(TokenType.COMMA):
                        break
            paren = self._consume(TokenType.RPAREN, "Expected ')' after function arguments.")
            return CallExpr(callee=left, arguments=arguments, paren=paren)

        # Indexing: expr[...]
        if token.type == TokenType.LBRACKET:
            index = self._expression(PREC_NONE)
            bracket = self._consume(TokenType.RBRACKET, "Expected ']' after index expression.")
            return IndexExpr(target=left, index=index, bracket=bracket)

        # Logical operators (and, or, &&, ||)
        if token.type in (TokenType.AND, TokenType.OR):
            prec = self.precedences[token.type]
            right = self._expression(prec)
            return LogicalExpr(left=left, operator=token, right=right)

        # Binary operators (+, -, *, /, %, ==, !=, <, <=, >, >=)
        prec = self.precedences[token.type]
        right = self._expression(prec)
        return BinaryExpr(left=left, operator=token, right=right)

    # ==========================================
    # Parser Utilities
    # ==========================================
    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise self._error(self._peek(), message)

    def _error(self, token: Token, message: str) -> NovaSyntaxError:
        line_text = None
        if 1 <= token.line <= len(self._lines):
            line_text = self._lines[token.line - 1]
        return NovaSyntaxError(message, token.line, token.column, line_text)

    def _synchronize(self):
        self._advance()
        while not self._is_at_end():
            if self._previous().type == TokenType.SEMICOLON:
                return
            if self._peek().type in (
                TokenType.LET, TokenType.FN, TokenType.IF,
                TokenType.WHILE, TokenType.FOR, TokenType.RETURN, TokenType.PRINT
            ):
                return
            self._advance()
