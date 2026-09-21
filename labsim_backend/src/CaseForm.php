<?php

declare(strict_types=1);

require_once __DIR__ . '/CaseBuilder.php';
require_once __DIR__ . '/CaseProfile.php';
require_once __DIR__ . '/CaseCompleteness.php';
require_once __DIR__ . '/CaseReview.php';
require_once __DIR__ . '/Sala.php';

/**
 * El POST del formulario de admin/case_create.php traducido a cases.data.
 *
 * Vivía dentro de la vista, así que la única forma de ejercitarlo era abrir
 * el navegador y guardar un caso: 600 líneas que deciden el audiograma, la
 * acumetría, el ABR, las EOA, el VEMP y qué le pisa la proyección del perfil
 * a cada uno, sin un solo test posible. Acá adentro no toca $_POST, ni
 * imprime, ni redirige -- recibe el array y devuelve el resultado.
 *
 * Lo que NO entra: el gate de form_action, requireCsrf y el guardado en la
 * base con su redirect. Eso es HTTP y sigue en la vista.
 */
final class CaseForm
{
    /** Mensaje de validación que bloquea el guardado; null si está todo bien. */
    public ?string $error = null;
    /** Incoherencias con el perfil auditivo: avisan, no bloquean (ver CaseProfile::warnings). */
    public array $avisos = [];
    /** Datos que faltan decidir; sí bloquean (ver CaseCompleteness::pending). */
    public array $faltantes = [];
    /** Fichas que nadie declaró revisadas; también bloquean (ver CaseReview). */
    public array $sinRevisar = [];
    /** cases.data listo para persistir; [] si no se llegó a armar. */
    public array $data = [];
    /** Id del caso: el que se editaba, o el que se reservó recién. '' si no se llegó. */
    public string $caseId = '';
    public bool $isUpdate = false;
    /** Los tres que el guardado necesita para el paciente_snapshot. */
    public int $age = 0;
    public string $nombre1 = '';
    public string $apellido1 = '';

    /**
     * Se guarda solo si no hay error, ni avisos sin confirmar, ni faltantes,
     * ni fichas sin revisar.
     */
    public function ok(): bool
    {
        return $this->error === null && $this->avisos === []
            && $this->faltantes === [] && $this->sinRevisar === [];
    }

    /** Lee un valor anidado de un array (ej. $v['aerea']['od'][3]) con default si falta. */
    public static function val(array $arr, array $path, $default = null)
    {
        $cur = $arr;
        foreach ($path as $p) {
            // isset() y no array_key_exists(): una clave presente en null
            // cuenta como ausente, que es lo que quiere el formulario (un
            // campo que no vino en el POST y uno que vino vacío dan igual).
            if (!is_array($cur) || !isset($cur[$p])) {
                return $default;
            }
            $cur = $cur[$p];
        }
        return $cur;
    }

    /** [od0,od1,...] + [oi0,oi1,...] -> [[od0,oi0],[od1,oi1],...] -- shape que espera cases.data. */
    public static function zip(array $od, array $oi): array
    {
        $out = [];
        foreach ($od as $i => $val) {
            $out[] = [$val, $oi[$i] ?? 0];
        }
        return $out;
    }

