<?php

    session_start();

    $iccurso = $_GET["iccurso"];
    $time = $_GET["time"]; 
    $name = $_GET["name"];
    $email = $_GET["email"];
    $url = $_GET["url"];
    $id = $_GET["id"];
    $name_all = $_GET["name_all"];
    $cmid = $_GET["cmid"];
 
    ini_set( 'display_errors', 1 );
    error_reporting( E_ALL );
    $from = "tmeduca@tmeduca.cl";
    $to = $email;
    $subject = "dirigete a esta cuenta para validar";
    $message = "PHP mail works just fine";
    $headers = "From:" . $from;
    mail($to,$subject,$message, $headers);
    echo "The email message was sent.";
