<?php

declare(strict_types=1);

/**
 * Preferencias personales de la app de escritorio (users.prefs, JSON):
 * atajos de teclado propios y "mouse para zurdos". Viven en la cuenta y no
 * en el equipo: en el laboratorio el alumno se sienta en cualquier máquina
 * y sus preferencias lo siguen.
 *
 * Solo se guarda lo que se reconoce: acciones conocidas (mismas claves que
 * src/core/atajos.py en el cliente) y teclas simples. Una acción que no
 * viene usa la tecla por defecto.
 */
final class UserPrefs
{
    /** Acciones con atajo configurable. Mantener igual a core/atajos.py. */
    public const ACCIONES = [
        'a_ch1_subir', 'a_ch1_bajar', 'a_ch2_subir', 'a_ch2_bajar',
        'a_estimulo_ch1', 'a_estimulo_ch2', 'a_freq_menos', 'a_freq_mas',
        'a_salida_ch1', 'a_tipo_estimulo_ch1', 'a_transductor_ch1',
        'a_salida_ch2', 'a_tipo_estimulo_ch2', 'a_transductor_ch2',
        'z_subir', 'z_bajar', 'z_estimulo',
    ];

    /** Una tecla: letra, número, F1-F12 o una tecla de navegación (nombres de QKeySequence). */
    private const TECLA = '/^([A-Z0-9]|F([1-9]|1[0-2])|Up|Down|Left|Right|Space|PgUp|PgDown|Home|End)$/';

    public static function vacias(): array
    {
        return ['mouse_zurdo' => false, 'atajos' => new stdClass()];
    }

    /** @param mixed $raw */
    public static function normalizar($raw): array
    {
        $raw = is_array($raw) ? $raw : [];
        $atajos = [];
        foreach ((array) ($raw['atajos'] ?? []) as $accion => $tecla) {
            if (!in_array($accion, self::ACCIONES, true) || !is_string($tecla)) {
                continue;
            }
            $tecla = trim($tecla);
            if (strlen($tecla) === 1) {
                $tecla = strtoupper($tecla);
            }
            if (preg_match(self::TECLA, $tecla)) {
                $atajos[$accion] = $tecla;
            }
        }
        return [
            'mouse_zurdo' => !empty($raw['mouse_zurdo']),
            // Objeto JSON aunque esté vacío: el cliente espera un dict.
            'atajos' => $atajos ?: new stdClass(),
        ];
    }

    public static function leer(int $userId): array
    {
        Db::migrateUserPrefsIfNeeded();
        $stmt = Db::get()->prepare('SELECT prefs FROM users WHERE id = ?');
        $stmt->execute([$userId]);
        $json = $stmt->fetchColumn();
        return self::normalizar(json_decode((string) ($json ?: '{}'), true));
    }

    /** Guarda y devuelve lo guardado (ya normalizado). */
    public static function guardar(int $userId, $raw): array
    {
        Db::migrateUserPrefsIfNeeded();
        $prefs = self::normalizar($raw);
        Db::get()->prepare('UPDATE users SET prefs = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
            ->execute([json_encode($prefs, JSON_UNESCAPED_UNICODE), $userId]);
        return $prefs;
    }
}
