import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.lexer import PhpLexer
from backend.parser import build_parser


@pytest.fixture()
def lexer():
    return PhpLexer()


@pytest.fixture()
def parser():
    # Un parser puede reutilizarse entre pruebas siempre que la instancia sea fresca.
    return build_parser()


def tokenize_pairs(lexer: PhpLexer, source: str):
    return [(tok.type, tok.value) for tok in lexer.tokenize(source)]


def parse_source(parser, source: str):
    # Se usa un lexer independiente para que PLY no conserve estado entre ejecuciones.
    php_lexer = PhpLexer()
    return parser.parse(source, lexer=php_lexer.lexer)


def test_invalid_characters_report_errors_and_recover(lexer, capsys):
    source = "<?php $foo @ $bar; &$baz; ?>"
    pairs = tokenize_pairs(lexer, source)
    captured = capsys.readouterr().out

    assert "[Lexer] Error lexico en linea 1: caracter inesperado '@'" in captured
    assert "[Lexer] Error lexico en linea 1: caracter inesperado '&'" in captured
    assert pairs == [
        ("PHP_OPEN", "<?php"),
        ("VARIABLE", "$foo"),
        ("VARIABLE", "$bar"),
        ("SEMICOLON", ";"),
        ("VARIABLE", "$baz"),
        ("SEMICOLON", ";"),
        ("PHP_CLOSE", "?>"),
    ]


def test_unterminated_string_reports_error(lexer, capsys):
    source = '<?php echo "hola ?>'
    pairs = tokenize_pairs(lexer, source)
    captured = capsys.readouterr().out

    assert "[Lexer] Error lexico en linea 1: caracter inesperado '\"'" in captured
    assert ("STRING", "hola") not in pairs  # no se genera token STRING valido
    assert pairs == [
        ("PHP_OPEN", "<?php"),
        ("ECHO", "echo"),
        ("ID", "hola"),
        ("PHP_CLOSE", "?>"),
    ]


def test_invalid_variable_name_reports_error(lexer, capsys):
    source = "<?php $9abc = 1; ?>"
    pairs = tokenize_pairs(lexer, source)
    captured = capsys.readouterr().out

    assert "identificador de variable no v" in captured.lower()
    assert "'$9abc'" in captured
    assert ("VARIABLE", "$9abc") not in pairs
    assert pairs == [
        ("PHP_OPEN", "<?php"),
        ("ASSIGN", "="),
        ("NUMBER", 1),
        ("SEMICOLON", ";"),
        ("PHP_CLOSE", "?>"),
    ]


def test_parser_flags_missing_semicolon(parser, capsys):
    source = "<?php echo 'hola' ?>"
    result = parse_source(parser, source)
    captured = capsys.readouterr().out

    assert result is None
    assert "[Parser] Error de sintaxis en token PHP_CLOSE" in captured


def test_parser_reports_unclosed_block(parser, capsys):
    source = "<?php if ($flag) { echo $flag; ?>"
    result = parse_source(parser, source)
    captured = capsys.readouterr().out

    assert result is None
    assert "[Parser] Error de sintaxis en token PHP_CLOSE" in captured


def test_parser_requires_parentheses_in_new(parser, capsys):
    source = "<?php $g = new Greeter; ?>"
    result = parse_source(parser, source)
    captured = capsys.readouterr().out

    assert result is None
    assert "[Parser] Error de sintaxis en token SEMICOLON" in captured
