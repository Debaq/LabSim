
<?php
session_start();
include_once('module/global_function.php');

if(!isset($_SESSION["login"])){
    
  header('Location: module/login.php');

}

if(!isset($_SESSION['user'])){
  $activate = false;
 }else{ 
   $activate = true; 
 }
 



include_once('module/redirect.php');

if(!isset($_SESSION['page_prev'])){
  $_SESSION["page_prev"] = "index";
  $_SESSION["page_actual"] = "index";

}


define('VERSION', '0.1.1');
define('APP_TITLE', 'LabSim');
define('APP_ICON', 'https://tmeduca.cl/AudioSim/lib/icon.svg');
define('CONSUMER', 'UACH');
define('WEB', 'http://www.tmeduca.cl');
define('CFG_SIDEBAR', 'sidebar.json');
define('CFG_NAVBAR', 'navbar.json');
define('TEMPLATES', 'pages/');
define('VERSION_SW', '0.7.5');
define('ROOT', __DIR__ . '/');


//Configurations
$config_file = __DIR__.'/config.json';
if (!file_exists($config_file)){
  //Default Configuration
  $CONFIG = json_decode('{"use_lti":true}');
}else{
  $file = fopen($config_file, 'r');
  //Config setup
  $CONFIG = json_decode($config_file, true);
  fclose($file);
}

// logout
if (isset($_GET['logout'])) {
  unset($_SESSION[FM_SESSION_ID]['logged']);
  fm_redirect(FM_SELF_URL);
}

if(isset($_GET['p'])){
  $page = $_GET['p'];
  if(isset($_GET['a'])){
    $action = $_GET['a'];
  }else{
    $action = null;
  }
}else{
  $page = 'index';
  $action = null;
} 
$credential = $_SESSION["credentials"];
$page_prev = $_SESSION["page_prev"];
$result_page = page_action($page, $action, $credential);

if($activate){
  echo head();
  echo body($result_page, $credential);
}else{
  $data = file_get_contents(TEMPLATES . "block_entry.html_");
  echo $data;
}


function wrapper_content($page) {
  $result = str_replace("%SECTION%",$_SESSION["page_actual"],$page);
  $result = str_replace("%BACK%",$_SESSION["page_prev"],$result);
  $result = str_replace("%HOME%",'index',$result);

  if($_SESSION["page_actual"]== "index"){
    $result = str_replace("%VER_SW%",VERSION_SW,$result);
    $result = str_replace("%VERSION%",VERSION,$result);
    }
  return $result;
}

function Preload(){
  $img = APP_ICON;
  $img_alt = APP_TITLE;
  $result=<<<EOF
  <div class="preloader flex-column justify-content-center align-items-center">
  <img class="animation__shake" src="$img" alt="$img_alt" height="60" width="60">
  </div>

  EOF;
  return $result;
}

function Body($page, $c){
  $user_img = "user_generic.jpg";
  $user_name = $_SESSION['Username'];
  $idx_web = json_decode('', true);
  $preloader = Preload();
  $nav = Navbar($c);
  $sidebar = Sidebar($user_name, $user_img, $idx_web, $c);

  $body_wrapper = wrapper_content($page);
  $foot = footer();
  $script = script();
  $result=<<<EOL
    <body class="hold-transition sidebar-mini">
      <div class="wrapper">
      $preloader
      $nav
      $sidebar
      $body_wrapper
      $foot
      </div>
      $script
      </body>
      </html>

  EOL;
  return $result;
}

