<?php

final class Courses
{
    /**
     * Copia a mano de los módulos "pre" (listos para usar, no en desarrollo)
     * de Layout::APPS del lado del backend -- la lista de módulos bloqueables
     * por curso no puede vivir en el cliente (un alumno con binario viejo
     * podría destrabar lo que el docente le bloqueó). Si se agrega/saca un
     * módulo "pre" en Layout::APPS, actualizar esto también, o el checklist
     * de courses.php queda desincronizado.
     * "LOGIN" no entra: es la pantalla de ingreso, no un módulo que se
     * pueda bloquear por curso.
     */
    public const MODULES = [
        'A' => 'Audiómetro',
        'W' => 'Lista de Palabras',
        'Z' => 'Impedanciómetro',
        'ABR' => 'Potencial evocado auditivo de tronco cerebral',
        'CVOICE' => 'Comandos de Voz',
        'CVC' => 'Campo Visual Computarizado',
        'AGENDA' => 'Agenda',
        'CHAT' => 'Hablar con el paciente',
        'AC' => 'Acumetría',
        'OT' => 'Otoscopia',
        'INBOX' => 'Bandeja de entrada',
        'FICHA' => 'Ficha clínica',
        'EVOLUCION' => 'Evolución',
    ];

    /** Cursos donde $userId es docente (course_teachers). */
    public static function teacherCourseIds(int $userId): array
    {
        $stmt = Db::get()->prepare('SELECT course_id FROM course_teachers WHERE user_id = ?');
        $stmt->execute([$userId]);
        return array_map('intval', array_column($stmt->fetchAll(), 'course_id'));
    }

    /** Alumnos matriculados (course_students) en cualquiera de $courseIds. */
    public static function rosterUserIds(array $courseIds): array
    {
        if (!$courseIds) {
            return [];
        }
        $placeholders = implode(',', array_fill(0, count($courseIds), '?'));
        $stmt = Db::get()->prepare("SELECT DISTINCT user_id FROM course_students WHERE course_id IN ({$placeholders})");
        $stmt->execute($courseIds);
        return array_map('intval', array_column($stmt->fetchAll(), 'user_id'));
    }

    /** true si $userId está matriculado (course_students) en $courseId. */
    public static function isStudentOf(int $userId, int $courseId): bool
    {
        $stmt = Db::get()->prepare('SELECT 1 FROM course_students WHERE course_id = ? AND user_id = ?');
        $stmt->execute([$courseId, $userId]);
        return (bool) $stmt->fetchColumn();
    }

    /**
     * Códigos de módulo habilitados para $courseId (ver course_modules en
     * sql/schema.sql). Lista vacía si el docente todavía no configuró nada
     * -- ese curso no tiene ningún módulo habilitado hasta que lo haga.
     */
    public static function enabledModules(int $courseId): array
    {
        $stmt = Db::get()->prepare('SELECT module_code FROM course_modules WHERE course_id = ? ORDER BY module_code');
        $stmt->execute([$courseId]);
        return array_column($stmt->fetchAll(), 'module_code');
    }

    /**
     * Reemplaza por completo el set de módulos habilitados de $courseId.
     * Códigos que no están en self::MODULES se descartan en silencio -- el
     * formulario que llama a esto ya solo manda checkboxes con códigos
     * válidos, esto es el resguardo del lado servidor.
     */
    public static function setEnabledModules(int $courseId, array $moduleCodes): void
    {
        $pdo = Db::get();
        $pdo->beginTransaction();
        try {
            $pdo->prepare('DELETE FROM course_modules WHERE course_id = ?')->execute([$courseId]);
            $stmt = $pdo->prepare('INSERT INTO course_modules (course_id, module_code) VALUES (?, ?)');
            foreach (array_unique($moduleCodes) as $code) {
                $code = strtoupper(trim((string) $code));
                if (!array_key_exists($code, self::MODULES)) {
                    continue;
                }
                $stmt->execute([$courseId, $code]);
            }
            $pdo->commit();
        } catch (Throwable $e) {
            $pdo->rollBack();
            throw $e;
        }
    }

