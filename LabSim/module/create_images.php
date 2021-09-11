<?php



$profile_f5 = "nina_5.jpeg";
$Oto_OD_B = "Oto_OD_B.jpg";
$Oto_OI_B = "Oto_OI_B.jpg";
$Rinne_n = "";
$Weber_bi ="";
$Z_B_OI = "B_1.png";
$Z_B_OD = "B_2.png";
$reflex_n_OI = "left_neg.jpg";
$reflex_n_OD = "rigth_neg.jpg";




$profile_m50 = "hombre_50.jpeg";
$OTO_OD_N2 = "OTO_OD_N2.png";
$OTO_OI_N2 = "OTO_OI_N2.png";


$profile_m14 = "nino_14.jpeg";

$Z_A_OD = "A_2.png";
$Z_A_OI = "A_1.png";


$OTO_OD_N = "OTO_OD_N.PNG";
$OTO_OI_N = "OTO_OI_N.PNG";



$profile = $profile_m14;
$OTO_OD = $OTO_OD_N;
$OTO_OI = $OTO_OI_N;
$Rinne_OD = $Rinne_n;
$Rinne_OI = $Rinne_n;
$Weber = $Weber_bi;
$Z_OD = $Z_A_OD;
$Z_OI = $Z_A_OI;
$reflex_OD = $reflex_n_OD;
$reflex_OI = $reflex_n_OI;



$result =[
    "Profile" => $profile,
    "OTO_OD" => $OTO_OD,
    "OTO_OI" => $OTO_OI,
    "Rinne_OD" => $Rinne_OD ,
    "Rinne_OI" => $Rinne_OI,
    "Weber" =>$Weber,
    "Z_OD" => $Z_OD,
    "Z_OI" => $Z_OI,
    "Reflex_OD" => $reflex_OD,
    "Reflex_OI" => $reflex_OI
];


$result = base64_encode(json_encode($result));

print $result;