    /**
     * @param array $v      El $_POST crudo.
     * @param array $me     El admin de la sesión (queda como verificador del borrador de IA).
     * @param ?string $editId Id del caso que se edita; null al crear.
     */
    public static function fromPost(array $v, PDO $pdo, array $me, ?string $editId, bool $isUpdate): self
    {
        $f = new self();
        $f->isUpdate = $isUpdate;

        $error = null;
        $avisosPerfil = [];
        $faltantes = [];
        $sinRevisar = [];
        $data = [];
        $id = '';

        $gender = ($v['gender'] ?? '0') === '1' ? 1 : 0;
        // Edad = propia del paciente/caso, se guarda en cases.data ('edad').
        // Editable siempre acá, en creación y en edición -- la agenda no
        // incide en esto para nada, solo guarda la fecha de la cita.
        $age = max(0, (int) ($v['age'] ?? 0));
        // Horas de vida: solo tiene sentido en el primer año, y es lo que
        // decide si el caso es un recién nacido de turno de maternidad (con
        // su transitorio, ver CaseProfile::neonatalTransientDb) o un
        // lactante de ocho meses. La edad en años enteros no alcanza:
        // "0 años" mete en la misma bolsa un bebé de seis horas y uno de
        // once meses, que en pantalla no se parecen en nada.
        $horasVida = self::horasDeVida($v, $age);
        // Edad en meses: la calibración ósea del lactante se va con el cierre
        // de las suturas, que lleva un par de años -- no cabe en "horas de
        // vida" ni en años enteros.
        $edadMeses = $horasVida !== null ? $horasVida / 720.0 : $age * 12.0;
        // Circunstancias del parto: deciden cuánto refiere el screening (ver
        // NewbornScreening). Solo se guardan si el paciente es un recién
        // nacido; en un adulto no significan nada.
        $nacimiento = $horasVida !== null ? self::parseNacimiento($v) : [];
        $nombre1 = trim((string) ($v['nombre1'] ?? ''));
        $apellido1 = trim((string) ($v['apellido1'] ?? ''));

        $aerea = ['od' => [], 'oi' => []];
        $osea = ['od' => [], 'oi' => []];
        $ldl = ['od' => [], 'oi' => []];
        foreach (['od', 'oi'] as $lado) {
            foreach (CaseBuilder::FREQUENCIES as $n => $freq) {
                $aerea[$lado][] = (int) self::val($v, ['aerea', $lado, (string) $n], 0);
                $osea[$lado][] = (int) self::val($v, ['osea', $lado, (string) $n], 0);
                $ldl[$lado][] = (int) self::val($v, ['ldl', $lado, (string) $n], 130);
            }
            // "Igualar ósea a aérea" (equal_osea en create_a.py) también
            // sugiere y nada más: el JS copia la aérea encima de la ósea en
            // vivo y los campos quedan editables, así que lo que llega en el
            // POST manda. Solo se copia acá si la ósea no vino del todo (un
            // POST armado a mano, sin el formulario).
            if (isset($v['igualar'][$lado]) && !isset($v['osea'][$lado])) {
                $osea[$lado] = $aerea[$lado];
            }
            if (!isset($v['ldl_habilitado'][$lado])) {
                $ldl[$lado] = array_fill(0, count(CaseBuilder::FREQUENCIES), 130); // deshabilitado = ausente
            }
        }

        $reflexIpsi = ['od' => [], 'oi' => []];
        $reflexContra = ['od' => [], 'oi' => []];
        foreach (['od', 'oi'] as $lado) {
            for ($n = 0; $n < 4; $n++) {
                $reflexIpsi[$lado][] = (int) self::val($v, ['reflex_ipsi', $lado, (string) $n], 130);
            }
            for ($n = 0; $n < 5; $n++) {
                $reflexContra[$lado][] = (int) self::val($v, ['reflex_contra', $lado, (string) $n], 130);
            }
        }

        // Deterioro tonal (Carhart/Stat/Rosemberg): dB sobre el umbral aéreo
        // que hay que subir para sostener el tono 1 min, por frecuencia del
        // protocolo de cada prueba (ver ResponseAudiometry.DECAY_TESTS).
        $decayFieldCounts = ['carhart' => 4, 'stat' => 3, 'rosemberg' => 4];
        $decayPairs = [];
        foreach ($decayFieldCounts as $mode => $count) {
            $vals = ['od' => [], 'oi' => []];
            foreach (['od', 'oi'] as $lado) {
                for ($n = 0; $n < $count; $n++) {
                    $vals[$lado][] = max(0, (int) self::val($v, [$mode, $lado, (string) $n], 0));
                }
            }
            $decayPairs[$mode] = self::zip($vals['od'], $vals['oi']);
        }

        $reflexType = ['od' => 'normal', 'oi' => 'normal'];
        foreach (['od', 'oi'] as $lado) {
            $type = (string) self::val($v, ['reflex_type', $lado], 'normal');
            if (in_array($type, CaseBuilder::REFLEX_CURVE_TYPES, true)) {
                $reflexType[$lado] = $type;
            }
        }

        $airPairs = self::zip($aerea['od'], $aerea['oi']);
        $fletcher = CaseBuilder::fletcherAvg($airPairs);
        // SDT/SRT "auto (Fletcher)": el JS escribe el promedio en el campo y
        // lo deja editable, así que gana lo posteado. El cálculo de acá es
        // el respaldo para un POST sin ese campo.
        $sdt = [];
        $srt = [];
        foreach (['od' => 0, 'oi' => 1] as $lado => $i) {
            foreach ([['sdt', &$sdt], ['srt', &$srt]] as [$clave, &$destino]) {
                $posteado = self::val($v, [$clave, $lado], null);
                $destino[] = ($posteado === null && isset($v[$clave . '_auto'][$lado]))
                    ? $fletcher[$i] : (int) ($posteado ?? 0);
            }
            unset($destino);
        }

        $zOd = (string) ($v['z_od'] ?? 'A');
        $zOi = (string) ($v['z_oi'] ?? 'A');
        // Sonda de 1000 Hz (lactante): 'auto' = derivarlo de la letra, que
        // es lo que el simulador hacía siempre.
        $z1000Od = (string) ($v['z1000_od'] ?? 'auto');
        $z1000Oi = (string) ($v['z1000_oi'] ?? 'auto');
        if (!in_array($z1000Od, CaseBuilder::Z1000_OPTIONS, true)) {
            $z1000Od = 'auto';
        }
        if (!in_array($z1000Oi, CaseBuilder::Z1000_OPTIONS, true)) {
            $z1000Oi = 'auto';
        }
        $etfOd = (string) ($v['etf_od'] ?? 'Normal');
        $etfOi = (string) ($v['etf_oi'] ?? 'Normal');

        // Acumetría (Rinne/Weber). El "auto" global de la tabla (un solo
        // checkbox para las 6 celdas) la calcula desde los umbrales tonales
        // ya cargados arriba, pero lo hace en el formulario: acá gana lo
        // posteado, que es lo que el docente dejó en pantalla. El cálculo
        // de este lado es el respaldo para un POST que no traiga la celda.
        $rinne = [];
        $weber = [];
        $acumetriaValid = true;
        $acumetriaIsAuto = isset($v['acumetria_auto']);
        foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $freqIdx) {
            $rinne[$hz] = [];
            foreach (['od', 'oi'] as $lado) {
                $manual = self::val($v, ['rinne', $hz, $lado], null);
                if ($manual === null) {
                    $rinne[$hz][$lado] = $acumetriaIsAuto
                        ? CaseBuilder::rinneAuto($aerea[$lado][$freqIdx], $osea[$lado][$freqIdx])
                        : 'positivo';
                    continue;
                }
                if (!in_array((string) $manual, CaseBuilder::RINNE_OPTIONS, true)) {
                    $acumetriaValid = false;
                }
                $rinne[$hz][$lado] = (string) $manual;
            }
            $manualWeber = self::val($v, ['weber', $hz], null);
            if ($manualWeber === null) {
                $weber[$hz] = $acumetriaIsAuto
                    ? CaseBuilder::weberAuto($osea['od'][$freqIdx], $osea['oi'][$freqIdx])
                    : 'centrado';
                continue;
            }
            if (!in_array((string) $manualWeber, CaseBuilder::WEBER_OPTIONS, true)) {
                $acumetriaValid = false;
            }
            $weber[$hz] = (string) $manualWeber;
        }
        $bonePairs = self::zip($osea['od'], $osea['oi']);
        // Qué frecuencias califican para Fowler/I.W.A. se detecta solo de
        // los umbrales -- el alumno puede encontrarlo en cualquiera de
        // ellas, así que se pide un patrón de reclutamiento por cada una
        // (no una única frecuencia "elegida" al crear el caso).
        $fowlerQualifying = CaseBuilder::fowlerQualifyingFreqs($airPairs, $bonePairs);
        $fowlerPatterns = [];
        foreach ($fowlerQualifying as $freq) {
            $pattern = (string) self::val($v, ['fowler_pattern', (string) $freq], 'none');
            if (!array_key_exists($pattern, CaseBuilder::FOWLER_PATTERNS)) {
                $pattern = 'none';
            }
            $fowlerPatterns[(string) $freq] = $pattern;
        }
        $fowlerEnabled = count($fowlerPatterns) > 0;
        $fowlerDiplacusia = isset($v['diplacusia']);
        // Supraliminares: en variables (y no leídas inline más abajo) porque
        // la proyección del perfil las puede reescribir.
        $sisiVals = [(int) self::val($v, ['sisi', 'od'], 0), (int) self::val($v, ['sisi', 'oi'], 0)];
        // Logoaudiometría: máxima discriminación por oído, en variable por
        // lo mismo que las supraliminares (la proyección la puede pisar).
        $umd = [
            ['int' => (int) self::val($v, ['umd_int', 'od'], 35), 'percentage' => (int) self::val($v, ['umd_pct', 'od'], 100)],
            ['int' => (int) self::val($v, ['umd_int', 'oi'], 35), 'percentage' => (int) self::val($v, ['umd_pct', 'oi'], 100)],
        ];
        $recruitVals = [isset($v['recruit']['od']), isset($v['recruit']['oi'])];

