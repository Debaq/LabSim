<?php

declare(strict_types=1);

/**
 * El paciente del audiómetro en la prueba de umbrales: ¿levanta la mano?
 *
 * Copia de src/audiometria/response.py del cliente (response_,
 * response_aerea_wout_msk, response_aerea_w_msk, response_osea_w_msk,
 * _masking_calc, oclusive_efect). Se usa SOLO para los registros viejos,
 * los que no traen la mano (sin "v" en el payload): desde el registro v2 la
 * mano viene en audio_respuesta y es lo que vio el alumno de verdad.
 *
 * Copia fiel, rarezas incluidas: el oído estudiado sale de la salida del
 * canal 0 aunque el tono esté en el 1, una frecuencia fuera de la tabla deja
 * la anterior, dos canales prendidos sin instrucción de enmascarar no
 * cambian la mano. Arreglarlas acá daría otra mano que la que vio el
 * alumno. tests/test_audiometria_paciente.php tiene los casos de
 * referencia; tests/test_audiometria_paciente.py corre los mismos en
 * Python, así las dos copias no se separan sin que se note.
 *
 * Fuera de los umbrales (supraliminares, logoaudiometría) devuelve null:
 * esas respuestas dependen del tiempo o del azar y no se reconstruyen.
 */
final class AudiometriaPaciente
{
    /** Índice de frecuencia del motor (response.py: self.frecuency). */
    public const FRECUENCIAS = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000];
    /** Atenuación interaural aérea por frecuencia (self.attenuations). */
    public const ATENUACION = [35, 40, 40, 40, 40, 45, 45, 50, 50];
    /** Efecto de oclusión por frecuencia (oclusive_efect). */
    public const OCLUSION = [15, 15, 15, 10, 0, 0, 0, 0, 0];

    /** stim_list de resources/json/config_audiometer.json, en orden. */
    public const ESTIMULOS = ['Tono', 'FM', 'Habla', 'Narrow Band Noise', 'Withe Noise', 'Speech Noise', 'Pink Noise'];
    /** trans_list, en orden: 0 aérea, 1 ósea, 2 campo libre. */
    public const TRANSDUCTORES = ['Aerea', 'Oséa', 'Campo libre'];
    /** Índices de ESTIMULOS que enmascaran (masking_params.RUIDOS_ENMASCARANTES). */
    public const RUIDOS = [3, 4, 5, 6];
    /** CE tonal por ruido (masking_params.CE_TONAL). */
    public const CE_TONAL = [3 => 0, 6 => 5, 4 => 10, 5 => 10];

    /** Instrucciones que el motor resuelve con tiempo o azar: no se reconstruyen. */
    private const NO_RECONSTRUIBLES = [
        'mano_levantada', 'mano_levantada_en_ruido', 'ruido_blanco_contralateral',
        'rosemberg_bilateral', 'pitos_fuertes', 'dos_pitos', 'escuche_mi_voz',
        'cambie_de_volumen',
    ];

    /** @var array */
    private $caso;

    /** $caso: cases.data (usa Aerea_mkg y Osea_mkg, [frecuencia][oído]). */
    public function __construct(array $caso)
    {
        $this->caso = $caso;
    }

    /**
     * La mano tras prender o apagar un canal.
     *
     * $estado: ['prueba' => 'Umbrales', 'freq_idx' => 0..8,
     *   'instruccion' => ?string, 'canales' => [2 x ['on' => bool,
     *   'int' => int, 'output' => 0|1, 'trans' => 0|1|2, 'stim' => 0..6]]].
     * output: 0 derecha, 1 cualquier otra (como set_config).
     *
     * Devuelve true/false, $previa si el motor no la cambia, o null si la
     * respuesta no se puede reconstruir (otra prueba).
     */
    public function mano(array $estado, ?bool $previa): ?bool
    {
        $c = $estado['canales'];
        $stims = [(int) $c[0]['stim'], (int) $c[1]['stim']];
        $prendidos = (int) $c[0]['on'] + (int) $c[1]['on'];
        $mano = $previa;
        if (array_intersect($stims, [0, 1, 2])) {
            $instr = $estado['instruccion'] ?? null;
            if ($instr === 'colocar_fonos' || $instr === 'colocar_vibrador') {
                $mano = $this->sinEnmascarar($estado, $previa);
            } elseif ($instr === 'aerea_+_ruido') {
                $mano = $prendidos === 2 ? $this->enmascarado($estado, 'aerea', $previa) : $this->sinEnmascarar($estado, $previa);
            } elseif ($instr === 'vibrador_+_ruido') {
                $mano = $prendidos === 2 ? $this->enmascarado($estado, 'osea', $previa) : $this->sinEnmascarar($estado, $previa);
            } elseif ($instr !== null && in_array($instr, self::NO_RECONSTRUIBLES, true)) {
                $mano = null;
            }
        }
        if ($prendidos === 0) {
            return false;
        }
        return $mano;
    }

    /** response_aerea_wout_msk */
    private function sinEnmascarar(array $estado, ?bool $previa): ?bool
    {
        if (($estado['prueba'] ?? '') !== 'Umbrales') {
            return $previa;
        }
        $c = $estado['canales'];
        if ((int) $c[0]['on'] + (int) $c[1]['on'] !== 1) {
            return $previa;
        }
        $ch = $c[0]['on'] ? 0 : 1;
        if (in_array((int) $c[$ch]['stim'], self::RUIDOS, true)) {
            return false;
        }
        $via = (int) $c[$ch]['trans'] === 0 ? 'aerea' : 'osea';
        $oe = (int) $c[$ch]['output'];
        $umbral = $this->umbralAparente($via, (int) $estado['freq_idx'], $oe, 1 - $oe, 0, 0);
        return (int) $c[$ch]['int'] >= $umbral;
    }

    /** response_aerea_w_msk / response_osea_w_msk */
    private function enmascarado(array $estado, string $via, ?bool $previa): ?bool
    {
        if (($estado['prueba'] ?? '') !== 'Umbrales') {
            return $previa;
        }
        $c = $estado['canales'];
        $stims = [(int) $c[0]['stim'], (int) $c[1]['stim']];
        if (!array_intersect($stims, self::RUIDOS)) {
            return $previa;
        }
        if ($via === 'aerea') {
            if ((int) $c[0]['output'] === (int) $c[1]['output']
                    || (int) $c[0]['trans'] !== 0 || (int) $c[1]['trans'] !== 0) {
                return $previa;
            }
        } elseif ((int) $c[0]['trans'] !== 1 && (int) $c[1]['trans'] !== 1) {
            return $previa;
        }
        $oe = (int) $c[0]['output'] === 0 ? 0 : 1;
        $on = 1 - $oe;
        $chTono = $stims[0] === 0 ? 0 : 1;
        $chRuido = null;
        foreach ([0, 1] as $ch) {
            if ($c[$ch]['on'] && (int) $c[$ch]['output'] === $on && in_array($stims[$ch], self::RUIDOS, true)) {
                $chRuido = $ch;
                break;
            }
        }
        if ($chRuido === null) {
            return $previa;
        }
        $ce = self::CE_TONAL[$stims[$chRuido]] ?? 0;
        $umbral = $this->umbralAparente($via, (int) $estado['freq_idx'], $oe, $on, (int) $c[$chRuido]['int'], $ce);
        return $umbral <= (int) $c[$chTono]['int'];
    }

    /**
     * _resolve_masked_threshold: umbral que muestra el oído $oe con
     * $ruido dB de enmascaramiento en $on. Dentro del rango, el real;
     * sobre el máximo, 130 (sobreenmascarado); bajo el mínimo, la sombra.
     */
    public function umbralAparente(string $via, int $f, int $oe, int $on, int $ruido, int $ce): int
    {
        $m = $this->rangoEnmascaramiento($via, $f, $oe, $on, $ce);
        if ($ruido >= $m['min'] && $ruido <= $m['max']) {
            return $m['real'];
        }
        if ($ruido > $m['max']) {
            return 130;
        }
        return $m['sombra'];
    }

    /** _masking_calc */
    public function rangoEnmascaramiento(string $via, int $f, int $oe, int $on, int $ce = 0): array
    {
        $at = self::ATENUACION[$f] ?? 50;
        if ($via === 'aerea') {
            $uae = $this->u('Aerea_mkg', $f, $oe);
            $uane = $this->u('Aerea_mkg', $f, $on);
            $uoe = $this->u('Osea_mkg', $f, $oe);
            $uone = $this->u('Osea_mkg', $f, $on);
            $min = $uae - $at - $uone + $uane + $ce;
            $max = $uoe + $at;
            $real = $uae;
            $sombra = min($uae, $at + $uone);
        } else {
            $uoe = $this->u('Osea_mkg', $f, $oe);
            $uone = $this->u('Osea_mkg', $f, $on);
            $uane = $this->u('Aerea_mkg', $f, $on);
            $min = $uoe - $uone + $uane + $ce + $this->oclusion($f, $on);
            $max = $uoe + $at;
            $real = $uoe;
            $sombra = min($uoe, $uone);
        }
        return ['min' => min($min, $max), 'max' => max($min, $max), 'real' => $real, 'sombra' => $sombra];
    }

    /** Umbral real del caso. */
    public function umbralReal(string $via, int $f, int $oido): int
    {
        return $this->u($via === 'aerea' ? 'Aerea_mkg' : 'Osea_mkg', $f, $oido);
    }

    /** Lo que responde ese oído sin ruido en el otro: el real o la sombra. */
    public function umbralSinRuido(string $via, int $f, int $oido): int
    {
        return $this->umbralAparente($via, $f, $oido, 1 - $oido, 0, 0);
    }

    /** oclusive_efect: solo en graves y solo con el oído medio sano. */
    private function oclusion(int $f, int $o): int
    {
        if ($f >= count(self::OCLUSION)) {
            return 0;
        }
        $gap = $this->u('Aerea_mkg', $f, $o) - $this->u('Osea_mkg', $f, $o);
        return $gap > 5 ? 0 : self::OCLUSION[$f];
    }

    private function u(string $tabla, int $f, int $oido): int
    {
        $filas = $this->caso[$tabla] ?? ($this->caso[$tabla === 'Aerea_mkg' ? 'Aerea' : 'Osea'] ?? []);
        return isset($filas[$f][$oido]) && is_numeric($filas[$f][$oido]) ? (int) $filas[$f][$oido] : 130;
    }
}
