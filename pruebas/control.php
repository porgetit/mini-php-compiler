<?php
$total = 0;

foreach ([1, 2, 3] as $valor) {
    $total = $total + $valor;
}

if ($total === 6) {
    print $total;
} else {
    print 0;
}
?>