function Sidebar($user_name, $user_img, $idx, $c){
  $app_title = APP_TITLE;
  $app_version = VERSION;
  $app_img = APP_ICON;
  $cfg_sidebar = CFG_SIDEBAR;
  if(isset($_GET['p'])){
    $page = $_GET['p'];
  }else{$page = "";} 
  $active = $page;
  $credentials = $c;
  $menu = create_menu_sidebar(load_json(CFG_SIDEBAR), $credentials, $active);
  $menu_html=<<<EOL

      <aside class="main-sidebar sidebar-dark-primary elevation-4">
        <!-- Brand Logo -->
        <a href="?p=index" class="brand-link">
            <img src="$app_img" alt="AdminLTE Logo" class="brand-image img-circle elevation-3" style="opacity: 0.8" />
            <span class="brand-text font-weight-light">$app_title $app_version</span>
        </a>

        <!-- Sidebar -->
        <div class="sidebar">
            <!-- Sidebar user panel (optional) -->
            <div class="user-panel mt-3 pb-3 mb-3 d-flex">
                <div class="image">
                    <img src="dist/img/$user_img" class="img-circle elevation-2" alt="User Image" />
                </div>
                <div class="info">
                    <a href="#" class="d-block">$user_name</a>
                </div>
            </div>

            <!-- SidebarSearch Form -->
            <div class="form-inline">
                <div class="input-group" data-widget="sidebar-search">
                    <input class="form-control form-control-sidebar" type="search" placeholder="Search"
                        aria-label="Search" />
                    <div class="input-group-append">
                        <button class="btn btn-sidebar">
                            <i class="fas fa-search fa-fw"></i>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Sidebar Menu -->
            <nav class="mt-2">
                <ul class="nav nav-pills nav-sidebar flex-column" data-widget="treeview" role="menu" data-accordion="false">
                    $menu
                </ul>
            </nav>
            <!-- /.sidebar-menu -->
        </div>
        <!-- /.sidebar -->
    </aside>

  EOL;

  
  return $menu_html;

}

function Navbar($c){
  $credentials = $c;

  $menu = create_menu_navbar(load_json(CFG_NAVBAR), $credentials);

  $result =<<<EOL
    <!-- Navbar -->
    <nav class="main-header navbar navbar-expand navbar-white navbar-light">
     
    $menu
     
    </nav>
    <!-- /.navbar -->
  EOL;
  return $result;
}

function head(){
  $app_title = APP_TITLE;
  $app_version = VERSION;
  
  $result =<<<EOL
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>$app_title | $app_version</title>
    
        <!-- Google Font: Source Sans Pro -->
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,400i,700&display=fallback"
        />
        <!-- Font Awesome Icons -->
        <link rel="stylesheet" href="https://pro.fontawesome.com/releases/v5.10.0/css/all.css" integrity="sha384-AYmEC3Yw5cVb3ZcuHtOA93w35dYTsvhLPVnYs9eStHfGJvOvKxVfELGroGkvsg+p" crossorigin="anonymous"/>
        <!-- IonIcons -->
        <link rel="stylesheet" href="https://code.ionicframework.com/ionicons/2.0.1/css/ionicons.min.css" />
        <!-- Theme style -->
        <link rel="stylesheet" href="dist/css/adminlte.min.css" />
        
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.25/css/dataTables.bootstrap4.min.css"/>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/buttons/1.7.1/css/buttons.bootstrap4.min.css"/>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/responsive/2.2.9/css/responsive.bootstrap4.min.css"/>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/select/1.3.3/css/select.bootstrap4.min.css"/>
        
        
        <!-- jQuery -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
        <style>
          .monofont{
          font: 90%/1.45em "Courier New", monospace;
          margin: 0;
          padding: 0;
        }
        </style>
      </head>
      <!--
    `body` tag options:
    
      Apply one or more of the following classes to to the body tag
      to get the desired effect
    
      * sidebar-collapse
      * sidebar-mini
    -->

  EOL;
  return $result;
}

function script() {
  $result=<<<EOL
  
  <!-- REQUIRED SCRIPTS -->
  <!-- Bootstrap -->
  
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ho+j7jyWK8fNQe+A12Hb8AhRq26LrZ/JpcUGGOn+Y7RsweNrtN/tE3MoK7ZeZDyx" crossorigin="anonymous"></script>  <!-- AdminLTE -->
  <script src="dist/js/adminlte.js"></script>
  <!-- OPTIONAL SCRIPTS 
  <script src="plugins/chart.js/Chart.min.js"></script> -->


  EOL;

  return $result;

}

