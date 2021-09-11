<?php
session_start();


include 'global_function.php';
include 'conn.php';

$uri   = rtrim(__DIR__, '/\\');
$uri = trim($uri, 'module');
$result = ("$uri");
define('ROOT' , $result);


function check_priv($code, $conn){
    $conn->query("SET NAMES utf8");
    $result = mysqli_query($conn, "SELECT COUNT(*) FROM Activity WHERE pass_shared = '$code'");
    $row = mysqli_fetch_assoc($result);
    $exist = ($row['COUNT(*)'] == 0)? false : true;
    return $exist;
}

function generateRandomString_priv($pass, $conn) {
    if($pass == "client"){
        $result = generate(4);
        $result = 'Js-'.$result;
    }else{
        $result = generate(10);
    }
    if($pass == 'client'){
        while(check_priv($result, $conn)){
            $result = generate(6);
        }
    }
    return $result;
}


function generateRandomString_cod($cod) {
    $result = generate(6);
    $result = $cod."-".$result;
    return $result;
}

function insert_activity($array, $conn){

    $sth = ("INSERT INTO Activity ( " . implode(', ',array_keys($array)) . ") VALUES (" . implode(', ',array_values($array)) . ")");
    echo $sth;
    if (!mysqli_query($conn, $sth)) {die("Connection failed: " . mysqli_connect_error());}
}


function module_pred($list_module){

    $json_module_pred = load_json("module_pred.json");

    $modules_basic = [];
    foreach($json_module_pred["modules"] as $jmodule){
        $code = $jmodule[0];
       
        if(in_array($code,$list_module)){
            $jmodule[0] = generateRandomString_cod($code);
            array_push($modules_basic,$jmodule);
        }
    }

    return $modules_basic;

}

$list_module =  [];

foreach($_POST as $k => $h){
    if($h == "on"){
        array_push($list_module, $k);
    }
}

$modules = base64_encode(json_encode(module_pred($list_module)));

$fecha = date_create();
$time_now = date_timestamp_get($fecha);

$insData = array(
    'title' => '"'.$_POST['inputName'].'"',
    'number_users' => '"0"',
    'signatures' => '"'.$_POST['inputsignature'].'"',
    'description' => '"'.$_POST['inputDescription'].'"',
    'time' => '"'.$_POST['inputTimeTotal'].'"',
    'state' => '"'.$_POST['inputStatus'].'"',
    'goals' => '"'.$_POST['inputGoals'].'"',
    'SuperUser' => '"'.$_SESSION['user'].'"',
    'team' => '"0"',
    'file'=> '"0"',
    'icon' => '"'.'https://tmeduca.cl/AudioSim/lib/icon.svg'.'"',
    'url' => '"'.'https://tmeduca.cl/AudioSim/'.'"',
    'modules' =>'"'.$modules.'"',
    'pass_shared' => '"'.generateRandomString_priv("shared", $conn).'"',
    'pass_client' => '"'.generateRandomString_priv("client", $conn).'"',
    'time_stamp' => '"'.$time_now.'"'
);


insert_activity($insData, $conn);



GO_ACTIVITY();
