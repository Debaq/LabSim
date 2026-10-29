# Audiometría previa en la práctica libre (2026-10-29)

Resumen de lo que cambió para que los pacientes del libro no creyeran que
todos venían a la audiometría. El detalle técnico está en
`docs/decisiones.md`, "Audiometría previa en la práctica libre".

## El problema

Todos los pacientes del libro traen todos los exámenes, y el procedimiento
de cada uno salía de las figuras del capítulo. Como casi todos los capítulos
muestran el audiograma, casi todos decían "Audiometría + …". El chat le dice
al paciente "vienes por {{procedimiento}}", así que el paciente de un
capítulo de PEATC o de VEMP decía que venía a la audiometría.

## Antes y después

| | Antes | Después |
|---|---|---|
| Procedimiento (caps. 9, 11, 12, 14, 18, 20, 30 y H12) | "Audiometría + Impedanciometría + PEATC" | "Impedanciometría + PEATC" (27 pacientes en prod) |
| Procedimiento de H21 (ficha 36) | "Otoscopía + Acumetría" (el valor por defecto) | "Prueba de audífonos" |
| Ficha clínica | Sin rastro de la audiometría | Entrada en el historial, 14 días antes de la cita (o justo después de quien la pidió, si eso fue más cerca): "Audiometría. Trae el informe. **Ver informe**" |
| "Ver informe" | — | Subventana del MDI, "Examen que trae el paciente", con la hoja auditiva del libro |
| Chat del paciente | Solo sabía el motivo; no conocía la historia clínica | Conoce la historia clínica ("hace 2 meses el otorrino me mandó…") y que trae la audiometría ("hace un par de semanas me hicieron una prueba de audición y traigo el papel") |
| Docente en práctica libre | Veía el procedimiento de la ficha del caso, sin la audiometría, y su chat de prueba decía "audiometría" | Ve lo mismo que el alumno |
| Ficha abierta y otro paciente elegido en la agenda | Quedaba la ficha del anterior | La ficha cambia sola; la hoja del paciente anterior se cierra |
| Botón de la ficha en la agenda | Siempre "Ver ficha" | "Cerrar ficha" mientras está abierta |
| Carpeta nueva en práctica libre | La primera fila quedaba marcada sin estar elegida; con un solo paciente no se podía ver su ficha | Sin fila marcada; un clic la elige |
| Alumno que repite la audiometría | — | Puede hacerlo; queda como una atención más en su historial |

## Por qué se decidió así

- **El paciente llega con la audiometría hecha, no se le quita.** En la
  clínica, al que viene a un PEATC o a un VEMP lo derivan con su
  audiometría. Así el motivo deja de ser "audiometría" sin rearmar los casos
  ni borrar datos.
- **No se bloquea nada.** Pediste que los exámenes se puedan hacer igual: si
  el alumno la repite, queda en su historial y se puede evaluar.
- **Se ve dentro de la app.** Los kioskos solo tienen LabSim. Por eso la
  hoja va empaquetada con la app (`resources/libro/previos/<ficha>.svg`) y
  no se baja de internet ni se abre en el navegador.
- **Es la hoja del libro.** Se dibuja con el mismo motor de figuras del libro
  y con los mismos datos cargados en prod (`scripts/libro/previos.py`): lo
  que ve el alumno coincide con lo que mide si repite el examen.
- **Dentro del MDI.** Lo pediste así: queda al lado de la ficha y de los
  equipos, como cualquier otra ventana de LabSim.
- **Qué capítulos la traen.** Los que enseñan otro examen (potenciales,
  VEMP, ECochG, corticales). Los capítulos donde la audiometría es parte de
  lo que se resuelve (13, 15, 19, 34…) la siguen pidiendo. Se cambia en
  `AUDIOMETRIA_PREVIA` (`scripts/libro/sql_practica.py`).
- **Solo en la práctica libre.** En una cita que agenda el docente no
  aparece: el caso puede ser el mismo, pero qué trae el paciente lo decide
  el docente.
- **Sin hoja en el libro, no hay audiometría.** Los lactantes (H10, H13,
  caps. 16-17) no tienen audiograma en el libro y no traen ninguno: un recién
  nacido no tiene audiometría tonal.
- **Si viene a otoscopía, no la trae** (corrección tuya). La audiometría va
  después de la otoscopía. Por eso Benjamín (35, H1) ya no la trae.
- **H21 con procedimiento propio.** Su figura (campo libre) no tenía nombre en
  el catálogo y salía "Otoscopía + Acumetría", que con la regla anterior le
  quitaba la audiometría. Quien viene a probarse audífonos la trae.
- **La historia va al chat fuera de la plantilla.** Así una plantilla que
  edites en el panel no la pierde. Vale para todos los casos, no solo los del
  libro.

## Quién la trae hoy (práctica libre en prod)

- H7 Impedanciometría: 34, 35
- H9 Emisiones otoacústicas: 33, 35, 36
- H11 Electrococleografía: 38
- H12 VEMP: 33, 34, 38, 42
- H21 Prueba de audífonos: 36
- Cap. 9 Hidrops: 38, 72
- Cap. 11 Asimetría que no cierra: 78-83
- Cap. 12 El tronco: 84-88
- Cap. 14 Lo que mueve el ABR: 93
- Cap. 18 El ABR que engaña: 110-114
- Cap. 20 VEMP: 119-122
- Cap. 30 Oír y no entender: 129-131

## Cambios en prod

- 27 procedimientos de `practice_items` (respaldo previo
  `labsim_2026-10-29_102210.sqlite`).
- H21, ficha 36: "Prueba de audífonos" (respaldo previo
  `labsim_2026-10-29_112919.sqlite`).
- Los intentos que ya estaban abiertos conservan el procedimiento anterior;
  los nuevos toman el nuevo.

## Dónde está cada cosa

- Regla y ventana: `src/core/ficha.py` (`audiometria_previa`, `HojaPrevia`,
  `fila_de_practica`).
- Ficha que sigue a la agenda: `src/agenda/Agenda.py`
  (`_seguir_con_la_ficha`).
- Subventana: `PREVIO` en `labsim_backend/src/Layout.php`; `src/main.py` la
  agrega si el backend todavía no la manda.
- Chat: `LlmConfig::historiaPrevia` (`labsim_backend/src/LlmConfig.php`) y
  `trae_audiometria` en `llm_chat.php`.
- Hojas: `scripts/libro/previos.py` → `resources/libro/previos/`. Se vuelve a
  correr si cambia un caso o el dibujo del libro.
