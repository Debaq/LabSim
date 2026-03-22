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

/// Cambiar contraseña del usuario actual
#[tauri::command]
pub async fn api_change_password(
    api: State<'_, ApiClient>,
    current_password: String,
    new_password: String,
) -> Result<serde_json::Value, String> {
    let body = json!({
        "currentPassword": current_password,
        "newPassword": new_password,
    });
    api.post("auth/change-password", &body).await
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

// ═══════════════════════════════════════════════════
// GESTIONAR PACIENTES (CRUD de casos)
// ═══════════════════════════════════════════════════

/// Listar casos con filtros
#[tauri::command]
pub async fn api_list_cases(
    api: State<'_, ApiClient>,
    search: Option<String>,
    published: Option<String>,
    difficulty: Option<String>,
    archived: Option<String>,
    page: Option<u32>,
    limit: Option<u32>,
) -> Result<serde_json::Value, String> {
    let mut params = vec![];
    if let Some(s) = search { params.push(format!("search={}", s)); }
    if let Some(p) = published { params.push(format!("published={}", p)); }
    if let Some(d) = difficulty { params.push(format!("difficulty={}", d)); }
    if let Some(a) = archived { params.push(format!("archived={}", a)); }
    if let Some(pg) = page { params.push(format!("page={}", pg)); }
    if let Some(l) = limit { params.push(format!("limit={}", l)); }
    let route = if params.is_empty() {
        "cases".to_string()
    } else {
        format!("cases&{}", params.join("&"))
    };
    api.get(&route).await
}

/// Obtener detalle de un caso
#[tauri::command]
pub async fn api_get_case(
    api: State<'_, ApiClient>,
    case_id: String,
) -> Result<serde_json::Value, String> {
    api.get(&format!("cases/{}", case_id)).await
}

/// Actualizar caso existente
#[tauri::command]
pub async fn api_update_case(
    api: State<'_, ApiClient>,
    case_id: String,
    case_data: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.put(&format!("cases/{}", case_id), &case_data).await
}

/// Eliminar caso
#[tauri::command]
pub async fn api_delete_case(
    api: State<'_, ApiClient>,
    case_id: String,
) -> Result<serde_json::Value, String> {
    api.delete(&format!("cases/{}", case_id)).await
}

/// Publicar/despublicar caso
#[tauri::command]
pub async fn api_toggle_publish(
    api: State<'_, ApiClient>,
    case_id: String,
) -> Result<serde_json::Value, String> {
    api.put(&format!("cases/{}/publish", case_id), &json!({})).await
}

/// Archivar/desarchivar caso
#[tauri::command]
pub async fn api_toggle_archive(
    api: State<'_, ApiClient>,
    case_id: String,
) -> Result<serde_json::Value, String> {
    api.put(&format!("cases/{}/archive", case_id), &json!({})).await
}

// ═══════════════════════════════════════════════════
// LARISSA: EVOLUCIONES E INTERCONSULTAS
// ═══════════════════════════════════════════════════

/// Listar evoluciones de una cita
#[tauri::command]
pub async fn api_list_evolutions(
    api: State<'_, ApiClient>,
    agenda_item_id: String,
) -> Result<serde_json::Value, String> {
    api.get(&format!("evolutions&agenda_item_id={}", agenda_item_id)).await
}

/// Crear evolución clínica
#[tauri::command]
pub async fn api_create_evolution(
    api: State<'_, ApiClient>,
    evolution: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("evolutions", &evolution).await
}

/// Editar evolución
#[tauri::command]
pub async fn api_update_evolution(
    api: State<'_, ApiClient>,
    evolution_id: String,
    data: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.put(&format!("evolutions/{}", evolution_id), &data).await
}

/// Listar interconsultas de una cita
#[tauri::command]
pub async fn api_list_interconsultations(
    api: State<'_, ApiClient>,
    agenda_item_id: String,
) -> Result<serde_json::Value, String> {
    api.get(&format!("interconsultations&agenda_item_id={}", agenda_item_id)).await
}

/// Crear interconsulta
#[tauri::command]
pub async fn api_create_interconsultation(
    api: State<'_, ApiClient>,
    data: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("interconsultations", &data).await
}

// ═══════════════════════════════════════════════════
// CURSOS E INSCRIPCIÓN
// ═══════════════════════════════════════════════════

/// Listar cursos
#[tauri::command]
pub async fn api_list_courses(
    api: State<'_, ApiClient>,
    institution_id: Option<String>,
) -> Result<serde_json::Value, String> {
    let route = match institution_id {
        Some(iid) => format!("courses&institution_id={}", iid),
        None => "courses".to_string(),
    };
    api.get(&route).await
}

/// Detalle de un curso
#[tauri::command]
pub async fn api_get_course(
    api: State<'_, ApiClient>,
    course_id: String,
) -> Result<serde_json::Value, String> {
    api.get(&format!("courses/{}", course_id)).await
}

/// Crear curso
#[tauri::command]
pub async fn api_create_course(
    api: State<'_, ApiClient>,
    data: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("courses", &data).await
}

/// Actualizar curso
#[tauri::command]
pub async fn api_update_course(
    api: State<'_, ApiClient>,
    course_id: String,
    data: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.put(&format!("courses/{}", course_id), &data).await
}

/// Inscribir estudiante en curso
#[tauri::command]
pub async fn api_enroll_student(
    api: State<'_, ApiClient>,
    course_id: String,
    user_id: String,
    role: Option<String>,
) -> Result<serde_json::Value, String> {
    api.post(&format!("courses/{}/members", course_id), &json!({
        "userId": user_id,
        "role": role.unwrap_or_else(|| "estudiante".to_string()),
    })).await
}

/// Quitar estudiante de curso
#[tauri::command]
pub async fn api_remove_student(
    api: State<'_, ApiClient>,
    course_id: String,
    user_id: String,
) -> Result<serde_json::Value, String> {
    api.delete(&format!("courses/{}/members/{}", course_id, user_id)).await
}

/// Import masivo de estudiantes (CSV)
#[tauri::command]
pub async fn api_import_students(
    api: State<'_, ApiClient>,
    course_id: String,
    students: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post(&format!("courses/{}/import", course_id), &json!({
        "students": students,
    })).await
}

/// Listar estudiantes de la institución
#[tauri::command]
pub async fn api_list_institution_students(
    api: State<'_, ApiClient>,
    search: Option<String>,
    institution_id: Option<String>,
) -> Result<serde_json::Value, String> {
    let mut params = vec!["role=estudiante".to_string()];
    if let Some(s) = search { params.push(format!("search={}", s)); }
    if let Some(iid) = institution_id { params.push(format!("institution_id={}", iid)); }
    api.get(&format!("users&{}", params.join("&"))).await
}

/// Crear estudiante (como docente)
#[tauri::command]
pub async fn api_create_student(
    api: State<'_, ApiClient>,
    data: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("users", &data).await
}

// ═══════════════════════════════════════════════════
// STATS DEL CENTRO
// ═══════════════════════════════════════════════════

/// Estadísticas del centro (incidentes, reuniones, planes, validaciones)
#[tauri::command]
pub async fn api_get_center_stats(
    api: State<'_, ApiClient>,
    session_id: Option<String>,
) -> Result<serde_json::Value, String> {
    let route = match session_id {
        Some(sid) => format!("stats/center&sessionId={}", sid),
        None => "stats/center".to_string(),
    };
    api.get(&route).await
}

// ═══════════════════════════════════════════════════
// CENTRO: PLANES DE MEJORA
// ═══════════════════════════════════════════════════

/// Listar planes de mejora de una sesión
#[tauri::command]
pub async fn api_get_plans(
    api: State<'_, ApiClient>,
    session_id: String,
) -> Result<serde_json::Value, String> {
    api.get(&format!("center/plans&sessionId={}", session_id)).await
}

/// Crear plan de mejora
#[tauri::command]
pub async fn api_create_plan(
    api: State<'_, ApiClient>,
    plan: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("center/plans", &plan).await
}

/// Actualizar plan de mejora
#[tauri::command]
pub async fn api_update_plan(
    api: State<'_, ApiClient>,
    plan_id: String,
    data: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.put(&format!("center/plans/{}", plan_id), &data).await
}

/// Completar tarea de plan
#[tauri::command]
pub async fn api_complete_task(
    api: State<'_, ApiClient>,
    task_id: String,
) -> Result<serde_json::Value, String> {
    api.post(&format!("center/plans/{}/complete", task_id), &json!({})).await
}

// ═══════════════════════════════════════════════════
// SUPERVISIÓN: VALIDACIONES
// ═══════════════════════════════════════════════════

/// Listar validaciones pendientes
#[tauri::command]
pub async fn api_get_validations(
    api: State<'_, ApiClient>,
    status: Option<String>,
) -> Result<serde_json::Value, String> {
    let route = match status {
        Some(s) => format!("center/validations&status={}", s),
        None => "center/validations".to_string(),
    };
    api.get(&route).await
}

/// Solicitar validación (estudiante)
#[tauri::command]
pub async fn api_request_validation(
    api: State<'_, ApiClient>,
    data: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("center/validations", &data).await
}

/// Resolver validación (docente)
#[tauri::command]
pub async fn api_resolve_validation(
    api: State<'_, ApiClient>,
    validation_id: String,
    data: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.put(&format!("center/validations/{}", validation_id), &data).await
}

// ═══════════════════════════════════════════════════
// PACIENTES VIVOS: LOGS DE INTERACCIÓN
// ═══════════════════════════════════════════════════

/// Listar logs de interacción de un paciente
#[tauri::command]
pub async fn api_get_patient_logs(
    api: State<'_, ApiClient>,
    case_id: String,
) -> Result<serde_json::Value, String> {
    api.get(&format!("patient-logs&case_id={}", case_id)).await
}

/// Crear log de interacción (al terminar atención)
#[tauri::command]
pub async fn api_create_patient_log(
    api: State<'_, ApiClient>,
    data: serde_json::Value,
) -> Result<serde_json::Value, String> {
    api.post("patient-logs", &data).await
}

/// Detectar conflictos de agenda para un estudiante
#[tauri::command]
pub async fn api_check_agenda_conflicts(
    api: State<'_, ApiClient>,
    student_id: String,
    date: String,
    time: String,
    duration: Option<u32>,
) -> Result<serde_json::Value, String> {
    let dur = duration.unwrap_or(30);
    api.get(&format!(
        "agenda/conflicts&studentId={}&date={}&time={}&duration={}",
        student_id, date, time, dur
    )).await
}

/// Agenda global de un estudiante específico
#[tauri::command]
pub async fn api_get_student_agenda(
    api: State<'_, ApiClient>,
    student_id: String,
    from: Option<String>,
    to: Option<String>,
) -> Result<serde_json::Value, String> {
    let mut params = vec![];
    if let Some(f) = from { params.push(format!("from={}", f)); }
    if let Some(t) = to { params.push(format!("to={}", t)); }
    let route = if params.is_empty() {
        format!("agenda/student/{}", student_id)
    } else {
        format!("agenda/student/{}&{}", student_id, params.join("&"))
    };
    api.get(&route).await
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
