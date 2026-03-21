<?php
/**
 * LabSim Backend - Sincronización
 *
 * POST /sync/push     → Subir entidades al servidor
 * POST /sync/pull     → Descargar cambios desde el servidor
 * GET  /sync/status   → Estado de sincronización
 */

require_once __DIR__ . '/../core/auth_middleware.php';

$action = $routeSegments[0] ?? null;

switch ("$method:$action") {

    // ─── PUSH ───────────────────────────────────────
    case 'POST:push':
        $auth = require_auth();
        $body = get_json_body();

        if (empty($body['entities']) || !is_array($body['entities'])) {
            error_response('entities requerido (array)', 400);
        }

        $results = [];
        $db = Database::get();
        $db->beginTransaction();

        try {
            foreach ($body['entities'] as $entity) {
                $type = $entity['type'] ?? '';
                $entityId = $entity['id'] ?? '';
                $data = $entity['data'] ?? [];
                $updatedAt = $entity['updatedAt'] ?? date('c');

                switch ($type) {
                    case 'case':
                        // Solo admin/docente/instructor pueden push casos
                        if (!in_array($auth['role'], ['admin', 'docente', 'instructor'])) {
                            $results[] = ['id' => $entityId, 'type' => $type, 'status' => 'denied'];
                            continue 2;
                        }

                        $existing = Database::fetchOne('SELECT id, updated_at FROM cases WHERE id = :id', [':id' => $entityId]);

                        if ($existing) {
                            // Conflicto: gana el más reciente
                            if ($updatedAt > $existing['updated_at']) {
                                Database::execute(
                                    "UPDATE cases SET title = :title, description = :desc, profile_json = :profile,
                                        tags = :tags, difficulty = :diff, schema_version = :schema,
                                        updated_at = :updated
                                     WHERE id = :id",
                                    [
                                        ':id' => $entityId,
                                        ':title' => $data['title'] ?? '',
                                        ':desc' => $data['description'] ?? null,
                                        ':profile' => json_encode($data['profile'] ?? new stdClass()),
                                        ':tags' => $data['tags'] ?? '',
                                        ':diff' => $data['difficulty'] ?? 'medium',
                                        ':schema' => $data['schemaVersion'] ?? 1,
                                        ':updated' => $updatedAt,
                                    ]
                                );
                                $results[] = ['id' => $entityId, 'type' => $type, 'status' => 'updated'];
                            } else {
                                $results[] = ['id' => $entityId, 'type' => $type, 'status' => 'conflict_server_wins'];
                            }
                        } else {
                            Database::execute(
                                "INSERT INTO cases (id, title, description, author_id, profile_json, tags, difficulty, schema_version, created_at, updated_at)
                                 VALUES (:id, :title, :desc, :author, :profile, :tags, :diff, :schema, :created, :updated)",
                                [
                                    ':id' => $entityId,
                                    ':title' => $data['title'] ?? '',
                                    ':desc' => $data['description'] ?? null,
                                    ':author' => $auth['sub'],
                                    ':profile' => json_encode($data['profile'] ?? new stdClass()),
                                    ':tags' => $data['tags'] ?? '',
                                    ':diff' => $data['difficulty'] ?? 'medium',
                                    ':schema' => $data['schemaVersion'] ?? 1,
                                    ':created' => $data['createdAt'] ?? date('c'),
                                    ':updated' => $updatedAt,
                                ]
                            );
                            $results[] = ['id' => $entityId, 'type' => $type, 'status' => 'created'];
                        }
                        break;

                    case 'agenda':
                        if ($auth['role'] === 'estudiante') {
                            $results[] = ['id' => $entityId, 'type' => $type, 'status' => 'denied'];
                            continue 2;
                        }

                        $existing = Database::fetchOne('SELECT id FROM agenda_items WHERE id = :id', [':id' => $entityId]);

                        if ($existing) {
                            Database::execute(
                                "UPDATE agenda_items SET title = :title, description = :desc,
                                    patient_name = :patient, scheduled_date = :date, scheduled_time = :time,
                                    duration_minutes = :dur, item_type = :type2
                                 WHERE id = :id",
                                [
                                    ':id' => $entityId,
                                    ':title' => $data['title'] ?? '',
                                    ':desc' => $data['description'] ?? null,
                                    ':patient' => $data['patientName'] ?? null,
                                    ':date' => $data['scheduledDate'] ?? date('Y-m-d'),
                                    ':time' => $data['scheduledTime'] ?? '00:00',
                                    ':dur' => $data['durationMinutes'] ?? 30,
                                    ':type2' => $data['itemType'] ?? 'appointment',
                                ]
                            );
                            $results[] = ['id' => $entityId, 'type' => $type, 'status' => 'updated'];
                        } else {
                            Database::execute(
                                "INSERT INTO agenda_items (id, author_id, title, description, patient_name,
                                    scheduled_date, scheduled_time, duration_minutes, item_type)
                                 VALUES (:id, :uid, :title, :desc, :patient, :date, :time, :dur, :type2)",
                                [
                                    ':id' => $entityId,
                                    ':uid' => $auth['sub'],
                                    ':title' => $data['title'] ?? '',
                                    ':desc' => $data['description'] ?? null,
                                    ':patient' => $data['patientName'] ?? null,
                                    ':date' => $data['scheduledDate'] ?? date('Y-m-d'),
                                    ':time' => $data['scheduledTime'] ?? '00:00',
                                    ':dur' => $data['durationMinutes'] ?? 30,
                                    ':type2' => $data['itemType'] ?? 'appointment',
                                ]
                            );
                            $results[] = ['id' => $entityId, 'type' => $type, 'status' => 'created'];
                        }
                        break;

                    default:
                        $results[] = ['id' => $entityId, 'type' => $type, 'status' => 'unsupported_type'];
                }

                // Log sync
                Database::execute(
                    "INSERT INTO sync_log (id, user_id, device_id, entity_type, entity_id, action)
                     VALUES (:id, :uid, :did, :type, :eid, 'push')",
                    [
                        ':id' => Database::uuid(),
                        ':uid' => $auth['sub'],
                        ':did' => $body['deviceId'] ?? null,
                        ':type' => $type,
                        ':eid' => $entityId,
                    ]
                );
            }

            $db->commit();
        } catch (Exception $e) {
            $db->rollBack();
            error_response('Error en sync push: ' . $e->getMessage(), 500);
        }

        json_response(['results' => $results]);
        break;

    // ─── PULL ───────────────────────────────────────
    case 'POST:pull':
        $auth = require_auth();
        $body = get_json_body();

        $since = $body['since'] ?? '1970-01-01T00:00:00';
        $types = $body['types'] ?? ['cases', 'agenda'];

        $data = [];

        if (in_array('cases', $types)) {
            $where = "updated_at > :since";
            $params = [':since' => $since];

            // Estudiantes solo ven casos publicados
            if ($auth['role'] === 'estudiante') {
                $where .= " AND is_published = 1";
            }

            $cases = Database::fetchAll("SELECT * FROM cases WHERE $where ORDER BY updated_at", $params);
            foreach ($cases as &$c) {
                $c['profile'] = json_decode($c['profile_json'], true);
                unset($c['profile_json']);
            }
            $data['cases'] = $cases;
        }

        if (in_array('agenda', $types)) {
            $agendaWhere = "a.is_active = 1 AND a.scheduled_date >= date('now', '-7 days')";
            $agendaParams = [];

            if ($auth['role'] === 'estudiante') {
                $agendaWhere .= " AND a.author_id = :uid";
                $agendaParams[':uid'] = $auth['sub'];
            }

            $data['agenda'] = Database::fetchAll(
                "SELECT a.* FROM agenda_items a WHERE $agendaWhere ORDER BY a.scheduled_date, a.scheduled_time",
                $agendaParams
            );
        }

        if (in_array('sessions', $types)) {
            $sessionsWhere = "ps.status IN ('approved','active')";
            $sessionsParams = [];

            if ($auth['role'] === 'estudiante') {
                $sessionsWhere .= " AND EXISTS (SELECT 1 FROM group_members gm WHERE gm.group_id = ps.group_id AND gm.user_id = :uid)";
                $sessionsParams[':uid'] = $auth['sub'];
            }

            $data['sessions'] = Database::fetchAll(
                "SELECT ps.* FROM practice_sessions ps WHERE $sessionsWhere ORDER BY ps.scheduled_date",
                $sessionsParams
            );
        }

        // Log
        foreach ($types as $type) {
            Database::execute(
                "INSERT INTO sync_log (id, user_id, device_id, entity_type, entity_id, action)
                 VALUES (:id, :uid, :did, :type, 'pull', 'pull')",
                [
                    ':id' => Database::uuid(),
                    ':uid' => $auth['sub'],
                    ':did' => $body['deviceId'] ?? null,
                    ':type' => $type,
                ]
            );
        }

        json_response([
            'data' => $data,
            'syncedAt' => date('c'),
        ]);
        break;

    // ─── STATUS ─────────────────────────────────────
    case 'GET:status':
        $auth = require_auth();

        $lastSync = Database::fetchOne(
            "SELECT MAX(synced_at) as last_synced FROM sync_log WHERE user_id = :uid",
            [':uid' => $auth['sub']]
        );

        $pending = Database::fetchAll(
            "SELECT entity_type, COUNT(*) as count FROM sync_log
             WHERE user_id = :uid AND synced_at > datetime('now', '-1 hour')
             GROUP BY entity_type",
            [':uid' => $auth['sub']]
        );

        json_response([
            'lastSynced' => $lastSync['last_synced'] ?? null,
            'recentActivity' => $pending,
        ]);
        break;

    default:
        error_response("Ruta no encontrada: sync/$action", 404);
}
