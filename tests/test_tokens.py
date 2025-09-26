import pytest
import lexer_php_reducido as lexer_module


@pytest.fixture()
def lexer():
    return lexer_module.PhpLexer()


def collect_tokens(lexer, text):
    return list(lexer.tokenize(text))


def single_token(lexer, text):
    tokens = collect_tokens(lexer, text)
    assert len(tokens) == 1, f"expected 1 token, got {[t.type for t in tokens]}"
    return tokens[0]


def test_php_open_token(lexer):
    tok = single_token(lexer, "<?php")
    assert tok.type == "PHP_OPEN"
    assert tok.value == "<?php"


def test_php_close_token(lexer):
    tok = single_token(lexer, "?>")
    assert tok.type == "PHP_CLOSE"
    assert tok.value == "?>"


def test_variable_token(lexer):
    tok = single_token(lexer, "$miVariable")
    assert tok.type == "VARIABLE"
    assert tok.value == "$miVariable"


def test_identifier_token(lexer):
    tok = single_token(lexer, "miFuncion")
    assert tok.type == "ID"
    assert tok.value == "miFuncion"


def test_integer_number_token(lexer):
    tok = single_token(lexer, "42")
    assert tok.type == "NUMBER"
    assert tok.value == 42


def test_float_number_token(lexer):
    tok = single_token(lexer, "3.14")
    assert tok.type == "NUMBER"
    assert tok.value == pytest.approx(3.14)


def test_double_quoted_string_token(lexer):
    tok = single_token(lexer, '"hola"')
    assert tok.type == "STRING"
    assert tok.value == "hola"


def test_single_quoted_string_token(lexer):
    tok = single_token(lexer, "'mundo'")
    assert tok.type == "STRING"
    assert tok.value == "mundo"


def test_namespace_separator_token(lexer):
    tok = single_token(lexer, "\\")
    assert tok.type == "NAMESPACE_SEPARATOR"
    assert tok.value == "\\"


@pytest.mark.parametrize(
    ("snippet", "expected_type"),
    [
        ("+", "PLUS"),
        ("-", "MINUS"),
        ("*", "TIMES"),
        ("/", "DIVIDE"),
        ("%", "MOD"),
        (".", "CONCAT"),
        ("=", "ASSIGN"),
    ],
)
def test_arithmetic_and_assignment_tokens(lexer, snippet, expected_type):
    tok = single_token(lexer, snippet)
    assert tok.type == expected_type
    assert tok.value == snippet


@pytest.mark.parametrize(
    ("snippet", "expected_type"),
    [
        ("==", "EQUAL"),
        ("!=", "NOTEQUAL"),
        ("===", "IDENT"),
        ("!==", "NIDENT"),
        ("<", "LT"),
        ("<=", "LE"),
        (">", "GT"),
        (">=", "GE"),
    ],
)
def test_comparison_tokens(lexer, snippet, expected_type):
    tok = single_token(lexer, snippet)
    assert tok.type == expected_type
    assert tok.value == snippet


@pytest.mark.parametrize(
    ("snippet", "expected_type"),
    [
        ("&&", "AND"),
        ("||", "OR"),
        ("!", "NOT"),
    ],
)
def test_logical_tokens(lexer, snippet, expected_type):
    tok = single_token(lexer, snippet)
    assert tok.type == expected_type
    assert tok.value == snippet


@pytest.mark.parametrize(
    ("snippet", "expected_type"),
    [
        ("++", "INC"),
        ("--", "DEC"),
    ],
)
def test_increment_tokens(lexer, snippet, expected_type):
    tok = single_token(lexer, snippet)
    assert tok.type == expected_type
    assert tok.value == snippet


@pytest.mark.parametrize(
    ("snippet", "expected_type"),
    [
        ("->", "ARROW"),
        ("::", "SCOPE"),
        ("=>", "DOUBLEARROW"),
    ],
)
def test_accessor_tokens(lexer, snippet, expected_type):
    tok = single_token(lexer, snippet)
    assert tok.type == expected_type
    assert tok.value == snippet


@pytest.mark.parametrize(
    ("snippet", "expected_type"),
    [
        ("(", "LPAREN"),
        (")", "RPAREN"),
        ("[", "LBRACKET"),
        ("]", "RBRACKET"),
        ("{", "LBRACE"),
        ("}", "RBRACE"),
    ],
)
def test_grouping_tokens(lexer, snippet, expected_type):
    tok = single_token(lexer, snippet)
    assert tok.type == expected_type
    assert tok.value == snippet


@pytest.mark.parametrize(
    ("snippet", "expected_type"),
    [
        (",", "COMMA"),
        (";", "SEMICOLON"),
        (":", "COLON"),
        ("?", "QUESTION"),
    ],
)
def test_separator_tokens(lexer, snippet, expected_type):
    tok = single_token(lexer, snippet)
    assert tok.type == expected_type
    assert tok.value == snippet


