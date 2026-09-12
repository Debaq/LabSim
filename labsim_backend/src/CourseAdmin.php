<?php

/**
 * Todo lo que ESCRIBE la página de curso (admin/courses.php). La vista
 * quedó partida en pestañas (views/course/_*.php) y el POST no puede vivir
 * en una de ellas: el formulario de una pestaña se procesa antes de saber
 * cuál se va a pintar. Acá está el único lugar donde el curso se modifica,
 * con su auditoría al lado.
 *
 * handle() devuelve el resultado para la vista (error / aviso / tabla del
 * alta masiva) y en qué pestaña dejar al docente, en vez de imprimir nada:
 * quien renderiza es courses.php.
 */
final class CourseAdmin
{
    /**
     * Dónde vive cada formulario. Después de un POST hay que volver a la
     * pestaña de donde salió; sacarlo de la acción evita meter un <input
     * hidden name="tab"> en los diecisiete formularios de la página.
     */
    public const TAB_BY_ACTION = [
        'rename_course' => 'resumen',
        'toggle_active' => 'resumen',
        'add_student' => 'personas',
        'bulk_add_students' => 'personas',
        'remove_student' => 'personas',
        'bulk_enroll_selected' => 'personas',
        'add_teacher' => 'personas',
        'remove_teacher' => 'personas',
        'create_group' => 'personas',
        'rename_group' => 'personas',
        'delete_group' => 'personas',
        'split_groups' => 'personas',
        'set_modules' => 'modulos',
        'set_params' => 'modulos',
        'reset_params' => 'modulos',
        'generate_demo_code' => 'pruebas',
        'clean_demo' => 'pruebas',
        'link_lti_context' => 'vinculos',
    ];

    public static function tabForAction(string $action): ?string
    {
        return self::TAB_BY_ACTION[$action] ?? null;
    }

