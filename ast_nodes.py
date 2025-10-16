"""Árbol de Sintaxis Abstracta (AST) para un subconjunto de PHP."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Union, Tuple, Any

# === NODOS BÁSICOS ===
@dataclass
class Program:
    items: List[Any]

@dataclass
class NamespaceDecl:
    name: List[str]

@dataclass
class UseDecl:
    names: List[List[str]]  # nombres calificados

@dataclass
class ClassDecl:
    name: str
    members: List[Any]

@dataclass
class FunctionDecl:
    name: str
    params: List["Param"]
    body: "Block"
    visibility: Optional[str] = None
    is_static: bool = False

@dataclass
class Param:
    name: str
    default: Optional["Expr"] = None

@dataclass
class Block:
    stmts: List[Any]

# === SENTENCIAS ===
@dataclass
class EmptyStmt: ...
@dataclass
class EchoStmt:
    exprs: List["Expr"]

@dataclass
class PrintStmt:
    expr: "Expr"

@dataclass
class ReturnStmt:
    expr: Optional["Expr"]

@dataclass
class IncludeStmt:
    expr: "Expr"

@dataclass
class RequireStmt:
    expr: "Expr"

@dataclass
class IfStmt:
    cond: "Expr"
    then: Any
    elifs: List[Tuple["Expr", Any]]
    els: Optional[Any]

@dataclass
class WhileStmt:
    cond: "Expr"
    body: Any

@dataclass
class ForStmt:
    init: Optional[List["Expr"]]  # o declaración simplificada
    cond: Optional["Expr"]
    iters: Optional[List["Expr"]]
    body: Any

@dataclass
class ForeachStmt:
    iterable: "Expr"
    key: Optional[str]
    value: str
    body: Any

@dataclass
class VarDeclStmt:
    decls: List[Tuple[str, Optional["Expr"]]]  # [("$a", expr?), ...]

@dataclass
class ExprStmt:
    expr: "Expr"

# === EXPRESIONES ===
Expr = Any

@dataclass
class Name:
    parts: List[str]  # nombre calificado

@dataclass
class Var:
    name: str  # incluye el $

@dataclass
class NumberLit:
    value: Union[int, float]

@dataclass
class StringLit:
    value: str

@dataclass
class BoolLit:
    value: bool

@dataclass
class NullLit: ...

@dataclass
class ArrayLit:
    pairs: List[Tuple[Optional["Expr"], "Expr"]]  # (clave?, valor) ; si clave es None => [valor]

@dataclass
class Assign:
    target: Expr
    value: Expr

@dataclass
class Binary:
    op: str
    left: Expr
    right: Expr

@dataclass
class Unary:
    op: str
    expr: Expr

@dataclass
class PostfixUnary:
    op: str
    expr: Expr

@dataclass
class Call:
    callee: Expr
    args: List[Expr]

@dataclass
class Index:
    base: Expr
    index: Expr

@dataclass
class Member:
    obj: Expr
    name: str

@dataclass
class StaticAccess:
    qname: Name
    name: str

@dataclass
class New:
    class_name: Name
    args: List[Expr]
