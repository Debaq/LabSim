<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/../../src/Patients.php';

/**
 * Configuración de agendas por curso/grupo/alumno: agendar, reagendar,
 * cancelar/restaurar o eliminar citas, y el calendario mensual de ocupación.
 * La base de datos de fichas clínicas (todos los pacientes/casos, agendados
 * o no) vive aparte en patients.php.
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();
$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
$myCourseIds = $isFullAdmin ? null : Courses::teacherCourseIds((int) $me['id']);

// Cursos que este usuario puede asignar al agendar -- admin completo elige
// cualquiera activo, docente solo el/los suyo(s).
$availableCourses = $isFullAdmin
    ? Courses::listActive()
    : array_values(array_filter(array_map(
        static fn(int $cid): ?array => ($c = Courses::find($cid)) && $c['active'] ? $c : null,
        $myCourseIds ?? []
    )));
$groupsByCourse = [];
$studentsByCourse = [];
foreach ($availableCourses as $ac) {
    $groupsByCourse[(int) $ac['id']] = array_map(
        static fn(array $g): array => ['id' => (int) $g['id'], 'name' => $g['name']],
        Courses::groupsForCourse((int) $ac['id'])
    );
    $studentsByCourse[(int) $ac['id']] = array_map(
        static fn(array $s): array => ['id' => (int) $s['id'], 'name' => $s['display_name']],
        Courses::students((int) $ac['id'])
    );
}

$error = null;
// Mensaje de éxito sobrevive al redirect post-POST (ver más abajo) que
// cierra el modal -- si no, se perdía al no haber dónde mostrarlo.
$success = $_SESSION['agenda_flash_success'] ?? null;
unset($_SESSION['agenda_flash_success']);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $action = $_POST['form_action'] ?? '';

    if ($action === 'schedule') {
        $caseId = trim((string) ($_POST['case_id'] ?? ''));
        $appointmentId = (int) ($_POST['appointment_id'] ?? 0);
        // Agenda.py compara la fecha como STRING EXACTO 'dd-MM-yy' -- por
        // eso <input type="date"> y se convierte acá en vez de guardar el
        // ISO tal cual.
        $fechaIso = trim((string) ($_POST['fecha'] ?? ''));
        $fecha = $fechaIso !== '' ? date('d-m-y', strtotime($fechaIso)) : '';
        $hora = trim((string) ($_POST['hora'] ?? ''));
        $rut = trim((string) ($_POST['rut'] ?? ''));
        $nombre = trim((string) ($_POST['nombre'] ?? ''));
        $apellido = trim((string) ($_POST['apellido'] ?? ''));
        $fechaNacIso = trim((string) ($_POST['fecha_nac'] ?? ''));
        $fechaNac = $fechaNacIso !== '' ? date('d-m-Y', strtotime($fechaNacIso)) : '';
        $procedimiento = trim((string) ($_POST['procedimiento'] ?? '')) ?: 'Audiometría';
        $notaAdmin = trim((string) ($_POST['nota_admin'] ?? ''));
        $forceRound = ($_POST['force_round'] ?? '') === '1';

        // Identidad del paciente = del caso, no de la cita. Se fija recién al
        // primer agendamiento; si el caso ya tiene un patient_id asociado, se
        // ignora por completo lo tipeado en el form (RUT/nombre/apellido/fecha
        // nac) y se usa lo que ya hay guardado -- el área de agendamiento no
        // es donde se edita la ficha del paciente (eso es case_create.php /
        // patients.php). Ni un POST manipulado a mano lo cambia.
        $existingPatientId = null;
        $stmt = $pdo->prepare('SELECT patient_id FROM cases WHERE id = ?');
        $stmt->execute([$caseId]);
        $caseRow = $stmt->fetch();
        if ($caseRow !== false && $caseRow['patient_id'] !== null) {
            $existingPatientId = (int) $caseRow['patient_id'];
            $stmt = $pdo->prepare('SELECT rut, nombre, apellido, fecha_nac FROM patients WHERE id = ?');
            $stmt->execute([$existingPatientId]);
            $existingPatient = $stmt->fetch();
            if ($existingPatient !== false) {
                $rut = (string) $existingPatient['rut'];
                $nombre = (string) $existingPatient['nombre'];
                $apellido = (string) $existingPatient['apellido'];
                $fechaNac = (string) $existingPatient['fecha_nac'];
            }
        }

        // Curso/asignación -- obligatorio solo para citas NUEVAS (ver más
        // abajo, $willInsert); una edición in-place de una cita legado no
        // se ve forzada a adoptar un curso retroactivamente.
        $courseId = (int) ($_POST['course_id'] ?? 0) ?: null;
        $assignMode = (string) ($_POST['assign_mode'] ?? 'course');
        $assignedStudentId = $assignMode === 'student' ? ((int) ($_POST['assigned_student_id'] ?? 0) ?: null) : null;
        $assignedGroupId = $assignMode === 'group' ? ((int) ($_POST['assigned_group_id'] ?? 0) ?: null) : null;

        if ($caseId === '') {
            $error = 'Falta el caso.';
        } elseif ($fecha !== '' && $hora !== '') {
            $stmt = $pdo->prepare('SELECT id FROM appointments WHERE fecha = ? AND hora = ? AND cancelada = 0 AND id != ?');
            $stmt->execute([$fecha, $hora, $appointmentId]);
            if ($stmt->fetch()) {
                $error = 'Ya existe una cita agendada en esa fecha y hora.';
            }
        }

        if ($error === null && $courseId !== null && !$isFullAdmin && (!$myCourseIds || !in_array($courseId, $myCourseIds, true))) {
            $error = 'No tienes acceso a ese curso.';
        }
        if ($error === null && $courseId === null && ($assignedStudentId !== null || $assignedGroupId !== null)) {
            $error = 'No se puede asignar a un grupo o alumno sin seleccionar antes un curso.';
        }
        if ($error === null && $courseId !== null) {
            if ($assignedStudentId !== null) {
                $stmt = $pdo->prepare('SELECT 1 FROM course_students WHERE course_id = ? AND user_id = ?');
                $stmt->execute([$courseId, $assignedStudentId]);
                if (!$stmt->fetch()) {
                    $error = 'El alumno elegido no está matriculado en el curso seleccionado.';
                }
            } elseif ($assignedGroupId !== null) {
                $stmt = $pdo->prepare('SELECT 1 FROM student_groups WHERE id = ? AND course_id = ?');
                $stmt->execute([$assignedGroupId, $courseId]);
                if (!$stmt->fetch()) {
                    $error = 'El grupo elegido no pertenece al curso seleccionado.';
                }
            }
        }

        // Editar una cita con atenciones registradas se guarda en el sitio
        // (mismo appointment_id) igual que cualquier otra -- si el reagendo
        // mezcla atenciones de fechas distintas bajo el mismo id es cosa del
        // admin. "Nueva cita" ($forceRound, botón explícito) sigue siendo la
        // forma de agregar una cita en paralelo para el mismo caso sin pisar
        // la pendiente, en vez de editarla en el sitio.
        $isNewRound = $error === null && $appointmentId > 0 && $forceRound;

        $willInsert = $appointmentId <= 0 || $isNewRound;
        if ($error === null && $willInsert && $courseId === null) {
            $error = 'Falta el curso (obligatorio para citas nuevas).';
        }
        if ($error === null && $willInsert && $courseId !== null && $assignedStudentId === null && $assignedGroupId === null) {
            $error = 'Falta asignar la cita a un grupo o a un alumno específico (obligatorio para citas nuevas; '
                . '"todo el curso" ya no es una opción de asignación para citas nuevas).';
        }

        if ($error === null) {
            // Identidad ya resuelta más arriba (fija si el caso ya tenía
            // patient_id). Solo se crea/resuelve por RUT la primera vez.
            if ($existingPatientId !== null) {
                $patientId = $existingPatientId;
            } else {
                $patientId = Patients::upsertByRut($pdo, $rut, $nombre, $apellido, $fechaNac);
            }
            $pdo->prepare('UPDATE cases SET patient_id = ? WHERE id = ?')->execute([$patientId, $caseId]);

            if ($appointmentId > 0 && !$isNewRound) {
                $pdo->prepare(
                    'UPDATE appointments SET fecha = ?, hora = ?, rut = ?, nombre = ?, apellido = ?, fecha_nac = ?,
                            procedimiento = ?, nota_admin = ?, patient_id = ?,
                            course_id = COALESCE(?, course_id), assigned_student_id = ?, assigned_group_id = ?,
                            updated_at = CURRENT_TIMESTAMP
                     WHERE id = ?'
                )->execute([$fecha, $hora, $rut, $nombre, $apellido, $fechaNac, $procedimiento, $notaAdmin, $patientId, $courseId, $assignedStudentId, $assignedGroupId, $appointmentId]);
                $success = 'Cita actualizada.';
                AdminAudit::log($me, 'appointment_update', ['appointment_id' => $appointmentId, 'case_id' => $caseId]);
            } else {
                $pdo->prepare(
                    'INSERT INTO appointments (fecha, hora, rut, nombre, apellido, fecha_nac, procedimiento, case_id, nota_admin, course_id, assigned_student_id, assigned_group_id, patient_id)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
                )->execute([$fecha, $hora, $rut, $nombre, $apellido, $fechaNac, $procedimiento, $caseId, $notaAdmin, $courseId, $assignedStudentId, $assignedGroupId, $patientId]);
                $success = $isNewRound ? 'Nueva ronda agendada (se conserva el historial de la anterior).' : 'Caso agendado.';
                AdminAudit::log($me, 'appointment_schedule', ['case_id' => $caseId, 'new_round' => $isNewRound]);
            }
        }
    } elseif ($action === 'delete_appointment') {
        // Borra UNA cita puntual (p.ej. una de varias en paralelo del mismo
        // caso) sin tocar el caso ni sus otras citas -- distinto de eliminar
        // el caso completo, que se hace desde patients.php.
        $id = (int) ($_POST['id'] ?? 0);
        if ($id > 0) {
            $pdo->beginTransaction();
            $pdo->prepare('DELETE FROM attendances WHERE appointment_id = ?')->execute([$id]);
            $pdo->prepare('DELETE FROM appointments WHERE id = ?')->execute([$id]);
            $pdo->commit();
            $success = 'Cita eliminada (el caso y sus otras citas, si tenía, se conservan).';
            AdminAudit::log($me, 'appointment_delete', ['appointment_id' => $id]);
        }
    }

    // Sin error: cierra el modal (redirect sin schedule/appointment/new en
    // la URL) en vez de recargar la misma pantalla con el modal abierto.
    // Con error se queda en la misma URL para que el modal siga abierto y
    // el usuario vea qué corregir.
    if ($error === null) {
        $_SESSION['agenda_flash_success'] = $success;
        header('Location: ' . agenda_url([
            'schedule' => null, 'appointment' => null, 'force_round' => null, 'new' => null, 'fecha' => null,
        ]));
        exit;
    }
}

/** dd-MM-yy o dd-MM-yyyy (formato legado) -> ISO, para precargar un <input type="date">. */
function legacy_to_iso(string $legacy): string
{
    $parts = explode('-', $legacy);
    if (count($parts) !== 3) {
        return '';
    }
    $fmt = strlen($parts[2]) === 4 ? 'd-m-Y' : 'd-m-y';
    $d = DateTime::createFromFormat($fmt, $legacy);
    return $d !== false ? $d->format('Y-m-d') : '';
}

