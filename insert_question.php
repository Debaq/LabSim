<?php
$code = generate_string($permitted_chars, 10);

echo <<< TAO

  <div class="container">

    <div class="card o-hidden border-0 shadow-lg my-5">
      <div class="card-body p-0">
        <!-- Nested Row within Card Body -->
        <div class="row">
          <div class="col-lg-5 d-none d-lg-block bg-register-image"></div>
          <div class="col-lg-7">
            <div class="p-5">
              <div class="text-center">
                <h1 class="h4 text-gray-900 mb-4">Insertar Pregunta</h1>
              </div>
              <form class="user" name="new_user" action="create-question.php" method="POST" enctype="multipart/form-data">

                <div class="form-group row">
                  <div class="col-sm-6 mb-3 mb-sm-0">
                    <input type="text" class="form-control form-control-user" name="name" placeholder="Nombre de la pregunta" required>
                  </div>
                  <div class="col-sm-6">
                    <input type="text" class="form-control form-control-user" name="code" placeholder="$code" value="$code" readonly>
                  </div>
   
                </div>

                <div class="form-group">
                    <input type="file" id="documento" name="documento" accept=".pdf">                
                </div>

                <input type="submit" id="submit" name="uploadBtn" value="Subir"  class="btn btn-primary btn-user btn-block">
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
TAO;