        // Acufenometría: lo normal es que el paciente NO tenga acúfeno, así
        // que la ficha arranca con la casilla apagada y el resto de los
        // campos deshabilitados (no llegan en el POST y caen en su default,
        // que igual no se valida ni se guarda si no hay tinnitus).
        //
        // Con tinnitus: lateralidad (craneal/unilateral/bilateral) es
        // independiente de permanente/ocasional -- un tinnitus unilateral
        // puede ser permanente igual que uno bilateral. Solo "unilateral"
        // pide oído; "bilateral" admite predominio (asimetría), opcional.
        // Pulsátil es otro flag aparte. Ruido + frecuencia (matching, Hz)
        // son "la forma".
        $tinnitusPresente = isset($v['tinnitus']['presente']);
        $tinnitusLateralidad = (string) ($v['tinnitus']['lateralidad'] ?? 'craneal');
        $tinnitusOido = (string) ($v['tinnitus']['oido'] ?? 'od');
        $tinnitusPredominio = (string) ($v['tinnitus']['predominio'] ?? 'igual');
        $tinnitusPermanente = isset($v['tinnitus']['permanente']);
        $tinnitusRuido = (string) ($v['tinnitus']['ruido'] ?? CaseBuilder::TINNITUS_RUIDO_OPTIONS[0]);
        $tinnitusFrecuencia = (int) ($v['tinnitus']['frecuencia'] ?? CaseBuilder::FREQUENCIES[0]);

        // Otoscopia: sin modo -- 1 sola fase (índice 0) ya ES "única"; una
        // 2ª fase en adelante es lo que la convierte en "por fase".
        $otoscopiaCount = max(1, min(CaseBuilder::OTOSCOPIA_MAX_FASES, (int) ($v['otoscopia']['fase_count'] ?? 1)));
        $otoscopiaFases = [];
        for ($n = 0; $n < $otoscopiaCount; $n++) {
            // Fase 1 (índice 0) nunca tiene texto -- todavía no hay "fase
            // anterior" que describir.
            $texto = $n === 0 ? '' : trim((string) self::val($v, ['otoscopia', 'texto', (string) $n], ''));
            $otoscopiaFases[] = ['texto' => $texto];
        }

        // ABR: una patología por oído (ver ABR_TYPE_OPTIONS) -- ya no hay
        // banco de casos compartido, cada paciente trae la suya (ver
        // AbrMainWindow.la_super/DEFAULT_ABR_CASE en el cliente).
        $abrOd = self::parseAbr($v, 'od');
        $abrOi = self::parseAbr($v, 'oi');
        // Con qué set normativo se armó este caso. No cambia nada de lo que
        // se simula --las ondas ya están escritas en cada campo, con el
        // offset del autor adentro-- pero deja el rastro: sin esto, un caso
        // hecho con Hood y otro con Sanfins son indistinguibles después de
        // guardar, y la diferencia entre sets es del orden de la desviación
        // que el docente quiso cargar a mano.
        $abrAutor = self::abrAutor($v, $age, $gender, $horasVida);

        // EOA: patología por oído, mismo shape simplificado (type + umbral)
        // que ABR usa para su curva -- ver oae_attenuation_db en
        // src/oae/generators/base.py.
        $eoasOd = self::parseEoas($v, 'od');
        $eoasOi = self::parseEoas($v, 'oi');

        // Perfil auditivo: el sitio de la lesión (ver src/CaseProfile.php y
        // ROADMAP.md). El audiograma ya dice cuánta pérdida hay y cuánta es
        // conductiva; lo único que no puede decir es qué parte del
        // componente sensorioneural es coclear y cuál retrococlear. Eso es
        // `cce_pct`, y con `retro` es todo lo que el perfil agrega.
        //
        // Todavía no tiene UI propia (fase 3 del roadmap): viaja en inputs
        // ocultos y, en un caso que nunca lo tuvo, se infiere de la
        // patología ya cargada. Los `auto` arrancan apagados, así un caso
        // existente no cambia de comportamiento por abrirlo y guardarlo.
        $perfilLados = [];
        foreach ([['od', 'OD', $abrOd, $eoasOd], ['oi', 'OI', $abrOi, $eoasOi]] as [$lado, $ladoData, $abrLado, $eoasLado]) {
            $ccePost = self::val($v, ['perfil', $lado, 'cce_pct'], null);
            $perfilLados[$ladoData] = [
                'cce_pct' => ($ccePost === null || $ccePost === '')
                    ? CaseProfile::inferCcePct($abrLado, $eoasLado)
                    : max(0.0, min(100.0, (float) $ccePost)),
                // El patrón retrococlear sigue viviendo en el tab ABR hasta
                // la fase 3: son los MISMOS inputs, no dos verdades.
                'retro' => CaseProfile::normalizeRetro($abrLado['neural']),
            ];
        }
        $perfilAuto = [];
        foreach (CaseProfile::AUTO_MODULES as $moduloAuto) {
            $perfilAuto[$moduloAuto] = (bool) self::val($v, ['perfil', 'auto', $moduloAuto], false);
        }
        $perfil = [
            'version' => CaseProfile::VERSION,
            'OD' => $perfilLados['OD'],
            'OI' => $perfilLados['OI'],
            'auto' => $perfilAuto,
        ];

        // Todo lo que el perfil proyecta, calculado de una pasada (ver
        // CaseProfile::project). La misma función alimenta la vista previa
        // en vivo del formulario, vía admin/case_project.php: una sola
        // implementación de cada ley.
        $proyeccion = CaseProfile::project($airPairs, $bonePairs, $perfil, ['OD' => $zOd, 'OI' => $zOi], $horasVida, $edadMeses, $nacimiento);
        $decomp = $proyeccion['decomp'];

