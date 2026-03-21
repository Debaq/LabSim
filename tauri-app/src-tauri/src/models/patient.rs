use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PatientSummary {
    pub id: String,
    pub name: String,
    pub age: i32,
    pub created_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PatientProfile {
    pub id: String,
    pub metadata: serde_json::Value,
    pub modules: serde_json::Value,
}
