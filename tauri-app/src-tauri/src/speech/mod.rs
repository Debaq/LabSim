use base64::Engine as _;
use std::io::{BufRead, BufReader, Write};
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};

/// Client that communicates with the labsim-speech sidecar process via JSON lines.
struct SidecarProcess {
    child: Child,
    reader: BufReader<std::process::ChildStdout>,
}

impl SidecarProcess {
    fn send(&mut self, request: serde_json::Value) -> Result<serde_json::Value, String> {
        let stdin = self.child.stdin.as_mut()
            .ok_or("Sidecar stdin no disponible")?;

        let line = serde_json::to_string(&request)
            .map_err(|e| format!("Error serializando: {}", e))?;

        writeln!(stdin, "{}", line)
            .map_err(|e| format!("Error escribiendo a sidecar: {}", e))?;
        stdin.flush()
            .map_err(|e| format!("Error flush: {}", e))?;

        let mut response_line = String::new();
        self.reader.read_line(&mut response_line)
            .map_err(|e| format!("Error leyendo de sidecar: {}", e))?;

        if response_line.is_empty() {
            return Err("Sidecar cerró la conexión".into());
        }

        let resp: serde_json::Value = serde_json::from_str(&response_line)
            .map_err(|e| format!("Respuesta inválida del sidecar: {}", e))?;

        if resp.get("ok").and_then(|v| v.as_bool()) == Some(true) {
            Ok(resp)
        } else {
            let err = resp.get("error")
                .and_then(|v| v.as_str())
                .unwrap_or("Error desconocido del sidecar");
            Err(err.to_string())
        }
    }
}

impl Drop for SidecarProcess {
    fn drop(&mut self) {
        let _ = self.child.kill();
    }
}

pub struct SpeechEngine {
    process: Option<SidecarProcess>,
    model_loaded: bool,
    sidecar_path: String,
}

impl SpeechEngine {
    pub fn new(sidecar_path: String) -> Self {
        Self {
            process: None,
            model_loaded: false,
            sidecar_path,
        }
    }

    fn ensure_process(&mut self) -> Result<(), String> {
        if self.process.is_some() {
            return Ok(());
        }

        let mut child = Command::new(&self.sidecar_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
            .map_err(|e| format!("Error lanzando sidecar Speech ({}): {}", self.sidecar_path, e))?;

        let stdout = child.stdout.take()
            .ok_or("No se pudo obtener stdout del sidecar")?;

        self.process = Some(SidecarProcess {
            child,
            reader: BufReader::new(stdout),
        });

        log::info!("Sidecar Speech iniciado: {}", self.sidecar_path);
        Ok(())
    }

    fn send(&mut self, request: serde_json::Value) -> Result<serde_json::Value, String> {
        self.ensure_process()?;
        self.process.as_mut().unwrap().send(request)
    }

    pub fn is_loaded(&self) -> bool {
        self.model_loaded
    }

    pub fn load_model(&mut self) -> Result<(), String> {
        self.send(serde_json::json!({"cmd": "load"}))?;
        self.model_loaded = true;
        Ok(())
    }

    pub fn transcribe(&mut self, samples: &[f32], language: &str) -> Result<String, String> {
        // Encode f32 samples as base64 little-endian bytes
        let bytes: Vec<u8> = samples.iter()
            .flat_map(|s| s.to_le_bytes())
            .collect();
        let b64 = base64::engine::general_purpose::STANDARD.encode(&bytes);

        let resp = self.send(serde_json::json!({
            "cmd": "transcribe",
            "samples_b64": b64,
            "language": language,
        }))?;

        resp.get("data")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string())
            .ok_or("Respuesta sin texto".into())
    }
}

pub struct SpeechState {
    pub engine: Arc<Mutex<SpeechEngine>>,
}

impl SpeechState {
    pub fn new(sidecar_path: String) -> Self {
        Self {
            engine: Arc::new(Mutex::new(SpeechEngine::new(sidecar_path))),
        }
    }
}
