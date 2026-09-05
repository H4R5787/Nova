/**
 * Nova In-Browser Engine
 * Complete client-side Lexer, Pratt Parser, and Lexical Environment Evaluator.
 * Mirrors Python runtime semantics 1:1.
 */

// Token Types
const TokenType = {
  NUMBER: 'NUMBER',
  STRING: 'STRING',
  BOOLEAN: 'BOOLEAN',
  NIL: 'NIL',
  IDENTIFIER: 'IDENTIFIER',
  LET: 'LET',
  MUT: 'MUT',
  FN: 'FN',
  IF: 'IF',
  ELSE: 'ELSE',
  WHILE: 'WHILE',
  FOR: 'FOR',
  RETURN: 'RETURN',
  BREAK: 'BREAK',
  CONTINUE: 'CONTINUE',
  PRINT: 'PRINT',
  ASSIGN: 'ASSIGN',
  PLUS: 'PLUS',
  MINUS: 'MINUS',
  STAR: 'STAR',
  SLASH: 'SLASH',
  PERCENT: 'PERCENT',
  BANG: 'BANG',
  EQ: 'EQ',
  NOT_EQ: 'NOT_EQ',
  LT: 'LT',
  LTE: 'LTE',
  GT: 'GT',
  GTE: 'GTE',
  AND: 'AND',
  OR: 'OR',
  LPAREN: 'LPAREN',
  RPAREN: 'RPAREN',
  LBRACE: 'LBRACE',
  RBRACE: 'RBRACE',
  LBRACKET: 'LBRACKET',
  RBRACKET: 'RBRACKET',
  SEMICOLON: 'SEMICOLON',
  COMMA: 'COMMA',
  EOF: 'EOF'
};

class NovaToken {
  constructor(type, lexeme, literal, line, column) {
    this.type = type;
    this.lexeme = lexeme;
    this.literal = literal;
    this.line = line;
    this.column = column;
  }
}

class NovaLexer {
  constructor(source) {
    this.source = source;
    this.tokens = [];
    this.start = 0;
    this.current = 0;
    this.line = 1;
    this.column = 1;
    this.tokenStartCol = 1;

    this.keywords = {
      let: TokenType.LET,
      mut: TokenType.MUT,
      fn: TokenType.FN,
      if: TokenType.IF,
      else: TokenType.ELSE,
      while: TokenType.WHILE,
      for: TokenType.FOR,
      return: TokenType.RETURN,
      break: TokenType.BREAK,
      continue: TokenType.CONTINUE,
      print: TokenType.PRINT,
      true: TokenType.BOOLEAN,
      false: TokenType.BOOLEAN,
      nil: TokenType.NIL,
      and: TokenType.AND,
      or: TokenType.OR
    };
  }

  scanTokens() {
    while (!this.isAtEnd()) {
      this.start = this.current;
      this.tokenStartCol = this.column;
      this.scanToken();
    }
    this.tokens.push(new NovaToken(TokenType.EOF, '', null, this.line, this.column));
    return this.tokens;
  }

  isAtEnd() {
    return this.current >= this.source.length;
  }

  advance() {
    const ch = this.source[this.current++];
    this.column++;
    return ch;
  }

  peek() {
    return this.isAtEnd() ? '\0' : this.source[this.current];
  }

  peekNext() {
    return (this.current + 1 >= this.source.length) ? '\0' : this.source[this.current + 1];
  }

  match(expected) {
    if (this.isAtEnd() || this.source[this.current] !== expected) return false;
    this.current++;
    this.column++;
    return true;
  }

