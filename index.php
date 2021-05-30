<?php
header("Content-Type: text/html;charset=utf-8");
session_start();
$user_check = $_SESSION['Nombre'];
$user_apellido = $_SESSION['Apellido'];
$user_email = $_SESSION['Correo'];
$privilegios = $_SESSION['Privilegios'];
$user_name = ($user_check . " " . $user_apellido);
#$user_name = utf8_encode($user_name);
$permitted_chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';

function generate_string($input, $strength = 16) {
    $input_length = strlen($input);
    $random_string = '';
    for($i = 0; $i < $strength; $i++) {
        $random_character = $input[mt_rand(0, $input_length - 1)];
        $random_string .= $random_character;
    }

    return $random_string;
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
$URI_code = "index.php?RX";
$URI_codeTest = strpos($URI_into, $URI_code);

if ($URI_codeTest) {
    decodifica_urlget($_SERVER["REQUEST_URI"]);
    $view = $_GET["view"];

    $idQ = $_GET["idQ"];
    $nameArea = $_GET["nameArea"];
    if ($view == "false") {
        $view = false;
    } else {
        $view = true;
    }
    if ($view == true) {
        #$nameArea = "Pregunta N° " . $idQ . "-" . $nameArea;
        $idArea = null;
    } else {
        $idArea = $_GET["idArea"];
    }

    $conector = ".-";

} else {

    $nameArea = null;
    $idArea = null;
    $view = false;
    $idQ = null;
    $conector = ".-";


}

$user_check = ucfirst($user_check);
if (!isset($_SESSION['Nombre'])) {
    header("location:login.php");
    die();
}

if ($privilegios == "Estudiante") {
    $Title = "LabSim";
} else {
    $Title = "LabSim";
}


?>
<!doctype html>
<html lang="es">

<head>

    <meta http-equiv="Content-type" content="text/html; charset=utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <meta name="description" content="">
    <meta name="author" content="">
    <title>
        <?php echo $Title; ?>
    </title>

    <!-- Custom fonts for this template-->
    <link href="../vendor/vendor/fontawesome-free/css/all.min.css" rel="stylesheet" type="text/css">
    <link href="https://fonts.googleapis.com/css?family=Nunito:200,200i,300,300i,400,400i,600,600i,700,700i,800,800i,900,900i"
          rel="stylesheet">
    <link href="cdn.datatables.net/plug-ins/1.10.20/i18n/Spanish.json">
    <!-- Custom styles for this template-->
    <link href="../vendor/css/sb-admin-2.css" rel="stylesheet">
    <link href="../vendor/vendor/datatables/dataTables.bootstrap4.min.css" rel="stylesheet">

    <?php if($privilegios != "Estudiante"){
        echo <<< TOU
    <script>
        
        function Set_Question(area, loc, id) {
            $.ajax({
                type: "post",
                url: "Set_Question.php",
                data: {area: area, id: id}
            }).done(function (info) {
                $(loc).html(info);
            });

        }
                
    </script>
TOU;

    } ?>


</head>
<body id="page-top">
<!-- Page Wrapper -->
<div id="wrapper">

    <?php include('bar.php') ?>
    <!-- Content Wrapper -->
    <div id="content-wrapper" class="d-flex flex-column">
        <!-- Main Content -->
        <div id="content">
            <?php include('sidebar.php') ?>


            <!-- Begin Page Content -->
            <div class="container-fluid">

                <!-- Page Heading -->
                <div class="d-sm-flex align-items-center justify-content-between mb-4">
                    <h1 class="h3 mb-0 text-gray-800">
                        <?php
                        if ($privilegios == "Docente") {
                            include('area_title.php');
                            echo "Tablero";
                            //echo $name_tablero;
                            echo "</h1></div>";

                        }
                        if ($privilegios == "Estudiante") {
                            include('area_title.php');
                            echo "Tablero - ";
                            echo $name_tablero;
                            echo "</h1></div>";
                        }
                        if ($privilegios == "Administrador") {
                            echo "</h1></div>";
                        }
                        if ($privilegios == "Director") {
                            echo "</h1></div>";
                        }
                        if ($privilegios == "Observador") {
                        }
                        ?>

                        <div>
                            <hr>
                            <div class="row">
                                <?php

                                if ($privilegios == "Docente") {
                                    if ($view == false) {

                                        if ($nameArea == 'Estudiantes'){
                                            include 'est_card.php';
                                        }
                                        if ($nameArea == 'Preguntas'){
                                            include 'question_card.php';
                                        }

                                    }
                                    if ($view == true) {
                                        if ($nameArea == 'newEst'){
                                            include 'create-user.php';
                                        }
                                        if ($nameArea == 'newQuestion'){
                                            include 'insert_question.php';

                                        }
                                        if ($nameArea == 'Preguntas'){
                                            include 'view_question.php';

                                        }
                                        if ($nameArea == 'Estudiantes'){
                                            include 'view_est.php';

                                        }

                                    }

                                }
                                if ($privilegios == "Estudiante") {
                                    if ($view == false ) {
                                        if ($nameArea == 'Sorteo') {include "Sorteo_pregunta.php";}
                                        if ($nameArea == 'Envio') {include "create-send.php";}
                                    }
                                    if ($view == true) {
                                        if ($nameArea == 'Sorteo') {include 'view_question.php';}
                                        }
                                    }

                                ?>
                            </div>
                        </div>
                        <!-- Footer -->
                        <footer class="sticky-footer bg-white">
                            <div class="container my-auto">
                                <div class="copyright text-center my-auto">
                                    <span>Examen Oral </span>
                                </div>
                            </div>
                        </footer>
                        <!-- End of Footer -->

                </div>
                <!-- End of Content Wrapper -->


                <!-- Scroll to Top Button-->
                <a class="scroll-to-top rounded" href="#page-top">
                    <i class="fas fa-angle-up"></i>
                </a>

                <!-- Logout Modal-->
                <div class="modal fade" id="logoutModal" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel"
                     aria-hidden="true">
                    <div class="modal-dialog" role="document">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="exampleModalLabel">¿Realmente quiere Salir?</h5>
                                <button class="close" type="button" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">×</span>
                                </button>
                            </div>
                            <div class="modal-body">Seleccione "Salir" para cerrar sesión.</div>
                            <div class="modal-footer">
                                <button class="btn btn-secondary" type="button" data-dismiss="modal">Cancel</button>

                                <a class="btn btn-primary" href="logout.php">Salir</a>
                            </div>
                        </div>
                    </div>
                </div>


                <!-- Bootstrap core JavaScript-->
                <script src="../vendor/vendor/jquery/jquery.min.js"></script>
                <script src="../vendor/vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
                <!-- Core plugin JavaScript-->
                <script src="../vendor/vendor/jquery-easing/jquery.easing.min.js"></script>

                <!-- Custom scripts for all pages-->
                <script src="js/sb-admin-2.min.js"></script>
                <script src="../vendor/vendor/datatables/jquery.dataTables.min.js"></script>
                <script src="../vendor/vendor/datatables/dataTables.bootstrap4.min.js"></script>

                <!-- Page level custom scripts -->
                <script src="../vendor/js/demo/datatables-demo.js"></script>
                <!-- <script src="js/tempo1.js"></script> -->
               <!-- <script>
                    $(document).ready(function () {
                        //Disable cut copy paste
                        $('body').bind('cut copy paste', function (e) {
                            e.preventDefault();
                        });

                        //Disable mouse right click
                        $("body").on("contextmenu",function(e){
                            return false;
                        });
                    });
                </script>-->
</body>

</html>