/** Arma un link a agenda.php conservando los GET actuales (mes, filtro de curso/grupo/alumno, etc.). */
function agenda_url(array $overrides = []): string
{
    $params = array_merge($_GET, $overrides);
    $params = array_filter($params, static fn($v): bool => $v !== null && $v !== '');
    return 'agenda.php' . ($params ? '?' . http_build_query($params) : '');
}

// Docente: solo ve citas de su(s) curso(s) + citas legado sin curso
// (course_id NULL) -- nunca citas de un curso ajeno. Admin completo sin
// filtro. Filtro de navegación (curso -> grupo/alumno) vía querystring,
// separado del permiso de arriba: el permiso dice qué puede ver un docente,
// el filtro dice qué recorte de eso quiere ver ahora mismo.
$availableCourseIds = array_map(static fn(array $c): int => (int) $c['id'], $availableCourses);

$filterCourseId = isset($_GET['filter_course']) && $_GET['filter_course'] !== '' ? (int) $_GET['filter_course'] : null;
if ($filterCourseId !== null && !in_array($filterCourseId, $availableCourseIds, true)) {
    $filterCourseId = null; // curso ajeno/inexistente -- se ignora en silencio, es solo navegación
}

$filterGroupId = null;
$filterStudentId = null;
if ($filterCourseId !== null) {
    $filterGroupId = isset($_GET['filter_group']) && $_GET['filter_group'] !== '' ? (int) $_GET['filter_group'] : null;
    if ($filterGroupId !== null && !in_array($filterGroupId, array_column($groupsByCourse[$filterCourseId] ?? [], 'id'), true)) {
        $filterGroupId = null;
    }
    $filterStudentId = isset($_GET['filter_student']) && $_GET['filter_student'] !== '' ? (int) $_GET['filter_student'] : null;
    if ($filterStudentId !== null && !in_array($filterStudentId, array_column($studentsByCourse[$filterCourseId] ?? [], 'id'), true)) {
        $filterStudentId = null;
    }
}

