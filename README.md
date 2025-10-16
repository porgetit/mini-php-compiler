# Mini PHP Compiler Front-End

## 1. Contexto del Proyecto
- **Descripcion breve:** Front-end academico de un compilador reducido para PHP escrito en Python. Implementa las etapas de analisis lexico y sintactico, genera un arbol de sintaxis abstracta (AST) y ofrece una interfaz de linea de comandos orientada a practicas formativas de compiladores.
- **Alcance del lenguaje:** Se reconocen archivos delimitados por `<?php ... ?>`, declaraciones `namespace` y `use`, definicion de clases y metodos con modificadores de visibilidad, asignaciones, sentencias de control (`if/elseif/else`, `while`, `for`, `foreach`), expresiones aritmeticas, logicas y de concatenacion, arrays con `=>`, acceso a miembros `->` y `::`, literales numericos y de cadena sin interpolacion, asi como construcciones `new`. La fase actual no cubre plantillas heredoc/nowdoc, genericos del motor Zend ni semantica de ejecucion.
- **Dependencias clave:**
  - Python 3.11+.
  - PLY (Python Lex-Yacc) para las fases de analisis.
  - `pytest` para la verificacion automatizada.
  - `requirements.txt` centraliza las versiones utilizadas en el curso.

## 2. Arquitectura Tecnica
### 2.1 Componentes Principales
- `lexer.PhpLexer`: encapsula la construccion del lexer de PLY, expone `tokenize` y `print_tokens`, y reutiliza `LexerConfig` para derivar la tupla de tokens.
- `parser.build_parser`: fabrica un parser LR a partir de `parser.py`, apoyado en las reglas declaradas con PLY y reutilizando los mismos tokens del lexer.
- `ast_nodes.py`: define mediante `dataclasses` la jerarquia de nodos del AST (programa, declaraciones, sentencias y expresiones).
- `main.py`: punto de entrada que orquesta la lectura del archivo, la recoleccion de tokens, la ejecucion del parser y la serializacion del AST en JSON cuando se solicita.
- `tests/test_compiler_failures.py`: conjunto de pruebas que valida escenarios de error lexicos y sintacticos, garantizando mensajes y recuperacion consistentes.
- Directorios auxiliares:
  - `pruebas/`: fuentes PHP de referencia para experimentar manualmente con el CLI.
  - `reportes/`: destino de los artefactos JSON generados con la bandera `--verbose`.

### 2.2 Flujo General
1. `main.py` carga el codigo fuente desde la ruta indicada por el usuario.
2. `PhpLexer.tokenize` produce la secuencia de tokens, reutilizable para impresion o almacenamiento.
3. `build_parser()` crea un parser LR que consume el mismo lexer y construye instancias del AST definido en `ast_nodes.py`.
4. La CLI reporta el exito del parseo, imprime tokens o AST bajo demanda y, en modo verbose, persiste un paquete JSON con insumos de la ejecucion.

### 2.3 Diseno y Patrones
- **Dataclasses:** el AST y la configuracion del lexer se modelan con `dataclasses`, lo que simplifica su serializacion y mantiene la inmutabilidad donde corresponde.
- **Separacion de responsabilidades:** lexer, parser, AST y CLI residen en modulos independientes, posibilitando pruebas unitarias aisladas y futuras extensiones (por ejemplo, generacion de codigo o interpretacion).
- **Uso disciplinado de PLY:** las reglas y precedencias se encuentran centralizadas en `parser.py`, manteniendo trazabilidad con el analizador lexico y evitando divergencias en los tokens compartidos.

## 3. Flujo de Analisis del Front-End
- **Entrada admitida:** archivos PHP codificados en UTF-8 o ASCII; se asume que caben en memoria y que el contenido responde al subconjunto soportado.
- **Preprocesamiento:** la aplicacion no modifica el texto previo al analisis, mas alla de la normalizacion de fin de linea que realiza Python al leer archivos.
- **Analisis lexico:** `PhpLexer` identifica palabras reservadas, operadores, literales y delimitadores. Convierte numeros a `int`/`float` y despoja las comillas de los strings. El estado `lineno` se mantiene actualizado para mejorar los reportes.
- **Analisis sintactico:** `build_parser` aplica una gramatica LR que crea nodos especificos para declaraciones (`ClassDecl`, `FunctionDecl`, `NamespaceDecl`), sentencias (`IfStmt`, `ForeachStmt`, `ReturnStmt`) y expresiones (`Binary`, `Assign`, `Call`, etc.). Al terminar se obtiene un `Program` con todos los elementos de alto nivel.
- **Salida:** la CLI puede imprimir tokens legibles, mostrar el AST como JSON legible o persistir un paquete con la fuente, los tokens y el AST en `reportes/`.

