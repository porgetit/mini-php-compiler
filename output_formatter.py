"""Herramientas para formatear las salidas del compilador usando Rich."""
from __future__ import annotations

import argparse
import sys
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich_argparse import RichHelpFormatter


class _BoundHelpFormatter(RichHelpFormatter):
    def __init__(self, prog: str, console: Console) -> None:
        super().__init__(prog, console=console, show_metavar_column=True)


class _RichArgumentParser(argparse.ArgumentParser):
    """ArgumentParser que imprime ayuda y errores usando Rich."""

    def __init__(
        self,
        output: "RichCompilerConsole",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        formatter_cls = kwargs.pop("formatter_class", None)
        if formatter_cls is None:
            formatter_cls = lambda prog: _BoundHelpFormatter(prog, console=output.console)  # type: ignore
        kwargs["formatter_class"] = formatter_cls
        super().__init__(*args, **kwargs)
        self._output = output

    def _print_message(self, message: Any, file: Any | None = None) -> None:
        if not message:
            return
        target = self._output.console if file in (None, sys.stdout) else self._output.err_console
        if isinstance(message, str) and message.endswith("\n"):
            target.print(message, soft_wrap=True, end="")
        else:
            target.print(message, soft_wrap=True)

    def error(self, message: str) -> None:
        usage = self.format_usage()
        if usage:
            self._print_message(usage, file=sys.stderr)
        self._output.message(f"{self.prog}: {message}", level="error", stderr=True)
        raise SystemExit(2)


class RichCompilerConsole:
    """Punto central para producir salidas del CLI con Rich."""

    _LEVEL_STYLES = {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red",
    }

    _LEVEL_LABELS = {
        "info": "[INFO]",
        "success": "[OK]",
        "warning": "[WARN]",
        "error": "[ERROR]",
    }

    def __init__(
        self,
        console: Console | None = None,
        err_console: Console | None = None,
        default_prefix: str = "[Main]",
    ) -> None:
        self.console = console or Console()
        self.err_console = err_console or Console(stderr=True)
        self.default_prefix = default_prefix

    def message(
        self,
        text: str,
        *,
        level: str = "info",
        prefix: str | None = None,
        stderr: bool = False,
    ) -> None:
        """Imprime un mensaje corto con estilo estandarizado."""
        style = self._LEVEL_STYLES.get(level, "white")
        label = self._LEVEL_LABELS.get(level, "[INFO]")
        target = self.err_console if stderr else self.console

        composed = Text()
        composed.append(label, style=f"bold {style}")
        composed.append(" ")
        composed.append(prefix or self.default_prefix, style=f"bold {style}")
        composed.append(" ")
        composed.append(text)

        target.print(composed)

    def show_tokens(self, tokens: Sequence[Mapping[str, Any]]) -> None:
        """Representa la tabla de tokens generada por el lexer."""
        table = Table(
            title="Tokens",
            header_style="bold cyan",
            box=box.SIMPLE_HEAD,
            show_lines=False,
        )
        table.add_column("Linea", style="dim", justify="right", width=6)
        table.add_column("Tipo", style="bold")
        table.add_column("Valor", overflow="fold")

        for token in tokens:
            lineno = token.get("lineno")
            line_str = f"{lineno:04d}" if isinstance(lineno, int) else "-"
            token_type = str(token.get("type", ""))
            value_repr = repr(token.get("value"))
            table.add_row(line_str, token_type, value_repr)

        self.console.print(table)

    def show_ast(self, ast_data: Any) -> None:
        """Muestra el AST serializado en una vista plegable."""
        json_text = json.dumps(ast_data, indent=2, ensure_ascii=False)
        syntax = Syntax(
            json_text,
            "json",
            theme="monokai",
            indent_guides=True,
            word_wrap=False,
        )
        panel = Panel(
            syntax,
            title="AST",
            border_style="cyan",
            box=box.SIMPLE,
        )
        self.console.print(panel)

    def show_verbose_artifact(self, path: Path) -> None:
        """Reporta la ubicacion de un artefacto generado en modo verbose."""
        self.message(
            f"Artefactos verbose guardados en {path}",
            level="info",
        )

    def show_summary(self, error_count: int) -> None:
        """Imprime el resumen final de errores detectados."""
        level = "success" if error_count == 0 else "error"
        plural = "error" if error_count == 1 else "errores"
        text = f"Total de errores sintacticos detectados: {error_count} {plural}"
        self.message(text, level=level, stderr=error_count > 0)

    def create_argument_parser(self, **kwargs: Any) -> argparse.ArgumentParser:
        """Construye un ArgumentParser que renderiza ayuda y errores con Rich."""
        return _RichArgumentParser(self, **kwargs)
