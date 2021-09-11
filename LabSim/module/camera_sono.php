<?php
include_once('global_function.php');

$user = $_POST["u"];

$state = $_POST["a"];


if($state == 0){
    $result = 0;
}else{
    $result = array(
        'patient' => $_POST["p"],
        'sector' => $_POST["pl"]
    );
    $result = json_encode($result);
    
}

echo update_sql($result, "Users", "pred_case", "Users", $user, $conn);