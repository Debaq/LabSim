# Exámenes previos en la práctica libre (2026-10-29)

Resumen de lo que cambió para que los pacientes del libro no creyeran que
todos venían a la audiometría, y para que la ficha muestre los exámenes que
ya les hicieron. Empezó con la audiometría (de ahí el nombre del archivo) y
se extendió a todos los exámenes. El detalle técnico está en
`docs/decisiones.md`, "Audiometría previa en la práctica libre" y
"Exámenes previos: foco por capítulo y hojas de la historia".

## El problema

Todos los pacientes del libro traen todos los exámenes, y el procedimiento
de cada uno salía de las figuras del capítulo. Como casi todos los capítulos
muestran el audiograma, casi todos decían "Audiometría + …". El chat le dice
al paciente "vienes por {{procedimiento}}", así que el paciente de un
capítulo de PEATC o de VEMP decía que venía a la audiometría. Y lo que la
historia contaba ("audiometría de base: normal", "AABR refiere") era solo
texto: no había nada que revisar.

## Antes y después

| | Antes | Después |
|---|---|---|
| Procedimiento en los capítulos que enseñan un examen | Todo lo de las figuras: "Audiometría + Impedanciometría + PEATC" | Solo lo que enseña el capítulo: "PEATC" (ver "Foco por capítulo") |
| Procedimiento de H21 (ficha 36) | "Otoscopía + Acumetría" (el valor por defecto) | "Prueba de audífonos" |
| Lo que el paciente trae | Nada | Los exámenes del libro que su procedimiento no nombra, en una entrada del historial: "Audiometría e impedanciometría. Trae los informes. **Ver audiometría · Ver impedanciometría**", 14 días antes de la cita (o justo después de quien los pidió, si eso fue más cerca) |
| Cuándo aparecen en la ficha | — | Con cuenta y chat: cuando el paciente los entrega en el chat (hay que pedírselos). Sin cuenta o en un curso sin chat: desde el principio. En "Mis pacientes" (atención cerrada): enteros |
| En el chat | El paciente decía "traigo los papeles" pero no los podía pasar | Si se los piden, los entrega: aparecen como papeles en la conversación ("Te entrega sus informes: Audiometría · Impedanciometría") y entran a la ficha |
| Exámenes que cuenta la historia | Solo texto | La línea lleva su hoja: "Audiometría de base: normal… **Ver audiometría · Ver EOA**" |
| Tamizajes de la historia | Solo texto | Tarjeta con el resultado de cada oído ("AABR · Oído derecho: Refiere"), sin curva |
| "Ver …" | — | Subventana del MDI, "<Examen> del paciente", con la hoja del libro |
| Chat del paciente | Solo sabía el motivo; no conocía la historia clínica | Conoce la historia clínica ("hace 2 meses el otorrino me mandó…") y lo que trae ("me hicieron una prueba de audición y un examen con una sonda, y traigo los papeles") |
| Docente en práctica libre | Veía el procedimiento de la ficha del caso, sin lo que trae, y su chat de prueba decía "audiometría" | Ve lo mismo que el alumno |
| Ficha abierta y otro paciente elegido en la agenda | Quedaba la ficha del anterior | La ficha cambia sola; la hoja del paciente anterior se cierra |
| Botón de la ficha en la agenda | Siempre "Ver ficha" | "Cerrar ficha" mientras está abierta |
| Carpeta nueva en práctica libre | La primera fila quedaba marcada sin estar elegida; con un solo paciente no se podía ver su ficha | Sin fila marcada; un clic la elige |
| Alumno que repite un examen que trae | — | Puede hacerlo; queda como una atención más en su historial |

## Foco por capítulo

| Capítulo | El procedimiento nombra | Trae el resto de lo que muestra el libro |
|---|---|---|
| H7 Impedanciometría | Impedanciometría | audiometría |
| H9 Emisiones | EOA | audiometría, PEATC (paciente 40) |
| H10 PEATC | PEATC | — |
| H11 ECochG | ECochG | audiometría |
| H12 VEMP | VEMP | audiometría |
| H13 ASSR | ASSR | impedanciometría, EOA, PEATC (al lactante, el PEAT ya está en su historia) |
| Cap. 9 Hidrops | ECochG + VEMP | audiometría, impedanciometría |
| Cap. 11 Asimetría que no cierra | PEATC (+ VEMP si el libro lo muestra) | audiometría, impedanciometría, EOA |
| Cap. 12 El tronco | PEATC (+ VEMP) | audiometría, impedanciometría |
| Cap. 14 Lo que mueve el ABR | PEATC | audiometría, impedanciometría, EOA |
| Cap. 18 El ABR que engaña | PEATC | audiometría, impedanciometría |
| Cap. 20 VEMP | VEMP | audiometría, impedanciometría, ECochG (Ménière) |
| Cap. 30 Oír y no entender | Corticales | audiometría, impedanciometría, EOA |

Lo que trae sale de la ficha del libro en ese capítulo, más la audiometría,
que va antes de todo lo demás. Un paciente de práctica que sale en varias
carpetas (el 34 en H2, H3, H7, H12 y el cap. 4) trae en cada una lo de ese
capítulo: a la de impedanciometría no llega con el VEMP de H12.

