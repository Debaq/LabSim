# Roadmap: práctica libre = los pacientes del libro

Decidido con el autor el 2026-10-28. Reemplaza la lista de práctica que
cada docente armaba por curso (`practice_cases`).
Libro: `~/Escritorio/Proyectos/libro-orl`.

## Qué se decidió

- **La práctica libre son los pacientes del libro**, en carpetas por
  capítulo y en el orden en que aparecen en el capítulo. Ya no hay lista
  por curso: la que armaba cada docente sale.
- **Dos entradas desde el login:**
  - **Sin cuenta** ("Practicar con los pacientes del libro"): sin red. Se
    hacen los exámenes, pero no hay chat con el paciente (gasta tokens) y no
    se guarda nada. En vez del chat, la anamnesis escrita del caso.
  - **Con cuenta:** los mismos pacientes, con chat y con el avance guardado
    (cada intento con su evolución, informes y técnica, como hoy).
- **Lo que LabSim todavía no simula** (nasal, vestibular salvo VEMP) no se
  ofrece por ahora. Entra cuando haya módulo.

## Lo que ya hay

- `libro-orl/material/casos/generados/<cap>_<nombre>.json`: 144 casos que
  armó LabSim, `{pedido, semilla, data}`, con `data` en el formato de
  `cases.data`. Unos 2 MB en total.
- `libro-orl/material/casos/pacientes_demo.json`: los 10 pacientes de
  práctica (33-42), que ya están en prod con esos mismos ids.
- `libro-orl/material/casos/<cap>_<nombre>.json`: qué figuras usa cada caso
  (`audiosupra`, `impedancia`, `vemp`…). De ahí sale qué módulos necesita.
- `texto/capitulos/NN-*.py`: los casos de cada capítulo, en orden (`CASOS`).
- Los intentos ya hechos en prod son de los pacientes 33-42, que también
  son del libro: no se pierde nada.

## Fases

- [x] **F0. Carpetas (2026-10-28), vacías.** Backend: `practice_folders` y
  `practice_items` (un paciente puede estar en varias carpetas),
  `appointments.practice_item_id` para los intentos; `Practica.php`
  reescrito (`lista`, `iniciar`, carpetas); `api/practica.php` manda
  `carpetas` y la lista plana `items` para las apps de antes. Panel:
  Docencia → Práctica libre (`admin/practica.php`, solo admin completo):
  crear, renombrar, ordenar y borrar carpetas; agregar, ordenar y sacar
  pacientes. La pestaña Práctica de cada curso se fue. App: en Práctica
  libre, las carpetas a la izquierda y la tabla con los pacientes de la
  elegida, columna N° con su lugar; al buscar, en todas. Los 33-42 quedaron
  archivados y toda la lista vieja por curso apagada: la práctica arranca
  vacía.

- [ ] **F1. Catálogo del libro en la app.** `scripts/catalogo_libro.py` lee
  el libro y escribe `resources/libro/catalogo.json`:
  `[{carpeta, titulo, orden, pacientes: [{clave, nombre, edad, sexo, procedimiento, modulos, data}]}]`
  en el orden del libro, dejando fuera los pacientes que necesitan un módulo
  que no existe. La práctica libre de la app muestra el árbol carpeta →
  pacientes numerados. Revisar que no lleve nada privado (los casos del
  libro son inventados).
- [x] **F2a. Tomo II cargado (2026-10-29).** 25 carpetas (caps. 1-20, 28-30,
  33-34), 99 pacientes, 97 fichas: 89 nuevas (49-137, en la carpeta
  "Libro" de Fichas Clínicas) y 33-38, 41, 42 desarchivadas. N° = el número
  del caso en el libro (caso 1.4 -> 4), con huecos donde el caso no se
  simula. Fuera: los vestibulares (21-27, 31, 32) y nasales (35-38), y los
  casos sin un examen de LabSim (otitis externa 1.3...). RUT cambiados
  porque chocaban: Rocío Torres (12.1) 18087953 (el del libro es de
  Carolina, 34) y los lactantes del 17, Alba 28268815 y Jorge 28268816 (los
  tres tenían el mismo). Scripts: `scripts/libro/catalogo_tomo2.py` y
  `sql_practica.py`; backup previo `labsim_2026-10-29_000515.sqlite`.
