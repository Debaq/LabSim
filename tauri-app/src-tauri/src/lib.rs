mod commands;
mod db;
mod audio;
mod models;
mod utils;
mod llm;
mod speech;

use db::Database;
use llm::LlmState;
use commands::audio::AudioState;
use speech::SpeechState;
use commands::speech::RecordingState;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let db = Database::new().expect("Error inicializando base de datos");
    let llm = LlmState::new();
    let audio = AudioState::new();
    let speech = SpeechState::new();
    let recording = RecordingState::new();

    tauri::Builder::default()
        .manage(db)
        .manage(llm)
        .manage(audio)
        .manage(speech)
        .manage(recording)
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
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
