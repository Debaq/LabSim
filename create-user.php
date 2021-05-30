<?php
echo <<< TEO
  <script>
    var check = function() {
      if (document.getElementById('password').value ==
        document.getElementById('password_c').value) {
        document.getElementById('message').style.color = 'green';
        document.getElementById('message').innerHTML = '<svg class="bi bi-check" width="2em" height="2em" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg"> <path fill-rule="evenodd" d="M13.854 3.646a.5.5 0 010 .708l-7 7a.5.5 0 01-.708 0l-3.5-3.5a.5.5 0 11.708-.708L6.5 10.293l6.646-6.647a.5.5 0 01.708 0z" clip-rule="evenodd"/></svg>';
        document.getElementById("submit").disabled = false;
      } else {
        document.getElementById('message').style.color = 'red';
        document.getElementById('message').innerHTML = '<svg class="bi bi-x" width="2em" height="2em" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M11.854 4.146a.5.5 0 010 .708l-7 7a.5.5 0 01-.708-.708l7-7a.5.5 0 01.708 0z" clip-rule="evenodd"/><path fill-rule="evenodd" d="M4.146 4.146a.5.5 0 000 .708l7 7a.5.5 0 00.708-.708l-7-7a.5.5 0 00-.708 0z" clip-rule="evenodd"/></svg>';
        document.getElementById("submit").disabled = true;
      }
    }
  </script>


<body class="bg-gradient-primary">

  <div class="container">

    <div class="card o-hidden border-0 shadow-lg my-5">
      <div class="card-body p-0">
        <!-- Nested Row within Card Body -->
        <div class="row">
          <div class="col-lg-5 d-none d-lg-block bg-register-image"></div>
          <div class="col-lg-7">
            <div class="p-5">
              <div class="text-center">
                <h1 class="h4 text-gray-900 mb-4">Crear una cuenta</h1>
              </div>
              <form class="user" name="new_user" onsubmit="return validateForm()" action="create-account-into.php" method="POST">

                <div class="form-group row">
                  <div class="col-sm-6 mb-3 mb-sm-0">
                    <input type="text" class="form-control form-control-user" name="name" placeholder="Nombre" required>
                  </div>
                  <div class="col-sm-6">
                    <input type="text" class="form-control form-control-user" name="apellido" placeholder="Apellido" required>
                  </div>
   
                </div>

                <div class="form-group">
                  <input type="email" class="form-control form-control-user" name="email" placeholder="Correo electrónico" required>
                </div>


                <div class="form-group row">
                  <div class="col-sm-6 mb-3 mb-sm-0">
                    <input type="password" class="form-control form-control-user" name="password" id="password" placeholder="Contraseña" required>
                  </div>
                  <span id='message'></span>
                  <div class="col-md-auto">
                    <input type="password" class="form-control form-control-user" id="password_c" name="password_c" placeholder="Repita contraseña" onkeyup='check();' required>                
                  </div>
                </div>

              
                <div class="form-group row">
                  <div class="form-check form-check-inline">
                    <input class="form-check-input" type="radio" name="privilegio" id="PrivRadio1" value="Docente">
                    <label class="form-check-label" for="PrivRadio1">Docente</label>
                    <input class="form-check-input" type="radio" name="privilegio" id="PrivRadio2" value="Estudiante">
                    <label class="form-check-label" for="PrivRadio2">Estudiante</label>
                  </div>
                </div>

                
                <input type="submit" value="Registrar cuenta" id="submit" class="btn btn-primary btn-user btn-block">
                <hr>
           </form>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
  </div>

  </div>

TEO;
