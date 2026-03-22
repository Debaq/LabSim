use base64::Engine as _;
use serde::{Deserialize, Serialize};
use std::io::{self, BufRead, Write};
use whisper_rs::{FullParams, SamplingStrategy, WhisperContext, WhisperContextParameters};

// ── Protocol types ──────────────────────────────────────

#[derive(Deserialize)]
#[serde(tag = "cmd", rename_all = "snake_case")]
enum Request {
    Status,
    Load,
    Transcribe {
        /// Base64-encoded little-endian f32 samples at 16kHz
        samples_b64: String,
        language: String,
    },
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

// ── Engine ──────────────────────────────────────────────

struct SpeechEngine {
    ctx: Option<WhisperContext>,
}

unsafe impl Send for SpeechEngine {}

impl SpeechEngine {
    fn new() -> Self {
        Self { ctx: None }
    }

    fn load_model(&mut self, path: &str) -> Result<(), String> {
        let params = WhisperContextParameters::default();
        let ctx = WhisperContext::new_with_params(path, params)
            .map_err(|e| format!("Error cargando Whisper: {}", e))?;
        self.ctx = Some(ctx);
        Ok(())
    }

    fn transcribe(&self, samples: &[f32], language: &str) -> Result<String, String> {
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

// ── Helpers ─────────────────────────────────────────────

fn decode_samples(b64: &str) -> Result<Vec<f32>, String> {
    let bytes = base64::engine::general_purpose::STANDARD
        .decode(b64)
        .map_err(|e| format!("Error decodificando base64: {}", e))?;

    if bytes.len() % 4 != 0 {
        return Err("Bytes no alineados a f32 (múltiplo de 4)".into());
    }

    let samples: Vec<f32> = bytes
        .chunks_exact(4)
        .map(|chunk| f32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
        .collect();

    Ok(samples)
}

fn download_whisper_tiny() -> Result<String, String> {
    let api = hf_hub::api::sync::ApiBuilder::new()
        .with_progress(false)
        .build()
        .map_err(|e| format!("Error API HF: {}", e))?;

    let repo = api.model("ggerganov/whisper.cpp".to_string());
    let path = repo.get("ggml-tiny.bin")
        .map_err(|e| format!("Error descargando whisper: {}", e))?;

    Ok(path.to_string_lossy().to_string())
}

// ── Main loop ───────────────────────────────────────────

fn main() {
    env_logger::init();

    let mut engine = SpeechEngine::new();
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

fn handle_request(engine: &mut SpeechEngine, req: Request) -> Response {
    match req {
        Request::Status => {
            Response::success(serde_json::json!(engine.ctx.is_some()))
        }

        Request::Load => {
            match download_whisper_tiny() {
                Ok(path) => match engine.load_model(&path) {
                    Ok(()) => Response::ok(),
                    Err(e) => Response::err(e),
                },
                Err(e) => Response::err(e),
            }
        }

        Request::Transcribe { samples_b64, language } => {
            match decode_samples(&samples_b64) {
                Ok(samples) => match engine.transcribe(&samples, &language) {
                    Ok(text) => Response::success(serde_json::json!(text)),
                    Err(e) => Response::err(e),
                },
                Err(e) => Response::err(e),
            }
        }
    }
}
