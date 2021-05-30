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

$setQuestion = "SELECT `id`,`id_pregunta`,`Nombre`,`Disponible`,`Archivo`, `Hide` FROM `question`";
$resultSetQuestion = $mysqli->query($setQuestion);
for ($arraySetQuestion = array(); $row = $resultSetQuestion->fetch_assoc(); $arraySetQuestion[] = $row) ;

$newQuestionLink = codifica_urlget("nameArea=newQuestion&idArea=0&view=true&idQ=0");

if (!empty($arraySetQuestion)) {
    $count = count($arraySetQuestion);
    #echo generate_string($permitted_chars, 10);

    echo <<< TEO
    <div class="col-xl-2 col-md-6 mb-4">
              <a href="index.php?$newQuestionLink">
              <div class="card border-left-info shadow h-100 py-2">
                <div class="card-body">
                  <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="h5 mb-0 font-weight-bold text-gray-800 text-truncate" style="max-width: 5000px;" >Agregar pregunta</div> 
                      </div>
                    <div class="col-auto">
                  <i class="fas fa-fw fa-plus "></i>
                    </div>
                  </div>
                </div>
              </div>
              </a>
          </div>
TEO;
    for ($x = 0; $x < $count; $x++) {
        $id_Question = $arraySetQuestion[$x]["id"];
        $code_Question = $arraySetQuestion[$x]["id_pregunta"];
        $avaliable_Question = $arraySetQuestion[$x]["Disponible"];
        $file_question = $arraySetQuestion[$x]["Archivo"];
        $NA = $arraySetQuestion[$x]["Nombre"];
        if($avaliable_Question==1){$color_question = "border-left-success";}else{$color_question = "bg-gray-500";}
        $txt_idQuestion = "nameArea=Preguntas&idArea=&view=true&idQ=" . $code_Question;
        $idWeb = codifica_urlget($txt_idQuestion);
        $Hide_question = $arraySetQuestion[$x]["Hide"];

        $card = <<< EOT
            <div class="col-xl-3 col-md-6 mb-4">
              <a href="index.php?$idWeb">
              <div class="card $color_question shadow h-100 py-2">
                <div class="card-body">
                  <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">$code_Question</div>
                        <div class="h5 mb-0 font-weight-bold text-gray-800 text-truncate" style="max-width: 5000px;" >$NA</div> 

                      </div>
                    <div class="col-auto">
                        <i class="far fa-fw fa-file-pdf fa-2x"></i>

                    </div>
                  </div>
                </div>
              </div>
              </a>
          </div>
EOT;
        if($Hide_question == 0){
            echo $card;
        }

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
                         <h2>Aun no hay preguntas.</h2>
                        </div>
                        <div class="copyright text-center my-auto">
                            <a class="btn btn-primary btn-user" href="index.php?$newQuestionLink" role="button">registre una nueva pregunta</a>
                         </div>
                      </div>
                    </footer>
                    </div>
EOT;
    echo $card;
}

?>