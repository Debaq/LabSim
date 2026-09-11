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
        int $permission
    ): int {
        $hash = password_hash($password, PASSWORD_DEFAULT);
        $pdo = Db::get();

        $stmt = $pdo->prepare('SELECT id FROM users WHERE username = ?');
        $stmt->execute([$username]);
        $existing = $stmt->fetch();

        if ($existing) {
            $pdo->prepare(
                'UPDATE users SET role = ?, display_name = ?, password_hash = ?, permission = ?,
                        active = 1, updated_at = CURRENT_TIMESTAMP
                 WHERE id = ?'
            )->execute([$role, $displayName, $hash, $permission, $existing['id']]);
            return (int) $existing['id'];
        }

        $pdo->prepare(
            'INSERT INTO users (role, username, display_name, password_hash, permission)
             VALUES (?, ?, ?, ?, ?)'
        )->execute([$role, $username, $displayName, $hash, $permission]);
        return (int) $pdo->lastInsertId();
    }

    /** Cambia rol/permiso/nombre de una cuenta existente sin tocar su password_hash. */
    public static function updateProfile(int $userId, string $role, int $permission, string $displayName): void
    {
        Db::get()->prepare(
            'UPDATE users SET role = ?, permission = ?, display_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        )->execute([$role, $permission, $displayName, $userId]);
    }

    /**
     * Contraseña de login local de una cuenta (la que se escribe en la app
     * de escritorio, ver api/admin_login.php). Una cuenta creada por LTI
     * nace sin password_hash: esto es lo que se la pone, sin tocar nada más
     * de la cuenta.
     */
    public static function setPassword(int $userId, string $password): void
    {
        Db::get()->prepare(
            'UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        )->execute([password_hash($password, PASSWORD_DEFAULT), $userId]);
    }

    /**
     * Usuario de login elegido por la propia persona (admin/perfil.php).
     * Marca username_locked: un launch LTI reescribe username con el email o
     * el nombre de Moodle en cada entrada (ver Lti::upsertStudentBySub), y
     * eso le cambiaría el usuario de la app por debajo cada vez.
     */
    public static function setUsername(int $userId, string $username): void
    {
        Db::get()->prepare(
            'UPDATE users SET username = ?, username_locked = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        )->execute([$username, $userId]);
    }

    /** ¿Ese usuario ya lo tiene otra cuenta? Sin distinguir mayúsculas (se escribe a mano en la app). */
    public static function usernameTaken(string $username, int $exceptUserId): bool
    {
        $stmt = Db::get()->prepare('SELECT 1 FROM users WHERE lower(username) = lower(?) AND id != ?');
        $stmt->execute([$username, $exceptUserId]);
        return (bool) $stmt->fetch();
    }

    public static function setDisplayName(int $userId, string $displayName): void
    {
        Db::get()->prepare(
            'UPDATE users SET display_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        )->execute([$displayName, $userId]);
    }

    /**
     * Formato del usuario de login: lo tipea una persona en la app, sin
     * teclado cómodo. La arroba entra porque LTI usa el email de Moodle como
     * username cuando la plataforma lo comparte, y ese sí se puede escribir;
     * lo que queda afuera es el fallback opaco "Nombre (1:42)" con espacios y
     * paréntesis.
     */
    public static function usernameValido(string $username): bool
    {
        return (bool) preg_match('/^[a-zA-Z0-9._@+-]{3,64}$/', $username);
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
