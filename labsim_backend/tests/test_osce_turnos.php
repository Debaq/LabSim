<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/OscePreguntas.php';

/**
 * OSCE por turnos con tiempo por alumno (2026-11-25): cada alumno tiene su
 * tiempo desde que confirma su nombre; el cambio parte cuando todas las
 * estaciones del turno cerraron; ausentes y descanso no se esperan.
 */

// -- Puro: estadoTurno / faseTurno ------------------------------------------
$cfg = ['modo' => 'cadena', 'estaciones' => 3, 'duracion_s' => 480, 'pausa_s' => 120, 'pausa_vueltas_s' => 0,
        'por_turno' => 1, 'grupos' => 3, 'turnos' => 5, 'vueltas' => 1];
$est = [['id' => 10, 'tipo' => 'pauta_docente'], ['id' => 11, 'tipo' => 'preguntas'], ['id' => 12, 'tipo' => 'marcaje']];
$parts = [['id' => 1, 'numero' => 1, 'ausente' => 0], ['id' => 2, 'numero' => 2, 'ausente' => 0], ['id' => 3, 'numero' => 3, 'ausente' => 0]];

t_eq(Osce::totalTurnos($cfg), 5, 'Cadena: 3 grupos + 3 estaciones − 1 = 5 turnos');
t_eq(Osce::turnoDe($cfg, $parts[1], 2), 3, 'El N.º 2 llega a la estación 3 en el turno 4 (índice 3)');

$st = Osce::estadoTurno($cfg, $est, $parts, [], 1, 500);
t_eq(array_map(static fn ($x) => [$x['numero'], $x['indice'], $x['estado']], $st['pares']),
     [[1, 1, 'esperando'], [2, 0, 'esperando']], 'Turno 2: el 1 en preguntas y el 2 en la limpieza, sin entrar');
t_eq([$st['abiertos'], $st['restante_s']], [2, null], 'Nadie ha confirmado: dos abiertos y sin cuenta');

$en = [1 => [11 => ['estado' => 'en_curso', 'reloj_inicio_s' => 600]], 2 => [10 => ['estado' => 'en_curso', 'reloj_inicio_s' => 700]]];
$st = Osce::estadoTurno($cfg, $est, $parts, $en, 1, 800);
t_eq(array_column($st['pares'], 'restante_s'), [280, 380], 'Cada uno con su tiempo desde que confirmó');
t_eq($st['restante_s'], 380, 'La cuenta grande es la del último que entró');

$st = Osce::estadoTurno($cfg, $est, $parts, $en, 1, 600 + 480 + Osce::GRACIA_S + 1);
t_eq(array_column($st['pares'], 'estado'), ['vencida', 'trabajando'], 'Al primero se le acabó (con la gracia); el segundo sigue');
t_eq($st['abiertos'], 1, 'El turno espera al que entró después');

$en[2][10] = ['estado' => 'enviada', 'reloj_inicio_s' => 700];
$st = Osce::estadoTurno($cfg, $est, $parts, $en, 1, 1200);
t_eq($st['abiertos'], 0, 'Entregó uno y al otro se le acabó: turno cerrado');

$ausentes = $parts;
$ausentes[1]['ausente'] = 1;
t_eq(Osce::estadoTurno($cfg, $est, $ausentes, [], 1, 0)['abiertos'], 1, 'Un ausente no se espera');
$conDescanso = $est;
$conDescanso[0]['tipo'] = 'descanso';
t_eq(Osce::estadoTurno($cfg, $conDescanso, $parts, [], 1, 0)['abiertos'], 1, 'El descanso no se espera');

$o = ['estado' => 'en_curso', 'turno' => 1, 'cambio_desde_s' => null];
$f = Osce::faseTurno($o, $cfg, ['abiertos' => 2, 'restante_s' => 300], 900);
t_eq([$f['fase'], $f['slot'], $f['restante_s'], $f['abiertos']], ['estacion', 1, 300, 2], 'Fase en estación con la cuenta del último');
$o['cambio_desde_s'] = 1000;
$f = Osce::faseTurno($o, $cfg, null, 1030);
t_eq([$f['fase'], $f['restante_s']], ['cambio', 90], 'Cambio: 2 min desde que cerró la última estación');
t_eq(Osce::faseTurno(['estado' => 'borrador', 'turno' => 0, 'cambio_desde_s' => null], $cfg, null, null)['fase'], 'antes', 'Sin partir');
t_eq(Osce::faseTurno(['estado' => 'cerrado', 'turno' => 4, 'cambio_desde_s' => null], $cfg, null, 5000)['fase'], 'terminado', 'Cerrado');

$cv = ['modo' => 'vueltas', 'estaciones' => 6, 'vueltas' => 3, 'duracion_s' => 480, 'pausa_s' => 120, 'pausa_vueltas_s' => 600];
t_eq(Osce::totalTurnos($cv), 18, 'Vueltas: 3 × 6 turnos');
t_eq([Osce::largoCambio($cv, 4), Osce::largoCambio($cv, 5)], [120, 600], 'Al cerrar la vuelta va la pausa entre vueltas');
t_eq(Osce::vueltaSlot($cv, 7), ['vuelta' => 1, 'slot' => 1], 'Turno 8 = vuelta 2, tiempo 2');

