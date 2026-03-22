# Flujo del Sistema

## Capa Admin — Infraestructura

El admin gestiona lo **estructural**, no lo pedagógico:

- Base de datos de **pacientes simulados** activos
- **Aplicaciones activas** en el desktop (qué simuladores están disponibles)
- **Docentes/instructores** y sus **cursos** (creación)
- Configuración global de la institución

## Capa Docente — Pedagogía

El docente gestiona el **contenido y la actividad**:

- **Unidades de aprendizaje** con objetivos verificables
- **Material educativo**
- **Actividades** semanales, diarias, o por sesiones cortas
- **Crear pacientes** (compartidos o privados)
- **Registrar estudiantes** por CSV con contraseña temporal = identificador
- **Agenda del centro**: visibilidad cruzada con otros docentes que comparten estudiantes
- **Configuración de sesión** por cita: cooperación del paciente, artefactos por equipo

## Capa Estudiante — El Día Clínico

### Sin agenda = modo exploración
- Puede abrir los simuladores pero no hay pacientes
- Karime no está disponible (fuera de horario)
- Solo explora libremente

### Con agenda = simulación completa

```
1. Abrir agenda → ver citas del día
2. Llamar al paciente → el paciente aparece en chat con voz y personalidad
3. Karime inicia presión de tiempo
4. Hacer exámenes → los simuladores muestran datos del paciente
5. Crear evolución clínica → ficha MINSAL
6. Derivar si necesario → interconsulta
7. Finalizar atención → log de memoria del paciente
8. Karime avisa del siguiente paciente
9. Reuniones clínicas con compañeros → actas, planes de mejora
```

## El Centro es Emergente

Nadie "crea" el Centro. Emerge cuando dos docentes comparten estudiantes y ambos les agendan citas. El Centro es la **vista unificada** del día clínico del estudiante.

Cuando Docente A ve que sus estudiantes tienen citas de Docente B → ahí está el Centro. La agenda es global por estudiante, no por curso.

## Supervisión Docente

El docente no ve en tiempo real (eso satura todo). Ve:

- **Tablero de estado**: quién se presentó, quién atiende, quién se atrasó
- **Checkpoints de validación**: el paciente no se retira hasta que el docente valide el procedimiento (configurable por nivel del estudiante)

## La Clínica Nunca Cierra

- El Centro es permanente, como un hospital
- Los procesos pedagógicos tienen inicio y fin
- Cuando terminan, los estudiantes dejan de asistir
- Se guardan stats para ver evolución
