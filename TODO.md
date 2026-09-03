# TODO

## Otoscopia: derivación + aprobación docente + fase por alumno

Ficha Otoscopia (case_create.php, antes de Audiometría) construida como N
fases (sin selector de modo aparte: 1 sola fase ya ES "única"), cada una
con imagen OD + imagen OI + texto libre describiendo qué pasó desde la
fase anterior — vacío en fase 1. Dato guardado en `cases.data.Otoscopia`.

Dinámica pedagógica real (no implementada aún): el paciente NO es un estado
compartido igual para todos los alumnos — cada estudiante avanza su propia
fase de otoscopia según sus propias derivaciones aprobadas por el docente.
Ej: alumno atiende, hace otoscopia (fase 1), encuentra tapón de cerumen,
deriva a lavado; si el docente aprueba esa derivación, la próxima vez que
ESE alumno atienda a ese paciente ve la fase 2 (con el texto "se realizó un
lavado"); si no derivó o no fue aprobada, sigue viendo la fase 1. Si un
alumno solo llega hasta fase 2 aprobada y no hay fase 3, siempre ve la 2.

Hoy: todo alumno ve fase 1 fija (hardcodeado), no hay derivación ni revisión.

Pendiente:
- [ ] Derivación del estudiante: campo/acción al cerrar atención
      (`attendance_action.php`, action `atendido`) para redactar la
      derivación, separado de la nota general de atención.
- [ ] Bandeja docente de revisión: UI nueva donde el profesor ve
      derivaciones pendientes por alumno-paciente y aprueba/rechaza.
- [ ] Tabla de progreso por alumno-paciente: qué fase de otoscopia tiene
      aprobada CADA estudiante para CADA paciente (no existe hoy — nueva
      tabla, ej. `patient_student_progress` o similar).
- [ ] Motor de selección de fase en el lado alumno: qué fase se muestra al
      abrir la ficha del paciente según el progreso aprobado de ESE
      alumno, clamp a la última fase disponible si no hay más.
- [x] Vista de otoscopia en la app de escritorio: botón "Otoscopia" en
      Box Audiología (a la izquierda de Acumetría, ver resources/json/apps.json
      y src/audiometria/Otoscopia.py) -- muestra la imagen OD/OI lado a
      lado ("Otoscopio sin batería" si no hay imagen subida). Hoy siempre
      trae la fase 1 (índice 0, `FASE_FIJA` en Otoscopia.py) para todos los
      alumnos, ni el texto libre de cada fase se muestra todavía.
- [ ] Aplicar el motor de selección de fase (punto anterior) también acá:
      hoy `FASE_FIJA = 0` está hardcodeado en src/audiometria/Otoscopia.py.
      Mostrar además el texto libre de la fase actual (hoy no se pide ni
      se muestra en la app, solo las imágenes).
- [ ] Notificación al alumno al aprobar/rechazar su derivación (posible
      tipo nuevo en `inbox_messages`, mismo patrón que OirsEvaluator).
- [ ] Historial/auditoría de derivaciones: quién derivó, cuándo, quién
      aprobó/rechazó.
- [ ] Reglas de reintento: qué pasa si el docente rechaza (¿queda en la
      misma fase?, ¿puede el alumno volver a derivar la misma cita?).

## Voces de respuesta logoaudiometria (ListWords.py)

Bug: paciente "no responde" en logoaudiometria. Causa real: `create_word_response`
(lib/h_audio.py) arma el nombre de archivo como
`audio/LP_palacios_r_{sex}{number}_{name}.mp3`, usando `gender`/`id` reales
de la ficha del paciente. Solo existen grabadas las voces `feme1` y `feme2`
(`resources/audio/LP_palacios_r_feme{1,2}_*.mp3`) — no hay ninguna voz `male`
grabada, y ningun otro numero de id tiene voz asociada. Si el archivo no
existe, Qt/ffmpeg falla en silencio ("No existe el fichero o el directorio")
y no suena nada, dando la impresion de que el paciente no responde.

Fix temporal aplicado en `ListWords.la_super` (src/ListWords.py): se fuerza
siempre `gender="feme"` e `id=1`, ignorando el genero/id real del paciente,
para que siempre use una voz que sí existe.

Pendiente:
- [ ] Grabar voces `male1`/`male2` (set completo de palabras + `none1/2/3`).
- [ ] Decidir que representa realmente el numero de voz (¿variante de
      locutor, no el id de la ficha?) y mapear correctamente en vez de
      hardcodear a 1.
- [ ] Quitar el forzado temporal en `ListWords.la_super` una vez resuelto.
