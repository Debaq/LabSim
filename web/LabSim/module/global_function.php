<?php

include 'conn.php';



function check($code, $conn, $from, $where = 'Code'){
    $consult =  "SELECT COUNT(*) FROM $from WHERE $where = '$code'";
    $result = mysqli_query($conn, $consult);
    $row = mysqli_fetch_assoc($result);
    $exist = ($row['COUNT(*)'] == 0)? false : true;
    return $exist;
}



function request_data($name, $conn, $from, $single = false){
    $consult =  "SELECT * FROM $from WHERE Users = '$name'";
    $request = mysqli_query($conn, $consult);
    $row = mysqli_fetch_assoc($request);
    if($single != false){
        $result = $row[$single];
    }else{
        $result = $row;
    }
    return $result;
}


function request_datav2($code, $conn, $from, $single = false){
    $consult =  "SELECT * FROM $from WHERE Code = '$code'";
    $request = mysqli_query($conn, $consult);
    $row = mysqli_fetch_assoc($request);
    if($single != false){
        $result = $row[$single];
    }else{
        $result = $row;
    }
    return $result;
}

function generateRandomString($n, $from, $code, $conn) {
    $result = generate($n);
    $result = $code.'-'.$result;
    while(check($result, $conn, $from)){
            $result = generate($n);
        }
    
    return $result;
}

function insert_sql($array, $from, $conn){
    $sth = ("INSERT INTO $from ( " . implode(', ',array_keys($array)) . ") VALUES ('" . implode("', '" ,array_values($array)) . "')");
    #echo $sth;
    if (!mysqli_query($conn, $sth)) {die("Connection failed: " . mysqli_connect_error());}
}

function update_sql($data, $from, $column, $where, $search, $conn){
    $sth = "UPDATE `Users` SET `$column`='$data' WHERE `$where`='$search'";
    if (!mysqli_query($conn, $sth)) {die("Connection failed: " . mysqli_connect_error());}
    return $sth;
}

function load_json($file, $raw=false) {
    $file_json = ROOT . "/config/" . $file;
    if (file_exists($file_json)){
        $data_json = file_get_contents($file_json);
        if($raw == false){
            $result = json_decode($data_json,true);
        }else{
            $result = $data_json;
        }
        return $result;
    }else{echo "error no haz creado bien los archivos";}    
}


function REDIRECT($page_idx){
    $host  = $_SERVER['HTTP_HOST'];
    $uri   = rtrim(dirname($_SERVER['PHP_SELF']), '/\\');
    $uri = trim($uri, 'module');
    $result = ("Location: http://$host$uri?p=$page_idx");
    return $result;
}

function BACK_INDEX(){
    header(REDIRECT('index'));
    exit;    
}

function GO_ACTIVITY(){
    header(REDIRECT('cfg_activity'));
    exit; 
}

function generate($length = 10){
    $characters = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    $charactersLength = strlen($characters);
    $randomString = '';
    for ($i = 0; $i < $length; $i++) {
        $randomString .= $characters[rand(0, $charactersLength - 1)];
    }
    return $randomString;
}