$permissionSql = '1=1';
$permissionParams = [];
if (!$isFullAdmin) {
    if ($myCourseIds) {
        $placeholders = implode(',', array_fill(0, count($myCourseIds), '?'));
        $permissionSql = "(a.course_id IS NULL OR a.course_id IN ({$placeholders}))";
        $permissionParams = $myCourseIds;
    } else {
        // docente sin curso asignado: igual ve citas legado sin curso
        $permissionSql = 'a.course_id IS NULL';
    }
}

$courseNameById = [];
foreach ($pdo->query('SELECT id, name FROM courses')->fetchAll() as $cn) {
    $courseNameById[(int) $cn['id']] = $cn['name'];
}
$groupNameById = [];
foreach ($pdo->query('SELECT id, name FROM student_groups')->fetchAll() as $gn) {
    $groupNameById[(int) $gn['id']] = $gn['name'];
}
$userNameById = [];
foreach ($pdo->query('SELECT id, display_name FROM users')->fetchAll() as $un) {
    $userNameById[(int) $un['id']] = $un['display_name'];
}

$historyCaseId = $_GET['history'] ?? null;
$historyRows = [];
if ($historyCaseId !== null) {
    $stmt = $pdo->prepare(
        "SELECT a.id, a.fecha, a.hora, a.procedimiento, a.cancelada, a.nombre, a.apellido,
                (SELECT COUNT(*) FROM attendances att WHERE att.appointment_id = a.id) AS atenciones_count
         FROM appointments a WHERE a.case_id = ? ORDER BY a.id DESC"
    );
    $stmt->execute([$historyCaseId]);
    $historyRows = $stmt->fetchAll();
}

// El caso a agendar/reagendar se busca directo por id (no depende de la
// lista filtrada de abajo) -- así el link "Agendar" desde patients.php
// funciona sin importar el filtro curso/grupo/alumno activo acá.
$scheduleCaseId = $_GET['schedule'] ?? null;
$scheduleRow = null;
if ($scheduleCaseId !== null) {
    $stmt = $pdo->prepare(
        "SELECT c.id, c.data, c.updated_at,
                a.id AS appointment_id, a.fecha, a.hora, a.rut, a.nombre, a.apellido, a.fecha_nac,
                a.procedimiento, a.cancelada, a.nota_admin, a.course_id, a.assigned_student_id, a.assigned_group_id
         FROM cases c
         LEFT JOIN appointments a ON a.id = (
             SELECT id FROM appointments WHERE case_id = c.id ORDER BY id DESC LIMIT 1
         )
         WHERE c.id = ?"
    );
    $stmt->execute([$scheduleCaseId]);
    $found = $stmt->fetch();
    $scheduleRow = $found !== false ? $found : null;
}
// $scheduleRow trae solo la ÚLTIMA cita del caso -- si viene un "appointment"
// explícito (link del calendario o del historial, apuntando a una cita
// puntual que puede no ser la última), se pisan los campos de cita con los
// de esa fila específica para editar/eliminar la correcta.
$scheduleAppointmentId = isset($_GET['appointment']) ? (int) $_GET['appointment'] : null;
if ($scheduleRow !== null && $scheduleAppointmentId !== null) {
    $stmt = $pdo->prepare('SELECT * FROM appointments WHERE id = ? AND case_id = ?');
    $stmt->execute([$scheduleAppointmentId, $scheduleRow['id']]);
    $specificAppt = $stmt->fetch();
    if ($specificAppt !== false) {
        $specificApptId = (int) $specificAppt['id'];
        unset($specificAppt['id']); // no pisar el id del CASO
        $scheduleRow = array_merge($scheduleRow, $specificAppt, ['appointment_id' => $specificApptId]);
    }
}
$scheduleSnapshot = [];
if ($scheduleRow !== null && !$scheduleRow['appointment_id']) {
    $data = json_decode($scheduleRow['data'] ?? '', true);
    $scheduleSnapshot = is_array($data) ? ($data['paciente_snapshot'] ?? []) : [];
}
$scheduleForceRound = isset($_GET['force_round']) && $_GET['force_round'] === '1';
$scheduleIsNewRound = $scheduleRow !== null && (bool) $scheduleRow['appointment_id'] && $scheduleForceRound;
// Identidad del paciente ya fija apenas el caso tuvo una primera cita --
// nombre/apellido/fecha_nac/rut se editan solo desde "Editar ficha"
// (case_create.php / patients.php), nunca desde este formulario de
// agendamiento.
$scheduleIdentityLocked = $scheduleRow !== null && (bool) $scheduleRow['appointment_id'];

