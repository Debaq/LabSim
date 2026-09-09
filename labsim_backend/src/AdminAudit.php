<?php

final class AdminAudit
{
    /**
     * Deja registro de una acción de administración (crear/eliminar
     * usuario, restaurar backup, borrar caso...). Nunca corta la request si
     * falla el INSERT -- una auditoría rota no debería tumbar la acción que
     * está registrando.
     */
    public static function log(array $admin, string $action, array $details = []): void
    {
        try {
            Db::get()->prepare(
                'INSERT INTO admin_audit_log (admin_user_id, admin_username, action, details) VALUES (?, ?, ?, ?)'
            )->execute([
                (int) $admin['id'],
                (string) $admin['username'],
                $action,
                $details ? json_encode($details, JSON_UNESCAPED_UNICODE) : null,
            ]);
        } catch (Throwable $e) {
            error_log('AdminAudit::log falló: ' . $e->getMessage());
        }
    }
}
