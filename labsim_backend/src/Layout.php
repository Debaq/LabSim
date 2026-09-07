<?php

/**
 * Layout de la app de escritorio: módulos, sectores y boxes.
 *
 * Antes vivía en resources/json/apps.json del cliente Python. Ahora vive
 * acá y el cliente lo pide por GET /api/layout.php al arrancar. Sin red,
 * la app abre pero solo muestra la ventana de login (no carga toolbar).
 *
 * El shape de cada módulo es la misma tupla que tenía apps.json:
 *   [activo(bool), tooltip(str), z_pos(int), fix(tuple), size(tuple|"max"), state(str)]
 * -- size="max" hace que la subventana abra ocupando todo el mdi (queda
 * maximizada y Qt la re-ajusta sola si el mdi cambia de tamaño).
 * state ∈ {"pre", "development"}. "pre" = listo para usar,
 * "development" = gris/deshabilitado en el cliente. El filtro por curso
 * (qué módulos ve cada alumno/docente) sigue aparte en course_modules
 * vía Auth::userProfile; Layout solo describe la estructura, no los
 * permisos.
 */
final class Layout
{
    public const APPS = [
        'LOGIN'      => [true, 'Ingreso', 0, [true, true], [410, 140], 'pre'],
        'A'          => [false, 'Audiómetro', 1, [true, true], [740, 560], 'pre'],
        'W'          => [false, 'Lista de Palabras', 2, [true, true], [170, 500], 'pre'],
        'Z'          => [false, 'Impedanciómetro', 3, [true, true], [740, 560], 'pre'],
        'ABR'        => [false, 'Potencial evocado auditivo de tronco cerebral', 4, [false, true], 'max', 'pre'],
        'VEMP'       => [false, 'Potenciales evocados vestibulares miogénicos', 5, [false, true], 'max', 'pre'],
        'EOAS'       => [false, 'Emisor Otoacústico', 6, [false, true], 'max', 'pre'],
        'EOAC'       => [false, 'Emisor Otoacústico Clínico', 7, [false, true], [1000, 600], 'development'],
        'VNG'        => [false, 'Videonistagmografía', 8, [false, true], [1000, 600], 'development'],
        'VHIT'       => [false, 'Video Head Impulse Test', 9, [false, true], [1000, 600], 'development'],
        'POS'        => [false, 'Posturografía', 10, [false, true], [1000, 600], 'development'],
        'CVOICE'     => [false, 'Comandos de Voz', 11, [true, true], [420, 200], 'pre'],
        'AGENDA'     => [false, 'Agenda', 13, [true, true], [900, 400], 'pre'],
        'CHAT'       => [false, 'Hablar con el paciente', 14, [true, true], [480, 280], 'pre'],
        'AC'         => [false, 'Acumetría', 15, [true, true], [480, 420], 'pre'],
        'OT'         => [false, 'Otoscopia', 16, [true, true], [520, 340], 'pre'],
        'INBOX'      => [false, 'Bandeja de entrada', 17, [true, true], [700, 480], 'pre'],
        'FICHA'      => [false, 'Ficha clínica', 18, [false, true], [480, 560], 'pre'],
        'EVOLUCION'  => [false, 'Evolución', 19, [false, true], [420, 340], 'pre'],
        'MIS_PACIENTES' => [false, 'Mis pacientes', 20, [true, true], [900, 560], 'pre'],
    ];

    public const SECTORS = [
        'Camara_sono' => 'Usuario en cámara sonoamortiguada',
        'Z_OD'        => 'Usuario con oliva en OD',
        'Z_OI'        => 'Usuario con oliva en OI',
        'none'        => 'Usuario en el Box',
        'ABR'         => 'Usuario en PEATC',
    ];

    /**
     * Boxes físicos. `activo` decide si aparece como pestaña seleccionable
     * en la barra de la app; `modulos` es la lista de códigos que se
     * muestran cuando esa pestaña está activa.
     */
    public const BOXS = [
        'sala_espera' => [true,  ['AGENDA'],                                          'Sala de Espera'],
        'Box_1'       => [true,  ['OT', 'AC', 'A', 'Z'],                              'Box Audiología'],
        'Box_2'       => [true,  ['ABR', 'VEMP', 'EOAS'],                             'Box Electrofisiología'],
        'Box_3'       => [false, ['VNG', 'VHIT', 'POS'],                              'Box Otoneurología'],
    ];

    /** Payload serializable que devuelve GET /api/layout.php. */
    public static function payload(): array
    {
        return [
            'APP' => self::APPS,
            'SECTORS' => self::SECTORS,
            'BOXS' => self::BOXS,
        ];
    }
}
