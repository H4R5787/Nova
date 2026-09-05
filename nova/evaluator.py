"""
Nova Tree-Walk Evaluator & Runtime Core
Implements AST visitor, closure evaluation, native built-ins, and loop frame isolation.
"""
import time
from typing import Any, List, Optional, Callable, Dict
from nova.ast_nodes import (
    Program, Stmt, Expr, LetStmt, ExprStmt, PrintStmt, BlockStmt,
    IfStmt, WhileStmt, ForStmt, FunctionStmt, ReturnStmt, BreakStmt, ContinueStmt,
    LiteralExpr, VariableExpr, AssignExpr, BinaryExpr, UnaryExpr, LogicalExpr,
    CallExpr, FunctionExpr, ListExpr, IndexExpr, IndexAssignExpr
)
from nova.tokens import TokenType, Token
from nova.environment import Environment
from nova.errors import NovaRuntimeError, ReturnException, BreakException, ContinueException


class NovaCallable:
    """Interface for callable objects in Nova (native functions & closures)."""
    def arity(self) -> int:
        raise NotImplementedError

    def call(self, evaluator: 'Evaluator', arguments: List[Any], token: Token) -> Any:
        raise NotImplementedError


class NovaFunction(NovaCallable):
    """User-defined first-class function retaining its lexical closure environment."""
    def __init__(self, name: str, params: List[Token], body: List[Stmt], closure: Environment):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure

    def arity(self) -> int:
        return len(self.params)

    def call(self, evaluator: 'Evaluator', arguments: List[Any], token: Token) -> Any:
        # Create function call scope bound to the closure environment
        fn_env = Environment(parent=self.closure, name=f"fn_{self.name}")
        for param, arg in zip(self.params, arguments):
            # Function arguments are mutable by default within function scope
            fn_env.define(param.lexeme, arg, is_mutable=True)

        try:
            return evaluator.execute_block(self.body, fn_env)
        except ReturnException as ret:
            return ret.value

    def __repr__(self) -> str:
        return f"<function {self.name}>"


class NovaNativeFunction(NovaCallable):
    """Built-in native host function."""
    def __init__(self, name: str, arity_count: int, fn: Callable[..., Any]):
        self.name = name
        self.arity_count = arity_count
        self.fn = fn

    def arity(self) -> int:
        return self.arity_count

    def call(self, evaluator: 'Evaluator', arguments: List[Any], token: Token) -> Any:
        return self.fn(*arguments)

    def __repr__(self) -> str:
        return f"<native fn {self.name}>"


