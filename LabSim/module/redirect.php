<?php

function page_action($p,$a,$c){
    $_SESSION["page_prev"] = $_SESSION["page_actual"];
    $_SESSION["page_actual"] = $p;
    $pages = load_json('pages.json')['pages'];
    if(array_key_exists($p, $pages)){
        if(authorize($c,$pages[$p][1])){
            if (false !== ($data = file_get_contents(TEMPLATES . $pages[$p][0]))) {
                $result = $data;
            }else{
                $result = file_get_contents(TEMPLATES . $pages['503'][0]);
            }
        }else{
            $result = file_get_contents(TEMPLATES . $pages['401'][0]);
        }
    }else{
        $type = load_json('pages.json')['Type'];
        $rest = substr($p,0,2);
        $rest = strtoupper($rest);
        if(array_key_exists($rest, $type)){
            $actions = array_search($a, $type[$rest][0]);
            if ($actions == false){
                $result = file_get_contents(TEMPLATES . $pages['401'][0]);
                $page = $pages['404'][0];
            
            }else{
                $page = $type[$rest][$actions];
                echo $page;
            
            };

            
            if (false !== ($data = file_get_contents(TEMPLATES . $page))) {
                $result = $data;
                $result = str_replace("%ACTIVITY%",'"'.$p.'"',$result);

            }else{
                $result = file_get_contents(TEMPLATES . $pages['503'][0]);
            }

        }else{
            $result = file_get_contents(TEMPLATES . $pages['401'][0]);
        }
    }
    return $result;
}

function authorize($c,$l){
    if(in_array("All",$l)){
        return true;
    }else{
        return in_array($c,$l);  
    }
}

