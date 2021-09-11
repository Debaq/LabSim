<?php
include_once 'global_function.php';
session_start();

$credential  = $_SESSION['credentials'];


if($credential == "Instructor"){
    $_SESSION['credentials'] = 'Learner_V';
    $_SESSION['credentials_simulate'] = 'Instructor';
}else{
    $_SESSION['credentials'] = 'Instructor';
    $_SESSION['credentials_simulate'] = 'Learner_V';
}
  
BACK_INDEX();