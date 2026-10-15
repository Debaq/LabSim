# Inventario: ¿qué haría falta para un libro vestibular y uno nasal?

Revisión de solo lectura hecha el 2026-10-15 sobre los proyectos hermanos en
`~/Escritorio/Proyectos/`. No se compiló, instaló ni ejecutó nada de esos
proyectos. Los respaldos de Moodle se abrieron en un directorio temporal, fuera
del repositorio. Lo que no se pudo confirmar va marcado con **(sin verificar)**.

Punto de partida: el motor del libro (`docs/libro/figuras/motor/`) es Python.
Importa los motores de la app (`src/vemp`, `src/abr`…) con una semilla estable
(blake2b) y dibuja SVG con su propia clase `Svg`. Cada figura sale de un
`cases.data` de LabSim. Cualquier fuente nueva tiene que encajar en ese
esquema: **datos de un motor real → SVG**.

---

## 0. Resumen en una tabla

| Proyecto | Qué es | Madurez | Genera datos sintéticos de pacientes | Figuras para el libro | Licencia / DOI | Enganche al motor |
|---|---|---|---|---|---|---|
| **LabSim** (VEMP) | Módulo VEMP + eje `vemp` del caso | En producción ("pre") | Sí, desde `cases.data` | cVEMP/oVEMP (ya en H12 y cap. 20) | (la del repo) | **Hecho** (`motor/vemp.py`) |
| **LabSim** (VNG/VHIT/POS) | Solo marcadores en `Layout.php`, estado `development`, Box_3 "Otoneurología" inactivo | Vacío | No | — | — | Habría que construirlo |
| **labyrinthus3d** | Simulador 3D docente: canales, otolitos, vía VOR/VSR, VPPB, pruebas provocadas, oculomotor, postural | Alta (132 commits, ~26 archivos de test con `node --test`) | **Sí, a partir de un modelo por sitio anatómico** (sin guiones por enfermedad) | Nistagmo espontáneo/posicional, calórica + Jongkees, oculomotor, VPPB, VEMP, Romberg/mCTSIB/SOT/Fukuda | Apache-2.0 · **sin DOI** | **Medio**: módulos ES puros sin DOM; se pueden llamar desde Node |
| **simHit** | Simulador vHIT con gafas IMU propias y paciente virtual programable | Media-alta (156 commits) | Sí: 17 casos predefinidos, 6 canales | Velocidad cabeza/ojo, sacadas covert/overt, tabla de ganancias, artefactos | **Inconsistente**: `LICENSE` = Apache-2.0; README, `.zenodo.json` y `CITATION.cff` = MIT · DOI 10.5281/zenodo.20160851 | **Bajo**: el modelo del ojo es una gaussiana más una sacada gaussiana; se porta a Python en pocas líneas |
| **trainHIT** | vHIT didáctico en el navegador (webcam a 30 fps, MediaPipe) + paciente simulado | Alta (144 commits, CI, manual, artículo en preparación) | Sí: 5 casos a ciegas + perfiles simulados + banco sintético (`test/sintetico.mjs`) | Paneles vHIT, ganancia contra pico, 3 métodos de ganancia, efecto del paralaje | Apache-2.0 · DOI 10.5281/zenodo.23106742 | **Bajo-medio**: ya tiene scripts Python de figuras para el artículo (`docs/articulo/figura1`, `figura2`) |
| **vhit-wout-google** | vHIT nativo en Rust (webcam), suite con Posturografox | Media (96 commits) | No (solo un pipeline sintético de prueba) | Aporta método: `GANANCIAS.md`, `VALIDACION.md`, `REGULATORIO.md` | Apache-2.0 · sin DOI | No hace falta: es fuente de texto, no de figuras |
| **Siev** | Estación clínica VNG real (Tauri+React+Rust): calórica, posicional, oculomotor, audiometría, postural | Media-alta (145 commits) en captura y análisis | **No**: mide pacientes reales, no simula | Convenciones de gráfico: diagramas calóricos de **Claussen, Freyss y mariposa**, línea de tiempo de VFL, ganancia de seguimiento, nube de sacadas | MIT (README) | **Medio**: se reimplementan sus gráficos en Python; los datos tienen que venir de otro motor |
| **vng** | Prototipo VNG viejo en PySide6 (v0.0.2) + entrenamiento YOLO | Abandonado / reemplazado por Siev | No | `DetectorNistagmo.py` (detección de fase rápida y cálculo de VFL) como referencia | MIT | No conviene |
| **siev_vng_models** | Pesos YOLOv8n del detector de iris (SIEV-iris r01.1) | Publicado | No aplica | No aplica | AGPL-3.0 · DOI 10.5281/zenodo.23106567 | No aplica |
| **cvemp** | App Rust de captura para un VEMP de hardware propio (ESP32-S3) | Temprana (2 commits) | Solo un firmware simulado (`sim.rs`) | Fotos del equipo, nada más | Sin archivo LICENSE **(sin verificar)** | No aplica (el VEMP del libro ya sale de LabSim) |
| **posturografox** | Posturógrafo de 4 celdas (ESP32-C3+HX711) + app Rust: COP, elipse 95 %, CTSIB, límites de estabilidad, juego | Media-alta (89 commits) | Simulador de balanceo **sin patología** (sinusoides de 0,2–1,2 Hz más ruido) | Estatocinesigrama, elipse, métricas, cocientes del CTSIB | MIT · sin DOI | **Medio**: reimplementar métricas y gráficos; los pacientes tienen que venir de labyrinthus3d |
| **posturografo** | Versión anterior en Python/PySide6 | Reemplazada por posturografox | No | — | Sin licencia | No conviene |
| **otoneuro_moodle** | Respaldo del curso ETMP174 + programa + GIFT | Curso 2026-2 en marcha | — | Viñetas de caso, tablas periférico/central | Material del autor; unidades II y III son de colegas | Fuente de texto |
| **nasal** | Respaldos de 3 cursos (ETMP172, ETMP182, INGI152) | — | **Ningún simulador nasal** | — | Material de la colega, "all rights reserved" | No hay nada que enganchar |

