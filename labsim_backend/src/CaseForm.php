<?php

declare(strict_types=1);

require_once __DIR__ . '/CaseBuilder.php';
require_once __DIR__ . '/CaseProfile.php';
require_once __DIR__ . '/CaseCompleteness.php';
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
    /** cases.data listo para persistir; [] si no se llegó a armar. */
    public array $data = [];
    /** Id del caso: el que se editaba, o el que se reservó recién. '' si no se llegó. */
    public string $caseId = '';
    public bool $isUpdate = false;
    /** Los tres que el guardado necesita para el paciente_snapshot. */
    public int $age = 0;
    public string $nombre1 = '';
    public string $apellido1 = '';

    /** Se guarda solo si no hay error, ni avisos sin confirmar, ni faltantes. */
    public function ok(): bool
    {
        return $this->error === null && $this->avisos === [] && $this->faltantes === [];
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
        $data = [];
        $id = '';

        $gender = ($v['gender'] ?? '0') === '1' ? 1 : 0;
        // Edad = propia del paciente/caso, se guarda en cases.data ('edad').
        // Editable siempre acá, en creación y en edición -- la agenda no
        // incide en esto para nada, solo guarda la fecha de la cita.
        $age = max(0, (int) ($v['age'] ?? 0));
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
            if (isset($v['igualar'][$lado])) {
                $osea[$lado] = $aerea[$lado]; // "igualar ósea a aérea", igual que equal_osea en create_a.py
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
        $sdt = [
            isset($v['sdt_auto']['od']) ? $fletcher[0] : (int) self::val($v, ['sdt', 'od'], 0),
            isset($v['sdt_auto']['oi']) ? $fletcher[1] : (int) self::val($v, ['sdt', 'oi'], 0),
        ];
        $srt = [
            isset($v['srt_auto']['od']) ? $fletcher[0] : (int) self::val($v, ['srt', 'od'], 0),
            isset($v['srt_auto']['oi']) ? $fletcher[1] : (int) self::val($v, ['srt', 'oi'], 0),
        ];

        $zOd = (string) ($v['z_od'] ?? 'A');
        $zOi = (string) ($v['z_oi'] ?? 'A');
        $etfOd = (string) ($v['etf_od'] ?? 'Normal');
        $etfOi = (string) ($v['etf_oi'] ?? 'Normal');

        // Acumetría (Rinne/Weber), auto-calculada desde los umbrales tonales
        // ya cargados arriba ($aerea/$osea, índices de CaseBuilder::ACUMETRIA_FREQS)
        // salvo que el docente haya destildado el único "auto" global de la
        // tabla (un solo checkbox para las 6 celdas, no uno por celda).
        $rinne = [];
        $weber = [];
        $acumetriaValid = true;
        $acumetriaIsAuto = isset($v['acumetria_auto']);
        foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $freqIdx) {
            $rinne[$hz] = [];
            foreach (['od', 'oi'] as $lado) {
                if ($acumetriaIsAuto) {
                    $rinne[$hz][$lado] = CaseBuilder::rinneAuto($aerea[$lado][$freqIdx], $osea[$lado][$freqIdx]);
                } else {
                    $manual = (string) self::val($v, ['rinne', $hz, $lado], 'positivo');
                    if (!in_array($manual, CaseBuilder::RINNE_OPTIONS, true)) {
                        $acumetriaValid = false;
                    }
                    $rinne[$hz][$lado] = $manual;
                }
            }
            if ($acumetriaIsAuto) {
                $weber[$hz] = CaseBuilder::weberAuto($osea['od'][$freqIdx], $osea['oi'][$freqIdx]);
            } else {
                $manualWeber = (string) self::val($v, ['weber', $hz], 'centrado');
                if (!in_array($manualWeber, CaseBuilder::WEBER_OPTIONS, true)) {
                    $acumetriaValid = false;
                }
                $weber[$hz] = $manualWeber;
            }
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
        $proyeccion = CaseProfile::project($airPairs, $bonePairs, $perfil, ['OD' => $zOd, 'OI' => $zOi]);
        $decomp = $proyeccion['decomp'];

        // Qué se aplica y qué no lo dicen los `auto`: un módulo en manual
        // sigue siendo del docente, incluso si el perfil predice otra cosa.
        if ($perfilAuto['abr']) {
            $abrOd = array_merge($abrOd, $proyeccion['abr']['OD']);
            $abrOi = array_merge($abrOi, $proyeccion['abr']['OI']);
        }
        if ($perfilAuto['eoas']) {
            $eoasOd = array_merge($eoasOd, $proyeccion['eoas']['OD']);
            $eoasOi = array_merge($eoasOi, $proyeccion['eoas']['OI']);
        }
        if ($perfilAuto['reflex']) {
            $reflexIpsi = $proyeccion['reflex']['ipsi'];
            $reflexContra = $proyeccion['reflex']['contra'];
            $reflexType = $proyeccion['reflex']['tipo'];
        }
        if ($perfilAuto['recruit']) {
            $sisiVals = $proyeccion['recruit']['sisi'];
            $recruitVals = $proyeccion['recruit']['recruit'];
            // Solo las frecuencias que el formulario ya reconoció como
            // calificantes: la proyección no agrega ni saca ninguna.
            foreach ($fowlerPatterns as $freqFowler => $_) {
                if (isset($proyeccion['recruit']['fowler'][(string) $freqFowler])) {
                    $fowlerPatterns[(string) $freqFowler] = $proyeccion['recruit']['fowler'][(string) $freqFowler];
                }
            }
            foreach ($proyeccion['recruit']['decay'] as $modoDecay => $valsDecay) {
                $decayPairs[$modoDecay] = self::zip($valsDecay['od'], $valsDecay['oi']);
            }
            // El LDL es la expresión audiométrica del reclutamiento: el
            // umbral sube y el disconfort no. Derivado, siempre está medido
            // (el 130 de "no medido" dejaría el hallazgo invisible).
            $ldl = $proyeccion['recruit']['ldl'];
        }
        if ($perfilAuto['logo']) {
            $umd = [
                ['int' => $proyeccion['logo']['OD']['int'], 'percentage' => $proyeccion['logo']['OD']['pct']],
                ['int' => $proyeccion['logo']['OI']['int'], 'percentage' => $proyeccion['logo']['OI']['pct']],
            ];
        }

        // VEMP: patología vestibular por oído. El subtipo (CVEMP cervical,
        // OVEMP ocular, MVEMP masetero) define qué picos se observan (ver
        // VEMP_PEAKS); los 4 peaks siempre se rinden en el form porque
        // simplificar con sub-bloques por subtipo haría el form más frágil
        // y no aporta nada pedagógico (el docente los edita y el cliente
        // usa solo los del subtipo activo).
        $vempOd = self::parseVemp($v, 'od');
        $vempOi = self::parseVemp($v, 'oi');

        if ($age <= 0) {
            $error = 'Falta la edad.';
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
                ?? CaseBuilder::normalCoherenceError($vempOd, 'VEMP', 'OD', false)
                ?? CaseBuilder::normalCoherenceError($vempOi, 'VEMP', 'OI', false)) !== null) {
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
                'id' => $id,
                'aerea' => $airPairs,
                'osea' => self::zip($osea['od'], $osea['oi']),
                'ldl' => self::zip($ldl['od'], $ldl['oi']),
                'z_od' => $zOd,
                'z_oi' => $zOi,
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
                'abr' => ['OD' => $abrOd, 'OI' => $abrOi],
                'eoas' => ['OD' => $eoasOd, 'OI' => $eoasOi],
                'vemp' => ['OD' => $vempOd, 'OI' => $vempOi],
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
        }
        $f->error = $error;
        $f->avisos = $avisosPerfil;
        $f->faltantes = $faltantes;
        $f->data = $data;
        $f->caseId = (string) $id;
        $f->age = $age;
        $f->nombre1 = $nombre1;
        $f->apellido1 = $apellido1;
        return $f;
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

    /** Un oído de VEMP desde el POST (ver VEMP_PEAKS). */
    private static function parseVemp(array $v, string $lado): array
    {
            $subtipo = (string) self::val($v, ['vemp', $lado, 'subtipo'], 'CVEMP');
            if (!in_array($subtipo, CaseBuilder::VEMP_SUBTIPOS, true)) {
                $subtipo = 'CVEMP';
            }
            $peaks = CaseBuilder::VEMP_PEAKS[$subtipo];
            $desv = [];
            // siempre persistimos los 4 picos aunque el subtipo use solo 2;
            // los picos no usados quedan con lat=0/amp=0 (no molestan).
            foreach (['p13', 'n23', 'n10', 'p16'] as $pico) {
                $desv[$pico] = [
                    'lat' => (float) self::val($v, ['vemp', $lado, "lat_{$pico}"], 0),
                    'amp' => (float) self::val($v, ['vemp', $lado, "amp_{$pico}"], 0),
                ];
            }
            return [
                'subtipo' => $subtipo,
                'type' => (string) self::val($v, ['vemp', $lado, 'type'], 'normal'),
                'repro' => isset($v['vemp'][$lado]['repro']),
                'repro_var' => (float) self::val($v, ['vemp', $lado, 'repro_var'], 0.2),
                'umbral' => (int) self::val($v, ['vemp', $lado, 'umbral'], 60),
                'average_objetivo' => (int) self::val($v, ['vemp', $lado, 'average_objetivo'], 200),
                'desviaciones' => $desv,
                'peaks' => $peaks,
            ];
    }
}
