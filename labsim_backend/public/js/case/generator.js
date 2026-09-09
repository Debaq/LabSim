// Generador del caso: un solo botón escribe el audiograma completo, el
// timpanograma, la función tubaria, el sitio de la lesión, el patrón
// retrococlear, las ondas del ABR y las emisiones -- todo coherente entre sí.
//
// Antes eran cuatro botones en cuatro pasos, cada uno pidiendo una decisión
// que ya estaba tomada (el grado de la OEA aparte del audiograma, por
// ejemplo) y sin mostrar resultado hasta el final. Elegir dos veces lo mismo
// era además la forma más fácil de dejar un caso que se contradice solo.
//
// El catálogo se serializa desde CaseProfile::SCENARIOS, no se re-tipea acá.
(function () {
    var ESCENARIOS = window.CASE_CONST.escenarios;
    var CATEGORIAS = window.CASE_CONST.categorias;
    var NEURAL_DEFAULTS = window.CASE_CONST.neuralDefaults;
    var GRADES = window.CASE_CONST.grades;
    var GRADE_FREQS = window.CASE_CONST.gradeFreqs;
    var ISO7029 = window.CASE_CONST.iso7029;
    var ISO7029_EDAD_BASE = window.CASE_CONST.iso7029EdadBase;
    var FREQS = window.CASE_CONST.freqs;
    var AUTO_MODULES = window.CASE_CONST.autoModules;
    // Banco compartido con la app de escritorio (resources/names.json, fuera
    // de public/: no se puede pedir por HTTP, viaja serializado acá).
    var NOMBRES = window.CASE_CONST.nombres;
    var JITTER_DB = 4;   // ruido por frecuencia: ningún audiograma real es liso
    // Techo de la audiometría. Si una frecuencia del promedio satura, subir
    // más la escala ya no sube el promedio: el grado pedido no se alcanza y
    // el cuadro se aplana.
    var MAX_DB = 115;

    var boton = document.getElementById('perfil-generar');
    var estado = document.getElementById('armado-estado');
    var igualar = document.getElementById('armado-igualar');
    var tablaNorma = document.getElementById('armado-norma-edad');
    var categorias = {}, selectores = {}, grados = {};
    document.querySelectorAll('.perfil-categoria').forEach(function (s) { categorias[s.dataset.lado] = s; });
    document.querySelectorAll('.perfil-escenario').forEach(function (s) { selectores[s.dataset.lado] = s; });
    document.querySelectorAll('.perfil-grado').forEach(function (s) { grados[s.dataset.lado] = s; });
    if (!boton || !selectores.od || !selectores.oi) return;

    function entre(a, b) { return a + Math.random() * (b - a); }
    function aCinco(x) { return Math.max(0, Math.min(120, Math.round(x / 5) * 5)); }
    function alAzar(lista) { return lista[Math.floor(Math.random() * lista.length)]; }

    /**
     * Nombre al azar según el sexo elegido.
     *
     * Solo en creación: al editar, los campos son `nombre`/`apellido` y
     * escriben sobre el PACIENTE, así que regenerarlos le cambiaría el nombre
     * en todas sus otras citas. Ahí se deja lo que haya.
     */
    function generarNombre() {
        var n1 = document.querySelector('#case-form [name="nombre1"]');
        if (!n1) { return null; }   // modo edición
        var pila = generoActual() === 1 ? NOMBRES.nombres_mujeres : NOMBRES.nombres_hombres;
        var apellidos = NOMBRES.apellidos;
        if (!pila || !pila.length || !apellidos || !apellidos.length) { return null; }

        function dosDistintos(lista) {
            var a = alAzar(lista);
            var resto = lista.filter(function (x) { return x !== a; });
            return [a, resto.length ? alAzar(resto) : a];
        }
        var nom = dosDistintos(pila);
        var ape = dosDistintos(apellidos);
        var campos = { nombre1: nom[0], nombre2: nom[1], apellido1: ape[0], apellido2: ape[1] };
        Object.keys(campos).forEach(function (k) {
            var el = document.querySelector('#case-form [name="' + k + '"]');
            if (el) { el.value = campos[k]; }
        });
        return nom[0] + ' ' + ape[0];
    }

    /**
     * Agrega la madre cuando el paciente es menor de edad.
     *
     * Un menor no llega solo a la consulta, y el acompañante aporta lo que el
     * niño no puede contar por más que hable bien: embarazo, parto, screening
     * neonatal, hitos del desarrollo, cómo le va en el colegio. Sin esto el
     * alumno se encontraba con un paciente de 10 años que cuenta la mitad de
     * su historia y nadie que cuente la otra mitad.
     *
     * Quién lleva la voz cantante depende de la edad (ver Sala::capacidad):
     * hasta los 13 la historia la cuenta la madre y el niño aporta; de 14 a
     * 17 la cuenta el paciente y la madre completa.
     *
     * NO toca una sala que ya tenga gente: volver a apretar Generar para
     * resortear el audiograma no puede borrar una sala armada a mano.
     */
    function agregarAcompanante(apellido) {
        var edad = edadActual();
        if (edad >= 18) { return null; }
        var filas = document.getElementById('sala-rows');
        var addBtn = document.getElementById('sala-add');
        if (!filas || !addBtn || filas.querySelector('.sala-row')) { return null; }

        addBtn.click();   // reusa la plantilla y el id de persona del bloque de Sala
        var row = filas.querySelector('.sala-row:last-child');
        if (!row) { return null; }

        function set(name, valor) {
            var el = row.querySelector('[name="' + name + '"]');
            if (el) { el.value = valor; }
        }
        var nombres = NOMBRES.nombres_mujeres || [];
        var nombre = nombres.length ? alAzar(nombres) : 'Madre';
        set('sala_rol[]', 'madre');
        set('sala_nombre[]', apellido ? nombre + ' ' + apellido : nombre);
        set('sala_genero[]', '1');
        // La madre de un niño de 10 no tiene 10 + 2 años: el rango sale de
        // una edad materna plausible al momento del parto.
        set('sala_edad[]', String(edad + Math.round(entre(25, 38))));
        // Cuánto se mete y cuánto le creemos varían en cada generación: dos
        // casos del mismo cuadro tienen que dar entrevistas distintas, si no
        // el alumno memoriza la dinámica en vez de leerla.
        set('sala_interrumpe[]', String(Math.round(entre(25, 85))));
        set('sala_confiabilidad[]', String(Math.round(entre(60, 95))));

        // Hasta los 13 la historia la cuenta ella; de 14 a 17 el paciente.
        if (edad <= 13) {
            var radio = row.querySelector('input[name="sala_informante"]');
            if (radio) { radio.checked = true; }
        }
        return nombre;
    }

    function edadActual() {
        var el = document.getElementById('patient-age');
        var n = el ? parseInt(el.value, 10) : NaN;
        return isNaN(n) ? 30 : Math.max(0, n);
    }
    function generoActual() {
        var chk = document.querySelector('#case-form input[name="gender"]:checked');
        return chk && chk.value === '1' ? 1 : 0;
    }

    /**
     * Umbral mediano esperable a esta edad (ISO 7029), por frecuencia.
     * Misma fórmula que CaseProfile::ageNorm -- si se toca una, tocar la otra.
     */
    function normaEdad() {
        var delta = Math.max(0, edadActual() - ISO7029_EDAD_BASE);
        var cuadrado = delta * delta;
        var idx = generoActual() === 1 ? 1 : 0;
        var out = {};
        FREQS.forEach(function (hz) {
            var c = ISO7029[hz];
            out[hz] = c ? c[idx] * 0.001 * cuadrado : 0;
        });
        return out;
    }

    function escribir(clave, lado, valores) {
        for (var n = 0; n < FREQS.length; n++) {
            var el = document.getElementById(clave + '_' + lado + '_' + n);
            if (el) { el.value = valores[n]; }
        }
    }

    // --- Grado -------------------------------------------------------------
    // El promedio se mide sobre la curva AÉREA final, que es la norma por edad
    // más la forma escalada. Como la norma no depende de la escala, el factor
    // sale de una ecuación lineal en vez de a tanteo:
    //     BIAP(norma) + k * BIAP(forma) = objetivo
    function promedioDe(fn) {
        var suma = 0;
        GRADE_FREQS.forEach(function (hz) { suma += fn(hz); });
        return suma / GRADE_FREQS.length;
    }
    function formaAerea(esc, escalas, hz) {
        return (esc.sn_shape[hz] || 0) * escalas.sn + ((esc.gap_shape || {})[hz] || 0) * escalas.gap;
    }

    /** Hasta dónde puede escalarse sin que sature una frecuencia DEL promedio. */
    function techoDe(esc, escalas, norma) {
        var peorForma = 0, peorNorma = 0, biapForma, biapNorma;
        GRADE_FREQS.forEach(function (hz) {
            var f = formaAerea(esc, escalas, hz);
            if (f > peorForma) { peorForma = f; peorNorma = norma[hz] || 0; }
        });
        biapForma = promedioDe(function (hz) { return formaAerea(esc, escalas, hz); });
        biapNorma = promedioDe(function (hz) { return norma[hz] || 0; });
        var porSaturacion = peorForma > 0
            ? biapNorma + biapForma * ((MAX_DB - peorNorma) / peorForma)
            : Infinity;
        return Math.min(porSaturacion, esc.max_db || Infinity);
    }

    /** Opciones de grado del cuadro elegido (las que ese cuadro puede dar). */
    function sincronizarGrados(lado) {
        var sel = grados[lado];
        if (!sel) { return; }
        var esc = ESCENARIOS[selectores[lado].value];
        var lista = (esc && esc.grados) || [];
        var previo = sel.value;
        var html = '<option value="random">Cualquiera (al azar)</option>';
        lista.forEach(function (clave) {
            if (GRADES[clave]) { html += '<option value="' + clave + '">' + GRADES[clave].label + '</option>'; }
        });
        sel.innerHTML = html;
        sel.value = lista.indexOf(previo) !== -1 ? previo : 'random';
        // Un oído sano no tiene grado de hipoacusia: el cuadro 'normal' no
        // trae ninguno y el select queda apagado en vez de ofrecer una lista
        // vacía que igual se puede desplegar.
        sel.disabled = lista.length === 0;
        sel.style.opacity = lista.length === 0 ? '0.6' : '';
        sel.title = lista.length === 0 ? 'Este cuadro no tiene grado de hipoacusia' : '';
    }

    /** Cuadros de la categoría elegida. */
    function sincronizarCuadros(lado) {
        var sel = selectores[lado];
        var cat = categorias[lado] ? categorias[lado].value : '__random__';
        var previo = sel.value;
        var html = '';
        var hay = [];
        Object.keys(ESCENARIOS).forEach(function (clave) {
            if (cat !== '__random__' && ESCENARIOS[clave].categoria !== cat) { return; }
            hay.push(clave);
            html += '<option value="' + clave + '">' + ESCENARIOS[clave].label + '</option>';
        });
        if (hay.length > 1) { html += '<option value="__random__">Cualquiera (al azar)</option>'; }
        sel.innerHTML = html;
        sel.value = hay.indexOf(previo) !== -1 ? previo : (hay[0] || '');
        sincronizarGrados(lado);
    }

    /**
     * Corrige las escalas para que el promedio BIAP caiga en el grado pedido.
     *
     * El factor es UNO SOLO para las dos escalas: la proporción entre el
     * componente conductivo y el sensorioneural la define el cuadro, no el
     * grado. Escalando solo lo sensorioneural, subirle el grado a una
     * conductiva la convertiría en una mixta.
     *
     * `asimetria` son los dB que se le van a sumar DESPUÉS a este oído: se
     * descuentan del objetivo, porque si no un "leve" con 8 dB de asimetría
     * terminaba midiendo como moderada.
     */
    function ajustarAlGrado(esc, escalas, claveGrado, asimetria, norma) {
        var lista = esc.grados || [];
        if (!lista.length) { return escalas; }
        var clave = claveGrado;
        if (clave === 'random' || lista.indexOf(clave) === -1) { clave = alAzar(lista); }

        // El objetivo se busca DENTRO del rango: el jitter por frecuencia y el
        // redondeo a 5 corren el promedio final unos dB, y un "leve" apuntado
        // a 40 terminaba midiendo 45, o sea moderada.
        var rango = GRADES[clave].rango;
        var margen = Math.min(JITTER_DB + 1, (rango[1] - rango[0]) / 4);
        var min = rango[0] + margen - asimetria;
        var max = Math.min(rango[1] - margen, techoDe(esc, escalas, norma)) - asimetria;
        var objetivo = max <= min ? Math.max(min, max) : entre(min, max);

        var biapNorma = promedioDe(function (hz) { return norma[hz] || 0; });
        var biapForma = promedioDe(function (hz) { return formaAerea(esc, escalas, hz); });
        if (biapForma < 1) { return escalas; }
        // Con la norma por edad ya por encima del objetivo el factor daría
        // negativo: un cuadro no puede dejar al paciente oyendo MEJOR que su
        // mediana por edad. Se deja el mínimo y el grado real sale mayor al
        // pedido, que es la verdad clínica.
        var factor = Math.max(0.05, (objetivo - biapNorma) / biapForma);
        return { sn: escalas.sn * factor, gap: escalas.gap * factor };
    }

    function escalasDe(esc) {
        return {
            sn: entre(esc.sn_scale[0], esc.sn_scale[1]),
            gap: entre(esc.gap_scale[0], esc.gap_scale[1])
        };
    }

    function generarLado(esc, lado, escalas, asimetria, norma) {
        // La curva final = umbral mediano por edad + forma del cuadro. Un
        // señor de 70 con una otitis tiene la otitis Y su presbiacusia.
        var sn = FREQS.map(function (hz) {
            return (norma[hz] || 0) + (esc.sn_shape[hz] || 0) * escalas.sn
                 + entre(-JITTER_DB, JITTER_DB) + asimetria;
        });
        var gap = FREQS.map(function (hz) {
            if (!esc.gap_shape || !Object.keys(esc.gap_shape).length) { return 0; }
            return (esc.gap_shape[hz] || 0) * escalas.gap + entre(-JITTER_DB, JITTER_DB);
        });

        var osea = sn.map(aCinco);
        var aerea = sn.map(function (v, i) { return aCinco(v + Math.max(0, gap[i])); });
        // La ósea nunca puede quedar peor que la aérea después de redondear.
        osea = osea.map(function (v, i) { return Math.min(v, aerea[i]); });
        escribir('aerea', lado, aerea);
        escribir('osea', lado, osea);
        // "Igualar ósea a aérea" pisaría la ósea recién generada al guardar.
        var ig = document.querySelector('.igualar-toggle[data-side="' + lado + '"]');
        if (ig && ig.checked && gap.some(function (g) { return g > 0; })) { ig.checked = false; }

        // Oído medio: el gap y el timpanograma tienen que contar la misma
        // historia. Sin esto una conductiva salía con 35 dB de gap y curva A.
        var z = document.getElementById('z_' + lado);
        if (z) { z.value = alAzar(esc.z && esc.z.length ? esc.z : ['A']); }
        var etf = document.querySelector('select[name="etf_' + lado + '"]');
        if (etf) { etf.value = esc.etf || 'Normal'; }

        var cce = document.querySelector('input[name="perfil[' + lado + '][cce_pct]"]');
        if (cce) { cce.value = Math.round(entre(esc.cce_pct[0], esc.cce_pct[1]) / 5) * 5; }

        // Patrón retrococlear. Sin `retro` hay que LIMPIARLO a los defaults:
        // pedir "OI normal" después de un schwannoma dejaba los interpicos
        // prolongados de la vuelta anterior en un oído recién declarado sano.
        // No se puede con el preset ("normal" no existe en ABR_NEURAL_PRESETS).
        var sel = document.querySelector('.abr-neural-preset-select[data-lado="' + lado + '"]');
        var btn = document.querySelector('.abr-neural-preset-btn[data-lado="' + lado + '"]');
        var nota = document.querySelector('.abr-neural-preset-nota[data-lado="' + lado + '"]');
        if (esc.retro && sel && btn) {
            sel.value = esc.retro;
            btn.click();
        } else {
            Object.keys(NEURAL_DEFAULTS).forEach(function (param) {
                var el = document.querySelector(
                    '.abr-neural-input[data-lado="' + lado + '"][data-param="' + param + '"]');
                if (el) { el.value = NEURAL_DEFAULTS[param]; }
            });
            if (sel) { sel.value = ''; }
            if (nota) { nota.textContent = ''; }
        }
    }

    /** Cuadro elegido para un oído, resolviendo "Cualquiera (al azar)". */
    function escenarioDe(lado) {
        var cat = categorias[lado];
        if (cat && cat.value === '__random__') {
            cat.value = alAzar(Object.keys(CATEGORIAS));
            sincronizarCuadros(lado);
        }
        var sel = selectores[lado];
        if (sel.value === '__random__') {
            var opciones = [].slice.call(sel.options)
                .map(function (o) { return o.value; })
                .filter(function (v) { return v !== '__random__'; });
            sel.value = alAzar(opciones);   // el docente tiene que ver qué salió
            sincronizarGrados(lado);
        }
        return ESCENARIOS[sel.value] ? sel.value : null;
    }

    // --- Cableado de los selectores ----------------------------------------
    ['od', 'oi'].forEach(function (lado) {
        var otro = lado === 'od' ? 'oi' : 'od';
        function espejar() {
            if (!igualar || !igualar.checked || lado !== 'od') { return; }
            if (categorias[otro]) { categorias[otro].value = categorias.od.value; }
            sincronizarCuadros(otro);
            selectores[otro].value = selectores.od.value;
            sincronizarGrados(otro);
            if (grados[otro] && grados.od) { grados[otro].value = grados.od.value; }
        }
        if (categorias[lado]) {
            categorias[lado].addEventListener('change', function () {
                sincronizarCuadros(lado);
                espejar();
            });
        }
        selectores[lado].addEventListener('change', function () {
            sincronizarGrados(lado);
            // Sugerencia para el otro oído cuando NO están igualados (ver
            // `lateralidad`): un cuadro unilateral propone dejar el contrario
            // normal, uno bilateral propone repetirlo.
            if (igualar && igualar.checked) { espejar(); return; }
            var esc = ESCENARIOS[selectores[lado].value];
            if (!esc || !categorias[otro]) { return; }
            if (esc.lateralidad === 'unilateral') {
                categorias[otro].value = 'normal';
                sincronizarCuadros(otro);
            }
        });
        if (grados[lado]) { grados[lado].addEventListener('change', espejar); }
    });
    if (igualar) {
        igualar.addEventListener('change', function () {
            document.querySelectorAll('.side-block[data-lado="oi"] select').forEach(function (s) {
                s.disabled = igualar.checked || (s.classList.contains('perfil-grado') && s.disabled);
                s.style.opacity = igualar.checked ? '0.6' : '';
            });
            if (igualar.checked) { categorias.od.dispatchEvent(new Event('change', { bubbles: true })); }
        });
    }

    /** Tabla de lo que es normal a esta edad, para que se vea antes de generar. */
    function pintarNorma() {
        if (!tablaNorma) { return; }
        var norma = normaEdad();
        var cols = [500, 1000, 2000, 4000, 8000];
        var html = '<table class="reflex-pattern-table" style="margin-top:0.4rem;"><thead><tr><th>Umbral normal a los ' +
                   edadActual() + ' años</th>';
        cols.forEach(function (hz) { html += '<th>' + (hz >= 1000 ? (hz / 1000) + ' k' : hz) + '</th>'; });
        html += '</tr></thead><tbody><tr><td>dB HL (mediana ISO 7029)</td>';
        cols.forEach(function (hz) { html += '<td>' + Math.round(norma[hz] || 0) + '</td>'; });
        html += '</tr></tbody></table>';
        tablaNorma.innerHTML = html;
    }
    ['patient-age', 'armado-age'].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) { ['input', 'change'].forEach(function (ev) { el.addEventListener(ev, pintarNorma); }); }
    });
    document.querySelectorAll('#case-form input[name="gender"], #armado-gender').forEach(function (el) {
        el.addEventListener('change', pintarNorma);
    });

    // --- El botón ----------------------------------------------------------
    boton.addEventListener('click', function () {
        var claveOd = escenarioDe('od');
        var claveOi = escenarioDe('oi');
        if (!claveOd || !claveOi) { return; }
        var escOd = ESCENARIOS[claveOd], escOi = ESCENARIOS[claveOi];
        var gradoOd = grados.od ? grados.od.value : 'random';
        var gradoOi = grados.oi ? grados.oi.value : 'random';
        var norma = normaEdad();

        // Mismo cuadro Y mismo grado = un solo cálculo para el paciente.
        // Resolviendo cada oído por separado, una presbiacusia bilateral
        // moderada podía salir con 43 dB en un oído y 68 en el otro: una
        // asimetría enorme --que es un hallazgo, no ruido-- en un cuadro que
        // se define por ser simétrico.
        var simetrico = claveOd === claveOi && gradoOd === gradoOi;
        var peor = Math.random() < 0.5 ? 'od' : 'oi';
        var asimetria = simetrico ? entre(0, 8) : 0;

        if (simetrico) {
            // El objetivo se centra descontando media asimetría: un oído
            // queda arriba y el otro abajo, y el par cae dentro del grado.
            var esc = ajustarAlGrado(escOd, escalasDe(escOd), gradoOd, asimetria / 2, norma);
            generarLado(escOd, 'od', esc, peor === 'od' ? asimetria : 0, norma);
            generarLado(escOi, 'oi', esc, peor === 'oi' ? asimetria : 0, norma);
        } else {
            generarLado(escOd, 'od', ajustarAlGrado(escOd, escalasDe(escOd), gradoOd, 0, norma), 0, norma);
            generarLado(escOi, 'oi', ajustarAlGrado(escOi, escalasDe(escOi), gradoOi, 0, norma), 0, norma);
        }

        // Un caso generado nace coherente: las proyecciones se encienden.
        AUTO_MODULES.forEach(function (modulo) {
            var chk = document.querySelector('input[name="perfil[auto][' + modulo + ']"]');
            if (chk) {
                chk.checked = true;
                chk.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        // Ondas del ABR y condiciones de registro de la OEA: es lo único que
        // el perfil NO puede derivar del audiograma (morfología onda por onda,
        // ruido del paciente, sello de la sonda), y sin esto el caso se
        // guardaba con las ondas de un oído sano y CaseCompleteness lo
        // reclamaba. Va acá y no en un botón aparte: es parte de generar.
        document.querySelectorAll('.abr-autofill-btn, .eoas-autofill-btn').forEach(function (b) { b.click(); });

        if (window.drawAudiogram) { window.drawAudiogram(); }
        if (window.drawTympanogram) { window.drawTympanogram(); }
        if (window.drawReflexPattern) { window.drawReflexPattern(); }
        // La proyección va ÚLTIMA: pisa el tipo, el umbral y las desviaciones
        // de OEA y ABR con lo que dice el perfil, así el autofill de arriba
        // aporta solo lo que el perfil no describe.
        if (window.proyectarPerfil) { window.proyectarPerfil(); }

        var nombre = generarNombre();
        var apellido = document.querySelector('#case-form [name="apellido1"]');
        var madre = agregarAcompanante(apellido ? apellido.value : '');
        if (estado) {
            estado.textContent = 'Listo: ' + (nombre ? nombre + ' -- ' : '') +
                'OD ' + escOd.label + ', OI ' + escOi.label +
                (madre ? '. Es menor: viene con su madre (' + madre + '), revisá la pestaña Sala' : '') +
                '. Revisalo en Audiometría antes de guardar.';
        }
    });

    // --- Arranque ----------------------------------------------------------
    ['od', 'oi'].forEach(sincronizarCuadros);
    pintarNorma();
    if (igualar) { igualar.dispatchEvent(new Event('change', { bubbles: true })); }
})();
