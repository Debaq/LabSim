use serde::{Deserialize, Serialize};
use serde_json::json;
use tauri::State;
use crate::api::client::ApiClient;

#[derive(Debug, Serialize, Deserialize)]
pub struct ApiLoginResult {
    pub success: bool,
    pub user: Option<serde_json::Value>,
    pub source: String, // "server" o "local"
}

/// Login contra el servidor remoto, con fallback a SQLite local
#[tauri::command]
pub async fn api_login(
    api: State<'_, ApiClient>,
    username: String,
    password: String,
) -> Result<ApiLoginResult, String> {
    // Intentar servidor primero
    let body = json!({ "username": username, "password": password });

    match api.post("auth/login", &body).await {
        Ok(resp) => {
            // Guardar tokens
            if let (Some(access), Some(refresh)) = (
                resp.get("accessToken").and_then(|v| v.as_str()),
                resp.get("refreshToken").and_then(|v| v.as_str()),
            ) {
                api.set_tokens(crate::api::client::TokenPair {
                    access_token: access.to_string(),
                    refresh_token: refresh.to_string(),
                });
            }

            Ok(ApiLoginResult {
                success: true,
                user: resp.get("user").cloned(),
                source: "server".to_string(),
            })
        }
        Err(_) => {
            // Fallback: login local (SQLite)
            Err("No se pudo conectar al servidor. Login local no implementado aún.".to_string())
        }
    }
}

/// Logout: revocar tokens
#[tauri::command]
pub async fn api_logout(api: State<'_, ApiClient>) -> Result<(), String> {
    let _ = api.post("auth/logout", &json!({})).await;
    api.clear_tokens();
    Ok(())
}

/// Sincronizar casos: pull del servidor
#[tauri::command]
pub async fn api_sync_cases(
    api: State<'_, ApiClient>,
    since: Option<String>,
) -> Result<serde_json::Value, String> {
    let body = json!({
        "since": since.unwrap_or_else(|| "1970-01-01T00:00:00".to_string()),
        "types": ["cases"]
    });
    api.post("sync/pull", &body).await
}

/// Push un caso al servidor
#[tauri::command]
pub async fn api_push_case(
    api: State<'_, ApiClient>,
    case_data: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("cases", &case_data).await
}

/// Enviar entrega de trabajo
#[tauri::command]
pub async fn api_submit_work(
    api: State<'_, ApiClient>,
    session_id: String,
    case_id: String,
    submission_json: serde_json::Value,
) -> Result<serde_json::Value, String> {
    let body = json!({
        "sessionId": session_id,
        "caseId": case_id,
        "submissionJson": submission_json
    });
    api.post("submissions", &body).await
}

/// Verificar si hay actualizaciones
#[tauri::command]
pub async fn api_check_update(
    api: State<'_, ApiClient>,
) -> Result<serde_json::Value, String> {
    api.get("releases/latest").await
}

/// Obtener agenda
#[tauri::command]
pub async fn api_get_agenda(
    api: State<'_, ApiClient>,
    from: Option<String>,
    to: Option<String>,
) -> Result<serde_json::Value, String> {
    let mut route = "agenda".to_string();
    let mut params = vec![];
    if let Some(f) = from { params.push(format!("from={}", f)); }
    if let Some(t) = to { params.push(format!("to={}", t)); }
    if !params.is_empty() {
        route = format!("agenda&{}", params.join("&"));
    }
    api.get(&route).await
}

/// Obtener sesiones prácticas
#[tauri::command]
pub async fn api_get_sessions(
    api: State<'_, ApiClient>,
    status: Option<String>,
) -> Result<serde_json::Value, String> {
    let route = match status {
        Some(s) => format!("sessions&status={}", s),
        None => "sessions".to_string(),
    };
    api.get(&route).await
}

/// Obtener detalle de una sesión
#[tauri::command]
pub async fn api_get_session_detail(
    api: State<'_, ApiClient>,
    session_id: String,
) -> Result<serde_json::Value, String> {
    api.get(&format!("sessions/{}", session_id)).await
}

