<?php


include 'global_function.php';

$uri   = rtrim(__DIR__, '/\\');
$uri = trim($uri, 'module');
$result = ("$uri");
define('ROOT' , $result);



$first_name = names_rand($_POST["gender"]);
$second_name = names_rand($_POST["gender"]);
    while($second_name == $first_name){
        $second_name = names_rand($_POST["gender"]);
    }
$first_lastname  = names_rand(2);
$second_lastname  = names_rand(2);

function names_rand($pos){
    $file = ["name_f.csv", "name_m.csv", "lastname.csv"];
 

    $file= ROOT . "/config/".$file[$pos];
    $linecount = 0;
    $handle = fopen($file, "r");
    while(!feof($handle)){
      $line = fgets($handle);
      $linecount++;
    }
    fclose($handle);
    $select_line = rand(0, $linecount);
    $lines = file($file); 
    $result_1 = str_replace(',', '', $lines[$select_line-1]);
    $result = preg_replace("/\s+/", "", $result_1);

    return $result;
}


function separe_ids($array, $string, $base64 =true){
    $result = [];
    foreach($_POST as $k => $v){
        if(strpos($k, $string) === 0){
            $cut = explode('_', $k);
            if($cut[1] == "other" or $cut[1] == "reason"){
                array_push($result,$v);

            }else{
                array_push($result,$k);

            }
        }
    }
    if($base64){
        $result = base64_encode(json_encode($result));

    }else{
        $result = json_encode($result);
    }
    return $result;
}

$full_name = [
    "first_name" => $first_name,
    "second_name"=> $second_name,
    "first_lastname" => $first_lastname,
    "second_lastname" => $second_lastname
];

$full_name = base64_encode(json_encode($full_name));

$age = $_POST["age"];
$gender = $_POST["gender"];
$morbid = separe_ids($_POST, "morbid_");
$anamesis = separe_ids($_POST, "anam_");
$audio_pre = $_POST["audio_audio"];
$audio = base64_encode($audio_pre);


$result = [
    'Code' => generateRandomString(4, "Patients", "Pt", $conn),
    'Name' => $full_name,
    'Age' => $age,
    'Gender' => $gender,
    'Morbid' => $morbid,
    'Anamnesis' => $anamesis,
    'Audiology' => $audio
];

insert_sql($result, "Patients", $conn);



