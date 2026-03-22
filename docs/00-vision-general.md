# LabSim — Visión General

## Qué es LabSim

LabSim es una **plataforma de simulación clínica educativa** donde estudiantes de ciencias de la salud practican con equipamiento médico simulado que replica la experiencia de usar instrumentos reales. No es un sistema de informes ni un tutorial — es una réplica funcional del entorno clínico.

## El problema

Un audiómetro cuesta USD $5.000-$15.000. Un campímetro $20.000+. Un OCT $50.000-$150.000. Las universidades tienen pocos equipos y muchos estudiantes. El resultado: los profesionales llegan a sus primeras prácticas sin haber tocado el instrumental real.

## La solución

LabSim simula el día completo de un profesional en un centro clínico:

1. El estudiante abre la app y ve su **agenda** de pacientes del día
2. **Llama al paciente** — un personaje con personalidad, voz e historia propia
3. **Usa los simuladores** (audiómetro, impedanciómetro, OCT, etc.) que responden con datos del paciente
4. **Crea evoluciones clínicas** en la ficha (norma MINSAL Chile)
5. **Deriva** si es necesario mediante interconsultas
6. **Participa en reuniones clínicas** con compañeros
7. Todo bajo la presión de **Karime**, la secretaria que avisa si se atrasa

Los pacientes evolucionan, recuerdan atenciones anteriores, y los docentes observan todo.

## Arquitectura del sistema (9 capas)

```
Capa 0: Instituciones + Usuarios (multi-tenant)
Capa 1: Cursos + Inscripción de estudiantes (CSV)
Capa 2: Agenda global con visibilidad cruzada entre docentes
Capa 3: Pacientes vivos (personalidad, memoria, estados)
Capa 4: Simuladores conectados al paciente en atención
Capa 5: Larissa (ficha clínica real con evoluciones/interconsultas)
Capa 6: Karime + presión de tiempo + feedback pacientes
Capa 7: Reuniones clínicas, actas, planes de mejora
Capa 8: Supervisión docente (tablero + checkpoints de validación)
Capa 9: Stats y reportes del centro
```

## Roles

| Rol | Qué hace |
|-----|----------|
| **Admin** | Gestiona infraestructura: instituciones, docentes, cursos, apps activas, pacientes base |
| **Docente** | Gestiona pedagogía: unidades de aprendizaje, agenda, pacientes, actividades. Crea estudiantes (CSV) |
| **Instructor** | Apoyo al docente: ajusta sesiones, supervisa en tiempo real |
| **Estudiante** | Vive el día clínico: atiende pacientes, usa equipos, crea evoluciones, participa en reuniones |

## Stack tecnológico

```
Frontend:  React 19 + TypeScript + Tailwind CSS + Zustand
Backend:   Tauri 2 (Rust) + llama.cpp (LLM) + Whisper (STT) + Piper (TTS)
Servidor:  PHP + SQLite (tmeduca.org)
Audio:     cpal (Rust nativo, <10ms latencia)
```
