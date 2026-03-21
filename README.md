# LabSim 3.0 — Plataforma de Simulación Clínica Educativa

<p align="center">
  <strong>Simulación de equipamiento clínico para la formación de profesionales de la salud</strong><br>
  Audiología · Otoneurología · Oftalmología · IA conversacional · Reconocimiento de voz · Simulación de centro clínico · Multiplataforma
</p>

<p align="center">
  <code>Tauri 2 + React 19 + Rust + PHP Backend</code>&nbsp;&nbsp;|&nbsp;&nbsp;Versión 3.0.0&nbsp;&nbsp;|&nbsp;&nbsp;Licencia MIT
</p>

---

## Tabla de Contenidos

1. [Contexto educativo y fundamentos](#1-contexto-educativo-y-fundamentos)
2. [Historia de la simulación en ciencias de la salud](#2-historia-de-la-simulación-en-ciencias-de-la-salud)
3. [Evolución de LabSim](#3-evolución-de-labsim)
4. [Áreas clínicas y visión multidisciplinaria](#4-áreas-clínicas-y-visión-multidisciplinaria)
5. [Arquitectura del sistema](#5-arquitectura-del-sistema)
6. [Motor de audio y DSP](#6-motor-de-audio-y-dsp)
7. [Módulos clínicos en detalle](#7-módulos-clínicos-en-detalle)
8. [Inteligencia artificial integrada](#8-inteligencia-artificial-integrada)
9. [Reconocimiento de voz](#9-reconocimiento-de-voz)
10. [Interfaz de usuario](#10-interfaz-de-usuario)
11. [Base de datos y persistencia](#11-base-de-datos-y-persistencia)
12. [Backend Web — tmeduca.org/labsim/backend](#12-backend-web--tmeducaorglabsimbackend)
13. [Larissa — Sistema de fichas clínicas](#13-larissa--sistema-de-fichas-clínicas)
14. [Modalidad Centro — Simulación de gestión clínica](#14-modalidad-centro--simulación-de-gestión-clínica)
15. [Guía de instalación y desarrollo](#15-guía-de-instalación-y-desarrollo)
16. [Creación de módulos adicionales (Add-ons)](#16-creación-de-módulos-adicionales-add-ons)
17. [Creación de personas IA personalizadas](#17-creación-de-personas-ia-personalizadas)
18. [Stack tecnológico completo](#18-stack-tecnológico-completo)
19. [Estructura del proyecto](#19-estructura-del-proyecto)
20. [Roadmap](#20-roadmap)

---

## 1. Contexto educativo y fundamentos

### El problema

La formación de profesionales de la salud enfrenta un desafío estructural y universal: el acceso a equipamiento clínico real es costoso, escaso y centralizado. Un audiómetro clínico de dos canales cuesta entre USD $5.000 y $15.000; un campímetro computarizado supera los $20.000; un equipo de OCT ronda los $50.000-$150.000. Las universidades deben atender a decenas de estudiantes con equipos limitados, y el resultado es predecible: muchos futuros profesionales llegan a sus primeras prácticas clínicas sin haber manipulado nunca el instrumental real de su disciplina.

Este problema no es exclusivo de una especialidad. Afecta a:

| Profesión | Equipamiento inaccesible | Consecuencia formativa |
|-----------|--------------------------|------------------------|
| **Audiólogos** | Audiómetros, impedanciómetros, equipos de OAE/ABR | No practican enmascaramiento ni interpretan resultados en tiempo real |
| **Otoneurólogos** | Videonistagmografía, posturografía, vHIT | No visualizan nistagmos ni correlacionan con patología vestibular |
| **Oftalmólogos / Tecnólogos** | Campímetros, OCT, tonómetros | No interpretan defectos de campo visual ni scans retinianos |
| **Fonoaudiólogos** | Equipos de logoaudiometría, análisis acústico | No aplican protocolos de discriminación del habla |

### La propuesta de LabSim

LabSim no es un sistema de informes ni un software de gestión clínica. Es un **simulador**: una réplica funcional del entorno clínico donde el estudiante interactúa con controles realistas (perillas rotatorias, interruptores, displays LCD) que reproducen fielmente el flujo de trabajo de los equipos reales.

La plataforma nació centrada en audiología — el área más madura — pero su arquitectura modular permite (y ya comenzó a) expandirse hacia otras especialidades. Hoy LabSim incluye módulos de audiología, otoneurología y oftalmología, con visión de incorporar evaluación vestibular, rehabilitación y más.

El simulador aborda tres dimensiones del aprendizaje:

| Dimensión | Qué cubre LabSim | Ejemplo audiológico | Ejemplo oftalmológico |
|-----------|-------------------|---------------------|-----------------------|
| **Procedimental** | Manipulación de controles, secuencia de pruebas, técnica de presentación | Girar la perilla de frecuencia, ajustar intensidad en pasos de 5 dB | Posicionar estímulos en un campímetro, ajustar tamaño del target |
| **Conceptual** | Interpretación de resultados, clasificación de patologías, criterios diagnósticos | Leer un audiograma y distinguir hipoacusia conductiva vs. sensorioneural | Identificar un escotoma arcuato en una campimetría y correlacionarlo con glaucoma |
| **Decisional** | Cuándo cambiar de protocolo, qué derivar, cómo integrar hallazgos | Decidir aplicar enmascaramiento cuando hay gap aéreo-óseo > 40 dB | Solicitar OCT ante sospecha de edema macular en un paciente diabético |

### Roles de usuario

| Rol | Acceso | Propósito |
|-----|--------|-----------|
| **Estudiante** | Simuladores, Larissa (fichas), sesiones, agenda asignada, chat de box | Práctica clínica |
| **Instructor** | Todo lo anterior + Crear Casos, crear sesiones (con aprobación), gestionar agenda | Docente junior, apoyo directo |
| **Docente** | Todo lo anterior + sesiones auto-aprobadas, directrices Karime, inyectar incidentes, calificar | Diseño y supervisión |
| **Admin** | Acceso completo + panel web + directrices globales + gestión usuarios | Administración del sistema |

---

## 2. Historia de la simulación en ciencias de la salud

### El origen: maniquíes y pacientes estandarizados (1960s-1980s)

La simulación en salud no nació con la informática. En 1960, la Universidad de Southern California presentó **Sim One**, el primer maniquí programable para anestesiología. En 1963, **Resusci Anne** (Laerdal) se convirtió en el estándar para entrenamiento en RCP. Estos simuladores físicos demostraron una verdad pedagógica que sigue vigente: *la práctica repetida en un entorno seguro es insustituible para desarrollar competencias clínicas*.

Paralelamente, la evaluación por **pacientes estandarizados** (actores entrenados para simular síntomas) revolucionó la enseñanza médica en los 70s, pero su costo y logística los hicieron inviables para especialidades que dependen de equipamiento instrumental (audiología, oftalmología, neurofisiología).

### Simulación por computadora en audiología (1980s-2000s)

La audiología fue una de las primeras especialidades en explorar simulación digital:

- **CASPA** (Computer-Aided Speech and Hearing Analysis, años 80): software DOS con audiogramas estáticos. Sin controles interactivos.
- **Audiology Teaching Software** (Universidad de Memphis, años 90): timpanogramas y casos pre-grabados, pero interacción tipo "cuestionario".
- **AudSim** (Parrot Software, 2000s): primer simulador con interfaz gráfica que emulaba la apariencia de un audiómetro. Pacientes virtuales con respuestas pre-programadas (árboles de decisión).
- **OtoSim/AudioSim** (Universidad de Toronto): enfocado en otoscopía con imágenes reales de membranas timpánicas.

### Simulación en oftalmología y neurología (2000s-2020s)

Otras especialidades desarrollaron sus propias herramientas:

- **EyeSi** (VRmagic): simulador quirúrgico de realidad virtual para cirugía de catarata y vitreoretina. Excelente para habilidades motoras, pero no cubre evaluación funcional (campimetría, OCT).
- **Humphrey Field Analyzer Virtual**: módulos de entrenamiento en interpretación de campos visuales, pero sin simulación del equipo — solo lectura de resultados estáticos.
- **Simuladores vestibulares**: casi inexistentes. La evaluación otoneurológica (videonistagmografía, maniobras posicionales, vHIT) se enseña casi exclusivamente con pacientes reales o videos.

### Limitaciones históricas comunes

Todas estas herramientas compartían limitaciones que LabSim busca superar:

1. **Monoespecialidad**: cada simulador cubría una sola disciplina, impidiendo la formación integrada (ej: un caso otoneurológico requiere audiometría + pruebas vestibulares + a veces campimetría).
2. **Sin síntesis de señales reales**: los estímulos eran pregrabados o inexistentes.
3. **Controles simplificados**: botones y menús desplegables en lugar de controles que repliquen la experiencia real.
4. **Sin IA**: las respuestas de pacientes virtuales eran árboles de decisión rígidos, no lenguaje natural.
5. **Dependencia de internet**: muchos eran aplicaciones web sin modo offline.
6. **Sin interoperabilidad**: imposible correlacionar hallazgos entre pruebas de distintas áreas en un mismo paciente.

### LabSim en contexto

LabSim 3.0 es la primera plataforma de simulación clínica que combina:
- **Múltiples especialidades** en un solo paquete: audiología, otoneurología y oftalmología, con arquitectura abierta para incorporar más
- Síntesis de audio en tiempo real (tonos puros, ruido de enmascaramiento, ruido speech-shaped)
- Interfaz de audiómetro con controles rotatorios realistas
- IA conversacional local (sin dependencia de la nube) para pacientes virtuales y tutoría
- Reconocimiento de voz para interacción natural
- Cobertura de 14+ módulos de evaluación clínica
- Ejecución nativa multiplataforma sin navegador
- **Paciente unificado**: un mismo caso puede tener datos audiológicos, vestibulares y oftalmológicos, fomentando el razonamiento clínico integrado

---

## 3. Evolución de LabSim

### v1.0 — PySide2/Qt (Python)

La primera versión fue una aplicación de escritorio escrita en Python con PySide2 (Qt para Python). Incluía módulos básicos de audiometría e impedanciometría con interfaces funcionales pero limitadas gráficamente. La generación de audio dependía de librerías Python que introducían latencia perceptible.

### v2.0 — Interfaz web (Python + Flask)

Se migró la interfaz a un frontend web servido localmente, manteniendo el backend Python. Esto mejoró la presentación visual pero introdujo la complejidad de mantener un servidor local y la comunicación HTTP añadía overhead.

### v3.0 — Tauri 2 + React + Rust (versión actual)

La versión actual es una reescritura completa que resuelve todos los problemas anteriores:

| Aspecto | v1/v2 (Python) | v3 (Tauri/Rust) |
|---------|----------------|-----------------|
| Audio | PyAudio (~50ms latencia) | cpal nativo (~5ms latencia) |
| UI | Qt widgets / HTML básico | React 19 + shadcn/ui + D3.js |
| IA | No disponible | LLM local (Qwen vía llama.cpp) |
| Voz | No disponible | Whisper.cpp integrado |
| Tamaño | ~200 MB (Python + Qt) | ~15 MB (binario Rust) |
| Arranque | ~8 segundos | ~1 segundo |
| Seguridad | Sin autenticación | bcrypt + roles (admin/docente/estudiante) |

---

## 4. Áreas clínicas y visión multidisciplinaria

### Mapa de especialidades

LabSim organiza sus módulos en **áreas clínicas** que corresponden a disciplinas profesionales reales. Cada área agrupa pruebas que un profesional de esa especialidad realizaría:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LabSim 3.0                                  │
├─────────────────┬──────────────────┬──────────────────┬─────────────┤
│   AUDIOLOGÍA    │  OTONEUROLOGÍA   │  OFTALMOLOGÍA    │  COMUNES    │
│   (core)        │  (en desarrollo) │  (activo)        │             │
├─────────────────┼──────────────────┼──────────────────┼─────────────┤
│ Audiometría     │ ABR / BERA       │ OCT              │ Datos del   │
│ Logoaudiometría │ Electrococleo-   │ Campo Visual /   │ paciente    │
│ Supraliminal    │ grafía           │ Perimetría       │ Anamnesis   │
│ Impedanciometría│ (futuro:         │                  │ Agenda      │
│ OAE             │ vHIT, VNG,       │ (futuro:         │ Exportar    │
│ Audífonos       │ posturografía)   │ tonometría,      │ JSON        │
│                 │                  │ fondo de ojo)    │             │
└─────────────────┴──────────────────┴──────────────────┴─────────────┘
```

### Audiología (core — 7 módulos)

El área fundacional de LabSim. Cubre la evaluación auditiva completa desde el screening hasta la rehabilitación protésica:

| Módulo | Prueba clínica | Qué evalúa |
|--------|---------------|-------------|
| **Audiometría** | Audiometría tonal liminar | Umbrales auditivos por frecuencia (125-20kHz) |
| **Logoaudiometría** | SDT, SRT, discriminación | Procesamiento del habla |
| **Supraliminal** | SISI, tone decay, loudness balance | Reclutamiento, adaptación patológica |
| **Impedanciometría** | Timpanometría, reflejos acústicos | Función del oído medio |
| **OAE** | TEOAE, DPOAE | Función coclear (células ciliadas externas) |
| **Audífonos** | REM, compresión WDRC, campo libre | Adaptación y verificación protésica |

### Otoneurología (en expansión — 2 módulos activos)

Pruebas que exploran la frontera entre audición y sistema vestibular/neural. Estas pruebas son clave para diagnósticos diferenciales (ej: neurinoma del acústico, enfermedad de Ménière):

| Módulo | Prueba clínica | Qué evalúa |
|--------|---------------|-------------|
| **ABR** | Potenciales evocados auditivos de tronco | Integridad de la vía auditiva neural (ondas I-V) |
| **Electrococleografía** | Relación SP/AP | Hidrops endolinfático, patología coclear |

**Módulos planificados para otoneurología:**
- **vHIT** (Video Head Impulse Test) — función de cada canal semicircular
- **VNG** (Videonistagmografía) — evaluación del nistagmo, pruebas calóricas, pruebas posicionales
- **Posturografía** — control postural, integración sensorial
- **VEMP** (Potenciales evocados miogénicos vestibulares) — función sacular y utricular

### Oftalmología (activo — 2 módulos)

Evaluación de la función visual, con énfasis en las pruebas instrumentales que requieren equipamiento costoso:

| Módulo | Prueba clínica | Qué evalúa |
|--------|---------------|-------------|
| **OCT** | Tomografía de coherencia óptica | Estructura retiniana, espesor macular, fibras nerviosas |
| **Campo visual** | Perimetría computarizada | Defectos del campo visual, screening de glaucoma |

**Módulos planificados para oftalmología:**
- **Tonometría** — presión intraocular
- **Fondo de ojo** — retinografía, evaluación de papila y mácula
- **Agudeza visual** — optotipos, tablas de Snellen/LogMAR

### Visión futura: más allá de las tres áreas iniciales

La arquitectura modular de LabSim permite que cualquier profesional o institución cree módulos para su especialidad. Algunas expansiones naturales:

| Área potencial | Profesional | Módulos posibles |
|----------------|-------------|------------------|
| **Fonoaudiología** | Fonoaudiólogo | Análisis acústico de la voz, evaluación de la deglución |
| **Neurofisiología** | Tecnólogo médico | EEG, EMG, potenciales somatosensoriales |
| **Cardiología** | Tecnólogo / Cardiólogo | ECG, ecocardiografía (interpretación) |
| **Neumología** | Kinesiólogo | Espirometría, curvas flujo-volumen |

El diseño de "paciente unificado" de LabSim hace que estos módulos no sean islas: un caso clínico de un paciente con diabetes puede tener datos de audiometría (neuropatía auditiva), OCT (retinopatía diabética) y campo visual (defectos por neuropatía óptica) simultáneamente, entrenando al estudiante en el razonamiento clínico integrado.

---

## 5. Arquitectura del sistema

### Vista general

```
┌──────────────────────────────────────────────────────────┐
│                    FRONTEND (WebView)                     │
│  React 19 + TypeScript + Tailwind CSS + shadcn/ui        │
│                                                           │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐  │
│  │ Zustand  │ │ React    │ │ D3.js     │ │ Dexie      │  │
│  │ Stores   │ │ Hook Form│ │ Charts    │ │ (IndexedDB)│  │
│  └─────────┘ └──────────┘ └───────────┘ └────────────┘  │
│                       │                                    │
│                  Tauri invoke()                            │
├──────────────────────────────────────────────────────────┤
│                    BACKEND (Rust)                          │
│  Tauri 2.9 Runtime                                        │
│                                                           │
│  ┌───────────┐ ┌───────────┐ ┌────────────┐ ┌─────────┐ │
│  │ Audio     │ │ LLM       │ │ Speech     │ │ SQLite  │ │
│  │ Engine    │ │ Engine    │ │ Engine     │ │ DB      │ │
│  │ (cpal)    │ │ (llama.cpp)│ │ (whisper)  │ │(rusqlite)│ │
│  └───────────┘ └───────────┘ └────────────┘ └─────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Comunicación Frontend ↔ Backend

La comunicación se realiza mediante **Tauri Commands**: funciones Rust anotadas con `#[tauri::command]` que el frontend invoca con `invoke()`. Esto es un IPC (Inter-Process Communication) binario, no HTTP, lo que garantiza latencia mínima (~0.1ms por llamada).

```typescript
// Frontend: invocación de comando Rust
const result = await invoke("play_tone", {
  params: { frequency: 1000, duration: 2.0, levelDbfs: -20.0 }
});
```

```rust
// Backend: definición del comando
#[tauri::command]
pub fn play_tone(audio: State<AudioState>, params: ToneParams) -> Result<(), String> {
    let engine = audio.engine.lock().unwrap();
    engine.as_ref().ok_or("Motor no disponible")?.play_tone(
        params.frequency, params.duration, params.level_dbfs,
        params.pulsatile_hz, params.duty_cycle.unwrap_or(0.5),
    )
}
```

### Estado compartido (Tauri Managed State)

Cada subsistema mantiene su estado en un `Mutex` gestionado por Tauri:

```rust
tauri::Builder::default()
    .manage(Database::new()?)       // SQLite
    .manage(LlmState::new())        // Motor LLM
    .manage(AudioState::new())      // Motor de audio
    .manage(SpeechState::new())     // Motor Whisper
    .manage(RecordingState::new())  // Buffer de grabación
```

---

## 6. Motor de audio y DSP

### Cadena de señal

El motor de audio de LabSim genera señales digitales en tiempo real usando síntesis directa (no samples pregrabados). La cadena es:

```
Generador de señal → Modulación (pulsátil/FM) → Envelope (attack/release) → Normalización → CPAL → Hardware de audio
```

### Tipos de señal implementados

#### Tono puro (`PureTone`)

Onda sinusoidal con control de frecuencia, intensidad, duración, y modulaciones:

```
y(t) = A · sin(2π · f · t + φ)
```

Donde `A = 10^(dB/20)` (conversión dB a amplitud lineal).

**Modulaciones disponibles:**
- **Pulsátil (PWM)**: on/off con duty cycle configurable (por defecto 50%, 500ms on / 500ms off)
- **FM (modulación de frecuencia)**: `f_inst = f + Δf · sin(2π · f_mod · t)` para warble tones
- **Envelope**: fade in/out lineal de 5ms para eliminar clics transientes

#### Ruido blanco (`WhiteNoise`)

Distribución gaussiana (Box-Muller transform) con espectro plano:

```
y(t) = A · N(0,1)
```

#### Ruido rosa (`PinkNoise`)

Algoritmo Voss-McCartney con 16 registros para espectro -3 dB/octava. Normalización estadística (media=0, σ=1) por bloque.

#### Ruido speech-shaped (`SpeechNoise`)

Ruido blanco filtrado con tres biquads paralelos para aproximar el espectro del habla:

```
y(t) = HPF₂₀₀(x) + 1.5 · BPF₁₀₀₀(x) + 0.6 · LPF₆₀₀₀(x)
```

Los pesos (1.0, 1.5, 0.6) enfatizan las frecuencias del habla (300-3000 Hz).

#### Ruido de banda estrecha (`NarrowBandNoise`)

Ruido blanco + filtro biquad bandpass centrado en la frecuencia del tono de prueba. El factor Q controla el ancho de banda:

```
Q = f_centro / ancho_de_banda
```

### Procesamiento DSP

**Filtros biquad IIR (RBJ Cookbook):**

Implementación Direct Form I de segundo orden con coeficientes calculados según las ecuaciones de Robert Bristow-Johnson:

```rust
// Coeficientes bandpass
w0 = 2π · fc / sr
α  = sin(w0) / (2·Q)

b0 =  Q·α
b1 =  0
b2 = -Q·α
a0 =  1 + α
a1 = -2·cos(w0)
a2 =  1 - α
```

**Generación por bloques:**

Todas las señales implementan el trait `Signal` que genera audio en bloques de 1024 muestras. Esto optimiza el uso del CPU y permite procesamiento sin interrupciones a la tasa de muestreo (típicamente 48 kHz).

### Especificaciones de audio

| Parámetro | Valor |
|-----------|-------|
| Tasa de muestreo | 48.000 Hz (nativo del dispositivo) |
| Profundidad de bits | 32-bit float (IEEE 754) |
| Canales | Mono (expansible a estéreo) |
| Latencia típica | < 10 ms (CPAL nativo) |
| Rango de frecuencias | 125 Hz — 20.000 Hz |
| Rango dinámico | -15 dBFS a +120 dBFS (referencia audiológica) |
| Tamaño de bloque | 1024 muestras (~21 ms @ 48kHz) |

---

## 7. Módulos clínicos en detalle

LabSim implementa 14 módulos organizados en tres áreas clínicas y un grupo de módulos transversales comunes a cualquier especialidad.

### AUDIOLOGÍA

#### Audiometría tonal liminar

El módulo central del simulador. Replica un audiómetro de dos canales con:

- **Frecuencias ISO**: 125, 250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000 Hz
- **Frecuencias extendidas**: hasta 20.000 Hz (alta frecuencia)
- **Transductores**: vía aérea (auriculares), vía ósea (vibrador), campo libre (parlantes)
- **Intensidad**: -15 a 120 dB HL en pasos de 5 dB (límites dependientes de frecuencia y transductor)
- **Enmascaramiento**: ruido de banda estrecha contralateral
- **Presentación**: continua, pulsátil (500ms on/off), alternante (700ms ipsi / 300ms silencio)
- **Audiograma**: graficado en tiempo real con D3.js según convenciones ISO 8253

**Rangos de intensidad por frecuencia y transductor:**

| Frecuencia | Vía aérea | Vía ósea | Campo libre |
|------------|-----------|----------|-------------|
| 125 Hz     | -15 a 100 dB | 0 a 40 dB | 0 a 100 dB |
| 250 Hz     | -15 a 100 dB | 0 a 45 dB | 0 a 100 dB |
| 500 Hz     | -15 a 100 dB | 0 a 50 dB | 0 a 100 dB |
| 1000-8000 Hz | -15 a 100 dB | 0 a 100 dB | 0 a 100 dB |
| 10000+ Hz  | -15 a 75 dB | — | 0 a 75 dB |

#### Logoaudiometría

Evaluación del procesamiento del habla:
- **SDT** (Speech Detection Threshold): umbral de detección de la palabra
- **SRT** (Speech Reception Threshold): umbral de reconocimiento del 50%
- **Discriminación**: porcentaje de palabras correctamente repetidas a intensidad supraumbrál

#### Pruebas supraliminares

Pruebas sobre el umbral para detectar reclutamiento y deterioro tonal:
- SISI (Short Increment Sensitivity Index)
- Tone Decay (deterioro del tono)
- Loudness Balance (equilibrio de sonoridad)

#### Impedanciometría

Evaluación del oído medio:
- **Timpanometría**: curvas tipo A, As, Ad, B, C (clasificación Jerger) con presiones de -400 a +200 daPa
- **Reflejos acústicos**: ipsilateral y contralateral, umbral y decaimiento

#### Emisiones otoacústicas (OAE)

Evaluación de función coclear (células ciliadas externas):
- **TEOAE** (Transient Evoked): respuesta a clics
- **DPOAE** (Distortion Product): dos tonos, producto de distorsión 2f1-f2

#### Audífonos

Módulo de adaptación y verificación protésica:
- Compresión WDRC (Wide Dynamic Range Compression)
- Medición en oído real (REM - Real Ear Measurement)
- Audiometría en campo libre con/sin audífonos
- Fórmulas prescriptivas (NAL-NL2, DSL)

### OTONEUROLOGÍA

#### Potenciales evocados auditivos (ABR)

Evaluación de la vía auditiva neural:
- Formas de onda con identificación de ondas I, III, V
- Latencias absolutas e intervalos (I-III, III-V, I-V)
- Función latencia-intensidad

#### Electrococleografía

Evaluación del potencial coclear:
- Relación SP/AP (potencial de sumación / potencial de acción)
- Criterios diagnósticos para hidrops endolinfático (Ménière)

Los ABR son una herramienta fundamental en otoneurología porque permiten diferenciar entre patología coclear (sensorioneural) y retrococlear (neural). Un patrón clásico de neurinoma del acústico muestra prolongación del intervalo I-V con onda V degradada.

### OFTALMOLOGÍA

#### Tomografía de coherencia óptica (OCT)

Evaluación estructural de la retina mediante scans sintéticos de alta resolución:
- Scans de corte transversal (B-scan) de capas retinianas
- Espesor macular: evaluación de edema, tracción, agujero macular
- Capa de fibras nerviosas de la retina (RNFL): screening y seguimiento de glaucoma
- Análisis de capas ganglionares (GCL+IPL)

**Relevancia educativa**: el OCT se ha convertido en el examen complementario más solicitado en oftalmología moderna. Los estudiantes necesitan aprender a interpretar scans normales vs. patológicos antes de enfrentarse a decisiones terapéuticas (ej: inyección antiangiogénica en edema macular diabético).

#### Campo visual / Perimetría

Evaluación funcional del campo visual:
- Perimetría estática computarizada (tipo Humphrey)
- Detección de escotomas (absolutos y relativos)
- Patrones de defecto: arcuato, altitudinal, hemianopsia, cuadrantanopsia
- Índices globales: MD (Mean Deviation), PSD (Pattern Standard Deviation)
- Análisis de progresión (GPA - Guided Progression Analysis)

**Relevancia educativa**: la perimetría es esencial para diagnóstico y seguimiento del glaucoma (primera causa de ceguera irreversible mundial), pero también revela patología neurológica — una hemianopsia homónima sugiere lesión en vía óptica retroquiasmática (ACV, tumor).

### MÓDULOS TRANSVERSALES

Estos módulos son comunes a cualquier especialidad clínica:

| Módulo | Descripción | Uso interdisciplinario |
|--------|-------------|------------------------|
| **Datos del paciente** | Información demográfica, antecedentes, contacto | Base de todo caso clínico |
| **Anamnesis** | Historia clínica estructurada: motivo de consulta, antecedentes, medicamentos, alergias | Adaptable por especialidad |
| **Agenda** | Programación de citas y gestión de horarios | Simula la logística real de una consulta |
| **Exportar JSON** | Exportación completa de datos del paciente en formato estructurado | Interoperabilidad, backup, análisis |

---

## 8. Inteligencia artificial integrada

### LLM local (sin nube, sin internet)

LabSim integra un motor de lenguaje grande (LLM) que corre **completamente en la máquina del usuario**, sin enviar datos a servidores externos. Esto garantiza:

- **Privacidad**: los datos del paciente simulado nunca salen del computador
- **Disponibilidad offline**: funciona sin conexión a internet (después de la descarga inicial del modelo)
- **Costo cero**: no hay APIs de pago ni suscripciones

### Motor: llama.cpp vía Rust FFI

El backend usa `llama-cpp-2`, un binding Rust de [llama.cpp](https://github.com/ggerganov/llama.cpp), el motor de inferencia LLM más eficiente disponible. Los modelos usan formato GGUF con cuantización para reducir consumo de RAM.

### Modelos disponibles

| Modelo | Tamaño | RAM necesaria | Uso recomendado |
|--------|--------|---------------|-----------------|
| **Qwen3 0.6B** (Q8_0) | 610 MB | ~1 GB | Respuestas rápidas, PCs modestas |
| **Qwen2.5 1.5B** (Q4_K_M) | 1.065 MB | ~2 GB | Balance calidad/velocidad |
| **Qwen3 1.7B** (Q8_0) | 1.750 MB | ~3 GB | Mejor calidad de respuesta |

Los modelos se descargan automáticamente desde HuggingFace Hub la primera vez.

### Personas IA

LabSim incluye dos personas predefinidas que simulan interacciones clínicas reales:

#### Karime — Secretaria/Recepcionista

- **Rol**: secretaria del Centro Audiológico LabSim
- **Personalidad**: simpática, eficiente, informal. Usa expresiones latinas naturales ("dale", "listo", "oka")
- **Función pedagógica**: simula la dinámica real de una clínica — avisa cuando llegan pacientes, da contexto sobre cada caso, maneja la agenda
- **Temperatura**: 0.7 (respuestas más variadas y naturales)
- **Max tokens**: 120 (mensajes cortos, tipo WhatsApp)

#### Profesor Andrés Soto — Docente de audiología

- **Rol**: profesor universitario de audiología clínica con 25 años de experiencia
- **Personalidad**: amable pero exigente, usa analogías cotidianas, plantea casos clínicos
- **Función pedagógica**: responde dudas técnicas, corrige errores del estudiante sin humillar, guía hacia el razonamiento clínico correcto
- **Temperatura**: 0.5 (respuestas más consistentes y precisas)
- **Max tokens**: 350 (explicaciones detalladas)

### Formato de prompt: ChatML

Todos los modelos Qwen usan el formato ChatML con la directiva `/no_think` para desactivar el modo de razonamiento interno y producir respuestas directas:

```
<|im_start|>system
{system_prompt}
/no_think<|im_end|>
<|im_start|>user
{mensaje del usuario}<|im_end|>
<|im_start|>assistant
```

### Parámetros de generación

```rust
// Cadena de muestreo
LlamaSampler::chain_simple([
    LlamaSampler::temp(temperature),  // 0.5-0.7 según persona
    LlamaSampler::top_p(0.9, 1),      // Nucleus sampling
    LlamaSampler::dist(42),           // Distribución determinista
])
// Contexto: 2048 tokens
```

---

## 9. Reconocimiento de voz

### Whisper.cpp integrado

LabSim incluye reconocimiento de voz offline mediante [whisper-rs](https://github.com/tazz4843/whisper-rs), un binding Rust de OpenAI Whisper. Esto permite al estudiante interactuar con las personas IA usando su voz en lugar de escribir.

### Flujo de trabajo

```
1. speech_load_model()      → Descarga whisper-tiny (~75 MB) la primera vez
2. speech_start_recording() → Captura audio del micrófono a 16 kHz mono
3. speech_stop_recording()  → Detiene la captura
4. speech_transcribe("es")  → Convierte audio a texto en español
```

### Especificaciones

| Parámetro | Valor |
|-----------|-------|
| Modelo | whisper-tiny (39M parámetros) |
| Idiomas | Español (principal), multilingüe |
| Tasa de muestreo | 16.000 Hz (mono) |
| Latencia de transcripción | ~1-3 segundos (CPU) |
| Precisión | ~85% en español conversacional |

---

## 10. Interfaz de usuario

### Escritorio virtual (Desktop metaphor)

La interfaz principal emula un escritorio de computador donde cada módulo se abre como una ventana independiente:

- **Ventanas arrastrables y redimensionables** (`WindowFrame`)
- **Barra de tareas** inferior con ventanas abiertas, accesos directos (Mensajes con globito de notificación, Agenda), indicador de conexión al servidor (verde/amarillo/rojo)
- **Escritorio limpio** — solo lo esencial: 4 simuladores + Larissa + Centro + Sesiones + Estadísticas + Crear Casos (admin/docente/instructor)
- **Menú inicio** — acceso a todas las apps incluyendo Historial, Explorador, Editor, Configuración

### Audiómetro virtual

El componente más complejo de la interfaz. Replica fielmente los controles de un audiómetro clínico:

| Control | Componente | Función |
|---------|-----------|---------|
| Dial de frecuencia | `RotaryKnob` | Selección 125-20000 Hz |
| Dial de intensidad | `RotaryKnob` | Ajuste -15 a 120 dB en pasos de 5 dB |
| Canal CH0/CH1 | `ChannelStrip` | Control independiente por canal |
| Transductor | `ToggleSwitch` | Aéreo / Óseo / Campo libre |
| Estímulo | `ToggleSwitch` | Tono / FM / Habla / NBN / WN / PN / SN |
| Display LCD | `UnifiedDisplay` | Frecuencia, intensidad, modo actual |
| VU meter | `VuMeter` | Nivel de señal en tiempo real |
| Presentación | Botones | Continuo / Pulsátil / Alternante |

### Temas y personalización

- Modo oscuro / claro (con `next-themes`)
- Tamaño de fuente configurable
- Wallpaper personalizable
- Internacionalización español/inglés (i18next)

---

## 11. Base de datos y persistencia

### Capa dual de almacenamiento

LabSim usa dos sistemas de persistencia complementarios:

**SQLite (Backend Rust — rusqlite):**
```sql
-- Usuarios y autenticación (bcrypt)
users (id, username, password_hash, role, created_at)

-- Pacientes simulados
patients (id, name, age, gender, diagnosis, created_at, updated_at)

-- Perfiles de datos clínicos (JSON completo)
patient_profiles (id, patient_id, profile_json, schema_version, created_at)

-- Sesiones de simulación
sessions (id, user_id, patient_id, started_at, ended_at)

-- Calibración del audiómetro virtual
calibration (id, frequency, reference_db, correction_factor, updated_at)
```

**IndexedDB (Frontend — Dexie):**

Almacenamiento del lado del cliente para datos de sesión, preferencias de UI, y cache de estados de módulos usando Zustand con persistencia en `localStorage`.

### Esquema de datos del paciente

Cada paciente tiene un perfil JSON que contiene todos los datos de todos los módulos:

```typescript
interface PatientData {
  patientInfo:    { /* datos demográficos */ }
  anamnesis:      { /* historia clínica */ }
  audiometry:     { /* umbrales, audiograma */ }
  logoaudiometry: { /* SDT, SRT, discriminación */ }
  supraliminal:   { /* SISI, tone decay */ }
  impedance:      { /* timpanograma, reflejos */ }
  oae:            { /* TEOAE, DPOAE */ }
  abr:            { /* ondas, latencias */ }
  electrocochleo: { /* SP/AP */ }
  hearingAids:    { /* compresión, REM */ }
  oct:            { /* scans OCT */ }
  visualField:    { /* perimetría */ }
}
```

---

## 12. Backend Web — tmeduca.org/labsim/backend

### Arquitectura servidor

LabSim se conecta a un backend centralizado que gestiona usuarios, sesiones prácticas, entregas, telemetría y la modalidad Centro. El backend es **PHP 7.4+ puro** (sin frameworks) con **SQLite** como base de datos, diseñado para funcionar en cualquier hosting compartido.

```
App Tauri ←─ HTTPS ─→ tmeduca.org/labsim/backend/api/v1/
  │                              │
  SQLite (local)            SQLite (servidor)
```

### Stack del backend

| Componente | Tecnología | Justificación |
|---|---|---|
| API REST | PHP 7.4+ puro | Disponible en cualquier hosting, sin dependencias |
| Base de datos | SQLite (WAL mode) | Un solo archivo .db, sin servidor de BD |
| Panel admin | PHP + HTML/CSS/JS vanilla | Sin build step, deploy por FTP |
| Autenticación | JWT HS256 (implementación propia) | Sin librerías externas |
| Archivos | Upload con validación MIME | Guías, releases, assets |

### Estructura del backend

```
labsim-backend/
├── api/                     # 16 endpoints REST
│   ├── index.php            # Router principal
│   ├── auth.php             # Login JWT, refresh, logout
│   ├── users.php            # CRUD usuarios (admin)
│   ├── cases.php            # CRUD casos clínicos
│   ├── groups.php           # Grupos + miembros
│   ├── sessions.php         # Sesiones prácticas + aprobación + guías
│   ├── submissions.php      # Entregas + calificación
│   ├── agenda.php           # Agenda de atención del centro
│   ├── procedures.php       # Cartera de procedimientos
│   ├── telemetry.php        # Ingest de eventos de simuladores
│   ├── stats.php            # Estadísticas + export CSV
│   ├── feedback.php         # Reclamos/felicitaciones de pacientes
│   ├── directives.php       # Directrices jerárquicas de Karime
│   ├── center.php           # Boxes, incidentes, reuniones, chat
│   ├── assets.php           # Releases + archivos
│   └── sync.php             # Push/pull sincronización
├── admin/                   # Panel web admin (10 páginas)
├── core/                    # JWT, DB, auth, validators, upload
├── data/                    # SQLite (protegido por .htaccess)
├── uploads/                 # Guías, releases, assets
├── .htaccess                # Routing + seguridad
└── install.php              # Setup: 22 tablas + procedimientos + incidentes
```

### Roles y permisos

| Rol | Panel admin | Crear casos | Crear sesiones | Ver entregas | Gestionar centro |
|---|---|---|---|---|---|
| **admin** | ✓ | ✓ | ✓ (auto-aprobada) | Todas | ✓ |
| **docente** | — | ✓ | ✓ (auto-aprobada) | Sus estudiantes | ✓ |
| **instructor** | — | ✓ | ✓ (requiere aprobación) | Sus estudiantes | ✓ |
| **estudiante** | — | — | — | Solo las suyas | Ve su box |

### Base de datos (22 tablas)

- **Usuarios**: users, login_attempts, refresh_tokens
- **Casos**: cases
- **Grupos**: student_groups, group_members
- **Sesiones**: practice_sessions, practice_session_cases, session_guides, submissions
- **Agenda**: agenda_items, procedures (cartera de 17 procedimientos)
- **Centro**: boxes, center_incidents (40 templates), clinical_meetings, meeting_participants, meeting_incidents, chat_messages
- **Telemetría**: app_sessions, simulator_events, patient_encounter_stats, module_interaction_stats
- **Karime**: karime_directives
- **Feedback**: patient_feedback
- **Otros**: app_releases, assets, sync_log, time_alerts

### Cartera de procedimientos

El sistema incluye 17 procedimientos clínicos predefinidos:

| Categoría | Procedimientos |
|---|---|
| Audiología | Audiometría tonal, Logoaudiometría, Supraliminar, Impedanciometría, EOA, PEATC, Electrococleografía, Audífonos, Evaluación completa |
| Oftalmología | OCT, Campimetría, Evaluación completa |
| Vestibular | VNG, Prueba calórica, vHIT |
| General | Consulta, Control/seguimiento |

---

## 13. Larissa — Sistema de fichas clínicas

### Concepto

**Larissa** es el sistema de registro de fichas clínicas del estudiante. Es la app donde el estudiante llena los formularios con sus hallazgos, resultados de simuladores, y diagnósticos. Es distinto a "Crear Casos" (herramienta de autoría del docente).

### Versionado de pacientes

Cuando un docente crea un caso y lo asigna en una sesión práctica:

1. **Caso base** = paciente creado por el docente (perfil completo, "respuesta correcta")
2. **Versión del estudiante** = cada estudiante recibe el caso con `patientInfo` + `anamnesis`, pero los módulos de resultados llegan **vacíos**
3. **Propagación docente** = el docente puede inyectar nuevas entradas (ej: "nueva información de anamnesis") que se aplican a TODAS las versiones de los estudiantes
4. **Entrega** = el estudiante envía su versión final (snapshot) como submission al servidor

Los módulos configurables del simulador (qué patología OCT mostrar, qué defecto de campo visual) se copian del caso base para que los simuladores muestren la patología correcta.

---

## 14. Modalidad Centro — Simulación de gestión clínica

### Concepto

La **Modalidad Centro** simula un día de trabajo completo en un centro clínico real. Cada estudiante es asignado a un box con su propia agenda de pacientes, y durante la sesión surgen incidentes realistas que deben resolver individualmente o en reuniones clínicas de equipo.

Esto es **único en simulación clínica educativa** — no existe ningún simulador que cubra la gestión administrativa y operativa de un centro.

### Flujo completo

```
1. Docente crea sesión práctica
2. Configura N boxes (Box 1, Box 2, ...)
3. Asigna estudiantes a cada box
4. Crea agenda de pacientes por box (con procedimientos y duraciones)
5. Opcionalmente programa incidentes que aparecerán durante la sesión
6. Activa la sesión → los estudiantes ven su box y comienzan a atender
7. Durante la sesión: incidentes surgen, Karime avisa atrasos, pacientes se quejan
8. Reuniones clínicas: los estudiantes discuten problemas y toman decisiones
9. Al finalizar: el docente ve estadísticas, reclamos, felicitaciones, tiempos
```

### Agenda de atención

La agenda representa horarios reales del centro. El docente crea citas con:
- Nombre del paciente
- Hora exacta de llegada
- Procedimiento a realizar (de la cartera, con duración estándar)
- Estudiante asignado
- Estados: `scheduled` → `in_progress` → `completed` | `rescheduled` | `no_show`

Los estudiantes pueden **reagendar** un paciente (cambiar hora), pero esto puede generar reclamos.

### Incidentes dinámicos

40 templates de incidentes en 7 categorías que el docente puede inyectar durante la sesión:

| Categoría | Ejemplos |
|---|---|
| **Accesibilidad** | Paciente en silla de ruedas no entra a cámara sonoamortiguada, paciente con discapacidad visual |
| **Equipamiento** | Calibración vencida del audiómetro, impedanciómetro no enciende, sin olivas, auriculares obstruidos |
| **Infraestructura** | Corte de luz, filtración de agua en box, ruido de construcción afecta exámenes, baños sin agua |
| **Paciente** | Crisis de ansiedad en cámara, niño que no coopera, paciente con otitis activa, sospecha de maltrato infantil |
| **Administrativo** | Colega no vino y hay que asumir doble agenda, doble agendamiento, paciente quiere grabar consulta |
| **Bioseguridad** | Sospecha de COVID en sala de espera, falta alcohol gel |
| **Emergencia** | Paciente se desmaya (somos especialidad, no urgencias), niño convulsiona, reacción alérgica a gel conductor |

Los incidentes pueden programarse con `trigger_time_minutes` para que aparezcan automáticamente durante la sesión, o inyectarse en vivo por el docente.

### Reuniones clínicas

Los estudiantes pueden convocar o ser convocados a reuniones clínicas:
- Se vinculan los incidentes activos a discutir
- Se registran participantes, actas y decisiones
- El docente/instructor puede participar u observar
- Se notifica por chat del centro

### Karime — Secretaria IA configurable

Karime es la secretaria IA del centro. Su comportamiento es **configurable jerárquicamente**:

| Nivel | Quién configura | Alcance | Aprobación |
|---|---|---|---|
| `global` | Admin | Todo el sistema (inamovible) | — |
| `docente` | Docente | Sus actividades y estudiantes | Auto-aprobada |
| `instructor` | Instructor | Ajustes a directrices del docente | Requiere aprobación del docente |
| `session` | Instructor | Solo una sesión específica | Auto-aprobada |

**Parámetros configurables:**
- **Tratamiento**: cómo se dirige al estudiante (formal, nombre propio, custom)
- **Tono**: profesional, amigable, estricto, relajado (4 sets completos de mensajes)
- **Nivel de presión** (1-5): afecta cuándo aparecen avisos y probabilidad de quejas
- **Mensajes custom**: sobreescriben los predefinidos
- **Reglas**: texto libre con instrucciones adicionales

**Control de tiempo:**

| Evento | Karime avisa |
|---|---|
| Faltan 5 min | "Le quedan aproximadamente 5 minutos con el paciente" |
| +5 min excedido | "Ha excedido el tiempo, el siguiente paciente aguarda" |
| +15 min excedido | "15 minutos de retraso, los pacientes consultan por la demora" |
| +30 min excedido | "30 minutos de retraso, un paciente solicitó hablar con el encargado" |
| Termina a tiempo | "Atención completada en tiempo, buen trabajo" |

### Reclamos y felicitaciones de pacientes

Los pacientes simulados generan feedback automático:
- **Reclamos**: atraso, reagendamiento, exceso de tiempo, mala atención
- **Felicitaciones**: atención rápida, buen trato, diagnóstico acertado
- Cada uno con severidad (1-3) y llega al docente/instructor
- Panel de resumen: reclamos vs felicitaciones por estudiante

### Chat del centro

- Docente → estudiante individual o grupo completo
- Instructor → estudiantes de su sesión
- Estudiantes → entre ellos dentro de su grupo de box
- Tipos de mensaje: texto, sistema, incidente, convocatoria a reunión

---

## 15. Guía de instalación y desarrollo

### Requisitos previos

| Herramienta | Versión mínima | Para qué |
|-------------|----------------|----------|
| **Rust** | 1.77.2+ | Backend nativo |
| **Node.js** | 18+ | Frontend y tooling |
| **pnpm** o **npm** | Última | Gestión de paquetes JS |
| **Tauri CLI** | 2.x | Build y desarrollo |
| Compilador C/C++ | gcc/clang | llama.cpp y whisper.cpp (FFI) |
| **CMake** | 3.14+ | Dependencias nativas |
| **pkg-config** | — | Detección de librerías del sistema |

**Dependencias de sistema (Linux):**
```bash
# Debian/Ubuntu
sudo apt install libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev \
  patchelf build-essential cmake pkg-config libasound2-dev

# Arch Linux
sudo pacman -S webkit2gtk-4.1 base-devel cmake alsa-lib pkg-config
```

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/LabSim.git
cd LabSim/tauri-app

# 2. Instalar dependencias JavaScript
npm install

# 3. Desarrollo (hot reload)
npm run tauri:dev

# 4. Build de producción
npm run tauri:build
```

El build de producción genera:
- **Linux**: `.deb`, `.AppImage`, `.rpm`
- **macOS**: `.dmg`, `.app`
- **Windows**: `.msi`, `.exe`

### Credenciales por defecto

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| `admin` | `labsim2025` | Administrador |

---

## 16. Creación de módulos adicionales (Add-ons)

### Arquitectura modular

Cada módulo en LabSim es una unidad independiente compuesta por 3 archivos dentro de `tauri-app/src/modules/{nombre}/`:

```
src/modules/mi-modulo/
├── index.tsx        # Componente React principal
├── schema.ts        # Esquema Zod de validación
└── (opcional) componentes adicionales
```

### Paso 1: Definir el esquema de datos

Crear `schema.ts` con la validación Zod del módulo:

```typescript
// src/modules/mi-modulo/schema.ts
import { z } from "zod";

export const miModuloSchema = z.object({
  resultado: z.string().default(""),
  valor: z.number().min(0).max(100).default(50),
  observaciones: z.string().optional(),
});

export type MiModuloData = z.infer<typeof miModuloSchema>;
```

### Paso 2: Crear el componente

Crear `index.tsx` con el componente React:

```tsx
// src/modules/mi-modulo/index.tsx
import { useModuleForm } from "@/hooks/use-module-form";
import { miModuloSchema, type MiModuloData } from "./schema";

export default function MiModulo() {
  const { form, onSubmit } = useModuleForm<MiModuloData>({
    moduleId: "mi-modulo",
    schema: miModuloSchema,
  });

  return (
    <form onSubmit={onSubmit}>
      {/* Controles del módulo */}
      <input {...form.register("resultado")} />
      <input type="number" {...form.register("valor", { valueAsNumber: true })} />
      <button type="submit">Guardar</button>
    </form>
  );
}
```

### Paso 3: Registrar el módulo

Agregar el identificador en `src/lib/constants.ts`:

```typescript
export const MODULE_IDS = [
  // ... módulos existentes
  "mi-modulo",       // ← Agregar aquí
] as const;

export const MODULE_LABELS: Record<ModuleId, string> = {
  // ... labels existentes
  "mi-modulo": "Mi Módulo",  // ← Agregar aquí
};
```

### Paso 4: Agregar al store del paciente

Extender la interfaz `PatientData` en el store correspondiente para incluir los datos del nuevo módulo:

```typescript
// En el patient store
miModulo: MiModuloData;
```

### Paso 5 (opcional): Agregar comandos Rust

Si el módulo necesita procesamiento nativo (audio, cálculos pesados, acceso a hardware):

```rust
// src-tauri/src/commands/mi_modulo.rs

#[tauri::command]
pub fn mi_calculo(input: f32) -> Result<f32, String> {
    // Procesamiento nativo de alto rendimiento
    Ok(input * 2.0)
}
```

Registrar en `lib.rs`:

```rust
.invoke_handler(tauri::generate_handler![
    // ... comandos existentes
    commands::mi_modulo::mi_calculo,
])
```

### Convenciones

- Los IDs de módulo usan `kebab-case` (ej: `hearing-aids`)
- Cada módulo es auto-contenido: no depende de otros módulos
- Los datos se persisten automáticamente via el hook `useModuleForm`
- Los esquemas Zod aseguran validación en tiempo de compilación y runtime

---

## 17. Creación de personas IA personalizadas

### Agregar una nueva persona

Las personas se definen en `src-tauri/src/llm/personas.rs`:

```rust
pub const MI_PERSONA: Persona = Persona {
    id: "mi-persona",
    name: "Dr. García",
    system_prompt: r#"Eres el Dr. García, un otorrinolaringólogo con 20 años de experiencia...

PERSONALIDAD:
- ...

REGLAS:
- Responde SIEMPRE en español
- Mensajes de 2-5 oraciones
- NUNCA salgas del personaje"#,
    temperature: 0.6,    // 0.0 = determinista, 1.0 = muy creativo
    max_tokens: 200,     // Largo máximo de respuesta
};
```

Registrar en la función `get_persona()`:

```rust
pub fn get_persona(id: &str) -> Option<&'static Persona> {
    match id {
        "karime"      => Some(&KARIME),
        "docente"     => Some(&DOCENTE),
        "mi-persona"  => Some(&MI_PERSONA),  // ← Agregar aquí
        _ => None,
    }
}
```

### Guía para prompts efectivos

| Aspecto | Recomendación |
|---------|---------------|
| **Identidad** | Nombre, edad, profesión, años de experiencia |
| **Personalidad** | 3-5 rasgos con ejemplos concretos de comportamiento |
| **Límites** | Qué sabe y qué NO sabe el personaje |
| **Formato** | Largo de respuesta, idioma, uso de emojis, estilo |
| **Restricciones** | "NUNCA salgas del personaje", "NUNCA respondas en inglés" |

### Parámetros de generación

| Parámetro | Rango | Efecto |
|-----------|-------|--------|
| `temperature` | 0.0 — 1.0 | Baja = respuestas consistentes y predecibles. Alta = más variadas y creativas |
| `max_tokens` | 50 — 500 | Controla el largo máximo de cada respuesta |

---

## 18. Stack tecnológico completo

### Frontend

| Tecnología | Versión | Rol |
|------------|---------|-----|
| React | 19.2 | Framework UI |
| TypeScript | 5.9 | Tipado estático |
| Vite | 8.0 | Bundler y dev server |
| Tailwind CSS | 4.2 | Estilos utilitarios |
| shadcn/ui | 4.1 | Componentes UI (Radix primitives) |
| D3.js | 7.9 | Visualización de audiogramas y gráficos |
| Zustand | 5.0 | Estado global (stores) |
| React Hook Form | 7.71 | Formularios con validación |
| Zod | 4.3 | Validación de esquemas |
| TanStack Router | 1.167 | Enrutamiento tipo-seguro |
| Dexie | 4.3 | IndexedDB ORM |
| i18next | 25.8 | Internacionalización (es/en) |
| Lucide React | 0.577 | Iconografía |
| Sonner | 2.0 | Notificaciones toast |
| Geist Font | 5.2 | Tipografía |

### Backend (Rust)

| Crate | Versión | Rol |
|-------|---------|-----|
| tauri | 2.9.5 | Framework de aplicación desktop |
| cpal | 0.15 | Audio cross-platform (ALSA/CoreAudio/WASAPI) |
| llama-cpp-2 | 0.1 | Inferencia LLM (Qwen GGUF) |
| whisper-rs | 0.16 | Speech-to-text (Whisper.cpp) |
| rusqlite | 0.34 | Base de datos SQLite embebida |
| reqwest | 0.12 | HTTP client para API del servidor |
| tokio | 1 | Runtime async |
| hf-hub | 0.4 | Descarga de modelos desde HuggingFace |
| serde | 1.0 | Serialización/deserialización JSON |
| bcrypt | 0.17 | Hashing de contraseñas |
| chrono | 0.4 | Manejo de fechas |
| uuid | 1.0 | Identificadores únicos (v4) |
| thiserror | 2.0 | Error handling ergonómico |
| rand | 0.9 | Generación de números aleatorios (audio) |
| log | 0.4 | Logging estructurado |

### Backend Web (PHP)

| Tecnología | Versión | Rol |
|---|---|---|
| PHP | 7.4+ | API REST, panel admin |
| SQLite | 3 | Base de datos servidor (WAL mode) |
| JWT HS256 | Puro PHP | Autenticación sin dependencias |
| HTML/CSS/JS | Vanilla | Panel admin sin frameworks |

### Plugins Tauri

| Plugin | Función |
|--------|---------|
| tauri-plugin-fs | Acceso al sistema de archivos |
| tauri-plugin-dialog | Diálogos nativos (abrir/guardar archivo) |
| tauri-plugin-shell | Ejecución de comandos del sistema |
| tauri-plugin-log | Logging a consola y archivo |

---

## 19. Estructura del proyecto

```
LabSim/
├── tauri-app/                          # Aplicación principal (v3.0)
│   ├── src/                            # Frontend React + TypeScript
│   │   ├── App.tsx                     # Componente raíz + router
│   │   ├── routes/                     # Páginas
│   │   │   ├── login.tsx               # Autenticación
│   │   │   ├── desktop.tsx             # Escritorio virtual
│   │   │   └── clinical.tsx            # Vista clínica fullscreen
│   │   ├── modules/                    # Módulos clínicos (14 módulos)
│   │   │   ├── audiometry/             # Audiometría tonal
│   │   │   ├── logoaudiometry/         # Logoaudiometría
│   │   │   ├── impedance/             # Impedanciometría
│   │   │   ├── oae/                   # Emisiones otoacústicas
│   │   │   ├── abr/                   # Potenciales evocados
│   │   │   ├── electrocochleo/        # Electrococleografía
│   │   │   ├── supraliminal/          # Pruebas supraliminares
│   │   │   ├── hearing-aids/          # Audífonos
│   │   │   ├── oct/                   # Tomografía de coherencia óptica
│   │   │   ├── visual-field/          # Campo visual / perimetría
│   │   │   ├── patient-info/          # Datos del paciente
│   │   │   ├── anamnesis/             # Historia clínica
│   │   │   ├── agenda/                # Programación de citas
│   │   │   └── json-output/           # Exportación de datos
│   │   ├── components/                 # Componentes compartidos
│   │   │   ├── audiometer/            # Audiómetro virtual
│   │   │   ├── chat/                  # Panel de chat con IA
│   │   │   ├── clinical/             # Módulo clínico (Crear Casos)
│   │   │   ├── layout/               # Desktop, Taskbar, WindowFrame
│   │   │   ├── windows/              # Ventanas de la app
│   │   │   │   ├── audiometer-placeholder.tsx
│   │   │   │   ├── impedance-placeholder.tsx
│   │   │   │   ├── perimetry-window.tsx
│   │   │   │   ├── oct-window.tsx
│   │   │   │   ├── larissa-window.tsx     # Fichas clínicas (estudiante)
│   │   │   │   ├── center-window.tsx      # Modalidad Centro (boxes)
│   │   │   │   ├── practice-sessions-window.tsx  # Sesiones prácticas
│   │   │   │   ├── my-stats-window.tsx    # Estadísticas propias
│   │   │   │   ├── agenda-window.tsx      # Agenda de atención
│   │   │   │   ├── messaging-app.tsx      # Chat / Mensajería
│   │   │   │   ├── settings-window.tsx    # Configuración
│   │   │   │   └── window-content.tsx     # Registry de componentes
│   │   │   └── ui/                   # shadcn/ui base components
│   │   ├── stores/                     # Zustand stores (10)
│   │   │   ├── auth-store.ts          # Autenticación (login servidor)
│   │   │   ├── patient-store.ts       # Paciente + versionado
│   │   │   ├── chat-store.ts          # Conversaciones IA (Karime, Docente)
│   │   │   ├── ui-store.ts            # Estado de ventanas
│   │   │   ├── theme-store.ts         # Tema y personalización
│   │   │   ├── audio-store.ts         # Estado de reproducción
│   │   │   ├── sync-store.ts          # Conexión al servidor
│   │   │   ├── telemetry-store.ts     # Eventos + flush automático
│   │   │   ├── center-store.ts        # Modalidad Centro completa
│   │   │   └── agenda-timer-store.ts  # Timer de Karime + feedback
│   │   ├── charts/                     # Visualizaciones D3.js
│   │   ├── hooks/                      # React hooks personalizados
│   │   ├── lib/                        # Utilidades y constantes
│   │   └── locales/                    # Traducciones es/en
│   ├── src-tauri/                      # Backend Rust
│   │   ├── src/
│   │   │   ├── lib.rs                 # Entry point (48 comandos registrados)
│   │   │   ├── api/                   # HTTP client para backend web
│   │   │   │   ├── mod.rs
│   │   │   │   └── client.rs          # ApiClient (reqwest + JWT)
│   │   │   ├── commands/              # Comandos Tauri (IPC)
│   │   │   │   ├── auth.rs            # Login local
│   │   │   │   ├── patients.rs        # CRUD pacientes
│   │   │   │   ├── audio.rs           # play_tone, play_noise, stop
│   │   │   │   ├── chat.rs            # LLM chat, modelos, descarga
│   │   │   │   ├── speech.rs          # Whisper recording/transcription
│   │   │   │   ├── sync.rs            # 30 comandos API (centro, agenda, etc.)
│   │   │   │   └── telemetry.rs       # 4 comandos de telemetría
│   │   │   ├── audio/                 # Motor de audio
│   │   │   ├── llm/                   # Motor de lenguaje (llama.cpp)
│   │   │   ├── speech/                # Reconocimiento de voz (whisper)
│   │   │   ├── db/                    # Base de datos local
│   │   │   ├── models/                # Structs compartidos
│   │   │   └── utils/
│   │   ├── Cargo.toml                 # Dependencias Rust
│   │   └── capabilities/             # Permisos Tauri
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.ts
├── labsim-backend/                     # Backend web (PHP 7.4+)
│   ├── api/                            # 16 endpoints REST
│   ├── admin/                          # Panel admin (10 páginas + CSS/JS)
│   ├── core/                           # JWT, DB, auth, validators, upload
│   ├── data/                           # SQLite servidor
│   ├── uploads/                        # Guías, releases, assets
│   ├── .htaccess                       # Routing + seguridad
│   └── install.php                     # Setup inicial
├── src/                                # Legacy: PySide2 (v1.0)
├── web/                                # Legacy: documentación web (v2.0)
└── README.md                           # Este archivo
```

---

## 20. Roadmap

### Completado recientemente

- [x] **Backend web** (PHP 7.4+ / SQLite): 16 endpoints REST, panel admin, JWT, 22 tablas
- [x] **Larissa**: sistema de fichas clínicas del estudiante con versionado de pacientes
- [x] **Modalidad Centro**: simulación de gestión de centro clínico con boxes, agenda real, incidentes dinámicos (40 templates), reuniones clínicas, chat grupal
- [x] **Karime configurable**: directrices jerárquicas (admin > docente > instructor > sesión), 4 tonos, 5 niveles de presión
- [x] **Telemetría**: tracking de eventos por simulador, tiempos por módulo, flush automático cada 30s
- [x] **Feedback de pacientes**: reclamos y felicitaciones automáticos, panel de resumen para docentes
- [x] **Cartera de procedimientos**: 17 procedimientos clínicos con duración estándar y equipo requerido
- [x] **Sesiones prácticas**: flujo completo docente→instructor→estudiante con aprobación, guías, entregas, calificación
- [x] **Conexión servidor**: login JWT, indicador de conexión en tiempo real, sync de casos y agenda
- [x] **Rol instructor**: nuevo rol intermedio entre docente y estudiante

### Corto plazo — Consolidación

- [ ] Deploy del backend a tmeduca.org
- [ ] Pacientes virtuales con patologías pre-configuradas y respuestas automáticas
- [ ] Streaming de tokens LLM (respuesta en tiempo real, no batch)
- [ ] Estéreo real: canal izquierdo / derecho independiente para simular lateralidad
- [ ] Exportación de informes en PDF con formato clínico estándar

### Mediano plazo — Expansión otoneurológica y oftalmológica

- [ ] **vHIT** (Video Head Impulse Test): simulación de respuestas por canal semicircular
- [ ] **VNG / Videonistagmografía**: nistagmo espontáneo, posicional y calórico
- [ ] **VEMP**: potenciales evocados miogénicos vestibulares
- [ ] **Posturografía**: control postural con análisis sensorial
- [ ] **Tonometría**: presión intraocular
- [ ] **Fondo de ojo**: retinografía simulada con patologías
- [ ] Personas IA de pacientes otoneurológicos (vértigo, Ménière, VPPB)
- [ ] Personas IA de pacientes oftalmológicos (glaucoma, diabético)

### Largo plazo — Plataforma multidisciplinaria

- [ ] **Marketplace de casos clínicos**: docentes crean y comparten pacientes virtuales
- [ ] Soporte GPU (CUDA/Metal) para inferencia LLM acelerada
- [ ] Calibración acústica real con micrófono de referencia
- [ ] Integración NOAH (estándar de la industria audiológica)
- [ ] Aplicación móvil (Tauri 2 soporta iOS/Android)
- [ ] Módulos para nuevas especialidades: fonoaudiología, neurofisiología, neumología
- [ ] Integración con LMS (Moodle, Canvas) para calificación automática

---

<p align="center">
  <sub>LabSim 3.0 — Plataforma de simulación clínica educativa</sub><br>
  <sub>Audiología · Otoneurología · Oftalmología · y más</sub><br>
  <sub>Desarrollado con Tauri, React y Rust — Licencia MIT</sub>
</p>
