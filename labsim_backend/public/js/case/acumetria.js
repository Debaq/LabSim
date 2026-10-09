// Acumetría (Rinne/Weber) auto -- espejo en JS de CaseBuilder::rinneAuto()/
// weberAuto(). Con el auto encendido escribe las 6 celdas mientras el
// docente tipea los umbrales tonales, y las deja editables: al guardar gana
// lo que quedó en pantalla (ver CaseForm, "acá gana lo posteado").
(function () {
    var RINNE_GAP = window.CASE_CONST.rinneGap;
    var RINNE_FALSO_NEG = window.CASE_CONST.rinneFalsoNegAerea;
    var WEBER_ASYM = window.CASE_CONST.weberAsym;
    var FREQ_IDX = window.CASE_CONST.acumetriaFreqIdx;

    function threshold(kind, side, n) {
        var el = document.getElementById(kind + '_' + side + '_' + n);
        return el ? (parseInt(el.value, 10) || 0) : 0;
    }
    function rinneAuto(air, bone, boneOtro) {
        if ((air - bone) >= RINNE_GAP) return 'negativo';
        if (air >= RINNE_FALSO_NEG && (air - boneOtro) >= RINNE_GAP && boneOtro < bone) return 'falso_negativo';
        return 'positivo';
    }
    function weberAuto(airOd, boneOd, airOi, boneOi) {
        var haciaOd = (Math.max(0, airOd - boneOd) - Math.max(0, airOi - boneOi)) + (boneOi - boneOd);
        if (Math.abs(haciaOd) < WEBER_ASYM) return 'centrado';
        return haciaOd > 0 ? 'od' : 'oi';
    }

    /**
     * Ningún diapasón queda bloqueado, ni con el auto encendido: el auto
     * muestra el cálculo, no lo impone, y al guardar gana lo que quedó en
     * pantalla. Se fuerza acá además de en la vista porque un select
     * `disabled` tampoco se postea, así que dejarlo bloqueado no es solo
     * incómodo: es perder lo que el docente escribió.
     */
    function desbloquear() {
        FREQ_IDX.forEach(function (n) {
            ['od', 'oi'].forEach(function (side) {
                var r = document.getElementById('rinne_' + n + '_' + side);
                if (r) { r.disabled = false; }
            });
            var w = document.getElementById('weber_' + n);
            if (w) { w.disabled = false; }
        });
    }

    function syncAll() {
        var auto = document.getElementById('acumetria-auto-toggle');
        var isAuto = !!(auto && auto.checked);
        desbloquear();
        var cambio = false;
        function escribir(select, valor) {
            if (!select || select.value === valor) { return; }
            select.value = valor;
            cambio = true;
        }
        FREQ_IDX.forEach(function (n) {
            ['od', 'oi'].forEach(function (side) {
                var select = document.getElementById('rinne_' + n + '_' + side);
                if (!select || !isAuto) return;
                var otro = side === 'od' ? 'oi' : 'od';
                escribir(select, rinneAuto(threshold('aerea', side, n), threshold('osea', side, n),
                    threshold('osea', otro, n)));
            });
            var weberSelect = document.getElementById('weber_' + n);
            if (!weberSelect || !isAuto) return;
            escribir(weberSelect, weberAuto(threshold('aerea', 'od', n), threshold('osea', 'od', n),
                threshold('aerea', 'oi', n), threshold('osea', 'oi', n)));
        });
        // La acumetría vive en Audiometría, pero la reescriben umbrales que
        // se tipean en cualquier lado (el generador, por ejemplo).
        if (cambio && window.avisarCambioAutomatico) {
            window.avisarCambioAutomatico(['audiometria'], 'la acumetría automática se recalculó');
        }
    }

    var acumetriaAutoToggle = document.getElementById('acumetria-auto-toggle');
    if (acumetriaAutoToggle) { acumetriaAutoToggle.addEventListener('change', syncAll); }
    FREQ_IDX.forEach(function (n) {
        ['od', 'oi'].forEach(function (side) {
            var a = document.getElementById('aerea_' + side + '_' + n);
            var o = document.getElementById('osea_' + side + '_' + n);
            if (a) a.addEventListener('input', syncAll);
            if (o) o.addEventListener('input', syncAll);
        });
    });
    syncAll();
})();
