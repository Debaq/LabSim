# LabSim 3.0 — Plataforma de Simulación Clínica Educativa

<p align="center">
  <strong>Simulación realista de equipamiento clínico para la formación de profesionales de la salud</strong><br>
  Audiología · Otoneurología · Vestibular · Oftalmología · IA conversacional · Pacientes vivos · Centro clínico simulado
</p>

<p align="center">
  <code>Tauri 2 + React 19 + Rust + PHP</code>&nbsp;&nbsp;|&nbsp;&nbsp;Versión 3.0.0&nbsp;&nbsp;|&nbsp;&nbsp;Licencia MIT
</p>

---

## Qué es LabSim

LabSim simula el **día completo** de un profesional en un centro clínico. El estudiante no "usa un simulador" — vive una jornada clínica con pacientes que tienen personalidad, voz e historia, equipos que responden con datos reales, y la presión de una secretaria que le avisa que se está atrasando.

Los pacientes **evolucionan**, **recuerdan** atenciones anteriores, y los docentes **diseñan** la actividad completa configurando artefactos y situaciones pedagógicas.

## Simuladores

| Equipo | Nombre LabSim | Especialidad | Estado |
|--------|---------------|--------------|--------|
| Audiómetro | AU-2000 | Audiología | Activo |
| Impedanciómetro | Z-400 | Audiología | Activo |
| Logoaudiometría | — | Audiología | Activo |
| OAE | — | Audiología | Activo |
| ABR | — | Otoneurología | Activo |
| Electrococleografía | — | Otoneurología | Activo |
| VNG | VN-200 | Vestibular | Activo |
| vHIT | HI-600 | Vestibular | Activo |
| OCT | — | Oftalmología | Activo |
| Campímetro | HFA-III | Oftalmología | Activo |
| Retinógrafo | — | Oftalmología | Activo |
| Topógrafo de Placido | — | Oftalmología | Activo |
| Tomógrafo Scheimpflug | SA-1 | Oftalmología | Activo |
| Audífonos | — | Audiología | Activo |

Agregar un nuevo simulador = crear schema + formulario + ventana + registrar. [Ver guía](docs/05-agregar-simulador.md).

## Arquitectura

```
┌─────────────────────────────────────────┐
│  Capa 0-1: Instituciones + Cursos       │
│  Capa 2:   Agenda global + conflictos   │
│  Capa 3-4: Pacientes vivos + equipos    │
│  Capa 5-6: Larissa + Karime            │
│  Capa 7-8: Reuniones + Supervisión      │
│  Capa 9:   Stats                        │
└─────────────────────────────────────────┘
```

Los pacientes tienen un **core fijo** (identidad, personalidad, historia clínica) y **módulos dinámicos** (un key por simulador, extensible sin tocar el core).

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [Visión General](docs/00-vision-general.md) | Qué es LabSim, problema, solución, stack |
| [Flujo del Sistema](docs/01-flujo-del-sistema.md) | Admin → Docente → Estudiante, Centro emergente |
| [Simuladores](docs/02-simuladores.md) | Detalle de cada equipo y modelo de datos |
| [Pacientes Vivos](docs/03-pacientes-vivos.md) | Personalidad, voz, memoria, evolución |
| [Larissa y Centro](docs/04-larissa-y-centro.md) | Ficha clínica MINSAL, Karime, reuniones |
| [Agregar Simulador](docs/05-agregar-simulador.md) | Guía paso a paso para nuevos módulos |
| [Instalación](docs/06-instalacion.md) | Setup, estructura del proyecto |

## Stack

```
Frontend:  React 19 · TypeScript · Tailwind CSS 4 · Zustand · React Hook Form · Zod · D3.js
Backend:   Tauri 2 · Rust · cpal (audio) · llama.cpp (LLM) · Whisper (STT) · Piper (TTS)
Servidor:  PHP 8.1 · SQLite · JWT · bcrypt
```

## Autor

**Nicolás Baier Quezada**

---

<p align="center">
  <sub>LabSim nació para resolver un problema real: los estudiantes de salud no tienen acceso a los equipos que necesitan aprender a usar. Esta plataforma les da ese acceso.</sub>
</p>
