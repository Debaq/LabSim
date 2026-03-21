use serde::Deserialize;
use tauri::State;
use crate::audio::engine::AudioEngine;
use std::sync::Mutex;

pub struct AudioState {
    pub engine: Mutex<Option<AudioEngine>>,
}

impl AudioState {
    pub fn new() -> Self {
        match AudioEngine::new() {
            Ok(engine) => Self {
                engine: Mutex::new(Some(engine)),
            },
            Err(e) => {
                log::warn!("No se pudo inicializar audio: {}", e);
                Self {
                    engine: Mutex::new(None),
                }
            }
        }
    }
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ToneParams {
    pub frequency: f32,
    pub duration: f32,
    pub level_dbfs: f32,
    pub pulsatile_hz: Option<f32>,
    pub duty_cycle: Option<f32>,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct NoiseParams {
    pub noise_type: String,
    pub duration: f32,
    pub level_dbfs: f32,
    pub center_hz: Option<f32>,
    pub bandwidth_hz: Option<f32>,
}

#[tauri::command]
pub fn play_tone(audio: State<AudioState>, params: ToneParams) -> Result<(), String> {
    let guard = audio.engine.lock().unwrap();
    let engine = guard.as_ref().ok_or("Motor de audio no disponible")?;

    engine.play_tone(
        params.frequency,
        params.duration,
        params.level_dbfs,
        params.pulsatile_hz,
        params.duty_cycle.unwrap_or(0.5),
    )
}

#[tauri::command]
pub fn play_noise(audio: State<AudioState>, params: NoiseParams) -> Result<(), String> {
    let guard = audio.engine.lock().unwrap();
    let engine = guard.as_ref().ok_or("Motor de audio no disponible")?;

    match params.noise_type.as_str() {
        "white" => engine.play_white_noise(params.duration, params.level_dbfs),
        "pink" => engine.play_pink_noise(params.duration, params.level_dbfs),
        "speech" => engine.play_speech_noise(params.duration, params.level_dbfs),
        "narrowband" => {
            let center = params.center_hz.unwrap_or(1000.0);
            let bw = params.bandwidth_hz.unwrap_or(160.0);
            engine.play_nbn(center, bw, params.duration, params.level_dbfs)
        }
        _ => Err(format!("Tipo de ruido desconocido: {}", params.noise_type)),
    }
}

#[tauri::command]
pub fn stop_playback(audio: State<AudioState>) -> Result<(), String> {
    let guard = audio.engine.lock().unwrap();
    if let Some(engine) = guard.as_ref() {
        engine.stop();
    }
    Ok(())
}
