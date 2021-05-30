<?php
$user_check = ucfirst($user_check);
if (!isset($_SESSION['Nombre'])) {
    header("location:login.php");
    die();
}

if ($privilegios == "Estudiante") {
    header("location:logout.php");
    die();
}

include 'conn.php';

$mysqli = new mysqli($dbhost, $dbuser, $dbpass, $dbname);
if (mysqli_connect_errno()) {
    printf("Falló la conexión failed: %s\n", $mysqli->connect_error);
    exit();
}
mysqli_set_charset($mysqli, "utf8");

$setEstudiante = "SELECT * FROM `users` WHERE `Privilegios` = 'Estudiante'";
$resultSetEstudiante = $mysqli->query($setEstudiante);
for ($arraySetEstudiante = array(); $row = $resultSetEstudiante->fetch_assoc(); $arraySetEstudiante[] = $row) ;

$newUserLink = codifica_urlget("nameArea=newEst&idArea=0&view=true&idQ=0");

if (!empty($arraySetEstudiante)) {
    $count = count($arraySetEstudiante);
    #echo generate_string($permitted_chars, 10);



echo <<< TEO
    <div class="col-xl-2 col-md-6 mb-4">
              <a href="index.php?$newUserLink">
              <div class="card border-left-info shadow h-100 py-2">
                <div class="card-body">
                  <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="h5 mb-0 font-weight-bold text-gray-800 text-truncate" style="max-width: 5000px;" >Crear nuevo</div> 
                      </div>
                    <div class="col-auto">
                  <i class="fas fa-fw fa-plus"></i>
                    </div>
                  </div>
                </div>
              </div>
              </a>
          </div>
TEO;
    for ($x = 0; $x < $count; $x++) {
        $N = $arraySetEstudiante[$x]["Nombre"];
        $A = $arraySetEstudiante[$x]["Apellido"];
        $NA = $N." ".$A;
        $Correo = $arraySetEstudiante[$x]["Correo"];
        $Fn = $arraySetEstudiante[$x]["Fono"];
        $Ph = $arraySetEstudiante[$x]["Foto"];
        $IdUser = $arraySetEstudiante[$x]["id_user_O"];
        $Usernumber = $arraySetEstudiante[$x]["posicion"];
        $Phthumb = $Ph."_thumb.png";
        $Pregunta = $arraySetEstudiante[$x]["Pregunta"];
        $txt_idQ = "nameArea=Estudiantes&idArea=&view=true&idQ=" . $IdUser;
        $avaliable_User = $arraySetEstudiante[$x]["Activo"];
        if($avaliable_User==1){$color_question = "border-left-success";}else{$color_question = "bg-gray-500";}

        $getQuestion = mysqli_query($mysqli, "SELECT * FROM question WHERE id_pregunta = '$Pregunta'");
        $resultQ = mysqli_fetch_assoc($getQuestion);
        $Nombre_pregunta = $resultQ['Nombre'];
        $idWeb = codifica_urlget($txt_idQ);
        $Timepo1 = $arraySetEstudiante[$x]["Tiempo1"];

        $card = <<< EOT
            <div class="col-xl-3 col-md-6 mb-4">
              <a href="index.php?$idWeb">
              <div class="card $color_question shadow h-100 py-2">
                <div class="card-body">
                  <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="h5 mb-0 font-weight-bold text-gray-800 text-truncate" style="max-width: 5000px;" >$NA</div> 
                        <div class="text-xs font-weight-bold text-primary mb-1">$Correo</div>
                        <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">$Nombre_pregunta</div>


                      </div>
                    <div class="col-auto">
                    <img class="img-profile rounded-circle" width="48" src="photo_profile/$Phthumb">
                    </div>
                  </div>
                </div>
              </div>
              </a>
          </div>
EOT;
        echo $card;
    }
    echo "</div></div>";

    $mysqli->close();
} else {
    $card = <<< EOT
                     </div>
                      <footer class="sticky-footer bg-white">
                      <div class="container my-auto">
                        <div class="copyright text-center my-auto">
                        <img class="img-responsive" src="img/logo.png">

                        </div>
                        
                        <div class="copyright text-center my-auto">
                         <h2>Aun no hay estudiantes.</h2>
                        </div>
                        <div class="copyright text-center my-auto">
                            <a class="btn btn-primary btn-user" href="index.php?$newUserLink" role="button">registre estudiantes</a>
                         </div>
                      </div>
                    </footer>
                    </div>
EOT;
    echo $card;
}

?>