  scanToken() {
    const c = this.advance();
    switch (c) {
      case ' ':
      case '\r':
      case '\t':
        break;
      case '\n':
        this.line++;
        this.column = 1;
        break;
      case '(': this.addToken(TokenType.LPAREN); break;
      case ')': this.addToken(TokenType.RPAREN); break;
      case '{': this.addToken(TokenType.LBRACE); break;
      case '}': this.addToken(TokenType.RBRACE); break;
      case '[': this.addToken(TokenType.LBRACKET); break;
      case ']': this.addToken(TokenType.RBRACKET); break;
      case ',': this.addToken(TokenType.COMMA); break;
      case ';': this.addToken(TokenType.SEMICOLON); break;
      case '+': this.addToken(TokenType.PLUS); break;
      case '-': this.addToken(TokenType.MINUS); break;
      case '*': this.addToken(TokenType.STAR); break;
      case '%': this.addToken(TokenType.PERCENT); break;
      case '!': this.addToken(this.match('=') ? TokenType.NOT_EQ : TokenType.BANG); break;
      case '=': this.addToken(this.match('=') ? TokenType.EQ : TokenType.ASSIGN); break;
      case '<': this.addToken(this.match('=') ? TokenType.LTE : TokenType.LT); break;
      case '>': this.addToken(this.match('=') ? TokenType.GTE : TokenType.GT); break;
      case '&':
        if (this.match('&')) this.addToken(TokenType.AND);
        else throw new Error(`Syntax Error: Unexpected character '&' at ${this.line}:${this.tokenStartCol}`);
        break;
      case '|':
        if (this.match('|')) this.addToken(TokenType.OR);
        else throw new Error(`Syntax Error: Unexpected character '|' at ${this.line}:${this.tokenStartCol}`);
        break;
      case '/':
        if (this.match('/')) {
          while (this.peek() !== '\n' && !this.isAtEnd()) this.advance();
        } else {
          this.addToken(TokenType.SLASH);
        }
        break;
      case '"': this.stringLiteral(); break;
      default:
        if (/\d/.test(c)) {
          this.numberLiteral();
        } else if (/[a-zA-Z_]/.test(c)) {
          this.identifier();
        } else {
          throw new Error(`Syntax Error: Unexpected character '${c}' at ${this.line}:${this.tokenStartCol}`);
        }
    }
  }

  stringLiteral() {
    let str = '';
    while (this.peek() !== '"' && !this.isAtEnd()) {
      if (this.peek() === '\n') {
        this.line++;
        this.column = 1;
      }
      if (this.peek() === '\\') {
        this.advance();
        const esc = this.advance();
        if (esc === 'n') str += '\n';
        else if (esc === 't') str += '\t';
        else str += esc;
      } else {
        str += this.advance();
      }
    }
    if (this.isAtEnd()) throw new Error(`Syntax Error: Unterminated string at line ${this.line}`);
    this.advance(); // closing quote
    this.addToken(TokenType.STRING, str);
  }

  numberLiteral() {
    while (/\d/.test(this.peek())) this.advance();
    if (this.peek() === '.' && /\d/.test(this.peekNext())) {
      this.advance();
      while (/\d/.test(this.peek())) this.advance();
    }
    const text = this.source.substring(this.start, this.current);
    this.addToken(TokenType.NUMBER, parseFloat(text));
  }

  identifier() {
    while (/[a-zA-Z0-9_]/.test(this.peek())) this.advance();
    const text = this.source.substring(this.start, this.current);
    const type = this.keywords[text] || TokenType.IDENTIFIER;
    let literal = null;
    if (type === TokenType.BOOLEAN) literal = text === 'true';
    this.addToken(type, literal);
  }

  addToken(type, literal = null) {
    const text = this.source.substring(this.start, this.current);
    this.tokens.push(new NovaToken(type, text, literal, this.line, this.tokenStartCol));
  }
}

// Precedence ranks
const PREC_NONE = 0;
const PREC_ASSIGNMENT = 1;
const PREC_OR = 2;
const PREC_AND = 3;
const PREC_EQUALITY = 4;
const PREC_COMPARISON = 5;
const PREC_TERM = 6;
const PREC_FACTOR = 7;
const PREC_UNARY = 8;
const PREC_CALL = 9;

class NovaParser {
  constructor(tokens) {
    this.tokens = tokens;
    this.current = 0;
    this.precedences = {
      [TokenType.ASSIGN]: PREC_ASSIGNMENT,
      [TokenType.OR]: PREC_OR,
      [TokenType.AND]: PREC_AND,
      [TokenType.EQ]: PREC_EQUALITY,
      [TokenType.NOT_EQ]: PREC_EQUALITY,
      [TokenType.LT]: PREC_COMPARISON,
      [TokenType.LTE]: PREC_COMPARISON,
      [TokenType.GT]: PREC_COMPARISON,
      [TokenType.GTE]: PREC_COMPARISON,
      [TokenType.PLUS]: PREC_TERM,
      [TokenType.MINUS]: PREC_TERM,
      [TokenType.STAR]: PREC_FACTOR,
      [TokenType.SLASH]: PREC_FACTOR,
      [TokenType.PERCENT]: PREC_FACTOR,
      [TokenType.LPAREN]: PREC_CALL,
      [TokenType.LBRACKET]: PREC_CALL
    };
  }

