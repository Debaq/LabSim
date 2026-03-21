<?php
/**
 * LabSim Backend - Telemetría
 *
 * POST /telemetry/session/start    → Iniciar sesión de app
 * POST /telemetry/session/end      → Finalizar sesión de app
 * POST /telemetry/events           → Enviar batch de eventos
 * POST /telemetry/encounter        → Enviar resumen de encounter
 * POST /telemetry/module           → Enviar stats de módulo
 */

require_once __DIR__ . '/../core/auth_middleware.php';

$action = $routeSegments[0] ?? null;
$subAction = $routeSegments[1] ?? null;
$combined = $action . ($subAction ? "/$subAction" : '');

if ($method !== 'POST') {
    error_response('Solo se acepta POST para telemetría', 405);
}

$auth = require_auth();
$body = get_json_body();

switch ($combined) {

    // ─── INICIAR SESIÓN DE APP ──────────────────────
    case 'session/start':
        $sessionId = Database::uuid();

        Database::execute(
            "INSERT INTO app_sessions (id, user_id, device_id, started_at, case_id, practice_session_id, app_version, os)
             VALUES (:id, :uid, :did, datetime('now'), :cid, :psid, :ver, :os)",
            [
                ':id' => $sessionId,
                ':uid' => $auth['sub'],
                ':did' => $body['deviceId'] ?? null,
                ':cid' => $body['caseId'] ?? null,
                ':psid' => $body['practiceSessionId'] ?? $body['assignmentId'] ?? null,
                ':ver' => $body['appVersion'] ?? null,
                ':os' => $body['os'] ?? null,
            ]
        );

        json_response(['sessionId' => $sessionId]);
        break;

    // ─── FINALIZAR SESIÓN DE APP ────────────────────
    case 'session/end':
        if (empty($body['sessionId'])) error_response('sessionId requerido', 400);

        Database::execute(
            "UPDATE app_sessions SET ended_at = datetime('now'), duration_seconds = :dur WHERE id = :id AND user_id = :uid",
            [
                ':id' => $body['sessionId'],
                ':uid' => $auth['sub'],
                ':dur' => $body['durationSecs'] ?? $body['duration_seconds'] ?? null,
            ]
        );

        json_response(['message' => 'Sesión finalizada']);
        break;

    // ─── BATCH DE EVENTOS ───────────────────────────
    case 'events':
        if (empty($body['sessionId'])) error_response('sessionId requerido', 400);
        if (empty($body['events']) || !is_array($body['events'])) error_response('events requerido (array)', 400);

        $events = $body['events'];
        if (count($events) > TELEMETRY_BATCH_MAX) {
            error_response("Máximo " . TELEMETRY_BATCH_MAX . " eventos por batch", 400);
        }

        $db = Database::get();
        $db->beginTransaction();

        try {
            $stmt = $db->prepare(
                "INSERT INTO simulator_events (id, session_id, user_id, simulator, event_type, event_data, event_timestamp)
                 VALUES (:id, :sid, :uid, :sim, :type, :data, :ts)"
            );

            foreach ($events as $event) {
                $stmt->execute([
                    ':id' => Database::uuid(),
                    ':sid' => $body['sessionId'],
                    ':uid' => $auth['sub'],
                    ':sim' => $event['simulator'] ?? 'unknown',
                    ':type' => $event['eventType'] ?? $event['event_type'] ?? 'unknown',
                    ':data' => json_encode($event['eventData'] ?? $event['event_data'] ?? new stdClass()),
                    ':ts' => $event['timestamp'] ?? $event['event_timestamp'] ?? date('c'),
                ]);
            }

            $db->commit();
        } catch (Exception $e) {
            $db->rollBack();
            error_response('Error al guardar eventos: ' . $e->getMessage(), 500);
        }

        json_response(['message' => 'Eventos guardados', 'count' => count($events)]);
        break;

    // ─── ENCOUNTER STATS ────────────────────────────
    case 'encounter':
        $stats = $body['stats'] ?? $body;
        $encounterId = Database::uuid();

        Database::execute(
            "INSERT INTO patient_encounter_stats (
                id, session_id, user_id, case_id, practice_session_id,
                total_duration_secs, anamnesis_duration_secs, audiometry_duration_secs,
                logoaudiometry_duration_secs, impedance_duration_secs, oae_duration_secs,
                abr_duration_secs, oct_duration_secs, perimetry_duration_secs, report_duration_secs,
                modules_completed, modules_visited, total_edits,
                audio_thresholds_recorded, audio_frequency_changes, audio_intensity_changes, audio_masking_used,
                vf_test_completed, vf_test_duration_secs, vf_fixation_loss_pct, vf_false_pos_pct, vf_false_neg_pct,
                oct_views_consulted, oct_time_on_bscan_secs, oct_time_on_rnfl_secs,
                started_at, completed_at
            ) VALUES (
                :id, :sid, :uid, :cid, :psid,
                :total, :anam, :audio, :logo, :imp, :oae, :abr, :oct, :peri, :rep,
                :mc, :mv, :edits,
                :thr, :freq, :int, :mask,
                :vfc, :vfd, :vffl, :vffp, :vffn,
                :octv, :octb, :octr,
                :start, :end
            )",
            [
                ':id' => $encounterId,
                ':sid' => $stats['sessionId'] ?? $body['sessionId'] ?? null,
                ':uid' => $auth['sub'],
                ':cid' => $stats['caseId'] ?? null,
                ':psid' => $stats['practiceSessionId'] ?? null,
                ':total' => $stats['totalDurationSecs'] ?? null,
                ':anam' => $stats['anamnesisDurationSecs'] ?? null,
                ':audio' => $stats['audiometryDurationSecs'] ?? null,
                ':logo' => $stats['logoaudiometryDurationSecs'] ?? null,
                ':imp' => $stats['impedanceDurationSecs'] ?? null,
                ':oae' => $stats['oaeDurationSecs'] ?? null,
                ':abr' => $stats['abrDurationSecs'] ?? null,
                ':oct' => $stats['octDurationSecs'] ?? null,
                ':peri' => $stats['perimetryDurationSecs'] ?? null,
                ':rep' => $stats['reportDurationSecs'] ?? null,
                ':mc' => $stats['modulesCompleted'] ?? 0,
                ':mv' => $stats['modulesVisited'] ?? 0,
                ':edits' => $stats['totalEdits'] ?? 0,
                ':thr' => $stats['audioThresholdsRecorded'] ?? 0,
                ':freq' => $stats['audioFrequencyChanges'] ?? 0,
                ':int' => $stats['audioIntensityChanges'] ?? 0,
                ':mask' => $stats['audioMaskingUsed'] ?? 0,
                ':vfc' => $stats['vfTestCompleted'] ?? 0,
                ':vfd' => $stats['vfTestDurationSecs'] ?? null,
                ':vffl' => $stats['vfFixationLossPct'] ?? null,
                ':vffp' => $stats['vfFalsePosPct'] ?? null,
                ':vffn' => $stats['vfFalseNegPct'] ?? null,
                ':octv' => $stats['octViewsConsulted'] ?? 0,
                ':octb' => $stats['octTimeOnBscanSecs'] ?? null,
                ':octr' => $stats['octTimeOnRnflSecs'] ?? null,
                ':start' => $stats['startedAt'] ?? null,
                ':end' => $stats['completedAt'] ?? null,
            ]
        );

        json_response(['encounterId' => $encounterId]);
        break;

    // ─── MODULE STATS ───────────────────────────────
    case 'module':
        $moduleId = Database::uuid();

        Database::execute(
            "INSERT INTO module_interaction_stats (id, session_id, user_id, module_id, time_spent_secs,
                fields_filled, fields_total, edits_count, first_opened_at, last_saved_at)
             VALUES (:id, :sid, :uid, :mid, :time, :filled, :total, :edits, :first, :last)",
            [
                ':id' => $moduleId,
                ':sid' => $body['sessionId'] ?? null,
                ':uid' => $auth['sub'],
                ':mid' => $body['moduleId'] ?? 'unknown',
                ':time' => $body['timeSpentSecs'] ?? null,
                ':filled' => $body['fieldsFilled'] ?? null,
                ':total' => $body['fieldsTotal'] ?? null,
                ':edits' => $body['editsCount'] ?? null,
                ':first' => $body['firstOpenedAt'] ?? null,
                ':last' => $body['lastSavedAt'] ?? null,
            ]
        );

        json_response(['message' => 'Stats de módulo guardados']);
        break;

    default:
        error_response("Ruta no encontrada: telemetry/$combined", 404);
}
