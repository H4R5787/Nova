"""
Nova Command Line Interface
Supports running scripts, interactive terminal REPL, AST dumping, and token inspection.
"""
import sys
import json
import argparse
from typing import Optional

import nova
from nova.errors import NovaError
from nova.evaluator import Evaluator
from nova.parser import Parser
from nova.lexer import Lexer


def run_file(filepath: str):
    """Execute a Nova source file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}", file=sys.stderr)
        sys.exit(1)

    try:
        nova.run(source, filename=filepath)
    except NovaError as e:
        print(e.format(filepath), file=sys.stderr)
        sys.exit(1)


def run_ast(filepath: str):
    """Parse a file and dump its Abstract Syntax Tree as structured JSON."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        ast = nova.parse(source, filename=filepath)
        print(json.dumps(ast.to_dict(), indent=2))
    except NovaError as e:
        print(e.format(filepath), file=sys.stderr)
        sys.exit(1)


def run_tokens(filepath: str):
    """Tokenize a file and print the token stream."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        tokens = nova.tokenize(source, filename=filepath)
        for t in tokens:
            print(f"{t.line:4}:{t.column:3} | {t.type.name:<12} | '{t.lexeme}' (literal: {t.literal})")
    except NovaError as e:
        print(e.format(filepath), file=sys.stderr)
        sys.exit(1)


def run_repl():
    """Interactive Read-Eval-Print Loop."""
    print("Nova Programming Language (v1.0.0)")
    print("Type 'exit' or press Ctrl+C to terminate session.\n")

    evaluator = Evaluator()

    while True:
        try:
            line = input("nova> ").strip()
            if not line:
                continue
            if line in ("exit", "quit"):
                break

            # If line doesn't end with semicolon or brace, add semicolon for convenience in REPL
            source_line = line
            if not source_line.endswith(";") and not source_line.endswith("}"):
                source_line += ";"

            tokens = Lexer(source_line, filename="<repl>").scan_tokens()
            parser = Parser(tokens, source=source_line, filename="<repl>")
            program = parser.parse()

            result = evaluator.evaluate_program(program)
            if result is not None:
                print(f"=> {evaluator._stringify(result)}")

        except KeyboardInterrupt:
            print("\nExiting Nova REPL.")
            break
        except EOFError:
            print("\nExiting Nova REPL.")
            break
        except NovaError as e:
            print(e.format("<repl>"))
        except Exception as e:
            print(f"Internal Runtime Exception: {e}")


def main():
    parser = argparse.ArgumentParser(description="Nova Language Toolchain")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 'run' command
    run_parser = subparsers.add_parser("run", help="Execute a .nv source file")
    run_parser.add_argument("file", help="Path to Nova source file")

    # 'repl' command
    subparsers.add_parser("repl", help="Start interactive Nova REPL")

    # 'ast' command
    ast_parser = subparsers.add_parser("ast", help="Dump AST of a .nv source file as JSON")
    ast_parser.add_argument("file", help="Path to Nova source file")

    # 'tokens' command
    tokens_parser = subparsers.add_parser("tokens", help="Display token stream for a .nv source file")
    tokens_parser.add_argument("file", help="Path to Nova source file")

    args = parser.parse_args()

    if args.command == "run":
        run_file(args.file)
    elif args.command == "repl":
        run_repl()
    elif args.command == "ast":
        run_ast(args.file)
    elif args.command == "tokens":
        run_tokens(args.file)
    else:
        # Default behavior: if a single argument is provided, treat it as a file to run; else run REPL
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            run_file(sys.argv[1])
        else:
            run_repl()


if __name__ == "__main__":
    main()
