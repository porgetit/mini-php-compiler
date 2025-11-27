"""Puerta de entrada del paquete lexer."""

from .core import LexerConfig, PhpLexer  # re-export principales


def demo(code: str) -> None:
    """Imprime tokens para una cadena de codigo PHP."""
    lexer = PhpLexer()
    for tok in lexer.tokenize(code):
        print(f"{tok.lineno:03d}: {tok.type:<15} {tok.value!r}")


if __name__ == "__main__":
    import sys

    sample = "<?php echo 'hola'; $a = 1 + 2; ?>"
    code = sample if len(sys.argv) == 1 else open(sys.argv[1], encoding="utf-8").read()
    demo(code)