/// Obtener mis entregas
#[tauri::command]
pub async fn api_get_submissions(
    api: State<'_, ApiClient>,
    session_id: Option<String>,
) -> Result<serde_json::Value, String> {
    let route = match session_id {
        Some(sid) => format!("submissions&sessionId={}", sid),
        None => "submissions".to_string(),
    };
    api.get(&route).await
}

/// Verificar conectividad
#[tauri::command]
pub async fn api_ping(api: State<'_, ApiClient>) -> Result<bool, String> {
    Ok(api.ping().await)
}

/// Obtener mis estadísticas
#[tauri::command]
pub async fn api_get_my_stats(api: State<'_, ApiClient>) -> Result<serde_json::Value, String> {
    api.get("stats/me").await
}

// ═══════════════════════════════════════════════════
// PROCEDIMIENTOS
// ═══════════════════════════════════════════════════

#[tauri::command]
pub async fn api_get_procedures(
    api: State<'_, ApiClient>,
    category: Option<String>,
) -> Result<serde_json::Value, String> {
    let route = match category {
        Some(c) => format!("procedures&category={}", c),
        None => "procedures".to_string(),
    };
    api.get(&route).await
}

// ═══════════════════════════════════════════════════
// DIRECTRICES KARIME
// ═══════════════════════════════════════════════════

#[tauri::command]
pub async fn api_get_directives(api: State<'_, ApiClient>) -> Result<serde_json::Value, String> {
    api.get("directives").await
}

#[tauri::command]
pub async fn api_resolve_directives(
    api: State<'_, ApiClient>,
    session_id: Option<String>,
) -> Result<serde_json::Value, String> {
    let route = match session_id {
        Some(sid) => format!("directives/resolve&sessionId={}", sid),
        None => "directives/resolve".to_string(),
    };
    api.get(&route).await
}

#[tauri::command]
pub async fn api_save_directive(
    api: State<'_, ApiClient>,
    directive: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("directives", &directive).await
}

// ═══════════════════════════════════════════════════
// FEEDBACK PACIENTES
// ═══════════════════════════════════════════════════

#[tauri::command]
pub async fn api_send_feedback(
    api: State<'_, ApiClient>,
    feedback: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("feedback", &feedback).await
}

#[tauri::command]
pub async fn api_get_feedback(
    api: State<'_, ApiClient>,
    unread: Option<bool>,
) -> Result<serde_json::Value, String> {
    let route = match unread {
        Some(true) => "feedback&unread=true".to_string(),
        _ => "feedback".to_string(),
    };
    api.get(&route).await
}

#[tauri::command]
pub async fn api_get_feedback_summary(api: State<'_, ApiClient>) -> Result<serde_json::Value, String> {
    api.get("feedback/summary").await
}

// ═══════════════════════════════════════════════════
// CENTRO: BOXES
// ═══════════════════════════════════════════════════

#[tauri::command]
pub async fn api_get_boxes(
    api: State<'_, ApiClient>,
    session_id: String,
) -> Result<serde_json::Value, String> {
    api.get(&format!("center/boxes&sessionId={}", session_id)).await
}

#[tauri::command]
pub async fn api_create_boxes(
    api: State<'_, ApiClient>,
    session_id: String,
    box_count: u32,
) -> Result<serde_json::Value, String> {
    api.post("center/boxes", &json!({
        "sessionId": session_id,
        "boxCount": box_count,
    })).await
}

#[tauri::command]
pub async fn api_assign_box(
    api: State<'_, ApiClient>,
    box_id: String,
    student_id: String,
) -> Result<serde_json::Value, String> {
    api.put(&format!("center/boxes/{}", box_id), &json!({
        "studentId": student_id,
    })).await
}

// ═══════════════════════════════════════════════════
// CENTRO: INCIDENTES
// ═══════════════════════════════════════════════════

#[tauri::command]
pub async fn api_get_incident_templates(
    api: State<'_, ApiClient>,
    category: Option<String>,
) -> Result<serde_json::Value, String> {
    let route = match category {
        Some(c) => format!("center/incidents/templates&category={}", c),
        None => "center/incidents/templates".to_string(),
    };
    api.get(&route).await
}

