/**
 * Tablero de personas del curso (admin/courses.php).
 *
 * El tablero ES el roster: cada tarjeta es un alumno y la columna donde está
 * es su grupo (uno solo por curso, ver Courses::moveStudentToGroup). Las
 * tarjetas del panel "Matricular" son candidatos --alumnos activos fuera del
 * curso-- y se arrastran a una columna para matricularlos y ubicarlos en un
 * solo gesto; por eso el servidor las pinta con la MISMA estructura que una
 * tarjeta de miembro y solo cambia data-enroll: al matricular alcanza con
 * cambiar qué controles se ven, sin rearmar HTML desde acá ni recargar.
 *
 * Todo va contra group_move.php (JSON, no <form>), que valida acceso al
 * curso, matrícula (enroll=1) y que el grupo sea de ese curso.
 */
(function () {
    var board = document.getElementById('course_board');
    if (!board) return;

    var csrf = board.dataset.csrf;
    var courseId = board.dataset.courseId;
    var endpoint = board.dataset.endpoint || 'group_move.php';
    var errorBox = document.getElementById('board_error');
    var candidateList = document.getElementById('candidate_list');
    var dragged = null;

    function showError(msg) {
        if (!errorBox) return;
        errorBox.textContent = msg;
        errorBox.hidden = false;
    }

    function clearError() {
        if (errorBox) errorBox.hidden = true;
    }

    function updateCounts() {
        board.querySelectorAll('.group_column').forEach(function (col) {
            var label = col.querySelector('.group_count');
            if (label) label.textContent = col.querySelectorAll('.group_card').length;
        });
        var total = document.getElementById('candidate_total');
        if (total && candidateList) {
            total.textContent = candidateList.querySelectorAll('.group_card').length;
        }
        updateChecked();
    }

    function updateChecked() {
        var out = document.getElementById('candidate_count');
        if (!out) return;
        out.textContent = document.querySelectorAll('#candidate_list .candidate_check:checked').length;
    }

    /** Un candidato recién matriculado pasa a miembro: se va el checkbox, aparecen
     * las acciones de miembro. Los contadores de citas quedan en 0 hasta recargar,
     * que es la verdad: recién entra al curso. */
    function promoteToMember(card) {
        card.dataset.enroll = '0';
        card.querySelectorAll('.card-enroll-only').forEach(function (el) { el.hidden = true; });
        card.querySelectorAll('.card-member-only').forEach(function (el) { el.hidden = false; });
        var check = card.querySelector('.candidate_check');
        if (check) check.checked = false;
    }

    function move(card, zone, fromZone) {
        var groupId = zone.closest('.group_column').dataset.groupId;
        var enroll = card.dataset.enroll === '1';

        var body = new URLSearchParams();
        body.set('csrf_token', csrf);
        body.set('course_id', courseId);
        body.set('user_id', card.dataset.userId);
        body.set('group_id', groupId);
        if (enroll) body.set('enroll', '1');

        fetch(endpoint, { method: 'POST', body: body })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.ok) throw new Error(data.error || 'No se pudo mover al alumno.');
                if (enroll) promoteToMember(card);
            })
            .catch(function (err) {
                fromZone.appendChild(card);
                updateCounts();
                showError(err.message);
            });
    }

    document.addEventListener('dragstart', function (e) {
        var card = e.target.closest ? e.target.closest('.group_card') : null;
        dragged = card;
    });

    board.querySelectorAll('.group_dropzone').forEach(function (zone) {
        zone.addEventListener('dragover', function (e) {
            e.preventDefault();
            zone.classList.add('group_dropzone--over');
        });
        zone.addEventListener('dragleave', function () {
            zone.classList.remove('group_dropzone--over');
        });
        zone.addEventListener('drop', function (e) {
            e.preventDefault();
            zone.classList.remove('group_dropzone--over');
            if (!dragged) return;

            var fromZone = dragged.parentElement;
            if (fromZone === zone) return;

            clearError();
            zone.appendChild(dragged);
            updateCounts();
            move(dragged, zone, fromZone);
        });
    });

    // Devolver una tarjeta al panel = sacarla del grupo pero NO del curso:
    // para eso está la × de la tarjeta. Por eso el panel no acepta drops.

    var search = document.getElementById('people_search');
    if (search) {
        search.addEventListener('input', function () {
            var q = search.value.toLowerCase();
            document.querySelectorAll('.group_card').forEach(function (card) {
                card.hidden = q !== '' && card.dataset.search.indexOf(q) === -1;
            });
        });
    }

    document.querySelectorAll('[data-origin-select]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var label = btn.dataset.originSelect;
            document.querySelectorAll('#candidate_list .group_card').forEach(function (card) {
                if (card.dataset.origin !== label) return;
                card.hidden = false;
                var check = card.querySelector('.candidate_check');
                if (check) check.checked = true;
            });
            updateChecked();
        });
    });

    if (candidateList) {
        candidateList.addEventListener('change', function (e) {
            if (e.target.classList.contains('candidate_check')) updateChecked();
        });
    }

    // Renombrar grupo: el título se cambia por su input, sin diálogo del
    // navegador ni pantalla aparte. Escape cancela, Enter envía el form.
    board.querySelectorAll('[data-rename-toggle]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var head = btn.closest('.row');
            var title = head.querySelector('.group_title');
            var form = head.querySelector('.group_rename');
            if (!title || !form) return;
            title.hidden = true;
            form.hidden = false;
            var input = form.querySelector('input[name="name"]');
            input.focus();
            input.select();
            input.addEventListener('keydown', function (e) {
                if (e.key === 'Escape') {
                    form.hidden = true;
                    title.hidden = false;
                }
            });
        });
    });

    updateCounts();
})();