  parse() {
    const statements = [];
    while (!this.isAtEnd()) {
      statements.push(this.declaration());
    }
    return { type: 'Program', statements };
  }

  declaration() {
    if (this.match(TokenType.LET)) return this.varDeclaration();
    if (this.match(TokenType.FN) && this.check(TokenType.IDENTIFIER)) return this.functionDeclaration();
    return this.statement();
  }

  varDeclaration() {
    const isMutable = this.match(TokenType.MUT);
    const name = this.consume(TokenType.IDENTIFIER, "Expected variable name after 'let'.");
    let initializer = null;
    if (this.match(TokenType.ASSIGN)) {
      initializer = this.expression();
    }
    this.consume(TokenType.SEMICOLON, "Expected ';' after variable declaration.");
    return { type: 'LetStmt', name: name.lexeme, isMutable, initializer };
  }

  functionDeclaration() {
    const name = this.consume(TokenType.IDENTIFIER, 'Expected function name.');
    this.consume(TokenType.LPAREN, "Expected '(' after function name.");
    const params = [];
    if (!this.check(TokenType.RPAREN)) {
      do {
        params.push(this.consume(TokenType.IDENTIFIER, 'Expected parameter name.').lexeme);
      } while (this.match(TokenType.COMMA));
    }
    this.consume(TokenType.RPAREN, "Expected ')' after parameters.");
    this.consume(TokenType.LBRACE, "Expected '{' before function body.");
    const body = this.blockStatements();
    return { type: 'FunctionStmt', name: name.lexeme, params, body };
  }

  statement() {
    if (this.match(TokenType.PRINT)) return this.printStatement();
    if (this.match(TokenType.IF)) return this.ifStatement();
    if (this.match(TokenType.WHILE)) return this.whileStatement();
    if (this.match(TokenType.FOR)) return this.forStatement();
    if (this.match(TokenType.RETURN)) return this.returnStatement();
    if (this.match(TokenType.BREAK)) {
      this.consume(TokenType.SEMICOLON, "Expected ';' after 'break'.");
      return { type: 'BreakStmt' };
    }
    if (this.match(TokenType.CONTINUE)) {
      this.consume(TokenType.SEMICOLON, "Expected ';' after 'continue'.");
      return { type: 'ContinueStmt' };
    }
    if (this.match(TokenType.LBRACE)) return { type: 'BlockStmt', statements: this.blockStatements() };
    return this.expressionStatement();
  }

  printStatement() {
    const hasParen = this.match(TokenType.LPAREN);
    const expressions = [];
    if (!(hasParen && this.check(TokenType.RPAREN))) {
      do {
        expressions.push(this.expression());
      } while (this.match(TokenType.COMMA));
    }
    if (hasParen) this.consume(TokenType.RPAREN, "Expected ')' after print.");
    this.consume(TokenType.SEMICOLON, "Expected ';' after print statement.");
    return { type: 'PrintStmt', expressions };
  }

  ifStatement() {
    const hasParen = this.match(TokenType.LPAREN);
    const condition = this.expression();
    if (hasParen) this.consume(TokenType.RPAREN, "Expected ')' after if condition.");
    this.consume(TokenType.LBRACE, "Expected '{' after if condition.");
    const thenBranch = { type: 'BlockStmt', statements: this.blockStatements() };
    let elseBranch = null;
    if (this.match(TokenType.ELSE)) {
      if (this.match(TokenType.IF)) {
        elseBranch = this.ifStatement();
      } else {
        this.consume(TokenType.LBRACE, "Expected '{' after 'else'.");
        elseBranch = { type: 'BlockStmt', statements: this.blockStatements() };
      }
    }
    return { type: 'IfStmt', condition, thenBranch, elseBranch };
  }

  whileStatement() {
    const hasParen = this.match(TokenType.LPAREN);
    const condition = this.expression();
    if (hasParen) this.consume(TokenType.RPAREN, "Expected ')' after while condition.");
    this.consume(TokenType.LBRACE, "Expected '{' after while condition.");
    const body = { type: 'BlockStmt', statements: this.blockStatements() };
    return { type: 'WhileStmt', condition, body };
  }