// Calendario mensual: agrupa las citas vigentes (no canceladas) del mes
// pedido para dar una vista de ocupación antes de agendar un caso nuevo.
$month = $_GET['month'] ?? date('Y-m');
if (!preg_match('/^\d{4}-\d{2}$/', $month)) {
    $month = date('Y-m');
}
$monthStart = DateTime::createFromFormat('Y-m-d', $month . '-01');
$prevMonth = (clone $monthStart)->modify('-1 month')->format('Y-m');
$nextMonth = (clone $monthStart)->modify('+1 month')->format('Y-m');
$daysInMonth = (int) $monthStart->format('t');
$firstWeekday = (int) $monthStart->format('N'); // 1=lunes .. 7=domingo
$today = date('Y-m-d');
$monthNames = [1 => 'enero', 2 => 'febrero', 3 => 'marzo', 4 => 'abril', 5 => 'mayo', 6 => 'junio',
               7 => 'julio', 8 => 'agosto', 9 => 'septiembre', 10 => 'octubre', 11 => 'noviembre', 12 => 'diciembre'];

// Rango de años del selector: año actual +/- 5, ampliado si el mes visto cae afuera.
$curMonthNum = (int) $monthStart->format('n');
$curYearNum = (int) $monthStart->format('Y');
$yearRangeMin = min($curYearNum, (int) date('Y') - 5);
$yearRangeMax = max($curYearNum, (int) date('Y') + 5);

// El calendario y la lista de citas de abajo SÍ se acotan al filtro
// curso/grupo/alumno -- acá sirve como vista de ocupación/agenda de ese
// scope. El alumno filtrado puede pertenecer a varios grupos, por eso se
// resuelven acá.
$filterStudentGroupIds = [];
if ($filterStudentId !== null) {
    $stmt = $pdo->prepare('SELECT group_id FROM group_members WHERE user_id = ?');
    $stmt->execute([$filterStudentId]);
    $filterStudentGroupIds = array_map('intval', array_column($stmt->fetchAll(), 'group_id'));
}

/** Filtro curso/grupo/alumno compartido por el calendario y la lista de citas. */
function appt_in_filter_scope(
    ?int $cCourseId,
    ?int $cGroupId,
    ?int $cStudentId,
    ?int $filterCourseId,
    ?int $filterGroupId,
    ?int $filterStudentId,
    array $filterStudentGroupIds
): bool {
    if ($filterCourseId === null) {
        return true;
    }
    if ($filterStudentId !== null) {
        // filter_student solo se puede setear junto a un filter_course donde
        // ya está matriculado (validado más arriba), por eso "todo el curso"
        // (sin assigned_*) le aplica directo si el curso coincide.
        return $cCourseId === null
            || $cStudentId === $filterStudentId
            || ($cGroupId !== null && in_array($cGroupId, $filterStudentGroupIds, true))
            || ($cStudentId === null && $cGroupId === null && $cCourseId === $filterCourseId);
    }
    if ($filterGroupId !== null) {
        return $cGroupId === $filterGroupId
            || ($cStudentId === null && $cGroupId === null && $cCourseId === $filterCourseId);
    }
    return $cCourseId === $filterCourseId;
}

$calStmt = $pdo->prepare(
    "SELECT a.id AS appointment_id, a.case_id, a.fecha, a.hora, a.nombre, a.apellido,
            a.course_id, a.assigned_student_id, a.assigned_group_id
     FROM appointments a
     WHERE a.cancelada = 0" . ($permissionSql !== '1=1' ? " AND ({$permissionSql})" : '')
);
$calStmt->execute($permissionParams);
$calendarAppointments = $calStmt->fetchAll();

$appointmentsByDay = [];
foreach ($calendarAppointments as $c) {
    if ($c['fecha'] === '') {
        continue;
    }
    $iso = legacy_to_iso($c['fecha']);
    if ($iso === '' || substr($iso, 0, 7) !== $month) {
        continue;
    }
    $inScope = appt_in_filter_scope(
        $c['course_id'] !== null ? (int) $c['course_id'] : null,
        $c['assigned_group_id'] !== null ? (int) $c['assigned_group_id'] : null,
        $c['assigned_student_id'] !== null ? (int) $c['assigned_student_id'] : null,
        $filterCourseId,
        $filterGroupId,
        $filterStudentId,
        $filterStudentGroupIds
    );
    if (!$inScope) {
        continue;
    }
    $appointmentsByDay[$iso][] = $c;
}
foreach ($appointmentsByDay as &$dayList) {
    usort($dayList, static fn(array $a, array $b): int => strcmp((string) $a['hora'], (string) $b['hora']));
}
unset($dayList);

// "Nueva cita" (botón de arriba o "+" al pasar el mouse sobre un día del
// calendario): a diferencia de "Agendar" desde patients.php, acá todavía no
// se sabe qué caso -- se abre un selector de caso en el modal primero. El
// día de origen (si vino del "+") viaja en $_GET['fecha'] y se precarga en
// el form una vez elegido el caso.
$isNewFlow = isset($_GET['new']) && $scheduleCaseId === null;
$prefillFechaIso = isset($_GET['fecha']) && preg_match('/^\d{4}-\d{2}-\d{2}$/', (string) $_GET['fecha']) ? (string) $_GET['fecha'] : null;
$caseOptions = [];
if ($isNewFlow) {
    $stmt = $pdo->query(
        "SELECT c.id, c.data, a.nombre, a.apellido, a.fecha, a.cancelada
         FROM cases c
         LEFT JOIN appointments a ON a.id = (
             SELECT id FROM appointments WHERE case_id = c.id ORDER BY id DESC LIMIT 1
         )
         ORDER BY c.updated_at DESC"
    );
    foreach ($stmt->fetchAll() as $co) {
        $data = json_decode($co['data'] ?? '', true);
        $snapshot = is_array($data) ? ($data['paciente_snapshot'] ?? null) : null;
        $nombre = trim(($co['nombre'] ?? '') . ' ' . ($co['apellido'] ?? ''));
        if ($nombre === '' && $snapshot) {
            $nombre = trim(($snapshot['nombre'] ?? '') . ' ' . ($snapshot['apellido'] ?? ''));
        }
        $estado = $co['fecha'] ? ($co['cancelada'] ? 'cancelada' : 'agendada') : 'sin agendar';
        $caseOptions[] = [
            'id' => $co['id'],
            'label' => $co['id'] . ' — ' . ($nombre !== '' ? $nombre : 'sin nombre') . ' (' . $estado . ')',
        ];
    }
}

