<?php
// Connection variables
$dbhost	= "localhost";	   // localhost or IP
$dbuser	= "tmeducac_labsim_user";		  // database username
$dbpass	= "5XXrx2G5XlI3kTf*";		     // database password
$dbname	= "tmeducac_LabSim";    // database name
$conn = new mysqli($dbhost, $dbuser, $dbpass, $dbname);
if (!$conn) {die("Connection failed: " . mysqli_connect_error());}

mysqli_set_charset($conn, "utf8");
?>