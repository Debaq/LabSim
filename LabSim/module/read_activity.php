<?php

session_start();

include_once 'conn.php';




$p = $_POST["p"];


$sql_act = "SELECT * FROM Activity WHERE pass_client = '$p'";


$resultsE = $conn->query($sql_act);
$rows = array();
while ($r = $resultsE->fetch_assoc()){
    $rows[] = $r;
}

$data = $rows[0];



$title = $data["title"];
$number_users = $data["number_users"];
$signatures = $data["signatures"];
$time = $data["time"];
$SuperUser =  $data["SuperUser"];
$team = $data["team"];
$icon = $data["icon"];
$url = $data["url"];
$pass_client =$data["pass_client"];
$time_stamp = $data["time_stamp"];

$state = $data["state"];
$goals = $data["goals"];
$description = $data["description"];

$file = [
    ["ADSVCR" , "archivo1.pdf", "far fa-fw fa-file-pdf"],
    ["AHGDSV" , "archivo2.pdf", "far fa-fw fa-file-pdf"],
    ["ASDDR" , "archivo3.pdf", "far fa-fw fa-file-pdf"]
];

$modules = json_decode(base64_decode($data["modules"]));


$data = [
    'title' => $title,
    'number_users' => $number_users,
    'signatures' => $signatures,
    'description'=> $description,

    'time' => $time,
    'state' => $state,
    'goals'=> $goals,

    'SuperUser' => $SuperUser,
    'team' => $team,
    'file' => $file,
    'icon' => $icon,
    'url' => $url,

    'modules' => $modules,
    'pass_client' => $pass_client,
    'time_stamp' => $time_stamp

];

echo json_encode($data);