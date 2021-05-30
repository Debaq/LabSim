<?php
include 'conn.php';
$mysqli = new mysqli($dbhost, $dbuser, $dbpass, $dbname);

if (mysqli_connect_errno()) {
    printf("Falló la conexión failed: %s\n", $mysqli->connect_error);
    exit();
}
mysqli_set_charset($mysqli, "utf8");
// que id es el estudiante
$id_user = $_SESSION['id'];

$SorteoState = "SELECT Activo, Pregunta FROM users WHERE id_user_O ='$id_user'";
$SorteoState = $mysqli->query($SorteoState);
$SorteoSorteo = mysqli_fetch_assoc($SorteoState);

$Activo = $SorteoSorteo["Activo"];
$Pregunta = $SorteoSorteo["Pregunta"];



if ($Activo == "1") {
    if ($Pregunta == null) {
        $getPreguntas = "SELECT * FROM question WHERE Disponible = '1'";
        $Preguntas = $mysqli->query($getPreguntas);
        for ($arraySetPreguntas = array(); $row = $Preguntas->fetch_assoc(); $arraySetPreguntas[] = $row) ;
        $countSetAreas = count($arraySetPreguntas);
        echo <<< TAU
        <form class="form-inline" action="sortear.php" method="POST">
          <div class="form-group mb-2">
          Información:<br>
          El sorteo se realiza tomando todas las preguntas disponibles y ordenandolas aleatoriamente como barajar naipes, una vez esten ordenadas se le asociará la pregunta según el número que usted establezca.<br>
            <input type="text" readonly class="form-control-plaintext" id="staticEmail2" value="Favor seleccione un número del 1 al $countSetAreas">
          </div>
          <div class="form-group mx-sm-3 mb-2">
            <input type="number" class="form-control" name="numberMagic" id="numberMagic" min="1" max="$countSetAreas" required>
          </div>
          <button type="submit" class="btn btn-primary mb-2">Seleccionar y Sortear</button>
        </form>
TAU;
        echo "</div></div>";

    } else {
        $txt_idQuestion = "nameArea=Sorteo&idArea=&view=true&idQ=" . $Pregunta;
        $idWeb = codifica_urlget($txt_idQuestion);
        #header("location:index.php?$idWeb");
        echo '<meta http-equiv="refresh" content="0; url=index.php?'.$idWeb.'">';
    }
}else{
    echo "El acceso al sorteo aun se encuentra deshabilitado, ingrese al link Zoom que disponible en la parte superior y espere ser aceptado/a, esto puede tomar un tiempo pues ingresarán a medida que se realizen los examenes";
    echo "</div></div>";
}






