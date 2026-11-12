// Exámenes que trae el paciente (ver ExamenesPrevios.php): agregar/quitar
// filas y la vista previa del informe. Cada fila se clona de la plantilla
// #previo-row-tpl, que dibuja PHP.
(function () {
    var container = document.getElementById('previo-rows');
    var tpl = document.getElementById('previo-row-tpl');
    var addBtn = document.getElementById('previo-add');
    if (!container || !tpl || !addBtn) { return; }

    // Mismos colores por lado que el audiograma (CaseCharts::COLOR_OD/OI).
    var COLOR = { OD: '#b33a3a', OI: '#2255aa' };
    var SERVICIO = 'Servicio de Otorrinolaringología · Unidad de Audiología';
    // Títulos que la app le pone a cada examen conocido
    // (informe_previo.TITULO); los demás van como los escribió el docente.
    var TITULO = {
        'audiometría': 'Audiometría tonal y logoaudiometría',
        'impedanciometría': 'Impedanciometría',
        'eoa': 'Emisiones otoacústicas',
        'peatc': 'Potenciales evocados auditivos de tronco cerebral',
        'ecochg': 'Electrococleografía',
        'vemp': 'Potenciales evocados miogénicos vestibulares',
        'corticales': 'Potenciales auditivos corticales'
    };

    function campo(name) {
        var el = document.querySelector('[name="' + name + '"]');
        return el ? el.value.trim() : '';
    }

    function esc(s) {
        return String(s).replace(/[&<>"]/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
        });
    }

    // 12345678 -> 12.345.678-5 (informe_previo.formato_rut).
    function formatoRut(rut) {
        if (!/^\d+$/.test(rut)) { return rut; }
        var suma = 0, factor = 2;
        for (var i = rut.length - 1; i >= 0; i--) {
            suma += parseInt(rut[i], 10) * factor;
            factor = factor === 7 ? 2 : factor + 1;
        }
        var dv = 11 - suma % 11;
        dv = dv === 11 ? '0' : (dv === 10 ? 'K' : String(dv));
        return parseInt(rut, 10).toLocaleString('es-CL') + '-' + dv;
    }

    // Lo que significa el resultado de un oído en un tamizaje
    // (informe_previo._dice / conclusion_tamizaje): la conclusión que arma
    // la app cuando el docente la deja vacía.
    function tipoTamizaje(prueba) {
        var p = prueba.toLowerCase();
        if (/emisi|eoa|oae|otoemis/.test(p)) { return 'eoa'; }
        if (/peat|aabr|automatiz|potencial|abr/.test(p)) { return 'aabr'; }
        return null;
    }
    function dice(tipo, resultado, nivel) {
        var r = resultado.trim().toLowerCase();
        if (tipo === 'eoa' && r === 'pasa') { return 'emisiones otoacústicas presentes (pasa)'; }
        if (tipo === 'eoa' && r === 'refiere') { return 'emisiones otoacústicas ausentes (refiere)'; }
        if (tipo === 'aabr' && r === 'pasa') { return 'respuesta presente' + nivel + ' (pasa)'; }
        if (tipo === 'aabr' && r === 'refiere') { return 'sin respuesta' + nivel + ' (refiere)'; }
        if (r === 'no evaluable') { return 'no evaluable'; }
        return resultado.trim() || '—';
    }
    function mayus(s) { return s.charAt(0).toUpperCase() + s.slice(1); }
    function conclusionAuto(prueba, od, oi) {
        var tipo = tipoTamizaje(prueba);
        var m = /(\d+)\s*dB\s*nHL/i.exec(prueba);
        var nivel = m && tipo === 'aabr' ? ' a ' + m[1] + ' dB nHL' : '';
        if (od.toLowerCase() === oi.toLowerCase()) {
            return [mayus(dice(tipo, od, nivel)) + ' en ambos oídos.'];
        }
        return ['OD: ' + mayus(dice(tipo, od, nivel)) + '.', 'OI: ' + mayus(dice(tipo, oi, nivel)) + '.'];
    }

    function dibujar(row) {
        var caja = row.querySelector('.previo-preview');
        if (!caja || caja.hidden) { return; }
        var val = function (n) {
            var el = row.querySelector('[name="' + n + '[]"]');
            return el ? el.value.trim() : '';
        };
        var prueba = val('prev_prueba');
        var od = val('prev_od');
        var oi = val('prev_oi');
        var dias = Math.abs(parseInt(val('prev_dias'), 10) || 0);
        var conclusion = val('prev_conclusion');

        var nombre = [campo('nombre1'), campo('nombre2'), campo('apellido1'), campo('apellido2')]
            .filter(Boolean).join(' ');
        var datos = [];
        if (nombre) { datos.push('Paciente: ' + nombre); }
        var edad = parseFloat(campo('age'));
        if (!isNaN(edad) && edad >= 1) {
            // La edad que tenía el día del examen, no la de la cita.
            var e = Math.floor(edad - dias / 365.25);
            datos.push('Edad: ' + e + ' año' + (e === 1 ? '' : 's'));
        }
        if (campo('rut')) { datos.push('RUT: ' + formatoRut(campo('rut'))); }
        datos.push('Fecha: ' + (dias ? dias + ' días antes de la cita' : 'la de la cita'));

        var bien = function (r) { return /^(pasa|normal)$/i.test(r); };
        var oido = function (lado, etiqueta, r) {
            return '<div class="ip-oido"><div class="ip-lado" style="color:' + COLOR[lado] + '">' + etiqueta + '</div>'
                + '<div class="ip-res" style="color:' + (bien(r) ? '#1F2933' : COLOR[lado]) + '">'
                + esc(r ? mayus(r) : '—') + '</div></div>';
        };
        // Audiometría e impedanciometría la app las dibuja con los datos del
        // caso (src/core/hoja_previa.py), no como tarjeta.
        var p = prueba.toLowerCase();
        var hoja = /audiometr/.test(p)
            ? 'Audiograma del caso (aérea, ósea, LDL, Fowler), logoaudiometría y SISI'
            : (/impedanciometr/.test(p) ? 'Timpanograma de cada oído y tabla de reflejos del caso' : null);
        var lineas = conclusion ? [conclusion]
            : (hoja ? ['La arma la app con los datos del caso.'] : conclusionAuto(prueba, od, oi));
        var cuerpo = hoja
            ? '<div class="ip-conclusion" style="margin:12px 0;text-align:center;color:#5B6670">' + esc(hoja) + '</div>'
            : '<div class="ip-oidos">' + oido('OD', 'Oído derecho', od) + oido('OI', 'Oído izquierdo', oi) + '</div>';

        caja.innerHTML =
            '<div class="ip-titulo">' + esc(TITULO[p] || prueba || 'Examen sin nombre') + '</div>'
            + '<div class="ip-servicio">' + SERVICIO + '</div>'
            + '<div class="ip-datos">' + esc(datos.join('   ·   ')) + '</div>'
            + cuerpo
            + '<div class="ip-conclusion"><strong>Conclusión</strong>'
            + lineas.map(function (l) { return '<div>' + esc(l) + '</div>'; }).join('') + '</div>'
            + '<div class="ip-firma">Firma: un tecnólogo médico ficticio que asigna la app, fijo por paciente.<br>'
            + 'La fecha real la pone la app según la cita.</div>';
    }

    addBtn.addEventListener('click', function () {
        var wrap = document.createElement('div');
        wrap.innerHTML = tpl.innerHTML;
        var row = wrap.querySelector('.previo-row');
        container.appendChild(row);
        var dias = row.querySelector('input[name="prev_dias[]"]');
        if (dias) { dias.focus(); }
    });

    container.addEventListener('click', function (e) {
        var row = e.target.closest('.previo-row');
        if (!row) { return; }
        if (e.target.classList.contains('previo-remove')) {
            row.remove();
        } else if (e.target.classList.contains('previo-ver')) {
            var caja = row.querySelector('.previo-preview');
            caja.hidden = !caja.hidden;
            e.target.textContent = caja.hidden ? 'Vista previa' : 'Ocultar vista previa';
            dibujar(row);
        }
    });

    // La vista previa abierta sigue lo que se escribe en la fila.
    container.addEventListener('input', function (e) {
        var row = e.target.closest('.previo-row');
        if (row) { dibujar(row); }
    });
})();
