from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Symbol:
    name: str
    kind: str  # 'var', 'func', 'class', 'param'
    type: Any = None
    node: Any = None
    lineno: Optional[int] = None
    value: Any = None
    owner: Optional[str] = None


class SymbolTable:
    def __init__(self) -> None:
        # stack de scopes activos: scopes[-1] = scope actual
        self.scopes: List[Dict[str, Symbol]] = [{}]
        self.scopes_meta: List[Dict[str, Any]] = [{"name": "global", "kind": "global", "id": 0}]
        self.closed_scopes: List[Dict[str, Any]] = []
        self._next_scope_id = 1

    def enter_scope(self, name: Optional[str] = None, kind: str = "block") -> None:
        meta = {"name": name, "kind": kind, "id": self._next_scope_id}
        self._next_scope_id += 1
        self.scopes.append({})
        self.scopes_meta.append(meta)

    def exit_scope(self) -> None:
        if len(self.scopes) == 1:
            raise RuntimeError("Intento de salir del scope global")
        scope = self.scopes.pop()
        meta = self.scopes_meta.pop()
        self.closed_scopes.append({"meta": meta, "symbols": scope})

    def declare(self, name: str, symbol: Symbol) -> bool:
        """Declara en el scope actual. Devuelve False si ya existe en el mismo scope."""
        scope = self.scopes[-1]
        if name in scope:
            return False
        scope[name] = symbol
        return True

    def lookup(self, name: str) -> Optional[Symbol]:
        """Busca desde el scope actual hacia afuera."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def lookup_current(self, name: str) -> Optional[Symbol]:
        return self.scopes[-1].get(name)

    def snapshot(self) -> List[Dict[str, Any]]:
        """Devuelve una vista serializable de la tabla de simbolos."""
        serializable: List[Dict[str, Any]] = []

        def _serialize_scope(scope: Dict[str, Symbol], meta: Dict[str, Any]) -> Dict[str, Any]:
            symbols: List[Dict[str, Any]] = []
            for sym in scope.values():
                sym_type = sym.type
                if isinstance(sym_type, (dict, list, tuple)):
                    sym_type = str(sym_type)
                val = sym.value
                symbols.append(
                    {
                        "name": sym.name,
                        "kind": sym.kind,
                        "type": sym_type,
                        "value": val,
                        "owner": sym.owner,
                        "lineno": sym.lineno,
                    }
                )
            return {
                "scope": meta.get("id"),
                "name": meta.get("name"),
                "kind": meta.get("kind"),
                "symbols": symbols,
            }

        for entry in self.closed_scopes:
            serializable.append(_serialize_scope(entry["symbols"], entry["meta"]))

        for scope, meta in zip(self.scopes, self.scopes_meta):
            serializable.append(_serialize_scope(scope, meta))

        serializable.sort(key=lambda s: s.get("scope", 0))
        return serializable
