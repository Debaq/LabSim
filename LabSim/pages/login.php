<?php
// Required field names
$required = array(
    'lis_person_contact_email_primary', 
    'lis_person_name_full', 
    'roles',
    'custom_actividad',
    'ext_user_username'
);

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
include_once('global_function.php');

// Revisa si el correo existe
$email = $_POST["lis_person_contact_email_primary"];
$count = check($email, $conn, 'Users', 'Email');


// si count == 1 significa que la cuenta ya existe, por tanto da aviso de ello
if ($count == "1") {
        $name =  $_POST['ext_user_username'];
        $_SESSION['Username'] = request_data($name, $conn, 'Users' );
        $_SESSION['user'] = $_POST['ext_user_username'];
        $_SESSION['credentials'] = $_POST['roles'];
        $_SESSION['login'] = true;
        header('Location: ../index.php');
    }
else {

}
mysqli_close($conn);

}
