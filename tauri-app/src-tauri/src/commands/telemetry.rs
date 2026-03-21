use serde::{Deserialize, Serialize};
use serde_json::json;
use tauri::State;
use crate::api::client::ApiClient;

#[derive(Debug, Serialize, Deserialize)]
pub struct SimulatorEvent {
    pub simulator: String,
    pub event_type: String,
    pub event_data: serde_json::Value,
    pub timestamp: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EncounterStats {
    pub session_id: Option<String>,
    pub case_id: Option<String>,
    pub practice_session_id: Option<String>,
    pub total_duration_secs: Option<u64>,
    pub anamnesis_duration_secs: Option<u64>,
    pub audiometry_duration_secs: Option<u64>,
    pub logoaudiometry_duration_secs: Option<u64>,
    pub impedance_duration_secs: Option<u64>,
    pub oae_duration_secs: Option<u64>,
    pub abr_duration_secs: Option<u64>,
    pub oct_duration_secs: Option<u64>,
    pub perimetry_duration_secs: Option<u64>,
    pub modules_completed: Option<u32>,
    pub modules_visited: Option<u32>,
    pub total_edits: Option<u32>,
    pub audio_thresholds_recorded: Option<u32>,
    pub audio_frequency_changes: Option<u32>,
    pub audio_intensity_changes: Option<u32>,
    pub audio_masking_used: Option<u32>,
    pub vf_test_completed: Option<u32>,
    pub vf_test_duration_secs: Option<u64>,
    pub oct_views_consulted: Option<u32>,
    pub started_at: Option<String>,
    pub completed_at: Option<String>,
}

/// Iniciar sesión de telemetría
#[tauri::command]
pub async fn telemetry_start_session(
    api: State<'_, ApiClient>,
    case_id: Option<String>,
    assignment_id: Option<String>,
    app_version: Option<String>,
    os: Option<String>,
) -> Result<String, String> {
    let body = json!({
        "caseId": case_id,
        "practiceSessionId": assignment_id,
        "appVersion": app_version,
        "os": os,
    });

    let resp = api.post("telemetry/session/start", &body).await?;
    resp.get("sessionId")
        .and_then(|v| v.as_str())
        .map(|s| s.to_string())
        .ok_or_else(|| "No se recibió sessionId".to_string())
}

/// Finalizar sesión de telemetría
#[tauri::command]
pub async fn telemetry_end_session(
    api: State<'_, ApiClient>,
    session_id: String,
    duration_secs: u64,
) -> Result<(), String> {
    let body = json!({
        "sessionId": session_id,
        "durationSecs": duration_secs,
    });
    api.post("telemetry/session/end", &body).await?;
    Ok(())
}

/// Enviar batch de eventos de simulador
#[tauri::command]
pub async fn telemetry_push_events(
    api: State<'_, ApiClient>,
    session_id: String,
    events: Vec<SimulatorEvent>,
) -> Result<(), String> {
    if events.is_empty() {
        return Ok(());
    }

    let body = json!({
        "sessionId": session_id,
        "events": events.iter().map(|e| json!({
            "simulator": e.simulator,
            "eventType": e.event_type,
            "eventData": e.event_data,
            "timestamp": e.timestamp,
        })).collect::<Vec<_>>(),
    });

    api.post("telemetry/events", &body).await?;
    Ok(())
}

/// Enviar resumen de encounter
#[tauri::command]
pub async fn telemetry_push_encounter(
    api: State<'_, ApiClient>,
    stats: EncounterStats,
) -> Result<(), String> {
    let body = json!({
        "sessionId": stats.session_id,
        "stats": {
            "caseId": stats.case_id,
            "practiceSessionId": stats.practice_session_id,
            "totalDurationSecs": stats.total_duration_secs,
            "anamnesisDurationSecs": stats.anamnesis_duration_secs,
            "audiometryDurationSecs": stats.audiometry_duration_secs,
            "logoaudiometryDurationSecs": stats.logoaudiometry_duration_secs,
            "impedanceDurationSecs": stats.impedance_duration_secs,
            "oaeDurationSecs": stats.oae_duration_secs,
            "abrDurationSecs": stats.abr_duration_secs,
            "octDurationSecs": stats.oct_duration_secs,
            "perimetryDurationSecs": stats.perimetry_duration_secs,
            "modulesCompleted": stats.modules_completed,
            "modulesVisited": stats.modules_visited,
            "totalEdits": stats.total_edits,
            "audioThresholdsRecorded": stats.audio_thresholds_recorded,
            "audioFrequencyChanges": stats.audio_frequency_changes,
            "audioIntensityChanges": stats.audio_intensity_changes,
            "audioMaskingUsed": stats.audio_masking_used,
            "vfTestCompleted": stats.vf_test_completed,
            "vfTestDurationSecs": stats.vf_test_duration_secs,
            "octViewsConsulted": stats.oct_views_consulted,
            "startedAt": stats.started_at,
            "completedAt": stats.completed_at,
        }
    });

    api.post("telemetry/encounter", &body).await?;
    Ok(())
}
