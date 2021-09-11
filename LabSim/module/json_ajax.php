<?php

$uri   = rtrim(__DIR__, '/\\');
$uri = trim($uri, 'module');
$result = ("$uri");
define('ROOT' , $result);

include_once('global_function.php');

$select = $_POST['select'];
$list = $_POST['list'].'.json';


function json_ajax($file, $select, $json = false){


    $request = load_json($file);

    if($select == "all"){
        $result = $request;
    }else{
        $result = $request[$select];
    }

    $result = ($json ? json_encode($result) : $result);

    return $result;
}


echo json_ajax($list, $select, true);


