/* Destroy current user session */

<?php
session_start();

// Connection info. file
include 'conn.php';

// Connection variables
$conn = mysqli_connect($dbhost, $dbuser, $dbpass, $dbname);

// Check connection
if (!$conn) {
    die("Connection failed: " . mysqli_connect_error());
}
$ID_USER = $_SESSION['id'];
$IP_UPDATE = mysqli_query($conn, "UPDATE users SET IP='' WHERE id='$ID_USER'");
mysqli_close($conn);

session_unset($_SESSION['email']);
session_unset($_SESSION['id']);
session_unset($_SESSION['loggedin']);
session_unset($_SESSION['name']);
session_unset($_SESSION['start']);
session_unset($_SESSION['expire']);
session_unset($_SESSION['apellido']);
session_unset($_SESSION['privilegios']);
session_unset($_SESSION['mencion']);
session_unset($_SESSION['email']);
session_unset($_SESSION['Sorteo']);
session_unset($_SESSION["IP"]);
session_destroy();
header('location: login.php');
?>