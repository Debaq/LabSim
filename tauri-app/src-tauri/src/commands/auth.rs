use serde::Serialize;
use tauri::State;
use crate::db::Database;

#[derive(Serialize)]
pub struct LoginResult {
    pub success: bool,
    pub role: String,
}

#[tauri::command]
pub fn login(db: State<Database>, username: String, password: String) -> Result<LoginResult, String> {
    let result = db.verify_credentials(&username, &password)
        .map_err(|e| e.to_string())?;

    if result {
        let role = db.get_user_role(&username).unwrap_or("estudiante".to_string());
        Ok(LoginResult { success: true, role })
    } else {
        Ok(LoginResult { success: false, role: String::new() })
    }
}
