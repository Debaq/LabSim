pub mod personas;
pub mod patient_persona;

use llama_cpp_2::context::params::LlamaContextParams;
use llama_cpp_2::llama_backend::LlamaBackend;
use llama_cpp_2::llama_batch::LlamaBatch;
use llama_cpp_2::model::params::LlamaModelParams;
use llama_cpp_2::model::{AddBos, LlamaModel};
use llama_cpp_2::sampling::LlamaSampler;
use std::num::NonZeroU32;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

pub struct LlmEngine {
    backend: LlamaBackend,
    model: Option<LlamaModel>,
    model_path: Option<PathBuf>,
}

unsafe impl Send for LlmEngine {}

impl LlmEngine {
    pub fn new() -> Self {
        let backend = LlamaBackend::init().expect("Failed to init llama backend");
        Self {
            backend,
            model: None,
            model_path: None,
        }
    }

    pub fn load_model(&mut self, path: &str) -> Result<(), String> {
        let model_params = LlamaModelParams::default();
        let model = LlamaModel::load_from_file(&self.backend, path, &model_params)
            .map_err(|e| format!("Error cargando modelo: {}", e))?;
        self.model = Some(model);
        self.model_path = Some(PathBuf::from(path));
        log::info!("Modelo cargado: {}", path);
        Ok(())
    }

    pub fn is_loaded(&self) -> bool {
        self.model.is_some()
    }

    pub fn generate(&self, prompt: &str, max_tokens: u32, temperature: f32) -> Result<String, String> {
        let model = self.model.as_ref().ok_or("Modelo no cargado")?;

        let ctx_params = LlamaContextParams::default()
            .with_n_ctx(NonZeroU32::new(2048));

        let mut ctx = model.new_context(&self.backend, ctx_params)
            .map_err(|e| format!("Error creando contexto: {}", e))?;

        // Tokenize
        let tokens = model.str_to_token(prompt, AddBos::Always)
            .map_err(|e| format!("Error tokenizando: {}", e))?;

        let mut batch = LlamaBatch::new(2048, 1);
        let last_idx = (tokens.len() - 1) as i32;

        for (i, token) in tokens.iter().enumerate() {
            batch.add(*token, i as i32, &[0], i as i32 == last_idx)
                .map_err(|e| format!("Error en batch: {}", e))?;
        }

        // Decode prompt
        ctx.decode(&mut batch)
            .map_err(|e| format!("Error decode prompt: {}", e))?;

        // Setup sampler chain: temperature + top-p + dist
        let mut sampler = LlamaSampler::chain_simple([
            LlamaSampler::temp(temperature),
            LlamaSampler::top_p(0.9, 1),
            LlamaSampler::dist(42),
        ]);

        let mut output = String::new();
        let mut n_cur = tokens.len() as i32;

        for _ in 0..max_tokens {
            let new_token = sampler.sample(&ctx, batch.n_tokens() - 1);
            sampler.accept(new_token);

            // Check EOS
            if model.is_eog_token(new_token) {
                break;
            }

            let bytes = model.token_to_piece_bytes(new_token, 64, true, None)
                .map_err(|e| format!("Error decodificando token: {}", e))?;
            let piece = String::from_utf8_lossy(&bytes);
            output.push_str(&piece);

            // Next batch
            batch.clear();
            batch.add(new_token, n_cur, &[0], true)
                .map_err(|e| format!("Error batch: {}", e))?;

            ctx.decode(&mut batch)
                .map_err(|e| format!("Error decode: {}", e))?;

            n_cur += 1;
        }

        // Strip <think>...</think> blocks (Qwen3 thinking mode)
        let cleaned = output.trim().to_string();
        // Remove all <think>...</think> blocks
        let mut result = cleaned.clone();
        while let (Some(start), Some(end)) = (result.find("<think>"), result.find("</think>")) {
            if end > start {
                result = format!("{}{}", &result[..start], &result[end + 8..]);
            } else {
                break;
            }
        }
        // If still starts with <think> (unclosed), take everything after it
        if result.trim().starts_with("<think>") {
            result = result.trim().replacen("<think>", "", 1);
        }
        let result = result.trim().to_string();

        // If empty after stripping, return the original without tags
        if result.is_empty() {
            Ok(cleaned.replace("<think>", "").replace("</think>", "").trim().to_string())
        } else {
            Ok(result)
        }
    }
}

pub struct LlmState {
    pub engine: Arc<Mutex<LlmEngine>>,
}

impl LlmState {
    pub fn new() -> Self {
        Self {
            engine: Arc::new(Mutex::new(LlmEngine::new())),
        }
    }
}
