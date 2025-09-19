# Mini PHP Lexical Analyser

## 1. Contexto del Proyecto
- **Descripcion breve:** Analizador lexico escrito en Python que tokeniza un subconjunto expresivo de PHP pensado para experimentos de compilacion e interpretacion.
- **Alcance del lenguaje:** Soporta etiquetas `<?php ?>`, declaraciones `namespace`, `use`, clases y metodos, control de flujo (`if/else`, `foreach`), operadores aritmeticos y logicos, arrays con `=>`, acceso a miembros `->` y `::`, variables `$ident` y literales escalares (numeros enteros y flotantes, cadenas simples o dobles sin interpolacion). No reconoce herencia multiple, interpolacion de cadenas compleja, heredoc/nowdoc ni directivas especificas del motor Zend.
- **Dependencias clave:**
  - Python 3.13+
  - PLY (Python Lex-Yacc)
  - `pytest` para la suite automatizada

## 2. Arquitectura Tecnica
### 2.1 Componentes Principales
- `lexer_php_reducido.PhpLexer`: clase orientada a objetos que expone metodos `tokenize` y `print_tokens`, encapsulando el lexer generado por PLY y las reglas `t_*` como metodos de instancia.
- `lexer_php_reducido.LexerConfig`: dataclass inmutable que centraliza el diccionario de palabras reservadas y deriva la tupla completa de tokens consumida por PLY.
- `tests/test_tokens.py`: bateria de pruebas unitarias y parametrizadas que validan tokens individuales, escenarios completos y casos negativos de recuperacion ante errores.

### 2.2 Flujo General
1. Construir `LexerConfig` con la tabla de palabras reservadas.
2. Instanciar `PhpLexer`, lo que invoca `lex.lex(module=self)` para registrar reglas y generar el automata.
3. Alimentar el codigo fuente via `tokenize`/`print_tokens`; PLY produce objetos `LexToken` en orden de aparicion.
4. Consumir los tokens en la capa superior (impresion, pruebas, integracion futura) y manejar errores emitidos por `t_error`.

### 2.3 Diseno y Patrones
- **Dataclasses:** se usan para encapsular configuracion inmutable (`LexerConfig`), facilitando la extension de palabras reservadas sin tocar la logica del lexer.
- **Orientacion a objetos:** `PhpLexer` agrupa reglas y estado del analizador, permitiendo multiples instancias con configuraciones diferentes y simplificando pruebas.
- **Separacion de responsabilidades:** la capa de pruebas consume la API publica (`tokenize`), evitando dependencias directas con PLY y manteniendo la suite desacoplada del detalle interno.

## 3. Flujo de Analisis Lexico
- **Entrada aceptada:** codigo PHP en texto ASCII/UTF-8; se asume que las nuevas lineas usan `\n` o `\r\n` y que el archivo completo cabe en memoria.
- **Normalizacion previa:** no se aplica normalizacion adicional; el lexer opera directamente sobre la cadena de entrada entregada.
- **Tokenizacion:**
  - Palabras reservadas: mapeadas mediante `LexerConfig.reserved`, cubriendo palabras clave comunes (`function`, `class`, `namespace`, `foreach`, etc.).
  - Literales: numeros enteros o flotantes (identificados por expresion regular) y cadenas simples/dobles sin interpolacion; los valores se convierten a `int`, `float` o cadenas despojadas de comillas.
  - Operadores y delimitadores: cobertura para aritmetica (`+ - * / %`), logica (`&& || !`), comparacion (`== != === !== <= >=`), concatenacion (`.`), flechas `->`, resolucion de ambito `::`, `=>`, y simbolos de agrupacion/separacion.
- **Actualizacion de estado:** el metodo `t_newline` incrementa `lexer.lineno`; los comentarios de bloque actualizan el conteo de lineas segun saltos detectados.

## 4. Manejo de Errores
- **Estrategia `t_error`:** imprime un mensaje `[Lexer] Error lexico en linea X: caracter inesperado 'Y'` y avanza un caracter con `lexer.skip(1)` para continuar el analisis.
- **Cobertura negativa en pruebas:** se validan caracteres ilegales (`@`, `&`), identificadores mal formados (`$9abc`) y literales de cadena sin cerrar, confirmando que se reportan y que el flujo se recupera produciendo tokens posteriores.
- **Riesgos conocidos:** comentarios de bloque sin cierre se tokenizan como `DIVIDE` y `TIMES` sueltos (limitacion de la gramatica actual); no se detectan automaticamente secuencias UTF-8 invalidas ni se diferencian advertencias de errores fatales.

## 5. Uso de PLY en el Proceso de Compilacion
### 5.1 Rol de PLY en esta etapa
- PLY registra las reglas `t_*` definidas en `PhpLexer`, construyendo un lexer basado en automatas deterministas que produce `LexToken` al consumir la entrada.
- Dentro del pipeline de compilacion, la etapa lexica convierte caracteres en tokens significativos, sirviendo como base para un parser (futuro) que trabaje con unidades semanticas en lugar de texto crudo.

### 5.2 Ventajas de PLY para este proyecto
- Implementacion madura y bien documentada que replica el comportamiento de Lex/Yacc con semantica Python.
- Integracion directa con posibles analizadores sintacticos usando PLY, facilitando extender el proyecto hacia la construccion de AST o interpretes.
- Herramientas de depuracion (`debug`, `errorlog`, `lextab`) utiles para rastrear reglas conflictivas sin salir del ecosistema Python.

### 5.3 Buenas practicas actuales
- Organizacion de reglas como metodos de clase mantiene el codigo cohesivo y reutilizable; PLY admite este patron al recibir un modulo/objeto con atributos `t_*`.
- Separacion entre configuracion (`reserved`) y comportamiento permite modificar vocabulario sin regenerar manualmente tokens.
- Uso de pruebas automatizadas y `capsys` para capturar mensajes confirma que la integracion con PLY se comporta como se espera ante entradas validas e invalidas.

## 6. Estrategia de Pruebas
- Suite `pytest` con fixture `lexer` que crea una instancia fresca de `PhpLexer` en cada test, garantizando independencia entre casos.
- Cobertura actual: tokens unitarios, combinaciones parametrizadas, analisis de un programa PHP reducido completo (119 tokens) y escenarios negativos de recuperacion.
- Los tests se ejecutan de forma determinista en < 0.2 s usando el entorno virtual (`.venv`).

## 7. Procedimientos Operativos
- **Ejecutar demo:** `python lexer_php_reducido.py` imprime la lista de tokens generada a partir del snippet de demostracion incluido en el modulo.
- **Lanzar pruebas:** `.venv\Scripts\python.exe -m pytest`; requiere instalar dependencias (`pip install -r requirements.txt` si existe) y activar el entorno virtual.
- **Reproducir errores lexicos conocidos:** ejemplos rapidos `python -c "from lexer_php_reducido import PhpLexer; PhpLexer().print_tokens('$foo @ $bar')"` o `python -c "from lexer_php_reducido import PhpLexer; PhpLexer().print_tokens('echo \"hola')"`.
