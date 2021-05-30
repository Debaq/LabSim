<?php
session_start();
//IP Client
$IP = $_SERVER['REMOTE_ADDR'];

// Connection info. file
include 'conn.php';

// Connection variables
$conn = new mysqli($dbhost, $dbuser, $dbpass, $dbname);

// Check connection
if (!$conn) {
    die("Connection: " . mysqli_connect_error());
}
// NO afectará a $mysqli->real_escape_string();
$conn->query("SET NAMES utf8");
// data sent from form login.html
$Correo = $_POST['Correo'];
$password = $_POST['Contrasena'];

// Query sent to dsatabase
$result = mysqli_query($conn, "SELECT *  FROM users WHERE Correo = '$Correo'");
// Variable $row hold the result of the query
$row = mysqli_fetch_assoc($result);

// Variable $hash hold the password hash on database
$hash = $row['Contrasena'];

//Verificar IP
echo $row['IP'];
echo $IP;

#if($row['IP']== NULL){
 #   $IP_CHECK = true;
 #   echo "hola loli";

#}else{
#    if($row['IP']==$IP){
 #       $IP_CHECK = true;
 #   }else{$IP_CHECK = false;}

#}
$IP_CHECK = true;
echo $IP_CHECK;


/*
password_Verify() function verify if the password entered by the user
match the password hash on the database. If everything is OK the session
is created for one minute. Change 1 on $_SESSION[start] to 5 for a 5 minutes session.
*/
if (password_verify($_POST['Contrasena'], $hash)) {
    if($IP_CHECK == true) {
        echo "entramos";
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

    }else{	mysqli_close($conn);
        echo "??";
        header( 'Location: login.php');
    }
} else {	mysqli_close($conn);
    echo "error";
    header('Location: login.php');
    }

