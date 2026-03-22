# LabSim — Simulador Clínico Educativo

<p align="center">
  <strong>Plataforma de simulación de equipamiento clínico para la formación de profesionales de la salud</strong>
</p>

<p align="center">
  <code>Tauri 2 · React · Rust · TypeScript</code>
</p>

---

## Qué es LabSim

LabSim simula el día completo de un profesional en un centro clínico. El estudiante opera equipos realistas con las mismas perillas, joystick y flujos que encontrará en la práctica real: posicionar al paciente, ajustar mentonera, alinear el equipo, y ejecutar la prueba.

Los pacientes tienen personalidad, voz, historia clínica y memoria de atenciones anteriores. Los docentes diseñan la actividad configurando casos, artefactos y situaciones pedagógicas. Una secretaria virtual (Karime) gestiona la agenda y avisa sobre atrasos y pacientes en espera.

## Especialidades

- **Audiología** — Audiómetro, Impedanciómetro, Logoaudiometría, OAE, ABR, Audífonos
- **Otoneurología** — VNG, vHIT, Electrococleografía
- **Oftalmología** — OCT, Campímetro, Retinógrafo, Topógrafo Corneal, Scheimpflug, Autorefractómetro

## Documentación

La documentación completa está en la [Wiki del proyecto](https://github.com/Debaq/LabSim/wiki).

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | React 19, TypeScript, Tailwind CSS 4, Zustand |
| Desktop | Tauri 2, Rust |
| IA | llama.cpp (LLM local), Whisper (STT), Piper (TTS) |
| Servidor | PHP 8.1, SQLite, JWT |

## Autor

**Nicolás Baier Quezada**

---

<p align="center">
  <sub>LabSim nació para resolver un problema real: los estudiantes de salud no tienen acceso a los equipos que necesitan aprender a usar.</sub>
</p>