@pytest.mark.parametrize(
    ("keyword", "token_type"),
    [
        ("function", "FUNCTION"),
        ("echo", "ECHO"),
        ("print", "PRINT"),
        ("if", "IF"),
        ("else", "ELSE"),
        ("elseif", "ELSEIF"),
        ("while", "WHILE"),
        ("for", "FOR"),
        ("foreach", "FOREACH"),
        ("as", "AS"),
        ("return", "RETURN"),
        ("true", "TRUE"),
        ("false", "FALSE"),
        ("null", "NULL"),
        ("class", "CLASS"),
        ("new", "NEW"),
        ("public", "PUBLIC"),
        ("private", "PRIVATE"),
        ("protected", "PROTECTED"),
        ("static", "STATIC"),
        ("use", "USE"),
        ("namespace", "NAMESPACE"),
        ("include", "INCLUDE"),
        ("require", "REQUIRE"),
    ],
)
def test_reserved_word_tokens(lexer, keyword, token_type):
    tok = single_token(lexer, keyword)
    assert tok.type == token_type
    assert tok.value == keyword

def test_complex_php_program(lexer):
    snippet = r"""<?php
namespace Demo\Sub;

use Lib\Utils;

class Foo {
    public static function bar($x, $y = 10) {
        $msg = "Hola\n";
        $count = 0;
        // comentario inline
        # comentario hash
        /* comentario
           multilinea */
        $a = 1 + 2 * 3;
        $ok = ($a === 7) && !false || ($x != $y);
        $arr = ["k1" => 10, "k2" => 20];
        foreach ($arr as $key => $value) {
            $count++;
            echo $key . " => " . $value;
        }
        if ($count >= 2) {
            return Utils::format($arr['k1']);
        } else {
            return null;
        }
    }
}
?>
"""

    expected = [
        ("PHP_OPEN", "<?php"),
        ("NAMESPACE", "namespace"),
        ("ID", "Demo"),
        ("NAMESPACE_SEPARATOR", "\\"),
        ("ID", "Sub"),
        ("SEMICOLON", ";"),
        ("USE", "use"),
        ("ID", "Lib"),
        ("NAMESPACE_SEPARATOR", "\\"),
        ("ID", "Utils"),
        ("SEMICOLON", ";"),
        ("CLASS", "class"),
        ("ID", "Foo"),
        ("LBRACE", "{"),
        ("PUBLIC", "public"),
        ("STATIC", "static"),
        ("FUNCTION", "function"),
        ("ID", "bar"),
        ("LPAREN", "("),
        ("VARIABLE", "$x"),
        ("COMMA", ","),
        ("VARIABLE", "$y"),
        ("ASSIGN", "="),
        ("NUMBER", 10),
        ("RPAREN", ")"),
        ("LBRACE", "{"),
        ("VARIABLE", "$msg"),
        ("ASSIGN", "="),
        ("STRING", "Hola\\n"),
        ("SEMICOLON", ";"),
        ("VARIABLE", "$count"),
        ("ASSIGN", "="),
        ("NUMBER", 0),
        ("SEMICOLON", ";"),
        ("VARIABLE", "$a"),
        ("ASSIGN", "="),
        ("NUMBER", 1),
        ("PLUS", "+"),
        ("NUMBER", 2),
        ("TIMES", "*"),
        ("NUMBER", 3),
        ("SEMICOLON", ";"),
        ("VARIABLE", "$ok"),
        ("ASSIGN", "="),
        ("LPAREN", "("),
        ("VARIABLE", "$a"),
        ("IDENT", "==="),
        ("NUMBER", 7),
        ("RPAREN", ")"),
        ("AND", "&&"),
        ("NOT", "!"),
        ("FALSE", "false"),
        ("OR", "||"),
        ("LPAREN", "("),
        ("VARIABLE", "$x"),
        ("NOTEQUAL", "!="),
        ("VARIABLE", "$y"),
        ("RPAREN", ")"),
        ("SEMICOLON", ";"),
        ("VARIABLE", "$arr"),
        ("ASSIGN", "="),
        ("LBRACKET", "["),
        ("STRING", "k1"),
        ("DOUBLEARROW", "=>"),
        ("NUMBER", 10),
        ("COMMA", ","),
        ("STRING", "k2"),
        ("DOUBLEARROW", "=>"),
        ("NUMBER", 20),
        ("RBRACKET", "]"),
        ("SEMICOLON", ";"),
        ("FOREACH", "foreach"),
        ("LPAREN", "("),
        ("VARIABLE", "$arr"),
        ("AS", "as"),
        ("VARIABLE", "$key"),
        ("DOUBLEARROW", "=>"),
        ("VARIABLE", "$value"),
        ("RPAREN", ")"),
        ("LBRACE", "{"),
        ("VARIABLE", "$count"),
        ("INC", "++"),
        ("SEMICOLON", ";"),
        ("ECHO", "echo"),
        ("VARIABLE", "$key"),
        ("CONCAT", "."),
        ("STRING", " => "),
        ("CONCAT", "."),
        ("VARIABLE", "$value"),
        ("SEMICOLON", ";"),
        ("RBRACE", "}"),
        ("IF", "if"),
        ("LPAREN", "("),
        ("VARIABLE", "$count"),
        ("GE", ">="),
        ("NUMBER", 2),
        ("RPAREN", ")"),
        ("LBRACE", "{"),
        ("RETURN", "return"),
        ("ID", "Utils"),
        ("SCOPE", "::"),
        ("ID", "format"),
        ("LPAREN", "("),
        ("VARIABLE", "$arr"),
        ("LBRACKET", "["),
        ("STRING", "k1"),
        ("RBRACKET", "]"),
        ("RPAREN", ")"),
        ("SEMICOLON", ";"),
        ("RBRACE", "}"),
        ("ELSE", "else"),
        ("LBRACE", "{"),
        ("RETURN", "return"),
        ("NULL", "null"),
        ("SEMICOLON", ";"),
        ("RBRACE", "}"),
        ("RBRACE", "}"),
        ("RBRACE", "}"),
        ("PHP_CLOSE", "?>"),
    ]

    tokens = [(tok.type, tok.value) for tok in lexer.tokenize(snippet)]
    assert tokens == expected

