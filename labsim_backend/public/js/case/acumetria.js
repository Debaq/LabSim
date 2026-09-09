// Acumetría (Rinne/Weber) auto -- espejo en JS de CaseBuilder::rinneAuto()/
// weberAuto() (PHP recalcula igual al enviar; esto es solo para que el
// docente vea el resultado en vivo mientras tipea los umbrales tonales).
(function () {
    var RINNE_GAP = window.CASE_CONST.rinneGap;
    var WEBER_ASYM = window.CASE_CONST.weberAsym;
    var FREQ_IDX = window.CASE_CONST.acumetriaFreqIdx;

    function threshold(kind, side, n) {
        var el = document.getElementById(kind + '_' + side + '_' + n);
        return el ? (parseInt(el.value, 10) || 0) : 0;
    }
    function rinneAuto(air, bone) {
        return (air - bone) >= RINNE_GAP ? 'negativo' : 'positivo';
    }
    function weberAuto(boneOd, boneOi) {
        if (Math.abs(boneOd - boneOi) < WEBER_ASYM) return 'centrado';
        return boneOd < boneOi ? 'od' : 'oi';
    }

    function syncAll() {
        var auto = document.getElementById('acumetria-auto-toggle');
        var isAuto = !!(auto && auto.checked);
        FREQ_IDX.forEach(function (n) {
            ['od', 'oi'].forEach(function (side) {
                var select = document.getElementById('rinne_' + n + '_' + side);
                if (!select) return;
                if (isAuto) {
                    select.value = rinneAuto(threshold('aerea', side, n), threshold('osea', side, n));
                }
                select.disabled = isAuto;
            });
            var weberSelect = document.getElementById('weber_' + n);
            if (!weberSelect) return;
            if (isAuto) {
                weberSelect.value = weberAuto(threshold('osea', 'od', n), threshold('osea', 'oi', n));
            }
            weberSelect.disabled = isAuto;
        });
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
