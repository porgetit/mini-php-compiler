<?php
namespace Demo;

use Lib\Utils;

class Greeter {
    public function greet($nombre = "visitante") {
        $saludo = "Hola " . $nombre;
        echo $saludo;
    }

    private function helper() {
        // Función auxiliar
    }
}

function test() {
    $greeter = new Greeter();
    $greeter->greet("Mundo");
}
?>