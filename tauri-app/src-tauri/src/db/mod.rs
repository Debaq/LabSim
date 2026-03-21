pub mod schema;

use rusqlite::Connection;
use std::sync::Mutex;
use crate::models::patient::{PatientSummary, PatientProfile};

pub struct Database {
    conn: Mutex<Connection>,
}

impl Database {
    pub fn new() -> Result<Self, rusqlite::Error> {
        let conn = Connection::open("labsim.db")?;
        let db = Self {
            conn: Mutex::new(conn),
        };
        db.run_migrations()?;
        db.seed_default_user()?;
        Ok(db)
    }

    fn run_migrations(&self) -> Result<(), rusqlite::Error> {
        let conn = self.conn.lock().unwrap();
        conn.execute_batch(schema::MIGRATIONS)?;
        Ok(())
    }

    fn seed_default_user(&self) -> Result<(), rusqlite::Error> {
        let conn = self.conn.lock().unwrap();
        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM users",
            [],
            |row| row.get(0),
        )?;
        if count == 0 {
            let hash = bcrypt::hash("labsim2025", 8).unwrap();
            conn.execute(
                "INSERT INTO users (id, username, password_hash, role) VALUES (?1, ?2, ?3, ?4)",
                rusqlite::params![
                    uuid::Uuid::new_v4().to_string(),
                    "admin",
                    hash,
                    "admin"
                ],
            )?;
        }
        Ok(())
    }

    pub fn verify_credentials(&self, username: &str, password: &str) -> Result<bool, rusqlite::Error> {
        let conn = self.conn.lock().unwrap();
        let hash: Result<String, _> = conn.query_row(
            "SELECT password_hash FROM users WHERE username = ?1",
            [username],
            |row| row.get(0),
        );
        match hash {
            Ok(h) => Ok(bcrypt::verify(password, &h).unwrap_or(false)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(false),
            Err(e) => Err(e),
        }
    }

    pub fn get_user_role(&self, username: &str) -> Result<String, rusqlite::Error> {
        let conn = self.conn.lock().unwrap();
        conn.query_row(
            "SELECT role FROM users WHERE username = ?1",
            [username],
            |row| row.get(0),
        )
    }

    pub fn list_patients(&self) -> Result<Vec<PatientSummary>, rusqlite::Error> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, name, age, created_at FROM patients ORDER BY created_at DESC"
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(PatientSummary {
                id: row.get(0)?,
                name: row.get(1)?,
                age: row.get(2)?,
                created_at: row.get(3)?,
            })
        })?;
        rows.collect()
    }

    pub fn get_patient(&self, id: &str) -> Result<PatientProfile, rusqlite::Error> {
        let conn = self.conn.lock().unwrap();
        conn.query_row(
            "SELECT p.id, p.name, p.age, p.gender, pp.profile_json
             FROM patients p
             LEFT JOIN patient_profiles pp ON pp.patient_id = p.id
             WHERE p.id = ?1",
            [id],
            |row| {
                let profile_json: Option<String> = row.get(4)?;
                let modules = profile_json
                    .and_then(|j| serde_json::from_str(&j).ok())
                    .unwrap_or_default();
                Ok(PatientProfile {
                    id: row.get(0)?,
                    metadata: serde_json::json!({
                        "name": row.get::<_, String>(1)?,
                        "age": row.get::<_, i32>(2)?,
                        "gender": row.get::<_, Option<String>>(3)?,
                    }),
                    modules,
                })
            },
        )
    }

    pub fn save_patient(&self, data: &PatientProfile) -> Result<String, rusqlite::Error> {
        let conn = self.conn.lock().unwrap();
        let id = if data.id.is_empty() {
            uuid::Uuid::new_v4().to_string()
        } else {
            data.id.clone()
        };

        let name = data.metadata.get("name")
            .and_then(|v| v.as_str())
            .unwrap_or("Sin nombre");
        let age = data.metadata.get("age")
            .and_then(|v| v.as_i64())
            .unwrap_or(0) as i32;
        let gender = data.metadata.get("gender")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string());

        conn.execute(
            "INSERT OR REPLACE INTO patients (id, name, age, gender) VALUES (?1, ?2, ?3, ?4)",
            rusqlite::params![id, name, age, gender],
        )?;

        let modules_json = serde_json::to_string(&data.modules).unwrap_or_default();
        conn.execute(
            "INSERT OR REPLACE INTO patient_profiles (id, patient_id, profile_json, schema_version)
             VALUES (?1, ?2, ?3, 1)",
            rusqlite::params![
                uuid::Uuid::new_v4().to_string(),
                id,
                modules_json
            ],
        )?;

        Ok(id)
    }

    pub fn delete_patient(&self, id: &str) -> Result<(), rusqlite::Error> {
        let conn = self.conn.lock().unwrap();
        conn.execute("DELETE FROM patient_profiles WHERE patient_id = ?1", [id])?;
        conn.execute("DELETE FROM patients WHERE id = ?1", [id])?;
        Ok(())
    }
}