        // La derivación es una SUGERENCIA, no una fuente que pise al
        // docente. Con el módulo en automático la proyección ya está en el
        // formulario --la escribe case/profile-preview.js en vivo, contra
        // este mismo CaseProfile::project()-- así que lo que llega en el
        // POST ES la proyección, salvo donde el docente la haya corregido a
        // mano. Y esa corrección es justo lo que hay que respetar: el caso
        // incoherente a propósito (Stenger, falsa onda V, simulación) se
        // arma editando un examen derivado, no apagando la casilla.
        //
        // Por eso lo posteado gana y la proyección solo aporta las claves
        // que el formulario no tiene cómo mandar: el umbral por estímulo
        // del ABR, aéreo y óseo, que no es un campo sino una tabla.
        if ($perfilAuto['abr']) {
            $abrOd = array_merge($proyeccion['abr']['OD'], $abrOd);
            $abrOi = array_merge($proyeccion['abr']['OI'], $abrOi);
        }
        if ($perfilAuto['eoas']) {
            $eoasOd = array_merge($proyeccion['eoas']['OD'], $eoasOd);
            $eoasOi = array_merge($proyeccion['eoas']['OI'], $eoasOi);
        }
        // Reflejos, supraliminares y logoaudiometría no necesitan ni eso:
        // cada número que proyectan tiene su campo en el formulario.

        // VEMP: patología vestibular por oído, y los tres subtipos armados
        // por separado (ver parseVemp).
        $vempOd = self::parseVemp($v, 'od');
        $vempOi = self::parseVemp($v, 'oi');

        // Edad 0 es válida SI viene la edad exacta: es un recién nacido o un
        // lactante, no un campo sin llenar. Sin esa excepción no se podía
        // guardar ningún caso de maternidad -- el formulario los rechazaba
        // con "Falta la edad" justo cuando la edad era el dato.
        if ($age <= 0 && $horasVida === null) {
            $error = 'Falta la edad: si es un recién nacido o un lactante, dejá 0 y cargá la edad exacta (horas, días o meses) en la ficha Paciente.';
        } elseif (!$isUpdate && ($nombre1 === '' || $apellido1 === '')) {
            $error = 'Falta el nombre del paciente: generalo con "Generar caso" (Armado rápido) o escribilo a mano en la pestaña Paciente.';
        } elseif ($isUpdate && (trim((string) ($v['nombre'] ?? '')) === '' || trim((string) ($v['apellido'] ?? '')) === '')) {
            $error = 'Falta el nombre del paciente.';
        } elseif (!in_array($zOd, CaseBuilder::Z_OPTIONS, true) || !in_array($zOi, CaseBuilder::Z_OPTIONS, true)) {
            $error = 'Tipo de timpanograma inválido.';
        } elseif (!in_array($etfOd, CaseBuilder::ETF_OPTIONS, true) || !in_array($etfOi, CaseBuilder::ETF_OPTIONS, true)) {
            $error = 'Valor de ETF inválido.';
        } elseif (!$acumetriaValid) {
            $error = 'Valor de Rinne/Weber inválido.';
        } elseif ($tinnitusPresente && !in_array($tinnitusLateralidad, CaseBuilder::TINNITUS_LATERALIDAD_OPTIONS, true)) {
            $error = 'Lateralidad del tinnitus inválida.';
        } elseif ($tinnitusPresente && $tinnitusLateralidad === 'unilateral' && !in_array($tinnitusOido, ['od', 'oi'], true)) {
            $error = 'Falta el oído del tinnitus (unilateral, hay que indicar cuál).';
        } elseif ($tinnitusPresente && !in_array($tinnitusPredominio, CaseBuilder::TINNITUS_PREDOMINIO_OPTIONS, true)) {
            $error = 'Predominio del tinnitus inválido.';
        } elseif ($tinnitusPresente && !in_array($tinnitusRuido, CaseBuilder::TINNITUS_RUIDO_OPTIONS, true)) {
            $error = 'Tipo de ruido del tinnitus inválido.';
        } elseif ($tinnitusPresente && !in_array($tinnitusFrecuencia, CaseBuilder::FREQUENCIES, true)) {
            $error = 'Frecuencia del tinnitus inválida.';
        } elseif (!in_array($abrOd['type'], CaseBuilder::ABR_TYPE_OPTIONS, true) || !in_array($abrOi['type'], CaseBuilder::ABR_TYPE_OPTIONS, true)) {
            $error = 'Patología ABR inválida.';
        } elseif (!in_array($eoasOd['type'], CaseBuilder::EOAS_TYPE_OPTIONS, true) || !in_array($eoasOi['type'], CaseBuilder::EOAS_TYPE_OPTIONS, true)) {
            $error = 'Patología EOA inválida.';
        } elseif ($eoasOd['sello_pct'] < 5 || $eoasOd['sello_pct'] > 100 || $eoasOi['sello_pct'] > 100 || $eoasOi['sello_pct'] < 5) {
            $error = 'Sello de sonda EOA fuera de rango (5-100%).';
        } elseif ($eoasOd['variabilidad_db'] < 0 || $eoasOi['variabilidad_db'] < 0 || $eoasOd['ruido_db'] < -20 || $eoasOi['ruido_db'] < -20) {
            $error = 'Ruido/variabilidad EOA fuera de rango.';
        } elseif (!in_array($eoasOd['soae_mode'], CaseBuilder::EOAS_SOAE_MODES, true) || !in_array($eoasOi['soae_mode'], CaseBuilder::EOAS_SOAE_MODES, true)) {
            $error = 'Modo SOAE inválido.';
        } elseif (($soaeError = CaseBuilder::soaePeaksError($eoasOd) ?? CaseBuilder::soaePeaksError($eoasOi)) !== null) {
            $error = $soaeError;
        } elseif (!in_array($vempOd['type'], CaseBuilder::VEMP_TYPE_OPTIONS, true) || !in_array($vempOi['type'], CaseBuilder::VEMP_TYPE_OPTIONS, true)) {
            $error = 'Patología VEMP inválida.';
        } elseif (($neuralError = CaseBuilder::neuralParamsError($abrOd['neural'], 'OD')
                ?? CaseBuilder::neuralParamsError($abrOi['neural'], 'OI')) !== null) {
            $error = $neuralError;
        // La coherencia se chequea sobre lo que el docente escribió a mano.
        // Un módulo derivado del perfil no puede contradecirse a sí mismo, y
        // además su umbral ya no está en la misma unidad que este chequeo
        // (el del ABR es dB nHL, no dB HL).
        } elseif (($coherencia = CaseBuilder::normalCoherenceError($abrOd, 'ABR', 'OD', !$perfilAuto['abr'])
                ?? CaseBuilder::normalCoherenceError($abrOi, 'ABR', 'OI', !$perfilAuto['abr'])
                ?? ($perfilAuto['eoas'] ? null : CaseBuilder::normalCoherenceError($eoasOd, 'EOA', 'OD'))
                ?? ($perfilAuto['eoas'] ? null : CaseBuilder::normalCoherenceError($eoasOi, 'EOA', 'OI'))
                // VEMP sin chequeo de umbral: el suyo ronda 60-90 dB nHL.
                // Subtipo por subtipo: las desviaciones viven en cada uno.
                ?? CaseBuilder::vempCoherenceError($vempOd, 'OD')
                ?? CaseBuilder::vempCoherenceError($vempOi, 'OI')) !== null) {
            $error = $coherencia;
        }

