# 🌌 Nova Programming Language

> A custom, dynamically typed, lexically scoped interpreted programming language built from first principles in Python, accompanied by an interactive browser-based WebAssembly playground in React.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/react-18.x-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.x-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg?style=flat)](LICENSE)

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture & Pipeline](#-architecture--pipeline)
- [Language Syntax Tour](#-language-syntax-tour)
- [The Loop-Scoping Challenge & Solution](#-the-loop-scoping-challenge--solution)
- [Browser Playground & REPL](#-browser-playground--repl)
- [Quick Start](#-quick-start)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Engineering Highlights](#-engineering-highlights)
- [License](#-license)

---

## 🚀 Overview

**Nova** is designed to explore programming language semantics, abstract syntax tree (AST) execution, activation records, and lexical environment resolution.

It features a full compiler-front-to-runtime pipeline:
1. **Lexical Analyzer (Scanner):** Converts source code into typed tokens with exact coordinate tracking (line/column).
2. **Parser (Recursive Descent + Pratt):** Employs Pratt parsing for expressions to handle operator precedence gracefully.
3. **AST Evaluator:** A visitor-pattern tree-walk interpreter.
4. **Lexical Scope Engine:** Implements hierarchical environment frames with immutability guarantees.
5. **Interactive Web REPL:** Client-side React/TypeScript playground running the engine via WebAssembly (Pyodide).

---

## ✨ Key Features

* **Immutability by Default:** Declarations via `let` are immutable; mutable bindings require explicit `let mut`.
* **First-Class Functions & Closures:** Functions capture their enclosing lexical environment at creation time.
* **Per-Iteration Frame Isolation:** Prevents loop counter alias leaks across closure invocations.
* **Pratt Operator Precedence:** Clean evaluation of arithmetic, relational, and equality operators without grammar bloat.
* **Zero-Install Web Playground:** Run code directly in your browser with real-time AST tree and scope inspection.

---

## 🏗️ Architecture & Pipeline

```
+-----------------------------------------------------------------------+
|                             NOVA PIPELINE                             |
+-----------------------------------------------------------------------+
|                                                                       |
|  Source Code (.nv)                                                    |
|        │                                                              |
|        ▼                                                              |
|  [ Lexer (Scanner) ]          ──► Emits Token Stream                  |
|        │                                                              |
|        ▼                                                              |
|  [ Pratt / Descent Parser ]   ──► Generates Typed AST                 |
|        │                                                              |
|        ▼                                                              |
|  [ Tree-Walk Evaluator ]      ◄─► [ Lexical Environment Chain ]       |
|        │                                                              |
|        ▼                                                              |
|  Standard Output / Web REPL State Stream                              |
+-----------------------------------------------------------------------+
```

---

## 📖 Language Syntax Tour

### Variables & Immutability
```nova
let language = "Nova";      // Immutable
// language = "Other";      // Runtime Error: Cannot reassign immutable variable 'language'

let mut counter = 0;        // Mutable
counter = counter + 1;      // Valid
```

### Functions & First-Class Closures
```nova
fn make_multiplier(factor) {
    return fn(value) {
        return value * factor;
    };
}

let double = make_multiplier(2);
let triple = make_multiplier(3);

print(double(10)); // 20
print(triple(10)); // 30
```

### Control Flow & Clean Loop Iteration
```nova
let mut i = 0;
let mut sum = 0;

while (i < 5) {
    let current = i;
    sum = sum + current;
    i = i + 1;
}

print(sum); // 10
```

---

## 🔬 The Loop-Scoping Challenge & Solution

During interpreter development, closures instantiated inside loops exposed a critical scoping bug:

```nova
let mut callbacks = [];
let mut i = 0;

while (i < 3) {
    let captured = i;
    callbacks.push(fn() { return captured; });
    i = i + 1;
}
```

### The Problem
When the loop reused a single mutable environment frame across all passes, mutating `i` updated the referenced frame in place. All closures subsequently returned `2`.

### The Solution: Per-Iteration Frame Isolation
Nova was re-architected to fork a **discrete environment frame per loop iteration**. Outer mutable variables are resolved up the parent chain, while per-iteration bindings (`captured`) are isolated within their iteration frame:

```
Iteration 0 Frame [captured: 0] <--- Callback 0
        │
Iteration 1 Frame [captured: 1] <--- Callback 1
        │
Iteration 2 Frame [captured: 2] <--- Callback 2
        │ (parent pointer)
[Outer Enclosing Scope] [i: 3]
```

---

## 🌐 Browser Playground & REPL

The Nova Web Playground runs entirely client-side using **WebAssembly (Pyodide)** and **Web Workers**:

* **Non-blocking Execution:** Prevents UI freezes on long-running code.
* **Live AST Explorer:** Collapsible interactive tree visualizer.
* **Active Scope Inspector:** Visual representation of active environment bindings.

---

## ⚡ Quick Start

### 1. Prerequisites
* Python 3.10+
* Node.js 18+ (for Web Playground)

### 2. CLI Execution
```bash
# Clone the repository
git clone https://github.com/yourusername/nova-lang.git
cd nova-lang

# Run a Nova script
python3 -m nova.cli run examples/closures.nv

# Start the interactive CLI REPL
python3 -m nova.cli repl
```

### 3. Frontend Playground
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing & Quality Assurance

Nova includes a comprehensive test suite covering edge cases, syntax diagnostics, and closure isolation:

```bash
# Run test suite
pytest tests/ -v --cov=nova
```

---

## 💡 Engineering Highlights

* **Pure Standard Library Core:** The language engine requires zero third-party dependencies.
* **Deterministic Line/Col Mapping:** Error messages pinpoint exact source coordinates.
* **Pratt Operator Precedence:** Scales cleanly to arbitrary binary and unary operators.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
