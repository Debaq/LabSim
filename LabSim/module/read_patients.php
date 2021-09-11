<?php

include_once('conn.php');
$conn = new mysqli($dbhost, $dbuser, $dbpass, $dbname);

$list_pat = ["Pt-n8hr"];

$data = [];

function SQL_PAT($id, $conn){

    #$sql_act = "SELECT * FROM Patients WHERE Code = '$id'";
    $sql_act = "SELECT * FROM Patients";

    $resultsE = $conn->query($sql_act);
    $rows = array();
    while ($r = $resultsE->fetch_assoc()){
        $rows[] = $r;
    }
    $result = array($rows);
    return $result[0];
}

foreach($list_pat as $n){
    array_push($data, SQL_PAT($n, $conn));
}



$str_final = "";
foreach($data as $dat){

    foreach($dat as $f){
        if($f["Audiology"]== null){
            $f["Audiology"] = "0";
        }else{
            #$a = json_decode($f["Audiology"],true);
            $f["Audiology"] = "0";
        }
        if($f["Gender"]==0){
            $f["Gender"] = "femenino";
        }else{
            $f["Gender"] = "masculino";
        }
        $f["Otoneuro"] = "0";
        $f["Electro"] = "0";

        $name_64 = $f["Name"];
        $name_json = base64_decode($name_64);     
        $name_array = json_decode($name_json, true);      
        $nombre = $name_array["first_name"]." ".$name_array["second_name"]." ".$name_array["first_lastname"]." ".$name_array["second_lastname"];

        $morbid_64 = $f["Morbid"];
        $morbid_json = base64_decode($morbid_64);
        $morbid_array = json_decode($morbid_json, true);
        $f["Morbid"]= $morbid_array;

        $Anamnesis_64 = $f["Anamnesis"];
        $Anamnesis_json = base64_decode($Anamnesis_64);
        $Anamnesis_array = json_decode($Anamnesis_json, true);
        $f["Anamnesis"]= $Anamnesis_array;


        $f["Name"] = $nombre;
        $JSON_dat = json_encode($f);
        $str_final .= $JSON_dat . ',';
    }

}
$str_final = rtrim($str_final, ",");
$result = '{ "data" : [' . $str_final . ']}';
echo $result;