# Pacientes Vivos

## El paciente no es un JSON — es una persona

Cada paciente tiene:
- **Identidad**: nombre, RUN, edad, género, ocupación, previsión
- **Personalidad**: colaborador/ansioso/impaciente/tímido/agresivo/confuso + tono de voz + estilo de comunicación
- **Historia**: lo que cuenta cuando le preguntan (backstory escrito por el docente)
- **Datos clínicos**: lo que tienen sus ojos, oídos, sistema vestibular (lo que los simuladores muestran)
- **Memoria**: recuerda atenciones anteriores

## El paciente habla

Cuando el estudiante "llama" al paciente:
1. Aparece como contacto de chat en Mensajes
2. El LLM genera un system prompt dinámico desde su personalidad + backstory + historia clínica + memoria
3. El paciente responde según su personaje — no sabe términos médicos, hace preguntas, se asusta o se impacienta
4. Si otro estudiante lo atiende después, menciona experiencias anteriores

## Los pacientes evolucionan

Un paciente tiene una **línea de tiempo de estados**:
- Estado 1: paciente llega con síntomas iniciales
- Estado 2: una semana después empeoró
- Estado 3: respondió al tratamiento

El docente crea estados y los propaga a los estudiantes. Cada estudiante tiene su propia versión del paciente.

## Memoria entre atenciones

Cada vez que termina una atención se registra:
- Quién lo atendió (nombre del estudiante)
- Cuánto duró
- Qué exámenes le hicieron
- Su estado emocional al final

Cuando otro estudiante lo atiende, el LLM recibe estos logs:
> "Ah, el otro joven que me atendió antes me hizo una audiometría. ¿Van a repetirla?"

## Cooperación y artefactos van en la AGENDA

Los artefactos no son del paciente — son del contexto de la sesión. El mismo paciente puede tener artefactos de gafas un día y no otro.

El docente configura esto al crear la cita, no al crear el paciente:
- Cooperación general (0-1)
- Artefactos específicos por equipo (fuga de sonda, parpadeo, goggle slippage, ruido eléctrico, etc.)

El estudiante NO ve esta configuración — solo la experimenta.