Los demás capítulos enseñan un cuadro con toda la batería: el procedimiento
sigue nombrando todo y el paciente no trae nada (salvo lo de su historia). Se
cambia en `FOCO` (`scripts/libro/procedimientos.py`).

## Por qué se decidió así

- **El paciente llega con los otros exámenes hechos, no se le quitan.** En
  la clínica, al que viene a un PEATC lo derivan con su audiometría y su
  impedanciometría. Así el motivo es el examen del capítulo, sin rearmar los
  casos ni borrar datos.
- **Depende del capítulo** (pediste eso): si el capítulo enseña el PEATC y la
  ficha del libro tiene otros exámenes, esos los trae.
- **No se bloquea nada.** Si el alumno repite un examen, queda en su
  historial y se puede evaluar.
- **Se ve dentro de la app.** Los kioskos solo tienen LabSim: las hojas van
  empaquetadas con la app (`resources/libro/previos/<ficha>/`, 1,7 MB) y no
  se bajan de internet.
- **Es la hoja del libro.** Se dibuja con el mismo motor de figuras del libro
  y con los mismos datos cargados en prod (`scripts/libro/previos.py`): lo
  que ve el alumno coincide con lo que mide si repite el examen.
- **La historia lleva su hoja** (el punto 3, "hace que el estudiante sienta
  que está revisando algo"): la línea que cuenta un examen hecho la lleva.
  Si el resultado de entonces calza con el de hoy, es la hoja actual; si
  cuenta otro estado (la base normal antes del cisplatino, el ingreso del
  trabajador), es un caso aparte, a revisar en el libro.
- **El tamizaje es una tarjeta, no una curva.** El equipo de tamizaje entrega
  pasa o refiere por oído; una hoja de emisiones diagnósticas diría más de lo
  que la línea cuenta.
- **Lo que ya cuenta la historia no se repite como algo que trae** (el PEAT
  del lactante de H13 está en su línea de hace tres meses).
- **Solo en la práctica libre** lo que trae: en una cita que agenda el
  docente no aparece; lo decide él. Las hojas de la historia salen siempre:
  son la historia del caso.
- **Si viene a otoscopía, no trae nada** (corrección tuya): todo va después
  de mirarle el oído.
- **Los informes se piden** (lo elegiste): en la consulta el paciente los
  entrega cuando se los piden, y pedirlos es parte de la anamnesis. Sin chat
  no hay a quién pedírselos, así que salen en la ficha desde el principio.
  El modelo marca la entrega y el backend solo acepta lo que el paciente
  trae: no puede entregar un examen que no existe. Cada atención nueva
  empieza con los papeles en la mano del paciente, como el chat empieza de
  cero. Las hojas de la historia no se piden: son el registro del caso.
- **Peso:** las hojas van comprimidas (`.svgz`, que Qt lee directo): 1,7 MB
  en vez de 8,5. Con la fecha del gzip fija, una hoja que no cambia no viaja
  en la actualización.
- **La historia va al chat fuera de la plantilla.** Así una plantilla que
  edites en el panel no la pierde. Vale para todos los casos.

## Pendiente de revisión (en el libro)

Lista en `pendientes_urgentes.md` del libro, "Exámenes previos de los
pacientes en LabSim":

- Seis estados anteriores son provisorios: podman no arranca en este kernel
  y se usaron datos de otro caso del libro con el mismo cuadro y sexo. Se
  regeneran con `armar_casos.sh 'previo_*'` y `previos.py --solo-historia`.
- Cuatro líneas quedaron sin hoja (autoinmune de un solo oído, refuerzo
  visual en campo libre, la audiometría real del que exagera, un PEATC sin
  figura).
- Dos tarjetas de tamizaje con un oído inferido.

## Cambios en prod

- Audiometría previa: 27 procedimientos (respaldo `labsim_2026-10-29_102210.sqlite`).
- H21, ficha 36: "Prueba de audífonos" (respaldo `labsim_2026-10-29_112919.sqlite`).
- Foco por capítulo: 30 procedimientos más (respaldo `labsim_2026-10-29_133700.sqlite`).
- Los intentos que ya estaban abiertos conservan el procedimiento anterior;
  los nuevos toman el nuevo.

## Dónde está cada cosa

- Regla, ficha y ventana: `src/core/ficha.py` (`examenes_que_trae`,
  `enlaces_de_la_historia`, `HojaPrevia`, `fila_de_practica`).
- Ficha que sigue a la agenda y botón Ver/Cerrar: `src/agenda/Agenda.py`.
- Subventana: `PREVIO` en `labsim_backend/src/Layout.php`; `src/main.py` la
  agrega si el backend todavía no la manda.
- Chat: `LlmConfig::historiaPrevia`, `EXAMEN_PREVIO` y `separarEntrega`
  (`labsim_backend/src/LlmConfig.php`); la app manda `trae` y recibe
  `entrega` en `llm_chat.php`. En la app: `ChatPacienteWidget.entrego` →
  `main._al_entregar_informes` → `core.ficha.registrar_entrega`.
- Hojas: `scripts/libro/previos.py` (con `historia_examenes.json`, la tabla de
  las líneas de la historia) → `resources/libro/previos/`. Se vuelve a correr
  si cambia un caso o el dibujo del libro.
- Procedimientos: `FOCO` y `PROC_PROPIO` en `scripts/libro/procedimientos.py`, que usan
  `sql_practica.py` y `previos.py`.
