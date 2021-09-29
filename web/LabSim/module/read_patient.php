
<?php
session_start();
include_once('global_function.php');

$user =$_SESSION["user"];
$request = $_POST["p"];

$box_name = "Box_1";

$box = array(
    'patient' => $_POST["p"],
    'sector' => "none",
    'box' => $box_name
);
$box = json_encode($box);

update_sql($box, "Users", "pred_case", "Users", $user, $conn);


function SQL_PAT($id, $conn){

$sql_act = "SELECT * FROM Patients WHERE Code = '$id'";
#$sql_act = "SELECT * FROM Patients";

$resultsE = $conn->query($sql_act);
$rows = array();
while ($r = $resultsE->fetch_assoc()){
    $rows[] = $r;
}
$result = $rows;
return $result[0];
}

$data = SQL_PAT($request, $conn);

$name = json_decode(base64_decode($data["Name"]), true);
$gender = ($data['Gender']==1) ? "Masculino" : "Femenino";

$img = json_decode(base64_decode($data["Image_audiology"]), true);

$profile = $img["Profile"];
$OTO_OD = $img["OTO_OD"];
$OTO_OI = $img["OTO_OI"];
$Z_OI = $img["Z_OD"];
$Z_OD = $img["Z_OI"];
$reflex_OD = $img["Reflex_OD"];
$reflex_OI = $img["Reflex_OI"];


$result = [
    "Name" => $name["first_name"].' '.$name["second_name"].' '.$name["first_lastname"].' '.$name["second_lastname"],
    "Age" => $data["Age"],
    "Gender" => $gender,
    "Morbid" => json_decode(base64_decode($data["Morbid"])),
    "Anamnesis" => json_decode(base64_decode($data["Anamnesis"]))[0],
    "Profile" => $profile,
    "Box" => $box_name,
    "OTO_OD" => $OTO_OD,
    "OTO_OI" => $OTO_OI,
    "Z_OD" => $Z_OI,
    "Z_OI" => $Z_OD,
    "Reflex_OD" => $reflex_OD,
    "Reflex_OI" => $reflex_OI,
    "User" => $_SESSION["user"],
    "Patient" => $request,
];


echo json_encode($result);
