# Mini PHP Compiler GUI

Aplicacion de escritorio liviana que expone el compilador reducido de PHP a traves de una interfaz web embebida en PyWebView. El enfoque actual cubre analisis lexico y sintactico, visualizacion de tokens y AST, y deja listo un gancho para la etapa semantica.

## Arquitectura
- **Backend (`backend/`)**: contiene la logica del compilador (lexer, parser, AST), la fachada `CompilerFacade` que orquesta el proceso y el adaptador `BackendAPI` que expone metodos a JavaScript mediante PyWebView.
- **Frontend (`frontend/`)**: HTML + CSS (Bootstrap) + JS. Consume el API expuesto por PyWebView para abrir, guardar y compilar archivos PHP, y muestra tokens, AST y mensajes.
- **Entrada (`main.py`)**: crea la ventana PyWebView apuntando a `frontend/index.html` y registra la API del backend. Es el punto de arranque unico para la app.

## Requerimientos
- Python 3.11+
- Dependencias en `requirements.txt` (`ply`, `pywebview`, `pytest`)

Instalacion rapida:
```bash
python -m venv .venv
. .venv/Scripts/activate  # en Windows
pip install -r requirements.txt
```

## Uso
```bash
python main.py
```
La ventana permite:
- Abrir un archivo PHP (dialogo de archivo) o crear uno nuevo.
- Editar el codigo y guardarlo (guardar/guardar como).
- Ejecutar el compilador para ver mensajes, tokens y AST.
- Probar el gancho de analisis semantico (stub informativo por ahora).

## Operaciones del backend (PyWebView API)
- `open_file_dialog`, `load_file(path)`, `save_file(path, content)`, `save_file_as(nombre, content)`
- `compile(code, path=None)`: devuelve tokens, AST serializado, contadores de errores y mensajes lexicos/sintacticos.
- `semantic_preview(code)`: placeholder para la futura etapa semantica.

## Pruebas
La suite `pytest` (`tests/test_compiler_failures.py`) valida los errores lexicos y sintacticos. Ejecuta `pytest -q` desde la raiz del proyecto.

## Estructura rápida
- `backend/ast_nodes.py` – dataclasses del AST.
- `backend/lexer.py` – definicion del lexer y reglas de tokens.
- `backend/parser.py` – gramatica PLY y construccion del parser.
- `backend/facade.py` – fachada para compilar y serializar resultados.
- `backend/api.py` – API expuesta a la GUI via PyWebView.
- `frontend/index.html` – layout de la interfaz.
- `frontend/app.js` – logica de la UI y llamadas al backend.
- `main.py` – arranque de la ventana PyWebView.
