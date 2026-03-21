use reqwest::{Client, header};
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use std::time::Duration;

const BASE_URL: &str = "https://tmeduca.org/labsim/backend/api/index.php?route=";
const TIMEOUT_SECS: u64 = 30;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenPair {
    pub access_token: String,
    pub refresh_token: String,
}

pub struct ApiClient {
    client: Client,
    tokens: Mutex<Option<TokenPair>>,
    base_url: Mutex<String>,
}

impl ApiClient {
    pub fn new() -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(TIMEOUT_SECS))
            .build()
            .expect("Error creando HTTP client");

        Self {
            client,
            tokens: Mutex::new(None),
            base_url: Mutex::new(BASE_URL.to_string()),
        }
    }

    pub fn set_tokens(&self, tokens: TokenPair) {
        *self.tokens.lock().unwrap() = Some(tokens);
    }

    pub fn clear_tokens(&self) {
        *self.tokens.lock().unwrap() = None;
    }

    pub fn get_access_token(&self) -> Option<String> {
        self.tokens.lock().unwrap().as_ref().map(|t| t.access_token.clone())
    }

    pub fn set_base_url(&self, url: &str) {
        *self.base_url.lock().unwrap() = url.to_string();
    }

    fn get_url(&self, route: &str) -> String {
        let base = self.base_url.lock().unwrap().clone();
        format!("{}{}", base, route)
    }

    /// GET request con JWT automático
    pub async fn get(&self, route: &str) -> Result<serde_json::Value, String> {
        let mut req = self.client.get(self.get_url(route));

        if let Some(token) = self.get_access_token() {
            req = req.header(header::AUTHORIZATION, format!("Bearer {}", token));
        }

        let resp = req.send().await.map_err(|e| format!("Error de red: {}", e))?;
        let status = resp.status();
        let body: serde_json::Value = resp.json().await.map_err(|e| format!("Error parseando respuesta: {}", e))?;

        if !status.is_success() {
            let msg = body.get("error").and_then(|e| e.as_str()).unwrap_or("Error desconocido");
            return Err(format!("{} ({})", msg, status.as_u16()));
        }

        Ok(body)
    }

    /// POST request con JWT automático
    pub async fn post(&self, route: &str, body: &serde_json::Value) -> Result<serde_json::Value, String> {
        let mut req = self.client.post(self.get_url(route))
            .json(body);

        if let Some(token) = self.get_access_token() {
            req = req.header(header::AUTHORIZATION, format!("Bearer {}", token));
        }

        let resp = req.send().await.map_err(|e| format!("Error de red: {}", e))?;
        let status = resp.status();
        let resp_body: serde_json::Value = resp.json().await.map_err(|e| format!("Error parseando respuesta: {}", e))?;

        if !status.is_success() {
            let msg = resp_body.get("error").and_then(|e| e.as_str()).unwrap_or("Error desconocido");
            return Err(format!("{} ({})", msg, status.as_u16()));
        }

        Ok(resp_body)
    }

    /// PUT request con JWT automático
    pub async fn put(&self, route: &str, body: &serde_json::Value) -> Result<serde_json::Value, String> {
        let mut req = self.client.put(self.get_url(route))
            .json(body);

        if let Some(token) = self.get_access_token() {
            req = req.header(header::AUTHORIZATION, format!("Bearer {}", token));
        }

        let resp = req.send().await.map_err(|e| format!("Error de red: {}", e))?;
        let status = resp.status();
        let resp_body: serde_json::Value = resp.json().await.map_err(|e| format!("Error parseando respuesta: {}", e))?;

        if !status.is_success() {
            let msg = resp_body.get("error").and_then(|e| e.as_str()).unwrap_or("Error desconocido");
            return Err(format!("{} ({})", msg, status.as_u16()));
        }

        Ok(resp_body)
    }

    /// DELETE request con JWT automático
    pub async fn delete(&self, route: &str) -> Result<serde_json::Value, String> {
        let mut req = self.client.delete(self.get_url(route));

        if let Some(token) = self.get_access_token() {
            req = req.header(header::AUTHORIZATION, format!("Bearer {}", token));
        }

        let resp = req.send().await.map_err(|e| format!("Error de red: {}", e))?;
        let status = resp.status();
        let resp_body: serde_json::Value = resp.json().await.map_err(|e| format!("Error parseando respuesta: {}", e))?;

        if !status.is_success() {
            let msg = resp_body.get("error").and_then(|e| e.as_str()).unwrap_or("Error desconocido");
            return Err(format!("{} ({})", msg, status.as_u16()));
        }

        Ok(resp_body)
    }

    /// Verificar conectividad con el servidor
    pub async fn ping(&self) -> bool {
        match self.client.get(self.get_url("")).timeout(Duration::from_secs(5)).send().await {
            Ok(resp) => resp.status().is_success(),
            Err(_) => false,
        }
    }
}
