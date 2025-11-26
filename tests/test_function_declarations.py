from textwrap import dedent

from backend.ast_nodes import ClassDecl, FunctionDecl
from backend.lexer import PhpLexer
from backend.parser import build_parser


def test_top_level_function_after_class_parses():
    code = dedent(
        """<?php
        class Greeter {
            public function greet($name = "friend") {
                echo $name;
            }
        }

        function test() {
            $greeter = new Greeter();
            $greeter->greet("World");
        }
        ?>"""
    )

    parser = build_parser()
    ast = parser.parse(code, lexer=PhpLexer().lexer)

    assert parser.error_count == 0
    assert ast is not None
    assert len(ast.items) == 2
    assert isinstance(ast.items[0], ClassDecl)
    assert isinstance(ast.items[1], FunctionDecl)

    func = ast.items[1]
    assert func.name == "test"
    assert func.params == []
    assert len(func.body.stmts) == 2
