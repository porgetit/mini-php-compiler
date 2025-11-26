<?php
namespace Demo;

use Lib\Utils;

class Greeter {
    public function greet($nombre = "visitante") {
        $0saludo = "Hola " . $0nombre;
        echo $0saludo;
    }
}

$g = new Greeter();
$g->greet()
?>