  forStatement() {
    this.consume(TokenType.LPAREN, "Expected '(' after 'for'.");
    let initializer = null;
    if (this.match(TokenType.SEMICOLON)) initializer = null;
    else if (this.match(TokenType.LET)) initializer = this.varDeclaration();
    else initializer = this.expressionStatement();

    let condition = null;
    if (!this.check(TokenType.SEMICOLON)) condition = this.expression();
    this.consume(TokenType.SEMICOLON, "Expected ';' after for condition.");

    let increment = null;
    if (!this.check(TokenType.RPAREN)) increment = this.expression();
    this.consume(TokenType.RPAREN, "Expected ')' after for clauses.");

    this.consume(TokenType.LBRACE, "Expected '{' before loop body.");
    const body = { type: 'BlockStmt', statements: this.blockStatements() };
    return { type: 'ForStmt', initializer, condition, increment, body };
  }

  returnStatement() {
    let value = null;
    if (!this.check(TokenType.SEMICOLON)) value = this.expression();
    this.consume(TokenType.SEMICOLON, "Expected ';' after return.");
    return { type: 'ReturnStmt', value };
  }

  blockStatements() {
    const stmts = [];
    while (!this.check(TokenType.RBRACE) && !this.isAtEnd()) {
      stmts.push(this.declaration());
    }
    this.consume(TokenType.RBRACE, "Expected '}' after block.");
    return stmts;
  }

  expressionStatement() {
    const expr = this.expression();
    this.consume(TokenType.SEMICOLON, "Expected ';' after expression.");
    return { type: 'ExprStmt', expression: expr };
  }

  expression(precedence = PREC_NONE) {
    if (this.isAtEnd()) throw new Error('Unexpected end of input.');
    const token = this.advance();
    let left = this.prefixParse(token);

    while (precedence < this.currentPrecedence()) {
      const opToken = this.advance();
      left = this.infixParse(left, opToken);
    }
    return left;
  }

  currentPrecedence() {
    if (this.isAtEnd()) return PREC_NONE;
    return this.precedences[this.peek().type] || PREC_NONE;
  }

  prefixParse(token) {
    if (token.type === TokenType.NUMBER || token.type === TokenType.STRING || token.type === TokenType.BOOLEAN) {
      return { type: 'LiteralExpr', value: token.literal };
    }
    if (token.type === TokenType.NIL) return { type: 'LiteralExpr', value: null };
    if (token.type === TokenType.IDENTIFIER) return { type: 'VariableExpr', name: token.lexeme };

    if (token.type === TokenType.BANG || token.type === TokenType.MINUS) {
      const right = this.expression(PREC_UNARY);
      return { type: 'UnaryExpr', operator: token.lexeme, right };
    }

    if (token.type === TokenType.LPAREN) {
      const expr = this.expression(PREC_NONE);
      this.consume(TokenType.RPAREN, "Expected ')' after grouped expression.");
      return expr;
    }

    if (token.type === TokenType.LBRACKET) {
      const elements = [];
      if (!this.check(TokenType.RBRACKET)) {
        do {
          elements.push(this.expression(PREC_NONE));
        } while (this.match(TokenType.COMMA));
      }
      this.consume(TokenType.RBRACKET, "Expected ']' after list elements.");
      return { type: 'ListExpr', elements };
    }

    if (token.type === TokenType.FN) {
      this.consume(TokenType.LPAREN, "Expected '(' after 'fn'.");
      const params = [];
      if (!this.check(TokenType.RPAREN)) {
        do {
          params.push(this.consume(TokenType.IDENTIFIER, 'Expected parameter name.').lexeme);
        } while (this.match(TokenType.COMMA));
      }
      this.consume(TokenType.RPAREN, "Expected ')' after parameter list.");
      this.consume(TokenType.LBRACE, "Expected '{' before function body.");
      const body = this.blockStatements();
      return { type: 'FunctionExpr', params, body };
    }

    throw new Error(`Syntax Error: Unexpected token '${token.lexeme}' at line ${token.line}`);
  }

