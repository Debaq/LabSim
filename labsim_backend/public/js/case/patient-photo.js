// Foto de paciente: elegir archivo -> modal de recorte circular (pan/zoom
// con mouse o touch) -> fetch con FormData a patient_photo_upload.php. El
// crop se manda como rectángulo (crop_x/y/size) en píxeles de la imagen
// ORIGINAL -- PatientPhoto::save() hace el recorte real server-side con GD,
// acá solo se calcula el rectángulo a partir del pan/zoom en pantalla.
(function () {
    var fileInput = document.getElementById('patient-photo-input');
    var modal = document.getElementById('photo-crop-modal');
    var viewport = document.getElementById('photo-crop-viewport');
    var img = document.getElementById('photo-crop-img');
    var zoomSlider = document.getElementById('photo-crop-zoom');
    var cancelBtn = document.getElementById('photo-crop-cancel');
    var confirmBtn = document.getElementById('photo-crop-confirm');
    var avatarPreview = document.getElementById('patient-avatar-preview');
    var avatarEmpty = document.getElementById('patient-avatar-empty');
    var msgEl = document.getElementById('photo-msg');
    // El parrafo entero, no cada enlace: entre los dos hay un "|" de texto
    // suelto que ocultando solo los <a> quedaba flotando en la ficha.
    var dlLinks = document.getElementById('patient-download-links');
    if (!fileInput || !modal) { return; }

    var CASE_ID = window.CASE_CONST.caseId;
    var VIEWPORT = 280;
    var naturalW = 0, naturalH = 0, coverScale = 1, scale = 1;
    var tx = 0, ty = 0;
    var dragging = false, dragStartX = 0, dragStartY = 0, dragOrigTx = 0, dragOrigTy = 0;
    var selectedFile = null;
    // Quién es el dueño de la foto que se está recortando: el paciente
    // (persona '') o un acompañante de la sala. El modal es uno solo -- lo
    // que cambia es a qué fila vuelve la miniatura cuando termina.
    var pendingInput = fileInput;
    var pendingPersona = '';
    var pendingPreview = avatarPreview;
    var pendingEmpty = avatarEmpty;

    function clampPan() {
        var dispW = naturalW * scale;
        var dispH = naturalH * scale;
        var minTx = Math.min(0, VIEWPORT - dispW);
        var minTy = Math.min(0, VIEWPORT - dispH);
        tx = Math.max(minTx, Math.min(0, tx));
        ty = Math.max(minTy, Math.min(0, ty));
    }

    function applyTransform() {
        img.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')';
    }

    function openModal(file, input, persona, preview, empty) {
        selectedFile = file;
        pendingInput = input;
        pendingPersona = persona;
        pendingPreview = preview;
        pendingEmpty = empty;
        img.onload = function () {
            naturalW = img.naturalWidth;
            naturalH = img.naturalHeight;
            coverScale = Math.max(VIEWPORT / naturalW, VIEWPORT / naturalH);
            scale = coverScale;
            tx = (VIEWPORT - naturalW * scale) / 2;
            ty = (VIEWPORT - naturalH * scale) / 2;
            zoomSlider.value = '1';
            applyTransform();
            modal.hidden = false;
        };
        img.src = URL.createObjectURL(file);
    }

    function closeModal() {
        modal.hidden = true;
        if (pendingInput) { pendingInput.value = ''; }
        selectedFile = null;
    }

    function showMsg(text, isError) {
        msgEl.textContent = text;
        msgEl.style.color = isError ? '#a33' : '#2a7a2a';
        msgEl.hidden = false;
    }

    fileInput.addEventListener('change', function () {
        if (fileInput.files && fileInput.files[0]) {
            openModal(fileInput.files[0], fileInput, '', avatarPreview, avatarEmpty);
        }
    });

    // Delegado: las filas de la sala se agregan y se borran en caliente, así
    // que no se les puede colgar el listener una sola vez al cargar.
    document.addEventListener('change', function (e) {
        var input = e.target;
        if (!input.classList || !input.classList.contains('sala-photo-input')) { return; }
        if (!input.files || !input.files[0]) { return; }
        var row = input.closest('.sala-row');
        openModal(
            input.files[0], input, input.dataset.persona,
            row.querySelector('.sala-avatar'), row.querySelector('.sala-avatar-empty')
        );
    });

    cancelBtn.addEventListener('click', closeModal);

    zoomSlider.addEventListener('input', function () {
        var z = parseFloat(zoomSlider.value);
        // Ancla el zoom al centro del viewport, no a la esquina.
        var cx = VIEWPORT / 2, cy = VIEWPORT / 2;
        var imgCx = (cx - tx) / scale;
        var imgCy = (cy - ty) / scale;
        scale = coverScale * z;
        tx = cx - imgCx * scale;
        ty = cy - imgCy * scale;
        clampPan();
        applyTransform();
    });

    function pointerDown(x, y) {
        dragging = true;
        dragStartX = x; dragStartY = y;
        dragOrigTx = tx; dragOrigTy = ty;
    }
    function pointerMove(x, y) {
        if (!dragging) { return; }
        tx = dragOrigTx + (x - dragStartX);
        ty = dragOrigTy + (y - dragStartY);
        clampPan();
        applyTransform();
    }
    function pointerUp() { dragging = false; }

    viewport.addEventListener('mousedown', function (e) { pointerDown(e.clientX, e.clientY); });
    window.addEventListener('mousemove', function (e) { pointerMove(e.clientX, e.clientY); });
    window.addEventListener('mouseup', pointerUp);
    viewport.addEventListener('touchstart', function (e) {
        pointerDown(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: true });
    viewport.addEventListener('touchmove', function (e) {
        pointerMove(e.touches[0].clientX, e.touches[0].clientY);
        e.preventDefault();
    }, { passive: false });
    viewport.addEventListener('touchend', pointerUp);

    confirmBtn.addEventListener('click', function () {
        if (!selectedFile) { return; }
        // Recuadro visible en pantalla = el viewport completo (0,0)-(V,V);
        // se convierte a coordenadas de píxel de la imagen ORIGINAL.
        var srcSize = VIEWPORT / scale;
        var srcX = -tx / scale;
        var srcY = -ty / scale;

        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Guardando...';

        var fd = new FormData();
        fd.append('csrf_token', document.querySelector('input[name="csrf_token"]').value);
        fd.append('case_id', CASE_ID);
        fd.append('persona', pendingPersona);
        fd.append('crop_x', Math.round(srcX));
        fd.append('crop_y', Math.round(srcY));
        fd.append('crop_size', Math.round(srcSize));
        fd.append('photo', selectedFile);

        fetch('patient_photo_upload.php', { method: 'POST', body: fd })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                confirmBtn.disabled = false;
                confirmBtn.textContent = 'Guardar foto';
                if (data.ok) {
                    pendingPreview.src = 'patient_photo.php?case_id=' + encodeURIComponent(CASE_ID)
                        + '&persona=' + encodeURIComponent(pendingPersona) + '&type=avatar&v=' + Date.now();
                    pendingPreview.hidden = false;
                    pendingEmpty.hidden = true;
                    // Los enlaces de descarga son del bloque del paciente:
                    // un acompañante no los tiene.
                    if (pendingPersona === '' && dlLinks) { dlLinks.hidden = false; }
                    showMsg('Foto actualizada.', false);
                    closeModal();
                } else {
                    showMsg(data.error || 'No se pudo guardar la foto.', true);
                }
            })
            .catch(function () {
                confirmBtn.disabled = false;
                confirmBtn.textContent = 'Guardar foto';
                showMsg('Error de red al subir la foto.', true);
            });
    });
})();