#[tauri::command]
pub async fn api_get_incidents(
    api: State<'_, ApiClient>,
    session_id: String,
) -> Result<serde_json::Value, String> {
    api.get(&format!("center/incidents&sessionId={}", session_id)).await
}

#[tauri::command]
pub async fn api_inject_incident(
    api: State<'_, ApiClient>,
    incident: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("center/incidents", &incident).await
}

#[tauri::command]
pub async fn api_resolve_incident(
    api: State<'_, ApiClient>,
    incident_id: String,
    notes: Option<String>,
) -> Result<serde_json::Value, String> {
    api.post(&format!("center/incidents/{}/resolve", incident_id), &json!({
        "notes": notes,
    })).await
}

#[tauri::command]
pub async fn api_discuss_incident(
    api: State<'_, ApiClient>,
    incident_id: String,
) -> Result<serde_json::Value, String> {
    api.post(&format!("center/incidents/{}/discuss", incident_id), &json!({})).await
}

// ═══════════════════════════════════════════════════
// CENTRO: REUNIONES CLÍNICAS
// ═══════════════════════════════════════════════════

#[tauri::command]
pub async fn api_get_meetings(
    api: State<'_, ApiClient>,
    session_id: String,
) -> Result<serde_json::Value, String> {
    api.get(&format!("center/meetings&sessionId={}", session_id)).await
}

#[tauri::command]
pub async fn api_call_meeting(
    api: State<'_, ApiClient>,
    meeting: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("center/meetings", &meeting).await
}

#[tauri::command]
pub async fn api_start_meeting(
    api: State<'_, ApiClient>,
    meeting_id: String,
) -> Result<serde_json::Value, String> {
    api.post(&format!("center/meetings/{}/start", meeting_id), &json!({})).await
}

#[tauri::command]
pub async fn api_end_meeting(
    api: State<'_, ApiClient>,
    meeting_id: String,
    minutes: Option<String>,
    decisions: Option<String>,
) -> Result<serde_json::Value, String> {
    api.post(&format!("center/meetings/{}/end", meeting_id), &json!({
        "minutesText": minutes,
        "decisionsText": decisions,
    })).await
}

// ═══════════════════════════════════════════════════
// CENTRO: CHAT
// ═══════════════════════════════════════════════════

#[tauri::command]
pub async fn api_get_chat(
    api: State<'_, ApiClient>,
    session_id: String,
    since: Option<String>,
) -> Result<serde_json::Value, String> {
    let route = match since {
        Some(s) => format!("center/chat&sessionId={}&since={}", session_id, s),
        None => format!("center/chat&sessionId={}", session_id),
    };
    api.get(&route).await
}

#[tauri::command]
pub async fn api_send_chat(
    api: State<'_, ApiClient>,
    message: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("center/chat", &message).await
}

// ═══════════════════════════════════════════════════
// AGENDA (extendida)
// ═══════════════════════════════════════════════════

#[tauri::command]
pub async fn api_create_agenda_item(
    api: State<'_, ApiClient>,
    item: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("agenda", &item).await
}

#[tauri::command]
pub async fn api_assign_agenda_group(
    api: State<'_, ApiClient>,
    item: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("agenda/assign-group", &item).await
}

#[tauri::command]
pub async fn api_reschedule_appointment(
    api: State<'_, ApiClient>,
    appointment_id: String,
    scheduled_date: String,
    scheduled_time: String,
) -> Result<serde_json::Value, String> {
    api.post(&format!("agenda/{}/reschedule", appointment_id), &json!({
        "scheduledDate": scheduled_date,
        "scheduledTime": scheduled_time,
    })).await
}

#[tauri::command]
pub async fn api_update_appointment_status(
    api: State<'_, ApiClient>,
    appointment_id: String,
    status: String,
    notes: Option<String>,
) -> Result<serde_json::Value, String> {
    api.post(&format!("agenda/{}/status", appointment_id), &json!({
        "status": status,
        "notes": notes,
    })).await
}
