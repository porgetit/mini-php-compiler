# lexer_php_reducido.py
from dataclasses import dataclass, field
from typing import ClassVar, Dict, Iterator, Tuple

import ply.lex as lex


@dataclass(frozen=True)
class LexerConfig:
    reserved: Dict[str, str] = field(
        default_factory=lambda: {
            'function': 'FUNCTION',
            'echo': 'ECHO',
            'print': 'PRINT',
            'if': 'IF',
            'else': 'ELSE',
            'elseif': 'ELSEIF',
            'while': 'WHILE',
            'for': 'FOR',
            'foreach': 'FOREACH',
            'as': 'AS',
            'return': 'RETURN',
            'true': 'TRUE',
            'false': 'FALSE',
            'null': 'NULL',
            'class': 'CLASS',
            'new': 'NEW',
            'public': 'PUBLIC',
            'private': 'PRIVATE',
            'protected': 'PROTECTED',
            'static': 'STATIC',
            'use': 'USE',
            'namespace': 'NAMESPACE',
            'include': 'INCLUDE',
            'require': 'REQUIRE',
        }
    )

    base_tokens: ClassVar[Tuple[str, ...]] = (
        'PHP_OPEN',
        'PHP_CLOSE',
        'VARIABLE',
        'ID',
        'NUMBER',
        'STRING',
        'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
        'CONCAT',
        'ASSIGN',
        'EQUAL', 'NOTEQUAL',
        'IDENT', 'NIDENT',
        'LT', 'LE', 'GT', 'GE',
        'AND', 'OR', 'NOT',
        'ARROW',
        'SCOPE',
        'DOUBLEARROW',
        'INC', 'DEC',
        'LPAREN', 'RPAREN',
        'LBRACKET', 'RBRACKET',
        'LBRACE', 'RBRACE',
        'COMMA', 'SEMICOLON', 'COLON', 'QUESTION',
        'NAMESPACE_SEPARATOR',
    )

    def full_token_list(self) -> Tuple[str, ...]:
        return self.base_tokens + tuple(self.reserved.values())


@dataclass
class PhpLexer:
    config: LexerConfig = field(default_factory=LexerConfig)
    tokens: Tuple[str, ...] = field(init=False)
    reserved: Dict[str, str] = field(init=False)
    lexer: lex.Lexer = field(init=False)

    t_ignore: ClassVar[str] = ' \t\r'
    t_PLUS: ClassVar[str] = r'\+'
    t_MINUS: ClassVar[str] = r'-'
    t_TIMES: ClassVar[str] = r'\*'
    t_DIVIDE: ClassVar[str] = r'/'
    t_MOD: ClassVar[str] = r'%'
    t_ASSIGN: ClassVar[str] = r'='
    t_LT: ClassVar[str] = r'<'
    t_GT: ClassVar[str] = r'>'
    t_NOT: ClassVar[str] = r'!'
    t_LPAREN: ClassVar[str] = r'\('
    t_RPAREN: ClassVar[str] = r'\)'
    t_LBRACKET: ClassVar[str] = r'\['
    t_RBRACKET: ClassVar[str] = r'\]'
    t_LBRACE: ClassVar[str] = r'\{'
    t_RBRACE: ClassVar[str] = r'\}'
    t_COMMA: ClassVar[str] = r','
    t_SEMICOLON: ClassVar[str] = r';'
    t_COLON: ClassVar[str] = r':'
    t_QUESTION: ClassVar[str] = r'\?'
    t_CONCAT: ClassVar[str] = r'\.'
    t_NAMESPACE_SEPARATOR: ClassVar[str] = r'\\'

    def __post_init__(self) -> None:
        self.reserved = self.config.reserved
        self.tokens = self.config.full_token_list()
        self.lexer = lex.lex(module=self)

    def t_PHP_OPEN(self, t):
        r'<\?php'
        return t

    def t_PHP_CLOSE(self, t):
        r'\?>'
        return t

    def t_IDENT(self, t):
        r'==='
        t.type = 'IDENT'
        return t

    def t_NIDENT(self, t):
        r'!=='
        t.type = 'NIDENT'
        return t

    def t_EQUAL(self, t):
        r'=='
        return t

    def t_NOTEQUAL(self, t):
        r'!='
        return t

    def t_LE(self, t):
        r'<='
        return t

    def t_GE(self, t):
        r'>='
        return t

    def t_AND(self, t):
        r'&&'
        return t

    def t_OR(self, t):
        r'\|\|'
        return t

    def t_INC(self, t):
        r'\+\+'
        return t

    def t_DEC(self, t):
        r'--'
        return t

    def t_ARROW(self, t):
        r'->'
        return t

    def t_SCOPE(self, t):
        r'::'
        return t

    def t_DOUBLEARROW(self, t):
        r'=>'
        return t

    def t_ID_INVALID(self, t):
        r'\d+[A-Za-z_][A-Za-z0-9_]*'
        print(f"[Lexer] Error lexico en linea {t.lexer.lineno}: identificador no válido {t.value!r}")
        return None

    def t_NUMBER(self, t):
        r'(?:\d+\.\d+|\d+)'
        if '.' in t.value:
            t.value = float(t.value)
        else:
            t.value = int(t.value)
        return t

    def t_STRING(self, t):
        r'(?:"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')'
        raw = t.value
        if raw and raw[0] == raw[-1] and raw[0] in ("'", '"'):
            t.value = raw[1:-1]
        return t

    def t_VARIABLE_INVALID(self, t):
        r'\$(?:[ \t]+[A-Za-z_][A-Za-z0-9_]*|[^A-Za-z_\s][^\s]*)'
        print(f"[Lexer] Error lexico en linea {t.lexer.lineno}: identificador de variable no válido {t.value!r}")
        return None

    def t_VARIABLE(self, t):
        r'\$[A-Za-z_][A-Za-z0-9_]*'
        return t

    def t_ID(self, t):
        r'[A-Za-z_][A-Za-z0-9_]*'
        t.type = self.reserved.get(t.value, 'ID')
        return t

    def t_COMMENT_BLOCK(self, t):
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count('\n')

    def t_COMMENT_LINE(self, t):
        r'//[^\n]*'

    def t_COMMENT_HASH(self, t):
        r'\#[^\n]*'

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        print(f"[Lexer] Error lexico en linea {t.lexer.lineno}: caracter inesperado {repr(t.value[0])}")
        t.lexer.skip(1)

    def tokenize(self, data: str) -> Iterator[lex.LexToken]:
        self.lexer.input(data)
        while True:
            token = self.lexer.token()
            if not token:
                break
            yield token

    def print_tokens(self, data: str) -> None:
        for token in self.tokenize(data):
            print(token)


def main() -> None:
    lexer = PhpLexer()
    demo = r'''
<?php
namespace Demo;

use Lib\Utils;

class Foo {
    public function bar($x, $y) {
        $msg = "Hola\n";
        $a = 1 + 2 * 3;
        $ok = ($a === 7) && !false || ($x != $y);
        $arr = ["k1" => 10, "k2" => 20];
        echo $msg . ' Mundo';
        // comentario de linea
        # otro comentario de linea
        /* bloque
           de comentario */
        if ($ok) {
            return $arr['k1'] + $a;
        } else {
            return null;
        }
    }
}
?>
'''
    print("=== TOKENS ===")
    lexer.print_tokens(demo)


if __name__ == '__main__':
    main()
