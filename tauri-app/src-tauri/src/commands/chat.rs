use serde::{Deserialize, Serialize};
use tauri::State;
use crate::llm::LlmState;
use crate::llm::personas;
use crate::llm::patient_persona;

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SendMessageRequest {
    pub persona_id: String,
    pub messages: Vec<ChatMessageDto>,
    /// Contexto del paciente (solo cuando personaId = "patient")
    pub patient_context: Option<PatientContext>,
}

#[derive(Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct PatientContext {
    pub personality: serde_json::Value,
    pub patient_info: serde_json::Value,
    pub interaction_logs: Vec<String>,
}

#[derive(Deserialize, Serialize, Clone)]
pub struct ChatMessageDto {
    pub role: String,
    pub content: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ModelInfo {
    pub id: String,
    pub name: String,
    pub size_mb: u32,
    pub filename: String,
}

pub const AVAILABLE_MODELS: &[(&str, &str, &str, u32)] = &[
    ("Qwen/Qwen3-0.6B-GGUF", "Qwen3 0.6B (Recomendado)", "Qwen3-0.6B-Q8_0.gguf", 610),
    ("Qwen/Qwen2.5-1.5B-Instruct-GGUF", "Qwen2.5 1.5B", "qwen2.5-1.5b-instruct-q4_k_m.gguf", 1065),
    ("Qwen/Qwen3-1.7B-GGUF", "Qwen3 1.7B (Mejor calidad)", "Qwen3-1.7B-Q8_0.gguf", 1750),
];

#[tauri::command]
pub fn llm_list_models() -> Vec<ModelInfo> {
    AVAILABLE_MODELS
        .iter()
        .map(|(id, name, filename, size_mb)| ModelInfo {
            id: id.to_string(),
            name: name.to_string(),
            size_mb: *size_mb,
            filename: filename.to_string(),
        })
        .collect()
}

#[tauri::command]
pub fn llm_status(llm: State<LlmState>) -> bool {
    let engine = llm.engine.lock().unwrap();
    engine.is_loaded()
}

#[tauri::command]
pub async fn llm_download_model(
    model_id: String,
    filename: String,
    app_handle: tauri::AppHandle,
) -> Result<String, String> {
    use tauri::Emitter;

    let fname = filename.clone();
    let mid = model_id.clone();

    let _ = app_handle.emit("llm-download-progress", serde_json::json!({
        "status": "downloading",
        "filename": fname,
        "progress": 0,
    }));

    // Run blocking download in a separate thread
    let handle = app_handle.clone();
    let path = tauri::async_runtime::spawn_blocking(move || {
        let api = hf_hub::api::sync::ApiBuilder::new()
            .with_progress(false)
            .build()
            .map_err(|e| format!("Error API HF: {}", e))?;

        let repo = api.model(mid.clone());
        log::info!("Descargando {} / {}", mid, fname);

        let path = repo.get(&fname)
            .map_err(|e| format!("Error descargando: {}", e))?;

        Ok::<String, String>(path.to_string_lossy().to_string())
    })
    .await
    .map_err(|e| format!("Error en hilo: {}", e))?
    ?;

    let _ = handle.emit("llm-download-progress", serde_json::json!({
        "status": "complete",
        "filename": filename,
        "progress": 100,
    }));

    Ok(path)
}

#[tauri::command]
pub async fn llm_load_model_async(
    llm: State<'_, LlmState>,
    path: String,
) -> Result<bool, String> {
    let engine = llm.engine.clone();
    tauri::async_runtime::spawn_blocking(move || {
        let mut eng = engine.lock().unwrap();
        eng.load_model(&path)
    })
    .await
    .map_err(|e| format!("Error en hilo: {}", e))?
    ?;
    Ok(true)
}

#[tauri::command]
pub async fn llm_chat(llm: State<'_, LlmState>, request: SendMessageRequest) -> Result<String, String> {
    let engine = llm.engine.clone();

    tauri::async_runtime::spawn_blocking(move || {
        let eng = engine.lock().unwrap();

        if !eng.is_loaded() {
            return Err("Modelo no cargado. Descargue uno primero.".to_string());
        }

        // Determinar system prompt, temperature y max_tokens
        let (system_prompt, temperature, max_tokens) = if request.persona_id == "patient" {
            // Paciente dinámico: generar prompt desde contexto
            let ctx = request.patient_context.as_ref()
                .ok_or("Se requiere patientContext para el paciente".to_string())?;
            let prompt = patient_persona::build_patient_prompt(
                &ctx.personality,
                &ctx.patient_info,
                &ctx.interaction_logs,
            );
            let (temp, tokens) = patient_persona::get_patient_config();
            (prompt, temp, tokens)
        } else {
            // Persona estática (Karime, Docente)
            let persona = personas::get_persona(&request.persona_id)
                .ok_or(format!("Persona '{}' no encontrada", request.persona_id))?;
            (persona.system_prompt.to_string(), persona.temperature, persona.max_tokens)
        };

        // Build chat prompt in ChatML format (used by Qwen)
        // /no_think disables Qwen3's thinking mode for faster, direct responses
        let mut prompt = format!("<|im_start|>system\n{}\n/no_think<|im_end|>\n", system_prompt);

        for msg in &request.messages {
            let role = match msg.role.as_str() {
                "user" => "user",
                "assistant" => "assistant",
                _ => "user",
            };
            prompt.push_str(&format!("<|im_start|>{}\n{}<|im_end|>\n", role, msg.content));
        }
        prompt.push_str("<|im_start|>assistant\n");

        eng.generate(&prompt, max_tokens, temperature)
    })
    .await
    .map_err(|e| format!("Error en hilo: {}", e))?
}