---

## 1. Proyecto por proyecto

### 1.1 LabSim: lo vestibular que ya existe

- **Módulo VEMP** (`src/vemp/`, unas 2 450 líneas): cVEMP, oVEMP y mVEMP,
  promediado en vivo, corrección por EMG, vía ósea con el gap del audiograma y
  sintonía invertida por debajo de 55 dB (la firma de la dehiscencia,
  `UMBRAL_SINTONIA_INVERTIDA` en `patient.py`). Las figuras ya salen del motor:
  `docs/libro/figuras/motor/vemp.py`, usadas en H12 y en el cap. 20.
- **Eje `vemp` en `CaseProfile::SCENARIOS`** (76 cuadros): los tipos son
  `normal` (31 cuadros, casi todos con `umbral_gap` por ser conductivos),
  `neural` (12: laberintitis, fractura transversal, parotiditis, osificación,
  schwannoma, NF2…) y `sacular` (2: Ménière e hidrops retardado). `utricular`
  existe en `CaseBuilder::VEMP_TYPE_OPTIONS`, pero ningún cuadro lo usa. Hay
  `vemp.lat_ms` para lo central (EM, CMT, kernícterus). Que la súbita y la
  ototóxica no tengan regla vestibular **es una decisión documentada**, no un
  olvido.
- **No hay eje vestibular aparte del VEMP.** Ningún cuadro dice nada de
  canales, vHIT, calórica, nistagmo ni VPPB. Tampoco existen cuadros
  puramente vestibulares (neuritis, VPPB, migraña vestibular, bilateral,
  PPPD).
- **Marcadores de módulo** en `labsim_backend/src/Layout.php`: `VNG`
  (Videonistagmografía), `VHIT` y `POS` (Posturografía), los tres en estado
  `development`, dentro de `Box_3` "Box Otoneurología", que está inactivo.
- **El libro**: `capitulos/H13-evaluacion-vestibular.md` es un esqueleto vacío
  (53 líneas de "✍") y su `.py` no declara casos. B1 (Fisiología, a cargo de
  una colega) ya promete "el sistema vestibular". En `investigacion/`,
  `tecnica_b.md` tiene 15 menciones vestibulares (VEMP) y `fisiologia.md`, 6.
- **Protocolo técnico ORL 2019** (`docs/libro/fuentes/`, privado, 186 págs.):
  tiene una sección de **Otoneurología** con examen con lentes de +20 D
  (p. 109), VNG (p. 116), calórica mínima con VNG (p. 122), rehabilitación
  vestibular (p. 127), maniobras de reposición (p. 136), cVEMP (p. 144), oVEMP
  (p. 149) y vHIT (p. 154). Tiene también una sección de **Rinología**:
  anamnesis y rinoscopía (p. 82), rinomanometría anterior (p. 85) y rinometría
  acústica (p. 89). **No trae posturografía ni olfatometría.** Es la base
  natural de la "Técnica" de ambos volúmenes, igual que hoy lo es para el
  libro auditivo.

### 1.2 labyrinthus3d: el candidato fuerte para las figuras vestibulares

- **Qué es.** Un simulador 3D en el navegador (three.js, módulos ES) con
  cabeza, ojos y los dos laberintos. Nació dentro de trainHIT y se mudó a
  repositorio propio el 2026-09-27. Está publicado en
  tecmedhub.org/labyrinthus3d. Trae un checklist de revisión clínica pensado
  para ETMP174.
- **Modelo de patología** (`js/patologia.js`): no tiene guiones por
  enfermedad. Cada sitio (canales, otolitos, ramas superior e inferior del
  nervio, núcleos vestibulares, FLM, flóculo, integrador…) tiene una función
  entre 0 y 1, y lo que llega al ojo es el producto del camino. A eso se suman
  la ley de Ewald II, la compensación según los días desde la lesión (de horas
  a 3 meses) y las sacadas covert, overt, overt tardías o mixtas según el
  tiempo. El nistagmo espontáneo es 3D, con freno por fijación (OFI) y un
  freno que depende del flóculo.
- **Casos armados.** Neuritis superior e inferior, pérdida unilateral,
  hipofunción lateral, infarto de la AICA, lesión de los núcleos,
  oftalmoplejía internuclear, degeneración cerebelosa, nistagmo evocado por la
  mirada, upbeat, parálisis de la mirada horizontal, hipofunción y arreflexia
  bilaterales, hidrops (Ménière: "la calórica cae y el impulso no"),
  dehiscencia, fístula, y en lo postural polineuropatía, cordones
  posteriores, vermis anterior, déficit multisensorial y **PPPD**. Todos con
  modo "paciente a ciegas / Revelar".
- **VPPB** (`js/vppb.js`): canalitiasis y cupulolitiasis en los 3 canales, con
  física de partículas, latencia, crescendo-decrescendo, inversión y fatiga, y
  posicional central para diferenciar. Pruebas: Dix-Hallpike, rolido en
  supino, cabeza colgando. Maniobras: Epley, Semont, Lempert, Gufoni, Zuma e
  Maia, Appiani y Yacovino. Hay un dibujo 2D del canal, pero en canvas.
