from backend.lexer import PhpLexer
from backend.parser import build_parser
from backend.ast_nodes import VarDeclStmt, Ternary


def test_ternary_expression_parses_and_uses_tokens():
    code = "<?php $a = $flag ? 'yes' : 'no'; ?>"

    # tokens incluyen ? y :
    tokens = [tok.type for tok in PhpLexer().tokenize(code)]
    assert "QUESTION" in tokens and "COLON" in tokens

    parser = build_parser()
    ast = parser.parse(code, lexer=PhpLexer().lexer)

    assert parser.error_count == 0
    assert ast is not None
    assert ast.items

    decl = ast.items[0]
    assert isinstance(decl, VarDeclStmt)
    _, expr = decl.decls[0]
    assert isinstance(expr, Ternary)
    assert expr.if_true.value == "yes"
    assert expr.if_false.value == "no"
