# Roadmap de los manuales

Estado y plan de los manuales de LabSim. Lo ya hecho, y el porqué, está en
`docs/decisiones.md` § Manuales del estudiante y del docente. El ítem abierto
en `TODO.md` es el 65.

## Reglas para los dos

- Formato del manual de PosAR: markdown + `hacer_pdf.py`, guía rápida al
  inicio, partes numeradas, cada sección en hoja nueva.
  `cd docs/manual && /usr/bin/python hacer_pdf.py estudiante|docente`.
- Autores, en este orden: Nicolás Baier-Quezada, Vanessa Uribe-Hernández,
  Fernanda López-Moncada, Cristina Vargas-Bustamante. TecMedHub · Universidad
  Austral de Chile, Sede Puerto Montt.
- Portada: `LabSim v0.9.9-r<sha>` (se lee solo al armar el PDF); logo LabSim
  chico en la fila de logos, nunca grande arriba.
- Los textos dicen **cómo opera el software**, no clínica: el docente es el
  experto. Nada de guías didácticas ni interpretación de resultados.
- Capturas reales con datos **inventados** (pacientes 33-42 de
  `capturas/casos_demo.json`, alumna Valentina Rojas, docente Andrea Soto
  Vidal). Nunca datos de prod.
- "Código de ingreso" / "la plataforma de tu curso", no "Moodle": sirve
  cualquier plataforma LTI.
- Al cambiar algo que se ve, volver a correr la captura de ese grupo y
  regenerar el PDF.

## Manual del estudiante — hecho

`manual-estudiante.md` → `manual-estudiante.pdf` (57 págs). Guía rápida y
seis partes: I Entrar · II Atender · III Tu avance en la web · IV Box
Audiología · V Box Electrofisiología · VI Ajustes y problemas.

Capturas:
- App: `micromamba run -n labsim python docs/manual/capturas/capturar_app.py <grupo>`
  desde la raíz, **un grupo por proceso** (de corrido se cuelga).
- Portal web: `docs/manual/capturas/capturar_portal.sh` (podman + Chromium,
  copia del backend, nunca prod).

Queda al día salvo estos cambios futuros, que lo tocan cuando lleguen:

| Cuando se haga | Qué actualizar |
|---|---|
| Otoscopía por fases (postergada) | §21 Otoscopía: cómo se ven las fases |
| Criterio para evaluar el ABR | §23 ABR y §11-13 (logro del ABR en la web, si se suma) |
| TODO 62-64: enmascaramiento, tinnitumetría, logo/supra como técnica | §17-19 y §12-13 (nuevos pasos de la técnica) |
| Audiograma del alumno (`AudiometriaTecnicaGrafico::audiograma`, guardado) | §13 si se muestra en Mis pacientes |
| Login, agenda, chat o barra de la app | Guía rápida (las fotos de los pasos 2-6) |

## Manual del docente — pendiente

Mismo formato. Falta `img/portada-docente.svg` (la configuración de
`hacer_pdf.py docente` ya existe y la pide).

### Contenido propuesto

Lo que ve un docente (menú **Docencia** + su perfil). Lo de administración
del sistema va en una parte aparte, al final, porque solo lo ve el
administrador.

| Parte | Secciones |
|---|---|
| **Guía rápida** | Entrar desde la actividad del curso → vincular el curso → armar un caso → agendarlo → ver la atención del alumno y comentarla |
| **I — Entrar** | Ingreso LTI como docente (página con las estadísticas del curso), vincular el curso de la plataforma con un curso LabSim, curso en foco, Mi perfil (usuario y contraseña para la app), entrar a la app como docente |
| **II — Cursos** | Pestañas de Cursos: Resumen (checklist, próximas citas, sin actividad), Personas (roster, grupos, alumno nuevo a mano), Módulos (equipos habilitados), Agenda, Práctica (pacientes de práctica libre, ficha de estudio), Vínculos (claves LTI), Pruebas |
| **III — Casos (fichas clínicas)** | Lista de fichas, crear/editar caso pestaña por pestaña (0 armado rápido, paciente, sala y acompañantes, perfil auditivo, audiometría, otoscopía con fotos, timpanometría, ABR, EOA, VEMP, tinnitus, anamnesis con IA), Resumen y revisión ficha por ficha, importar caso, ficha PDF docente y ficha de estudio |
| **IV — Agenda y práctica** | Agendar a todo el curso / grupo / alumno, choques de horario, reemplazar o ronda nueva, no se presentó, práctica libre |
| **V — Seguimiento** | Dashboard, Avance del curso y objetivos, técnica de audiometría por alumno, detalle de una atención (conversación con comentarios por turno, evolución, informes PDF y versiones), bandeja de entrada (mensajes al alumno), OIRS simulada, ver como alumno |
| **VI — La app desde el lado docente** | Qué cambia al entrar como docente en la app (consola de depuración, sesiones anteriores del ABR, etc.) |
| **VII — Administración** (solo administrador) | Normativas (ABR, acumetría, impedanciometría) y Bibliografía, IA Paciente, Usuarios, Sesiones y bloqueos, Auditoría, Versiones de la app, Tickets, LTI, Base de datos y respaldos |

### Fases

1. **Siembra docente.** Ampliar `capturas/sembrar_portal.php` (o uno nuevo
   `sembrar_docente.php`): curso con dos grupos y ~8 alumnos inventados,
   objetivos, citas pasadas y futuras, atenciones cerradas con comentarios,
   informes y mensajes, casos 33-42 completos con fotos de otoscopía. Una
   docente y un administrador.
2. **Capturas del panel.** `capturas/capturar_docente.py` con el mismo
   Chromium por DevTools de `capturar_portal.py` (recorte por tarjeta,
   pestañas abiertas, modales), sobre la misma copia del backend. Escritorio
   1300 px y, donde sirva, celular.
3. **Capturas de la app como docente**, si la parte VI lo pide (grupo nuevo
   en `capturar_app.py`).
4. **Texto**, parte por parte, con los nombres exactos de botones y avisos
   sacados del código (no de memoria).
5. **Portada** `img/portada-docente.svg` (misma línea que la del estudiante)
   y PDF.
6. **Revisión** hoja por hoja del PDF, como con el del estudiante.
