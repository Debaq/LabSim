# Larissa y el Centro

## Larissa — Sistema de Fichas Clínicas

Larissa es donde el estudiante **atiende** pacientes. No es un editor de módulos.

### Flujo
1. Panel izquierdo: **agenda de atenciones** agrupada por fecha
2. Click en cita → **ficha clínica** del paciente
3. Botón "Llamar Paciente" → inicia la sesión en vivo
4. 4 tabs:
   - **Evoluciones**: lista cronológica + crear nueva (motivo consulta, anamnesis próxima, examen físico, hipótesis diagnóstica, plan de estudio, plan terapéutico, observaciones)
   - **Interconsultas**: solicitar derivación a otra especialidad (urgencia configurable)
   - **Exámenes**: resultados de simuladores vinculados al caso
   - **Ficha Base**: datos del paciente (read-only, creados por docente)

### Ficha clínica según normativa chilena (Decreto 41 MINSAL, Ley 20.584)
- Identificación del paciente
- Motivo de consulta
- Anamnesis próxima y remota
- Examen físico
- Hipótesis/Impresión diagnóstica
- Plan de estudio y plan terapéutico
- Derivaciones/Interconsultas
- Evoluciones clínicas
- Consentimientos informados

## El Centro

### No se crea — emerge

El Centro no es un botón ni una modalidad. Es lo que sucede cuando dos docentes comparten estudiantes y ambos les ponen agenda.

El docente está armando su agenda y ve: "estos 20 estudiantes ya tienen citas de oftalmología el martes, puestas por Docente B". Ahí está el Centro.

### La agenda es global por estudiante

- Si Docente A agenda audiometría a las 10:00 para María
- Y Docente B agenda OCT a las 10:00 para María
- El sistema marca conflicto
- Ambos docentes ven las citas del otro

### Vista Centro en la agenda

Toggle "Mi agenda" / "Centro":
- **Mi agenda**: citas agrupadas por fecha
- **Centro**: timeline por estudiante, citas coloreadas por curso/docente, conflictos en rojo

## Karime — La Secretaria

Karime es una secretaria de centro clínico real. No felicita.

### Cuando el estudiante está atendiendo
- Avisa cuánto tiempo queda
- Si se pasa → warning → urgent → critical
- Los mensajes escalan según nivel de presión configurado por el docente

### Cuando termina un paciente
No dice "buen trabajo". Dice:
> "Se fue el Sr. Martínez. La Sra. López ya lleva 10 minutos esperando."

### Tonos configurables
- Profesional, amigable, estricto, relajado
- Nivel de presión 1-5 (ajusta umbrales de alertas)
- Tratamiento: formal, nombre personalizado, custom

## Reuniones Clínicas

- Convocar reuniones entre estudiantes (asignados por docente o automáticamente)
- Registrar actas
- Crear planes de mejora con tareas asignables
- Los planes se aplican (tienen efecto en la simulación)
