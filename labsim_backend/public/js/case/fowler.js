// Filas de Fowler/I.W.A. por frecuencia -- espejo en JS de
// CaseBuilder::fowlerQualifyingFreqs()/fowlerValidationError() (PHP recalcula
// todo igual al enviar, esto es solo para que el docente vea en vivo en
// cuáles frecuencias calificó cada vez que cambia un umbral, y pueda elegir
// el patrón de reclutamiento en cada una sin perder lo ya elegido).
(function () {
    var table = document.getElementById('fowler-table');
    var container = document.getElementById('fowler-rows');
    var noneMsg = document.getElementById('fowler-none-msg');
    if (!table || !container) return;

    var NORMAL_HL = 20, GAP_MAX = 10, DIFF_MIN = 20, DIFF_MAX = 40;
    var FREQ_HZ = { 1: 250, 2: 500, 3: 1000, 4: 2000, 5: 3000, 6: 4000 }; // mismos índices que CaseBuilder::FREQUENCIES
    var FREQ_INDEXES = Object.keys(FREQ_HZ).map(Number);
    var PATTERNS = [
        ['none', 'Sin reclutamiento'],
        ['partial', 'Reclutamiento parcial'],
        ['complete', 'Reclutamiento completo'],
        ['over', 'Sobre-reclutamiento']
    ];
    var DEFAULT_PATTERN = 'none';

    function val(id) {
        var el = document.getElementById(id);
        return el ? (parseInt(el.value, 10) || 0) : 0;
    }

    function qualifyingFreqs() {
        var out = [];
        FREQ_INDEXES.forEach(function (i) {
            var od = val('aerea_od_' + i), oi = val('aerea_oi_' + i);
            var refSide = od <= oi ? 'od' : 'oi';
            var studySide = refSide === 'od' ? 'oi' : 'od';
            var refTh = refSide === 'od' ? od : oi;
            var studyTh = studySide === 'od' ? od : oi;
            var diff = studyTh - refTh;
            if (refTh > NORMAL_HL || studyTh <= NORMAL_HL || diff < DIFF_MIN || diff > DIFF_MAX) return;
            var boneStudy = val('osea_' + studySide + '_' + i);
            if (studyTh - boneStudy > GAP_MAX) return;
            out.push({ idx: i, diff: diff });
        });
        return out;
    }

    function rebuild() {
        // Preserva lo ya elegido en cada fila antes de reconstruir -- si
        // cambiar un umbral en OTRA frecuencia no debería resetear esta.
        var current = {};
        container.querySelectorAll('select[data-freq]').forEach(function (sel) {
            current[sel.dataset.freq] = sel.value;
        });

        var qualifying = qualifyingFreqs();
        container.innerHTML = '';

        qualifying.forEach(function (q) {
            var tr = document.createElement('tr');
            tr.dataset.freq = String(q.idx);

            var tdFreq = document.createElement('td');
            tdFreq.textContent = FREQ_HZ[q.idx] + ' Hz';
            tr.appendChild(tdFreq);

            var tdDiff = document.createElement('td');
            tdDiff.textContent = q.diff + ' dB';
            tr.appendChild(tdDiff);

            var tdSelect = document.createElement('td');
            var select = document.createElement('select');
            select.name = 'fowler_pattern[' + q.idx + ']';
            select.dataset.freq = String(q.idx);
            PATTERNS.forEach(function (p) {
                var opt = document.createElement('option');
                opt.value = p[0];
                opt.textContent = p[1];
                select.appendChild(opt);
            });
            select.value = current[q.idx] || DEFAULT_PATTERN;
            tdSelect.appendChild(select);
            tr.appendChild(tdSelect);

            container.appendChild(tr);
        });

        table.hidden = qualifying.length === 0;
        if (noneMsg) { noneMsg.hidden = qualifying.length > 0; }
    }

    FREQ_INDEXES.forEach(function (i) {
        ['aerea_od_', 'aerea_oi_', 'osea_od_', 'osea_oi_'].forEach(function (prefix) {
            var el = document.getElementById(prefix + i);
            if (el) el.addEventListener('input', rebuild);
        });
    });
    // "Igualar ósea a aérea" copia los valores por JS (sin disparar 'input'
    // en los campos de ósea) -- sin este listener aparte, activar el toggle
    // no actualizaba qué frecuencias calificaban hasta que se volvía a
    // tipear algo. Corre después del listener que hace la copia (registrado
    // antes en el archivo), así que ya lee los valores de ósea al día.
    document.querySelectorAll('.igualar-toggle').forEach(function (el) {
        el.addEventListener('change', rebuild);
    });
    rebuild();
})();
