"""Herramientas para formatear las salidas del compilador usando Rich."""
from __future__ import annotations

import argparse
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich_argparse import RichHelpFormatter


class _BoundHelpFormatter(RichHelpFormatter):
    def __init__(self, prog: str, console: Console) -> None:
        super().__init__(prog, console=console)


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
        stream = target.file if hasattr(target, "file") else sys.stdout
        if isinstance(message, str):
            stream.write(message)
        else:
            stream.write(str(message))
        stream.flush()

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

    def show_summary(self, syntax_errors: int, lexical_errors: int = 0) -> None:
        """Imprime el resumen final de errores detectados."""

        def _emit_summary(label: str, count: int) -> None:
            level = "success" if count == 0 else "error"
            plural = "error" if count == 1 else "errores"
            text = f"Total de errores {label} detectados: {count} {plural}"
            self.message(text, level=level, stderr=count > 0)

        _emit_summary("lexicos", lexical_errors)
        _emit_summary("sintacticos", syntax_errors)
        _emit_summary("", lexical_errors + syntax_errors)

    def create_argument_parser(self, **kwargs: Any) -> argparse.ArgumentParser:
        """Construye un ArgumentParser que renderiza ayuda y errores con Rich."""
        return _RichArgumentParser(self, **kwargs)

    def make_reporter(self) -> Callable[[str, str], None]:
        """Devuelve un callback compatible con los emisores del lexer y parser."""
        def reporter(level: str, message: str) -> None:
            self.message(message, level=level, stderr=(level == "error"))

        return reporter


@dataclass
class BufferedReporter:
    console: "RichCompilerConsole"
    lexical_messages: list[tuple[str, str]] = field(default_factory=list)
    syntax_messages: list[tuple[str, str]] = field(default_factory=list)

    def make_lexical_reporter(self) -> Callable[[str, str], None]:
        return self._make_bucket_reporter(self.lexical_messages)

    def make_syntax_reporter(self) -> Callable[[str, str], None]:
        return self._make_bucket_reporter(self.syntax_messages)

    def _make_bucket_reporter(
        self,
        bucket: list[tuple[str, str]],
    ) -> Callable[[str, str], None]:
        def reporter(level: str, message: str) -> None:
            bucket.append((level, message))

        return reporter

    def flush(self) -> None:
        self._drain(self.lexical_messages)
        self._drain(self.syntax_messages)

    def clear(self) -> None:
        self.lexical_messages.clear()
        self.syntax_messages.clear()

    def _drain(self, bucket: list[tuple[str, str]]) -> None:
        for level, message in bucket:
            self.console.message(message, level=level, stderr=(level == "error"))
        bucket.clear()
