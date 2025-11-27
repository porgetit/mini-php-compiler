import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.facade import CompilerFacade


def test_semantic_reports_undeclared_variable():
    code = "<?php echo $x; ?>"
    result = CompilerFacade().compile(code)

    assert result.semantic_errors == 1
    assert any("not declared" in m["message"].lower() for m in result.semantic_messages)
    assert result.ok is False


def test_semantic_passes_when_symbols_exist():
    code = "<?php $a = 1; echo $a; ?>"
    result = CompilerFacade().compile(code)

    assert result.semantic_errors == 0
    assert result.ok is True


def test_symbol_table_includes_functions_classes_and_methods():
    code = """
    <?php
    function util($x = 5) {
        $y;
        $y = $x;
    }
    class Greeter {
        public function hello($name = "guest") {
            $msg;
            $msg = $name;
        }
    }
    $g;
    $g = new Greeter();
    ?>
    """
    result = CompilerFacade().compile(code)
    table = result.symbol_table

    def find_symbol(scope_name, name):
        for scope in table:
            if scope.get("name") == scope_name:
                for sym in scope.get("symbols", []):
                    if sym.get("name") == name:
                        return sym
        return None

    util_sym = find_symbol("global", "util")
    greeter_sym = find_symbol("global", "Greeter")
    hello_sym = find_symbol("Greeter", "hello")
    g_var = find_symbol("global", "$g")

    assert util_sym and util_sym["kind"] == "func"
    assert greeter_sym and greeter_sym["kind"] == "class"
    assert greeter_sym["value"] and "hello" in greeter_sym["value"].get("methods", [])
    assert hello_sym and hello_sym["kind"] == "method" and hello_sym["owner"] == "Greeter"
    assert g_var and g_var["kind"] == "var"


def test_arithmetic_operator_on_non_numeric_reports_error():
    code = "<?php $a = 'text' + 'more'; ?>"
    result = CompilerFacade().compile(code)

    assert result.semantic_errors == 1
    assert any("Arithmetic operator" in m["message"] for m in result.semantic_messages)
    assert result.ok is False
