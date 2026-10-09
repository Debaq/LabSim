<?php

declare(strict_types=1);

require_once __DIR__ . '/AdminAudit.php';

/**
 * Bloqueo de cuentas: la persona no puede usar la app ni volver a entrar
 * (contraseña, código de Moodle) hasta que se la desbloquee.
 *
 * Bloquear = users.active = 0 (lo que ya respetaban el login local y la
 * validación de tokens) + revocar todas sus sesiones al instante. Sin
 * columnas nuevas: quién, cuándo y por qué quedan en admin_audit_log
 * (acción user_block), de donde los lee el panel.
 *
 * A la app le llega 403 con `codigo: cuenta_bloqueada` (ver CODIGO), para que
 * diga "cuenta bloqueada" y no "sesión vencida" (401).
 */
final class Bloqueos
{
    public const CODIGO = 'cuenta_bloqueada';
    public const MENSAJE = 'Tu cuenta está bloqueada. Habla con tu docente.';

    /**
     * Bloquea a $userId y revoca sus sesiones. Devuelve cuántas se cortaron.
     *
     * @param array<string, mixed> $admin quien bloquea (no puede ser él mismo)
     */
    public static function bloquear(PDO $pdo, array $admin, int $userId, string $motivo): int
    {
        if ($userId === (int) $admin['id']) {
            throw new InvalidArgumentException('No puedes bloquear tu propia cuenta.');
        }
        $stmt = $pdo->prepare('SELECT username FROM users WHERE id = ?');
        $stmt->execute([$userId]);
        $username = $stmt->fetchColumn();
        $stmt->closeCursor();
        if ($username === false) {
            throw new InvalidArgumentException('Ese usuario no existe.');
        }
        $motivo = trim(mb_substr($motivo, 0, 300));
        $pdo->beginTransaction();
        try {
            $pdo->prepare('UPDATE users SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
                ->execute([$userId]);
            $del = $pdo->prepare('DELETE FROM tokens WHERE user_id = ?');
            $del->execute([$userId]);
            $revocadas = $del->rowCount();
            $pdo->commit();
        } catch (Throwable $e) {
            $pdo->rollBack();
            throw $e;
        }
        AdminAudit::log($admin, 'user_block', [
            'user_id' => $userId, 'username' => $username, 'motivo' => $motivo,
            'sesiones_revocadas' => $revocadas,
        ]);
        return $revocadas;
    }

    /** @param array<string, mixed> $admin */
    public static function desbloquear(PDO $pdo, array $admin, int $userId): void
    {
        $stmt = $pdo->prepare('SELECT username FROM users WHERE id = ?');
        $stmt->execute([$userId]);
        $username = $stmt->fetchColumn();
        $stmt->closeCursor();
        if ($username === false) {
            throw new InvalidArgumentException('Ese usuario no existe.');
        }
        $pdo->prepare('UPDATE users SET active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
            ->execute([$userId]);
        AdminAudit::log($admin, 'user_unblock', ['user_id' => $userId, 'username' => $username]);
    }

    public static function estaBloqueado(PDO $pdo, int $userId): bool
    {
        $stmt = $pdo->prepare('SELECT active FROM users WHERE id = ?');
        $stmt->execute([$userId]);
        $activo = $stmt->fetchColumn();
        $stmt->closeCursor();
        return $activo !== false && (int) $activo === 0;
    }

    /**
     * Cuentas bloqueadas, con el último bloqueo registrado (quién, cuándo,
     * motivo). Las desactivadas antes de esto ('Desactivar' de users.php)
     * salen sin motivo.
     *
     * @return list<array<string, mixed>>
     */
    public static function listar(PDO $pdo): array
    {
        $filas = $pdo->query(
            "SELECT id, username, display_name, role FROM users WHERE active = 0 ORDER BY username"
        )->fetchAll(PDO::FETCH_ASSOC);
        $ultimo = $pdo->prepare(
            "SELECT admin_username, details, created_at FROM admin_audit_log
             WHERE action IN ('user_block', 'user_deactivate') AND details LIKE ?
             ORDER BY id DESC"
        );
        foreach ($filas as &$f) {
            $f['motivo'] = '';
            $f['bloqueado_por'] = '';
            $f['bloqueado_at'] = '';
            // details es JSON con user_id; LIKE acota y se confirma al decodificar.
            $ultimo->execute(['%"user_id":' . (int) $f['id'] . '%']);
            foreach ($ultimo->fetchAll(PDO::FETCH_ASSOC) as $a) {
                $d = json_decode((string) $a['details'], true);
                if (is_array($d) && (int) ($d['user_id'] ?? 0) === (int) $f['id']) {
                    $f['motivo'] = (string) ($d['motivo'] ?? '');
                    $f['bloqueado_por'] = (string) $a['admin_username'];
                    $f['bloqueado_at'] = (string) $a['created_at'];
                    break;
                }
            }
        }
        unset($f);
        return $filas;
    }
}

/** La cuenta está bloqueada: los endpoints la convierten en 403 + CODIGO. */
final class CuentaBloqueada extends RuntimeException
{
    public function __construct()
    {
        parent::__construct(Bloqueos::MENSAJE);
    }
}
