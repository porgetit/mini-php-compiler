# lexer_php_reducido.py
import sys
import ply.lex as lex

# -------------------------------
# Palabras reservadas (reducidas)
# -------------------------------
reserved = {
    'function': 'FUNCTION',
    'echo':     'ECHO',
    'print':    'PRINT',
    'if':       'IF',
    'else':     'ELSE',
    'elseif':   'ELSEIF',
    'while':    'WHILE',
    'for':      'FOR',
    'foreach':  'FOREACH',
    'as':       'AS',
    'return':   'RETURN',
    'true':     'TRUE',
    'false':    'FALSE',
    'null':     'NULL',
    'class':    'CLASS',
    'new':      'NEW',
    'public':   'PUBLIC',
    'private':  'PRIVATE',
    'protected':'PROTECTED',
    'static':   'STATIC',
    'use':      'USE',
    'namespace':'NAMESPACE',
    'include':  'INCLUDE',
    'require':  'REQUIRE',
}

# -------------------------------
# Lista de tokens
# -------------------------------
tokens = (
    # Tags PHP
    'PHP_OPEN',      # <?php
    'PHP_CLOSE',     # ?>

    # Identificadores y variables
    'VARIABLE',      # $var
    'ID',            # nombres de funciones/clases/etc. (sin $)

    # Literales
    'NUMBER',
    'STRING',

    # Operadores y símbolos
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'CONCAT',            # .
    'ASSIGN',            # =
    'EQUAL', 'NOTEQUAL', # ==, !=
    'IDENT', 'NIDENT',   # ===, !==
    'LT', 'LE', 'GT', 'GE',
    'AND', 'OR', 'NOT',  # &&, ||, !
    'ARROW',             # ->
    'SCOPE',             # ::
    'DOUBLEARROW',       # => (arrays, argumentos nombrados)
    'INC', 'DEC',        # ++, --

    # Agrupación y separadores
    'LPAREN', 'RPAREN',
    'LBRACKET', 'RBRACKET',
    'LBRACE', 'RBRACE',
    'COMMA', 'SEMICOLON', 'COLON', 'QUESTION',
) + tuple(reserved.values())

# -------------------------------
# Reglas simples (1 caracter)
# -------------------------------
t_PLUS       = r'\+'
t_MINUS      = r'-'
t_TIMES      = r'\*'
t_DIVIDE     = r'/'
t_MOD        = r'%'
t_ASSIGN     = r'='
t_LT         = r'<'
t_GT         = r'>'
t_NOT        = r'!'
t_LPAREN     = r'\('
t_RPAREN     = r'\)'
t_LBRACKET   = r'\['
t_RBRACKET   = r'\]'
t_LBRACE     = r'\{'
t_RBRACE     = r'\}'
t_COMMA      = r','
t_SEMICOLON  = r';'
t_COLON      = r':'
t_QUESTION   = r'\?'
t_CONCAT     = r'\.'   # concatenación en PHP

# -------------------------------
# Reglas con mayor prioridad (multi-char)
#  (Defínelas como funciones para precedencia)
# -------------------------------
def t_PHP_OPEN(t):
    r'<\?php'
    return t

def t_PHP_CLOSE(t):
    r'\?>'
    return t

def t_IDENT(t):    # ===
    r'==='
    t.type = 'IDENT'
    return t

def t_NIDENT(t):   # !==
    r'!=='
    t.type = 'NIDENT'
    return t

def t_EQUAL(t):    # ==
    r'=='
    return t

def t_NOTEQUAL(t): # !=
    r'!='
    return t

def t_LE(t):       # <=
    r'<='
    return t

def t_GE(t):       # >=
    r'>='
    return t

def t_AND(t):      # &&
    r'&&'
    return t

def t_OR(t):       # ||
    r'\|\|'
    return t

def t_INC(t):      # ++
    r'\+\+'
    return t

def t_DEC(t):      # --
    r'--'
    return t

def t_ARROW(t):    # ->
    r'->'
    return t

def t_SCOPE(t):    # ::
    r'::'
    return t

def t_DOUBLEARROW(t):  # =>
    r'=>'
    return t

# -------------------------------
# Literales: números y cadenas
# -------------------------------
def t_NUMBER(t):
    r'(?:\d+\.\d+|\d+)'
    # Intenta castear a int si no hay punto; si hay, a float
    if '.' in t.value:
        t.value = float(t.value)
    else:
        t.value = int(t.value)
    return t

# Cadena "doble" o 'simple' con escapes simples (sin interpolación)
# Nota: Esto es una simplificación útil para un lexer base.
def t_STRING(t):
    r'"([^\\\n]|\\.)*"|\'([^\\\n]|\\.)*\''
    raw = t.value
    if raw[0] == raw[-1] and raw[0] in ("'", '"'):
        t.value = raw[1:-1]
    return t

# -------------------------------
# Variables e identificadores
# -------------------------------
def t_VARIABLE(t):
    r'\$[A-Za-z_][A-Za-z0-9_]*'
    return t

def t_ID(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    # Mapea a palabra reservada si aplica
    t.type = reserved.get(t.value, 'ID')
    return t

# -------------------------------
# Comentarios y espacios
# -------------------------------
t_ignore = ' \t\r'

# Comentarios tipo C
def t_COMMENT_BLOCK(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')

# Comentario de línea estilo C++: //...
def t_COMMENT_LINE(t):
    r'//[^\n]*'
    pass

# Comentario de línea estilo shell: #...
def t_COMMENT_HASH(t):
    r'\#[^\n]*'
    pass

# Manejo de nuevas líneas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# -------------------------------
# Errores
# -------------------------------
def t_error(t):
    print(f"[Lexer] Error léxico en línea {t.lexer.lineno}: carácter inesperado {repr(t.value[0])}")
    t.lexer.skip(1)

# -------------------------------
# Utilidad de prueba
# -------------------------------
def test(data, lexer):
    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)

# -------------------------------
# Construcción del lexer y demo
# -------------------------------
if __name__ == '__main__':
    lexer = lex.lex()

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
        // comentario de línea
        # otro comentario de línea
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
    test(demo, lexer)
