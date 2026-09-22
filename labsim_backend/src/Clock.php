<?php

declare(strict_types=1);

/**
 * El reloj de la aplicación.
 *
 * Existe porque había tres relojes que no se hablaban:
 *
 * 1. SQLite. `CURRENT_TIMESTAMP` es UTC, siempre, sin importar el servidor.
 * 2. PHP. `date()` y `strtotime()` usan la zona por DEFECTO del intérprete,
 *    que sale del php.ini del hosting. El repo no la fijaba, así que el
 *    mismo código daba resultados distintos en el servidor y en la máquina
 *    de desarrollo -- y nadie podía saber cuál, porque depende de una
 *    configuración que no está acá.
 * 3. La pantalla. Las fechas se mostraban convertidas a mano a
 *    America/Santiago en algunos lugares (`patients.php`) y en otros no
 *    (`CaseBuilder::fechaNacFromHoras`, que calcula con `date()`).
 *
 * El resultado era que un recién nacido de dos horas de vida podía quedar
 * con fecha de ayer en pantalla, según a qué hora se cargara y en qué zona
 * estuviera el servidor.
 *
 * Ahora hay una sola regla y no depende del hosting:
 *
 *   - Se guarda en UTC (ya lo hacía SQLite).
 *   - Se CALCULA y se MUESTRA en self::ZONA, que está declarada acá.
 *   - `bootstrap.php` fija esa zona al arrancar cada request, así que el
 *     php.ini del servidor deja de importar.
 *
 * Lo que NO se hace es mostrar cada fecha en la zona del computador del que
 * mira. Suena razonable y es un error para esta aplicación: las horas de
 * una cita son del CURSO, no del que las lee. Dos alumnos de la misma clase
 * con los relojes distintos verían horarios distintos para la misma cita, y
 * el que tuviera la zona mal configurada llegaría tarde convencido de que
 * llegaba a tiempo. La zona del cliente sí se usa, pero solo para AVISAR
 * que no coincide (ver api/clock.php y el reloj de admin/index.php).
 */
class Clock
{
    /**
     * Zona en la que la aplicación calcula y muestra las fechas.
     *
     * Es la de la institución, no la del servidor ni la del que mira. El
     * desfase del horario de verano lo maneja DateTimeZone solo.
     */
    public const ZONA = 'America/Santiago';

    /** Cómo se guarda en la base: UTC, sin excepción. */
    public const ZONA_ALMACENAMIENTO = 'UTC';

    /**
     * Fija la zona del intérprete. La llama bootstrap.php.
     *
     * Devuelve la que tenía el php.ini antes, que es el único lugar donde
     * se puede ver qué zona trae el servidor (después de esto, ya no).
     */
    public static function pin(): string
    {
        $previa = date_default_timezone_get();
        date_default_timezone_set(self::ZONA);
        return $previa;
    }

    /** Ahora, en la zona de la aplicación. */
    public static function now(): DateTimeImmutable
    {
        return new DateTimeImmutable('now', new DateTimeZone(self::ZONA));
    }

    /**
     * Una marca guardada (UTC) leída en la zona de la aplicación.
     *
     * $utc es lo que viene de la base: 'YYYY-MM-DD HH:MM:SS' en UTC.
     */
    public static function fromUtc(string $utc): DateTimeImmutable
    {
        $dt = new DateTimeImmutable($utc, new DateTimeZone(self::ZONA_ALMACENAMIENTO));
        return $dt->setTimezone(new DateTimeZone(self::ZONA));
    }

    /** Desfase de la zona de la aplicación ahora mismo, en minutos. */
    public static function offsetMinutes(): int
    {
        $tz = new DateTimeZone(self::ZONA);
        return (int) ($tz->getOffset(new DateTime('now', new DateTimeZone('UTC'))) / 60);
    }

    /**
     * Todo lo que hace falta para comparar este reloj con otro.
     *
     * `php_ini` es la zona que trae el servidor: es el dato que no se podía
     * averiguar desde afuera y por el que existe el endpoint.
     *
     * $previa es lo que devolvió pin() al arrancar la request; si no se
     * pasa, se informa la que esté puesta (que después de pin() es la de la
     * aplicación, o sea el dato deja de servir -- por eso bootstrap la
     * guarda).
     */
    public static function info(?string $previa = null): array
    {
        $tz = new DateTimeZone(self::ZONA);
        $ahoraUtc = new DateTime('now', new DateTimeZone('UTC'));
        $php = $previa !== null ? $previa : date_default_timezone_get();
        return [
            // Lo único absoluto: con esto el cliente calcula su propio
            // desfase sin discutir zonas.
            'utc' => $ahoraUtc->format('Y-m-d H:i:s'),
            'epoch' => (int) $ahoraUtc->format('U'),
            // La zona de la aplicación, que es la que manda.
            'zona' => self::ZONA,
            'zona_offset_min' => self::offsetMinutes(),
            'local' => self::now()->format('Y-m-d H:i:s'),
            'horario_verano' => (bool) self::now()->format('I'),
            // La del servidor, para poder verla.
            'php_ini' => $php,
            'php_ini_coincide' => $php === self::ZONA,
            // Y cómo se guarda, para confirmar que la base es UTC de verdad.
            'almacenamiento' => self::ZONA_ALMACENAMIENTO,
        ];
    }
}
