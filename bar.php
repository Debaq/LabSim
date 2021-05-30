<?php
if ($privilegios == "Docente") {
    $Texto = "Sistema Docente";
}
if ($privilegios == "Estudiante") {
    $Texto = "Examen Oral";
}

echo  <<< ETO
<!-- Sidebar -->
    <ul class="navbar-nav bg-gradient-primary sidebar sidebar-dark accordion" id="accordionSidebar">

      <!-- Sidebar - Brand -->
      <a class="sidebar-brand d-flex align-items-center justify-content-center" href="index.php">
        <div class="sidebar-brand-icon rotate-n-15">
        <img class="img-profile rounded-circle" width="48" src="img/logo.png">
        </div>
        <div class="sidebar-brand-text mx-3">
        $Texto
        </div>
      </a>

      <!-- Divider -->
      <hr class="sidebar-divider my-0">

      <!-- Nav Item - Dashboard -->
      <li class="nav-item active">
        <a class="nav-link" href="#page-top">
      </li>

      <!-- Divider -->

      <!-- Heading -->
      <div class="sidebar-heading">
      </div>
ETO;

$txt_area = codifica_urlget("nameArea=Sorteo&idArea=&view=false&idQ=");
$txt_preguntas = codifica_urlget("nameArea=Preguntas&idArea=&view=false&idQ=");
$txt_envio = codifica_urlget("nameArea=Envio&idArea=&view=false&idQ=");

$txt_estudiantes = codifica_urlget("nameArea=Estudiantes&idArea=&view=false&idQ=");

$EST = <<< TOE
      <!-- Nav Item - Utilities Collapse Menu -->
      <li class="nav-item">
        <a class="nav-link collapsed" href="#" data-toggle="collapse" data-target="#collapseUtilities" aria-expanded="true" aria-controls="collapseUtilities">
          <i class="fas fa-fw fa-wrench"></i>
          <span>Menú</span>
        </a>
        <div id="collapseUtilities" class="collapse show" aria-labelledby="headingUtilities" data-parent="#accordionSidebar">
          <div class="bg-white py-2 collapse-inner rounded">
            <a class="collapse-item" href="index.php?$txt_area">Pregunta/Sorteo</a>
            
          </div>
        </div>
      </li>
TOE;

$Area_Admin = <<<TOE
      <!-- Nav Item - Utilities Collapse Menu -->
      <li class="nav-item">
        <a class="nav-link collapsed" href="#" data-toggle="collapse" data-target="#collapseUtilities" aria-expanded="true" aria-controls="collapseUtilities">
          <i class="fas fa-fw fa-wrench"></i>
          <span>Menú</span>
        </a>
        <div id="collapseUtilities" class="collapse show" aria-labelledby="headingUtilities" data-parent="#accordionSidebar">
          <div class="bg-white py-2 collapse-inner rounded">
            <a class="collapse-item" href="index.php?$txt_estudiantes">Estudiantes</a>
            <a class="collapse-item" href="index.php?$txt_preguntas">Preguntas</a>

          </div>

        </div>
      </li>
TOE;

if ($privilegios == "Estudiante") {
    echo $EST;
}

if ($privilegios == "Docente") {
    echo $Area_Admin;
}

echo <<<EOT
        <!-- Divider -->
      <hr class="sidebar-divider">

      <!-- Heading -->
    

      <!-- Sidebar Toggler (Sidebar) -->


    </ul>
EOT;
