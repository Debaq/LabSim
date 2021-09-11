<?php
session_start();
include_once("global_function.php");

$code = generateRandomString(6, "Attention", "AT", $conn);
$user = $_SESSION['user'];
$patient = $_POST['patient'];
$data = base64_encode($_POST["anam_reason"]);
$files ="";

$data_insert = [
    "code" => $code,
    "User" => $user,
    "Patient" => $patient,
    "Data" => $data,
    "Files" => $files
];


insert_sql($data_insert, "Attention", $conn);

BACK_INDEX();