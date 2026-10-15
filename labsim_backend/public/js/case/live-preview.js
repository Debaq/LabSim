// Ayuda visual en vivo -- el servidor recalcula todo igual al enviar,
// así que si JS falla el caso igual queda bien formado.
(function () {
    // Estos autocompletados escriben campos de Audiometría, casi siempre
    // desde otra pestaña (el generador de Armado rápido tipea la aérea):
    // ver case/auto-cambios.js.
    function avisar(motivo) {
        if (window.avisarCambioAutomatico) {
            window.avisarCambioAutomatico(['audiometria'], motivo);
        }
    }
    function pairAvgFloor5(a, b) {
        var vals = [a, b].sort(function (x, y) { return x - y; });
        var avg = (vals[0] + vals[1]) / 2;
        return Math.floor(avg / 5) * 5;
    }
    function fletcher(side) {
        var f500 = parseInt(document.getElementById('aerea_' + side + '_2').value, 10) || 0;
        var f1000 = parseInt(document.getElementById('aerea_' + side + '_3').value, 10) || 0;
        var f2000 = parseInt(document.getElementById('aerea_' + side + '_4').value, 10) || 0;
        var trio = [f500, f1000, f2000].sort(function (x, y) { return x - y; });
        return Math.floor(((trio[0] + trio[1]) / 2) / 5) * 5;
    }
    // Espejo de CaseBuilder::SDT_BAJO_SRT_DB / SDT_MIN_DB / sdtAuto(): el
    // SDT auto va 5 dB bajo el Fletcher (ASHA 1988: 8-9 dB bajo el SRT), y
    // un oído sin respuesta (130) sigue sin respuesta.
    var SDT_BAJO_SRT_DB = 5;
    var SDT_MIN_DB = -10;
    var SIN_RESPUESTA_DB = 130;
    function sdtAuto(f) {
        if (f >= SIN_RESPUESTA_DB) { return f; }
        return Math.max(SDT_MIN_DB, f - SDT_BAJO_SRT_DB);
    }

    ['od', 'oi'].forEach(function (side) {
        // "Igualar ósea a aérea" copia y nada más: la ósea queda editable
        // (antes quedaba readOnly, y una casilla que traba no es una
        // sugerencia -- ver case/derived-fields.js).
        var igualar = document.querySelector('.igualar-toggle[data-side="' + side + '"]');
        function syncOsea() {
            if (!igualar || !igualar.checked) return;
            var cambio = false;
            for (var n = 0; n < 9; n++) {
                var a = document.getElementById('aerea_' + side + '_' + n);
                var o = document.getElementById('osea_' + side + '_' + n);
                if (a && o) {
                    if (o.value !== a.value) { cambio = true; }
                    o.value = a.value;
                }
            }
            if (window.drawAudiogram) window.drawAudiogram();
            if (cambio) { avisar('"igualar ósea a aérea" reescribió la vía ósea'); }
        }
        if (igualar) {
            igualar.addEventListener('change', syncOsea);
            for (var n = 0; n < 9; n++) {
                var a = document.getElementById('aerea_' + side + '_' + n);
                if (a) { a.addEventListener('input', syncOsea); }
            }
            if (igualar.checked) { syncOsea(); }
        }

        var ldlToggle = document.querySelector('.ldl-toggle[data-side="' + side + '"]');
        function syncLdlOpacity() {
            if (!ldlToggle) return;
            for (var n = 0; n < 9; n++) {
                var el = document.getElementById('ldl_' + side + '_' + n);
                if (el) { el.style.opacity = ldlToggle.checked ? '1' : '0.4'; }
            }
        }
        if (ldlToggle) { ldlToggle.addEventListener('change', syncLdlOpacity); syncLdlOpacity(); }

        ['sdt', 'srt'].forEach(function (kind) {
            var auto = document.querySelector('.auto-toggle[data-target="' + kind + '-input"][data-side="' + side + '"]');
            var input = document.querySelector('.' + kind + '-input[data-side="' + side + '"]');
            function syncAuto() {
                if (!auto || !input) return;
                // Escribe el promedio de Fletcher y deja el campo editable:
                // el docente puede correr el SDT/SRT del promedio tonal (que
                // es justo el hallazgo de la simulación y del retrococlear).
                // El SDT auto va SDT_BAJO_SRT_DB bajo ese promedio.
                if (auto.checked) {
                    var nuevo = String(kind === 'sdt' ? sdtAuto(fletcher(side)) : fletcher(side));
                    if (input.value !== nuevo) {
                        input.value = nuevo;
                        avisar('el auto de Fletcher reescribió el ' + kind.toUpperCase());
                    }
                }
                if (window.drawLogogram) window.drawLogogram();
            }
            if (auto) {
                auto.addEventListener('change', syncAuto);
                for (var n = 2; n <= 4; n++) {
                    var a = document.getElementById('aerea_' + side + '_' + n);
                    if (a) { a.addEventListener('input', syncAuto); }
                }
                syncAuto();
            }
        });
    });
})();