// -- Con base: avanzar, motivoNoToca, iniciarReloj --------------------------
if (!extension_loaded('pdo_sqlite')) {
    echo "  (sin pdo_sqlite: se saltan las pruebas de turnos con base)\n";
    return;
}
$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                                                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec("CREATE TABLE courses (id INTEGER PRIMARY KEY, name TEXT)");
$pdo->exec("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, display_name TEXT)");
$pdo->exec("INSERT INTO courses VALUES (1, 'ETMP196')");
$pdo->exec("INSERT INTO users VALUES (1,'a','Ana Pérez'), (2,'b','Beto Soto')");
$ref = new ReflectionProperty(Db::class, 'pdo');
$ref->setAccessible(true);
$antes = $ref->getValue();
$ref->setValue(null, $pdo);
try {
    Osce::migrar();
    $ahora = time();
    // Arrancó hace 100 s; 2 alumnos de a 1 por turno, 2 estaciones: 3 turnos.
    $pdo->exec("INSERT INTO osce (id, course_id, nombre, duracion_s, pausa_s, rotacion, por_turno, estado, inicio_epoch, reloj_token)
                VALUES (1, 1, 'OSCE', 480, 120, 'cadena', 1, 'en_curso', " . ($ahora - 100) . ", 'r')");
    $pdo->exec("INSERT INTO osce_estacion (id, osce_id, orden, tipo, titulo) VALUES (10, 1, 0, 'preguntas', 'P'), (11, 1, 1, 'marcaje', 'M')");
    $pdo->exec("INSERT INTO osce_participante (id, osce_id, user_id, numero, codigo, token) VALUES
                (1, 1, 1, 1, 'AAA-AAA', 'aa'), (2, 1, 2, 2, 'BBB-BBB', 'bb')");
    $o = Osce::obtener(1);
    $p1 = Osce::participantePorCodigo(1, '1');
    $p2 = Osce::participantePorCodigo(1, '2');
    $e10 = Osce::estacion(10);
    $e11 = Osce::estacion(11);

    t_eq(Osce::motivoNoToca($o, $e10, $p1), null, 'Turno 1: al N.º 1 le toca la estación 1');
    t_eq(Osce::motivoNoToca($o, $e10, $p2), 'Todavía no te toca esta estación. Revisa tu tarjeta.', 'Al 2 todavía no');
    t_eq((int) Osce::avanzar($o)['turno'], 0, 'Nadie ha entrado: el turno no avanza');

    $v = Osce::iniciarReloj($o, 1, 10);
    t_eq($v, ['inicio_s' => 100, 'fin_s' => 580], 'Su tiempo parte al confirmar el nombre');
    $pdo->exec('UPDATE osce SET inicio_epoch = inicio_epoch - 50 WHERE id = 1');
    t_eq(Osce::iniciarReloj(Osce::obtener(1), 1, 10), $v, 'Volver a entrar no le reinicia el tiempo');

    $pdo->exec("UPDATE osce_entrega SET estado = 'enviada' WHERE participante_id = 1");
    $o = Osce::avanzar(Osce::obtener(1));
    t_eq([(int) $o['turno'], (int) $o['cambio_desde_s']], [0, 150], 'Entregó el único del turno: parte el cambio');
    t_eq(Osce::motivoNoToca($o, $e10, $p2), 'Estamos en el cambio: esta estación te recibe en 2:00.', 'Durante el cambio la estación espera');

    $pdo->exec('UPDATE osce SET inicio_epoch = inicio_epoch - 121 WHERE id = 1');
    $o = Osce::avanzar(Osce::obtener(1));
    t_eq([(int) $o['turno'], $o['cambio_desde_s']], [1, null], 'Pasado el cambio: turno 2');
    t_eq(Osce::motivoNoToca($o, $e10, $p2), null, 'Ahora sí le toca al 2 en la estación 1');

    Osce::marcarAusente(1, 1, true);
    Osce::iniciarReloj($o, 2, 10);
    $pdo->exec("UPDATE osce_entrega SET estado = 'enviada' WHERE participante_id = 2");
    $o = Osce::avanzar(Osce::obtener(1));
    t_true($o['cambio_desde_s'] !== null, 'Con el 1 ausente en la estación 2, el turno 2 cierra al entregar el 2');
    t_eq(Osce::motivoNoToca($o, $e11, Osce::participantePorCodigo(1, '1')), 'Tu número está marcado como ausente. Avisa al docente.', 'El ausente no entra');

    Osce::forzarCambio(1);
    $pdo->exec('UPDATE osce SET inicio_epoch = inicio_epoch - 121 WHERE id = 1');
    $o = Osce::avanzar(Osce::obtener(1));
    t_eq((int) $o['turno'], 2, 'Turno 3 (el último)');
    Osce::forzarCambio(1);
    t_eq(Osce::obtener(1)['estado'], 'cerrado', 'Forzar el cambio en el último turno cierra el OSCE');
} finally {
    $ref->setValue(null, $antes);
}
