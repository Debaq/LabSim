<?php

if ($privilegios == "Docente") {
    if ($URI_codeTest) {

    } else {
        $name_tablero = "General";
    }
}


if ($privilegios == "Estudiante") {
    if ($nameArea != null) {
        $name_tablero = $nameArea;
    } else {
        $name_tablero = "General";
    }
}
