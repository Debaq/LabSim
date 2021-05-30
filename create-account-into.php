<?php
include 'conn.php';
$conn = mysqli_connect($dbhost, $dbuser, $dbpass, $dbname);

// Iniciar conexión con base de datos
if (!$conn) {
	die("Connection failed: " . mysqli_connect_error());
}
// Revisa si el correo existe
$email = $_POST["email"];
$checkEmail = "SELECT * FROM users WHERE Correo = '$email' ";
// Se obtiene los correo que conciden
$result = $conn-> query($checkEmail);

function codifica_urlget(string $cadena): string
{
    $cadena = utf8_encode($cadena); // Codifico a UTF-8
    $control = "Esteman106Control";
    $cadena = $control . $cadena . $control;  // Agrego al inicio y al final la palabra de control
    $cadena = base64_encode($cadena);  // Codifico en Base64
    return $cadena;
}

// la variable $count tiene el resultado de esta busqueda
$count = mysqli_num_rows($result);

// si count == 1 significa que la cuenta ya existe, por tanto da aviso de ello
if ($count == 1) {
    echo "<div class='alert alert-warning mt-4' role='alert'>
                    <p>La cuenta o correo ya esta en uso</p>
                    <p><a href='login.php'>Por favor ingrese con su cuenta aquí</a></p>
                </div>";
    }
else {
    //si el correo no exite se creará una nueva cuenta con los datos proporcionados
    $name = $_POST["name"];
    $apellido = $_POST["apellido"];
    $pass = $_POST["password"];
    $privilegios = $_POST["privilegio"];

    // The password_hash() function convert the password in a hash before send it to the database
    $passHash = password_hash($pass, PASSWORD_DEFAULT);

    // Query to send Name, Email and Password hash to the database
    $query = "INSERT INTO users (Nombre, Apellido, Correo, Contrasena, Privilegios) VALUES ('$name', '$apellido', '$email', '$passHash', '$privilegios')";

    if (mysqli_query($conn, $query)) {

        $newUserLink = codifica_urlget("nameArea=Estudiantes&idArea=0&view=false&idQ=0");

        header("location:index.php?$newUserLink");

    } else {
            header("location:index.php?$newUserLink");


        }
}
mysqli_close($conn);
