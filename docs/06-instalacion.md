# Instalación y Desarrollo

## Requisitos

- **Node.js** 20+
- **Rust** (rustup, cargo)
- **PHP** 8.1+ con SQLite (para el backend)

## Frontend + Tauri

```bash
cd tauri-app
npm install
npm exec tauri dev
```

## Backend PHP

El backend está en `labsim-backend/`. Necesita:

```bash
# Crear la base de datos
php labsim-backend/install.php

# Ejecutar migraciones
php labsim-backend/migrate.php
```

Base URL del API: `https://tmeduca.org/labsim/backend/api/index.php?route=`

## Estructura del proyecto

```
LabSim/
├── tauri-app/
│   ├── src/                          # Frontend React
│   │   ├── components/
│   │   │   ├── windows/              # Ventanas de la app
│   │   │   ├── impedance/            # Componentes del impedanciómetro
│   │   │   ├── perimetry/            # Componentes del campímetro
│   │   │   ├── scheimpflug/          # Componentes del Scheimpflug
│   │   │   ├── vestibular/           # Componentes compartidos VNG/vHIT
│   │   │   ├── oct/                  # Componentes del OCT
│   │   │   ├── corneal-topography/   # Componentes topógrafo
│   │   │   ├── layout/               # Desktop, taskbar, iconos
│   │   │   └── ui/                   # Componentes base (button, input, etc.)
│   │   ├── modules/                  # Módulos del editor de pacientes
│   │   │   ├── patient-info/         # Identidad
│   │   │   ├── patient-personality/  # Personalidad
│   │   │   ├── anamnesis/            # Historia clínica
│   │   │   ├── impedance/            # Schema + form impedanciometría
│   │   │   ├── oct/                  # Schema + form OCT
│   │   │   ├── visual-field/         # Schema + form campo visual
│   │   │   ├── vng/                  # Schema + form VNG
│   │   │   ├── vhit/                 # Schema + form vHIT
│   │   │   ├── scheimpflug/          # Schema + form Scheimpflug
│   │   │   └── .../                  # Demás módulos
│   │   ├── stores/                   # Estado Zustand
│   │   │   ├── patient-store.ts      # core + modules dinámicos
│   │   │   ├── live-session-store.ts # sesión en vivo con paciente
│   │   │   ├── larissa-store.ts      # agenda + evoluciones
│   │   │   ├── cases-store.ts        # CRUD de pacientes
│   │   │   ├── courses-store.ts      # cursos e inscripción
│   │   │   └── .../
│   │   └── lib/                      # Generadores sintéticos
│   │       ├── impedance-synthetic.ts
│   │       ├── oct-synthetic.ts
│   │       ├── perimetry-patient.ts
│   │       ├── vestibular-synthetic.ts
│   │       ├── scheimpflug-synthetic.ts
│   │       ├── session-config.ts     # Artefactos por cita
│   │       └── .../
│   └── src-tauri/src/                # Backend Rust
│       ├── commands/
│       │   ├── sync.rs               # 40+ comandos API
│       │   ├── chat.rs               # LLM chat con paciente dinámico
│       │   └── .../
│       ├── llm/
│       │   ├── personas.rs           # Karime + Docente
│       │   └── patient_persona.rs    # Generador dinámico de paciente
│       └── .../
└── labsim-backend/                   # Backend PHP
    ├── api/
    │   ├── agenda.php                # Agenda con visibilidad cruzada
    │   ├── cases.php                 # CRUD pacientes
    │   ├── courses.php               # Cursos + bulk import CSV
    │   ├── institutions.php          # Multi-tenant
    │   ├── evolutions.php            # Evoluciones clínicas
    │   ├── interconsultations.php    # Interconsultas
    │   ├── center.php                # Boxes, incidentes, reuniones, planes, validaciones
    │   └── .../
    └── migrate.php                   # Migraciones BD
```
