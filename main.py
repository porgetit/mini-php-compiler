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
from typing import Any, List, Sequence

import shutil
from lexer import PhpLexer
from parser import build_parser
from datetime import datetime
from output_formatter import RichCompilerConsole


def _load_source(path: Path, formatter: RichCompilerConsole) -> str:
    if not path.exists():
        formatter.message(f"No se encontro el archivo: {path}", level="error", stderr=True)
        raise SystemExit(1)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        formatter.message(f"Error al leer {path}: {exc}", level="error", stderr=True)
        raise SystemExit(1)


def _collect_tokens(code: str) -> List[dict]:
    lexer = PhpLexer()
    tokens = []
    for token in lexer.tokenize(code):
        tokens.append(
            {"lineno": token.lineno, "type": token.type, "value": token.value}
        )
    return tokens


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
    ast = parser.parse(code, lexer=PhpLexer().lexer)
    return ast, parser


def _write_verbose_artifacts(
    source_path: Path,
    tokens: List[dict],
    ast_obj: Any,
    formatter: RichCompilerConsole | None = None,
) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        relative = source_path.resolve().relative_to(Path.cwd())
    except ValueError:
        relative = Path(source_path.name)
    base_dir = Path("reportes") / relative
    base_dir.mkdir(parents=True, exist_ok=True)

    destination_source = base_dir / source_path.name
    try:
        if source_path.resolve() != destination_source.resolve():
            shutil.copy2(source_path, destination_source)
        else:
            destination_source.write_text(source_path.read_text(encoding="utf-8"))
    except OSError as exc:
        message = f"No se pudo copiar el archivo fuente: {exc}"
        if formatter is not None:
            formatter.message(message, level="warning", stderr=True)
        else:
            print(f"[Main] {message}", file=sys.stderr)

    payload = {
        "timestamp": timestamp,
        "source": str(source_path),
        "tokens": tokens,
        "ast": _to_serializable(ast_obj) if ast_obj is not None else None,
        "parse_success": ast_obj is not None,
    }
    json_path = base_dir / f"{timestamp}.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return json_path


def main(argv: Sequence[str] | None = None) -> int:
    output = RichCompilerConsole()
    cli_parser = output.create_argument_parser(
        description="Compilador reducido de PHP: lexing + parsing."
    )
    cli_parser.add_argument(
        "fuente",
        help="Ruta al archivo PHP que se desea analizar.",
    )
    cli_parser.add_argument(
        "--tokens",
        action="store_true",
        help="Imprime la secuencia de tokens generados por el lexer.",
    )
    cli_parser.add_argument(
        "--ast",
        action="store_true",
        help="Muestra el AST resultante en formato JSON.",
    )
    cli_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Guarda tokens y AST en un artefacto JSON junto con el archivo fuente.",
    )
    args = cli_parser.parse_args(argv)
    source_path = Path(args.fuente)
    code = _load_source(source_path, output)

    tokens_data: List[dict] | None = None
    if args.tokens or args.verbose:
        tokens_data = _collect_tokens(code)
        if args.tokens:
            output.show_tokens(tokens_data)

    ast, parser_obj = _parse(code)
    error_count = getattr(parser_obj, "error_count", 0)

    if error_count:
        output.message("Se encontraron errores durante el parseo.", level="error", stderr=True)
        if args.verbose:
            if tokens_data is None:
                tokens_data = _collect_tokens(code)
            json_path = _write_verbose_artifacts(
                source_path,
                tokens_data,
                ast,
                formatter=output,
            )
            output.show_verbose_artifact(json_path)
        output.show_summary(error_count)
        return 1

    output.message("Parseo completado correctamente.", level="success")

    if args.ast:
        serializable = _to_serializable(ast)
        output.show_ast(serializable)

    if args.verbose:
        if tokens_data is None:
            tokens_data = _collect_tokens(code)
        json_path = _write_verbose_artifacts(
            source_path,
            tokens_data,
            ast,
            formatter=output,
        )
        output.show_verbose_artifact(json_path)

    output.show_summary(error_count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
