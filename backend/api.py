"""Adaptador PyWebView que expone operaciones del compilador a la GUI."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import webview

from .facade import CompilerFacade


def _as_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    # Algunos dialogos de PyWebView retornan tuple/list; tomamos el primer elemento.
    if isinstance(value, (list, tuple)):
        if not value:
            return None
        value = value[0]
    return Path(value).expanduser()


class BackendAPI:
    """Puente entre la GUI web y la logica del compilador."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.facade = CompilerFacade(project_root)
        self.window: webview.Window | None = None

    # --- utilidades ---
    def bind_window(self, window: webview.Window) -> None:
        self.window = window

    def _dialog_error(self, message: str) -> Dict[str, Any]:
        return {"ok": False, "error": message}

    def _get_window(self) -> webview.Window | None:
        return self.window

    # --- archivos ---
    def open_file_dialog(self) -> Dict[str, Any]:
        window = self._get_window()
        if window is None:
            return self._dialog_error("Ventana no inicializada")

        selection = window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            directory=str(self.project_root),
            file_types=("Archivos PHP (*.php)", "Todos los archivos (*.*)"),
        )
        if not selection:
            return {"ok": False, "cancelled": True}

        path = Path(selection[0])
        return self.load_file(str(path))

    def load_file(self, path: str) -> Dict[str, Any]:
        target = _as_path(path)
        if target is None:
            return self._dialog_error("Ruta no valida")
        try:
            content = target.read_text(encoding="utf-8")
        except OSError as exc:
            return self._dialog_error(f"No se pudo leer el archivo: {exc}")

        return {
            "ok": True,
            "path": str(target),
            "content": content,
        }

    def save_file(self, path: str | None, content: str) -> Dict[str, Any]:
        target = _as_path(path)
        if target is None:
            return self._dialog_error("No hay una ruta valida para guardar")
        try:
            target.write_text(content, encoding="utf-8")
        except OSError as exc:
            return self._dialog_error(f"No se pudo guardar el archivo: {exc}")
        return {"ok": True, "path": str(target)}

    def save_file_as(self, suggested: str, content: str) -> Dict[str, Any]:
        window = self._get_window()
        if window is None:
            return self._dialog_error("Ventana no inicializada")
        destination = window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=suggested,
            directory=str(self.project_root),
            file_types=("Archivos PHP (*.php)", "Todos los archivos (*.*)"),
        )
        if not destination:
            return {"ok": False, "cancelled": True}
        dest_path = destination[0] if isinstance(destination, (list, tuple)) else destination
        path = Path(dest_path)
        try:
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            return self._dialog_error(f"No se pudo guardar el archivo: {exc}")
        return {"ok": True, "path": str(path)}

    # --- compilador ---
    def compile(self, code: str, path: str | None = None) -> Dict[str, Any]:
        result = self.facade.compile(code, path=_as_path(path))
        return result.__dict__

    def semantic_preview(self, code: str) -> Dict[str, Any]:
        result = self.facade.semantic_preview(code)
        return result.__dict__
