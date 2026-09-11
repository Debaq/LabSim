<?php

declare(strict_types=1);

require_once __DIR__ . '/CaseBuilder.php';

/**
 * Enmascaramiento tonal: cuándo hace falta y con cuánto ruido.
 *
 * Las fórmulas son EXACTAMENTE las de la app de escritorio
 * (src/audiometria/response.py::_masking_calc y DebugMkg.py::_terminos), no
 * una versión "para el informe": si el PDF dijera un rango y el motor
 * aceptara otro, el docente corregiría al alumno con el número equivocado.
 *
 *   ¿cruza?   nivel en el oído probado - AI >= umbral ÓSEO del contralateral
 *             (AI aérea por frecuencia; AI ósea = 0, siempre cruza)
 *   aérea     mín = UAE - AI - UONE + UANE + CE      máx = UOE + AI
 *   ósea      mín = UOE - UONE + UANE + CE + EfOcl   máx = UOE + AI
 *
 * UAE/UOE son los umbrales aéreo/óseo del oído ESTUDIADO y UANE/UONE los del
 * no estudiado. El ruido siempre entra por auricular, así que para volver a
 * tapar al oído estudiado tiene que cruzar por vía aérea -- de ahí que el
 * máximo use la AI aérea también en la vía ósea.
 *
 * CE queda en 0: es el coeficiente del ruido elegido y el que corresponde a
 * la vía tonal es el Narrow Band Noise, que vale 0 (ver masking_params.py).
 * Con otro ruido el mínimo sube, pero eso lo decide el alumno en la cabina,
 * no la ficha.
 */
final class CaseMasking
{
    /**
     * Atenuación interaural aérea por frecuencia (dB). Misma tabla que
     * ResponseAudiometry.attenuations en src/audiometria/response.py y que
     * AIR_ATTENUATION_BY_FREQ en public/js/case/audiogram.js.
     */
    public const AI_AEREA = [35, 40, 40, 40, 40, 45, 45, 50, 50];

    /**
     * Efecto oclusivo por frecuencia (dB): cuánto mejora la vía ósea de un
     * oído al taparlo con el auricular del ruido. Solo en graves, y solo si
     * ese oído tiene el oído medio sano -- uno con gap ya se comporta como
     * ocluido y no gana nada (por eso el Bing es negativo cuando hay gap).
     * Mismos valores que ResponseAudiometry.oclusive_efect.
     */
    public const EFECTO_OCLUSIVO = [15, 15, 15, 10, 0, 0, 0, 0, 0];

    /** Gap (dB) desde el cual el oído ya no gana nada al ocluirlo. */
    public const OCLUSIVO_GAP_MAX = 5;

    /**
     * Todo el cuadro de enmascaramiento de un oído, frecuencia por
     * frecuencia y vía por vía.
     *
     * @param array<int,float> $aereaEst umbrales aéreos del oído estudiado
     * @param array<int,float> $oseaEst  umbrales óseos del oído estudiado
     * @param array<int,float> $aereaNo  aéreos del contralateral
     * @param array<int,float> $oseaNo   óseos del contralateral
     * @return array<int,array<string,array{cruza:bool,min:float,max:float,dilema:bool,meseta:float}>>
     *         índice de frecuencia => ['aerea' => ..., 'osea' => ...]
     */
    public static function tabla(array $aereaEst, array $oseaEst, array $aereaNo, array $oseaNo): array
    {
        $out = [];
        foreach (CaseBuilder::FREQUENCIES as $i => $hz) {
            $out[$i] = [
                'aerea' => self::via('aerea', $i, $aereaEst, $oseaEst, $aereaNo, $oseaNo),
                'osea' => self::via('osea', $i, $aereaEst, $oseaEst, $aereaNo, $oseaNo),
            ];
        }
        return $out;
    }

    /**
     * @return array{cruza:bool,min:float,max:float,dilema:bool,meseta:float,nivel_cruce:float}
     */
    public static function via(string $via, int $i, array $aereaEst, array $oseaEst, array $aereaNo, array $oseaNo): array
    {
        $uae = (float) ($aereaEst[$i] ?? 0);
        $uoe = (float) ($oseaEst[$i] ?? 0);
        $uane = (float) ($aereaNo[$i] ?? 0);
        $uone = (float) ($oseaNo[$i] ?? 0);
        $ai = (float) (self::AI_AEREA[$i] ?? 0);

        if ($via === 'aerea') {
            $estim = $uae;
            $aiEstimulo = $ai;
            $min = $uae - $ai - $uone + $uane;
        } else {
            $estim = $uoe;
            // Por vía ósea no hay atenuación interaural: el estímulo llega a
            // las dos cócleas casi igual, y por eso una ósea sin enmascarar
            // no dice de qué oído es.
            $aiEstimulo = 0.0;
            $min = $uoe - $uone + $uane + self::efectoOclusivo($i, $aereaNo, $oseaNo);
        }

        // El ruido entra por auricular en las dos vías: para volver a tapar
        // al oído estudiado tiene que cruzar con la AI aérea.
        $max = $uoe + $ai;
        $nivelCruce = $estim - $aiEstimulo;

        return [
            'cruza' => $nivelCruce >= $uone,
            'min' => $min,
            'max' => $max,
            // El mínimo efectivo por encima del máximo tolerable: no existe
            // ruido que sirva. El motor ordena el rango y lo acepta igual,
            // así que sin este aviso el dilema pasa desapercibido.
            'dilema' => $min > $max,
            'meseta' => $max - $min,
            'nivel_cruce' => $nivelCruce,
        ];
    }

    /** Efecto oclusivo del oído NO estudiado, que es el que lleva el auricular del ruido. */
    public static function efectoOclusivo(int $i, array $aereaNo, array $oseaNo): float
    {
        $valor = (float) (self::EFECTO_OCLUSIVO[$i] ?? 0);
        $gap = (float) ($aereaNo[$i] ?? 0) - (float) ($oseaNo[$i] ?? 0);
        return $gap > self::OCLUSIVO_GAP_MAX ? 0.0 : $valor;
    }
}