- **Pruebas provocadas** (`js/provocadas.js`): **calórica** (convección con
  latencia de unos 20 s y pico a unos 60 s, COWS, invertida en prono) con
  `jongkees()` (paresia > 25 %, preponderancia > 30 %), vibración mastoidea,
  hiperventilación, Hennebert, Tullio y VEMP.
- **Oculomotor** (`js/oculomotor.js`, `js/estimulo.js`): sacadas (latencia,
  ganancia, dismetría), seguimiento, optocinético, intrusiones, silla
  rotatoria y trazas de los dos ojos. `test/examen.mjs` **ya corre un examen
  oculomotor entero sin DOM** y devuelve muestras cuadro a cuadro.
- **Postural** (`js/postural.js`): péndulo invertido (Peterka 2002) con
  repesada sensorial, Romberg, mCTSIB, **SOT con sus 6 condiciones**, análisis
  sensorial y puntaje compuesto, patrón del SOT, Fukuda y lateropulsión. Las
  funciones `prueba()` y `posturografia()` reciben una **semilla**.
- **Datos.** Todo es sintético y sale del modelo. No hay pacientes reales. La
  malla `modelos/cabeza.glb` es solo local (está en `.gitignore`) y su origen
  y licencia no constan **(sin verificar)**. La cabeza implícita de
  `js/cabeza.js` sí es propia.
- **Advertencia del propio README:** "las constantes dan los órdenes de
  magnitud de la clínica, no más". **No son valores normativos.** Para el
  libro habría que calibrar contra literatura y citar, como se hizo con el ABR.
- **Enganche al motor.** Medio. Los módulos son ES puros y ya corren en Node
  (26 archivos de test). Hay dos caminos: (a) un puente
  `node figuras/motor/vestibular.mjs <caso.json>` que devuelva JSON y que el
  motor Python dibuje, o (b) portar a Python las funciones que hagan falta
  (patología, calórica, postural). (a) agrega Node a la cadena del libro. (b)
  duplica un modelo vivo.

### 1.3 simHit

- **Qué es.** "Simulador para enseñar el Head Impulse Test". Unas gafas con
  IMU (giroscopio, acelerómetro y magnetómetro a 200 Hz), del mismo peso y
  forma que unas clínicas, se le ponen a un compañero, y el software genera la
  respuesta ocular del caso cargado. App en Tauri 2 + SvelteKit.
- **Contenido clínico.** Seis canales (LL, RL, LA, LP, RA, RP; los planos
  verticales LARP y RALP desde la fase F1), ganancia, sacadas `none`, `covert`
  u `overt`, y artefactos (dirección errónea, overshoot, pérdida de
  fijación…). Valida cada impulso (amplitud, pico, duración, plano) y arma un
  informe vHIT en PDF. Trae **17 casos de ejemplo**: normal, hipofunción
  derecha e izquierda overt, derecha covert, bilateral parcial, severa, leve,
  compensación post-aguda, examen con artefactos, mixto progresivo, cada canal
  vertical por separado, planos RALP y LARP, y global de 6 canales.
- **Modelo.** Es simple y explícito (`simulator.svelte.ts`). La cabeza es una
  gaussiana y el ojo es `-dir·pico·ganancia` con 7 ms de retraso. La sacada
  covert o overt es otra gaussiana con amplitud `pico·(1−g)·1,2` o `1,5`. **Se
  porta a Python en unas decenas de líneas.**
- **Datos.** `datasets/` está vacío ("pendiente", con CC-BY-4.0 planificada).
  No hay datos reales en el repositorio.
- **Licencia.** Ver la tabla: hay que resolver la contradicción entre
  Apache-2.0 y MIT antes de citarlo.

### 1.4 trainHIT

- **Qué es.** vHIT "didáctico" que corre en el navegador con la webcam. Tiene
  un tope deliberado de 30 fps para que no se use con pacientes. Calibra el
  paralaje y muestra 3 métodos de ganancia (área, instantánea a 60 ms,
  cociente de picos). Detecta sacadas, rechaza impulsos con su motivo y exporta
  CSV y preguntas GIFT. Tiene manual en PDF (español e inglés) y un artículo
  en preparación para *Advances in Physiology Education*.
- **Lo sintético.**
  - `js/ejemplo.js` tiene un paciente de ejemplo y **5 casos a ciegas**:
    normal; déficit derecho overt; bilateral; déficit izquierdo covert, que la
    media lee como normal (el falso negativo); y casi todo rechazado.
  - `js/simulacion.js` pone una patología sobre pulsos reales de un compañero
    sano: neuritis derecha o izquierda (g 0,35–0,55 con overt a 200–340 ms),
    déficit compensado (covert a 95–110 ms), bilateral (0,30–0,50) y control
    sano.
  - `test/sintetico.mjs` es un banco con ganancia conocida. Con k = 0, un VOR
    perfecto se lee 1,95.
- **Datos reales.** `docs/articulo/figura1/sesion_figura1.csv` es una sesión
  de **uno de los autores**, que según el README autorizó publicarla. Trae
  solo números.
- **Figuras.** `make_figure1.py` (calibración del paralaje: el mismo pulso
  con k y con k = 0) y `make_figure2.py` (diagrama del pipeline, en SVG). El
  patrón ya es el del libro: Python que llama al motor JS y escribe SVG.