function footer(){
  $app_title = APP_TITLE;
  $app_version = VERSION;
  $app_web = WEB;
  $year = date("Y"); 
  $result=<<<EOL
 
      <!-- Main Footer -->
      <footer class="main-footer">
        <strong
          >Copyright &copy; $year
          <a href="$app_web">$app_title</a>.</strong
        >
        Todos los Derechos reservados.
        <div class="float-right d-none d-sm-inline-block">
          <b>Version</b> $app_version
        </div>
      </footer>
    

  EOL;
  return $result;
}

function create_menu_sidebar($list_menu, $credentials, $active){
  $var_pred = ['menu-open','<i class="right fas fa-angle-left"></i>', 'active', 'disabled'];
  $result = '';
  foreach ($list_menu as $s){
    $root_access = in_array($credentials , $s['permits']);
    if($root_access){
      $state = ($s['alias'] == $active) ? $var_pred[2] : '';
      $is_menu = $s['subT'] ? "" : "";
      $result = $result.'<li class="nav-item '. $is_menu .'">'."\n";
      $result = $result.'<a href="'.$s['path'].'" class="nav-link '. $state .'">'."\n";
      $result = $result.'<i class="' . $s["icon"] . '"></i>'."\n";
      $result = $result.'<p>' . $s['name']."\n";
      $result = $result.$s['notice'];
      $icon_menu = $s['subT'] ? $var_pred[1] : '';
      $result= $result.$icon_menu.'</p></a>'."\n";
      if($s["subT"]){
        $result=$result.'<ul class="nav nav-treeview">'."\n";
        foreach ($s['sub_titles'] as $o) {
          $branches_access = in_array($credentials , $o['permits']);
          if($branches_access){
            $state = ($o['alias'] == $active) ? $var_pred[2] : '';
            $result=$result.'<li class="nav-item">'."\n";
            $result=$result.'<a href="'. $o['path'] .'" class="nav-link ' . $state . '">'."\n";
            $result=$result.'<i class="' . $o["icon"] . '"></i>'."\n";
            $result=$result.'<p>'. $o['name']."\n";
            $result = $result.$o['notice'].'</p></a></li>'."\n";
          }
        }
        $result=$result.'</ul>'."\n";
      }
    }
  }
    $result=$result."</li>"."\n";
    return $result;
}

function  create_menu_navbar($list_menu, $credentials){
  $left = '';
  $right = '';
  $head = '<ul class="navbar-nav ';
  $li = '<li class="nav-item ';
  $a = '<a class="nav-link" ';
  $icon = '<i class="';
  foreach($list_menu as $s){
    $side = $s['aling'];
    $root_access = in_array($credentials , $s['permits']);
    if ($root_access){
      if($side == 'left'){
        $left = $left . $li . $s['class'] . '">'."\n";
        $left = $left . $a . 'data-widget="'. $s['data-widget'] . '" ';
        $left = $left . 'data-toggle="'. $s['data-toggle'] . '" ';
        $left = $left . 'href="' . $s['href'] . '" ';
        $left = $left . 'role="' . $s['role'] . '">' . "\n";
        $left = $left . $s['name'] . "\n";
        if($s['icon'] != ''){
          $left = $left . $icon . $s['icon'] . '"></i></a>' . "\n";
        }else{
          $left = $left . ' </a>' . "\n";
        }
        $left = $left . '</li>' . "\n";
      }
      if($side == 'right'){
        $right = $right . $li . $s['class'] . '">'."\n";
        $right = $right . $a . 'data-widget="'. $s['data-widget'] . '" ';
        $right = $right . 'data-toggle="'. $s['data-toggle'] . '" ';
        $right = $right . 'href="' . $s['href'] . '" ';
        $right = $right . 'role="' . $s['role'] . '">' . "\n";
        $right = $right . $s['name'] . "\n";
        if($s['icon'] != ''){
          $right = $right . $icon . $s['icon'] . '"></i></a>' . "\n";
        }else{
          $right = $right . ' </a>' . "\n";
        }
        $right = $right . '</li>' . "\n";
      }
    }
  }
  $result = $head. '">' . "\n" . $left . '</ul> ' . "\n" . $head . 'ml-auto">'.$_SESSION["credentials"] . "\n" . $right . "\n";
  return $result;
}
