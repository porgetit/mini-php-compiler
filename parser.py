"""Parser para un subconjunto de PHP."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

import ply.yacc as yacc

from lexer import LexerConfig, PhpLexer
from ast_nodes import *

tokens = LexerConfig().full_token_list()


def _default_reporter(level: str, message: str) -> None:
    print(message)


@dataclass
class SyntaxErrorInfo:
    message: str
    token_type: Optional[str]
    token_value: Optional[str]
    lineno: Optional[int]


@dataclass
class ParserState:
    errors: List[SyntaxErrorInfo] = field(default_factory=list)
    parser: Any | None = None
    reporter: Callable[[str, str], None] | None = None


_CURRENT_STATE: ParserState | None = None
_RECOVERY_TOKENS = {"SEMICOLON", "RBRACE", "PHP_CLOSE"}


def _set_parser_state(state: ParserState | None) -> None:
    """Hace accesible el estado actual al manejador de errores del parser."""
    global _CURRENT_STATE
    _CURRENT_STATE = state


def _register_syntax_error(info: SyntaxErrorInfo) -> None:
    if _CURRENT_STATE is not None:
        _CURRENT_STATE.errors.append(info)


def _emit_parser_message(level: str, message: str) -> None:
    if _CURRENT_STATE is not None and _CURRENT_STATE.reporter is not None:
        _CURRENT_STATE.reporter(level, message)
    else:
        _default_reporter(level, message)


def _recover_parser() -> None:
    """Consume tokens hasta un punto seguro para continuar el análisis."""
    if _CURRENT_STATE is None or _CURRENT_STATE.parser is None:
        return

    parser = _CURRENT_STATE.parser
    while True:
        next_tok = parser.token()
        if not next_tok:
            break
        if next_tok.type in _RECOVERY_TOKENS:
            break
    parser.errok()


# === PRECEDENCIAS (de menor a mayor) ===
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQUAL', 'NOTEQUAL', 'IDENT', 'NIDENT'),
    ('left', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS', 'CONCAT'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('right', 'NOT'),
    ('right', 'UMINUS', 'UPLUS'),         # unarios
    ('right', 'INC', 'DEC'),              # prefijos
)

# === REGLAS ===
def p_program(p):
    """program : PHP_OPEN top_list_opt PHP_CLOSE"""
    p[0] = Program(p[2] or [])

def p_top_list_opt(p):
    """top_list_opt : top_list
                    | empty"""
    p[0] = p[1] if p.slice[1].type != 'empty' else []

def p_top_list(p):
    """top_list : top
                | top_list top"""
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[2]); p[0] = p[1]

def p_top(p):
    """top : namespace_decl
           | use_decl
           | class_decl
           | stmt"""
    p[0] = p[1]

# --- namespace / use ---
def p_namespace_decl(p):
    """namespace_decl : NAMESPACE qname SEMICOLON"""
    p[0] = NamespaceDecl(p[2].parts)

def p_use_decl(p):
    """use_decl : USE use_name_list SEMICOLON"""
    p[0] = UseDecl(p[2])

def p_use_name_list(p):
    """use_name_list : qname
                     | use_name_list COMMA qname"""
    if len(p) == 2:
        p[0] = [p[1].parts]
    else:
        p[1].append(p[3].parts); p[0] = p[1]

# --- class / members ---
def p_class_decl(p):
    """class_decl : CLASS ID LBRACE class_members_opt RBRACE"""
    p[0] = ClassDecl(p[2], p[4])

def p_class_members_opt(p):
    """class_members_opt : class_members
                         | empty"""
    p[0] = p[1] if p.slice[1].type != 'empty' else []

def p_class_members(p):
    """class_members : class_member
                     | class_members class_member"""
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[2]); p[0] = p[1]

def p_class_member(p):
    """class_member : visibility_opt static_opt function_decl"""
    func: FunctionDecl = p[3]
    func.visibility = p[1]
    func.is_static = p[2]
    p[0] = func

def p_visibility_opt(p):
    """visibility_opt : PUBLIC
                      | PRIVATE
                      | PROTECTED
                      | empty"""
    p[0] = None if p.slice[1].type == 'empty' else p[1].lower()

def p_static_opt(p):
    """static_opt : STATIC
                  | empty"""
    p[0] = False if p.slice[1].type == 'empty' else True

# --- funciones ---
def p_function_decl(p):
    """function_decl : FUNCTION ID LPAREN params_opt RPAREN block"""
    p[0] = FunctionDecl(p[2], p[4], p[6])

def p_params_opt(p):
    """params_opt : params
                  | empty"""
    p[0] = p[1] if p.slice[1].type != 'empty' else []

def p_params(p):
    """params : param
              | params COMMA param"""
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[3]); p[0] = p[1]

def p_param(p):
    """param : VARIABLE
             | VARIABLE ASSIGN expr"""
    if len(p) == 2:
        p[0] = Param(p[1], None)
    else:
        p[0] = Param(p[1], p[3])

# --- bloques y sentencias ---
def p_block(p):
    """block : LBRACE stmts_opt RBRACE"""
    p[0] = Block(p[2])

def p_stmts_opt(p):
    """stmts_opt : stmts
                 | empty"""
    p[0] = p[1] if p.slice[1].type != 'empty' else []

def p_stmts(p):
    """stmts : stmt
             | stmts stmt"""
    p[0] = [p[1]] if len(p) == 2 else (p[1] + [p[2]])

def p_stmt(p):
    """stmt : SEMICOLON
            | vardecl SEMICOLON
            | expr SEMICOLON
            | echo_stmt
            | print_stmt
            | return_stmt
            | include_stmt
            | require_stmt
            | if_stmt
            | while_stmt
            | for_stmt
            | foreach_stmt
            | block"""
    if p.slice[1].type == 'SEMICOLON':
        p[0] = EmptyStmt()
    elif isinstance(p[1], Block):
        p[0] = p[1]
    elif isinstance(p[1], (EchoStmt, PrintStmt, ReturnStmt, IncludeStmt, RequireStmt, IfStmt, WhileStmt, ForStmt, ForeachStmt, VarDeclStmt)):
        p[0] = p[1]
    else:
        p[0] = ExprStmt(p[1])

def p_vardecl(p):
    """vardecl : varbind_list"""
    p[0] = VarDeclStmt(p[1])

def p_varbind_list(p):
    """varbind_list : varbind
                    | varbind_list COMMA varbind"""
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[3]); p[0] = p[1]

def p_varbind(p):
    """varbind : VARIABLE
               | VARIABLE ASSIGN expr"""
    p[0] = (p[1], None) if len(p) == 2 else (p[1], p[3])

def p_echo_stmt(p):
    """echo_stmt : ECHO expr_list SEMICOLON"""
    p[0] = EchoStmt(p[2])

def p_print_stmt(p):
    """print_stmt : PRINT expr SEMICOLON"""
    p[0] = PrintStmt(p[2])

def p_return_stmt(p):
    """return_stmt : RETURN SEMICOLON
                   | RETURN expr SEMICOLON"""
    p[0] = ReturnStmt(None) if len(p) == 3 else ReturnStmt(p[2])

def p_include_stmt(p):
    """include_stmt : INCLUDE expr SEMICOLON"""
    p[0] = IncludeStmt(p[2])

def p_require_stmt(p):
    """require_stmt : REQUIRE expr SEMICOLON"""
    p[0] = RequireStmt(p[2])

def p_if_stmt(p):
    """if_stmt : IF LPAREN expr RPAREN stmt elseif_list_opt else_opt"""
    p[0] = IfStmt(p[3], p[5], p[6] or [], p[7])

def p_elseif_list_opt(p):
    """elseif_list_opt : elseif_list
                       | empty"""
    p[0] = p[1] if p.slice[1].type != 'empty' else []

def p_elseif_list(p):
    """elseif_list : ELSEIF LPAREN expr RPAREN stmt
                   | elseif_list ELSEIF LPAREN expr RPAREN stmt"""
    if len(p) == 6:
        p[0] = [(p[3], p[5])]
    else:
        p[1].append((p[4], p[6])); p[0] = p[1]

def p_else_opt(p):
    """else_opt : ELSE stmt
                | empty"""
    p[0] = None if p.slice[1].type == 'empty' else p[2]

def p_while_stmt(p):
    """while_stmt : WHILE LPAREN expr RPAREN stmt"""
    p[0] = WhileStmt(p[3], p[5])

def p_for_stmt(p):
    """for_stmt : FOR LPAREN for_init_opt SEMICOLON for_cond_opt SEMICOLON for_iter_opt RPAREN stmt"""
    p[0] = ForStmt(p[3], p[5], p[7], p[9])

def p_for_init_opt(p):
    """for_init_opt : empty
                    | expr_list
                    | varbind_list"""
    if p.slice[1].type == 'empty':
        p[0] = None
    else:
        p[0] = p[1]

def p_for_cond_opt(p):
    """for_cond_opt : empty
                    | expr"""
    p[0] = None if p.slice[1].type == 'empty' else p[1]

def p_for_iter_opt(p):
    """for_iter_opt : empty
                    | expr_list"""
    p[0] = None if p.slice[1].type == 'empty' else p[1]

def p_foreach_stmt(p):
    """foreach_stmt : FOREACH LPAREN expr AS foreach_bind RPAREN stmt"""
    key, val = p[5]
    p[0] = ForeachStmt(p[3], key, val, p[7])

def p_foreach_bind(p):
    """foreach_bind : VARIABLE
                    | VARIABLE DOUBLEARROW VARIABLE"""
    p[0] = (None, p[1]) if len(p) == 2 else (p[1], p[3])

# --- listas expr ---
def p_expr_list(p):
    """expr_list : expr
                 | expr_list COMMA expr"""
    p[0] = [p[1]] if len(p) == 2 else (p[1] + [p[3]])

# === EXPRESIONES ===
def p_expr(p):
    """expr : assign"""
    p[0] = p[1]

def p_assign(p):
    """assign : logic_or
              | postfix ASSIGN assign"""
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Assign(p[1], p[3])

def p_logic_or(p):
    """logic_or : logic_or OR logic_and
                | logic_and"""
    p[0] = Binary('||', p[1], p[3]) if len(p) == 4 else p[1]

def p_logic_and(p):
    """logic_and : logic_and AND equality
                 | equality"""
    p[0] = Binary('&&', p[1], p[3]) if len(p) == 4 else p[1]

def p_equality(p):
    """equality : equality EQUAL rel
                | equality NOTEQUAL rel
                | equality IDENT rel
                | equality NIDENT rel
                | rel"""
    if len(p) == 4:
        op = {'==': '==', '!=': '!=', 'IDENT': '===', 'NIDENT': '!=='}
        p[0] = Binary(op[p.slice[2].type if p.slice[2].type in ('IDENT','NIDENT') else p[2]], p[1], p[3])
    else:
        p[0] = p[1]

def p_rel(p):
    """rel : rel LT add
           | rel LE add
           | rel GT add
           | rel GE add
           | add"""
    if len(p) == 4:
        p[0] = Binary(p[2], p[1], p[3])
    else:
        p[0] = p[1]

def p_add(p):
    """add : add PLUS mul
           | add MINUS mul
           | add CONCAT mul
           | mul"""
    if len(p) == 4:
        op = p[2] if p.slice[2].type != 'CONCAT' else '.'
        p[0] = Binary(op, p[1], p[3])
    else:
        p[0] = p[1]

def p_mul(p):
    """mul : mul TIMES unary
           | mul DIVIDE unary
           | mul MOD unary
           | unary"""
    p[0] = Binary(p[2], p[1], p[3]) if len(p) == 4 else p[1]

def p_unary(p):
    """unary : NOT unary
             | PLUS unary %prec UPLUS
             | MINUS unary %prec UMINUS
             | INC unary
             | DEC unary
             | postfix"""
    if len(p) == 3:
        opmap = {'!':'!', '+':'u+', '-':'u-', 'INC':'++', 'DEC':'--'}
        op = opmap.get(p.slice[1].type, p[1])
        p[0] = Unary(op, p[2])
    else:
        p[0] = p[1]

def p_postfix(p):
    """postfix : primary
               | postfix INC
               | postfix DEC
               | postfix LBRACKET expr RBRACKET
               | postfix LPAREN args_opt RPAREN
               | postfix ARROW ID
               | qname SCOPE ID"""
    if len(p) == 3 and p.slice[2].type in ('INC','DEC'):
        p[0] = PostfixUnary('++' if p.slice[2].type=='INC' else '--', p[1])
    elif len(p) == 5 and p.slice[2].type == 'LBRACKET':
        p[0] = Index(p[1], p[3])
    elif len(p) == 5 and p.slice[2].type == 'LPAREN':
        p[0] = Call(p[1], p[3] or [])
    elif len(p) == 4 and p.slice[2].type == 'ARROW':
        p[0] = Member(p[1], p[3])
    elif len(p) == 4 and p.slice[2].type == 'SCOPE':
        p[0] = StaticAccess(p[1], p[3])
    else:
        p[0] = p[1]

def p_primary(p):
    """primary : VARIABLE
               | literal
               | LPAREN expr RPAREN
               | array_lit
               | qname
               | NEW qname LPAREN args_opt RPAREN"""
    if p.slice[1].type == 'VARIABLE':
        p[0] = Var(p[1])
    elif p.slice[1].type == 'LPAREN':
        p[0] = p[2]
    elif p.slice[1].type == 'NEW':
        args = p[4] or []
        p[0] = New(p[2], args)
    else:
        p[0] = p[1]

def p_literal(p):
    """literal : NUMBER
               | STRING
               | TRUE
               | FALSE
               | NULL"""
    t = p.slice[1].type
    if t == 'NUMBER':
        p[0] = NumberLit(p[1])
    elif t == 'STRING':
        p[0] = StringLit(p[1])
    elif t == 'TRUE':
        p[0] = BoolLit(True)
    elif t == 'FALSE':
        p[0] = BoolLit(False)
    else:
        p[0] = NullLit()

# --- arrays ---
def p_array_lit(p):
    """array_lit : LBRACKET array_pairs_opt RBRACKET"""
    p[0] = ArrayLit(p[2] or [])

def p_array_pairs_opt(p):
    """array_pairs_opt : array_pairs
                       | empty"""
    p[0] = p[1] if p.slice[1].type != 'empty' else []

def p_array_pairs(p):
    """array_pairs : array_pair
                   | array_pairs COMMA array_pair
                   | array_pairs COMMA"""
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 3:
        p[0] = p[1]
    else:
        p[1].append(p[3]); p[0] = p[1]

def p_array_pair(p):
    """array_pair : expr DOUBLEARROW expr
                  | expr"""
    if len(p) == 4:
        p[0] = (p[1], p[3])
    else:
        p[0] = (None, p[1])

# --- nombres calificados ---
def p_qname(p):
    """qname : ID
             | qname NAMESPACE_SEPARATOR ID"""
    if len(p) == 2:
        p[0] = Name([p[1]])
    else:
        p[1].parts.append(p[3]); p[0] = p[1]

def p_args_opt(p):
    """args_opt : empty
                | args"""
    p[0] = [] if p.slice[1].type == 'empty' else p[1]

def p_args(p):
    """args : expr
            | args COMMA expr"""
    p[0] = [p[1]] if len(p) == 2 else (p[1] + [p[3]])

def p_empty(p):
    """empty :"""
    p[0] = None

def p_error(tok):
    if tok:
        lineno = getattr(tok, "lineno", None)
        lineno_txt = str(lineno) if lineno is not None else "desconocida"
        message = (
            f"Error de sintaxis en línea {lineno_txt}"
        )
        _emit_parser_message("error", message)
        _register_syntax_error(
            SyntaxErrorInfo(
                message=message,
                token_type=tok.type,
                token_value=repr(tok.value),
                lineno=lineno,
            )
        )
        _recover_parser()
        return

class ParserWrapper:
    """Envoltura alrededor del parser PLY para manejar el estado y los errores."""
    def __init__(self, debug: bool = False, reporter: Callable[[str, str], None] | None = None):
        self._debug = debug
        self._reporter = reporter or _default_reporter
        self._parser = yacc.yacc(
            module=sys.modules[__name__],
            start='program',
            debug=debug,
            write_tables=False,
        )
        self.errors: List[SyntaxErrorInfo] = []
        self.error_count: int = 0

    def parse(self, source: str, lexer) -> Optional[Program]:
        state = ParserState(parser=self._parser, reporter=self._reporter)
        _set_parser_state(state)
        try:
            result = self._parser.parse(source, lexer=lexer, tracking=True)
        finally:
            _set_parser_state(None)

        self.errors = state.errors
        self.error_count = len(self.errors)
        if self.error_count:
            return None
        return result


# === CONSTRUCCIÓN DEL PARSER ===
def build_parser(debug: bool = False, reporter: Callable[[str, str], None] | None = None):
    return ParserWrapper(debug=debug, reporter=reporter)


# === PEQUEÑA FUNCIÓN DE UTILIDAD PARA PROBAR RÁPIDO ===
def parse_php(code: str):
    parser = build_parser()
    return parser.parse(code, lexer=PhpLexer().lexer)
