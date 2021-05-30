<?php


include'conn.php';

$mysqli = new mysqli($dbhost, $dbuser, $dbpass, $dbname);

if (mysqli_connect_errno()) {
    printf("Falló la conexión failed: %s\n", $mysqli->connect_error);
    exit();
}
mysqli_set_charset($mysqli,"utf8");
$getQuestion = mysqli_query($mysqli, "SELECT * FROM question WHERE id_pregunta = '$idQ'");
$result = mysqli_fetch_assoc($getQuestion);
$mysqli->close();
$file = $result["Archivo"];
$state_question = $result["Disponible"];
$name_question = $result["Nombre"];
$idQ_codificado = codifica_urlget('id='.$idQ);



if ($state_question == 1){
    $state_btn = "Desactivar";
}else{$state_btn = "Activar";}

$BTN_docentes = <<< TAU
  <div class="container">
    <div class="card o-hidden border-0 shadow-lg my-5">
      <div class="card-body p-0">
        <div class="row">
          <div class="col-lg-12">
            <div class="p-2">
            <div class="text-center">
                <h1 class="h4 text-gray-900 mb-4">$name_question</h1>
              </div>
        <form class="user" name="new_user" action="mod-question.php?$idQ_codificado" method="POST" enctype="multipart/form-data">
            <div class="form-group row">
                <div class="col-xl-2">
                    <input type="submit" id="submit" name="btn" value="Descargar"  class="btn btn-primary btn-user btn-block">
                </div>
                <div class="col-xl-2">
                    <input type="submit" id="submit" name="btn" value="Eliminar"  class="btn btn-danger btn-user btn-block">
                </div>
                <div class="col-xl-2">
                    <input type="submit" id="submit" name="btn" value="$state_btn"  class="btn btn-dark btn-user btn-block">
                </div>
             
            </div>
            <hr>
        </form>
</div>
TAU;


$BTN_estudiantes = <<< TAU
  <div class="container">
    <div class="card o-hidden border-0 shadow-lg my-5">
      <div class="card-body p-0">
        <div class="row">
          <div class="col-lg-12">
            <div class="p-2">
            <div class="text-center">
                <h1 class="h4 text-gray-900 mb-4">$name_question</h1>
              </div>
        <form class="user" name="new_user" action="mod-question.php?$idQ_codificado" method="POST" enctype="multipart/form-data">
            <div class="form-group row">
                <div class="col-xl-2">
                    <input type="submit" id="submit" name="btn" value="Descargar"  class="btn btn-primary btn-user btn-block">
                </div>
            
            </div>
            <hr>
        </form>
</div>
TAU;


$Frame = '<iframe src="'.$file.'" width="100%" height="600px"></iframe></div></div></div></div></div></div>';


if ($privilegios == "Docente"){
    echo $BTN_docentes;
    echo $Frame;
}


if ($privilegios == "Estudiante"){
    echo $BTN_estudiantes;
    echo $Frame;
}