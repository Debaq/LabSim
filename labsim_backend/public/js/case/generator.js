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
    var SCENARIO_EDAD = window.CASE_CONST.scenarioEdad || {};
    var SCENARIO_NEONATAL = window.CASE_CONST.scenarioNeonatal || [];
    var CATEGORIAS = window.CASE_CONST.categorias;
    var NEURAL_DEFAULTS = window.CASE_CONST.neuralDefaults;
    var GRADES = window.CASE_CONST.grades;
    var GRADE_FREQS = window.CASE_CONST.gradeFreqs;
    var ISO7029 = window.CASE_CONST.iso7029;
    var ISO7029_EDAD_BASE = window.CASE_CONST.iso7029EdadBase;
    var FREQS = window.CASE_CONST.freqs;
    var AUTO_MODULES = window.CASE_CONST.autoModules;
    var VEMP_SUBTIPOS = window.CASE_CONST.vempSubtipos || [];
    var VEMP_DEFAULTS = window.CASE_CONST.vempDefaults || {};
    var GRADE_FREQS_VEMP = window.CASE_CONST.gradeFreqs;
    // Banco compartido con la app de escritorio (resources/names.json, fuera
    // de public/: no se puede pedir por HTTP, viaja serializado acá).
    var NOMBRES = window.CASE_CONST.nombres;
    // Comportamientos de la madre que agrega el generador. Texto libre que
    // viaja al prompt del LLM: describe cómo se conduce en la entrevista,
    // no qué sabe (eso sale de la anamnesis y de su edad).
    var COMPORTAMIENTO_MADRE = [
        'atenta, contesta corto y espera a que le pregunten',
        'ansiosa, se adelanta y contesta por él antes de que termine',
        'cansada, viene de trabajar y quiere terminar rápido',
        'preocupada, trae fechas anotadas en el celular',
        'desconfiada, pregunta para qué sirve cada cosa',
        'conversadora, se va por las ramas y hay que traerla de vuelta',
        'callada, deja hablar al paciente y solo corrige lo que sabe',
        'insistente, repite lo que le preocupa hasta que le contestan'
    ];
    var JITTER_DB = 4;   // ruido por frecuencia: ningún audiograma real es liso
    // Techo de la audiometría. Si una frecuencia del promedio satura, subir
    // más la escala ya no sube el promedio: el grado pedido no se alcanza y
    // el cuadro se aplana.
    var MAX_DB = 115;
    // Techo de la transmisión (CaseProfile::GAP_MAX_DB). El oído medio solo
    // puede dejar de aportar lo que aporta: anulado del todo, la vía ósea le
    // pone piso a la aérea y el gap se para ahí. Cada cuadro declara el suyo,
    // más bajo; este es el tope y el que rige si no lo declara.
    var GAP_MAX_DB = window.CASE_CONST.gapMaxDb || 60;

    /** Hasta dónde puede llegar el gap de este cuadro, en dB. */
    function techoGap(esc) {
        return Math.min(esc.gap_max_db || GAP_MAX_DB, GAP_MAX_DB);
    }

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
        // Comportamiento y sensibilidad van al prompt del LLM. Vacíos, la
        // madre contesta como una voz neutra y las tres o cuatro madres que
        // el alumno entrevista en el semestre son la misma persona.
        set('sala_comportamiento[]', alAzar(COMPORTAMIENTO_MADRE));
        set('sala_disposicion[]', alAzar(['0', '0', '1', '1', '-1', '2']));

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
    /**
     * Edad en años con decimales: la exacta manda cuando está cargada.
     *
     * `edadActual()` sigue devolviendo años enteros porque es lo que usan
     * la norma ISO 7029 y la madre de la sala. Acá hace falta el detalle:
     * un recién nacido de 8 horas y uno de 8 meses son los dos "0 años" y
     * no se les ofrecen los mismos cuadros.
     */
    function edadEnAnios() {
        var anios = edadActual();
        if (anios > 0) { return anios; }
        var val = document.getElementById('patient-edad-valor');
        var uni = document.getElementById('patient-edad-unidad');
        var n = val ? parseFloat(val.value) : NaN;
        if (isNaN(n)) { return 0; }
        var horas = n * ({ horas: 1, dias: 24, meses: 720 }[uni ? uni.value : 'horas'] || 1);
        return horas / 8760.0;
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
            if (!el) { continue; }
            el.value = valores[n];
            // Rinne/Weber y SDT/SRT se recalculan escuchando 'input' sobre
            // estos campos (ver case/acumetria.js y case/live-preview.js).
            // Escribir el .value en silencio los dejaba con los del caso
            // anterior: un audiograma nuevo con la acumetría del viejo.
            el.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }

    /**
     * Devuelve a "auto" lo que se calcula desde el audiograma: acumetría
     * (Rinne/Weber) y SDT/SRT por Fletcher.
     *
     * Hace falta sobre todo al EDITAR: caseDataToForm() deja esas casillas
     * apagadas a propósito, para que abrir un caso guardado no le pise los
     * valores. Pero acabamos de reescribir el audiograma entero, así que lo
     * que había medido sobre el anterior ya no describe a este paciente --
     * y con la casilla apagada el servidor tampoco lo recalcula al guardar.
     * Mismo criterio que las casillas del perfil: un caso generado nace
     * coherente, y el docente puede volver a apagarlas.
     */
    function encenderDerivadosDelAudiograma() {
        var casillas = [document.getElementById('acumetria-auto-toggle')];
        ['sdt', 'srt'].forEach(function (kind) {
            ['od', 'oi'].forEach(function (lado) {
                casillas.push(document.querySelector('#case-form [name="' + kind + '_auto[' + lado + ']"]'));
            });
        });
        casillas.forEach(function (chk) {
            if (!chk) { return; }
            chk.checked = true;
            chk.dispatchEvent(new Event('change', { bubbles: true }));
        });
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

    /**
     * Hasta dónde puede escalarse el cuadro, en dB de promedio BIAP.
     *
     * Tres topes, y manda el más bajo:
     *  - saturación: que no se pase de MAX_DB ninguna frecuencia DEL promedio;
     *  - `max_db`: el techo clínico del promedio que declara el cuadro;
     *  - el gap: que ninguna frecuencia pase de techoGap(). Este último hace
     *    falta porque el factor del grado escala la forma COMPLETA -- sin él,
     *    pedirle "moderada" a una otitis le ponía 68 dB de gap en 125 Hz para
     *    que el promedio llegara, y eso ya no es un oído medio, es un error.
     *    Se mide sobre TODAS las frecuencias, no solo las del promedio: el
     *    gap se desborda en los graves, que no entran en el BIAP.
     */
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
        var peorGap = 0;
        FREQS.forEach(function (hz) {
            peorGap = Math.max(peorGap, ((esc.gap_shape || {})[hz] || 0) * escalas.gap);
        });
        var porGap = peorGap > 0
            ? biapNorma + biapForma * (techoGap(esc) / peorGap)
            : Infinity;
        return Math.min(porSaturacion, porGap, esc.max_db || Infinity);
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

    /**
     * ¿Este cuadro existe a esta edad? Espejo de
     * CaseProfile::scenariosParaEdad -- si se toca una, tocar la otra.
     *
     * Sin esto, la lista le ofrecía presbiacusia, NIHL crónica y
     * otoesclerosis a un recién nacido con la misma prominencia que el
     * kernícterus, y los cuadros del turno del RN estaban perdidos entre
     * setenta.
     */
    function vaEnEstaEdad(clave, edad) {
        var r = SCENARIO_EDAD[clave];
        if (!r) { return true; }
        if (r[0] !== null && r[0] !== undefined && edad < r[0]) { return false; }
        if (r[1] !== null && r[1] !== undefined && edad > r[1]) { return false; }
        return true;
    }

    function esNeonatal(clave) {
        return SCENARIO_NEONATAL.indexOf(clave) !== -1;
    }

    /** Cuadros de la categoría elegida que existen a la edad cargada. */
    function sincronizarCuadros(lado) {
        var sel = selectores[lado];
        var cat = categorias[lado] ? categorias[lado].value : '__random__';
        var edad = edadEnAnios();
        var previo = sel.value;
        var hay = [];
        Object.keys(ESCENARIOS).forEach(function (clave) {
            if (cat !== '__random__' && ESCENARIOS[clave].categoria !== cat) { return; }
            if (!vaEnEstaEdad(clave, edad)) { return; }
            hay.push(clave);
        });
        // Menor de un año: primero los del turno del recién nacido.
        if (edad < 1) {
            hay.sort(function (a, b) {
                return (esNeonatal(a) ? 0 : 1) - (esNeonatal(b) ? 0 : 1);
            });
        }
        var html = '';
        var separado = false;
        hay.forEach(function (clave) {
            if (edad < 1 && !separado && !esNeonatal(clave) && html !== '') {
                html += '<option disabled>── menos habituales a esta edad ──</option>';
                separado = true;
            }
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
     *
     * Devuelve las escalas con `grado`: el grado que resolvió cuando venía
     * "al azar". Sin eso, afuera no hay forma de saber qué salió -- ni para
     * mostrarlo en el selector ni para nombrarlo en el comentario docente.
     */
    function ajustarAlGrado(esc, escalas, claveGrado, asimetria, norma) {
        var lista = esc.grados || [];
        if (!lista.length) { return escalas; }
        var clave = claveGrado;
        if (clave === 'random' || lista.indexOf(clave) === -1) { clave = alAzar(lista); }
        escalas.grado = clave;

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
        return { sn: escalas.sn * factor, gap: escalas.gap * factor, grado: clave };
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
        // El recorte es el que garantiza el techo: techoDe() ya mantiene el
        // grado dentro de lo posible, pero el jitter por frecuencia y una
        // norma por edad alta todavía podían empujar el gap un poco más
        // arriba de lo que ese oído medio puede atenuar.
        var gap = FREQS.map(function (hz) {
            if (!esc.gap_shape || !Object.keys(esc.gap_shape).length) { return 0; }
            var v = (esc.gap_shape[hz] || 0) * escalas.gap + entre(-JITTER_DB, JITTER_DB);
            return Math.min(v, techoGap(esc));
        });

        var osea = sn.map(aCinco);
        var aerea = sn.map(function (v, i) { return aCinco(v + Math.max(0, gap[i])); });
        // La ósea nunca puede quedar peor que la aérea después de redondear.
        osea = osea.map(function (v, i) { return Math.min(v, aerea[i]); });
        // "Igualar ósea a aérea" pisaría la ósea recién generada: su listener
        // copia la aérea encima de la ósea en cuanto ve un 'input', y
        // escribir() dispara uno. Por eso se apaga ANTES de escribir, con un
        // 'change' de verdad para que el resto del formulario se entere.
        var ig = document.querySelector('.igualar-toggle[data-side="' + lado + '"]');
        if (ig && ig.checked && gap.some(function (g) { return g > 0; })) {
            ig.checked = false;
            ig.dispatchEvent(new Event('change', { bubbles: true }));
        }
        escribir('aerea', lado, aerea);
        escribir('osea', lado, osea);

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

        generarVemp(esc, lado, gap);
    }

    /**
     * Acúfeno del caso, desde el eje `tinnitus` de los cuadros.
     *
     * El tinnitus es UNO por caso (no por oído), así que se resuelve acá
     * arriba con los dos cuadros a la vista. La lateralidad no sale del
     * catálogo sino de a cuántos oídos les tocó un cuadro con acúfeno: uno
     * da unilateral con ese oído, los dos dan bilateral.
     *
     * `prob` es probabilidad y no sí/no a propósito: dos casos del mismo
     * cuadro tienen que poder salir uno con acúfeno y otro sin, si no el
     * alumno aprende que "muesca en 4 kHz" implica acúfeno siempre. Con los
     * dos oídos en el mismo cuadro se sortea UNA vez para los dos, para que
     * un cuadro bilateral no dé un acúfeno de un solo lado por azar.
     *
     * Escribe siempre, incluso el caso sin acúfeno: sin la rama de apagado,
     * regenerar dejaba el tinnitus del caso anterior colgado.
     */
    function generarTinnitus(claveOd, claveOi) {
        var presente = document.getElementById('tinnitus-presente');
        if (!presente) { return null; }

        function toca(clave) {
            var cfg = ESCENARIOS[clave] && ESCENARIOS[clave].tinnitus;
            return cfg && Math.random() < cfg.prob ? cfg : null;
        }
        var cfgOd, cfgOi;
        if (claveOd === claveOi) {
            cfgOd = cfgOi = toca(claveOd);
        } else {
            cfgOd = toca(claveOd);
            cfgOi = toca(claveOi);
        }

        function set(campo, valor) {
            var el = document.querySelector('#case-form [name="tinnitus[' + campo + ']"]');
            if (el) { el.value = valor; }
        }
        function marcar(campo, valor) {
            var el = document.querySelector('#case-form [name="tinnitus[' + campo + ']"]');
            if (el) { el.checked = valor; }
        }

        var cfg = cfgOd || cfgOi;
        presente.checked = !!cfg;
        if (cfg) {
            if (cfgOd && cfgOi) {
                set('lateralidad', 'bilateral');
                set('predominio', 'igual');
            } else {
                set('lateralidad', 'unilateral');
                set('oido', cfgOd ? 'od' : 'oi');
            }
            set('ruido', alAzar(cfg.ruido));
            set('frecuencia', alAzar(cfg.frecuencia));
            marcar('permanente', Math.random() < cfg.permanente);
            // Pulsátil solo lo enciende el cuadro que lo explica: es un
            // acúfeno vascular, y sortearlo en cualquiera le enseñaría al
            // alumno que el pulso no significa nada. Sin la clave queda
            // apagado, y se marca a mano cuando el caso lo pide.
            marcar('pulsatil', Math.random() < (cfg.pulsatil || 0));
        }
        // El 'change' es lo que abre o cierra el bloque de campos y los
        // habilita para el POST (ver case/tinnitus.js).
        presente.dispatchEvent(new Event('change', { bubbles: true }));
        return cfg ? (cfgOd && cfgOi ? 'bilateral' : (cfgOd ? 'OD' : 'OI')) : null;
    }

    /**
     * Rasgos del paciente en la entrevista: cuánta conciencia tiene de su
     * problema y cuánto le podemos creer.
     *
     * Se sortean en vez de quedar en el default fijo (80/80): son dos de los
     * números que más cambian la conversación con el alumno, y calcados en
     * todos los casos la entrevista se memoriza. El rango de conciencia sale
     * del cuadro cuando el cuadro lo corre (ver SCENARIOS.conciencia); si
     * los dos oídos traen rango se toma el más bajo, que es el que manda:
     * alcanza con que un oído se haya instalado despacio para que el
     * paciente no lo note.
     */
    function generarRasgosPaciente(escOd, escOi) {
        var rangos = [escOd.conciencia, escOi.conciencia].filter(Boolean);
        var rango = [55, 90];
        if (rangos.length) {
            rango = rangos.reduce(function (a, b) { return a[0] <= b[0] ? a : b; });
        }
        var conc = document.querySelector('#case-form [name="paciente_conciencia"]');
        if (conc) { conc.value = Math.round(entre(rango[0], rango[1])); }
        var conf = document.querySelector('#case-form [name="paciente_confiabilidad"]');
        if (conf) { conf.value = Math.round(entre(55, 95)); }
    }

    /**
     * VEMP del oído, desde el eje vestibular del cuadro (SCENARIOS.vemp).
     *
     * Se escribe SIEMPRE, traiga el cuadro esa clave o no: sin la rama de
     * limpieza, pedir "OI normal" después de un schwannoma dejaba el oído
     * recién declarado sano con los umbrales desarmados de la vuelta
     * anterior -- el mismo problema que ya tenía el patrón retrococlear.
     *
     * `umbral_gap` es el caso de las conductivas: el VEMP aéreo no se apaga
     * por una lesión vestibular sino porque el oído medio no deja pasar el
     * estímulo, así que el umbral sube tanto como el gap que acabamos de
     * generar en vez de salir de un rango fijo.
     *
     * Tilda "ya decidí lo vestibular": el armado decidió, incluso cuando lo
     * que decidió es que el VEMP queda normal (ver CaseCompleteness).
     */
    function generarVemp(esc, lado, gap) {
        var cfg = esc.vemp || null;
        var tipo = cfg ? cfg.type : 'normal';

        var sel = document.querySelector('.vemp-type-select[data-lado="' + lado + '"]');
        if (sel) { sel.value = tipo; }

        // Gap promedio sobre las mismas frecuencias con las que se mide el
        // grado, y solo la parte positiva: un gap negativo es ruido de
        // redondeo, no un oído medio que atenúa.
        var gapMedio = 0;
        if (cfg && cfg.umbral_gap) {
            var suma = 0;
            GRADE_FREQS_VEMP.forEach(function (hz) {
                var i = FREQS.indexOf(hz);
                suma += i === -1 ? 0 : Math.max(0, gap[i] || 0);
            });
            gapMedio = suma / GRADE_FREQS_VEMP.length;
        }

        VEMP_SUBTIPOS.forEach(function (subtipo) {
            var base = (VEMP_DEFAULTS[subtipo] || {}).umbral || 60;
            var umbral;
            if (cfg && cfg.umbral && cfg.umbral[subtipo]) {
                umbral = entre(cfg.umbral[subtipo][0], cfg.umbral[subtipo][1]);
            } else if (cfg && cfg.umbral_gap) {
                umbral = base + gapMedio;
            } else {
                // Sin eje vestibular: normal, con la variabilidad de
                // cualquier oído sano en vez de un número calcado.
                umbral = base + entre(-5, 10);
            }
            var campo = document.querySelector(
                '#case-form [name="vemp[' + lado + '][' + subtipo + '][umbral]"]');
            if (campo) { campo.value = Math.round(Math.min(100, Math.max(30, umbral)) / 5) * 5; }

            // Las ondas vuelven a 0: la patología y el umbral ya describen
            // el cuadro, y dejar las desviaciones de la generación anterior
            // sumaría el efecto dos veces.
            ['p13', 'n23', 'n10', 'p16'].forEach(function (pico) {
                ['lat', 'amp'].forEach(function (campoOnda) {
                    var el = document.querySelector('#case-form [name="vemp[' + lado + '][' +
                        subtipo + '][' + campoOnda + '_' + pico + ']"]');
                    if (el) { el.value = '0'; }
                });
            });
        });
    }

    /**
     * Comentario del docente: qué cuadro representa el caso, en una línea.
     *
     * Es una nota privada del paciente --el alumno no la ve nunca-- y toda
     * la información ya está decidida acá arriba: cuadro, grado y lado.
     * Dejarla vacía obligaba a abrir la ficha entera y leer el audiograma
     * para saber qué era este caso; escribirla a mano era re-tipear lo que
     * el generador acababa de sortear.
     *
     * No dice para qué sirve el caso ni qué hay que enseñar con él: eso es
     * criterio del docente y lo escribe él encima. En cuanto toca el campo
     * queda marcado como suyo y Generar no lo vuelve a pisar.
     */
    function generarComentarioDocente(claveOd, gradoOd, claveOi, gradoOi) {
        var el = document.querySelector('#case-form [name="comentario_docente"]');
        if (!el || el.dataset.tocado === '1') { return; }

        function sufijoGrado(clave) {
            // El label trae el rango en dB ("Moderada (41-70 dB)"), que en
            // una nota de una línea sobra: el rango se lee del audiograma.
            if (!clave || !GRADES[clave]) { return ''; }
            return ', ' + GRADES[clave].label.replace(/\s*\(.*\)\s*$/, '').toLowerCase();
        }
        function frase(clave, grado) {
            return ESCENARIOS[clave].label + sufijoGrado(grado);
        }

        if (claveOd === 'normal' && claveOi === 'normal') {
            el.value = 'Ambos oídos normales para la edad.';
        } else if (claveOd === claveOi && gradoOd === gradoOi) {
            el.value = ESCENARIOS[claveOd].label + ' bilateral' + sufijoGrado(gradoOd) + '.';
        } else {
            el.value = 'OD: ' + frase(claveOd, gradoOd) + '. OI: ' + frase(claveOi, gradoOi) + '.';
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
    // "Los dos oídos iguales" copia el cuadro de OD en OI y nada más: los
    // selectores de OI siguen habilitados (antes quedaban disabled, y una
    // casilla que traba no es una sugerencia -- ver case/derived-fields.js).
    // Cambiar OD vuelve a espejar, así que la diferencia se carga después.
    if (igualar) {
        igualar.addEventListener('change', function () {
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
    /**
     * Recién nacido sin edad exacta: se sortea el turno.
     *
     * Con la edad en 0 y el campo vacío, el caso quedaba como "lactante de
     * 0 meses" --sin horas de vida, o sea sin transitorio de las primeras
     * horas y sin tamizaje--, que es justo el turno que se quería armar. Lo
     * que ya esté cargado NO se pisa: si el docente puso 6 horas y una
     * cesárea, manda él.
     */
    function completarRecienNacido() {
        if (edadActual() !== 0) { return; }
        var valor = document.getElementById('patient-edad-valor');
        if (!valor || valor.value !== '') { return; }
        var unidad = document.getElementById('patient-edad-unidad');
        // Entre 6 y 36 horas: la ventana del tamizaje antes del alta, que
        // es donde la EOA y el AABR dicen cosas distintas.
        valor.value = String(Math.round(entre(6, 36)));
        if (unidad) {
            unidad.value = 'horas';
            unidad.dispatchEvent(new Event('change', { bubbles: true }));
        }
        valor.dispatchEvent(new Event('input', { bubbles: true }));
        valor.dispatchEvent(new Event('change', { bubbles: true }));
        var semanas = document.querySelector('#case-form [name="nacimiento[semanas]"]');
        if (semanas && semanas.value === '') {
            semanas.value = String(Math.round(entre(37, 41)));
            semanas.dispatchEvent(new Event('change', { bubbles: true }));
        }
        var peso = document.querySelector('#case-form [name="nacimiento[peso_g]"]');
        if (peso && peso.value === '') {
            peso.value = String(Math.round(entre(2700, 3900) / 10) * 10);
            peso.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    boton.addEventListener('click', function () {
        var claveOd = escenarioDe('od');
        var claveOi = escenarioDe('oi');
        if (!claveOd || !claveOi) { return; }
        completarRecienNacido();
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

        var escalasOd, escalasOi;
        if (simetrico) {
            // El objetivo se centra descontando media asimetría: un oído
            // queda arriba y el otro abajo, y el par cae dentro del grado.
            escalasOd = ajustarAlGrado(escOd, escalasDe(escOd), gradoOd, asimetria / 2, norma);
            escalasOi = escalasOd;
            generarLado(escOd, 'od', escalasOd, peor === 'od' ? asimetria : 0, norma);
            generarLado(escOi, 'oi', escalasOi, peor === 'oi' ? asimetria : 0, norma);
        } else {
            escalasOd = ajustarAlGrado(escOd, escalasDe(escOd), gradoOd, 0, norma);
            escalasOi = ajustarAlGrado(escOi, escalasDe(escOi), gradoOi, 0, norma);
            generarLado(escOd, 'od', escalasOd, 0, norma);
            generarLado(escOi, 'oi', escalasOi, 0, norma);
        }
        // El grado que salió, en el selector: "Cualquiera (al azar)" no dice
        // con qué se armó el caso y el docente lo tiene que ver -- mismo
        // criterio que el cuadro en escenarioDe().
        ['od', 'oi'].forEach(function (lado) {
            var resuelto = (lado === 'od' ? escalasOd : escalasOi).grado;
            if (grados[lado] && resuelto) { grados[lado].value = resuelto; }
        });
        generarComentarioDocente(claveOd, escalasOd.grado, claveOi, escalasOi.grado);
        var tinnitus = generarTinnitus(claveOd, claveOi);
        generarRasgosPaciente(escOd, escOi);

        // Un caso generado nace coherente: las proyecciones se encienden.
        AUTO_MODULES.forEach(function (modulo) {
            var chk = document.querySelector('input[name="perfil[auto][' + modulo + ']"]');
            if (chk) {
                chk.checked = true;
                chk.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        // La acumetría y el SDT/SRT salen del audiograma que acabamos de
        // reescribir: vuelven a derivarse (ver la función para el porqué).
        encenderDerivadosDelAudiograma();

        if (window.drawAudiogram) { window.drawAudiogram(); }
        if (window.drawTympanogram) { window.drawTympanogram(); }
        if (window.drawReflexPattern) { window.drawReflexPattern(); }
        if (window.drawVempPreview) { window.drawVempPreview(); }

        // Proyección -> autofill -> proyección, y el orden importa en los dos
        // pasos.
        //
        // Las ondas del ABR y las condiciones de registro de la OEA son lo
        // único que el perfil NO puede derivar del audiograma (morfología
        // onda por onda, ruido del paciente, sello de la sonda), pero el
        // autofill las sortea POR PATOLOGÍA y la patología la decide la
        // proyección. Corriendo antes leía el selector todavía en "normal", y
        // un caso coclear terminaba con el umbral elevado del perfil y las
        // ondas de un oído sano -- una disociación que no existe y que el
        // alumno no tiene cómo resolver.
        //
        // La segunda proyección es porque el autofill escribe también el
        // umbral (y en la OEA las desviaciones), que son del perfil: se las
        // devuelve, y del autofill queda solo lo que el perfil no describe.
        var proyectar = window.proyectarPerfil || function () { return Promise.resolve(); };
        Promise.resolve(proyectar()).then(function () {
            ['od', 'oi'].forEach(function (lado) {
                // conservarNeural: el patrón retrococlear ya lo puso
                // generarLado desde el cuadro clínico.
                if (window.abrAutofill) { window.abrAutofill(lado, true); }
                if (window.eoasAutofill) { window.eoasAutofill(lado); }
            });
            return proyectar();
        });

        var nombre = generarNombre();
        var apellido = document.querySelector('#case-form [name="apellido1"]');
        var madre = agregarAcompanante(apellido ? apellido.value : '');

        // Lo que estaba dado por revisado era el caso anterior: este es
        // otro y hay que recorrerlo de nuevo. El Resumen no se entera solo
        // porque generar escribe los campos por código, sin disparar los
        // eventos que destildan la ficha que se edita a mano.
        if (window.resumenDestildarTodo) { window.resumenDestildarTodo(); }

        if (estado) {
            estado.textContent = 'Listo: ' + (nombre ? nombre + ' -- ' : '') +
                'OD ' + escOd.label + ', OI ' + escOi.label +
                (tinnitus ? '. Con acúfeno (' + tinnitus + ')' : '. Sin acúfeno') +
                (madre ? '. Es menor: viene con su madre (' + madre + '), revisá la pestaña Sala' : '') +
                '. Revisalo ficha por ficha en Resumen antes de guardar.';
        }
    });

    // --- Arranque ----------------------------------------------------------
    // Desde la primera tecla el comentario docente es suyo y Generar no lo
    // vuelve a pisar (ver generarComentarioDocente).
    var comentarioDocente = document.querySelector('#case-form [name="comentario_docente"]');
    if (comentarioDocente) {
        comentarioDocente.addEventListener('input', function () {
            comentarioDocente.dataset.tocado = '1';
        });
    }
    ['od', 'oi'].forEach(sincronizarCuadros);
    pintarNorma();
    if (igualar) { igualar.dispatchEvent(new Event('change', { bubbles: true })); }
})();
