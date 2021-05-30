<?php
date_default_timezone_set("America/Santiago");
$code = generate_string($permitted_chars, 10);
$Tiempo1 = time();
$date = date("d/m/Y H:i:s");
$user_email = $_SESSION['Correo'];


include'conn.php';

$mysqli = new mysqli($dbhost, $dbuser, $dbpass, $dbname);

if (mysqli_connect_errno()) {
    printf("Falló la conexión failed: %s\n", $mysqli->connect_error);
    exit();
}
mysqli_set_charset($mysqli,"utf8");
$getUser = mysqli_query($mysqli, "SELECT * FROM users WHERE Correo = '$user_email'");
$result = mysqli_fetch_assoc($getUser);
$mysqli->close();
$Activo = $result["Activo"];
$Sortear = $result["Pregunta"];


if($Activo == 1) {
    if ($Sortear !== null) {
        $link_PDF = $result["Archivo"];
        $Link_video = $result["Link_video"];
        $Tiempo1 = $result["Tiempo1"];
        $Tiempo2 = $result["Tiempo2"];


        if ($Tiempo1 == null) {
            $Tiempo1 = " aun no hay entrega";

        }
        if ($Tiempo2 == null) {
            $Tiempo2 = " aun no hay entrega";
        }


        $Archivo = $result["Archivo"];


        if ($Archivo == null) {
            $Archivo = " aun no hay entrega";
        }

        if ($Tiempo1 > $Tiempo2) {
            $F_ultimo = date("d/m/Y H:i:s", $Tiempo1);
        }else{ $F_ultimo = "aún no hay entregas";}
        if ($Tiempo1 < $Tiempo2){
            $F_ultimo = date("d/m/Y H:i:s", $Tiempo2);
        }


        echo <<< TAO
    
      <div class="container">
    
        <div class="card o-hidden border-0 shadow-lg my-5">
          <div class="card-body p-0">
            <!-- Nested Row within Card Body -->
            <div class="row">
              <div class="col-lg-5 d-none d-lg-block bg-register-image"></div>
              <div class="col-lg-7">
                <div class="p-5">
                  <div class="text-center">
                    <h1 class="h4 text-gray-900 mb-4">Enviar Productos</h1>
                  </div>
                  <form class="user" name="new_user" action="send_answers.php" method="POST" enctype="multipart/form-data">
    
                    <div class="form-group row">
                      <div class="col-sm-6 mb-3 mb-sm-0">
                        <input type="text" class="form-control form-control-user" name="link" placeholder="Link del Vídeo">
                      </div>
                      <div class="col-sm-6">
                        <input type="text" class="form-control form-control-user" name="code" placeholder="$date" value="$date" readonly>
                      </div>
       
                    </div>
    
                    <div class="form-group">
                    Documento en  : 
                        <input type="file" id="documento" name="documento" accept="image/*">                
                    </div>
    
                    <input type="submit" id="submit" name="uploadBtn" value="Subir"  class="btn btn-primary btn-user btn-block">
                    <hr>
                </form>
                Último Envio: $F_ultimo <br>
                DOC: <a href="$link_PDF">Link</a><br>
                Vídeo: <a href="$Link_video">Link</a><br>
                </div>
              </div>
            </div>
          </div>
        </div>
    
      </div>
      </div>
      </div>
TAO;

    }else{
        echo "Debe sortear una pregunta antes de poder enviar su trabajo, favor ingresar al link de 'Pregunta'";
        echo "</div></div>";
    }

    } else {
        echo "Se ha deshabilitado el acceso a las preguntas y al sorteo, si esto es un error comuníquese con su docente";
        echo "</div></div>";
    }