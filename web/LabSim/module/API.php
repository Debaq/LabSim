<?php
$request = $_POST["request"];

function request_data($data){
    include 'conn.php';

    

    // Verificación de conexión exitosa
    if (!$conn) {
        die("Connection: " . mysqli_connect_error());
    }
    $request = mysqli_query($conn, "SELECT * FROM Program WHERE P='$data'");
    $row = mysqli_fetch_assoc($request);
    return $row;
}


function request_case($user){
    include 'conn.php';
    

    
    $request = mysqli_query($conn, "SELECT * FROM Users WHERE Users='$user'");
    $row = mysqli_fetch_assoc($request);
    return $row;
}


function request_datacase($patient){
    include 'conn.php';
   

   

    $request = mysqli_query($conn, "SELECT * FROM Patients WHERE Users='$patient'");
    $row = mysqli_fetch_assoc($request);
    return $row;
}

function read_line_end($file){
//    echo "read_last";
    $log_file_data = $file;
    $line = '';
    $f = fopen($log_file_data, 'r');
    $cursor = -1;
    fseek($f, $cursor, SEEK_END);
    $char = fgetc($f);
    //Trim trailing newline characters in the file
    while ($char === "\n" || $char === "\r") {
        fseek($f, $cursor--, SEEK_END);
        $char = fgetc($f);
    }
    //Read until the next line of the file begins or the first newline char
    while ($char !== false && $char !== "\n" && $char !== "\r") {
        //Prepend the new character
        $line = $char . $line;
        fseek($f, $cursor--, SEEK_END);
        $char = fgetc($f);
    }
    #echo "last ::: ". $line . ":::";
    return $line;
}

function wh_log($log_file, $log_msg) {
    $log_file_data = $log_file;

    //$log_msg_clean = substr_replace($log_msg ,"",-1);
    //$log_msg_clean = substr($log_msg_clean, 1);
    //$log_msg_clean = substr_replace($log_msg ,"",0);

    file_put_contents($log_file_data, $log_msg . "\n", FILE_APPEND);
}


function tiempo(){
    //$t_raw = getdate();
    //$t_assoc = localtime(time(), true);
    //$t_format = $t_raw['mday']."-".$t_raw['mon']."-".$t_raw['year']." ".$t_raw['hours'].":".$t_raw['minutes'].":".$t_raw['seconds'];
    
    $t = microtime(true);
    $micro = sprintf("%06d",($t - floor($t)) * 1000000);
    $d = new DateTime( date('Y-m-d H:i:s.'.$micro, $t) );
    $t_format = $d->format("Y-m-d H:i:s.u"); 
    return $t_format;
}


function init_new_session($log_file){
    $log_filename = $_SERVER['DOCUMENT_ROOT']."/LabSim/AudioSim/log";
    $log_file_data = $log_filename.'/' . $log_file . '.log';

    if (!file_exists($log_file_data)){
        $file = fopen($log_file_data, 'w') ;
        fclose($file);
        $count = 0; 
    }else{
        $line = read_line_end($log_file_data);
        $lineJSON = json_decode($line, true);
        $close = $lineJSON["close"];
        $count = $lineJSON["session"]+1;       
    }
    $data = [
        'timestamp' => tiempo(),
        'session' => $count,
        'close' => false
    ];
    $dataJSON = json_encode($data);
    wh_log($log_file_data, $dataJSON);
}

function close_session($log_file){
    $log_filename = $_SERVER['DOCUMENT_ROOT']."/AudioSim/log";
    $log_file_data = $log_filename.'/' . $log_file . '.log';
    $line = read_line_end($log_file_data);
    $lineJSON = json_decode($line, true);
    $count = $lineJSON["session"];
    $data = [
        'timestamp' => tiempo(),
        'session' => $count,
        'close' => true
    ];
   
    $dataJSON = json_encode($data);
    wh_log($log_file_data, $dataJSON);

}

if($request == "close_session"){
    $log_file = $_POST["user"];
    close_session($log_file);
}

if($request == "load_case"){
    $case_row = request_case($_POST["user"]);
    $case = $case_row["pred_case"];
    $data_case = request_datacase($case);

    $JSON_data = (base64_decode($data_case["Audiology"]));

    echo $JSON_data;
    #$file = $_SERVER['DOCUMENT_ROOT']."/LabSim/AudioSim/casos/caso".$case.".json";
    #$string = file_get_contents($file);
    #$json_a = json_decode($string, true);
    #$newJsonString = json_encode($json_a);
    #echo $newJsonString;
}

if($request == "write_data"){
    $log_filename = $_SERVER['DOCUMENT_ROOT']."/AudioSim/log";
    $log_file = $_POST["user"];
    $log_file_data = $log_filename.'/' . $log_file . '.log';

    if (!file_exists($log_file_data))
    {
        $file = fopen($log_file_data, 'w') ;
        fclose($file); 
    }

    $jsonString = read_line_end($log_file_data);
    if($jsonString==""){
        $jsonString = "{}";
    }

    $tiempo = tiempo();

    $new_data = json_decode($_POST["data"], true);
    $old_data = json_decode($jsonString, true);

    $keys = (array_keys($new_data));
    foreach($keys as $key){
        $old_data[$key] = $new_data[$key];
    }

    $old_data['timestamp'] = $tiempo;

    $newJsonString = json_encode($old_data);

    echo $newJsonString;

    #file_put_contents($file_name, $newJsonString);
    wh_log($log_file_data, $newJsonString);
    //echo json_encode($new_data);

}

if($request == "read_data"){
    $log_filename = $_SERVER['DOCUMENT_ROOT']."/AudioSim/log";
    $log_file = $_POST["user"];
    $log_file_data = $log_filename.'/' . $log_file . '.log';


    //$code_file = $_POST["code"];
    //$file_name = $code_file.".json";
    
    //$jsonString = file_get_contents($file_name);
    $jsonString = read_line_end($log_file_data); 
    if($jsonString == ''){
        echo "{}";
    }else{
        echo $jsonString;
    }
    //$data = json_decode($jsonString, true);

}




if($request == "login"){

    include 'conn.php';

 

    $user = $_POST["user"];
    $pass = $_POST["password"];
    $code = $_POST["code"];
    
    
    if($user == 'code3216'){
        /// sin implemantar
        echo json_encode($_POST);
        #echo "Hola";

    }else{

        $request_user = mysqli_query($conn, "SELECT hashPSW FROM Users WHERE Users='$user'");
        $row_rUser = mysqli_fetch_assoc($request_user);
        $hash = $row_rUser['hashPSW'];
        
        if(password_verify ( $pass, $hash)){
            $request = mysqli_query($conn, "SELECT * FROM Users WHERE Users='$user'");
            $rows = mysqli_fetch_assoc($request);
            //$UserName = $rows["UserName"];
            //$Active = $rows["Active"];
            $P = "AudioSim";
        
            $request1 = mysqli_query($conn, "SELECT VersionNow, CodeName FROM Program WHERE P ='$P'");
            $rows1 = mysqli_fetch_assoc($request1);
            //$VersionNow = $rows1["VersionNow"];
            //$CodeName = $rows1["CodeName"];
            unset($rows["hashPSW"]);
            $result = array_merge($rows , $rows1);
            init_new_session($user);
            echo json_encode($result);

            //echo '200'.",".$UserName.",".$Active.",".$CodeName.",".$VersionNow;

        }else{echo '{"E" :"062"}';}
    }
}
