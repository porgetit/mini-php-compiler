"""Modulo backend: fachada y componentes del compilador."""

from .ast_nodes import *  # re-export para consumo externo
from .lexer import LexerConfig, PhpLexer
from .parser import build_parser
from .facade import CompilerFacade, CompilationResult

__all__ = [
    "CompilerFacade",
    "CompilationResult",
    "LexerConfig",
    "PhpLexer",
    "build_parser",
] + [name for name in list(globals()) if name[0].isupper()]
