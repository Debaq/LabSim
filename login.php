<?php
// Required field names
$required = array('lis_person_contact_email_primary', 'lis_person_name_given', 'lis_person_name_family');

// Loop over field names, make sure each one exists and is not empty
$error = false;
foreach($required as $field) {
  if (empty($_POST[$field])) {
    $error = true;
  }
}

if ($error) {
  echo "vuelva a ingresar desde siveduc";
} else {



session_start();
$IP = $_SERVER['REMOTE_ADDR'];

include 'conn.php';
$conn = mysqli_connect($dbhost, $dbuser, $dbpass, $dbname);


// Iniciar conexión con base de datos
if (!$conn) {
	die("Connection failed: " . mysqli_connect_error());
}
// Revisa si el correo existe
$email = $_POST["lis_person_contact_email_primary"];
$checkEmail = "SELECT * FROM users WHERE Correo = '$email' ";
// Se obtiene los correo que conciden
$result = $conn-> query($checkEmail);
$row = mysqli_fetch_assoc($result);




// la variable $count tiene el resultado de esta busqueda
$count = mysqli_num_rows($result);

// si count == 1 significa que la cuenta ya existe, por tanto da aviso de ello
if ($count == 1) {
        $_SESSION['id'] = $row["id_user_O"];
        $_SESSION['loggedin'] = true;
        $_SESSION['Nombre'] = $row['Nombre'];
        $_SESSION['start'] = time();
        $_SESSION['expire'] = $_SESSION['start'] + (1 * 60);
        $_SESSION['Apellido'] = $row['Apellido'];
        $_SESSION['Privilegios'] = $row['Privilegios'];
        $_SESSION['Correo'] = $row['Correo'];
        $_SESSION["IP"] = $row['IP'];
        $_SESSION["Foto"] = $row['Foto'];
        $_SESSION["Tiempo1"] = $row['Tiempo1'];
        $_SESSION["Tiempo2"] = $row['Tiempo2'];

        $ID_USER = $_SESSION['id'];

        $IP_UPDATE = mysqli_query($conn, "UPDATE users SET IP='$IP' WHERE id_user_O='$ID_USER'");
        mysqli_close($conn);
        header('Location: index.php');
        
    }
else {
    //si el correo no exite se creará una nueva cuenta con los datos proporcionados
    $name = $_POST["lis_person_name_given"];
    $apellido = $_POST["lis_person_name_family"];
    $pass = "1234";
    $role = $_POST["roles"];
Yeah that makes total sense. If there were auto updates for windows/mac that worked directly in fbs this definitely would be a non-issue per say.

Having spent awhile making a "solution" and having seen others with similar issues for even barebones python apps it seems like a good fit as you mentioned for an "extras" module people could use/enable if desired. I'm totally cool with however you wanted to do it that fits logically into things. I provided the code for reference but if you need any help or further details to implement feel free to let me know and I'll see what I can do as time permits :)

Thanks again for your time and consideration.
    if($role == "Learner"){
    
    $privilegios = "Estudiante";
    
    } else {
        $privilegios = "Docente";
       }
    

    // The password_hash() function convert the password in a hash before send it to the database
    $passHash = password_hash($pass, PASSWORD_DEFAULT);

    // Query to send Name, Email and Password hash to the database
        $query = "INSERT INTO users (Nombre, Apellido, Correo, Contrasena, Privilegios, IP) VALUES ('$name', '$apellido', '$email', '$passHash', '$privilegios', '$IP')";

    if (mysqli_query($conn, $query)) {

        $email = $_POST["lis_person_contact_email_primary"];
        $checkEmail = "SELECT * FROM users WHERE Correo = '$email' ";
        // Se obtiene los correo que conciden
        $result = $conn-> query($checkEmail);
        $row = mysqli_fetch_assoc($result);
                $_SESSION['id'] = $row["id_user_O"];
        $_SESSION['loggedin'] = true;
        $_SESSION['Nombre'] = $row['Nombre'];
        $_SESSION['start'] = time();
        $_SESSION['expire'] = $_SESSION['start'] + (1 * 60);
        $_SESSION['Apellido'] = $row['Apellido'];
        $_SESSION['Privilegios'] = $row['Privilegios'];
        $_SESSION['Correo'] = $row['Correo'];
        $_SESSION["IP"] = $row['IP'];
        $_SESSION["Foto"] = $row['Foto'];
        $_SESSION["Tiempo1"] = $row['Tiempo1'];
        $_SESSION["Tiempo2"] = $row['Tiempo2'];

        $ID_USER = $_SESSION['id'];

        mysqli_close($conn);
        header('Location: index.php');
        

    } else {
            //header("location:index.php?$newUserLink");


        }
}
mysqli_close($conn);

}