- **Útil para el libro, sobre todo** en el capítulo de "cuando el problema es
  la técnica" (paralaje, impulsos predecibles, sesgo al falso negativo de las
  covert).

### 1.5 vhit-wout-google

vHIT nativo en Rust con webcam (MediaPipe). Su valor para el libro es el
**texto técnico**: `GANANCIAS.md` (el método de ganancia comparado con los
equipos comerciales y el origen del corte de 0,80), `VALIDACION.md`,
`REGULATORIO.md` ("herramienta de investigación, no dispositivo médico") y
`SUITE.md` (comparte la base SQLCipher con Posturografox). En
`rust/exportado/` hay dos exámenes `vhit_nico_*` (CSV, JSON y PDF), que son
**pruebas del propio autor** ("paciente: nico"). No tienen datos clínicos de
terceros, pero no conviene publicarlos sin decidirlo. `banco/portrait.jpg` es
un retrato que parece la imagen de muestra de MediaPipe **(sin verificar, no
se abrió)**.

### 1.6 Siev (VNG clínica)

- **Qué es.** Estación de trabajo real: cámaras duales a 120–240 fps,
  detector matemático de pupila con anclaje YOLO cada N cuadros, Kalman de 6
  estados, análisis de batidas (`vng/nystagmus.rs`), calórica bitérmica o
  monotérmica (tibia o fresca) con **Jongkees** y su método de cálculo
  seleccionable, posicional (Dix-Hallpike bilateral, tipo, dirección e
  intensidad del nistagmo, canal afectado), oculomotor (sacadas, seguimiento
  por dirección, OKN), estabilometría, audiometría e informe PDF. El trabajo
  actual va hacia un artículo de seguimiento ocular (`HANDOFF.md`,
  `NOTAS_HALLAZGOS.md`).
- **No simula pacientes.** No hay generador sintético. Los datos salen de
  capturas reales y no hay ninguna versionada.
- **Lo que sirve para el libro:**
  - Las **convenciones de informe**: `CaloricDiagram.tsx` en estilos
    `claussen`, `freyss` y `butterfly`, más `SPVTimelineDiagram`,
    `PursuitGainDiagram`, `SaccadeScatterDiagram` y `NystagmusSummaryDiagram`.
    Son el modelo de lo que el motor Python tendría que dibujar.
  - Las fotos y capturas del equipo para "Antes de empezar".
- **Datos sensibles.** `fixtures/seq_eyes_800/` tiene 800 cuadros PGM de ojos
  en disco. El README dice que vienen de un "registro de depuración, datos
  ficticios": el nombre es ficticio, pero **los ojos son de una persona real**
  (probablemente del equipo). No usarlos en el libro sin consentimiento
  explícito.

### 1.7 vng y siev_vng_models

- **vng**: el prototipo PySide6 previo a Siev, abandonado. Lo único
  rescatable es `src/utils/DetectorNistagmo.py` (fase rápida por umbral de
  velocidad y VFL, con scipy) como referencia de algoritmo.
  **⚠ `train/capture/` tiene unas 500 imágenes `eye_image_*.jpg`**, más
  `train/xml/` y los datasets YOLO, capturadas con `capture.py`.
  Probablemente son ojos de personas reales del laboratorio **(sin verificar,
  no se abrieron)**. No usar.
- **siev_vng_models**: pesos del detector de iris, publicados en Zenodo con
  AGPL-3.0. Lo entrenó Vanessa Uribe-Hernández sobre MPIIGaze, cuyas imágenes
  no se redistribuyen. No genera figuras clínicas.

### 1.8 cvemp

App Rust (egui) que controla un VEMP de hardware propio (ESP32-S3, JSON por
serie a 921 600 baudios), promedia las épocas y las exporta en CSV. Está en
fase temprana: 2 commits y un `sim.rs` que imita el firmware. Para el libro
solo sirve como **foto del equipo de laboratorio**. El VEMP del libro sigue
saliendo del motor de LabSim.

### 1.9 posturografox (y el viejo posturografo)

- **posturografox.** Plataforma de 4 celdas. Calcula el COP con su elipse de
  confianza del 95 %, área, velocidad media, velocidades ML y AP, RMS, rango,
  los **cocientes del CTSIB** (`estabilometria.rs`), límites de estabilidad
  (`limites.rs`, `maniobras.rs`), un espectro, un juego de rehabilitación e
  informes. Tiene base compartida con vHIT, cifrada con SQLCipher, y una nota
  de privacidad. Con `--simular` genera un balanceo sin patología, **sin
  ningún modelo clínico**.
- **posturografo.** La app anterior en PySide6. El único dato es una sesión
  de prueba `.posx` con RUT "1234" y nombre vacío. Sin datos personales.
- **Para el libro:** las métricas y el formato del informe salen de
  posturografox. Los pacientes (SOT, mCTSIB, Romberg patológico) los genera
  labyrinthus3d.

---

## 2. Cursos en los respaldos de Moodle

### 2.1 ETMP174 "Fundamentos en Otoneurología" (`otoneuro_moodle/`)

Moodle 4.5, semestre 2026-2. Es un curso **teórico de neurofisiología** (25,5
h teóricas y 0 prácticas), no de técnica vestibular. Su prerrequisito es
**ETMP162 "Morfofisiopatología cocleovestibular y nasal"**, del que no hay
respaldo. El respaldo trae 0 usuarios. Hay 4 variantes del `.mbz` (normal,
PLANO, SIN-cuestionario y `.bak`); se revisó la normal.

