use whisper_rs::{FullParams, SamplingStrategy, WhisperContext, WhisperContextParameters};
use std::sync::{Arc, Mutex};
use std::path::PathBuf;

pub struct SpeechEngine {
    ctx: Option<WhisperContext>,
    model_path: Option<PathBuf>,
}

unsafe impl Send for SpeechEngine {}

impl SpeechEngine {
    pub fn new() -> Self {
        Self { ctx: None, model_path: None }
    }

    pub fn load_model(&mut self, path: &str) -> Result<(), String> {
        let params = WhisperContextParameters::default();
        let ctx = WhisperContext::new_with_params(path, params)
            .map_err(|e| format!("Error cargando Whisper: {}", e))?;
        self.ctx = Some(ctx);
        self.model_path = Some(PathBuf::from(path));
        log::info!("Whisper cargado: {}", path);
        Ok(())
    }

    pub fn is_loaded(&self) -> bool {
        self.ctx.is_some()
    }

    pub fn transcribe(&self, samples: &[f32], language: &str) -> Result<String, String> {
        let ctx = self.ctx.as_ref().ok_or("Modelo Whisper no cargado")?;

        let mut state = ctx.create_state()
            .map_err(|e| format!("Error estado: {}", e))?;

        let mut params = FullParams::new(SamplingStrategy::Greedy { best_of: 1 });
        params.set_language(Some(language));
        params.set_print_special(false);
        params.set_print_progress(false);
        params.set_print_realtime(false);
        params.set_print_timestamps(false);
        params.set_single_segment(true);
        params.set_no_timestamps(true);

        state.full(params, samples)
            .map_err(|e| format!("Error transcribiendo: {}", e))?;

        let n = state.full_n_segments();
        let mut text = String::new();
        for i in 0..n {
            if let Some(seg) = state.get_segment(i) {
                if let Ok(s) = seg.to_str() {
                    text.push_str(s.trim());
                    text.push(' ');
                }
            }
        }

        Ok(text.trim().to_string())
    }
}

pub struct SpeechState {
    pub engine: Arc<Mutex<SpeechEngine>>,
}

impl SpeechState {
    pub fn new() -> Self {
        Self { engine: Arc::new(Mutex::new(SpeechEngine::new())) }
    }
}
