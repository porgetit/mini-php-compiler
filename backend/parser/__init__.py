"""Puerta de entrada del paquete parser."""

from .core import (
    build_parser,
    parse_php,
    Program,
    NamespaceDecl,
    UseDecl,
    ClassDecl,
    FunctionDecl,
    Param,
    Block,
    EmptyStmt,
    EchoStmt,
    PrintStmt,
    ReturnStmt,
    IncludeStmt,
    RequireStmt,
    IfStmt,
    WhileStmt,
    ForStmt,
    ForeachStmt,
    VarDeclStmt,
    ExprStmt,
    Name,
    Var,
    NumberLit,
    StringLit,
    BoolLit,
    NullLit,
    ArrayLit,
    Assign,
    Binary,
    Unary,
    PostfixUnary,
    Call,
    Index,
    Member,
    StaticAccess,
    New,
    Ternary,
)


def demo(code: str) -> None:
    """Parsea una cadena de codigo PHP y muestra AST y errores."""
    from ..lexer import PhpLexer

    parser = build_parser()
    ast = parser.parse(code, lexer=PhpLexer().lexer)
    print(f"Errores de sintaxis: {parser.error_count}")
    from pprint import pprint

    pprint(ast)


if __name__ == "__main__":
    import sys
    from ..lexer import PhpLexer

    sample = "<?php $a = 1 + 2; ?>"
    code = sample if len(sys.argv) == 1 else open(sys.argv[1], encoding="utf-8").read()
    demo(code)