def test_invalid_character_emits_error_and_recovers(lexer, capsys):
    tokens = collect_tokens(lexer, "$foo @ $bar")
    captured = capsys.readouterr()
    assert "[Lexer] Error lexico en linea 1" in captured.out
    assert "caracter inesperado '@'" in captured.out
    assert [(tok.type, tok.value) for tok in tokens] == [
        ("VARIABLE", "$foo"),
        ("VARIABLE", "$bar"),
    ]


def test_unterminated_string_reports_error(lexer, capsys):
    tokens = collect_tokens(lexer, 'echo "hola')
    captured = capsys.readouterr()
    assert "[Lexer] Error lexico en linea 1" in captured.out
    assert "caracter inesperado '\"'" in captured.out
    assert [(tok.type, tok.value) for tok in tokens] == [
        ("ECHO", "echo"),
        ("ID", "hola"),
    ]

def test_invalid_variable_name_reports_error(lexer, capsys):
    tokens = collect_tokens(lexer, "$9abc")
    captured = capsys.readouterr()
    assert "[Lexer] Error lexico en linea 1" in captured.out
    assert "identificador de variable invalido" in captured.out
    assert "'$9abc'" in captured.out
    assert [(tok.type, tok.value) for tok in tokens] == []


def test_variable_with_space_reports_error(lexer, capsys):
    tokens = collect_tokens(lexer, "$ foo")
    captured = capsys.readouterr()
    assert "[Lexer] Error lexico en linea 1" in captured.out
    assert "identificador de variable invalido" in captured.out
    assert "'$ foo'" in captured.out
    assert [(tok.type, tok.value) for tok in tokens] == []

def test_identifier_with_leading_digit_reports_error(lexer, capsys):
    tokens = collect_tokens(lexer, "7foo")
    captured = capsys.readouterr()
    assert "[Lexer] Error lexico en linea 1" in captured.out
    assert "identificador invalido" in captured.out
    assert "'7foo'" in captured.out
    assert [(tok.type, tok.value) for tok in tokens] == []

def test_function_name_with_leading_digit_reports_error(lexer, capsys):
    tokens = collect_tokens(lexer, "function 7foo() { }")
    captured = capsys.readouterr()
    assert "[Lexer] Error lexico en linea 1" in captured.out
    assert "identificador invalido" in captured.out
    assert "'7foo'" in captured.out
    assert [(tok.type, tok.value) for tok in tokens] == [
        ("FUNCTION", "function"),
        ("LPAREN", "("),
        ("RPAREN", ")"),
        ("LBRACE", "{"),
        ("RBRACE", "}"),
    ]


def test_single_ampersand_reports_error(lexer, capsys):
    tokens = collect_tokens(lexer, "&$foo")
    captured = capsys.readouterr()
    assert "[Lexer] Error lexico en linea 1" in captured.out
    assert "caracter inesperado '&'" in captured.out
    assert [(tok.type, tok.value) for tok in tokens] == [
        ("VARIABLE", "$foo"),
    ]
