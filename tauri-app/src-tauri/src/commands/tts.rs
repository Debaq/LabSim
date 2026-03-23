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
    /// ID de la voz para el motor TTS ("male", "female", "karime")
    pub voice_id: String,
    /// Rol en LabSim ("Paciente masculino", "Paciente femenino", "Karime")
    pub role: String,
}

/// (repo, nombre, onnx, config, size_mb, voice_id, role)
/// voice_id se usa para cargar/referir la voz en el motor
/// role describe para qué se usa en LabSim
pub const TTS_MODELS: &[(&str, &str, &str, &str, u32, &str, &str)] = &[
    (
        "rhasspy/piper-voices",
        "Ald — Paciente Masculino ♂",
        "es/es_MX/ald/medium/es_MX-ald-medium.onnx",
        "es/es_MX/ald/medium/es_MX-ald-medium.onnx.json",
        63,
        "male",
        "Paciente masculino",
    ),
    (
        "rhasspy/piper-voices",
        "Claude — Paciente Femenino ♀",
        "es/es_MX/claude/high/es_MX-claude-high.onnx",
        "es/es_MX/claude/high/es_MX-claude-high.onnx.json",
        106,
        "female",
        "Paciente femenino",
    ),
    (
        "rhasspy/piper-voices",
        "Daniela — Karime ♀",
        "es/es_AR/daniela/high/es_AR-daniela-high.onnx",
        "es/es_AR/daniela/high/es_AR-daniela-high.onnx.json",
        109,
        "karime",
        "Karime (secretaria)",
    ),
];

#[tauri::command]
pub fn tts_list_models() -> Vec<TtsModelInfo> {
    TTS_MODELS
        .iter()
        .enumerate()
        .map(|(i, (_repo, name, onnx, config, size_mb, voice_id, role))| TtsModelInfo {
            id: format!("tts-{}", i),
            name: name.to_string(),
            size_mb: *size_mb,
            onnx_path: onnx.to_string(),
            config_path: config.to_string(),
            voice_id: voice_id.to_string(),
            role: role.to_string(),
        })
        .collect()
}

#[tauri::command]
pub fn tts_status(tts: State<TtsState>) -> bool {
    let engine = tts.engine.lock().unwrap();
    engine.is_loaded()
}

/// Devuelve las voces actualmente cargadas en memoria
#[tauri::command]
pub fn tts_loaded_voices(tts: State<TtsState>) -> Vec<(String, String)> {
    let engine = tts.engine.lock().unwrap();
    engine.loaded_voices()
}

#[tauri::command]
pub async fn tts_download_model(
    model_index: usize,
    app_handle: tauri::AppHandle,
) -> Result<String, String> {
    use tauri::Emitter;

    let (repo_id, _name, onnx_path, config_path, _, _, _) = TTS_MODELS
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

        log::info!("Descargando TTS ONNX: {} / {}", repo_id, onnx_path);
        repo.get(&onnx_path)
            .map_err(|e| format!("Error descargando ONNX: {}", e))?;

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

/// Carga un modelo TTS con un voice_id (ej: "male", "female", "male-alt")
#[tauri::command]
pub async fn tts_load_model(
    tts: State<'_, TtsState>,
    config_path: String,
    voice_id: Option<String>,
    label: Option<String>,
) -> Result<bool, String> {
    let vid = voice_id.unwrap_or_else(|| "default".to_string());
    let lbl = label.unwrap_or_else(|| vid.clone());
    let engine = tts.engine.clone();
    tauri::async_runtime::spawn_blocking(move || {
        let mut eng = engine.lock().unwrap();
        eng.load_model(&vid, &lbl, &config_path)
    })
    .await
    .map_err(|e| format!("Error en hilo: {}", e))?
    ?;
    Ok(true)
}

/// Habla con la voz por defecto o una voz específica.
/// Retorna la duración del audio en milisegundos para que el frontend
/// pueda esperar antes de reproducir la siguiente línea.
///
/// - `pitch_shift`: semitonos (-4 a +4). Cada semitono = factor 2^(1/12).
/// - `speech_rate`: factor de velocidad (0.75 a 1.3). 1.0 = normal.
///
/// Ambos se aplican modificando la tasa de muestreo de reproducción:
///   effective_rate = sample_rate × 2^(pitch/12) × speed
#[tauri::command]
pub async fn tts_speak(
    tts: State<'_, TtsState>,
    audio: State<'_, AudioState>,
    text: String,
    voice_id: Option<String>,
    pitch_shift: Option<f64>,
    speech_rate: Option<f64>,
) -> Result<u64, String> {
    let engine = tts.engine.clone();

    let (samples, sample_rate) = tauri::async_runtime::spawn_blocking(move || {
        let eng = engine.lock().unwrap();
        match voice_id {
            Some(vid) => eng.synthesize_with(&vid, &text),
            None => eng.synthesize(&text),
        }
    })
    .await
    .map_err(|e| format!("Error en hilo: {}", e))?
    ?;

    // Aplicar modificaciones de voz via sample rate
    let pitch = pitch_shift.unwrap_or(0.0).clamp(-4.0, 4.0);
    let rate = speech_rate.unwrap_or(1.0).clamp(0.75, 1.3);
    let factor = 2.0_f64.powf(pitch / 12.0) * rate;
    let effective_rate = ((sample_rate as f64) * factor).round() as u32;

    let duration_ms = (samples.len() as u64 * 1000) / effective_rate as u64;

    let guard = audio.engine.lock().unwrap();
    let audio_engine = guard.as_ref().ok_or("Motor de audio no disponible")?;
    audio_engine.play_raw_samples(samples, effective_rate)?;

    Ok(duration_ms)
}
