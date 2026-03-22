use llama_cpp_2::context::params::LlamaContextParams;
use llama_cpp_2::llama_backend::LlamaBackend;
use llama_cpp_2::llama_batch::LlamaBatch;
use llama_cpp_2::model::params::LlamaModelParams;
use llama_cpp_2::model::{AddBos, LlamaModel};
use llama_cpp_2::sampling::LlamaSampler;
use serde::{Deserialize, Serialize};
use std::io::{self, BufRead, Write};
use std::num::NonZeroU32;

// ── Protocol types ──────────────────────────────────────

#[derive(Deserialize)]
#[serde(tag = "cmd", rename_all = "snake_case")]
enum Request {
    Status,
    ListModels,
    Download { model_id: String, filename: String },
    Load { path: String },
    Generate { prompt: String, max_tokens: u32, temperature: f32 },
}

#[derive(Serialize)]
struct Response {
    ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    data: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

impl Response {
    fn success(data: serde_json::Value) -> Self {
        Self { ok: true, data: Some(data), error: None }
    }
    fn ok() -> Self {
        Self { ok: true, data: None, error: None }
    }
    fn err(msg: String) -> Self {
        Self { ok: false, data: None, error: Some(msg) }
    }
}

// ── Model catalog ───────────────────────────────────────

const AVAILABLE_MODELS: &[(&str, &str, &str, u32)] = &[
    ("Qwen/Qwen3-0.6B-GGUF", "Qwen3 0.6B (Recomendado)", "Qwen3-0.6B-Q8_0.gguf", 610),
    ("Qwen/Qwen2.5-1.5B-Instruct-GGUF", "Qwen2.5 1.5B", "qwen2.5-1.5b-instruct-q4_k_m.gguf", 1065),
    ("Qwen/Qwen3-1.7B-GGUF", "Qwen3 1.7B (Mejor calidad)", "Qwen3-1.7B-Q8_0.gguf", 1750),
];

// ── Engine ──────────────────────────────────────────────

struct LlmEngine {
    backend: LlamaBackend,
    model: Option<LlamaModel>,
}

unsafe impl Send for LlmEngine {}

impl LlmEngine {
    fn new() -> Self {
        let backend = LlamaBackend::init().expect("Failed to init llama backend");
        Self { backend, model: None }
    }

    fn load_model(&mut self, path: &str) -> Result<(), String> {
        let params = LlamaModelParams::default();
        let model = LlamaModel::load_from_file(&self.backend, path, &params)
            .map_err(|e| format!("Error cargando modelo: {}", e))?;
        self.model = Some(model);
        Ok(())
    }

    fn generate(&self, prompt: &str, max_tokens: u32, temperature: f32) -> Result<String, String> {
        let model = self.model.as_ref().ok_or("Modelo no cargado")?;

        let ctx_params = LlamaContextParams::default()
            .with_n_ctx(NonZeroU32::new(2048));

        let mut ctx = model.new_context(&self.backend, ctx_params)
            .map_err(|e| format!("Error creando contexto: {}", e))?;

        let tokens = model.str_to_token(prompt, AddBos::Always)
            .map_err(|e| format!("Error tokenizando: {}", e))?;

        let mut batch = LlamaBatch::new(2048, 1);
        let last_idx = (tokens.len() - 1) as i32;

        for (i, token) in tokens.iter().enumerate() {
            batch.add(*token, i as i32, &[0], i as i32 == last_idx)
                .map_err(|e| format!("Error en batch: {}", e))?;
        }

        ctx.decode(&mut batch)
            .map_err(|e| format!("Error decode prompt: {}", e))?;

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

            if model.is_eog_token(new_token) {
                break;
            }

            let bytes = model.token_to_piece_bytes(new_token, 64, true, None)
                .map_err(|e| format!("Error decodificando token: {}", e))?;
            let piece = String::from_utf8_lossy(&bytes);
            output.push_str(&piece);

            batch.clear();
            batch.add(new_token, n_cur, &[0], true)
                .map_err(|e| format!("Error batch: {}", e))?;

            ctx.decode(&mut batch)
                .map_err(|e| format!("Error decode: {}", e))?;

            n_cur += 1;
        }

        // Strip <think>...</think> blocks (Qwen3 thinking mode)
        let cleaned = output.trim().to_string();
        let mut result = cleaned.clone();
        while let (Some(start), Some(end)) = (result.find("<think>"), result.find("</think>")) {
            if end > start {
                result = format!("{}{}", &result[..start], &result[end + 8..]);
            } else {
                break;
            }
        }
        if result.trim().starts_with("<think>") {
            result = result.trim().replacen("<think>", "", 1);
        }
        let result = result.trim().to_string();

        if result.is_empty() {
            Ok(cleaned.replace("<think>", "").replace("</think>", "").trim().to_string())
        } else {
            Ok(result)
        }
    }
}

// ── Main loop ───────────────────────────────────────────

fn main() {
    env_logger::init();

    let mut engine = LlmEngine::new();
    let stdin = io::stdin();
    let mut stdout = io::stdout();

    for line in stdin.lock().lines() {
        let line = match line {
            Ok(l) => l,
            Err(_) => break,
        };

        if line.trim().is_empty() {
            continue;
        }

        let response = match serde_json::from_str::<Request>(&line) {
            Ok(req) => handle_request(&mut engine, req),
            Err(e) => Response::err(format!("JSON inválido: {}", e)),
        };

        let json = serde_json::to_string(&response).unwrap();
        let _ = writeln!(stdout, "{}", json);
        let _ = stdout.flush();
    }
}

fn handle_request(engine: &mut LlmEngine, req: Request) -> Response {
    match req {
        Request::Status => {
            Response::success(serde_json::json!(engine.model.is_some()))
        }

        Request::ListModels => {
            let models: Vec<serde_json::Value> = AVAILABLE_MODELS.iter()
                .map(|(id, name, filename, size_mb)| serde_json::json!({
                    "id": id,
                    "name": name,
                    "filename": filename,
                    "sizeMb": size_mb,
                }))
                .collect();
            Response::success(serde_json::json!(models))
        }

        Request::Download { model_id, filename } => {
            match download_model(&model_id, &filename) {
                Ok(path) => Response::success(serde_json::json!(path)),
                Err(e) => Response::err(e),
            }
        }

        Request::Load { path } => {
            match engine.load_model(&path) {
                Ok(()) => Response::ok(),
                Err(e) => Response::err(e),
            }
        }

        Request::Generate { prompt, max_tokens, temperature } => {
            match engine.generate(&prompt, max_tokens, temperature) {
                Ok(text) => Response::success(serde_json::json!(text)),
                Err(e) => Response::err(e),
            }
        }
    }
}

fn download_model(model_id: &str, filename: &str) -> Result<String, String> {
    let api = hf_hub::api::sync::ApiBuilder::new()
        .with_progress(false)
        .build()
        .map_err(|e| format!("Error API HF: {}", e))?;

    let repo = api.model(model_id.to_string());
    let path = repo.get(filename)
        .map_err(|e| format!("Error descargando: {}", e))?;

    Ok(path.to_string_lossy().to_string())
}
