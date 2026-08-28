<?php

final class Users
{
    /**
     * Crea o actualiza un usuario con login local (usuario/contraseña).
     * Sirve tanto para admins reales como para cuentas de alumno de prueba
     * (sin LTI) -- por ejemplo la cuenta "labsim" para probar el flujo de
     * atención sin depender de Moodle.
     */
    public static function createOrUpdateLocal(
        string $role,
        string $username,
        string $displayName,
        string $password,
        int $permission,
        array $modules
    ): int {
        $hash = password_hash($password, PASSWORD_DEFAULT);
        $modulesJson = json_encode($modules, JSON_UNESCAPED_UNICODE);
        $pdo = Db::get();

        $stmt = $pdo->prepare('SELECT id FROM users WHERE username = ?');
        $stmt->execute([$username]);
        $existing = $stmt->fetch();

        if ($existing) {
            $pdo->prepare(
                'UPDATE users SET role = ?, display_name = ?, password_hash = ?, permission = ?,
                        modules = ?, active = 1, updated_at = CURRENT_TIMESTAMP
                 WHERE id = ?'
            )->execute([$role, $displayName, $hash, $permission, $modulesJson, $existing['id']]);
            return (int) $existing['id'];
        }

        $pdo->prepare(
            'INSERT INTO users (role, username, display_name, password_hash, permission, modules)
             VALUES (?, ?, ?, ?, ?, ?)'
        )->execute([$role, $username, $displayName, $hash, $permission, $modulesJson]);
        return (int) $pdo->lastInsertId();
    }

    public static function listAll(): array
    {
        return Db::get()->query(
            'SELECT id, role, username, display_name, permission, active, lti_sub, created_at
             FROM users ORDER BY role, username'
        )->fetchAll();
    }

    public static function setActive(int $userId, bool $active): void
    {
        Db::get()->prepare('UPDATE users SET active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
            ->execute([$active ? 1 : 0, $userId]);
    }
}
