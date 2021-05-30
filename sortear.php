<?php
session_start();

include 'conn.php';
$mysqli = new mysqli($dbhost, $dbuser, $dbpass, $dbname);

if (mysqli_connect_errno()) {
    printf("Falló la conexión failed: %s\n", $mysqli->connect_error);
    exit();
}
mysqli_set_charset($mysqli, "utf8");
// que id es el estudiante
$id_user = $_SESSION['id'];



$SorteoState = "SELECT Activo, Pregunta, Nombre FROM users WHERE id_user_O ='$id_user'";
$SorteoState = $mysqli->query($SorteoState);
$SorteoSorteo = mysqli_fetch_assoc($SorteoState);

$Activo = $SorteoSorteo["Activo"];
$Pregunta = $SorteoSorteo["Pregunta"];


$postSuerte = $_POST["numberMagic"]-1;
if(isset($_SERVER['HTTP_REFERER'])) {
    $previous = $_SERVER['HTTP_REFERER'];
}
if($Activo ==1){
    if($Pregunta==null){

    $getPreguntas = "SELECT * FROM question WHERE Disponible = '1'";
    $Preguntas = $mysqli->query($getPreguntas);
    for ($arraySetPreguntas = array(); $row = $Preguntas->fetch_assoc(); $arraySetPreguntas[] = $row) ;
    $countSetAreas = count($arraySetPreguntas);
    $arraySorteo = array();

    for ($x =0;  $x < $countSetAreas; $x++){
        $ide = $arraySetPreguntas[$x]['id_pregunta'];
        $Name = $arraySetPreguntas[$x]['Nombre'];
        $preg = array('nombre' => $Name,
            'id' => $ide);
        array_push($arraySorteo, $preg);
        }
    }

    shuffle($arraySorteo);
    $Pregunta_seleccionada = $arraySorteo[$postSuerte]["id"];
    $Sorteo_UPDATE = mysqli_query($mysqli, "UPDATE users SET Pregunta='$Pregunta_seleccionada'WHERE id_user_O='$id_user' ");
    $Sorteo_Pregunta = mysqli_query($mysqli, "UPDATE question SET Disponible='0'WHERE id_pregunta='$Pregunta_seleccionada' ");

    echo "<h1>Resultados</h1></p>";
    echo "Pregunta Seleccionada: ".$arraySorteo[$postSuerte]["id"]." => ".$arraySorteo[$postSuerte]["nombre"];
    echo "<hr>";
    echo "<br>";
    echo "Sorteo: <br>";
    for($x=0; $x < $countSetAreas; $x++){
        $numbre = $x+1;
        echo $numbre.".-".$arraySorteo[$x]["id"]."<br>";
    }
    echo "<hr>";
    echo '<a href="'.$previous.'">Volver</a>';



}


