"""Punto de entrada de la aplicacion GUI con PyWebView."""
from __future__ import annotations

from pathlib import Path

import webview

from backend.api import BackendAPI


def launch() -> None:
    project_root = Path(__file__).parent
    index_html = project_root / "frontend" / "index.html"
    api = BackendAPI(project_root)
    window = webview.create_window(
        "Mini PHP Compiler GUI",
        url=index_html.as_uri(),
        js_api=api,
        width=1280,
        height=860,
        min_size=(1024, 700),
    )
    api.bind_window(window)
    # Nota: debug=False evita el ruido en consola generado por WebView2/pywebview.
    webview.start(debug=False)


if __name__ == "__main__":
    launch()