admin_header('Agendas', $me);
?>
<style>
    .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; margin-top: 0.6rem; }
    .cal-dow { font-size: 0.75rem; font-weight: 600; color: #888; text-align: center; padding: 0.2rem 0; }
    .cal-day { min-height: 4.6rem; border: 1px solid #e5e5e5; border-radius: 4px; padding: 0.25rem; font-size: 0.75rem; background: #fafafa; }
    .cal-day.empty { background: transparent; border: none; }
    .cal-day.today { border-color: #1a2744; border-width: 2px; }
    .cal-day .cal-num { font-weight: 600; margin-bottom: 0.15rem; display: block; }
    .cal-day a { display: block; text-decoration: none; color: #1a2744; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .cal-day { position: relative; }
    .cal-day .cal-add {
        position: absolute; top: 0.2rem; right: 0.2rem; display: none;
        width: 1.15rem; height: 1.15rem; line-height: 1.1rem; text-align: center;
        border-radius: 50%; background: #1a2744; color: #fff; font-size: 0.85rem;
        font-weight: 700; text-decoration: none;
    }
    .cal-day:hover .cal-add { display: block; }
    .btn-link {
        display: inline-block; padding: 0.5rem 1.1rem; background: #1a2744; color: #fff;
        border-radius: 4px; text-decoration: none; font-size: 0.9rem;
    }
    .btn-link:hover { opacity: 0.9; }
    .modal-backdrop {
        position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 50;
        display: flex; align-items: flex-start; justify-content: center;
        padding: 3rem 1rem; overflow-y: auto;
    }
    .modal-box { max-width: 560px; width: 100%; margin: 0; }
    .modal-box-header { display: flex; justify-content: space-between; align-items: center; }
    .modal-close { color: #888; text-decoration: none; font-size: 1.2rem; line-height: 1; }
    .modal-close:hover { color: #333; }
</style>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<?php if ($scheduleRow !== null): ?>
<div class="modal-backdrop">
<div class="card modal-box">
    <div class="modal-box-header">
        <strong>
            <?= $scheduleRow['appointment_id'] ? 'Reagendar caso ' . htmlspecialchars($scheduleRow['id']) : 'Agendar caso ' . htmlspecialchars($scheduleRow['id']) ?>
            <?php if ($scheduleRow['appointment_id'] && $scheduleRow['cancelada']): ?><span style="color:#a33; font-weight:400; font-size:0.8rem;"> (cancelada)</span><?php endif; ?>
        </strong>
        <a class="modal-close" href="<?= agenda_url(['schedule' => null, 'appointment' => null, 'force_round' => null, 'new' => null, 'fecha' => null]) ?>" title="Cerrar">✕</a>
    </div>
    <p style="font-size:0.85rem; color:#555;">
        Ojo: en la app del alumno, la Agenda por defecto solo muestra las citas de <strong>hoy</strong>
        (hay un selector de fecha y una casilla "Ver todas las citas habilitadas" para ver otros días).
    </p>
    <?php if ($scheduleForceRound): ?>
    <p style="font-size:0.85rem; color:#886400;">
        <strong>Nueva cita</strong> para el mismo paciente -- se crea una cita aparte (horario/grupo propios) sin
        tocar la que ya tenía agendada. El historial completo del caso se ve desde
        <a href="patients.php">Fichas Clínicas</a>.
    </p>
    <?php elseif ($scheduleIsNewRound): ?>
    <p style="font-size:0.85rem; color:#886400;">
        Esta cita ya tiene atenciones registradas -- guardar acá crea una <strong>ronda nueva</strong> (cita distinta)
        en vez de editar la anterior, para no perder el historial de esa ronda. El historial completo del caso se ve
        desde <a href="patients.php">Fichas Clínicas</a>.
    </p>
    <?php endif; ?>
    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="schedule">
        <input type="hidden" name="case_id" value="<?= htmlspecialchars($scheduleRow['id']) ?>">
        <input type="hidden" name="appointment_id" value="<?= (int) ($scheduleRow['appointment_id'] ?? 0) ?>">
        <input type="hidden" name="force_round" value="<?= $scheduleForceRound ? '1' : '0' ?>">
        <label>Fecha (vacío = sin agendar aún)
            <input type="date" name="fecha" value="<?= $scheduleForceRound ? '' : htmlspecialchars($prefillFechaIso ?? legacy_to_iso($scheduleRow['fecha'] ?? '')) ?>">
        </label>
        <label>Hora
            <input type="time" name="hora" value="<?= $scheduleForceRound ? '' : htmlspecialchars($scheduleRow['hora'] ?? '') ?>">
        </label>
        <?php if ($scheduleIdentityLocked): ?>
        <p style="font-size:0.85rem; margin:0.3rem 0; padding:0.4rem 0.6rem; background:#f5f5f5; border-radius:4px;">
            <strong><?= htmlspecialchars(trim(($scheduleRow['nombre'] ?? '') . ' ' . ($scheduleRow['apellido'] ?? ''))) ?></strong>
            &nbsp;·&nbsp; RUT <?= htmlspecialchars($scheduleRow['rut'] ?? '') ?>
            &nbsp;·&nbsp; nac. <?= htmlspecialchars(legacy_to_iso($scheduleRow['fecha_nac'] ?? '')) ?>
            &nbsp;·&nbsp; <a href="case_create.php?edit=<?= urlencode($scheduleRow['id']) ?>">editar ficha</a>
        </p>
        <?php else: ?>
        <label>RUT
            <input type="text" name="rut" value="<?= htmlspecialchars($scheduleRow['rut'] ?? $scheduleSnapshot['rut'] ?? '') ?>">
        </label>
        <label>Nombre
            <input type="text" name="nombre" value="<?= htmlspecialchars($scheduleRow['nombre'] ?? $scheduleSnapshot['nombre'] ?? '') ?>">
        </label>
        <label>Apellido
            <input type="text" name="apellido" value="<?= htmlspecialchars($scheduleRow['apellido'] ?? $scheduleSnapshot['apellido'] ?? '') ?>">
        </label>
        <label>Fecha de nacimiento
            <input type="date" name="fecha_nac" value="<?= htmlspecialchars(legacy_to_iso($scheduleRow['fecha_nac'] ?? $scheduleSnapshot['fecha_nac'] ?? '')) ?>">
        </label>
        <?php endif; ?>
        <label>Procedimiento
            <input type="text" name="procedimiento" value="<?= htmlspecialchars($scheduleRow['procedimiento'] ?? $scheduleSnapshot['procedimiento'] ?? 'Audiometría') ?>">
        </label>
        <label>Nota admin
            <input type="text" name="nota_admin" value="<?= htmlspecialchars($scheduleRow['nota_admin'] ?? '') ?>">
        </label>
        <?php
        // "Reagendar" in-place (misma fila, sin ronda nueva) no exige curso --
        // se puede seguir editando datos de una cita legado sin forzarle uno.
        $requiresCourse = !$scheduleRow['appointment_id'] || $scheduleIsNewRound;
        $isBrandNew = !$scheduleRow['appointment_id'];
        $curCourseId = (int) ($scheduleRow['course_id'] ?? 0);
        $curGroupId = (int) ($scheduleRow['assigned_group_id'] ?? 0);
        $curStudentId = (int) ($scheduleRow['assigned_student_id'] ?? 0);
        // Caso sin cita aún + hay un filtro de curso/grupo/alumno activo en la
        // pantalla: precarga el form con ese scope en vez de dejarlo en blanco.
        if ($isBrandNew && $curCourseId === 0 && $filterCourseId !== null) {
            $curCourseId = $filterCourseId;
            $curGroupId = $filterGroupId ?? 0;
            $curStudentId = $filterStudentId ?? 0;
        }
        $curAssignMode = $curStudentId ? 'student' : ($curGroupId ? 'group' : ($requiresCourse ? 'group' : 'course'));
        ?>
        <label>Curso<?= $requiresCourse ? ' *' : ' (solo aplica a citas/rondas nuevas)' ?>
            <select name="course_id" id="sched-course" <?= $requiresCourse ? 'required' : '' ?> onchange="onCourseChange()">
                <option value="">-- selecciona curso --</option>
                <?php foreach ($availableCourses as $ac): ?>
                <option value="<?= $ac['id'] ?>" <?= $curCourseId === (int) $ac['id'] ? 'selected' : '' ?>><?= htmlspecialchars($ac['name']) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Asignar a<?= $requiresCourse ? ' *' : '' ?>
            <select name="assign_mode" id="sched-assign-mode" onchange="onAssignModeChange()">
                <option value="course" <?= $curAssignMode === 'course' ? 'selected' : '' ?> <?= $requiresCourse ? 'disabled' : '' ?>>
                    Todo el curso<?= $requiresCourse ? ' (solo lectura, valor histórico -- no disponible para citas nuevas)' : '' ?>
                </option>
                <option value="group" <?= $curAssignMode === 'group' ? 'selected' : '' ?>>Grupo</option>
                <option value="student" <?= $curAssignMode === 'student' ? 'selected' : '' ?>>Alumno</option>
            </select>
        </label>
        <div id="sched-group-wrap">
            <label>Grupo
                <select name="assigned_group_id" id="sched-group" data-selected="<?= $curGroupId ?>"></select>
            </label>
        </div>
        <div id="sched-student-wrap">
            <label>Alumno
                <select name="assigned_student_id" id="sched-student" data-selected="<?= $curStudentId ?>"></select>
            </label>
        </div>
        <button type="submit"><?= $scheduleForceRound ? 'Agendar cita nueva' : ($scheduleIsNewRound ? 'Agendar ronda nueva' : ($scheduleRow['appointment_id'] ? 'Guardar cambios' : 'Agendar')) ?></button>
        <a href="<?= agenda_url(['schedule' => null, 'appointment' => null, 'force_round' => null, 'new' => null, 'fecha' => null]) ?>" style="display:inline-block; margin-left:1rem; padding:0.5rem 0.9rem; border-radius:4px; background:#888; color:#fff; text-decoration:none; font-size:0.9rem;">Cancelar</a>
    </form>
    <?php if ($scheduleRow['appointment_id'] && !$scheduleForceRound): ?>
    <hr style="margin:1rem 0; border:none; border-top:1px solid #ddd;">
    <form method="post" style="display:inline;" onsubmit="return confirm(<?= htmlspecialchars(json_encode(
        '¿Eliminar esta cita (' . trim(($scheduleRow['fecha'] ?? '') . ' ' . ($scheduleRow['hora'] ?? '')) . ')? '
        . 'Se borran también las atenciones registradas para ella. El caso y sus otras citas, si tenía, se conservan. '
        . 'No se puede deshacer.'
    ), ENT_QUOTES) ?>);">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="delete_appointment">
        <input type="hidden" name="id" value="<?= (int) $scheduleRow['appointment_id'] ?>">
        <button type="submit" class="danger" style="margin-left:1rem; padding:0.3rem 0.7rem; font-size:0.85rem;">Eliminar esta cita</button>
    </form>
    <?php endif; ?>
</div>
</div>
<script>
    var COURSE_GROUPS = <?= json_encode($groupsByCourse) ?>;
    var COURSE_STUDENTS = <?= json_encode($studentsByCourse) ?>;

    function onCourseChange() {
        var courseId = document.getElementById('sched-course').value;
        fillSelect('sched-group', COURSE_GROUPS[courseId] || []);
        fillSelect('sched-student', COURSE_STUDENTS[courseId] || []);
    }

    function fillSelect(id, items) {
        var sel = document.getElementById(id);
        var keepSelected = sel.dataset.selected || '';
        sel.innerHTML = '<option value="">-- ninguno --</option>';
        items.forEach(function (item) {
            var opt = document.createElement('option');
            opt.value = item.id;
            opt.textContent = item.name;
            if (String(item.id) === String(keepSelected)) { opt.selected = true; }
            sel.appendChild(opt);
        });
        sel.dataset.selected = '';
    }

    function onAssignModeChange() {
        var mode = document.getElementById('sched-assign-mode').value;
        document.getElementById('sched-group-wrap').style.display = mode === 'group' ? 'block' : 'none';
        document.getElementById('sched-student-wrap').style.display = mode === 'student' ? 'block' : 'none';
        document.getElementById('sched-group').required = (mode === 'group');
        document.getElementById('sched-student').required = (mode === 'student');
    }

    onCourseChange();
    onAssignModeChange();
</script>
<?php endif; ?>

<?php if ($isNewFlow): ?>
<div class="modal-backdrop">
<div class="card modal-box">
    <div class="modal-box-header">
        <strong>Nueva cita<?= $prefillFechaIso !== null ? ' — ' . htmlspecialchars($prefillFechaIso) : '' ?></strong>
        <a class="modal-close" href="<?= agenda_url(['new' => null, 'fecha' => null]) ?>" title="Cerrar">✕</a>
    </div>
    <p style="font-size:0.85rem; color:#555;">Elige el caso/paciente al que le vas a agendar la cita.</p>
    <label>Buscar paciente por nombre
        <input type="text" id="new-case-search" placeholder="Escribe un nombre..." autocomplete="off" oninput="filterCaseOptions()">
    </label>
    <label>Caso / paciente
        <select id="new-case-picker" size="8" onchange="if (this.value) { location.href = this.options[this.selectedIndex].dataset.href; }">
            <?php foreach ($caseOptions as $co): ?>
            <option value="<?= htmlspecialchars($co['id']) ?>"
                    data-search="<?= htmlspecialchars(mb_strtolower($co['label'])) ?>"
                    data-href="<?= htmlspecialchars(agenda_url(['schedule' => $co['id'], 'new' => null])) ?>">
                <?= htmlspecialchars($co['label']) ?>
            </option>
            <?php endforeach; ?>
        </select>
    </label>
    <p id="new-case-empty" style="font-size:0.85rem; color:#888; display:none;">Ningún paciente coincide con esa búsqueda.</p>
    <p style="font-size:0.85rem; color:#555; margin-top:0.8rem;">
        ¿El paciente todavía no tiene ficha? <a href="case_create.php">Crear ficha nueva</a> primero.
    </p>
</div>
</div>
<script>
    function filterCaseOptions() {
        var q = document.getElementById('new-case-search').value.toLowerCase().trim();
        var opts = document.querySelectorAll('#new-case-picker option');
        var anyVisible = false;
        opts.forEach(function (o) {
            var match = q === '' || (o.dataset.search || '').indexOf(q) !== -1;
            o.hidden = !match;
            if (match) { anyVisible = true; }
        });
        document.getElementById('new-case-empty').style.display = anyVisible ? 'none' : 'block';
    }
    document.getElementById('new-case-search').focus();
</script>
<?php endif; ?>

<div class="card">
    <form method="get" style="display:flex; gap:1rem; align-items:flex-end; flex-wrap:wrap;">
        <input type="hidden" name="month" value="<?= htmlspecialchars($month) ?>">
        <?php if ($scheduleCaseId !== null): ?><input type="hidden" name="schedule" value="<?= htmlspecialchars($scheduleCaseId) ?>"><?php endif; ?>
        <label style="margin:0;">Curso
            <select name="filter_course" onchange="this.form.submit()">
                <option value="">-- todos<?= $isFullAdmin ? '' : ' (mis cursos)' ?> --</option>
                <?php foreach ($availableCourses as $ac): ?>
                <option value="<?= $ac['id'] ?>" <?= $filterCourseId === (int) $ac['id'] ? 'selected' : '' ?>><?= htmlspecialchars($ac['name']) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <?php if ($filterCourseId !== null): ?>
        <label style="margin:0;">Grupo
            <select name="filter_group" onchange="document.querySelector('[name=filter_student]').value='';this.form.submit()">
                <option value="">-- todos --</option>
                <?php foreach ($groupsByCourse[$filterCourseId] as $g): ?>
                <option value="<?= $g['id'] ?>" <?= $filterGroupId === $g['id'] ? 'selected' : '' ?>><?= htmlspecialchars($g['name']) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label style="margin:0;">Alumno
            <select name="filter_student" onchange="document.querySelector('[name=filter_group]').value='';this.form.submit()">
                <option value="">-- todos --</option>
                <?php foreach ($studentsByCourse[$filterCourseId] as $s): ?>
                <option value="<?= $s['id'] ?>" <?= $filterStudentId === $s['id'] ? 'selected' : '' ?>><?= htmlspecialchars($s['name']) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <?php endif; ?>
        <noscript><button type="submit">Filtrar</button></noscript>
    </form>
    <?php if ($filterCourseId !== null): ?>
    <p style="font-size:0.8rem; color:#555; margin-top:0.5rem;">
        Acotado a <strong><?= htmlspecialchars($courseNameById[$filterCourseId] ?? '') ?></strong>
        <?php if ($filterGroupId !== null): ?>· grupo <strong><?= htmlspecialchars($groupNameById[$filterGroupId] ?? '') ?></strong> (incluye también citas legado "todo el curso" de este curso, si las hubiera)<?php endif; ?>
        <?php if ($filterStudentId !== null): ?>· alumno <strong><?= htmlspecialchars($userNameById[$filterStudentId] ?? '') ?></strong> (incluye citas de su grupo, todo el curso o cola global que también le apliquen)<?php endif; ?>
        &nbsp;·&nbsp; <a href="<?= agenda_url(['filter_course' => null, 'filter_group' => null, 'filter_student' => null]) ?>">Quitar filtro</a>
    </p>
    <?php endif; ?>
</div>

<div class="card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <strong>Calendario</strong>
        <a class="btn-link" href="<?= agenda_url(['new' => 1, 'schedule' => null, 'appointment' => null, 'fecha' => null]) ?>">+ Crear nueva cita</a>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.8rem; gap:0.5rem; flex-wrap:wrap;">
        <a href="<?= agenda_url(['month' => $prevMonth]) ?>">&larr; anterior</a>
        <strong><?= $monthNames[(int) $monthStart->format('n')] ?> <?= $monthStart->format('Y') ?></strong>
        <form method="get" style="display:flex; gap:0.3rem; align-items:center;" onsubmit="this.querySelector('[name=month]').value = document.getElementById('cal-jump-year').value + '-' + document.getElementById('cal-jump-month').value; return true;">
            <?php foreach ($_GET as $k => $v): if ($k === 'month') continue; ?>
            <input type="hidden" name="<?= htmlspecialchars($k) ?>" value="<?= htmlspecialchars((string) $v) ?>">
            <?php endforeach; ?>
            <input type="hidden" name="month" value="">
            <select id="cal-jump-month" style="font-size:0.85rem;" onchange="this.form.requestSubmit()">
                <?php foreach ($monthNames as $mn => $mname): ?>
                <option value="<?= sprintf('%02d', $mn) ?>" <?= $mn === $curMonthNum ? 'selected' : '' ?>><?= ucfirst($mname) ?></option>
                <?php endforeach; ?>
            </select>
            <select id="cal-jump-year" style="font-size:0.85rem;" onchange="this.form.requestSubmit()">
                <?php for ($y = $yearRangeMin; $y <= $yearRangeMax; $y++): ?>
                <option value="<?= $y ?>" <?= $y === $curYearNum ? 'selected' : '' ?>><?= $y ?></option>
                <?php endfor; ?>
            </select>
        </form>
        <a href="<?= agenda_url(['month' => $nextMonth]) ?>">siguiente &rarr;</a>
    </div>
    <div class="cal-grid">
        <?php foreach (['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'] as $dow): ?>
        <div class="cal-dow"><?= $dow ?></div>
        <?php endforeach; ?>
        <?php for ($i = 1; $i < $firstWeekday; $i++): ?>
        <div class="cal-day empty"></div>
        <?php endfor; ?>
        <?php for ($day = 1; $day <= $daysInMonth; $day++):
            $iso = sprintf('%s-%02d', $month, $day);
            $dayAppts = $appointmentsByDay[$iso] ?? [];
        ?>
        <div class="cal-day<?= $iso === $today ? ' today' : '' ?>">
            <span class="cal-num"><?= $day ?></span>
            <a class="cal-add" href="<?= agenda_url(['new' => 1, 'fecha' => $iso, 'schedule' => null, 'appointment' => null]) ?>" title="Nueva cita el <?= htmlspecialchars($iso) ?>">+</a>
            <?php foreach ($dayAppts as $a): ?>
            <a href="<?= agenda_url(['schedule' => $a['case_id'], 'appointment' => $a['appointment_id']]) ?>" title="<?= htmlspecialchars(trim($a['hora'] . ' ' . $a['nombre'] . ' ' . $a['apellido'])) ?>">
                <?= htmlspecialchars($a['hora']) ?> <?= htmlspecialchars(trim($a['nombre'] . ' ' . $a['apellido'])) ?>
            </a>
            <?php endforeach; ?>
        </div>
        <?php endfor; ?>
    </div>
    <p style="font-size:0.85rem; color:#555; margin-top:0.6rem;">
        "+ Crear nueva cita" o el <strong>+</strong> que aparece al pasar el mouse sobre un día -- ambos abren el
        selector de caso/paciente para agendar (ese día queda precargado si vino del "+"). La biblioteca de
        fichas/pacientes está en <a href="patients.php">Fichas Clínicas</a>.
    </p>
</div>

<?php if ($historyCaseId !== null): ?>
<div class="card" id="historial">
    <strong>Historial del caso <?= htmlspecialchars($historyCaseId) ?></strong>
    &nbsp;·&nbsp; <a href="<?= agenda_url(['history' => null]) ?>" style="font-size:0.85rem;">Cerrar</a>
    <p style="font-size:0.85rem; color:#555;">Cada ronda es una cita distinta con su propio historial de atenciones y métricas (no se mezclan entre sí).</p>
    <table>
        <tr><th>Cita</th><th>Fecha</th><th>Hora</th><th>Paciente</th><th>Procedimiento</th><th>Estado</th><th>Atenciones</th><th></th></tr>
        <?php foreach ($historyRows as $h): ?>
        <tr>
            <td>#<?= (int) $h['id'] ?></td>
            <td><?= htmlspecialchars($h['fecha'] ?: '—') ?></td>
            <td><?= htmlspecialchars($h['hora'] ?: '—') ?></td>
            <td><?= htmlspecialchars(trim($h['nombre'] . ' ' . $h['apellido'])) ?: '—' ?></td>
            <td><?= htmlspecialchars($h['procedimiento']) ?></td>
            <td><?= $h['cancelada'] ? 'cancelada' : 'agendada' ?></td>
            <td>
                <?php if ((int) $h['atenciones_count'] > 0): ?>
                <a href="dashboard.php?appointment_id=<?= (int) $h['id'] ?>"><?= (int) $h['atenciones_count'] ?> alumno<?= (int) $h['atenciones_count'] === 1 ? '' : 's' ?></a>
                <?php else: ?>
                —
                <?php endif; ?>
            </td>
            <td style="font-size:0.8rem;">
                <a href="<?= agenda_url(['schedule' => $historyCaseId, 'appointment' => $h['id']]) ?>">Editar</a>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$historyRows): ?>
        <tr><td colspan="8" style="color:#888;">Este caso no tiene citas.</td></tr>
        <?php endif; ?>
    </table>
</div>
<?php endif; ?>
<?php
admin_footer();