class Evaluator:
    def __init__(self, stdout_capture: Optional[List[str]] = None):
        self.stdout_capture: List[str] = stdout_capture if stdout_capture is not None else []
        self.global_env = Environment(name="global")
        self.current_env = self.global_env
        self._register_builtins()

    def _register_builtins(self):
        # Native print
        def _native_print(*args):
            text = " ".join(self._stringify(a) for a in args)
            self.stdout_capture.append(text)
            print(text)
            return None

        # Native len
        def _native_len(val):
            if isinstance(val, (list, str)):
                return len(val)
            raise NovaRuntimeError(f"Cannot get length of type '{type(val).__name__}'.")

        # Native push
        def _native_push(lst, item):
            if isinstance(lst, list):
                lst.append(item)
                return lst
            raise NovaRuntimeError(f"push() expects a list as first argument.")

        # Native pop
        def _native_pop(lst):
            if isinstance(lst, list):
                if len(lst) == 0:
                    raise NovaRuntimeError("pop() called on empty list.")
                return lst.pop()
            raise NovaRuntimeError("pop() expects a list.")

        # Native clock
        def _native_clock():
            return time.time()

        # Native type
        def _native_type(val):
            if val is None:
                return "nil"
            if isinstance(val, bool):
                return "bool"
            if isinstance(val, (int, float)):
                return "number"
            if isinstance(val, str):
                return "string"
            if isinstance(val, list):
                return "list"
            if isinstance(val, NovaCallable):
                return "function"
            return "unknown"

        # Native str
        def _native_str(val):
            return self._stringify(val)

        self.global_env.define("print", NovaNativeFunction("print", -1, _native_print), is_mutable=False)
        self.global_env.define("len", NovaNativeFunction("len", 1, _native_len), is_mutable=False)
        self.global_env.define("push", NovaNativeFunction("push", 2, _native_push), is_mutable=False)
        self.global_env.define("pop", NovaNativeFunction("pop", 1, _native_pop), is_mutable=False)
        self.global_env.define("clock", NovaNativeFunction("clock", 0, _native_clock), is_mutable=False)
        self.global_env.define("type", NovaNativeFunction("type", 1, _native_type), is_mutable=False)
        self.global_env.define("str", NovaNativeFunction("str", 1, _native_str), is_mutable=False)

    def evaluate_program(self, program: Program) -> Any:
        result = None
        for stmt in program.statements:
            result = self.execute(stmt)
        return result

    def execute(self, stmt: Stmt) -> Any:
        method_name = f"visit_{type(stmt).__name__}"
        visitor = getattr(self, method_name, self._unhandled_node)
        return visitor(stmt)

    def eval_expr(self, expr: Expr) -> Any:
        method_name = f"visit_{type(expr).__name__}"
        visitor = getattr(self, method_name, self._unhandled_node)
        return visitor(expr)

    def _unhandled_node(self, node: Any):
        raise NotImplementedError(f"No visitor defined for node: {type(node).__name__}")

    # ==========================================
    # Statement Visitors
    # ==========================================
    def visit_Program(self, node: Program) -> Any:
        return self.evaluate_program(node)

    def visit_ExprStmt(self, stmt: ExprStmt) -> Any:
        return self.eval_expr(stmt.expression)

    def visit_PrintStmt(self, stmt: PrintStmt) -> Any:
        values = [self.eval_expr(e) for e in stmt.expressions]
        text = " ".join(self._stringify(v) for v in values)
        self.stdout_capture.append(text)
        print(text)
        return None

    def visit_LetStmt(self, stmt: LetStmt) -> Any:
        val = None
        if stmt.initializer is not None:
            val = self.eval_expr(stmt.initializer)
        self.current_env.define(stmt.name.lexeme, val, is_mutable=stmt.is_mutable, token=stmt.name)
        return val

    def visit_BlockStmt(self, stmt: BlockStmt) -> Any:
        block_env = Environment(parent=self.current_env, name="block")
        return self.execute_block(stmt.statements, block_env)

    def execute_block(self, statements: List[Stmt], env: Environment) -> Any:
        previous = self.current_env
        self.current_env = env
        try:
            result = None
            for s in statements:
                result = self.execute(s)
            return result
        finally:
            self.current_env = previous

    def visit_IfStmt(self, stmt: IfStmt) -> Any:
        cond_val = self.eval_expr(stmt.condition)
        if self._is_truthy(cond_val):
            return self.execute(stmt.then_branch)
        elif stmt.else_branch is not None:
            return self.execute(stmt.else_branch)
        return None

    def visit_WhileStmt(self, stmt: WhileStmt) -> Any:
        """
        While loop evaluation with per-iteration environment isolation.
        Eliminates closure variable aliasing bugs across iterations.
        """
        result = None
        while self._is_truthy(self.eval_expr(stmt.condition)):
            # Discrete iteration frame parented to the outer scope
            iteration_env = Environment(parent=self.current_env, name="while_iteration")
            try:
                result = self.execute_block(stmt.body.statements, iteration_env)
            except BreakException:
                break
            except ContinueException:
                continue
        return result

    def visit_ForStmt(self, stmt: ForStmt) -> Any:
        """
        For loop evaluation with per-iteration environment isolation.
        """
        for_scope = Environment(parent=self.current_env, name="for_scope")
        previous = self.current_env
        self.current_env = for_scope
        try:
            if stmt.initializer is not None:
                self.execute(stmt.initializer)

            result = None
            while True:
                if stmt.condition is not None:
                    if not self._is_truthy(self.eval_expr(stmt.condition)):
                        break

                # Discrete iteration frame parented to for_scope
                iteration_env = Environment(parent=self.current_env, name="for_iteration")
                try:
                    result = self.execute_block(stmt.body.statements, iteration_env)
                except BreakException:
                    break
                except ContinueException:
                    pass

                if stmt.increment is not None:
                    self.eval_expr(stmt.increment)

            return result
        finally:
            self.current_env = previous

    def visit_FunctionStmt(self, stmt: FunctionStmt) -> Any:
        # Function declared in current environment captures current_env as its closure
        fn = NovaFunction(
            name=stmt.name.lexeme,
            params=stmt.params,
            body=stmt.body,
            closure=self.current_env
        )
        self.current_env.define(stmt.name.lexeme, fn, is_mutable=False, token=stmt.name)
        return fn

    def visit_ReturnStmt(self, stmt: ReturnStmt) -> Any:
        val = None
        if stmt.value is not None:
            val = self.eval_expr(stmt.value)
        raise ReturnException(val)

    def visit_BreakStmt(self, stmt: BreakStmt) -> Any:
        raise BreakException()

    def visit_ContinueStmt(self, stmt: ContinueStmt) -> Any:
        raise ContinueException()

    # ==========================================
    # Expression Visitors
    # ==========================================
    def visit_LiteralExpr(self, expr: LiteralExpr) -> Any:
        return expr.value

    def visit_VariableExpr(self, expr: VariableExpr) -> Any:
        return self.current_env.get(expr.name)

    def visit_AssignExpr(self, expr: AssignExpr) -> Any:
        val = self.eval_expr(expr.value)
        self.current_env.assign(expr.name, val)
        return val

    def visit_IndexAssignExpr(self, expr: IndexAssignExpr) -> Any:
        target = self.eval_expr(expr.target)
        index = self.eval_expr(expr.index)
        val = self.eval_expr(expr.value)

        if not isinstance(target, list):
            raise NovaRuntimeError("Index assignment is only supported on lists.", expr.bracket.line, expr.bracket.column)
        if not isinstance(index, int):
            raise NovaRuntimeError("List index must be an integer.", expr.bracket.line, expr.bracket.column)
        if index < 0 or index >= len(target):
            raise NovaRuntimeError(f"List index out of bounds: {index} (length {len(target)}).", expr.bracket.line, expr.bracket.column)

        target[index] = val
        return val

    def visit_BinaryExpr(self, expr: BinaryExpr) -> Any:
        left = self.eval_expr(expr.left)
        right = self.eval_expr(expr.right)
        op = expr.operator.type
        line = expr.operator.line
        col = expr.operator.column

        # Arithmetic
        if op == TokenType.PLUS:
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            if isinstance(left, str) or isinstance(right, str):
                return self._stringify(left) + self._stringify(right)
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            raise NovaRuntimeError(f"Operator '+' not supported between '{type(left).__name__}' and '{type(right).__name__}'.", line, col)

        if op == TokenType.MINUS:
            self._check_number_operands(expr.operator, left, right)
            return left - right

        if op == TokenType.STAR:
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left * right
            if isinstance(left, str) and isinstance(right, int):
                return left * right
            if isinstance(left, list) and isinstance(right, int):
                return left * right
            raise NovaRuntimeError(f"Invalid operands for '*': '{type(left).__name__}' and '{type(right).__name__}'.", line, col)

        if op == TokenType.SLASH:
            self._check_number_operands(expr.operator, left, right)
            if right == 0:
                raise NovaRuntimeError("Division by zero.", line, col)
            return left / right

        if op == TokenType.PERCENT:
            self._check_number_operands(expr.operator, left, right)
            if right == 0:
                raise NovaRuntimeError("Modulo by zero.", line, col)
            return left % right

        # Equality
        if op == TokenType.EQ:
            return left == right
        if op == TokenType.NOT_EQ:
            return left != right

        # Relational
        if op == TokenType.LT:
            self._check_comparable_operands(expr.operator, left, right)
            return left < right
        if op == TokenType.LTE:
            self._check_comparable_operands(expr.operator, left, right)
            return left <= right
        if op == TokenType.GT:
            self._check_comparable_operands(expr.operator, left, right)
            return left > right
        if op == TokenType.GTE:
            self._check_comparable_operands(expr.operator, left, right)
            return left >= right

        raise NovaRuntimeError(f"Unknown binary operator: {expr.operator.lexeme}", line, col)

    def visit_UnaryExpr(self, expr: UnaryExpr) -> Any:
        right = self.eval_expr(expr.right)
        op = expr.operator.type
        if op == TokenType.MINUS:
            if not isinstance(right, (int, float)):
                raise NovaRuntimeError("Unary '-' operand must be a number.", expr.operator.line, expr.operator.column)
            return -right
        if op == TokenType.BANG:
            return not self._is_truthy(right)

        raise NovaRuntimeError(f"Unknown unary operator: {expr.operator.lexeme}", expr.operator.line, expr.operator.column)

    def visit_LogicalExpr(self, expr: LogicalExpr) -> Any:
        left = self.eval_expr(expr.left)
        op = expr.operator.type
        # Short-circuiting
        if op == TokenType.OR:
            if self._is_truthy(left):
                return left
            return self.eval_expr(expr.right)
        if op == TokenType.AND:
            if not self._is_truthy(left):
                return left
            return self.eval_expr(expr.right)

        raise NovaRuntimeError(f"Unknown logical operator: {expr.operator.lexeme}", expr.operator.line, expr.operator.column)

    def visit_CallExpr(self, expr: CallExpr) -> Any:
        callee = self.eval_expr(expr.callee)
        arguments = [self.eval_expr(arg) for arg in expr.arguments]

        if not isinstance(callee, NovaCallable):
            raise NovaRuntimeError("Can only call functions and classes.", expr.paren.line, expr.paren.column)

        expected_arity = callee.arity()
        if expected_arity != -1 and len(arguments) != expected_arity:
            raise NovaRuntimeError(
                f"Expected {expected_arity} arguments but got {len(arguments)}.",
                expr.paren.line,
                expr.paren.column
            )

        return callee.call(self, arguments, expr.paren)

    def visit_FunctionExpr(self, expr: FunctionExpr) -> Any:
        return NovaFunction(
            name="<anonymous>",
            params=expr.params,
            body=expr.body,
            closure=self.current_env
        )

    def visit_ListExpr(self, expr: ListExpr) -> Any:
        return [self.eval_expr(e) for e in expr.elements]

    def visit_IndexExpr(self, expr: IndexExpr) -> Any:
        target = self.eval_expr(expr.target)
        index = self.eval_expr(expr.index)

        if isinstance(target, list):
            if not isinstance(index, int):
                raise NovaRuntimeError("List index must be an integer.", expr.bracket.line, expr.bracket.column)
            if index < 0 or index >= len(target):
                raise NovaRuntimeError(f"List index out of range: {index}.", expr.bracket.line, expr.bracket.column)
            return target[index]

        if isinstance(target, str):
            if not isinstance(index, int):
                raise NovaRuntimeError("String index must be an integer.", expr.bracket.line, expr.bracket.column)
            if index < 0 or index >= len(target):
                raise NovaRuntimeError(f"String index out of range: {index}.", expr.bracket.line, expr.bracket.column)
            return target[index]

        raise NovaRuntimeError(f"Cannot index object of type '{type(target).__name__}'.", expr.bracket.line, expr.bracket.column)

    # ==========================================
    # Helpers
    # ==========================================
    def _is_truthy(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, list):
            return len(value) > 0
        return True

    def _check_number_operands(self, operator: Token, left: Any, right: Any):
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return
        raise NovaRuntimeError("Operands must be numbers.", operator.line, operator.column)

    def _check_comparable_operands(self, operator: Token, left: Any, right: Any):
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return
        if isinstance(left, str) and isinstance(right, str):
            return
        raise NovaRuntimeError("Operands must be of comparable types.", operator.line, operator.column)

    def _stringify(self, value: Any) -> str:
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return str(value)
        if isinstance(value, list):
            items_str = ", ".join(self._stringify(item) for item in value)
            return f"[{items_str}]"
        return str(value)