## 4. Manejo de Errores
- **Errores lexicos:** `t_error`, `t_VARIABLE_INVALID` y `t_ID_INVALID` reportan entradas ilegales, muestran el caracter o lexema conflictivo y avanzan para continuar con el resto del analisis.
- **Errores sintacticos:** `p_error` informa el token inesperado detectado por el parser y hace que `build_parser` devuelva `None`. La CLI propaga esta condicion con un codigo de salida distinto de cero.
- **Recuperacion:** las reglas estan disenadas para consumir la mayor cantidad posible de entrada legitima tras un error, de manera que el usuario obtenga una lista amplia de fallas en una sola corrida.
- **Mensajeria:** todos los mensajes se emiten con prefijos `[Lexer]` o `[Parser]`, facilitando el filtrado en pruebas automatizadas o scripts del curso.

## 5. Uso de PLY en el Proceso de Compilacion
### 5.1 Rol de PLY en esta etapa
- `ply.lex.lex` construye el automata determinista a partir de los metodos `t_*` definidos en `PhpLexer`.
- `ply.yacc.yacc` compila la gramatica LR registrada en `parser.py`, produciendo un parser reutilizable a lo largo de la sesion.
- Ambos componentes comparten el conjunto de tokens expuesto por `LexerConfig`, evitando inconsistencias entre etapas.

### 5.2 Ventajas de PLY para este proyecto
- Reproduce la metodologia tradicional Lex/Yacc con una API familiar para Python.
- Permite depuracion detallada (`debug=True`, inspeccion de `parser.out`, tablas `lextab.py` y `parsetab.py`) util para cursos de compiladores.
- Facilita la evolucion del front-end: el mismo marco soporta futuras fases semanticas o restructuraciones de la gramatica.

### 5.3 Buenas practicas actuales
- Mantener las reglas agrupadas por tipo de construccion y documentadas evita ambiguedades y colisiones de precedencia.
- El parser se genera bajo demanda para que cada prueba use una instancia fresca, minimizando efectos colaterales entre casos.
- La configuracion separada (`LexerConfig`) hace posible adaptar palabras reservadas sin tocar el resto del proyecto.

## 6. Estrategia de Pruebas
- La suite `pytest` (archivo `tests/test_compiler_failures.py`) cubre escenarios negativos relevantes: caracteres ilegales, variables mal formadas, cadenas sin cierre y errores de parseo comunes (faltan puntos y coma, bloques sin llave de cierre, `new` sin parentesis).
- Se emplean fixtures para crear instancias nuevas de `PhpLexer` y del parser, garantizando independencia y eliminando estado residual de PLY.
- Las aserciones validan tanto la secuencia de tokens obtenida como los mensajes emitidos a stdout/stderr, asegurando la experiencia esperada para quien usa la CLI.
- Las pruebas se ejecutan en segundos y sirven como red de seguridad antes de modificar reglas del lexer o la gramatica.

## 7. Procedimientos Operativos
- **Preparar entorno:** `python -m venv .venv`, activar el entorno y luego `pip install -r requirements.txt`.
- **Ejecucion del compilador:** `python main.py pruebas\\simple.php --tokens --ast` imprime la tabla de tokens y el AST en formato JSON. Cualquier archivo PHP compatible puede suministrarse en `--fuente`.
- **Modo verbose:** agregar `--verbose` genera un archivo JSON en `reportes/` con timestamp, ruta del origen, tokens y AST serializado; la fuente analizada se copia junto al reporte para auditoria.
- **Pruebas automatizadas:** `pytest -q` ejecuta la suite y confirma que los mensajes de error y el control de flujo siguen vigentes tras cambios.
- **Exploracion manual:** los scripts `python -c "from lexer import PhpLexer; PhpLexer().print_tokens(open('pruebas/simple.php').read())"` y `python -c "from parser import parse_php; print(parse_php(open('pruebas/control.php').read()))"` permiten inspeccionar rapidamente los resultados sin usar la CLI completa.

## 8. Asistencia de IA
- El modelo de lenguaje de OpenAI (Codex en la CLI) apoyo tareas de refactorizacion, ajuste de reglas del parser y redaccion de pruebas. Cada cambio se valido manualmente y mediante `pytest` antes de incorporarlo.
- Las decisiones de diseno y los criterios de aceptacion se documentaron para que el equipo pueda auditar facilmente las contribuciones asistidas por IA.

## 9. Correcciones
- **Validacion de identificadores:** se anadieron reglas especificas para variables e identificadores invalidos, evitando que fragmentos incorrectos se filtren como tokens legitimos. Las pruebas capturan ahora los mensajes esperados y la ausencia de tokens residuales.
- **Parser cohesionado:** el conjunto de producciones se reorganizo para admitir clases con miembros, arrays asociativos y llamadas encadenadas, corrigiendo conflictos de precedencia observados en versiones tempranas.
- **CLI robusta:** `main.py` consolido el manejo de errores y la generacion de artefactos, reemplazando scripts sueltos y asegurando codigos de salida coherentes para integraciones en pipelines de evaluacion.

## 10. Integrantes
- Kevin Esguerra Cardona
- Juan Felipe Lozano Aristizabal
- Juan Manuel Garcia Isaza
