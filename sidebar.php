<!-- Topbar -->
<?php header('Content-type: text/html; charset=utf-8');

$foto = $_SESSION["Foto"]."_thumb.png";


if ($privilegios == "Estudiante") {
    $line = '<a href="https://reuna.zoom.us/j/87598298830?pwd=K3ZhVXZvbk9pUVpGbitiVzFKdjU3Zz09" target="_blank">LINK ZOOM </a>';
}else{$line ='<a href="https://reuna.zoom.us/j/87598298830?pwd=K3ZhVXZvbk9pUVpGbitiVzFKdjU3Zz09" target="_blank">LINK ZOOM </a>';}

echo <<< TEO

<nav class="navbar navbar-expand navbar-light bg-white topbar mb-4 static-top shadow">

    <!-- Sidebar Toggle (Topbar) -->
    <button id="sidebarToggleTop" class="btn btn-link d-md-none rounded-circle mr-3">
        <i class="fa fa-bars"></i>
    </button>

    <!-- Topbar Search -->
    <form class="d-none d-sm-inline-block form-inline mr-auto ml-md-3 my-2 my-md-0 mw-100 navbar-search">
        <div class="input-group">
            <h1 class="h3 mb-0 text-gray-800">$line</h1>
        </div>
    </form>

    <!-- Topbar Navbar -->
    <ul class="navbar-nav ml-auto">


        <div class="topbar-divider d-none d-sm-block"></div>

        <!-- Nav Item - User Information -->
        <li class="nav-item dropdown no-arrow">
            <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-toggle="dropdown"
               aria-haspopup="true" aria-expanded="false">
                <span class="mr-2 d-none d-lg-inline text-gray-600 small">$user_name</span>
                <img class="img-profile rounded-circle"
                     src="photo_profile/$foto">
            </a>
            <!-- Dropdown - User Information -->
            <div class="dropdown-menu dropdown-menu-right shadow animated--grow-in" aria-labelledby="userDropdown">


                <a class="dropdown-item" href="#" data-toggle="modal" data-target="#logoutModal">
                    <i class="fas fa-sign-out-alt fa-sm fa-fw mr-2 text-gray-400"></i>
                    Salir
                </a>
            </div>
        </li>

    </ul>

</nav>
<!-- End of Topbar -->


TEO;

