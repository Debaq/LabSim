<?php
session_start();

if (!isset($_SESSION['Nombre'])) {
    header("location:login.php");
    die();
}

function decodifica_urlget(string $cadena)
{
    $arraycad = explode("?", $cadena); // Creo array apartir de la URL, separandolo por ?
    $cadena = $arraycad[1]; // Utilizo segundo array
    $cadena = base64_decode($cadena); // Decodifico
    $control = "Esteman106Control"; // la misma frase de control
    $cadena = str_replace($control, "", "$cadena"); // Remuevo la frase de control
    $cadena_get = explode("&", $cadena);
    foreach ($cadena_get as $value) {
        $val_gets = explode("=", $value);
        $_GET[$val_gets[0]] = utf8_decode($val_gets[1]);
    }
}

function codifica_urlget(string $cadena): string
{
    $cadena = utf8_encode($cadena); // Codifico a UTF-8
    $control = "Esteman106Control";
    $cadena = $control . $cadena . $control;  // Agrego al inicio y al final la palabra de control
    $cadena = base64_encode($cadena);  // Codifico en Base64
    return $cadena;
}

$URI_into = $_SERVER["REQUEST_URI"];
$URI_code = "mod-question.php?";
$URI_codeTest = strpos($URI_into, $URI_code);
$newQuestionLink = codifica_urlget("nameArea=Preguntas&idArea=0&view=false&idQ=0");


if ($URI_codeTest) {
    decodifica_urlget($_SERVER["REQUEST_URI"]);
    $idQ = $_GET["id"];
    $btn = $_POST["btn"];

    include 'conn.php';
    $mysqli = new mysqli($dbhost, $dbuser, $dbpass, $dbname);
    if (mysqli_connect_errno()) {
        printf("Falló la conexión failed: %s\n", $mysqli->connect_error);
        exit();
    }


    if($btn == "Desactivar"){
        $Q_UPDATE = mysqli_query($mysqli, "UPDATE question SET Disponible='0'WHERE id_pregunta='$idQ'");
        mysqli_close($mysqli);
        header("location:index.php?$newQuestionLink");
    }
    if($btn == "Activar"){
        $Q_UPDATE = mysqli_query($mysqli, "UPDATE question SET Disponible='1'WHERE id_pregunta='$idQ'");
        mysqli_close($mysqli);
        header("location:index.php?$newQuestionLink");
    }
    if($btn == "Eliminar"){
        $Q_UPDATE = mysqli_query($mysqli, "UPDATE question SET Disponible='0', Hide='1'WHERE id_pregunta='$idQ'");
        mysqli_close($mysqli);
        header("location:index.php?$newQuestionLink");
    }

    if($btn == "Descargar"){
        $getQuestion = mysqli_query($mysqli, "SELECT * FROM question WHERE id_pregunta = '$idQ'");
        $result = mysqli_fetch_assoc($getQuestion);
        $mysqli->close();

        $filePath = $result["Archivo"];

        $info = new SplFileInfo($filePath);
        $extension = ($info->getExtension());
        $fileName = $result["Nombre"].".".$extension;
        $fileName=str_replace(" ", "_",$fileName);

        if(!empty($fileName) && file_exists($filePath)){
            // Define headers
            header("Cache-Control: public");
            header("Content-Description: File Transfer");
            header("Content-Disposition: attachment; filename=$fileName");
            header("Content-Type: application/zip");
            header("Content-Transfer-Encoding: binary");

            // Read the file
           readfile($filePath);
           exit;
        }
        header("location:index.php?$newQuestionLink");
    }








} else {
    echo "no hay  nada";

}