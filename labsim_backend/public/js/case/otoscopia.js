// Ficha Otoscopia: sin selector de modo -- 1 sola fase ya ES "única"; se
// agrega/quita fase (solo la última -- así no hay que reindexar archivos
// en disco), y se sube/borra cada imagen por fetch + FormData. Mismo
// patrón de recorte manual que la foto de paciente (modal de pan/zoom),
// pero con guía cuadrada (no circular) -- ver #otoscopia-crop-modal y
// OtoscopiaPhoto::save().
(function () {
    var CASE_ID = window.CASE_CONST.caseId;
    var countInput = document.getElementById('otoscopia-fase-count');
    var container = document.getElementById('otoscopia-fases');
    var addBtn = document.getElementById('otoscopia-add-fase');
    var msgEl = document.getElementById('otoscopia-msg');
    if (!countInput || !container) { return; }

    // --- Modal de recorte cuadrado (pan/zoom), mismo mecanismo que el de
    // foto de paciente pero reutilizable para cualquier input de la lista
    // (se le pasa el <input> pendiente al abrir). ---
    var cropModal = document.getElementById('otoscopia-crop-modal');
    var cropViewport = document.getElementById('otoscopia-crop-viewport');
    var cropImg = document.getElementById('otoscopia-crop-img');
    var cropZoom = document.getElementById('otoscopia-crop-zoom');
    var cropCancelBtn = document.getElementById('otoscopia-crop-cancel');
    var cropConfirmBtn = document.getElementById('otoscopia-crop-confirm');
    var CROP_VIEWPORT = 280;
    var naturalW = 0, naturalH = 0, coverScale = 1, scale = 1;
    var tx = 0, ty = 0;
    var dragging = false, dragStartX = 0, dragStartY = 0, dragOrigTx = 0, dragOrigTy = 0;
    var pendingInput = null, pendingFile = null;

    function clampPan() {
        var dispW = naturalW * scale;
        var dispH = naturalH * scale;
        var minTx = Math.min(0, CROP_VIEWPORT - dispW);
        var minTy = Math.min(0, CROP_VIEWPORT - dispH);
        tx = Math.max(minTx, Math.min(0, tx));
        ty = Math.max(minTy, Math.min(0, ty));
    }

    function applyTransform() {
        cropImg.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')';
    }

    function openCropModal(input, file) {
        pendingInput = input;
        pendingFile = file;
        cropImg.onload = function () {
            naturalW = cropImg.naturalWidth;
            naturalH = cropImg.naturalHeight;
            coverScale = Math.max(CROP_VIEWPORT / naturalW, CROP_VIEWPORT / naturalH);
            scale = coverScale;
            tx = (CROP_VIEWPORT - naturalW * scale) / 2;
            ty = (CROP_VIEWPORT - naturalH * scale) / 2;
            cropZoom.value = '1';
            applyTransform();
            cropModal.hidden = false;
        };
        cropImg.src = URL.createObjectURL(file);
    }

    function closeCropModal() {
        cropModal.hidden = true;
        if (pendingInput) { pendingInput.value = ''; }
        pendingInput = null;
        pendingFile = null;
    }

    cropCancelBtn.addEventListener('click', closeCropModal);

    cropZoom.addEventListener('input', function () {
        var z = parseFloat(cropZoom.value);
        var cx = CROP_VIEWPORT / 2, cy = CROP_VIEWPORT / 2;
        var imgCx = (cx - tx) / scale;
        var imgCy = (cy - ty) / scale;
        scale = coverScale * z;
        tx = cx - imgCx * scale;
        ty = cy - imgCy * scale;
        clampPan();
        applyTransform();
    });

    function cropPointerDown(x, y) {
        dragging = true;
        dragStartX = x; dragStartY = y;
        dragOrigTx = tx; dragOrigTy = ty;
    }
    function cropPointerMove(x, y) {
        if (!dragging) { return; }
        tx = dragOrigTx + (x - dragStartX);
        ty = dragOrigTy + (y - dragStartY);
        clampPan();
        applyTransform();
    }
    function cropPointerUp() { dragging = false; }

    cropViewport.addEventListener('mousedown', function (e) { cropPointerDown(e.clientX, e.clientY); });
    window.addEventListener('mousemove', function (e) { cropPointerMove(e.clientX, e.clientY); });
    window.addEventListener('mouseup', cropPointerUp);
    cropViewport.addEventListener('touchstart', function (e) {
        cropPointerDown(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: true });
    cropViewport.addEventListener('touchmove', function (e) {
        cropPointerMove(e.touches[0].clientX, e.touches[0].clientY);
        e.preventDefault();
    }, { passive: false });
    cropViewport.addEventListener('touchend', cropPointerUp);

    cropConfirmBtn.addEventListener('click', function () {
        if (!pendingInput || !pendingFile) { return; }
        var side = pendingInput.getAttribute('data-side');
        var idx = pendingInput.getAttribute('data-fase-idx');
        var slot = pendingInput.closest('.otoscopia-photo-slot');
        var img = slot.querySelector('.otoscopia-thumb');
        var empty = slot.querySelector('.otoscopia-thumb-empty');

        var srcSize = CROP_VIEWPORT / scale;
        var srcX = -tx / scale;
        var srcY = -ty / scale;

        var fd = new FormData();
        fd.append('csrf_token', csrfToken());
        fd.append('case_id', CASE_ID);
        fd.append('side', side);
        fd.append('fase_idx', idx);
        fd.append('crop_x', Math.round(srcX));
        fd.append('crop_y', Math.round(srcY));
        fd.append('crop_size', Math.round(srcSize));
        fd.append('photo', pendingFile);

        var input = pendingInput;
        cropConfirmBtn.disabled = true;
        cropConfirmBtn.textContent = 'Guardando...';
        input.disabled = true;

        fetch('otoscopia_photo_upload.php', { method: 'POST', body: fd })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                cropConfirmBtn.disabled = false;
                cropConfirmBtn.textContent = 'Guardar foto';
                input.disabled = false;
                if (data.ok) {
                    img.src = 'otoscopia_photo.php?case_id=' + encodeURIComponent(CASE_ID) + '&side=' + side + '&fase=' + idx + '&v=' + Date.now();
                    img.hidden = false;
                    empty.hidden = true;
                    var delBtn = slot.querySelector('.otoscopia-delete-photo');
                    if (delBtn) { delBtn.hidden = false; }
                    var dlLink = slot.querySelector('.otoscopia-download-photo');
                    if (dlLink) { dlLink.hidden = false; }
                    showMsg('Imagen actualizada.', false);
                    cropModal.hidden = true;
                    input.value = '';
                    pendingInput = null;
                    pendingFile = null;
                } else {
                    showMsg(data.error || 'No se pudo guardar la imagen.', true);
                }
            })
            .catch(function () {
                cropConfirmBtn.disabled = false;
                cropConfirmBtn.textContent = 'Guardar foto';
                input.disabled = false;
                showMsg('Error de red al subir la imagen.', true);
            });
    });

    function csrfToken() {
        var el = document.querySelector('input[name="csrf_token"]');
        return el ? el.value : '';
    }

    function showMsg(text, isError) {
        if (!msgEl) { return; }
        msgEl.textContent = text;
        msgEl.style.color = isError ? '#a33' : '#2a7a2a';
        msgEl.hidden = false;
    }

    function faseBlocks() {
        return Array.prototype.slice.call(container.querySelectorAll('.otoscopia-fase'));
    }

    // Solo la última fase puede quitarse (sin reindexar imágenes en disco).
    function updateRemoveButtons() {
        var blocks = faseBlocks();
        blocks.forEach(function (block, i) {
            var btn = block.querySelector('.otoscopia-remove-fase');
            if (btn) {
                btn.hidden = i !== blocks.length - 1;
            }
        });
    }

    var slotTpl = document.getElementById('otoscopia-slot-tpl');
    var faseTpl = document.getElementById('otoscopia-fase-tpl');

    function buildSlot(side, label, idx) {
        var slot = slotTpl.content.firstElementChild.cloneNode(true);
        var tag = slot.querySelector('.side-tag');
        tag.textContent = label;
        tag.classList.add(side);
        var img = slot.querySelector('.otoscopia-thumb');
        img.setAttribute('data-side', side);
        img.setAttribute('data-fase-idx', idx);
        img.setAttribute('alt', 'Otoscopia ' + label + ' fase ' + (idx + 1));
        var input = slot.querySelector('.otoscopia-photo-input');
        input.setAttribute('data-side', side);
        input.setAttribute('data-fase-idx', idx);
        var delBtn = slot.querySelector('.otoscopia-delete-photo');
        delBtn.setAttribute('data-side', side);
        delBtn.setAttribute('data-fase-idx', idx);
        var dlLink = slot.querySelector('.otoscopia-download-photo');
        dlLink.setAttribute('data-side', side);
        dlLink.setAttribute('data-fase-idx', idx);
        dlLink.href = 'otoscopia_photo.php?case_id=' + encodeURIComponent(CASE_ID) + '&side=' + side + '&fase=' + idx + '&download=1';
        return slot;
    }

    function buildFaseBlock(idx) {
        var block = faseTpl.content.firstElementChild.cloneNode(true);
        block.setAttribute('data-fase-idx', idx);
        block.querySelector('.side-heading .side-tag').textContent = 'Fase ' + (idx + 1);
        block.querySelector('.otoscopia-remove-fase').setAttribute('data-fase-idx', idx);
        block.querySelector('textarea').setAttribute('name', 'otoscopia[texto][' + idx + ']');
        var twoCol = block.querySelector('.two-col');
        [['od', 'OD'], ['oi', 'OI']].forEach(function (s) {
            twoCol.appendChild(buildSlot(s[0], s[1], idx));
        });
        return block;
    }

    if (addBtn) {
        addBtn.addEventListener('click', function () {
            var count = parseInt(countInput.value, 10) || 1;
            if (count >= window.CASE_CONST.otoscopiaMaxFases) {
                showMsg('Ya se alcanzó el máximo de fases.', true);
                return;
            }
            container.appendChild(buildFaseBlock(count));
            countInput.value = String(count + 1);
            updateRemoveButtons();
        });
    }

    container.addEventListener('click', function (e) {
        var btn = e.target.closest('.otoscopia-remove-fase');
        if (!btn) { return; }
        var blocks = faseBlocks();
        var idx = parseInt(btn.getAttribute('data-fase-idx'), 10);
        if (idx !== blocks.length - 1 || idx === 0) { return; } // defensivo: solo la última, nunca la 1ª
        if (!confirm('¿Quitar la fase ' + (idx + 1) + '? Se borran también sus imágenes.')) { return; }

        var block = blocks[blocks.length - 1];
        if (CASE_ID) {
            ['od', 'oi'].forEach(function (side) {
                var fd = new FormData();
                fd.append('csrf_token', csrfToken());
                fd.append('case_id', CASE_ID);
                fd.append('side', side);
                fd.append('fase_idx', String(idx));
                fd.append('action', 'delete');
                fetch('otoscopia_photo_upload.php', { method: 'POST', body: fd }); // best-effort, no bloquea el UI
            });
        }
        block.remove();
        countInput.value = String(idx);
        updateRemoveButtons();
    });

    // Elegir archivo: delegado en el contenedor porque las fases agregadas
    // después no existían al cargar la página. Abre el modal de recorte en
    // vez de subir directo -- la subida real ocurre en cropConfirmBtn.
    container.addEventListener('change', function (e) {
        var input = e.target.closest('.otoscopia-photo-input');
        if (!input || !input.files || !input.files[0]) { return; }
        openCropModal(input, input.files[0]);
    });

    container.addEventListener('click', function (e) {
        var btn = e.target.closest('.otoscopia-delete-photo');
        if (!btn) { return; }
        if (!confirm('¿Borrar esta foto?')) { return; }
        var side = btn.getAttribute('data-side');
        var idx = btn.getAttribute('data-fase-idx');
        var slot = btn.closest('.otoscopia-photo-slot');
        var img = slot.querySelector('.otoscopia-thumb');
        var empty = slot.querySelector('.otoscopia-thumb-empty');
        var dlLink = slot.querySelector('.otoscopia-download-photo');

        var fd = new FormData();
        fd.append('csrf_token', csrfToken());
        fd.append('case_id', CASE_ID);
        fd.append('side', side);
        fd.append('fase_idx', idx);
        fd.append('action', 'delete');

        btn.disabled = true;
        fetch('otoscopia_photo_upload.php', { method: 'POST', body: fd })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                btn.disabled = false;
                if (data.ok) {
                    img.hidden = true;
                    img.removeAttribute('src');
                    empty.hidden = false;
                    btn.hidden = true;
                    if (dlLink) { dlLink.hidden = true; }
                    showMsg('Imagen borrada.', false);
                } else {
                    showMsg(data.error || 'No se pudo borrar la imagen.', true);
                }
            })
            .catch(function () {
                btn.disabled = false;
                showMsg('Error de red al borrar la imagen.', true);
            });
    });

    updateRemoveButtons();
})();
