
<?php
session_start();
$mail = $_SESSION['Correo'];
include 'conn.php';
$conn = mysqli_connect($dbhost, $dbuser, $dbpass, $dbname);

// Iniciar conexión con base de datos
if (!$conn) {
    die("Connection failed: " . mysqli_connect_error());
}
$Tiempo1 = time();

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

function codifica_urlget(string $cadena): string
{
    $cadena = utf8_encode($cadena); // Codifico a UTF-8
    $control = "Esteman106Control";
    $cadena = $control . $cadena . $control;  // Agrego al inicio y al final la palabra de control
    $cadena = base64_encode($cadena);  // Codifico en Base64
    return $cadena;
}
$newQuestionLink = codifica_urlget("nameArea=Preguntas&idArea=0&view=false&idQ=0");


$code = generate_string($permitted_chars, 10);

if (isset($_POST['uploadBtn']) && $_POST['uploadBtn'] == 'Subir') {
    if (isset($_FILES['documento']) && $_FILES['documento']['error'] === UPLOAD_ERR_OK) {
        // get details of the uploaded file
        $fileTmpPath = $_FILES['documento']['tmp_name'];
        $fileName = $_FILES['documento']['name'];
        $fileSize = $_FILES['documento']['size'];
        $fileType = $_FILES['documento']['type'];
        $fileNameCmps = explode(".", $fileName);
        $fileExtension = strtolower(end($fileNameCmps));
        $newFileName = $code. '.' . $fileExtension;
        $allowedfileExtensions = array('pdf');
        if (in_array($fileExtension, $allowedfileExtensions)) {
            $uploadFileDir = 'answer/';
            $dest_path = $uploadFileDir . $newFileName;
        }
        if(move_uploaded_file($fileTmpPath, $dest_path))
        {
            $query = "UPDATE users SET Tiempo1='$Tiempo1', Archivo='$dest_path' WHERE Correo='$mail'";
            if (mysqli_query($conn, $query)) {
                header("location:index.php");

         }
        }
    }
        header("location:index.php?$newQuestionLink");

    }
if ($_POST["link"] !== ""){
    $link = $_POST["link"];
    $query = "UPDATE users SET Tiempo2='$Tiempo1', Link_video='$link' WHERE Correo='$mail'";
    if (mysqli_query($conn, $query)) {
        echo "Lo logramos";
        header("location:index.php");

    }
}
