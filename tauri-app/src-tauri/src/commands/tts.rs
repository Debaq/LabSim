use serde::Serialize;
use tauri::State;
use crate::tts::TtsState;
use crate::commands::audio::AudioState;

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TtsModelInfo {
    pub id: String,
    pub name: String,
    pub size_mb: u32,
    pub onnx_path: String,
    pub config_path: String,
}

pub const TTS_MODELS: &[(&str, &str, &str, &str, u32)] = &[
    (
        "rhasspy/piper-voices",
        "Español MX — Ald (Medio)",
        "es/es_MX/ald/medium/es_MX-ald-medium.onnx",
        "es/es_MX/ald/medium/es_MX-ald-medium.onnx.json",
        63,
    ),
    (
        "rhasspy/piper-voices",
        "Español MX — Claude (Alto)",
        "es/es_MX/claude/high/es_MX-claude-high.onnx",
        "es/es_MX/claude/high/es_MX-claude-high.onnx.json",
        106,
    ),
];

#[tauri::command]
pub fn tts_list_models() -> Vec<TtsModelInfo> {
    TTS_MODELS
        .iter()
        .enumerate()
        .map(|(i, (_repo, name, onnx, config, size_mb))| TtsModelInfo {
            id: format!("tts-{}", i),
            name: name.to_string(),
            size_mb: *size_mb,
            onnx_path: onnx.to_string(),
            config_path: config.to_string(),
        })
        .collect()
}

#[tauri::command]
pub fn tts_status(tts: State<TtsState>) -> bool {
    let engine = tts.engine.lock().unwrap();
    engine.is_loaded()
}

#[tauri::command]
pub async fn tts_download_model(
    model_index: usize,
    app_handle: tauri::AppHandle,
) -> Result<String, String> {
    use tauri::Emitter;

    let (repo_id, _name, onnx_path, config_path, _) = TTS_MODELS
        .get(model_index)
        .ok_or("Índice de modelo inválido")?;

    let repo_id = repo_id.to_string();
    let onnx_path = onnx_path.to_string();
    let config_path = config_path.to_string();

    let _ = app_handle.emit("tts-download-progress", serde_json::json!({
        "status": "downloading",
        "progress": 0,
    }));

    let handle = app_handle.clone();
    let cfg_path = config_path.clone();

    let result_path = tauri::async_runtime::spawn_blocking(move || {
        let api = hf_hub::api::sync::ApiBuilder::new()
            .with_progress(false)
            .build()
            .map_err(|e| format!("Error API HF: {}", e))?;

        let repo = api.model(repo_id.clone());

        // Download ONNX model
        log::info!("Descargando TTS ONNX: {} / {}", repo_id, onnx_path);
        repo.get(&onnx_path)
            .map_err(|e| format!("Error descargando ONNX: {}", e))?;

        // Download config JSON
        log::info!("Descargando TTS config: {} / {}", repo_id, cfg_path);
        let config_file = repo.get(&cfg_path)
            .map_err(|e| format!("Error descargando config: {}", e))?;

        Ok::<String, String>(config_file.to_string_lossy().to_string())
    })
    .await
    .map_err(|e| format!("Error en hilo: {}", e))?
    ?;

    let _ = handle.emit("tts-download-progress", serde_json::json!({
        "status": "complete",
        "progress": 100,
    }));

    Ok(result_path)
}

#[tauri::command]
pub async fn tts_load_model(
    tts: State<'_, TtsState>,
    config_path: String,
) -> Result<bool, String> {
    let engine = tts.engine.clone();
    tauri::async_runtime::spawn_blocking(move || {
        let mut eng = engine.lock().unwrap();
        eng.load_model(&config_path)
    })
    .await
    .map_err(|e| format!("Error en hilo: {}", e))?
    ?;
    Ok(true)
}

#[tauri::command]
pub async fn tts_speak(
    tts: State<'_, TtsState>,
    audio: State<'_, AudioState>,
    text: String,
) -> Result<(), String> {
    let engine = tts.engine.clone();

    let (samples, sample_rate) = tauri::async_runtime::spawn_blocking(move || {
        let eng = engine.lock().unwrap();
        let samples = eng.synthesize(&text)?;
        let sr = eng.sample_rate();
        Ok::<(Vec<f32>, u32), String>((samples, sr))
    })
    .await
    .map_err(|e| format!("Error en hilo: {}", e))?
    ?;

    let guard = audio.engine.lock().unwrap();
    let audio_engine = guard.as_ref().ok_or("Motor de audio no disponible")?;
    audio_engine.play_raw_samples(samples, sample_rate)
}
