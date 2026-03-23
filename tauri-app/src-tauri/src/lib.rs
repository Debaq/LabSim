mod commands;
mod db;
mod audio;
mod models;
mod utils;
mod llm;
mod speech;
mod tts;
mod api;

use db::Database;
use llm::LlmState;
use commands::audio::AudioState;
use speech::SpeechState;
use tts::TtsState;
use commands::speech::RecordingState;
use api::client::ApiClient;

/// Resolve the path to a sidecar binary.
/// In development: looks next to the main binary or in binaries/ dir.
/// In production: bundled by Tauri alongside the main executable.
fn resolve_sidecar(name: &str) -> String {
    let exe = std::env::current_exe().unwrap_or_default();
    let exe_dir = exe.parent().unwrap_or(std::path::Path::new("."));

    // Try next to executable first (production bundle)
    let beside = exe_dir.join(name);
    if beside.exists() {
        return beside.to_string_lossy().to_string();
    }

    // Try with .exe extension (Windows)
    let beside_exe = exe_dir.join(format!("{}.exe", name));
    if beside_exe.exists() {
        return beside_exe.to_string_lossy().to_string();
    }

    // Development: try binaries/ dir relative to src-tauri
    // (when running via `tauri dev`, exe is in target/debug/)
    let target_triple = if cfg!(target_os = "windows") {
        if cfg!(target_arch = "x86_64") { "x86_64-pc-windows-msvc" }
        else { "aarch64-pc-windows-msvc" }
    } else if cfg!(target_os = "macos") {
        if cfg!(target_arch = "x86_64") { "x86_64-apple-darwin" }
        else { "aarch64-apple-darwin" }
    } else {
        if cfg!(target_arch = "x86_64") { "x86_64-unknown-linux-gnu" }
        else { "aarch64-unknown-linux-gnu" }
    };

    let dev_path = exe_dir.join(format!("{}-{}", name, target_triple));
    if dev_path.exists() {
        return dev_path.to_string_lossy().to_string();
    }

    // Fallback: just the name, hope it's in PATH or current dir
    name.to_string()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let db = Database::new().expect("Error inicializando base de datos");

    let llm_path = resolve_sidecar("labsim-llm");
    let speech_path = resolve_sidecar("labsim-speech");

    let llm = LlmState::new(llm_path);
    let audio = AudioState::new();
    let speech = SpeechState::new(speech_path);
    let tts = TtsState::new();
    let recording = RecordingState::new();
    let api_client = ApiClient::new();

    tauri::Builder::default()
        .manage(db)
        .manage(llm)
        .manage(audio)
        .manage(speech)
        .manage(tts)
        .manage(recording)
        .manage(api_client)
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::auth::login,
            commands::patients::list_patients,
            commands::patients::get_patient,
            commands::patients::save_patient,
            commands::patients::delete_patient,
            commands::audio::play_tone,
            commands::audio::play_noise,
            commands::audio::stop_playback,
            commands::chat::llm_list_models,
            commands::chat::llm_load_model_async,
            commands::chat::llm_download_model,
            commands::chat::llm_status,
            commands::chat::llm_chat,
            commands::speech::speech_status,
            commands::speech::speech_load_model,
            commands::speech::speech_start_recording,
            commands::speech::speech_stop_recording,
            commands::speech::speech_transcribe,
            commands::speech::speech_is_recording,
            // TTS (Piper)
            commands::tts::tts_list_models,
            commands::tts::tts_status,
            commands::tts::tts_loaded_voices,
            commands::tts::tts_download_model,
            commands::tts::tts_load_model,
            commands::tts::tts_speak,
            // API / Sync
            commands::sync::api_login,
            commands::sync::api_logout,
            commands::sync::api_change_password,
            commands::sync::api_sync_cases,
            commands::sync::api_push_case,
            commands::sync::api_list_cases,
            commands::sync::api_get_case,
            commands::sync::api_update_case,
            commands::sync::api_delete_case,
            commands::sync::api_toggle_publish,
            commands::sync::api_toggle_archive,
            // Stats del centro
            commands::sync::api_get_center_stats,
            // Centro: planes de mejora
            commands::sync::api_get_plans,
            commands::sync::api_create_plan,
            commands::sync::api_update_plan,
            commands::sync::api_complete_task,
            // Supervisión: validaciones
            commands::sync::api_get_validations,
            commands::sync::api_request_validation,
            commands::sync::api_resolve_validation,
            // Pacientes vivos: logs de interacción
            commands::sync::api_get_patient_logs,
            commands::sync::api_create_patient_log,
            // Agenda: conflictos y vista estudiante
            commands::sync::api_check_agenda_conflicts,
            commands::sync::api_get_student_agenda,
            // Cursos e inscripción
            commands::sync::api_list_courses,
            commands::sync::api_get_course,
            commands::sync::api_create_course,
            commands::sync::api_update_course,
            commands::sync::api_enroll_student,
            commands::sync::api_remove_student,
            commands::sync::api_import_students,
            commands::sync::api_list_institution_students,
            commands::sync::api_search_users,
            commands::sync::api_create_student,
            // Larissa: evoluciones e interconsultas
            commands::sync::api_list_evolutions,
            commands::sync::api_create_evolution,
            commands::sync::api_update_evolution,
            commands::sync::api_list_interconsultations,
            commands::sync::api_create_interconsultation,
            commands::sync::api_respond_interconsultation,
            commands::sync::api_submit_work,
            commands::sync::api_check_update,
            commands::sync::api_get_agenda,
            commands::sync::api_get_sessions,
            commands::sync::api_get_session_detail,
            commands::sync::api_create_session,
            commands::sync::api_update_session,
            commands::sync::api_activate_session,
            commands::sync::api_delete_session,
            commands::sync::api_add_session_case,
            commands::sync::api_remove_session_case,
            commands::sync::api_list_groups,
            commands::sync::api_create_group,
            commands::sync::api_add_group_member,
            commands::sync::api_remove_group_member,
            commands::sync::api_get_submissions,
            commands::sync::api_ping,
            commands::sync::api_get_my_stats,
            // Procedimientos
            commands::sync::api_get_procedures,
            // Directrices Karime
            commands::sync::api_get_directives,
            commands::sync::api_resolve_directives,
            commands::sync::api_save_directive,
            commands::sync::api_update_directive,
            commands::sync::api_delete_directive,
            commands::sync::api_approve_directive,
            // Feedback pacientes
            commands::sync::api_send_feedback,
            commands::sync::api_get_feedback,
            commands::sync::api_get_feedback_summary,
            // Centro: Boxes
            commands::sync::api_get_boxes,
            commands::sync::api_create_boxes,
            commands::sync::api_assign_box,
            // Centro: Incidentes
            commands::sync::api_get_incident_templates,
            commands::sync::api_get_incidents,
            commands::sync::api_inject_incident,
            commands::sync::api_resolve_incident,
            commands::sync::api_discuss_incident,
            // Centro: Reuniones
            commands::sync::api_get_meetings,
            commands::sync::api_call_meeting,
            commands::sync::api_start_meeting,
            commands::sync::api_end_meeting,
            // Centro: Chat
            commands::sync::api_get_chat,
            commands::sync::api_send_chat,
            // Base de Conocimiento
            commands::sync::api_list_kb_articles,
            commands::sync::api_get_kb_article,
            commands::sync::api_create_kb_article,
            commands::sync::api_update_kb_article,
            commands::sync::api_delete_kb_article,
            commands::sync::api_list_kb_categories,
            // Agenda extendida
            commands::sync::api_create_agenda_item,
            commands::sync::api_update_agenda_item,
            commands::sync::api_assign_agenda_group,
            commands::sync::api_reschedule_appointment,
            commands::sync::api_update_appointment_status,
            // Telemetría
            commands::telemetry::telemetry_start_session,
            commands::telemetry::telemetry_end_session,
            commands::telemetry::telemetry_push_events,
            commands::telemetry::telemetry_push_encounter,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
