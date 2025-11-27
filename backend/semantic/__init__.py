"""Paquete de analisis semantico."""

from .errors import SemanticError
from .symbol_table import Symbol, SymbolTable
from .semantic_analyzer import SemanticAnalyzer

__all__ = ["SemanticError", "Symbol", "SymbolTable", "SemanticAnalyzer"]


def demo(code: str) -> None:
    """Ejecuta analisis semantico rapido sobre codigo PHP."""
    from ..lexer import PhpLexer
    from ..parser import build_parser

    parser = build_parser()
    ast = parser.parse(code, lexer=PhpLexer().lexer)
    if parser.error_count:
        print(f"Errores sintacticos: {parser.error_count}")
        return

    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(ast)
    print(f"Errores semanticos: {len(errors)}")
    for err in errors:
        print(err)
    print("Tabla de simbolos (snapshot):")
    from pprint import pprint

    pprint(analyzer.snapshot_data)


if __name__ == "__main__":
    sample = "<?php function f($x=1){ $y=$x; } ?>"
    demo(sample)