| Unidad (docente según el programa) | Clases | Contenido en el respaldo |
|---|---|---|
| I. Generalidades e introducción (N. Baier) | 1 Neuroanatomía de la vía auditiva · 2 **Neuroanatomía de la vía vestibular** · 3 Transmisión sináptica audiovestibular · 4 **Correlación anatomo-clínica** · Prueba 1 (33 %) | **Completo**: 15 páginas y un quiz de 60 preguntas (más `preguntas-prueba1.gift`) |
| II. Procesos neurológicos de la audición (G. Casanova) | 6–9: núcleos cocleares, COS y lemnisco lateral, colículo, corteza · Prueba 2 (33 %) | Solo títulos, vacío |
| III. Procesos neurológicos vestibulares (P. Poza) | 11 **Reflejos vestíbulo-oculares** · 12 **Vestíbulo-espinales y control postural** · 13 Núcleos, cerebelo y tronco · 14 Tálamo y corteza vestibular · Prueba 3 (34 %) | Solo títulos, vacío |

Las páginas que sirven para sembrar capítulos (todas del autor):

- **2.1 "El sistema vestibular, nivel por nivel"**: seis niveles (laberinto,
  nervio, núcleos, cerebelo, corteza, eferentes/reflejos) con la prueba que
  interroga cada uno. Es buen esqueleto para los bloques de Fisiología.
- **2.2 "Referencia rápida"**: tabla periférico / central / cortical
  (nistagmo espontáneo, Romberg, vHIT…).
- **2.3 "Cinco casos vestibulares"**, con resolución:
  - A, el abuelo que se cae hacia un lado (vértigo agudo hace 3 días)
  - B, la bailarina con vértigo posicional
  - C, el ACV de cerebelo
  - D, el niño con otitis y desequilibrio
  - E, vértigo y acúfeno unilateral

  Son viñetas listas para el formato ABP del libro.
- **3.2 "El cáliz y la codificación"**: un caso de ototoxicidad por
  gentamicina con oscilopsia.
- **3.4 "Plasticidad"**: neuritis y compensación.
- **4.1 "Correlación anatomo-clínica"**: signos periféricos frente a
  centrales del nistagmo y **cuándo sirve el HINTS y cuándo no**.
- **4.2 "Banderas rojas"**: la lista de cuándo deja de ser ambulatorio.

### 2.2 Carpeta `nasal/`

| Respaldo | Qué curso es | ¿Sirve? |
|---|---|---|
| **etmp172** | **"Métodos de Exploración Nasorespiratorio"** (2026-2, docente TM ORL **Vanessa Uribe**) | **Sí: es el curso nasal** |
| etmp182 | "Salud Ocupacional" (docente N. Baier): conceptos, Ley 16.744 / DS 101 / DS 109, y **evaluación auditiva y ruido** (PREXOR/PEECCA, DS 594, DS 38, NCh 1619) | No para lo nasal. Sí para el libro **auditivo** (H3 ocupacional, cap. 6 ruido) |
| ingi152 | "Política Pública: Derechos Humanos y Enfoque de Género" | **No tiene relación.** No se abrió más allá del título |

Estructura de **ETMP172** (sin usuarios en el respaldo):

- **Unidad I, "Anamnesis, rinoscopía, rinomanometría pre y post ejercicio,
  posicional"**:
  - Guías de estudio: Clase 1 (anatomía y fisiología nasal), Clase 2 (Cottle
    y Broms), Clase 3 (rinoacústica) y Clase 4 (prick test y alergias).
  - Guías prácticas: rinoscopía, rinomanometría (equipo **Athmos
    Rhinomanometer 300**: RAA y posterior, resistencia uninasal, RNT, IRNT,
    gráfico polar) y rinometría acústica (**RHIN 2000**: área de sección
    contra distancia, MCA, protocolo ISCOANA).
  - Un video de configuración del rinomanómetro.
  - **Ejercicios de rinomanometría**: 8 casos con presión y flujo a 150 Pa en
    reposo, decúbitos, PVC y FND. Son solo números, sin nombres.
  - Formularios de examen y una **prueba práctica 1**, que es una rúbrica de
    69 puntos en blanco.
  - Preguntas formativas.
- **Unidad II, "Vías respiratorias, mecánica ventilatoria, SAHOS y
  polisomnografía"**: guía de la Clase 5 (espirometría, GLI-2012), guía de la
  Clase 6 (SAHOS) y guías clínicas MINSAL (asma, SAHOS).
- **Banco**: 79 preguntas en las categorías anatomía y fisiología, Cottle y
  Broms, rinoacústica, prick test y "cálculo de resistencia nasal".
- **Lecturas**: unos 40 PDF de terceros (Vergara 2002/2003 y Finkelstein
  2009 de rinometría acústica en Chile, Mamikoglu 2002, Lacroix 2009, Mygind
  1998, Armengol PSG, GLI-2012…). Tienen derechos de autor: **se citan, no se
  reproducen.**
- **Derechos:** las guías propias figuran con autoría de *Vanessa Soledad
  Uribe Hernández* y licencia **"allrightsreserved"** en Moodle.
