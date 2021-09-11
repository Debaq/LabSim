<?php
include_once('conn.php');

$list_pat = ["Pt-n8hr"];

$data = [];

function SQL_PAT($id, $conn){


    $sql_act = "SELECT * FROM Schedule";

    $resultsE = $conn->query($sql_act);
    $rows = array();
    while ($r = $resultsE->fetch_assoc()){
        $rows[] = $r;
    }
    $result = $rows;
    return $result;
}

foreach($list_pat as $n){
    array_push($data, SQL_PAT($n, $conn));
}

function now_timestamp(){
    $now = date("Y-m-d H:i:s");
    $fecha = date_create($now);
    return date_timestamp_get($fecha);
}

function new_timestam($Y, $m, $d, $H, $i){
    $now = date($Y.'-'.$m.'-'.$d.' '.$H.':'.$i.':0');
    $fecha = date_create($now);
    return date_timestamp_get($fecha);
}


function name_pat($code, $conn){
    $sql_act = "SELECT Name FROM Patients WHERE Code = '$code'";
    $resultsE = $conn->query($sql_act);
    $rows = array();
    $r = $resultsE->fetch_assoc();
   
    $request = json_decode(base64_decode($r["Name"]),true);
    $result = $request["first_name"]." ".$request["second_name"]." ".$request["first_lastname"]." ".$request["second_lastname"];
    return $result;
}


$Now = now_timestamp();
#$Now = 1626869200;


$str_final = "";
foreach($data as $dat){

    foreach($dat as $f){
        $f["Name"] = name_pat($f["Patient"], $conn);
        $memory_date = $f['Date'];

        $f["Date"] = date('m/d/Y', $memory_date);
        $f["Time"] = date('H:i', $memory_date);
       

        if($memory_date < $Now){
            $f["Active"] = "";
            $f["State"] = "Llamar al Box";
        }else{
            $f["Active"] = "disabled";
            $f["State"] = "Aún no llega";
        }


        $JSON_dat = json_encode($f);
        $str_final .= $JSON_dat . ',';
    }

}
$str_final = rtrim($str_final, ",");
$result = '{ "data" : [' . $str_final . ']}';
#$result = '{ "data" : [{"id":"2","Code":"Ll-jdh687","Date":"07\/21\/2021","Patient":"Pt-n8hr","Activity":"Js-xX6K","Attention":"Audiometr\u00eda Infantil","Name":"Agustina Catalina Aguirre Sanhueza","Time":"10:00","Active":"","State":"Llamar al Box"},{"id":"3","Code":"Ll-jdhs87","Date":"07\/21\/2021","Patient":"Pt-R2fX","Activity":"Js-xX6K","Attention":"Audiometr\u00eda Adulto","Name":"Mateo Maximiliano SanMartin SanMartin","Time":"10:45","Active":"","State":"Llamar al Box"},{"id":"4","Code":"Ll-jdhs90","Date":"07\/21\/2021","Patient":"Pt-KkIG","Activity":"Js-xX6K","Attention":"Audiometr\u00eda Infantil","Name":"Alonso Maximiliano Carcamo Calderon","Time":"11:30","Active":"","State":"Llamar al Box"}]}';
echo $result;