        // Incoherencias entre lo cargado a mano y lo que predice el perfil.
        // Avisan, no bloquean: un caso puede ser incoherente a propósito (el
        // Stenger y la simulación lo NECESITAN). Por eso se muestran una vez
        // y se guardan igual tildando la casilla -- pero el docente tiene que
        // haberlos leído, que es lo que hoy no pasa en ningún lado.
        $avisosPerfil = [];
        if ($error === null && !isset($v['perfil_confirmar'])) {
            $avisosPerfil = CaseProfile::warnings(
                $decomp, $perfil,
                ['OD' => $abrOd, 'OI' => $abrOi],
                ['OD' => $eoasOd, 'OI' => $eoasOi],
                ['ipsi' => $reflexIpsi, 'contra' => $reflexContra],
                ['OD' => $zOd, 'OI' => $zOi]
            );
        }

        if ($error === null && $avisosPerfil === []) {
            $antecedentes = [];
            foreach (CaseBuilder::HIST_CHECKBOXES as $h) {
                $antecedentes[$h] = isset($v['hist'][$h]);
            }

            // Estado del borrador de IA. `generado` lo pone el JS al traer
            // el borrador; `verificado` sale de la casilla que el docente
            // tilda después de leerlo, y se limpia sola al regenerar (el
            // texto nuevo no lo leyó nadie todavía). Se guarda quién y
            // cuándo: si el caso sale mal, hay a quién preguntarle.
            $iaGenerado = !empty($v['anamnesis_ia']['generado']);
            $iaVerificado = $iaGenerado && !empty($v['anamnesis_ia']['verificado']);
            $anamnesisIa = [
                'generado' => $iaGenerado,
                'verificado' => $iaVerificado,
                'generado_en' => trim((string) self::val($v, ['anamnesis_ia', 'generado_en'], '')),
                'verificado_por' => $iaVerificado ? (string) ($me['username'] ?? $me['id'] ?? '') : '',
                'verificado_en' => $iaVerificado ? date('c') : '',
            ];

            $id = $isUpdate ? $editId : CaseBuilder::nextCaseId($pdo);
            $data = CaseBuilder::buildCaseData([
                'gender' => $gender,
                'age' => $age,
                'edad_horas' => $horasVida,
                'nacimiento' => $nacimiento,
                'id' => $id,
                'aerea' => $airPairs,
                'osea' => self::zip($osea['od'], $osea['oi']),
                'ldl' => self::zip($ldl['od'], $ldl['oi']),
                'z_od' => $zOd,
                'z_oi' => $zOi,
                'z1000_od' => $z1000Od,
                'z1000_oi' => $z1000Oi,
                'rinne' => $rinne,
                'weber' => $weber,
                'umd' => $umd,
                'sdt' => $sdt,
                'srt' => $srt,
                'fowler' => [
                    'enabled' => $fowlerEnabled,
                    'patterns' => $fowlerPatterns,
                    'diplacusia' => $fowlerDiplacusia,
                ],
                'stenger' => [isset($v['stenger']['od']), isset($v['stenger']['oi'])],
                'sisi' => $sisiVals,
                'recruit' => $recruitVals,
                'decay' => [false, false], // reemplazado por carhart/stat/rosemberg; se conserva el shape por compatibilidad con casos viejos
                'carhart' => $decayPairs['carhart'],
                'stat' => $decayPairs['stat'],
                'rosemberg' => $decayPairs['rosemberg'],
                'reflex' => [
                    'ipsi' => self::zip($reflexIpsi['od'], $reflexIpsi['oi']),
                    'contra' => self::zip($reflexContra['od'], $reflexContra['oi']),
                    'tipo' => $reflexType,
                ],
                'etf_od' => $etfOd,
                'etf_oi' => $etfOi,
                'tinnitus' => $tinnitusPresente ? [
                    'presente' => true,
                    'lateralidad' => $tinnitusLateralidad,
                    'oido' => $tinnitusLateralidad === 'unilateral' ? $tinnitusOido : null,
                    'predominio' => $tinnitusLateralidad === 'bilateral' ? $tinnitusPredominio : null,
                    'pulsatil' => isset($v['tinnitus']['pulsatil']),
                    'permanente' => $tinnitusPermanente,
                    'ruido' => $tinnitusRuido,
                    'frecuencia' => $tinnitusFrecuencia,
                ] : ['presente' => false],
                'anamnesis' => [
                    'antecedentes' => $antecedentes,
                    'medicamentos' => trim((string) ($v['medicamentos'] ?? '')),
                    'cirugias' => trim((string) ($v['cirugias'] ?? '')),
                    'otros' => trim((string) ($v['otros'] ?? '')),
                    // Trazabilidad del borrador escrito por el LLM. Sin
                    // `verificado` en true el caso no se guarda ni se cita
                    // (ver CaseCompleteness): el modelo puede inventar una
                    // cirugía que no existe, y eso le llega al alumno como
                    // parte del caso.
                    'ia' => $anamnesisIa,
                ],
                'comportamiento' => trim((string) ($v['comportamiento'] ?? '')),
                'disposicion' => (int) ($v['disposicion'] ?? 0),
                // El paciente no viaja en las filas de la sala: sus datos
                // ya están en este mismo formulario y tener dos verdades
                // para la misma persona es pedir que se contradigan.
                'sala' => Sala::fromForm($v, [
                    'nombre' => trim((string) ($v['nombre'] ?? ($v['nombre1'] ?? ''))),
                    'edad' => $age,
                    'genero' => $gender,
                    'comportamiento' => trim((string) ($v['comportamiento'] ?? '')),
                    'disposicion' => (int) ($v['disposicion'] ?? 0),
                ]),
                'otoscopia' => ['fases' => $otoscopiaFases],
                'perfil' => $perfil,
                'abr' => ['OD' => $abrOd, 'OI' => $abrOi, 'autor' => $abrAutor],
                'eoas' => ['OD' => $eoasOd, 'OI' => $eoasOi],
                'vemp' => ['OD' => $vempOd, 'OI' => $vempOi],
                // La pasada final del docente por el Resumen: qué fichas
                // dio por buenas. Va adentro del caso, no al lado -- ver
                // más abajo, es lo último que bloquea el guardado.
                'revision' => CaseReview::fromPost($v, $me),
            ]);

            // Lo que no se puede calcular tiene que estar decidido antes de
            // que el caso salga del editor: un timpanograma en A con 40 dB
            // de gap, o un ABR "coclear" con la morfología de onda de un
            // oído sano, le llegan al alumno como un paciente que no cierra
            // y el docente no se entera nunca. Ver CaseCompleteness.
            //
            // No es lo mismo que $avisosPerfil: aquellos son incoherencias
            // que pueden SER el ejercicio (Stenger, falsa onda V) y se
            // guardan tildando una casilla. Esto es un dato que falta, y no
            // hay caso sin él.
            // pending() (y no pendingTexts) porque cada pendiente sabe en qué
            // pestaña se arregla: el listado de abajo salta ahí y le pinta el
            // punto rojo a la pestaña.
            $faltantes = CaseCompleteness::pending($data);

            // Y la revisión ficha por ficha: el caso no sale del editor sin
            // que alguien haya mirado las once y dicho que están así porque
            // sí. Es lo que hace que un caso generado al azar no pueda
            // guardarse sin que nadie lo lea.
            //
            // Va después de $faltantes a propósito: una ficha revisada
            // apaga sus pendientes (CaseCompleteness::pending filtra por
            // CaseReview::revisada), así que el docente ve la lista de lo
            // que el editor le reclama ANTES de tildar, no después.
            $sinRevisar = CaseReview::sinRevisar($data);
        }
        $f->error = $error;
        $f->avisos = $avisosPerfil;
        $f->faltantes = $faltantes;
        $f->sinRevisar = $sinRevisar;
        $f->data = $data;
        $f->caseId = (string) $id;
        $f->age = $age;
        $f->nombre1 = $nombre1;
        $f->apellido1 = $apellido1;
        return $f;
    }

    /**
     * Circunstancias del parto que mueven el screening neonatal.
     *
     * El percentil de cada oído se sortea UNA vez y queda guardado: dos
     * recién nacidos de la misma edad no tienen la misma cantidad de
     * líquido, y los dos oídos del mismo bebé tampoco --por eso en el turno
     * uno refiere y el otro no--. Si ya venía en el caso se respeta, así
     * volver a guardar no le cambia el resultado al ejercicio.
     *
     * Es pública porque la vista previa (admin/case_project.php) tiene que
     * proyectar con las MISMAS circunstancias que se van a guardar: sin
     * esto proyectaba con el percentil por defecto (0,5) y, como lo posteado
     * le gana a la proyección, un recién nacido de 14 horas salía siempre
     * con las EOA presentes --0,5 cae justo del lado que pasa--.
     */
    public static function parseNacimiento(array $v): array
    {
        $semanas = self::val($v, ['nacimiento', 'semanas'], '');
        $semanas = is_numeric($semanas) ? (int) $semanas : null;
        $peso = self::val($v, ['nacimiento', 'peso_g'], '');
        $peso = is_numeric($peso) ? (int) $peso : null;
        $torch = (string) self::val($v, ['nacimiento', 'torch'], '');
        $out = [
            'parto' => self::val($v, ['nacimiento', 'parto'], 'vaginal') === 'cesarea'
                ? 'cesarea' : 'vaginal',
            'semanas' => $semanas,
            'peso_g' => $peso,
            'torch' => isset(CaseBuilder::TORCH_OPTIONS[$torch]) && $torch !== '' ? $torch : null,
            'torch_sintomatica' => (bool) self::val($v, ['nacimiento', 'torch_sintomatica'], false),
            'uci_dias' => ($d = self::val($v, ['nacimiento', 'uci_dias'], '')) !== '' && is_numeric($d)
                ? max(0, (int) $d) : null,
            'ototoxicos' => (bool) self::val($v, ['nacimiento', 'ototoxicos'], false),
            'exanguinotransfusion' => (bool) self::val($v, ['nacimiento', 'exanguinotransfusion'], false),
            'peg' => (bool) self::val($v, ['nacimiento', 'peg'], false),
            'vernix_limpiado' => (bool) self::val($v, ['nacimiento', 'vernix_limpiado'], false),
            'liquido_persistente' => (bool) self::val($v, ['nacimiento', 'liquido_persistente'], false),
        ];
        // Los que mueven el tamizaje no son campos aparte: salen de las
        // semanas y del peso. Un prematuro de 30 semanas con 900 g acumula
        // los dos, que es lo que pasa de verdad.
        $out['cesarea'] = $out['parto'] === 'cesarea';
        $out['pretermino_tardio'] = $semanas !== null && $semanas >= 34 && $semanas <= 36;
        $out['pretermino'] = $semanas !== null && $semanas < 34;
        $out['muy_bajo_peso'] = $peso !== null && $peso < CaseBuilder::PESO_MUY_BAJO_G;
        $out['percentil'] = [];
        foreach (['OD', 'OI'] as $lado) {
            $guardado = self::val($v, ['nacimiento', 'percentil', $lado], '');
            $out['percentil'][$lado] = is_numeric($guardado)
                ? min(1.0, max(0.0, (float) $guardado))
                : round(mt_rand() / mt_getrandmax(), 4);
        }
        return $out;
    }

    /**
     * Horas de vida del paciente, o null si no viene al caso.
     *
     * El formulario lo pide con unidad (horas, días o meses) porque un
     * neonatólogo no dice "0.002 años". Se normaliza a horas, que es la
     * unidad en la que el transitorio de las primeras horas tiene sentido.
     * Sobre el año se descarta: ahí manda la edad en años.
     */
    private static function horasDeVida(array $v, int $age): ?int
    {
        if ($age > 0) {
            return null;
        }
        $n = self::val($v, ['edad_valor'], '');
        if ($n === '' || $n === null || !is_numeric($n)) {
            return null;
        }
        $unidad = (string) self::val($v, ['edad_unidad'], 'horas');
        $factor = ['horas' => 1, 'dias' => 24, 'meses' => 720];
        $horas = (int) round((float) $n * ($factor[$unidad] ?? 1));
        // Un año o más en horas ya no es un recién nacido: lo cubre 'age'.
        return max(0, min($horas, 8760));
    }

    /**
     * Con qué set normativo se construyó el caso, y qué valores tenía ese
     * set para la población que le toca al paciente.
     *
     * Se guarda el baseline RESUELTO y no solo el id: los sets del docente
     * se editan, y un caso de hace seis meses tiene que poder decir con qué
     * números se armó aunque ese set ya no sea el mismo.
     */
    private static function abrAutor(array $v, int $edad, int $genero, $horas = null): array
    {
        require_once __DIR__ . '/AbrReferences.php';
        require_once __DIR__ . '/CaseWaveforms.php';
        $id = trim((string) self::val($v, ['abr', 'autor'], '__default__'));
        // Los sets del docente viven en app_config, que es base de datos:
        // CaseForm se usa también desde los tests, sin PDO. Si no está a
        // mano se resuelve contra los publicados y el set propio queda
        // registrado por su id igual -- el rastro no se pierde.
        $propios = [];
        if (class_exists('AppConfig')) {
            try {
                $guardados = AppConfig::getEffective('abr_reference_authors', null);
                $propios = is_array($guardados) ? $guardados : [];
            } catch (Throwable $e) {
                $propios = [];
            }
        }
        $label = AbrReferences::label($id, $propios) ?? ($id !== '__default__' ? $id : null);
        if ($id === '__default__' || $label === null) {
            $id = '__default__';
            $label = 'LabSim (default)';
        }
        $pop = CaseWaveforms::poblacion($edad, $genero, $horas);
        return [
            'set' => $id,
            'label' => $label,
            'poblacion' => $pop,
            'baseline' => AbrReferences::resolve($id, $pop),
        ];
    }

    /** Un oído del ABR desde el POST (ver ABR_TYPE_OPTIONS). */
    private static function parseAbr(array $v, string $lado): array
    {
            return [
                'type' => (string) self::val($v, ['abr', $lado, 'type'], 'normal'),
                // Patrón retrococlear (ver ABR_NEURAL_DEFAULTS): se guarda
                // siempre, el generador solo lo mira si type === 'neural'.
                // Lo que se persiste son los parámetros, nunca la etiqueta
                // del preset -- la curva no puede depender de un nombre.
                'neural' => [
                    'i_iii_ms' => (float) self::val($v, ['abr', $lado, 'neural', 'i_iii_ms'], CaseBuilder::ABR_NEURAL_DEFAULTS['i_iii_ms']),
                    'iii_v_ms' => (float) self::val($v, ['abr', $lado, 'neural', 'iii_v_ms'], CaseBuilder::ABR_NEURAL_DEFAULTS['iii_v_ms']),
                    'global_delay_ms' => (float) self::val($v, ['abr', $lado, 'neural', 'global_delay_ms'], CaseBuilder::ABR_NEURAL_DEFAULTS['global_delay_ms']),
                    'bloqueo' => (string) self::val($v, ['abr', $lado, 'neural', 'bloqueo'], CaseBuilder::ABR_NEURAL_DEFAULTS['bloqueo']),
                    'v_i_factor' => (float) self::val($v, ['abr', $lado, 'neural', 'v_i_factor'], CaseBuilder::ABR_NEURAL_DEFAULTS['v_i_factor']),
                    'microfonica' => (string) self::val($v, ['abr', $lado, 'neural', 'microfonica'], CaseBuilder::ABR_NEURAL_DEFAULTS['microfonica']),
                    'desincronia' => (string) self::val($v, ['abr', $lado, 'neural', 'desincronia'], CaseBuilder::ABR_NEURAL_DEFAULTS['desincronia']),
                    'sensibilidad_tasa' => (string) self::val($v, ['abr', $lado, 'neural', 'sensibilidad_tasa'], CaseBuilder::ABR_NEURAL_DEFAULTS['sensibilidad_tasa']),
                ],
                'repro' => isset($v['abr'][$lado]['repro']),
                'repro_var' => (float) self::val($v, ['abr', $lado, 'repro_var'], 0.2),
                // Cuanto se mueve el paciente DURANTE la captura (ver
                // agitation_run en ABR_generator.py). 0 = quieto.
                'inquietud' => (float) self::val($v, ['abr', $lado, 'inquietud'], 0),
                // Reflejo post-auricular (miogenico, ~13 ms): 0 = no
                // aparece. Ver postauricular_reflex en ABR_generator.py.
                'pam' => (float) self::val($v, ['abr', $lado, 'pam'], 0),
                // Falsa onda V: artefacto que solo se descubre mirando los
                // subpromedios A/B (ver false_wave en ABR_generator.py).
                // amp = 0 lo desactiva, que es el default: es un ejercicio
                // que el docente arma a proposito, no algo del paciente.
                'falsa_v' => [
                    'amp' => (float) self::val($v, ['abr', $lado, 'falsa_v_amp'], 0),
                    'lat' => (float) self::val($v, ['abr', $lado, 'falsa_v_lat'], 5.6),
                    // Rango de intensidades donde aparece: fuera de el la
                    // serie queda limpia y coherente, que es lo que deja
                    // usar la migracion de latencia como segunda prueba.
                    'int_min' => (float) self::val($v, ['abr', $lado, 'falsa_v_int_min'], 0),
                    'int_max' => (float) self::val($v, ['abr', $lado, 'falsa_v_int_max'], 120),
                    'mitad' => in_array(self::val($v, ['abr', $lado, 'falsa_v_mitad'], 'auto'), ['auto', 'a', 'b'], true)
                        ? (string) self::val($v, ['abr', $lado, 'falsa_v_mitad'], 'auto') : 'auto',
                ],
                'umbral' => (int) self::val($v, ['abr', $lado, 'umbral'], 20),
                'average_objetivo' => (int) self::val($v, ['abr', $lado, 'average_objetivo'], 2000),
                'desviaciones' => [
                    'onda_I' => ['lat' => (float) self::val($v, ['abr', $lado, 'lat_I'], 0), 'amp' => (float) self::val($v, ['abr', $lado, 'amp_I'], 0)],
                    'onda_III' => ['lat' => (float) self::val($v, ['abr', $lado, 'lat_III'], 0), 'amp' => (float) self::val($v, ['abr', $lado, 'amp_III'], 0)],
                    'onda_V' => ['lat' => (float) self::val($v, ['abr', $lado, 'lat_V'], 0), 'amp' => (float) self::val($v, ['abr', $lado, 'amp_V'], 0)],
                ],
                // Cuán ruidoso es el paciente, declarado por las CONDICIONES
                // en que se midió y no por el FSP, que es el resultado: a
                // `nivel_referencia` hicieron falta `barridos_criterio` para
                // llegar al criterio. De ahí el cliente despeja el ruido de un
                // barrido (ver sigma_from_criterion en ABR_generator.py) y ese
                // ruido vale para todos los niveles.
                //
                // Vacío = el propio umbral de ese oído. Con la referencia en
                // el umbral y 2000 barridos, el umbral que declara el caso es
                // exactamente el nivel donde el equipo dice "presente" en la
                // mitad de los registros: el umbral del caso y el que marca el
                // alumno pasan a ser la misma definición.
                'nivel_referencia' => self::val($v, ['abr', $lado, 'nivel_referencia'], '') === ''
                    ? null : (float) self::val($v, ['abr', $lado, 'nivel_referencia'], 0.0),
                'barridos_criterio' => max(100.0, (float) self::val($v, ['abr', $lado, 'barridos_criterio'], 2000.0)),
                'respuesta_en_referencia' => self::val($v, ['abr', $lado, 'respuesta_en_referencia'], 'presente') === 'ausente'
                    ? 'ausente' : 'presente',
                'fsp_puntos' => [
                    '800' => (float) self::val($v, ['abr', $lado, 'fsp_800'], 2.3),
                    '2000' => (float) self::val($v, ['abr', $lado, 'fsp_2000'], 2.8),
                    'objetivo' => (float) self::val($v, ['abr', $lado, 'fsp_obj'], 3.0),
                ],
            ];
    }

    /** Un oído de EOA desde el POST. */
    private static function parseEoas(array $v, string $lado): array
    {
            $desv = [];
            foreach (CaseBuilder::EOAS_FREQS as $hz) {
                // Desviación en dB POR DEBAJO de la respuesta esperada
                // (positivo = OEA más chica), igual criterio que la
                // atenuación por patología: así "más número, peor oído".
                $desv[(string) $hz] = (float) self::val($v, ['eoas', $lado, 'desv', (string) $hz], 0);
            }
            // SOAE: picos fijados a mano (las filas vacías se ignoran).
            $soaePicos = CaseBuilder::soaePeaksFromForm(self::val($v, ['eoas', $lado, 'soae_peaks'], []));
            return [
                'type' => (string) self::val($v, ['eoas', $lado, 'type'], 'normal'),
                'umbral' => (int) self::val($v, ['eoas', $lado, 'umbral'], CaseBuilder::EOAS_DEFAULTS['umbral']),
                'atten_db' => (float) self::val($v, ['eoas', $lado, 'atten_db'], CaseBuilder::EOAS_DEFAULTS['atten_db']),
                'ruido_db' => (float) self::val($v, ['eoas', $lado, 'ruido_db'], CaseBuilder::EOAS_DEFAULTS['ruido_db']),
                'sello_pct' => (int) self::val($v, ['eoas', $lado, 'sello_pct'], CaseBuilder::EOAS_DEFAULTS['sello_pct']),
                'variabilidad_db' => (float) self::val($v, ['eoas', $lado, 'variabilidad_db'], CaseBuilder::EOAS_DEFAULTS['variabilidad_db']),
                'desviaciones' => $desv,
                'soae_mode' => (string) self::val($v, ['eoas', $lado, 'soae_mode'], CaseBuilder::EOAS_DEFAULTS['soae_mode']),
                'soae_peaks' => $soaePicos,
            ];
    }

    /**
     * Un oído de VEMP desde el POST: los TRES subtipos, cada uno con lo suyo.
     *
     * `type` (la patología) es del oído y no del subtipo: es el órgano el
     * que está lesionado, y qué VEMP lo muestra lo decide la anatomía --
     * VEMPGeneratorV1 ya cruza patología x subtipo (sacular pega en cVEMP,
     * utricular en oVEMP, neural en los dos). Una patología por subtipo
     * dejaría armar un oído con el sáculo enfermo según el cVEMP y sano
     * según el mVEMP, que miden el mismo órgano.
     *
     * Todo lo demás sí es por subtipo. El umbral sobre todo: la disociación
     * entre el umbral cervical y el ocular ES el hallazgo en la dehiscencia
     * (los dos bajos) y en la neuritis del nervio superior (oVEMP ausente
     * con cVEMP normal). Y las desviaciones no podían no serlo: cVEMP y
     * mVEMP comparten los nombres de pico (p13/n23) y hasta acá se pisaban
     * en los mismos cuatro campos.
     */
    private static function parseVemp(array $v, string $lado): array
    {
            $subtipos = [];
            foreach (CaseBuilder::VEMP_SUBTIPOS as $subtipo) {
                $desv = [];
                foreach (CaseBuilder::VEMP_PEAKS[$subtipo] as $pico) {
                    $desv[$pico] = [
                        'lat' => (float) self::val($v, ['vemp', $lado, $subtipo, "lat_{$pico}"], 0),
                        'amp' => (float) self::val($v, ['vemp', $lado, $subtipo, "amp_{$pico}"], 0),
                    ];
                }
                $def = CaseBuilder::VEMP_DEFAULTS[$subtipo];
                $subtipos[$subtipo] = [
                    'peaks' => CaseBuilder::VEMP_PEAKS[$subtipo],
                    'umbral' => (int) self::val($v, ['vemp', $lado, $subtipo, 'umbral'], $def['umbral']),
                    'repro' => isset($v['vemp'][$lado][$subtipo]['repro']),
                    'repro_var' => (float) self::val(
                        $v, ['vemp', $lado, $subtipo, 'repro_var'], CaseBuilder::VEMP_REPRO_VAR_DEFAULT
                    ),
                    'average_objetivo' => (int) self::val(
                        $v, ['vemp', $lado, $subtipo, 'average_objetivo'], $def['average_objetivo']
                    ),
                    'desviaciones' => $desv,
                ];
            }
            return [
                'type' => (string) self::val($v, ['vemp', $lado, 'type'], 'normal'),
                // Acá vivía `decidido`, la casilla "ya decidí qué pasa en el
                // VEMP de este oído": lo que hoy dice la revisión de la
                // ficha VEMP en el Resumen, para las once fichas y en un
                // solo lugar (ver CaseReview). Los casos guardados con ella
                // la conservan y siguen contando como revisados.
                'subtipos' => $subtipos,
            ];
    }
}