- **Olfato:** solo aparece de pasada (una pregunta sobre "las cinco funciones
  de la nariz" y el ítem de la anamnesis). **No hay olfatometría en ningún
  proyecto ni curso revisado.**

Fuera de `nasal/`, en `Proyectos/` no hay ningún proyecto de rinomanometría,
rinometría ni olfatometría. `labnas` es un NAS de almacenamiento y no tiene
relación.

---

## 3. Índice propuesto

### 3a. Vestibular: ¿Parte IX o Volumen 2 "Otoneurología"?

**Recomendación: Volumen 2.** Las razones:

- **Tamaño.** Con unas 9 herramientas y unos 12 capítulos clínicos, sería un
  libro tan grande como el actual.
- **Batería distinta.** La anamnesis, el examen a pie de cama y los equipos
  no son los del libro auditivo.
- **Otra procedencia de las figuras.** Hoy saldrían en buena parte de motores
  que no son LabSim (ver la decisión 2).
- **Mismo formato.** El volumen 2 puede reusar la misma maquinaria
  (`libro.py`, `hacer_libro.py`, el motor y el formato ABP).

H12 y el cap. 20 (VEMP) pueden **quedarse en el volumen 1 y citarse desde el
2**, o mudarse. Si en cambio se elige una **Parte IX**, bastaría con
promover H13 y fundir los capítulos en 4 o 5.

En la tabla de abajo, **L3D** = labyrinthus3d, **sH** = simHit, **tH** =
trainHIT, **PX** = posturografox y **LS** = LabSim.

#### Caja de herramientas (V-H)

| # | Herramienta | Contenido | Figuras: de dónde salen | Base técnica |
|---|---|---|---|---|
| VH1 | Anamnesis del mareo y examen a pie de cama | Tiempo y desencadenante (episódico, agudo continuo, crónico); DHI; Frenzel +20 D; Romberg; Fukuda; impulso cefálico clínico; head-shake; HINTS | Nistagmo espontáneo y de mirada desde L3D; ilustraciones | Protocolo 2019 p. 109; ETMP174 4.1–4.2 |
| VH2 | Videonistagmografía: calibración, espontáneo, mirada, fijación (OFI) | Trazas de posición (diente de sierra), VFL, OFI | L3D (patologia.js + estimulo.js); convenciones de Siev (SPVTimeline, NystagmusSummary) | Protocolo p. 116 |
| VH3 | Oculomotor: sacadas, seguimiento, optocinético | Latencia, ganancia y precisión de sacadas; ganancia de seguimiento; OKN; intrusiones | L3D (`test/examen.mjs` ya lo corre sin DOM); gráficos al estilo de Siev (PursuitGain, SaccadeScatter) | Protocolo p. 116 |
| VH4 | Posicionales y maniobras de reposición | Dix-Hallpike, rolido en supino, cabeza colgando; Epley, Semont, Lempert, Gufoni, Zuma, Appiani, Yacovino | L3D `vppb.js` (nistagmo con latencia, fatiga e inversión; el canal 2D redibujado en SVG) | Protocolo p. 136 |
| VH5 | Prueba calórica | Bitérmica y mínima con VNG, Jongkees, preponderancia, OFI, diagramas de Claussen, Freyss y mariposa | L3D `calorica()`, `jongkees()`; diagramas de Siev reimplementados | Protocolo p. 122 |
| VH6 | vHIT | Técnica del impulso, 6 canales, ganancias, covert/overt, artefactos, métodos de ganancia | sH (modelo portado) o tH (sintético); tabla de ganancias; LARP/RALP | Protocolo p. 154; `GANANCIAS.md`; manual de tH |
| VH7 | VEMP | → **H12 actual** | LS (hecho) | — |
| VH8 | Posturografía | Romberg cuantificado, mCTSIB, SOT (6 condiciones), límites de estabilidad | PX (métricas, elipse) + L3D (`prueba()`, `posturografia()` con semilla) | **No está en el protocolo 2019** → hay que escribirlo desde la literatura |
| VH9 | Pruebas complementarias *(opcional)* | Vibración, hiperventilación, Hennebert, Tullio, silla rotatoria | L3D `provocadas.js` | — |
| VH10 | Rehabilitación vestibular *(¿dentro?)* | — | PX (modo juego) | Protocolo p. 127. Es tratamiento, no evaluación (ver decisión 8) |

Falta en todos los proyectos: **SHIMP** (0 menciones), **test de supresión
visual del VOR con vHIT**, **vibración con registro** y **SVV / vertical
visual subjetiva**.

#### Capítulos clínicos (V1…)

| # | Problema | Cuadros | Batería con figura | Cuadro ya en LS |
|---|---|---|---|---|
| V1 | El vértigo agudo que no para | Neuritis superior / inferior / total; laberintitis; **ACV que la imita** (AICA, PICA) | VNG espontáneo, HINTS, vHIT, calórica, VEMP | `laberintitis`, `infarto_aica` (VEMP) |
| V2 | Vértigo al acostarse | VPPB posterior, lateral geotrópico y apogeotrópico, anterior; cupulolitiasis; posicional central | Posicionales, traza del nistagmo | — |
| V3 | Crisis con oído tapado | Ménière (la calórica cae y el vHIT no), hidrops retardado | Calórica frente a vHIT, ECochG, VEMP, audiograma fluctuante | `meniere`, `hidrops_retardado` (**la mejor integración**: audiología + ECochG + VEMP ya están) |
| V4 | Migraña vestibular | Diagnóstico por criterios, batería a menudo normal entre crisis | Pocas figuras (normales) | — **(no hay generador específico)** |
| V5 | Se le mueve el mundo al caminar | Hipofunción bilateral: gentamicina, idiopática, presbivestibulopatía | vHIT bilateral, calórica baja, posturografía (condición 5 del SOT) | `ototoxica` (VEMP normal a propósito, a revisar) |
| V6 | Cuando el ojo dice "central" | Oftalmoplejía internuclear, down/upbeat, evocado por la mirada, cerebelo, núcleos | VNG de mirada, oculomotor | `esclerosis_multiple`, `infarto_pontino`, `chiari_hic` (solo eje auditivo y VEMP) |
| V7 | La tercera ventana | Dehiscencia del canal superior, fístula perilinfática | Tullio, Hennebert, VEMP con umbral bajo, ósea supranormal | VEMP con sintonía invertida ya está; **ósea supranormal = TODO 40** |
| V8 | El schwannoma desde el equilibrio | Calórica débil con vHIT conservado, VEMP | Calórica, vHIT, VEMP | `schwannoma`, `nf2`, `tumor_angulo` |
| V9 | Tres meses después | Compensación, covert que esconden el déficit, descompensación por hiperventilación | vHIT con covert (falso negativo), posturografía | — |
| V10 | Mareo que no se explica | PPPD, déficit multisensorial y caídas del adulto mayor, preferencia visual | Posturografía (SOT), batería normal | — |
| V11 | El niño que se marea | VPPI, migraña, laberintitis serosa (caso D de ETMP174) | Limitado | parcial (`otitis_media`, `laberintitis`) |
| V12 | Cuando el problema es la técnica | vHIT: paralaje sin calibrar (1,95), impulsos predecibles, deslizamiento de gafas, parpadeo; calórica: tímpano, temperatura, alerta; VNG mal calibrada | tH, sH (artefactos), L3D | — |
| V13 | Casos integradores | Los 5 casos de ETMP174 2.3, rehechos con figuras | todos | — |

### 3b. Nasal: un volumen aparte

**Lo que existe:**

- El curso ETMP172, que no es del autor.
- El protocolo 2019 (rinoscopía, rinomanometría anterior, rinometría
  acústica).
- Los 8 ejercicios de rinomanometría (solo números).
- La lista de lecturas, que sirve como semilla de bibliografía.

**Lo que falta: todo lo demás.** No hay simulador, generador, módulo de
LabSim, fotos libres de rinoscopía ni normativa con citas. Tampoco hay nada de
olfato.

Índice tentativo, en el mismo formato:

- **Herramientas**:
  - N-H1: anamnesis nasal y rinoscopía anterior, con escalas de obstrucción
    (NOSE, EVA)
  - N-H2: rinomanometría anterior activa (Broms, Cottle, RNT/IRNT, gráfico
    polar, pre y post vasoconstrictor, posicional y ejercicio)
  - N-H3: rinometría acústica (curva área-distancia, MCA1/MCA2, volúmenes)
  - N-H4: flujo inspiratorio nasal máximo (PNIF) **(no está en ningún
    material)**
  - N-H5: pruebas cutáneas (prick)
  - N-H6: espirometría
  - N-H7: SAHOS y polisomnografía o poligrafía
  - N-H8: **olfatometría** (Sniffin' Sticks, UPSIT…) **(no hay nada: habría
    que escribirla desde cero, si se incluye)**
- **Clínicos**:
  - Desviación septal frente a válvula nasal
  - Hipertrofia de cornetes y rinitis alérgica
  - Rinitis vasomotora y medicamentosa
  - Poliposis
  - El niño respirador bucal (adenoides)
  - Antes y después de la septoplastía
  - Ronquido y SAHOS
  - Patrón obstructivo y restrictivo en la espirometría
  - Pérdida del olfato (si se incluye N-H8)

Las figuras serían fáciles de generar con un motor propio: la curva
presión-flujo por fosa (ecuación de Rohrer `ΔP = k1·V + k2·V²`), el gráfico
polar de Broms, la curva área-distancia, el asa flujo-volumen y el
hipnograma. **Pero ese motor no existe**, y el libro exige que cada figura
salga de un simulador.

---

## 4. Complejidad estimada por bloque

| Bloque | Complejidad | Por qué |
|---|---|---|
| VEMP (VH7, cap. 20) | **Baja** (hecha) | Ya sale del motor de LabSim |
| vHIT (VH6, V1, V5, V9, V12) | **Baja–media** | El modelo de sH cabe en ~100 líneas Python; tH ya tiene el sintético y figuras en Python. Falta tabla normativa con citas (≥0,8 lateral, ~0,7 vertical: **(sin verificar)**) y elegir un método de ganancia |
| Oculomotor y nistagmo espontáneo o de mirada (VH2, VH3, V6) | **Media** | L3D ya genera trazas sin DOM; hay que pasarlas a SVG con el estilo de Siev y calibrar las normas (latencia, ganancia de seguimiento) con bibliografía |
| Posicionales y VPPB (VH4, V2) | **Media** | La física está en L3D. La traza del nistagmo torsional-vertical en 2D y el dibujo del canal hay que hacerlos en SVG; los dibujos de maniobras son ilustraciones |
| Calórica (VH5, V3, V8) | **Media** | `calorica()` y `jongkees()` existen. Faltan el ruido realista, la variabilidad entre irrigaciones, la normativa citada y los 3 diagramas |
| Posturografía (VH8, V10) | **Media–alta** | Dos fuentes que juntar (PX tiene métricas reales pero no simula patología; L3D simula pero con constantes "de orden de magnitud"). El protocolo 2019 no la trae |
| **Eje vestibular en el caso de LabSim** (para que los casos "salgan de los generadores de la app", como hoy) | **Alta** | Hoy `cases.data` solo tiene `vemp`. Habría que diseñar un eje (función por sitio, días desde la lesión, canal y tipo de VPPB, central), declararlo en `CaseProfile::SCENARIOS` con cita por cuadro (regla de la bibliografía central), sumar cuadros puramente vestibulares y el editor PHP/JS. Y, si "En LabSim" ha de ser verdad, construir los módulos `VNG`, `VHIT` y `POS`, que hoy son marcadores |
| Fisiología vestibular | **Baja–media** | ETMP174 2.1–2.2, 3.2, 3.4 y 4.1 son del autor; B1 de la colega ya incluye lo vestibular |
| Nasal completo | **Alta** | Cero simulador y cero generador; el material es de otra docente con derechos reservados; no hay fotos libres de rinoscopía; la normativa hay que buscarla (ISCOANA, Clement 2005/2016, valores chilenos de Vergara) **(sin verificar)**; olfatometría inexistente |

**Bloqueos principales:**

1. **No hay eje vestibular en LabSim.** Es lo que rompe la regla del libro
   ("cada caso sale de los generadores de la app").
2. **Normativa.** L3D declara constantes no normativas. Todo número que salga
   en una figura necesita su cita.
3. **Puente JS → Python.** Usar Node en la cadena del libro, o portar.
4. **Licencias.** simHit se contradice (Apache-2.0 frente a MIT); L3D no
   tiene DOI; la malla `cabeza.glb` es de origen desconocido.
5. **Datos personales.** Imágenes de ojos en `vng/train/capture` y
   `Siev/fixtures`, y exámenes del autor en vhit-wout-google. No usarlos.
6. **Nasal.** No hay simulador; el material es de Vanessa Uribe con "all
   rights reserved" (hace falta permiso o coautoría); no hay nada de olfato.

---

## 5. Decisiones que le tocan al autor

> **Decidido (2026-10-15):** LabSim **no** se expande a lo vestibular. Las
> figuras y la práctica vestibulares salen de **trainHIT** (vHIT) y
> **labyrinthus3d** (VNG, posicionales, calórica, oculomotor, postural); el
> VEMP sigue en LabSim. Es la opción (b) de la decisión 2: en esos capítulos
> el bloque "En LabSim" pasa a ser "En el simulador" (trainHIT o
> labyrinthus3d). Quedan abiertas la 3 (puente Node o port a Python del
> modelo de labyrinthus3d) y las demás.

1. **¿Parte IX o Volumen 2?** Si es volumen 2, ¿H12 y el cap. 20 se quedan en
   el 1 o se mudan?
2. **¿De dónde pueden salir las figuras vestibulares?** Las opciones son:
   - (a) Solo de LabSim. Exige construir los módulos VNG, VHIT y POS antes que
     el libro.
   - (b) De los simuladores hermanos (labyrinthus3d, simHit, trainHIT,
     posturografox), que son "motores reales" pero no LabSim. Entonces el
     bloque "En LabSim" de cada herramienta se vuelve "En el simulador".
   - (c) Mixto: generar con L3D mientras se construye LabSim.
3. **Puente o port.** ¿El motor del libro llama a labyrinthus3d por Node, o
   el modelo de patología se porta a Python, por ejemplo a un
   `src/vestibular/` de LabSim que después use el módulo VNG?
4. **Forma del eje vestibular del caso.** ¿Un modelo por sitio anatómico
   como el de L3D (canal, rama del nervio, núcleo, FLM, flóculo, con días de
   compensación) o campos por prueba como el VEMP (ganancia vHIT por canal,
   paresia calórica, tipo de nistagmo)? El primero es más coherente (un solo
   modelo da todas las pruebas). El segundo es más simple de editar.
5. **Normativa.** ¿Se arma una planilla de normas vestibulares con
   bibliografía (como la de 27 fuentes del ABR) antes de escribir? Y ¿se
   recalibran las constantes de L3D contra ella?
6. **simHit.** Resolver si la licencia es Apache-2.0 o MIT antes de citarlo.
   ¿Darle DOI a labyrinthus3d?
7. **Material de colegas.** Las unidades II y III de ETMP174 son de G.
   Casanova y P. Poza, y ETMP172 es de V. Uribe. ¿Se los invita como
   coautores de capítulo (como en B1) o se escribe solo desde el protocolo
   2019 del autor?
8. **Alcance vestibular.** ¿Entra la rehabilitación vestibular (protocolo
   p. 127), que es tratamiento y no evaluación? ¿Y lo pediátrico (V11), que
   tiene poca base en los generadores?
9. **Alcance nasal.** ¿Volumen propio de "Rinología" con espirometría y
   SAHOS (como ETMP172) o solo nariz? ¿Se incluye el olfato, que no tiene
   ningún material? ¿Se construye antes un módulo nasal en LabSim
   (rinomanómetro y rinómetro simulados) para que el libro cumpla su regla?
10. **Fotos de equipos.** Siev, las gafas de simHit, posturografox y cvemp se
    pueden fotografiar en el laboratorio. Videos de ojos, solo de autores que
    consientan, como en `sesion_figura1.csv` de trainHIT.

---

## Anexo: lo que no se revisó

- `ingi152` (solo su título), `etmp182` (solo la vista previa).
- Las otras 3 variantes del `.mbz` de ETMP174.
- El contenido de imágenes y videos (ojos, retratos, el video del
  rinomanómetro).
- Las ramas de git que no son la actual.
- El código de Siev más allá de la estructura, los tipos de prueba y los
  gráficos del informe.