    public static function listActive(): array
    {
        return Db::get()->query('SELECT * FROM courses WHERE active = 1 ORDER BY name')->fetchAll();
    }

    public static function find(int $courseId): ?array
    {
        $stmt = Db::get()->prepare('SELECT * FROM courses WHERE id = ?');
        $stmt->execute([$courseId]);
        $row = $stmt->fetch();
        return $row ?: null;
    }

    public static function create(string $name): int
    {
        Db::get()->prepare('INSERT INTO courses (name) VALUES (?)')->execute([$name]);
        return (int) Db::get()->lastInsertId();
    }

    public static function rename(int $courseId, string $name): void
    {
        Db::get()->prepare('UPDATE courses SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
            ->execute([$name, $courseId]);
    }

    public static function setActive(int $courseId, bool $active): void
    {
        Db::get()->prepare('UPDATE courses SET active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
            ->execute([$active ? 1 : 0, $courseId]);
    }

    public static function teachers(int $courseId): array
    {
        $stmt = Db::get()->prepare(
            'SELECT u.id, u.username, u.display_name FROM course_teachers ct
             JOIN users u ON u.id = ct.user_id WHERE ct.course_id = ? ORDER BY u.display_name'
        );
        $stmt->execute([$courseId]);
        return $stmt->fetchAll();
    }

    /** Incluye al estudiante demo si el curso tiene uno (ver is_demo) -- quien
     * llama filtra según lo necesite: admin/courses.php lo separa en su
     * propia card "Área de pruebas", agenda.php lo deja para poder
     * asignarle citas igual que a cualquier alumno real. */
    public static function students(int $courseId): array
    {
        $stmt = Db::get()->prepare(
            'SELECT u.id, u.username, u.display_name, u.is_demo FROM course_students cs
             JOIN users u ON u.id = cs.user_id WHERE cs.course_id = ? ORDER BY u.display_name'
        );
        $stmt->execute([$courseId]);
        return $stmt->fetchAll();
    }

    /** Agrega un usuario existente (buscado por username) como docente o alumno del curso. */
    public static function addMemberByUsername(int $courseId, string $username, string $kind): ?string
    {
        $stmt = Db::get()->prepare("SELECT id, role FROM users WHERE username = ?");
        $stmt->execute([$username]);
        $user = $stmt->fetch();
        if (!$user) {
            return "Usuario '{$username}' no encontrado.";
        }
        $table = $kind === 'teacher' ? 'course_teachers' : 'course_students';
        Db::get()->prepare("INSERT OR IGNORE INTO {$table} (course_id, user_id) VALUES (?, ?)")
            ->execute([$courseId, (int) $user['id']]);
        return null;
    }

    /**
     * Alumnos activos que NO están matriculados en $courseId todavía, con el
     * nombre del curso Moodle de donde vinieron la última vez si LTI lo
     * informó (ver user_lti_contexts) -- para buscar/filtrar/agrupar en la
     * UI de matrícula en bloque en vez de tipear username por username.
     */
    public static function enrollableStudents(int $courseId): array
    {
        $stmt = Db::get()->prepare(
            "SELECT u.id, u.username, u.display_name,
                    (SELECT context_label FROM user_lti_contexts WHERE user_id = u.id ORDER BY last_seen_at DESC LIMIT 1) AS origin
             FROM users u
             WHERE u.role = 'student' AND u.active = 1 AND u.is_demo = 0
               AND u.id NOT IN (SELECT user_id FROM course_students WHERE course_id = ?)
             ORDER BY u.display_name"
        );
        $stmt->execute([$courseId]);
        return $stmt->fetchAll();
    }

    /** Matricula varios alumnos ya existentes de una vez (por id). Devuelve cuántos quedaron matriculados. */
    public static function enrollExistingUsers(int $courseId, array $userIds): int
    {
        $stmt = Db::get()->prepare('INSERT OR IGNORE INTO course_students (course_id, user_id) VALUES (?, ?)');
        $count = 0;
        foreach ($userIds as $userId) {
            $userId = (int) $userId;
            if ($userId <= 0) {
                continue;
            }
            $stmt->execute([$courseId, $userId]);
            $count += $stmt->rowCount();
        }
        return $count;
    }

    /**
     * Agrega un alumno al curso por username. Si no existe todavía como
     * usuario, lo crea como cuenta local (role=student, permission 444) --
     * con $password si se dio, o con una generada al azar que se devuelve
     * en el resultado para que el docente se la entregue al alumno.
     */
    public static function addOrCreateStudentByUsername(int $courseId, string $username, string $displayName = '', ?string $password = null): array
    {
        $username = trim($username);
        if ($username === '') {
            return ['status' => 'error', 'username' => $username, 'message' => 'Falta el username.'];
        }

        $stmt = Db::get()->prepare('SELECT id FROM users WHERE username = ?');
        $stmt->execute([$username]);
        $user = $stmt->fetch();

        if ($user) {
            $userId = (int) $user['id'];
            Db::get()->prepare('INSERT OR IGNORE INTO course_students (course_id, user_id) VALUES (?, ?)')
                ->execute([$courseId, $userId]);
            return ['status' => 'enrolled', 'username' => $username, 'message' => 'Ya existía -- matriculado.'];
        }

        $generated = null;
        if ($password === null || $password === '') {
            $generated = bin2hex(random_bytes(6));
            $password = $generated;
        } elseif (strlen($password) < 8) {
            return ['status' => 'error', 'username' => $username, 'message' => 'No existía y la contraseña indicada tiene menos de 8 caracteres.'];
        }

        require_once __DIR__ . '/Users.php';
        $userId = Users::createOrUpdateLocal('student', $username, $displayName !== '' ? $displayName : $username, $password, 444);
        Db::get()->prepare('INSERT OR IGNORE INTO course_students (course_id, user_id) VALUES (?, ?)')
            ->execute([$courseId, $userId]);

        return [
            'status' => 'created',
            'username' => $username,
            'message' => 'Cuenta creada y matriculada.',
            'password' => $generated,
        ];
    }

    /**
     * Crea el estudiante demo del curso: cuenta local (role=student,
     * is_demo=1) matriculada normalmente vía course_students -- es "un
     * alumno más" para todo efecto (se le pueden asignar citas igual que a
     * cualquier real), salvo que queda excluido de las vistas agregadas por
     * curso (ver dashboard.php). A lo más uno por curso -- error si
     * $courseId ya tiene demo_user_id (usar regenerateDemoPassword() para
     * una credencial nueva sin perder los datos acumulados).
     */
    public static function generateDemoStudent(int $courseId): array
    {
        $course = self::find($courseId);
        if (!$course) {
            return ['status' => 'error', 'message' => 'Curso no encontrado.'];
        }
        if ($course['demo_user_id']) {
            return ['status' => 'error', 'message' => 'Este curso ya tiene un estudiante demo.'];
        }

        $username = 'demo_curso_' . $courseId;
        $result = self::addOrCreateStudentByUsername($courseId, $username, 'Estudiante demo', null);
        if ($result['status'] === 'error') {
            return $result;
        }

        $pdo = Db::get();
        $stmt = $pdo->prepare('SELECT id FROM users WHERE username = ?');
        $stmt->execute([$username]);
        $userId = (int) $stmt->fetchColumn();
        $pdo->prepare('UPDATE users SET is_demo = 1 WHERE id = ?')->execute([$userId]);
        $pdo->prepare('UPDATE courses SET demo_user_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
            ->execute([$userId, $courseId]);

        return ['status' => 'created', 'username' => $username, 'password' => $result['password'] ?? null];
    }

    /** Nueva contraseña para el demo existente del curso, sin tocar sus datos. Null si el curso no tiene demo. */
    public static function regenerateDemoPassword(int $courseId): ?array
    {
        $course = self::find($courseId);
        $userId = $course['demo_user_id'] ?? null;
        if (!$userId) {
            return null;
        }
        $pdo = Db::get();
        $stmt = $pdo->prepare('SELECT username FROM users WHERE id = ?');
        $stmt->execute([$userId]);
        $username = $stmt->fetchColumn();
        if ($username === false) {
            return null;
        }
        $password = bin2hex(random_bytes(6));
        $pdo->prepare('UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
            ->execute([password_hash($password, PASSWORD_DEFAULT), (int) $userId]);
        return ['username' => $username, 'password' => $password];
    }

    /**
     * Borra todo lo que el demo del curso acumuló probando la app (sus
     * propias citas, atenciones, chats con paciente, comentarios, logs de
     * acción, bandeja) -- deja la cuenta y su contraseña intactas, para
     * volver a probar desde cero. No toca patients/cases: son el pool
     * compartido, no son datos del demo. No-op si el curso no tiene demo.
     */
    public static function cleanDemoData(int $courseId): void
    {
        $course = self::find($courseId);
        $userId = $course['demo_user_id'] ?? null;
        if (!$userId) {
            return;
        }
        $userId = (int) $userId;
        $pdo = Db::get();

        $stmt = $pdo->prepare('SELECT id FROM appointments WHERE assigned_student_id = ?');
        $stmt->execute([$userId]);
        $apptIds = array_map('intval', array_column($stmt->fetchAll(), 'id'));

        $stmt = $pdo->prepare('SELECT id FROM attendances WHERE student_id = ?');
        $stmt->execute([$userId]);
        $attIds = array_map('intval', array_column($stmt->fetchAll(), 'id'));

        $stmt = $pdo->prepare('SELECT id FROM llm_chat_logs WHERE student_id = ?');
        $stmt->execute([$userId]);
        $chatLogIds = array_map('intval', array_column($stmt->fetchAll(), 'id'));

        $pdo->beginTransaction();
        try {
            // Orden por FK (PRAGMA foreign_keys=ON, ver Db::get()): hijos
            // antes que padres -- chat_comments/attendance_comments antes de
            // llm_chat_logs/attendances, y esas dos e inbox_messages antes
            // de appointments.
            if ($chatLogIds) {
                $ph = implode(',', array_fill(0, count($chatLogIds), '?'));
                $pdo->prepare("DELETE FROM chat_comments WHERE chat_log_id IN ({$ph})")->execute($chatLogIds);
            }
            if ($attIds) {
                $ph = implode(',', array_fill(0, count($attIds), '?'));
                $pdo->prepare("DELETE FROM attendance_comments WHERE attendance_id IN ({$ph})")->execute($attIds);
            }
            $pdo->prepare('DELETE FROM llm_chat_logs WHERE student_id = ?')->execute([$userId]);
            $pdo->prepare('DELETE FROM attendances WHERE student_id = ?')->execute([$userId]);
            $pdo->prepare('DELETE FROM inbox_messages WHERE student_id = ?')->execute([$userId]);
            $pdo->prepare('DELETE FROM action_logs WHERE user_id = ?')->execute([$userId]);
            if ($apptIds) {
                $ph = implode(',', array_fill(0, count($apptIds), '?'));
                $pdo->prepare("DELETE FROM appointments WHERE id IN ({$ph})")->execute($apptIds);
            }
            $pdo->commit();
        } catch (Throwable $e) {
            $pdo->rollBack();
            throw $e;
        }
    }

    /**
     * Procesa varias líneas "username[, nombre completo][, password]" -- una
     * por alumno. Cada línea se procesa independiente (no aborta en bloque
     * si una falla) y se devuelve el resultado de todas para mostrar en la UI.
     */
    public static function bulkAddStudents(int $courseId, string $rawText): array
    {
        $results = [];
        foreach (preg_split('/\r\n|\r|\n/', $rawText) as $line) {
            $line = trim($line);
            if ($line === '') {
                continue;
            }
            $parts = array_map('trim', explode(',', $line));
            $username = $parts[0] ?? '';
            $displayName = $parts[1] ?? '';
            $password = isset($parts[2]) && $parts[2] !== '' ? $parts[2] : null;
            $results[] = self::addOrCreateStudentByUsername($courseId, $username, $displayName, $password);
        }
        return $results;
    }

    public static function removeTeacher(int $courseId, int $userId): void
    {
        Db::get()->prepare('DELETE FROM course_teachers WHERE course_id = ? AND user_id = ?')
            ->execute([$courseId, $userId]);
    }

    /** Quita al alumno del curso y de cualquier grupo del curso al que pertenezca. */
    public static function removeStudent(int $courseId, int $userId): void
    {
        $pdo = Db::get();
        $pdo->prepare(
            'DELETE FROM group_members WHERE user_id = ? AND group_id IN (SELECT id FROM student_groups WHERE course_id = ?)'
        )->execute([$userId, $courseId]);
        $pdo->prepare('DELETE FROM course_students WHERE course_id = ? AND user_id = ?')
            ->execute([$courseId, $userId]);
    }

    public static function groupsForCourse(int $courseId): array
    {
        $stmt = Db::get()->prepare(
            "SELECT g.*, (SELECT COUNT(*) FROM group_members gm WHERE gm.group_id = g.id) AS member_count
             FROM student_groups g WHERE g.course_id = ? ORDER BY g.name"
        );
        $stmt->execute([$courseId]);
        return $stmt->fetchAll();
    }

    public static function membersOfGroup(int $groupId): array
    {
        $stmt = Db::get()->prepare(
            'SELECT u.id, u.username, u.display_name FROM group_members gm
             JOIN users u ON u.id = gm.user_id WHERE gm.group_id = ? ORDER BY u.display_name'
        );
        $stmt->execute([$groupId]);
        return $stmt->fetchAll();
    }

    public static function createGroup(int $courseId, string $name): int
    {
        Db::get()->prepare('INSERT INTO student_groups (course_id, name) VALUES (?, ?)')->execute([$courseId, $name]);
        return (int) Db::get()->lastInsertId();
    }

    public static function renameGroup(int $groupId, string $name): void
    {
        Db::get()->prepare('UPDATE student_groups SET name = ? WHERE id = ?')->execute([$name, $groupId]);
    }

    public static function deleteGroup(int $groupId): void
    {
        $pdo = Db::get();
        $pdo->prepare('DELETE FROM group_members WHERE group_id = ?')->execute([$groupId]);
        $pdo->prepare('DELETE FROM student_groups WHERE id = ?')->execute([$groupId]);
    }

    /** Agrega al alumno al grupo -- debe ya estar matriculado en el curso del grupo. */
    public static function addGroupMemberByUsername(int $groupId, int $courseId, string $username): ?string
    {
        $stmt = Db::get()->prepare('SELECT id FROM users WHERE username = ?');
        $stmt->execute([$username]);
        $user = $stmt->fetch();
        if (!$user) {
            return "Usuario '{$username}' no encontrado.";
        }
        $userId = (int) $user['id'];

        $stmt = Db::get()->prepare('SELECT 1 FROM course_students WHERE course_id = ? AND user_id = ?');
        $stmt->execute([$courseId, $userId]);
        if (!$stmt->fetch()) {
            return "'{$username}' no está matriculado en este curso todavía -- agrégalo al roster primero.";
        }

        Db::get()->prepare('INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)')
            ->execute([$groupId, $userId]);
        return null;
    }

    public static function removeGroupMember(int $groupId, int $userId): void
    {
        Db::get()->prepare('DELETE FROM group_members WHERE group_id = ? AND user_id = ?')
            ->execute([$groupId, $userId]);
    }
}
