# Simuladores

Todos los simuladores siguen el mismo patrón:
1. El docente configura **datos fisiológicos** del paciente (no resultados)
2. Un **generador sintético** produce datos coherentes a partir de esos parámetros
3. El equipo muestra **datos crudos** — nunca interpreta
4. El estudiante analiza e interpreta

Los artefactos y la cooperación del paciente se configuran en la **agenda** (por cita), no en el paciente.

---

## Audiología

### Audiómetro (LabSim AU-2000)
- Réplica de audiómetro de dos canales con perillas rotatorias
- Frecuencias ISO 125-8000 Hz + extendidas hasta 20 kHz
- Vía aérea, ósea, campo libre
- Enmascaramiento con ruido de banda estrecha
- **El paciente responde** según sus umbrales + cooperación — no es una animación

### Impedanciómetro (LabSim Z-400)
Estructura modular por prueba:
- **Timpanometría**: sweep de presión con curva en tiempo real. Configurable: frecuencia sonda (226/678/1000 Hz), rango presión, velocidad
- **Reflejos acústicos**: búsqueda de umbral ipsi/contra por frecuencia. Traza de deflexión animada
- **Deterioro del reflejo**: estimulación 10s con medición de decaimiento
- **Función tubárica**: 3 timpanogramas (basal, Toynbee, Valsalva)

Datos del paciente: compliance pico, presión oído medio, volumen CAE, umbrales de reflejo por frecuencia, deterioro, desplazamientos tubáricos.

### Logoaudiometría
SDT, SRT, discriminación del habla.

### Pruebas supraliminares
SISI, Tone Decay, Loudness Balance.

### OAE
TEOAE y DPOAE con análisis por frecuencia.

### Audífonos
Prescripción (NAL-NL2, DSL), verificación REM, campo libre con/sin audífonos.

---

## Otoneurología

### ABR / Potenciales Evocados
Ondas I-V con latencias, intervalos, función latencia-intensidad.

### Electrococleografía
Relación SP/AP, criterios de hidrops.

### VNG (LabSim VN-200)
Estación modular — el operador elige la prueba:
- **Espontáneo**: sin fijación / con fijación (supresión = periférico)
- **Calórico**: 4 irrigaciones (OD/OI × caliente/frío), SPV pico por cada una
- **Posicional**: 7 posiciones (Dix-Hallpike bilateral, Roll bilateral, supino, head hanging, sentado). Cada una con dirección, SPV, latencia, duración, fatigabilidad
- **Oculomotor**: sacadas (latencia, precisión, velocidad), seguimiento (ganancia, tipo sinusoidal/sacádico/atáxico), optocinético (ganancia bilateral)

### vHIT (LabSim HI-600)
- 6 canales semicirculares (laterales, LARP, RALP)
- Ganancia VOR por canal
- **Sacadas overt** (durante impulso) y **covert** (después) configurables por separado con tasas independientes
- **Artefactos de gafas** (goggle slippage/bounce) — configurados en la agenda, no en el paciente
- Traza superpuesta cabeza + ojo por impulso
- Panel resumen: ganancia promedio, conteo overts/coverts/artefactos

---

## Oftalmología

### OCT (LabSim)
- B-scan con 10 capas retinales realistas
- RNFL TSNIT con normativas por hora del reloj
- Mapa ETDRS de espesor macular (9 sectores)
- GCL+IPL por sectores
- 7 patologías: normal, glaucoma, edema, drusen, epiretinal, DMAE seca/húmeda
- Severidad escala todas las distorsiones (leve/moderado/severo)
- Params opcionales: RNFL promedio, GCL+IPL, macular central

### Campo Visual (LabSim HFA-III)
- **El paciente es un agente**: responde a cada estímulo según su sensibilidad real + cooperación + fatiga
- Algoritmo staircase por protocolo: SITA Standard (8 max/punto), SITA Fast (4 max), Full Threshold (10 max)
- 13 defectos clínicos: arcuato sup/inf/doble, escalón nasal, hemianopsias, cuadrantanopsias, depresión general, isla central, constricción periférica
- Falsos positivos/negativos, pérdida de fijación, fatiga — todo configurable
- Catch trials automáticos (~8%)
- Cálculo real de MD y PSD desde las respuestas del paciente
- El estudiante puede cambiar de protocolo y los datos del paciente lo soportan

### Retinógrafo
- 13 patologías de fondo de ojo
- Generación procedural de disco óptico, vasos, mácula, lesiones
- Captura con flash simulado

### Topógrafo de Placido (LabSim)
- Mapas: axial, tangencial, elevación, paquimetría
- Severidad afecta el generador
- Params opcionales: K1/K2, CCT, punto más delgado
- Índices queratométricos: SimK, Kmax, cilindro, ISA, IHD

### Tomógrafo Scheimpflug (LabSim SA-1) — NUEVO
Equipo separado del topógrafo de Placido:
- **Corte Scheimpflug**: imagen de sección transversal de cámara anterior (córnea, iris, cristalino)
- Mapas de elevación anterior y posterior
- Paquimetría punto a punto
- Índices: K anterior/posterior, CCT, ACD, volumen CA, ángulo iridocorneal, densitometría del cristalino
- 8 patologías corneales + 6 estados del cristalino (incluyendo cataratas y pseudofaquia)

---

## Modelo de datos del paciente

```
PatientData = {
  core: {                          // FIJO
    identity: { ... }              // nombre, RUN, edad, género, previsión
    personality: { ... }           // tipo personalidad, tono, cooperación en exámenes
    clinicalHistory: { ... }       // motivo consulta, antecedentes, historia
  },
  modules: {                       // DINÁMICO — extensible sin límite
    "audiometry": { ... },
    "impedance": { ... },
    "oct": { ... },
    "vng": { ... },
    "scheimpflug": { ... },
    // agregar nuevo simulador = nuevo key, sin tocar nada más
  }
}
```

Los artefactos y cooperación numérica van en `session_config_json` del agenda_item.
