<?php

include_once('global_function.php');
$user = $_POST["u"];
$state = $_POST["a"];


if($state == 0){

    $result = array(
        'patient' => $_POST["p"],
        'sector' => "none",
        'box' => $_POST["b"]
    );
    $result = json_encode($result);

}else{
    $result = array(
        'patient' => $_POST["p"],
        'sector' => $_POST["pl"],
        'box' => $_POST["b"]
    );
    $result = json_encode($result);
    
}

update_sql($result, "Users", "pred_case", "Users", $user, $conn);