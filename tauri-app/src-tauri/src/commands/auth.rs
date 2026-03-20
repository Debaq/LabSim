use tauri::State;
use crate::db::Database;

#[tauri::command]
pub fn login(db: State<Database>, username: String, password: String) -> Result<bool, String> {
    db.verify_credentials(&username, &password)
        .map_err(|e| e.to_string())
}