- [x] **F2a+ (2026-10-29).** Sumada la otitis externa (1.3, ficha 138): en
  los capítulos que entran va todo paciente, aunque no traiga figura de
  examen (se practica con otoscopía y acumetría). `sql_practica.py` ya no
  corre los números al sumar un caso (lee `ids_libro.json`). Fotos subidas
  con la consola: 98 caras y 169 otoscopías (fase 0), de
  `material/rostros/<caso>.jpg` (`demo-NN.jpg` para 33-42) y
  `material/otoscopias/<caso>_<od|oi>.jpg`. El libro no tiene otoscopía de
  27 oídos (caps. 16-19 casi enteros, OI de Luis 41, entre otros): en LabSim
  quedan sin foto.
- [x] **Caras de los acompañantes de los menores (2026-10-29).** Los 24
  menores traen a la madre en la sala; el libro solo hizo la cara del
  paciente. Generadas con Gemini Lite a partir de la cara del hijo (parecido
  de familia, edad y modo de la sala), revisadas y subidas con
  `consola.py rostro <id> --persona <id>`. Quedan en
  `libro-orl/material/rostros/acompanantes/<caso>__<rol>.jpg` (hay una de
  más, cap26_pendred, capítulo vestibular). Ojo: desde este equipo urllib se
  cuelga con Gemini (IPv6); curl responde en segundos.
- [x] **F2b. Tomo I (2026-10-29).** 14 carpetas de herramientas (H1-H12,
  H21, H24; las demás no declaran pacientes), antes del Cap. 1 como en el
  libro (orden -100 + n). Repiten las fichas del Tomo II (Tomás 33 en H3,
  H9, H12, H24) y suman 9 propias (139-147) y los 39 y 40, desarchivados.
  El lactante de H10 (Álvaro) tenía el RUT de Andrea (17.1): va con
  28267995. Los tres de H10 no tenían cara en el libro: hechas y sumadas a
  `rostros/pedidos.json`. Total: 39 carpetas, 142 pacientes, 109 fichas,
  28 madres con cara. Backup previo `labsim_2026-10-29_004607.sqlite`.
- [x] **Auditoría de las 109 fichas (2026-10-29).** Todas traen todos los
  exámenes (tonal, logo, supraliminares, acumetría, Z 226/1000, reflejos,
  EOA, ABR con ECochG, VEMP, sala). Faltaba el bloque `Central` en 89: sin él
  la latencia media y tardía sale plana, como una ausencia patológica. Se
  les puso la vía central sana (`CaseBuilder::CENTRAL_DEFAULTS`, lo mismo
  que escribe el editor al guardar); los cuadros de tronco y neuropatía se
  modelan en el ABR, no en ese bloque. La 139 (dilema de H4) no tenía
  relato ni historia, y la 147 y la 102 no tenían historia: los escribió
  Claude coherentes con el cuadro, con nota en el comentario docente para
  revisar. Procedimientos del Tomo I corregidos (el mapa no conocía
  audiograma/timpanograma/acumetria). Backup `labsim_2026-10-29_005817.sqlite`.
  La app deja hacer cualquier examen a cualquier edad (una audiometría
  tonal a un recién nacido "responde"): elegir el que corresponde es parte
  de lo que se evalúa.
- [x] **Audiometría previa (2026-10-29).** En los caps. 9, 11, 12, 14, 18,
  20, 30 y H12 el paciente llega con la audiometría hecha: el procedimiento
  no la nombra y la ficha la muestra con "Ver informe" (hoja del libro en
  `resources/libro/previos`, `scripts/libro/previos.py`). Ver decisiones.md.
- [x] **Avance del alumno (2026-10-29).** "N de M casos" y avance por
  carpeta en la práctica libre de la app y en el portal (launch.php). Sin
  ranking. Ver decisiones.md.
- [ ] **F2. Llenar las carpetas con el libro.** Importar los casos del libro
  al backend (fichas con clave fija) y crear una carpeta por capítulo con
  sus pacientes en el orden del libro, por la consola o un script. Las
  fotos, con `consola.py otoscopia/rostro`.
- [ ] **F3. Modo sin cuenta.** Botón en el login. Sesión de invitado sin
  backend: los casos salen del catálogo, sin sync, logs, informes ni chat;
  autoguardado en modo prueba. Revisar cada módulo por llamadas al backend
  (normativa del curso → la de fábrica, fotos, avisos de la secretaria).
- [ ] **F4. Imágenes sin red.** Otoscopías y rostros de los pacientes del
  libro empaquetados con la app (ver tamaño; `labsim_build_sin_datos_privados`).
- [ ] **F5. Ficha de estudio** al cerrar el intento: la del libro, ya
  generada, sin redactor IA en el modo sin cuenta.

## Preguntas abiertas

- ¿Qué hacer con los pacientes de práctica de un curso que no están en el
  libro? Hoy son solo los 33-42 y esos sí están.
