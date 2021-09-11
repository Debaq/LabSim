<?php
$request = $_POST["request"];
include 'global_function.php';


if($request == "login"){
    $user = $_POST["user"];
    $pass = $_POST["password"];

    $request_user = mysqli_query($conn, "SELECT hashPSW FROM Users WHERE Users='$user'");
    $row_rUser = mysqli_fetch_assoc($request_user);
    $hash = $row_rUser['hashPSW'];
    if(password_verify ( $pass, $hash)){
        update_sql(1,"", "login", "Users", $user, $conn);
        echo "ok";

    }else{echo "error";
    }

}

if($request == "state"){
    $name = $_POST["user"];
    $from = "Users";
    $single = "pred_case";
    $case = request_data($name, $conn, $from, $single);

    if($case != "0"){
        $case = json_decode($case, true);
        $code = $case['patient'];
        $instrument = $case['sector'];

        $from = "Patients";
        $single = "Audiology";
        $Scode64 = request_datav2($code, $conn, $from, $single);
        $result = json_decode(base64_decode($Scode64), true);
        $result['sector'] =  $instrument;
        echo json_encode($result, JSON_UNESCAPED_UNICODE);

    }else{
        echo $case;
    }
}

if($request == "logout"){
    $user = $_POST["user"];
    $pass = $_POST["password"];

    $request_user = mysqli_query($conn, "SELECT hashPSW FROM Users WHERE Users='$user'");
    $row_rUser = mysqli_fetch_assoc($request_user);
    $hash = $row_rUser['hashPSW'];
    if(password_verify ( $pass, $hash)){
        update_sql(0,"", "login", "Users", $user, $conn);
        echo "saliendo";

    }else{echo "error";
    }

}

if($request == "state_login"){
    $name = $_POST["user"];
    $from = "Users";
    $single = "login";
    $login = request_data($name, $conn, $from, $single);
        echo $login;

}