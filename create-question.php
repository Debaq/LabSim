
<?php

include 'conn.php';
$conn = mysqli_connect($dbhost, $dbuser, $dbpass, $dbname);

// Iniciar conexión con base de datos
if (!$conn) {
    die("Connection failed: " . mysqli_connect_error());
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


$name = $_POST['name'];
$code =$_POST['code'];

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
        $allowedfileExtensions = array('pdf', 'png', 'jpg');
        if (in_array($fileExtension, $allowedfileExtensions)) {
            $uploadFileDir = 'upload/';
            $dest_path = $uploadFileDir . $newFileName;
        }
        if(move_uploaded_file($fileTmpPath, $dest_path))
        {
            $query = "INSERT INTO question (Nombre, id_pregunta, Archivo) VALUES ('$name', '$code', '$dest_path')";
            if (mysqli_query($conn, $query)) {
                header("location:index.php?$newQuestionLink");

                echo "<div class='alert alert-success mt-4' role='alert'><h3>La pregunta fue ingresada</h3>
		              <a class='btn btn-outline-primary' href='index.php' role='button'>Volver</a></div>";

            } else {
                echo "Error: " . $query . "<br>" . mysqli_error($conn);
                echo "<div class='alert alert-success mt-4' role='alert'><h3>Error al subir los datos, si el error persiste favor avisar al administrador</h3>
		              <a class='btn btn-outline-primary' href='index.php' role='button'>Volver</a></div>";
                header("location:index.php?$newQuestionLink");
            }
        }
        else
        {
            echo "<div class='alert alert-success mt-4' role='alert'><h3>Error del archivo, favor verificar sea .pfd, .png o .jpg</h3>
		              <a class='btn btn-outline-primary' href='index.php' role='button'>Volver</a></div>";
            header("location:index.php?$newQuestionLink");
        }
    }else{
        echo "<div class='alert alert-success mt-4' role='alert'><h3>Debe seleccionar un archivo de extensión: .pfd, .png o .jpg</h3>
		              <a class='btn btn-outline-primary' href='index.php' role='button'>Volver</a></div>";
        header("location:index.php?$newQuestionLink");

    }
}