    /**
     * Procesa el POST de la página de curso. El CSRF y la sesión los valida
     * quien llama (courses.php). 'create_course' redirige al curso nuevo y
     * no vuelve de acá.
     *
     * @return array{error: ?string, success: ?string, bulk: array, tab: ?string}
     */
    public static function handle(array $me, array $post): array
    {
        $isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
        $action = (string) ($post['form_action'] ?? '');
        $courseId = (int) ($post['course_id'] ?? 0);
        $res = ['error' => null, 'success' => null, 'bulk' => [], 'tab' => self::tabForAction($action)];

        if ($action === 'create_course') {
            if (!$isFullAdmin) {
                http_response_code(403);
                exit('Requiere permisos de administrador completo.');
            }
            $name = trim((string) ($post['name'] ?? ''));
            if ($name === '') {
                $res['error'] = 'Falta el nombre del curso.';
                return $res;
            }
            $newId = Courses::create($name);
            AdminAudit::log($me, 'course_create', ['course_id' => $newId, 'name' => $name]);
            header('Location: courses.php?id=' . $newId);
            exit;
        }

        if ($courseId <= 0) {
            return $res;
        }
        Courses::assertAdministers($courseId, $me);

        switch ($action) {
            case 'rename_course':
                if (!$isFullAdmin) {
                    break;
                }
                $name = trim((string) ($post['name'] ?? ''));
                if ($name === '') {
                    $res['error'] = 'Falta el nombre del curso.';
                    break;
                }
                Courses::rename($courseId, $name);
                $res['success'] = 'Curso actualizado.';
                AdminAudit::log($me, 'course_rename', ['course_id' => $courseId, 'name' => $name]);
                break;

            case 'toggle_active':
                if (!$isFullAdmin) {
                    break;
                }
                $course = Courses::find($courseId);
                if ($course) {
                    Courses::setActive($courseId, !$course['active']);
                    $res['success'] = $course['active'] ? 'Curso archivado.' : 'Curso activado.';
                    AdminAudit::log($me, $course['active'] ? 'course_archive' : 'course_activate', ['course_id' => $courseId]);
                }
                break;

            case 'set_modules':
                $codes = array_map('strval', (array) ($post['modules'] ?? []));
                Courses::setEnabledModules($courseId, $codes);
                $res['success'] = 'Módulos actualizados.';
                AdminAudit::log($me, 'course_set_modules', ['course_id' => $courseId, 'modules' => Courses::enabledModules($courseId)]);
                break;

            // Un solo par de acciones para TODOS los parámetros configurables
            // por curso (normativa ABR, VEMP y lo que se sume): la forma de
            // cada key vive en CourseParams, no en un handler por examen.
            case 'set_params':
            case 'reset_params':
                $paramKey = (string) ($post['param_key'] ?? '');
                $def = CourseParams::find($paramKey);
                if ($def === null) {
                    $res['error'] = 'Parámetro desconocido.';
                    break;
                }
                if ($action === 'reset_params') {
                    AppConfig::clearCourseOverride($paramKey, $courseId);
                    $res['success'] = $def['title'] . ': restablecido al default de la app.';
                    AdminAudit::log($me, 'course_reset_params', ['course_id' => $courseId, 'param_key' => $paramKey]);
                    break;
                }
                $override = CourseParams::parse($paramKey, (array) ($post['params'] ?? []));
                if ($override) {
                    AppConfig::set($paramKey, $override, $courseId);
                    $res['success'] = 'Configuración guardada -- el curso sobreescribe ' . self::contarValores($override) . ' valor(es).';
                } else {
                    // parse() omite lo que quedó igual al default: si no sobra
                    // nada, el curso no tiene por qué tener override.
                    AppConfig::clearCourseOverride($paramKey, $courseId);
                    $res['success'] = 'Todo quedó igual al default de la app -- el curso vuelve a heredarlo.';
                }
                AdminAudit::log($me, 'course_set_params', ['course_id' => $courseId, 'param_key' => $paramKey, 'override' => $override]);
                break;

            case 'generate_demo_code':
                $result = Courses::generateDemoAccessCode($courseId);
                $minutos = intdiv(Auth::secondsUntil($result['expires_at']), 60);
                $res['success'] = "Código para entrar como {$result['username']}: {$result['code']} (vence en {$minutos} min).";
                AdminAudit::log($me, 'course_generate_demo_code', ['course_id' => $courseId, 'username' => $result['username']]);
                break;

            case 'clean_demo':
                Courses::cleanDemoData($courseId);
                $res['success'] = 'Datos de prueba del demo eliminados (la cuenta y su contraseña siguen igual).';
                AdminAudit::log($me, 'course_clean_demo', ['course_id' => $courseId]);
                break;

            case 'add_teacher':
                if (!$isFullAdmin) {
                    break;
                }
                $username = trim((string) ($post['username'] ?? ''));
                $err = Courses::addMemberByUsername($courseId, $username, 'teacher');
                if ($err) {
                    $res['error'] = $err;
                    break;
                }
                $res['success'] = 'Docente agregado.';
                AdminAudit::log($me, 'course_add_teacher', ['course_id' => $courseId, 'username' => $username]);
                break;

            case 'remove_teacher':
                if (!$isFullAdmin) {
                    break;
                }
                $teacherId = (int) ($post['user_id'] ?? 0);
                Courses::removeTeacher($courseId, $teacherId);
                $res['success'] = 'Docente quitado del curso.';
                AdminAudit::log($me, 'course_remove_teacher', ['course_id' => $courseId, 'user_id' => $teacherId]);
                break;

            case 'add_student':
                $username = trim((string) ($post['username'] ?? ''));
                $displayName = trim((string) ($post['display_name'] ?? ''));
                $result = Courses::addOrCreateStudentByUsername($courseId, $username, $displayName);
                if ($result['status'] === 'error') {
                    $res['error'] = $result['message'];
                    break;
                }
                $res['success'] = $result['status'] === 'created'
                    ? "Alumno '{$username}' creado y matriculado. Contraseña temporal: {$result['password']}"
                    : 'Alumno agregado al curso.';
                AdminAudit::log($me, 'course_add_student', ['course_id' => $courseId, 'username' => $username, 'status' => $result['status']]);
                break;

            case 'bulk_add_students':
                $res['bulk'] = Courses::bulkAddStudents($courseId, (string) ($post['bulk_students'] ?? ''));
                $creadas = count(array_filter($res['bulk'], static fn(array $r): bool => $r['status'] === 'created'));
                $matriculados = count(array_filter($res['bulk'], static fn(array $r): bool => $r['status'] === 'enrolled'));
                $errores = count(array_filter($res['bulk'], static fn(array $r): bool => $r['status'] === 'error'));
                $res['success'] = "{$creadas} cuenta(s) creada(s), {$matriculados} matriculado(s), {$errores} error(es).";
                AdminAudit::log($me, 'course_bulk_add_students', [
                    'course_id' => $courseId, 'created' => $creadas, 'enrolled' => $matriculados, 'errors' => $errores,
                ]);
                break;

            case 'remove_student':
                $studentId = (int) ($post['user_id'] ?? 0);
                Courses::removeStudent($courseId, $studentId);
                $res['success'] = 'Alumno quitado del curso.';
                AdminAudit::log($me, 'course_remove_student', ['course_id' => $courseId, 'user_id' => $studentId]);
                break;

            case 'bulk_enroll_selected':
                $userIds = array_map('intval', (array) ($post['user_ids'] ?? []));
                $n = Courses::enrollExistingUsers($courseId, $userIds);
                $res['success'] = "{$n} alumno(s) matriculado(s).";
                AdminAudit::log($me, 'course_bulk_enroll', ['course_id' => $courseId, 'count' => $n]);
                break;

            case 'create_group':
                $name = trim((string) ($post['name'] ?? ''));
                if ($name === '') {
                    $res['error'] = 'Falta el nombre del grupo.';
                    break;
                }
                Courses::createGroup($courseId, $name);
                $res['success'] = 'Grupo creado.';
                AdminAudit::log($me, 'group_create', ['course_id' => $courseId, 'name' => $name]);
                break;

            // El group_id llega del navegador: tener acceso al curso no
            // alcanza, hay que confirmar que el grupo sea de ESTE curso.
            case 'rename_group':
            case 'delete_group':
                $groupId = (int) ($post['group_id'] ?? 0);
                if (!Courses::groupBelongsTo($groupId, $courseId)) {
                    $res['error'] = 'Ese grupo no pertenece a este curso.';
                    break;
                }
                if ($action === 'delete_group') {
                    Courses::deleteGroup($groupId);
                    $res['success'] = 'Grupo eliminado.';
                    AdminAudit::log($me, 'group_delete', ['course_id' => $courseId, 'group_id' => $groupId]);
                    break;
                }
                $name = trim((string) ($post['name'] ?? ''));
                if ($name === '') {
                    $res['error'] = 'Falta el nombre del grupo.';
                    break;
                }
                Courses::renameGroup($groupId, $name);
                $res['success'] = 'Grupo renombrado.';
                AdminAudit::log($me, 'group_rename', ['course_id' => $courseId, 'group_id' => $groupId, 'name' => $name]);
                break;

            case 'split_groups':
                $n = (int) ($post['n_groups'] ?? 0);
                if ($n < 2 || $n > 40) {
                    $res['error'] = 'Elige entre 2 y 40 grupos.';
                    break;
                }
                $repartidos = Courses::splitUngroupedIntoGroups($courseId, $n, trim((string) ($post['group_prefix'] ?? 'Grupo')));
                $res['success'] = $repartidos > 0
                    ? "{$repartidos} alumno(s) repartido(s) en {$n} grupo(s) nuevo(s)."
                    : 'No había alumnos sin grupo -- no se creó nada.';
                AdminAudit::log($me, 'course_split_groups', ['course_id' => $courseId, 'n' => $n, 'repartidos' => $repartidos]);
                break;

            case 'link_lti_context':
                $platformId = (int) ($post['lti_platform_id'] ?? 0);
                $contextId = trim((string) ($post['lti_context_id'] ?? ''));
                if ($platformId <= 0 || $contextId === '') {
                    $res['error'] = 'Datos de vínculo inválidos.';
                    break;
                }
                Lti::linkContextToCourse($platformId, $contextId, $courseId);
                $res['success'] = 'Curso de Moodle vinculado -- los alumnos que entren por ahí se matricularán solos.';
                AdminAudit::log($me, 'course_link_lti_context', [
                    'course_id' => $courseId, 'lti_platform_id' => $platformId, 'context_id' => $contextId,
                ]);
                break;
        }

        return $res;
    }

    /** Cuántos valores sueltos trae un override {grupo:{fila:{campo:valor}}}. */
    private static function contarValores(array $override): int
    {
        $n = 0;
        foreach ($override as $filas) {
            foreach ($filas as $campos) {
                $n += count($campos);
            }
        }
        return $n;
    }
}