  infixParse(left, token) {
    if (token.type === TokenType.ASSIGN) {
      const right = this.expression(PREC_ASSIGNMENT - 1);
      if (left.type === 'VariableExpr') {
        return { type: 'AssignExpr', name: left.name, value: right };
      }
      if (left.type === 'IndexExpr') {
        return { type: 'IndexAssignExpr', target: left.target, index: left.index, value: right };
      }
      throw new Error(`Invalid assignment target at line ${token.line}`);
    }

    if (token.type === TokenType.LPAREN) {
      const args = [];
      if (!this.check(TokenType.RPAREN)) {
        do {
          args.push(this.expression(PREC_NONE));
        } while (this.match(TokenType.COMMA));
      }
      this.consume(TokenType.RPAREN, "Expected ')' after function arguments.");
      return { type: 'CallExpr', callee: left, arguments: args };
    }

    if (token.type === TokenType.LBRACKET) {
      const index = this.expression(PREC_NONE);
      this.consume(TokenType.RBRACKET, "Expected ']' after index expression.");
      return { type: 'IndexExpr', target: left, index };
    }

    if (token.type === TokenType.AND || token.type === TokenType.OR) {
      const prec = this.precedences[token.type];
      const right = this.expression(prec);
      return { type: 'LogicalExpr', operator: token.lexeme, left, right };
    }

    const prec = this.precedences[token.type];
    const right = this.expression(prec);
    return { type: 'BinaryExpr', operator: token.lexeme, left, right };
  }

  match(...types) {
    for (const t of types) {
      if (this.check(t)) {
        this.advance();
        return true;
      }
    }
    return false;
  }

  check(type) {
    return !this.isAtEnd() && this.peek().type === type;
  }

  advance() {
    if (!this.isAtEnd()) this.current++;
    return this.tokens[this.current - 1];
  }

  isAtEnd() {
    return this.peek().type === TokenType.EOF;
  }

  peek() {
    return this.tokens[this.current];
  }

  consume(type, message) {
    if (this.check(type)) return this.advance();
    throw new Error(`Syntax Error: ${message} (Got '${this.peek().lexeme}' at line ${this.peek().line})`);
  }
}

// Runtime Environment
class NovaEnvironment {
  constructor(parent = null, name = 'block') {
    this.values = new Map();
    this.mutability = new Map();
    this.parent = parent;
    this.name = name;
  }

  define(name, value, isMutable = false) {
    if (this.values.has(name)) {
      throw new Error(`Runtime Error: Variable '${name}' is already defined in scope '${this.name}'.`);
    }
    this.values.set(name, value);
    this.mutability.set(name, isMutable);
  }

  get(name) {
    if (this.values.has(name)) return this.values.get(name);
    if (this.parent !== null) return this.parent.get(name);
    throw new Error(`Runtime Error: Undefined variable '${name}'.`);
  }

  assign(name, value) {
    if (this.values.has(name)) {
      if (!this.mutability.get(name)) {
        throw new Error(`Runtime Error: Cannot reassign immutable variable '${name}'. Declare with 'let mut ${name}' to allow mutation.`);
      }
      this.values.set(name, value);
      return;
    }
    if (this.parent !== null) {
      this.parent.assign(name, value);
      return;
    }
    throw new Error(`Runtime Error: Cannot assign to undefined variable '${name}'.`);
  }

  dumpSnapshot() {
    const bindings = {};
    for (const [k, v] of this.values.entries()) {
      let repr = typeof v === 'function' ? '<function>' : JSON.stringify(v);
      bindings[k] = { value: repr, mutable: this.mutability.get(k) };
    }
    return {
      scope: this.name,
      bindings,
      parent: this.parent ? this.parent.dumpSnapshot() : null
    };
  }
}

// Runtime Evaluator
class NovaEvaluator {
  constructor(outputCallback = console.log) {
    this.outputCallback = outputCallback;
    this.globalEnv = new NovaEnvironment(null, 'global');
    this.currentEnv = this.globalEnv;
    this.initBuiltins();
  }

