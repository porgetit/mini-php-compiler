"""Fachada de alto nivel para el compilador PHP reducido."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .lexer import PhpLexer
from .parser import build_parser


def _to_serializable(obj: Any) -> Any:
    """Convierte dataclasses y tuplas a objetos JSON friendly."""
    from dataclasses import asdict, is_dataclass

    if is_dataclass(obj):
        return {key: _to_serializable(val) for key, val in asdict(obj).items()}
    if isinstance(obj, list):
        return [_to_serializable(item) for item in obj]
    if isinstance(obj, tuple):
        return [_to_serializable(item) for item in obj]
    return obj


def _collect_tokens(code: str, reporter=None) -> List[dict]:
    lexer = PhpLexer(reporter=reporter)
    tokens = []
    for token in lexer.tokenize(code):
        tokens.append(
            {"lineno": token.lineno, "type": token.type, "value": token.value}
        )
    return tokens


def _safe_json_dump(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except TypeError:
        return json.dumps(str(obj), ensure_ascii=False)


@dataclass
class CompilationResult:
    ok: bool
    tokens: List[Dict[str, Any]]
    ast: Any
    ast_json: Optional[str]
    lexical_errors: int
    syntax_errors: int
    lexical_messages: List[Dict[str, str]]
    syntax_messages: List[Dict[str, str]]
    source_path: Optional[str]


class CompilerFacade:
    """Punto de entrada para compilar codigo PHP desde la GUI o adaptadores."""

    def __init__(self, project_root: Path | str | None = None) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()

    def compile(self, code: str, path: str | Path | None = None) -> CompilationResult:
        lexical_messages: List[Dict[str, str]] = []
        syntax_messages: List[Dict[str, str]] = []

        def _lex_reporter(level: str, message: str) -> None:
            lexical_messages.append({"level": level, "message": message})

        def _syn_reporter(level: str, message: str) -> None:
            syntax_messages.append({"level": level, "message": message})

        parser = build_parser(reporter=_syn_reporter)
        parse_lexer = PhpLexer(reporter=_lex_reporter)
        ast = parser.parse(code, lexer=parse_lexer.lexer)

        tokens = _collect_tokens(code, reporter=lambda *_: None)

        lexical_errors = parse_lexer.error_count
        syntax_errors = parser.error_count
        ok = ast is not None and lexical_errors == 0 and syntax_errors == 0

        ast_serializable = _to_serializable(ast) if ast is not None else None

        return CompilationResult(
            ok=ok,
            tokens=tokens,
            ast=ast_serializable,
            ast_json=_safe_json_dump(ast_serializable) if ast_serializable is not None else None,
            lexical_errors=lexical_errors,
            syntax_errors=syntax_errors,
            lexical_messages=lexical_messages,
            syntax_messages=syntax_messages,
            source_path=str(path) if path is not None else None,
        )
