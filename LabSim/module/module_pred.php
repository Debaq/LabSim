<?php


$uri   = rtrim(__DIR__, '/\\');
$uri = trim($uri, 'module');
$result = ("$uri");
define('ROOT' , $result);


$test = isset($_POST['data']);
if( $test){
    include 'global_function.php';
    $json_module_pred = load_json("module_pred.json");
    $modules_basic = [];
    foreach($json_module_pred["modules"] as $jmodule){
        $code = $jmodule[0];
        $name = $jmodule[2];
        $description = $jmodule[3];
        $result_prev = [
            "code" => $code,
            "name" => $name,
            "description" => $description
        ];
        array_push($modules_basic,$result_prev);
    }
    echo json_encode($modules_basic, JSON_FORCE_OBJECT);
}