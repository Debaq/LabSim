use piper_rs::synth::PiperSpeechSynthesizer;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

struct LoadedVoice {
    synth: PiperSpeechSynthesizer,
    sample_rate: u32,
    label: String,
}

pub struct TtsEngine {
    voices: HashMap<String, LoadedVoice>,
    /// Voz activa por defecto (la última cargada, o la seleccionada)
    default_voice: Option<String>,
}

unsafe impl Send for TtsEngine {}

impl TtsEngine {
    pub fn new() -> Self {
        Self {
            voices: HashMap::new(),
            default_voice: None,
        }
    }

    /// Carga un modelo y lo registra con un voice_id (ej: "male", "female")
    pub fn load_model(&mut self, voice_id: &str, label: &str, config_path: &str) -> Result<(), String> {
        let path = std::path::Path::new(config_path);
        let model = piper_rs::from_config_path(path)
            .map_err(|e| format!("Error cargando modelo Piper: {}", e))?;

        let mut sample_rate = 22050u32;
        if let Ok(json_str) = std::fs::read_to_string(config_path) {
            if let Ok(json) = serde_json::from_str::<serde_json::Value>(&json_str) {
                if let Some(sr) = json["audio"]["sample_rate"].as_u64() {
                    sample_rate = sr as u32;
                }
            }
        }

        let synth = PiperSpeechSynthesizer::new(model)
            .map_err(|e| format!("Error creando sintetizador: {}", e))?;

        log::info!("Piper TTS cargado [{}]: {} ({}Hz)", voice_id, config_path, sample_rate);

        self.voices.insert(voice_id.to_string(), LoadedVoice {
            synth,
            sample_rate,
            label: label.to_string(),
        });

        // Si no hay voz por defecto, usar esta
        if self.default_voice.is_none() {
            self.default_voice = Some(voice_id.to_string());
        }

        Ok(())
    }

    pub fn is_loaded(&self) -> bool {
        !self.voices.is_empty()
    }

    pub fn loaded_voices(&self) -> Vec<(String, String)> {
        self.voices.iter().map(|(id, v)| (id.clone(), v.label.clone())).collect()
    }

    /// Sintetiza con la voz por defecto
    pub fn synthesize(&self, text: &str) -> Result<(Vec<f32>, u32), String> {
        let voice_id = self.default_voice.as_ref().ok_or("No hay voz cargada")?;
        self.synthesize_with(voice_id, text)
    }

    /// Sintetiza con una voz específica
    pub fn synthesize_with(&self, voice_id: &str, text: &str) -> Result<(Vec<f32>, u32), String> {
        let voice = self.voices.get(voice_id)
            .ok_or_else(|| format!("Voz '{}' no cargada", voice_id))?;

        let audio_result = voice.synth.synthesize_parallel(text.to_string(), None)
            .map_err(|e| format!("Error sintetizando: {}", e))?;

        let samples: Vec<f32> = audio_result
            .flat_map(|r| match r {
                Ok(audio) => audio.into_vec().into_iter().collect::<Vec<_>>(),
                Err(_) => vec![],
            })
            .collect();

        if samples.is_empty() {
            return Err("No se generó audio".to_string());
        }

        Ok((samples, voice.sample_rate))
    }
}

pub struct TtsState {
    pub engine: Arc<Mutex<TtsEngine>>,
}

impl TtsState {
    pub fn new() -> Self {
        Self {
            engine: Arc::new(Mutex::new(TtsEngine::new())),
        }
    }
}
