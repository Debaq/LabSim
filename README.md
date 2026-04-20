# LabSim — Clinical Educational Simulator

<p align="center">
  <strong>Clinical equipment simulation platform for healthcare training</strong>
</p>

<p align="center">
  <a href="https://tmeduca.org/labsim/">Website</a> ·
  <a href="https://github.com/Debaq/LabSim/wiki">Wiki</a> ·
  <a href="https://github.com/Debaq/LabSim/releases">Downloads</a> ·
  <a href="https://github.com/Debaq/LabSim/issues">Report an issue</a>
</p>

<p align="center">
  <code>Tauri 2 · React · Rust · TypeScript · llama.cpp · Whisper · Piper</code>
</p>

---

## What is LabSim

LabSim is a desktop application that simulates a full working day at a clinical center. Students operate realistic equipment with the same knobs, joystick and workflows they will find in practice: positioning the patient, adjusting the chin rest, aligning the device and running the test.

Patients have personality, voice, clinical history and memory of previous encounters. Teachers design the activity by configuring cases, artifacts and pedagogical situations. A virtual secretary (Karime) manages the schedule and notifies about delays and waiting patients.

## Features

- **Realistic equipment** — Knobs, dials and flows identical to the physical instrument. Procedural memory before touching real hardware.
- **Living patients** — Characters with pathology, personality, their own voice and memory of previous encounters. An anxious patient does not react like a cooperative one.
- **Fully local AI** — LLM via llama.cpp, speech-to-text with Whisper, text-to-speech with Piper. Sidecar processes that use the GPU when available. No cloud dependency for the simulation.
- **Pedagogical management** — Teachers create cases, configure artifacts, define validation checkpoints per procedure and student level. Karime coordinates the flow of the center.
- **Emergent clinical center** — Real schedules, consultation boxes, clinical meetings, referrals and interconsultations. The center emerges when teachers share students and book appointments.
- **Cross-platform** — Native installers for Windows (MSI/EXE) and Linux (DEB/RPM/AppImage).

## Specialties

| Area | Simulators |
|------|-----------|
| **Audiology** | Audiometer, Impedance, Speech audiometry, OAE, ABR, Hearing aids |
| **Otoneurology** | VNG, vHIT, Electrocochleography |
| **Ophthalmology** | OCT, Perimeter, Retinograph, Corneal Topographer, Scheimpflug, Autorefractometer |

## Download and try it

Installers available on [Releases](https://github.com/Debaq/LabSim/releases).

Demo credentials to explore the app:

```
User: demo
Pass: test
```

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Tailwind CSS 4, Zustand |
| Desktop | Tauri 2, Rust |
| Local AI | llama.cpp (LLM), Whisper (STT), Piper (TTS) |
| Server | PHP 8.1, SQLite, JWT |

## Architecture

- **Native desktop** built with Tauri 2 + Rust (backend) and React + TypeScript (UI).
- **Independent AI sidecars** that adapt to the resources of each machine.
- **Multi-tenant**: staff creates students; each student has their own version of every patient. Teachers propagate changes to all versions.
- **Emergent center**: it is not created as an object — it appears when teachers share students and book appointments.

Detailed documentation: [Project Wiki](https://github.com/Debaq/LabSim/wiki).

## Development

Requirements: Node.js, Rust toolchain, PHP 8.1 (backend).

```bash
# Tauri client
cd tauri-app
npm install
npm run tauri dev

# Backend
cd labsim-backend
# follow the backend README
```

## Contributing

Issues and discussions on GitHub:

- [Issues](https://github.com/Debaq/LabSim/issues) — bugs and proposals
- [Discussions](https://github.com/Debaq/LabSim/discussions) — questions and feedback

## Author

**Nicolás Baier Quezada** — Universidad Austral de Chile

---

<p align="center">
  <sub>Developed at Universidad Austral de Chile · Open Source</sub>
</p>
