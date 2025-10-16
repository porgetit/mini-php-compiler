"""Punto de entrada principal para el mini compilador de PHP.

Proporciona una interfaz de linea de comandos que permite:
  * Imprimir los tokens generados por el lexer.
  * Construir el AST mediante el parser.
  * Mostrar el AST resultante en formato JSON opcionalmente.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Sequence

from lexer import PhpLexer
from parser import build_parser


def _load_source(path: str) -> str:
    source_path = Path(path)
    if not source_path.exists():
        print(f"[Main] No se encontro el archivo: {source_path}", file=sys.stderr)
        raise SystemExit(1)
    try:
        return source_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[Main] Error al leer {source_path}: {exc}", file=sys.stderr)
        raise SystemExit(1)


def _print_tokens(code: str) -> None:
    lexer = PhpLexer()
    print("=== TOKENS ===")
    for token in lexer.tokenize(code):
        value_repr = repr(token.value)
        print(f"{token.lineno:04d}: {token.type:<12} {value_repr}")
    print()


def _to_serializable(obj: Any) -> Any:
    if is_dataclass(obj):
        return {key: _to_serializable(val) for key, val in asdict(obj).items()}
    if isinstance(obj, list):
        return [_to_serializable(item) for item in obj]
    if isinstance(obj, tuple):
        return [_to_serializable(item) for item in obj]
    return obj


def _parse(code: str):
    parser = build_parser()
    return parser.parse(code, lexer=PhpLexer().lexer)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compilador reducido de PHP: lexing + parsing."
    )
    parser.add_argument(
        "fuente",
        help="Ruta al archivo PHP que se desea analizar.",
    )
    parser.add_argument(
        "--tokens",
        action="store_true",
        help="Imprime la secuencia de tokens generados por el lexer.",
    )
    parser.add_argument(
        "--ast",
        action="store_true",
        help="Muestra el AST resultante en formato JSON.",
    )

    args = parser.parse_args(argv)
    code = _load_source(args.fuente)

    if args.tokens:
        _print_tokens(code)

    ast = _parse(code)
    if ast is None:
        print("[Main] Se encontraron errores durante el parseo.", file=sys.stderr)
        return 1

    print("[Main] Parseo completado correctamente.")

    if args.ast:
        print("=== AST ===")
        serializable = _to_serializable(ast)
        print(json.dumps(serializable, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
