# Documento Técnico - Mini PHP Compiler GUI

## Propósito y estado

- Compilador educativo para un subconjunto de PHP con énfasis en funcionalidad principal; flujo completo GUI + backend vía PyWebView.
- Etapas léxica, sintáctica y primer corte semántico implementadas; retorna tokens, AST serializable, tabla de símbolos y mensajes.
- Punto de entrada `main.py`: crea ventana PyWebView apuntando a `frontend/index.html`, registra `BackendAPI`, soporta ejecución normal o empaquetada (PyInstaller `_MEIPASS`).

## Backend – Compilador

- AST (`backend/ast_nodes.py`): dataclasses para programa, declaraciones (namespace/use/class/func), sentencias (if/while/for/foreach/echo/print/include/require/return/bloques), expresiones (literales, binarios, unarios, ternario, llamadas, acceso a miembro, new, arrays); nodos pueden almacenar `lineno`.
- Léxico (`backend/lexer/core.py` y `backend/lexer/__init__.py`): lexer PLY configurable (`LexerConfig`); tokens PHP básicos, operadores, ternario, comentarios; reporter inyectable captura errores; `PhpLexer.tokenize/print_tokens` reinician conteo por llamada.
- Parser (`backend/parser/core.py` y `backend/parser/__init__.py`): gramática PLY para `<?php ... ?>`; precedencias declaradas; construcción de AST usando nodos; recuperación de errores consumiendo hasta `;`, `}`, `?>`; `ParserWrapper` acumula `SyntaxErrorInfo` y acepta reporter; utilidades `build_parser` y `parse_php`.
- Semántica (`backend/semantic/semantic_analyzer.py`, `backend/semantic/symbol_table.py`, `backend/semantic/errors.py`, `backend/semantic/__init__.py`): visitor sobre AST con tabla de símbolos basada en pila; valida redeclaraciones, uso antes de declarar, compatibilidad de tipos en asignaciones y operadores, llamadas, foreach sobre arrays, lvalues válidos; infiere tipos simples y retornos; snapshot serializable de scopes y símbolos.
- Fachada (`backend/facade.py`): orquesta pipeline `compile`; ejecuta lexer + parser con reporte desacoplado, recolecta tokens, serializa AST, corre semántica si no hay errores previos, construye `CompilationResult` y `SemanticPreviewResult`.
- API PyWebView (`backend/api.py`): adapta fachada a métodos expuestos a JS (`open_file_dialog`, `load_file`, `save_file`, `save_file_as`, `compile`, `semantic_preview`); maneja rutas y errores de E/S; conserva referencia a ventana para diálogos.

## Frontend – GUI

- Layout (`frontend/index.html`): Bootstrap 5 + Work Sans/JetBrains Mono; panel editor con numeración de líneas, barra de acciones (abrir/nuevo/guardar/ejecutar), pestañas Tokens/AST/Semántico, tablas y preformat para resultados.
- Lógica (`frontend/app.js`): inicializa estado/UI, enruta eventos de botones, gestiona guardar/abrir vía API, ejecuta compilación y vista previa semántica, sincroniza numeración y tabulación en el editor.
- Helpers (`frontend/ui.js`, `frontend/dom.js`, `frontend/backend.js`): estado global, badges de estado, render de mensajes combinados (léxico/sintáctico/semántico), tokens, AST JSON, resumen de errores, tabla de símbolos; caché de DOM; wrapper `invoke` para llamadas PyWebView.

## Pruebas y artefactos

- `tests/test_compiler_failures.py`: errores léxicos (caracteres ilegales, strings sin cerrar, variables inválidas) y sintácticos (falta de `;`, bloque sin cerrar, `new` sin paréntesis).
- `tests/test_function_declarations.py`: combina clase y función toplevel, verifica AST y orden de nodos.
- `tests/test_semantic.py`: variables no declaradas, éxito cuando existen símbolos, presencia de clases/métodos/funciones en tabla de símbolos, error por operador aritmético sobre strings.
- `tests/test_ternary.py`: asegura tokens `?`/`:` y nodo `Ternary` en AST.
- Carpeta `pruebas/`: ejemplos PHP (clases, control de flujo). `reportes/`: ejecuciones previas con fuentes usadas.
- `requirements.txt`: dependencias principales (`ply`, `pywebview`, `pytest`).

## Patrones y flujo

- Fachada (`CompilerFacade`) encapsula etapas y serialización para UI.
- Visitor semántico + tabla de símbolos en pila con snapshot ordenado.
- Reporteo desacoplado mediante callbacks para capturar mensajes sin acoplar a stdout.
- UI modular (DOM cache + funciones de render) y comunicación asíncrona con backend; Bootstrap para layout.
- Listo para empaquetar con PyInstaller (manejo de `_MEIPASS` en `main.py`).

## Descargo de responsabilidad (participación IA)

Este documento y la descripción de los módulos `backend/ast_nodes.py`, `backend/lexer/core.py`, `backend/lexer/__init__.py`, `backend/parser/core.py`, `backend/parser/__init__.py`, `backend/semantic/semantic_analyzer.py`, `backend/semantic/symbol_table.py`, `backend/semantic/errors.py`, `backend/semantic/__init__.py`, `backend/facade.py`, `backend/api.py`, `frontend/index.html`, `frontend/app.js`, `frontend/ui.js`, `frontend/dom.js`, `frontend/backend.js`, `tests/`, `pruebas/`, `reportes/`, `main.py` fueron elaborados/consolidados con apoyo de un agente de inteligencia artificial. La autoría académica y el control técnico corresponden a Kevin Esguerra Cardona y Juan Manuel Garcia Isaza, estudiantes de Ingeniería en Sistemas y Computación de la Universidad Tecnológica de Pereira (curso de Desarrollo de Compiladores, profesor Cesar Augusto Jaramillo Acevedo, segundo semestre 2025).