  initBuiltins() {
    this.globalEnv.define('print', (...args) => {
      const line = args.map(a => this.stringify(a)).join(' ');
      this.outputCallback(line);
      return null;
    }, false);

    this.globalEnv.define('len', (target) => {
      if (Array.isArray(target) || typeof target === 'string') return target.length;
      throw new Error('len() requires array or string.');
    }, false);

    this.globalEnv.define('push', (arr, item) => {
      if (Array.isArray(arr)) {
        arr.push(item);
        return arr;
      }
      throw new Error('push() requires list as first argument.');
    }, false);

    this.globalEnv.define('pop', (arr) => {
      if (Array.isArray(arr)) {
        if (arr.length === 0) throw new Error('pop() called on empty list.');
        return arr.pop();
      }
      throw new Error('pop() requires list.');
    }, false);
  }

  evaluate(ast) {
    let res = null;
    for (const stmt of ast.statements) {
      res = this.execute(stmt);
    }
    return res;
  }

  execute(stmt) {
    switch (stmt.type) {
      case 'PrintStmt': {
        const vals = stmt.expressions.map(e => this.evalExpr(e));
        const line = vals.map(v => this.stringify(v)).join(' ');
        this.outputCallback(line);
        return null;
      }
      case 'LetStmt': {
        const val = stmt.initializer ? this.evalExpr(stmt.initializer) : null;
        this.currentEnv.define(stmt.name, val, stmt.isMutable);
        return val;
      }
      case 'BlockStmt': {
        return this.executeBlock(stmt.statements, new NovaEnvironment(this.currentEnv, 'block'));
      }
      case 'IfStmt': {
        if (this.isTruthy(this.evalExpr(stmt.condition))) {
          return this.execute(stmt.thenBranch);
        } else if (stmt.elseBranch) {
          return this.execute(stmt.elseBranch);
        }
        return null;
      }
      case 'WhileStmt': {
        let res = null;
        while (this.isTruthy(this.evalExpr(stmt.condition))) {
          // Discrete Per-Iteration Environment Frame!
          const iterEnv = new NovaEnvironment(this.currentEnv, 'while_iter');
          try {
            res = this.executeBlock(stmt.body.statements, iterEnv);
          } catch (e) {
            if (e === 'BREAK') break;
            if (e === 'CONTINUE') continue;
            throw e;
          }
        }
        return res;
      }
      case 'ForStmt': {
        const forEnv = new NovaEnvironment(this.currentEnv, 'for_scope');
        const prev = this.currentEnv;
        this.currentEnv = forEnv;
        try {
          if (stmt.initializer) this.execute(stmt.initializer);
          let res = null;
          while (true) {
            if (stmt.condition && !this.isTruthy(this.evalExpr(stmt.condition))) break;
            const iterEnv = new NovaEnvironment(this.currentEnv, 'for_iter');
            try {
              res = this.executeBlock(stmt.body.statements, iterEnv);
            } catch (e) {
              if (e === 'BREAK') break;
              if (e === 'CONTINUE') {}
              else throw e;
            }
            if (stmt.increment) this.evalExpr(stmt.increment);
          }
          return res;
        } finally {
          this.currentEnv = prev;
        }
      }
      case 'FunctionStmt': {
        const closure = this.currentEnv;
        const fn = (...args) => {
          const fnEnv = new NovaEnvironment(closure, `fn_${stmt.name}`);
          stmt.params.forEach((param, i) => fnEnv.define(param, args[i], true));
          try {
            return this.executeBlock(stmt.body, fnEnv);
          } catch (e) {
            if (e && e.__isReturn) return e.value;
            throw e;
          }
        };
        fn.__name = stmt.name;
        this.currentEnv.define(stmt.name, fn, false);
        return fn;
      }
      case 'ReturnStmt': {
        const val = stmt.value ? this.evalExpr(stmt.value) : null;
        throw { __isReturn: true, value: val };
      }
      case 'BreakStmt': throw 'BREAK';
      case 'ContinueStmt': throw 'CONTINUE';
      case 'ExprStmt': return this.evalExpr(stmt.expression);
      default:
        throw new Error(`Unknown statement type: ${stmt.type}`);
    }
  }

  executeBlock(statements, env) {
    const prev = this.currentEnv;
    this.currentEnv = env;
    try {
      let res = null;
      for (const s of statements) res = this.execute(s);
      return res;
    } finally {
      this.currentEnv = prev;
    }
  }

