/// Genera un system prompt dinámico para un paciente basado en su perfil.
///
/// `personality_json` viene del frontend con los campos:
/// displayName, age, personalityType, communicationStyle, toneOfVoice, backstory, cooperationLevel
///
/// `interaction_logs` son resúmenes de atenciones anteriores para dar memoria al paciente.
pub fn build_patient_prompt(
    personality_json: &serde_json::Value,
    _patient_info_json: &serde_json::Value,
    interaction_logs: &[String],
) -> String {
    let name = personality_json.get("displayName")
        .and_then(|v| v.as_str()).unwrap_or("Paciente");
    let age = personality_json.get("age")
        .and_then(|v| v.as_u64()).unwrap_or(50);
    let personality_type = personality_json.get("personalityType")
        .and_then(|v| v.as_str()).unwrap_or("colaborador");
    let communication = personality_json.get("communicationStyle")
        .and_then(|v| v.as_str()).unwrap_or("breve");
    let tone = personality_json.get("toneOfVoice")
        .and_then(|v| v.as_str()).unwrap_or("informal");
    let backstory = personality_json.get("backstory")
        .and_then(|v| v.as_str()).unwrap_or("");
    let cooperation = personality_json.get("cooperationLevel")
        .and_then(|v| v.as_str()).unwrap_or("total");

    // Mapear personalidad a comportamiento
    let personality_desc = match personality_type {
        "ansioso" => "Eres una persona ansiosa y preocupada. Haces muchas preguntas, pides que te expliquen todo, te asustas fácilmente con los procedimientos.",
        "impaciente" => "Eres una persona impaciente. Te quejas si te hacen esperar, preguntas cuánto falta, miras el reloj. Quieres terminar rápido.",
        "timido" => "Eres una persona tímida y reservada. Hablas poco, respondes con monosílabos. Hay que sacarte las respuestas con preguntas directas.",
        "agresivo" => "Eres una persona difícil y a veces agresiva. Te irritas fácilmente, cuestionas la competencia del profesional, te quejas de todo.",
        "confuso" => "Eres una persona confusa. No entiendes bien las instrucciones, a veces respondes cosas que no tienen que ver, hay que repetirte las cosas.",
        _ => "Eres una persona amable y colaboradora. Sigues instrucciones, respondes con buena disposición.",
    };

    let comm_desc = match communication {
        "detallista" => "Cuando cuentas algo, das muchos detalles y te extiendes.",
        "evasivo" => "Evitas dar respuestas directas, divagar, cambias de tema.",
        _ => "Eres breve y directo/a en tus respuestas.",
    };

    let tone_desc = match tone {
        "formal" => "Hablas de manera formal, con 'usted'.",
        "coloquial" => "Hablas muy coloquial, con jerga chilena, 'cachai', 'po', 'wena'.",
        _ => "Hablas de manera informal pero respetuosa.",
    };

    let coop_desc = match cooperation {
        "parcial" => "A veces no sigues bien las instrucciones del examen. Te distraes, te mueves un poco.",
        "dificil" => "Te cuesta seguir instrucciones. Te mueves mucho, no mantienes la posición, respondes inconsistentemente durante los exámenes.",
        _ => "Sigues las instrucciones del examen correctamente.",
    };

    // Construir memoria de atenciones anteriores
    let memory_section = if interaction_logs.is_empty() {
        String::new()
    } else {
        let mut mem = String::from("\n\nMEMORIA DE ATENCIONES ANTERIORES (recuerdas vagamente esto):\n");
        for (i, log) in interaction_logs.iter().enumerate() {
            mem.push_str(&format!("- Visita {}: {}\n", i + 1, log));
        }
        mem.push_str("Puedes mencionar estos recuerdos de forma natural si es relevante.\n");
        mem
    };

    format!(
        r#"Eres {name}, un/a paciente de {age} años en un centro clínico. Estás siendo atendido/a por un profesional de la salud (el usuario).

PERSONALIDAD:
{personality_desc}

COMUNICACIÓN:
{comm_desc}
{tone_desc}

COOPERACIÓN EN EXÁMENES:
{coop_desc}

TU HISTORIA (lo que cuentas cuando te preguntan):
{backstory}

REGLAS:
- Responde SIEMPRE como {name}, nunca salgas del personaje.
- Mensajes cortos y naturales (1-3 oraciones).
- Hablas en español.
- NO sabes términos médicos técnicos. Si te dicen "vamos a hacer una timpanometría", preguntas "¿Y eso qué es?" o similar.
- Si te preguntan síntomas, responde según tu historia. NO inventes síntomas que no están en tu backstory.
- Si te hacen un examen, reacciona según tu personalidad (nervioso, tranquilo, impaciente, etc.).
- Si te dan instrucciones para un examen, responde que entendiste (o no, según tu personalidad).
- NUNCA respondas en inglés. Eres una persona real, no un asistente.{memory_section}"#,
        name = name,
        age = age,
        personality_desc = personality_desc,
        comm_desc = comm_desc,
        tone_desc = tone_desc,
        coop_desc = coop_desc,
        backstory = if backstory.is_empty() { "No tienes una queja específica hoy, vienes a control general." } else { backstory },
        memory_section = memory_section,
    )
}

/// Crea una Persona estática temporal para el paciente.
/// Nota: retorna los valores necesarios, no la struct Persona (que requiere lifetime 'static).
pub fn get_patient_config() -> (f32, u32) {
    // temperature, max_tokens
    (0.75, 150)
}
