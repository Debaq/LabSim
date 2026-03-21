use piper_rs::synth::PiperSpeechSynthesizer;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

pub struct TtsEngine {
    synth: Option<PiperSpeechSynthesizer>,
    model_path: Option<PathBuf>,
    sample_rate: u32,
}

unsafe impl Send for TtsEngine {}

impl TtsEngine {
    pub fn new() -> Self {
        Self {
            synth: None,
            model_path: None,
            sample_rate: 22050,
        }
    }

    pub fn load_model(&mut self, config_path: &str) -> Result<(), String> {
        let path = std::path::Path::new(config_path);
        let model = piper_rs::from_config_path(path)
            .map_err(|e| format!("Error cargando modelo Piper: {}", e))?;

        // Read sample rate from config JSON
        if let Ok(json_str) = std::fs::read_to_string(config_path) {
            if let Ok(json) = serde_json::from_str::<serde_json::Value>(&json_str) {
                if let Some(sr) = json["audio"]["sample_rate"].as_u64() {
                    self.sample_rate = sr as u32;
                }
            }
        }

        let synth = PiperSpeechSynthesizer::new(model)
            .map_err(|e| format!("Error creando sintetizador: {}", e))?;

        self.synth = Some(synth);
        self.model_path = Some(PathBuf::from(config_path));
        log::info!("Piper TTS cargado: {} ({}Hz)", config_path, self.sample_rate);
        Ok(())
    }

    pub fn is_loaded(&self) -> bool {
        self.synth.is_some()
    }

    pub fn sample_rate(&self) -> u32 {
        self.sample_rate
    }

    pub fn synthesize(&self, text: &str) -> Result<Vec<f32>, String> {
        let synth = self.synth.as_ref().ok_or("Modelo TTS no cargado")?;

        let audio_result = synth.synthesize_parallel(text.to_string(), None)
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

        Ok(samples)
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