  evalExpr(expr) {
    switch (expr.type) {
      case 'LiteralExpr': return expr.value;
      case 'VariableExpr': return this.currentEnv.get(expr.name);
      case 'AssignExpr': {
        const val = this.evalExpr(expr.value);
        this.currentEnv.assign(expr.name, val);
        return val;
      }
      case 'IndexAssignExpr': {
        const target = this.evalExpr(expr.target);
        const index = this.evalExpr(expr.index);
        const val = this.evalExpr(expr.value);
        if (!Array.isArray(target)) throw new Error('Index assignment requires a list.');
        target[index] = val;
        return val;
      }
      case 'BinaryExpr': {
        const left = this.evalExpr(expr.left);
        const right = this.evalExpr(expr.right);
        switch (expr.operator) {
          case '+': return (typeof left === 'string' || typeof right === 'string') ? `${this.stringify(left)}${this.stringify(right)}` : left + right;
          case '-': return left - right;
          case '*': return left * right;
          case '/':
            if (right === 0) throw new Error('Division by zero.');
            return left / right;
          case '%':
            if (right === 0) throw new Error('Modulo by zero.');
            return left % right;
          case '==': return left === right;
          case '!=': return left !== right;
          case '<': return left < right;
          case '<=': return left <= right;
          case '>': return left > right;
          case '>=': return left >= right;
        }
        throw new Error(`Unknown operator: ${expr.operator}`);
      }
      case 'UnaryExpr': {
        const right = this.evalExpr(expr.right);
        if (expr.operator === '-') return -right;
        if (expr.operator === '!') return !this.isTruthy(right);
        throw new Error(`Unknown unary operator: ${expr.operator}`);
      }
      case 'LogicalExpr': {
        const left = this.evalExpr(expr.left);
        if (expr.operator === 'or' || expr.operator === '||') {
          if (this.isTruthy(left)) return left;
          return this.evalExpr(expr.right);
        }
        if (expr.operator === 'and' || expr.operator === '&&') {
          if (!this.isTruthy(left)) return left;
          return this.evalExpr(expr.right);
        }
        throw new Error(`Unknown logical operator: ${expr.operator}`);
      }
      case 'CallExpr': {
        const callee = this.evalExpr(expr.callee);
        const args = expr.arguments.map(a => this.evalExpr(a));
        if (typeof callee !== 'function') throw new Error('Can only call functions.');
        return callee(...args);
      }
      case 'FunctionExpr': {
        const closure = this.currentEnv;
        const lambda = (...args) => {
          const fnEnv = new NovaEnvironment(closure, 'lambda');
          expr.params.forEach((param, i) => fnEnv.define(param, args[i], true));
          try {
            return this.executeBlock(expr.body, fnEnv);
          } catch (e) {
            if (e && e.__isReturn) return e.value;
            throw e;
          }
        };
        return lambda;
      }
      case 'ListExpr': return expr.elements.map(e => this.evalExpr(e));
      case 'IndexExpr': {
        const target = this.evalExpr(expr.target);
        const index = this.evalExpr(expr.index);
        if (Array.isArray(target) || typeof target === 'string') {
          if (index < 0 || index >= target.length) throw new Error(`Index out of range: ${index}`);
          return target[index];
        }
        throw new Error('Cannot index non-collection.');
      }
      default:
        throw new Error(`Unknown expression type: ${expr.type}`);
    }
  }

  isTruthy(val) {
    if (val === null || val === undefined || val === false || val === 0 || val === '') return false;
    return true;
  }

  stringify(val) {
    if (val === null || val === undefined) return 'nil';
    if (typeof val === 'boolean') return val ? 'true' : 'false';
    if (typeof val === 'function') return '<function>';
    if (Array.isArray(val)) return `[${val.map(v => this.stringify(v)).join(', ')}]`;
    return String(val);
  }
}

// Global Nova object for browser
window.Nova = {
  run: (source, onOutput) => {
    const lexer = new NovaLexer(source);
    const tokens = lexer.scanTokens();
    const parser = new NovaParser(tokens);
    const ast = parser.parse();
    const evaluator = new NovaEvaluator(onOutput);
    const result = evaluator.evaluate(ast);
    return {
      ast,
      result,
      scope: evaluator.currentEnv.dumpSnapshot()
    };
  },
  parseAST: (source) => {
    const lexer = new NovaLexer(source);
    const tokens = lexer.scanTokens();
    const parser = new NovaParser(tokens);
    return parser.parse();
  }
};
