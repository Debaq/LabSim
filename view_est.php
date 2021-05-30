<?php


include'conn.php';

$mysqli = new mysqli($dbhost, $dbuser, $dbpass, $dbname);

if (mysqli_connect_errno()) {
    printf("Falló la conexión failed: %s\n", $mysqli->connect_error);
    exit();
}
mysqli_set_charset($mysqli,"utf8");
$getEstudiante = mysqli_query($mysqli, "SELECT * FROM users WHERE id_user_o = '$idQ'");
$result = mysqli_fetch_assoc($getEstudiante);

$name = $result["Nombre"];
$apellido = $result["Apellido"];
$NA = $name." ".$apellido;
$state_user = $result["Activo"];
$Tiempo1 = $result["Tiempo1"];
$Tiempo2 = $result["Tiempo2"];
$Archivo = $result["Archivo"];
$Pregunta = $result["Pregunta"];


$idQ_codificado = codifica_urlget('id='.$idQ);
if ($state_user == 1){
    $state_btn = "Desactivar";
}else{$state_btn = "Activar";}

$urlyou = "</div></div></div></div></div></div></div>";




if($Tiempo1== null){
    $Tiempo1 = " aun no hay entrega";
    $Archivo = "#";
}else{
   $Tiempo1 = date("d/m/Y H:i:s", $Tiempo1);
}


if($Tiempo2 == null){
    $Tiempo2 = " aun no hay entrega";
}else {
    $Link_video_full = $result["Link_video"];
    $abuscar = "youtu.be";
    $pos = strpos($Link_video_full, $abuscar);
    if ($pos == true) {
        $Link_video = str_replace("https://youtu.be/", "", $Link_video_full);
        $urlyou = '<iframe width="100%" height="800" src="https://www.youtube.com/embed/' . $Link_video . '" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div></div></div></div></div></div>';
    } else {
        $urlyou = ' <a href="' . $Link_video_full . '">Link del vídeo</a>';
    }
    $Tiempo2 = date("d/m/Y H:i:s", $Tiempo2);

}

$getQuestion = mysqli_query($mysqli, "SELECT * FROM question WHERE id_pregunta = '$Pregunta'");
$resultQ = mysqli_fetch_assoc($getQuestion);
$Nombre_pregunta = $resultQ['Nombre'];



$BTN_docentes = <<< TAU
  <div class="container">
    <div class="card o-hidden border-0 shadow-lg my-5">
      <div class="card-body p-0">
        <div class="row">
          <div class="col-lg-12">
            <div class="p-2">
            <div class="text-center">
                <h1 class="h4 text-gray-900 mb-4">$NA</h1>
                <h1 class="h4 text-gray-900 mb-4">$Nombre_pregunta</h1>

              </div>
        <form class="user" name="new_user" action="mod-user.php?$idQ_codificado" method="POST" enctype="multipart/form-data">
            <div class="form-group row">
                <div class="col-xl-2">
                    <input type="submit" id="submit" name="btn" value="Eliminar"  class="btn btn-danger btn-user btn-block">
                </div>
                <div class="col-xl-2">
                    <input type="submit" id="submit" name="btn" value="$state_btn"  class="btn btn-dark btn-user btn-block">
                </div>
             
            </div>
            <hr>
        </form>
            <h1 class="h4 text-gray-900 mb-4">Archivo</h1>
            Fecha de entrega:$Tiempo1 <br>
            PDF: <a href="$Archivo">Link</a>
            <hr>
            <h1 class="h4 text-gray-900 mb-4">Vídeo</h1>
            Fecha de entrega: $Tiempo2
</div>
TAU;




#$Frame = '<iframe src="'.$file.'" width="100%" height="600px"></iframe></div></div></div></div></div></div>';

$mysqli->close();

if ($privilegios == "Docente"){
    echo $BTN_docentes;
    echo $urlyou;
}

