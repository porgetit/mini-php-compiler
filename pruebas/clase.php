<?php
namespace Demo;

use Lib\Utils;

class Greeter {
    public function greet($nombre = "visitante") {
        $saludo = "Hola " . $nombre;
        echo $saludo;
    }
}

$g = new Greeter();
$g->greet();
?>
