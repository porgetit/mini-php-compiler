from dataclasses import dataclass
from typing import Optional


@dataclass
class SemanticError:
    message: str
    lineno: Optional[int] = None
    col: Optional[int] = None

    def __str__(self) -> str:  # pragma: no cover - str solo para logging/UI
        suffix = f" (linea {self.lineno})" if self.lineno is not None else ""
        return f"[Semantic] {self.message}{suffix}"
