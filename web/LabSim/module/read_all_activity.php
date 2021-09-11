<?php
session_start();
$user = $_SESSION['user'];
include_once('conn.php');

$sql_act = "SELECT * FROM Activity WHERE SuperUser = '$user'";

$resultsE = $conn->query($sql_act);
$rows = array();
while ($r = $resultsE->fetch_assoc()){
    $rows[] = $r;
}
$data = $rows;


$sql_act_user = "SELECT activity FROM Users";

$resultsF = $conn->query($sql_act_user);
$rows_II = array();
while ($r = $resultsF->fetch_assoc()){
    $rows_II[] = $r;
}
$data_II = array($rows_II);

#{"act":["eeee","Js-Br0H"]}

$S = "eee";
$count = 0;

foreach($data_II[0] as $dt){    
    $r = json_decode($dt['activity'], true);
    if(in_array($S, $r['act'])){
        $count +=1;
    }    
}
$str_final = "";
foreach($data as $dat){
    $dat["users"] = $count;
    $modules=json_decode(base64_decode($dat["modules"]));
    $modules_list = [];
    foreach($modules as $m){
        array_push($modules_list,$m[2]);
    }
    $dat["modules"] = $modules_list;
    $JSON_dat = json_encode($dat);
    $str_final .= $JSON_dat . ',';

}
$str_final = rtrim($str_final, ",");
$result = '{ "data" : [' . $str_final . ']}';

echo $result;
#echo "</br>";
#print_r(base64_decode($data[0][1]["modules"]));