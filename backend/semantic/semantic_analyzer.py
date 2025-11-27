from __future__ import annotations
from typing import Any, List, Optional
from .. import ast_nodes as ast
from .errors import SemanticError
from .symbol_table import Symbol, SymbolTable


class SemanticAnalyzer:
    """Recorrido semantico sobre el AST."""

    def __init__(self) -> None:
        self.symtab = SymbolTable()
        self.errors: List[SemanticError] = []
        self.current_function: Optional[Symbol] = None
        self.current_class: Optional[Symbol] = None
        self.snapshot_data: List[dict] = []
        self._func_params: dict[str, List[Symbol]] = {}
        self._func_nodes: dict[str, Any] = {}

    def _get_lineno(self, node) -> Optional[int]:
        """Obtiene la linea del nodo o de alguno de sus hijos inmediatos."""
        if node is None:
            return None
        ln = getattr(node, "lineno", None)
        if ln is not None:
            return ln
        for attr in ("left", "right", "target", "value", "expr", "callee", "base", "index"):
            child = getattr(node, attr, None)
            ln = getattr(child, "lineno", None)
            if ln is not None:
                return ln
        for child in getattr(node, "__dict__", {}).values():
            ln = getattr(child, "lineno", None) if hasattr(child, "__dict__") else None
            if ln is not None:
                return ln
        return None

    def error(self, msg: str, node=None) -> None:
        lineno = self._get_lineno(node)
        self.errors.append(SemanticError(msg, lineno))

    def analyze(self, program: Any) -> List[SemanticError]:
        """Punto de entrada: recibe Program (raiz del AST)."""
        self.errors.clear()
        self.symtab = SymbolTable()
        self.visit(program)
        self.snapshot_data = self.symtab.snapshot()
        return self.errors

    # --- Dispatcher generico ---
    def visit(self, node):
        if node is None:
            return None
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        # Recorre atributos que son nodos o listas de nodos
        for _, value in getattr(node, "__dict__", {}).items():
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, "__class__"):
                        self.visit(item)
            elif hasattr(value, "__class__"):
                self.visit(value)

    # --- Helpers ---
    def is_lvalue(self, node) -> bool:
        """Determina si un nodo es un destino valido para asignacion."""
        return isinstance(node, (ast.Var, ast.Index, ast.Member, ast.StaticAccess))

    # --- Visitadores ---
    def visit_Program(self, node):
        for it in node.items:
            self.visit(it)

    def visit_ClassDecl(self, node):
        cname = node.name
        if self.symtab.lookup_current(cname):
            self.error(f"Class '{cname}' already declared in this scope", node)
            return

        cls_sym = Symbol(
            name=cname,
            kind="class",
            type={"members": []},
            node=node,
            lineno=getattr(node, "lineno", None),
            owner=None,
            value=None,
        )
        self.symtab.declare(cname, cls_sym)

        prev_class = self.current_class
        self.current_class = cls_sym
        member_names: List[str] = []

        self.symtab.enter_scope(name=cname, kind="class")
        for member in node.members:
            self.visit(member)
            if isinstance(member, ast.FunctionDecl):
                member_names.append(member.name)
        self.symtab.exit_scope()

        cls_sym.value = {"methods": member_names}
        self.current_class = prev_class

    def visit_FunctionDecl(self, node):
        fname = node.name
        if self.symtab.lookup_current(fname):
            self.error(f"Function '{fname}' already declared in this scope", node)
            return

        param_types = [None for _ in node.params]
        ret_type = None
        owner = self.current_class.name if self.current_class else None
        kind = "method" if self.current_class else "func"
        sym = Symbol(
            name=fname,
            kind=kind,
            type={"params": param_types, "ret": ret_type},
            node=node,
            lineno=getattr(node, "lineno", None),
            owner=owner,
        )
        self.symtab.declare(fname, sym)
        self._func_nodes[fname] = node

        self.symtab.enter_scope(name=fname, kind="function" if not self.current_class else "method")
        params_syms: List[Symbol] = []
        for idx, p in enumerate(node.params):
            pname = p.name
            default_type = None
            if getattr(p, "default", None) is not None:
                default_type = self.visit(p.default)
                param_types[idx] = default_type
            psym = Symbol(
                name=pname,
                kind="param",
                type=default_type,
                node=p,
                lineno=getattr(p, "lineno", None),
                value=self._literal_value(getattr(p, "default", None)),
                owner=fname,
            )
            if not self.symtab.declare(pname, psym):
                self.error(f"Parameter '{pname}' duplicated", p)
            if getattr(p, "default", None) is not None:
                self.visit(p.default)
            params_syms.append(psym)
        self._func_params[fname] = params_syms

        self.current_function = sym
        self.visit(node.body)
        self.current_function = None
        self.symtab.exit_scope()

    def visit_VarDeclStmt(self, node):
        for name, init in node.decls:
            existing = self.symtab.lookup(name)
            if existing:
                # En PHP las variables son dinamicas: actualizar tipo/valor, sin marcar redeclaracion.
                if init is not None:
                    init_type = self.visit(init)
                    if init_type and not existing.type:
                        existing.type = init_type
                    val = self._literal_value(init)
                    if val is not None:
                        existing.value = val
                continue

            sym = Symbol(name=name, kind="var", type=None, node=node, lineno=getattr(node, "lineno", None))
            self.symtab.declare(name, sym)
            if init is not None:
                init_type = self.visit(init)
                if init_type and not sym.type:
                    sym.type = init_type
                val = self._literal_value(init)
                if val is not None:
                    sym.value = val

    def visit_Assign(self, node):
        tgt = getattr(node, "target", None)
        val = getattr(node, "value", None)

        if tgt is None:
            self.error("Malformed assignment with no target", node)
            return

        if not self.is_lvalue(tgt):
            self.error("Invalid assignment target. Can only assign to variables, arrays, or object properties.", node)
            self.visit(val)
            return None

        if isinstance(tgt, ast.Var):
            name = tgt.name
            sym = self.symtab.lookup(name)

            if not sym:
                self.error(f"Variable '{name}' used before declaration", tgt)
                self.visit(val)
                return None

            vtype = self.visit(val)

            if sym.type and vtype and not self.type_compatible(sym.type, vtype):
                self.error(f"Type mismatch assigning to '{name}': {sym.type} <- {vtype}", node)

            if vtype and not sym.type:
                sym.type = vtype
            literal_val = self._literal_value(val)
            if literal_val is not None:
                sym.value = literal_val

            return vtype
        else:
            self.visit(tgt)
            return self.visit(val)

    def visit_Var(self, node: ast.Var):
        name = node.name
        sym = self.symtab.lookup(name)
        if not sym:
            self.error(f"Variable '{name}' not declared", node)
            return None
        return sym.type

    def visit_Name(self, node: ast.Name):
        return "::".join(node.parts)

    # --- Literales ---
    def visit_NumberLit(self, node: ast.NumberLit):
        v = node.value
        return "int" if isinstance(v, int) else "float"

    def visit_StringLit(self, node: ast.StringLit):
        return "string"

    def visit_BoolLit(self, node: ast.BoolLit):
        return "bool"

    def visit_NullLit(self, node: ast.NullLit):
        return "null"

    def visit_ArrayLit(self, node: ast.ArrayLit):
        for k, v in node.pairs:
            if k is not None:
                self.visit(k)
            self.visit(v)
        return "array"

    # --- Expresiones ---
    def visit_Binary(self, node):
        left_t = self.visit(getattr(node, "left", None))
        right_t = self.visit(getattr(node, "right", None))
        op = getattr(node, "op", None)

        if op in ("+", "-", "*", "/", "%"):
            if left_t is None or right_t is None:
                return None
            if left_t in ("int", "float") and right_t in ("int", "float"):
                return "float" if "float" in (left_t, right_t) else "int"
            self.error(f"Arithmetic operator '{op}' applied to non-numeric types: {left_t}, {right_t}", node)
            return None

        if op in ("==", "!=", "===", "!==", "<", ">", "<=", ">="):
            return "bool"

        if op in ("&&", "||"):
            if left_t not in (None, "bool"):
                self.error(f"Logical operator '{op}' expects boolean left operand, got '{left_t}'", node)
            if right_t not in (None, "bool"):
                self.error(f"Logical operator '{op}' expects boolean right operand, got '{right_t}'", node)
            return "bool"

        if op == ".":  # php concatenation
            return "string"
        return None

    def visit_Unary(self, node: ast.Unary):
        expr_t = self.visit(node.expr)
        op = node.op

        if op in ("-", "+", "~", "++", "--"):
            if expr_t not in ("int", "float"):
                self.error(f"Unary operator '{op}' requires numeric type, got '{expr_t}'", node)
                return None
            return expr_t

        if op == "!":
            return "bool"
        return None

    def visit_Ternary(self, node: ast.Ternary):
        self.visit(node.cond)
        true_t = self.visit(node.if_true)
        false_t = self.visit(node.if_false)
        if true_t == false_t:
            return true_t
        if true_t == "null":
            return false_t
        if false_t == "null":
            return true_t
        return None

    def visit_Call(self, node):
        callee = node.callee
        args = node.args

        if isinstance(callee, ast.Name):
            fname = "::".join(callee.parts)
            sym = self.symtab.lookup(fname)

            if not sym:
                self.error(f"Call to undefined function '{fname}'", node)
                for a in args:
                    self.visit(a)
                return None

            if sym.kind != "func":
                self.error(f"'{fname}' is not a function (it is a {sym.kind})", node)
                for a in args:
                    self.visit(a)
                return None

            sig = sym.type or {}
            params = sig.get("params", [])

            if params and len(params) != len(args):
                self.error(f"Function '{fname}' expects {len(params)} args, got {len(args)}", node)

            for i, a in enumerate(args):
                at = self.visit(a)
                if params and i < len(params) and params[i] is None and at is not None:
                    params[i] = at
                    # actualiza simbolo de parametro si lo tenemos registrado
                    if fname in self._func_params and i < len(self._func_params[fname]):
                        psym = self._func_params[fname][i]
                        if psym.type is None:
                            psym.type = at
                if i < len(params) and params[i] and at and not self.type_compatible(params[i], at):
                    self.error(f"Argument {i+1} of '{fname}' type mismatch: expected {params[i]}, got {at}", a)

            ret_type = sig.get("ret")
            # intento de inferir el tipo de retorno si aun no existe
            if ret_type is None and fname in self._func_nodes:
                param_map = {}
                if fname in self._func_params:
                    for psym in self._func_params[fname]:
                        param_map[psym.name] = psym.type
                func_node = self._func_nodes[fname]
                inferred = self._infer_return_from_body(func_node.body, param_map)
                if inferred is not None:
                    sig["ret"] = inferred
                    ret_type = inferred
            return ret_type
        else:
            callee_type = self.visit(callee)
            if callee_type in ("int", "float", "bool", "array", "null"):
                self.error(f"Invalid call: value of type '{callee_type}' is not callable", node)

            for a in args:
                self.visit(a)

            return None

    def visit_ReturnStmt(self, node):
        expr = getattr(node, "expr", None) or getattr(node, "value", None)
        rtype = self.visit(expr) if expr is not None else None
        if self.current_function:
            expected = self.current_function.type.get("ret") if isinstance(self.current_function.type, dict) else None
            if expected and rtype and not self.type_compatible(expected, rtype):
                self.error(
                    f"Return type mismatch in function '{self.current_function.name}': expected {expected}, got {rtype}",
                    node,
                )
            if isinstance(self.current_function.type, dict) and self.current_function.type.get("ret") is None and rtype is not None:
                self.current_function.type["ret"] = rtype
        return rtype

    # --- Control Flow ---
    def visit_Block(self, node):
        self.symtab.enter_scope(kind="block")
        for s in node.stmts:
            self.visit(s)
        self.symtab.exit_scope()

    def visit_EmptyStmt(self, node):
        return None

    def visit_EchoStmt(self, node):
        for e in node.exprs:
            self.visit(e)

    def visit_PrintStmt(self, node):
        self.visit(node.expr)

    def visit_IfStmt(self, node):
        self.visit(node.cond)
        self.visit(node.then)
        for cond, blk in node.elifs:
            self.visit(cond)
            self.visit(blk)
        if node.els:
            self.visit(node.els)

    def visit_WhileStmt(self, node):
        self.visit(node.cond)
        self.visit(node.body)

    def visit_ForStmt(self, node):
        if node.init:
            for e in node.init:
                self.visit(e)
        if node.cond:
            self.visit(node.cond)
        if node.iters:
            for it in node.iters:
                self.visit(it)
        self.visit(node.body)

    def visit_ForeachStmt(self, node):
        iterable_type = self.visit(node.iterable)
        if iterable_type != "array":
            self.error(f"Foreach expects an array, got '{iterable_type}'", node.iterable)

        self.symtab.enter_scope(kind="block")
        if node.key:
            self.symtab.declare(node.key, Symbol(name=node.key, kind="var", type=None, node=node))
        if node.value:
            self.symtab.declare(node.value, Symbol(name=node.value, kind="var", type=None, node=node))
        self.visit(node.body)
        self.symtab.exit_scope()

    def visit_IncludeStmt(self, node):
        self.visit(node.expr)

    def visit_RequireStmt(self, node):
        self.visit(node.expr)

    def visit_Index(self, node):
        base_t = self.visit(node.base)
        self.visit(node.index)

        if base_t not in ("array", "string", "any") and base_t is not None:
            self.error(f"Cannot index type '{base_t}'. Only arrays and strings are indexable.", node.base)

        return None

    def visit_Member(self, node):
        self.visit(node.obj)
        return None

    def visit_StaticAccess(self, node):
        return None

    def visit_New(self, node):
        for a in node.args:
            self.visit(a)
        return None

    # --- Utilities ---
    def _literal_value(self, node) -> Any:
        """Devuelve un valor Python si el nodo es literal simple; en otro caso None."""
        if isinstance(node, ast.NumberLit):
            return node.value
        if isinstance(node, ast.StringLit):
            return node.value
        if isinstance(node, ast.BoolLit):
            return node.value
        if isinstance(node, ast.NullLit):
            return None
        return None

    def _infer_expr_type(self, expr, param_map: dict[str, Any]) -> Any:
        """Inferencia simple de tipos sobre expresiones usando un mapa de parametros conocido."""
        if expr is None:
            return None
        if isinstance(expr, ast.NumberLit):
            return "int" if isinstance(expr.value, int) else "float"
        if isinstance(expr, ast.StringLit):
            return "string"
        if isinstance(expr, ast.BoolLit):
            return "bool"
        if isinstance(expr, ast.NullLit):
            return None
        if isinstance(expr, ast.Var):
            return param_map.get(expr.name)
        if isinstance(expr, ast.Binary):
            lt = self._infer_expr_type(expr.left, param_map)
            rt = self._infer_expr_type(expr.right, param_map)
            op = expr.op
            if op in ("+", "-", "*", "/", "%"):
                if lt in ("int", "float") and rt in ("int", "float"):
                    return "float" if "float" in (lt, rt) else "int"
                return None
            if op == ".":
                return "string"
            if op in ("==", "!=", "===", "!==", "<", ">", "<=", ">=", "&&", "||"):
                return "bool"
        if isinstance(expr, ast.Ternary):
            t = self._infer_expr_type(expr.if_true, param_map)
            f = self._infer_expr_type(expr.if_false, param_map)
            if t == f:
                return t
            if t is None:
                return f
            if f is None:
                return t
        return None

    def _infer_return_from_body(self, body: ast.Block, param_map: dict[str, Any]) -> Any:
        """Busca un return en el cuerpo y trata de inferir su tipo."""
        for stmt in getattr(body, "stmts", []):
            if isinstance(stmt, ast.ReturnStmt):
                return self._infer_expr_type(getattr(stmt, "expr", None) or getattr(stmt, "value", None), param_map)
        return None

    def type_compatible(self, declared, actual) -> bool:
        if declared == actual:
            return True
        if declared == "float" and actual == "int":
            return True
        if actual == "null":
            return True
        return False
