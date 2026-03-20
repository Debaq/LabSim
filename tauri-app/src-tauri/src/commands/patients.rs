use tauri::State;
use crate::db::Database;
use crate::models::patient::{PatientSummary, PatientProfile};

#[tauri::command]
pub fn list_patients(db: State<Database>) -> Result<Vec<PatientSummary>, String> {
    db.list_patients().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_patient(db: State<Database>, id: String) -> Result<PatientProfile, String> {
    db.get_patient(&id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn save_patient(db: State<Database>, data: PatientProfile) -> Result<String, String> {
    db.save_patient(&data).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn delete_patient(db: State<Database>, id: String) -> Result<(), String> {
    db.delete_patient(&id).map_err(|e| e.to_string())
}
