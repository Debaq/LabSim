# OSCE en LabSim — plan

Primer uso: prueba práctica de ETMP196 (Métodos de exploración
electrofisiológico), **4 de diciembre de 2026**, 17 estudiantes, estaciones de
8 minutos. Alcance: toda la electrofisiología del curso (PEATC, ECochG,
latencia media y tardía, estado estable, VEMP, AABR).

Fuente de las pautas: *Protocolo Técnico ORL 2019* (secciones PEATC clínico,
AABR, cVEMP, oVEMP, estado estable).

## Principio: todo se configura al crear el OSCE

Nada de esto vive en el código: el docente lo llena en el asistente de
creación y el sistema calcula el resto.

| Se configura | Ejemplo 4-dic | Lo calcula el sistema |
|---|---|---|
| Curso y alumnos inscritos | ETMP196, 17 | Códigos aleatorios + QR |
| Fecha y hora de inicio | 4-dic | Horario de cada vuelta |
| Duración de estación | 8 min | — |
| Pausa entre estaciones | 2 min (editable) | — |
| Estaciones (orden, tipo, peso) y circuitos paralelos | 6 × 1 | Vueltas parejas y recorrido de cada alumno; puestos vacíos si sobran |
| Examen de cada estación | PEATC, VEMP… | Límites de impedancia y parámetros esperados precargados del protocolo (editables) |
| Caso(s) de cada estación LabSim | caso + variantes | Sorteo de variante por alumno |
| Escala de nota y exigencia | 1–7, 60 % | Nota por estación y final |
| Ítems críticos | por pauta | Reprobar la estación aunque sume |

Con 17 alumnos, 6 estaciones, 1 circuito y 8 + 2 min (10 entre vueltas):
3 vueltas (6 + 6 + 5), 3 h 18 min. Con 2 circuitos: 2 vueltas (9 + 8). La
página del OSCE muestra el cálculo y el horario de cada vuelta.

## Tipos de estación

Cada estación es de un **tipo** genérico; el examen y el contenido son
configuración. Seis tipos cubren el OSCE del 4-dic.

### 1. `pauta_docente` — Limpieza y preparación de electrodos
Presencial. El docente evalúa en tablet ítem por ítem: tick (cumple /
parcial / no cumple), comentario y marca de crítico.

Pauta precargada para PEATC (editable, y una por examen):
- Material: alcohol, algodón, gel abrasivo, gel conductor, cinta adhesiva,
  otoscopio, riñón metálico, electrodos, cables, fonos de inserción, manta.
- Equipo encendido y verificado; áreas limpia y sucia separadas; lavado
  clínico de manos.
- Explica la limpieza (frente, ceja, detrás de ambos oídos) y que puede
  enrojecer o hacer costra y desaparece en días.
- Alcohol y gel abrasivo **en una sola dirección**; decúbito dorsal.
- Montaje: blanco vértex, negro ceja, rojo mastoide derecha, azul mastoide
  izquierda; gel conductor y cinta.
- Fonos: rojo OD, azul OI, tamaño según conducto.

**Impedancias:** ítem de tipo `impedancias`. El docente anota el valor
obtenido por cable (kΩ) y el sistema calcula solo:
- cada electrodo contra el límite absoluto;
- **interelectrodo** = mayor − menor, y la tabla de diferencias par a par;
- cumple / no cumple con colores.

Cables y límites dependen del examen configurado (precarga del protocolo):

| Examen | Por electrodo | Interelectrodo |
|---|---|---|
| PEATC clínico | < 5 kΩ | < 2 kΩ (mismas constantes que `src/abr/ABR_generator.py`) |
| cVEMP | < 5 kΩ | < 2 kΩ |
| oVEMP | < 3 kΩ | < 1 kΩ |
| AABR | < 12 kΩ | similares |
| Estado estable | < 3 kΩ | — |

### 2. `preguntas` — Preguntas en tablet
- Alternativas: corrección automática por clave.
- Desarrollo: corrige la IA según la pauta de la pregunta (reusa `LlmChat`).
- Banco cargable a mano o importado en GIFT.
- Después de la corrección automática: **feedback del docente** y **réplica
  del alumno**, ambos a mano en la plataforma; el docente resuelve la réplica
  y puede cambiar el puntaje.

### 3. `config_equipo` — Configuración del examen (LabSim)
El equipo abre con los controles sorteados (nunca en el valor correcto). Se
compara la configuración enviada contra la esperada del examen; cada
parámetro admite valor único, lista de válidos o rango.

Esperado PEATC precargado del protocolo: estímulo click / burst / CE-Chirp /
CE-ChirpNB, polaridad alternada, 80 dB nHL, tasa 21,1/s (81,1 si el caso es
sospecha de neuropatía), filtros 100–3000 Hz, ganancia 10k, delay 0,
ventana 10 ms (el protocolo dice "10 s": errata).

### 4. `marcaje` — Marcaje y detección de curvas (LabSim)
Registro ya hecho del caso. El alumno marca ondas, umbral e interpeaks.
Corrección automática contra la verdad del caso: latencias con tolerancia
(por defecto ±0,2 ms), umbral ±5 dB, presencia/ausencia de cada onda.

### 5. `protocolo` — Ejecución del protocolo (LabSim)
El alumno atiende el caso y se evalúa la **estrategia** desde
`action_logs` (los módulos ya registran todo). Reglas PEATC precargadas:
- inicia en 80 dB nHL y verifica I–V;
- baja de 20 en 20 buscando V; sin V sube de 10 en 10;
- sin V a 80 sube a 90–100;
- replica la intensidad máxima y el umbral;
- verifica el contralateral;
- tasa 81,1 si sospecha neuropatía.

Cada regla es un ítem con puntaje; las reglas de cada examen se configuran.

### 6. `conclusion` — Informe
Texto libre con el formato del protocolo. La IA corrige según una pauta
derivada del caso (por OD y OI: ondas a 80 dB con morfología y
replicabilidad, latencias absolutas e interpeaks, umbral de V, tipo de
audición y grado, rango 2–4 kHz). El docente revisa antes de publicar.

### `descanso`
Puesto sin tarea; el sistema lo agrega cuando sobran puestos en una vuelta.

## Identidad del alumno

- Código aleatorio legible (ej. `K7F-3QM`) + token largo para el QR.
- El QR abre `student/osce.php?t=<token>` sin login: durante el OSCE muestra
  en qué estación va y cuáles completó; al final muestra puntaje por estación,
  ítems y comentarios **solo cuando el docente publica**.
- En cada estación el alumno escribe su número, ve su nombre completo y lo
  confirma ("Sí, soy yo: empezar"): ahí parte su tiempo. Sin RUT en la base,
  el nombre hace de verificación (2026-11-25).

## Reloj

Por turnos con tiempo por alumno (2026-11-25, ver `docs/decisiones.md`):
cada alumno tiene sus minutos desde que confirma su nombre en la estación;
el cambio (2 min) parte cuando todas las estaciones del turno cerraron
(entregó, se le acabó el tiempo, ausente o descanso) y el panel del
coordinador (`admin/osce_vivo.php`) dice "cambio" en voz alta. Las
estaciones leen la fase de `api/osce_reloj.php` (`Osce::faseTurno`) y
entregan solas al llegar a cero.

## Sin internet

Las estaciones LabSim guardan local y sincronizan después (patrón de
`docs/roadmap_sin_servidor.md`). Para tablets: la pauta queda en la página y
se reintenta el envío; plan B en papel con la misma pauta impresa desde el
admin.

## Datos (MySQL, PHP 7.4)

- `osce`: course_id, nombre, inicio, duracion_s, pausa_s, pausa_vueltas_s,
  circuitos, exigencia, nota_aprobacion, reloj (inicio_epoch, pausas),
  estado (borrador / en_curso / cerrado / publicado).
- `osce_estacion`: osce_id, orden, tipo, titulo, examen, peso,
  config_json (caso, variantes, tolerancias, límites, esperado).
- `osce_item`: estacion_id, orden, texto, puntaje, critico, tipo (tick /
  impedancias / regla / parametro).
- `osce_pregunta`: estacion_id, tipo (alternativa / desarrollo), enunciado,
  alternativas_json, clave, pauta, puntaje.
- `osce_participante`: osce_id, user_id, codigo, token, vuelta, circuito_json,
  variante_json.
- `osce_resultado`: participante_id, estacion_id, item_id / pregunta_id,
  valor_json, puntaje, comentario, fuente (docente / auto / ia), evaluador, ts.
- `osce_replica`: resultado_id, texto_alumno, respuesta_docente, estado.

## Pantallas

Backend:
- `admin/osce.php` — lista y asistente de creación (con el cálculo de vueltas).
- `admin/osce_estacion.php` — editor de pauta / preguntas / esperado / reglas.
- `admin/osce_vivo.php` — reloj, timbre y tablero de avance.
- `admin/osce_evaluar.php` — tablet del docente (pauta + impedancias).
- `admin/osce_resultados.php` — revisión de IA, feedback, réplicas, publicar.
- `student/osce.php` — página del QR.
- `student/osce_tablet.php` — preguntas y conclusión en tablet.
- `api/osce_*.php` — estación LabSim: abrir con código, enviar resultado.

App LabSim:
- Modo OSCE: entra con código, abre el equipo del tipo de estación con el
  caso asignado, reloj sincronizado, envío automático al timbre.

## Orden de trabajo (para el 4-dic)

1. ✅ Tablas + asistente de creación + códigos/QR + página del QR + reloj
   (2026-11-25). Rotación por circuitos paralelos (no copias sueltas de una
   estación).
2. ✅ `pauta_docente` con impedancias (tablet docente) (2026-11-25).
3. ✅ `preguntas` con corrección automática e IA; feedback y réplica; publicar
   resultados (2026-11-25).
4. ✅ Modo OSCE en LabSim: `config_equipo` y `marcaje` (2026-11-25). El PC
   entra como "Estación OSCE" con el código de la estación.
5. ✅ `protocolo`: parámetros de cada curva + estrategia sobre las curvas de la
   entrega (no `action_logs`), con bonificaciones; ABR y VEMP (2026-11-25).
6. ✅ `conclusion` con IA + revisión docente (2026-11-25). Publicar resultados ya
   estaba desde el paso 3.
7. ✅ Rotación en cadena, tarjetas sorteadas con número (un solo gafete en el
   pecho: número grande + QR y código chicos), panel de control del coordinador, avisos de tiempo
   en cada pantalla y cierre automático; sin timbre ni proyector (2026-11-25).
8. ✅ Estaciones por competencias: tareas con peso %, pacientes variantes por
   número (el mismo en todas las tareas), barra "Siguiente tarea" sin volver,
   ABR y VEMP en la misma estación (2026-11-25).
9. ✅ Marcaje de ECochG (PS/PA) y corticales en su canal (MLR/CAEP Cz, P300
   Pz, MMN Fz); P300 y MMN como exámenes; esperados = `STANDARD_SETUP`;
   oddball al azar en configuración (2026-11-25).
10. ✅ Imagen en las preguntas técnicas (2026-11-25).
11. ✅ Pauta docente con ítems dicotómicos y escala con descriptores; pauta de
    limpieza de 19 pts con escala de comunicación y de desempeño global;
    criterios de conclusión de ECochG y corticales (2026-11-25).
12. ✅ Guía de una hoja con plano de la sala y manual (12 hojas, la guía va
    como hoja 2) en `~/Escritorio/osce/`; fuentes HTML y cómo armarlos en
    `~/Escritorio/osce/fuentes/`. El manual no nombra la IA (a pedido) y trae
    por estación la tabla "Practica en LabSim" con pacientes de la práctica
    libre.
13. ✅ 8 pacientes de latencia media y tardía en la práctica libre (casos
    167-174, fuera del libro; `scripts/practica_lmt/`). Aviso al libro en
    `libro-orl/pendientes_urgentes.md`, sin commitear allá.
14. ✅ Turnos con tiempo por alumno (parte al confirmar el nombre), cambio
    cuando cierran todas las estaciones con "cambio" en voz alta, ausentes
    y "Forzar cambio" en el panel; estación activada solo por un docente
    (usuario y contraseña → lista de estaciones); ventanita de casos con
    indicaciones que se aceptan e ida y vuelta entre casos (también en
    marcaje) (2026-11-25).
15. ✅ En la estación el alumno solo llega a lo de esa estación (sin
    cerrar sesión, sin módulos, sin Electrodos, sin cambiar de prueba, sin
    "Restore Defaults", pestañas por tipo; salir pide clave docente). Se
    conecta todo lo que el alumno toca: vibrador y polaridad en los
    corticales (2026-11-25).

## Pendiente (roadmap al 2026-11-25)

Decisiones que tiene que tomar él:
- **IA en la corrección**: la consulta con el equipo ("muchos odian la IA").
  Si no va, desactivarla y corregir conclusión y desarrollo a mano en la
  revisión. El manual ya no la nombra.
- **Ítem crítico**: hoy solo se marca; ¿reprueba la estación?
- Supuestos del manual a confirmar: exigencia 60 % → 4,0; estación 6 con dos
  exámenes 50/50; estación 5 = 40 % parámetros / 60 % estrategia; esperados
  de configuración (protocolo 2019 + rutina de clases).
- Qué es el rectángulo del centro del plano (¿mesón?) y dónde se juntan para
  el sorteo; grupos de 2 o de 4 (`por_turno`).

Contenido que falta cargar (en el sistema, por estación):
- Estación 2: banco de preguntas técnicas (40 % PEATC, 40 % U-II, 20 % VEMP)
  con imágenes de curvas; ofrecido un borrador en GIFT. Las imágenes se pueden
  sacar de LabSim (capturas de registros con artefacto, impedancia alta,
  filtro mal puesto, tubo pinzado, EMG insuficiente en VEMP).
- Estación 3: las 4 tareas (PEATC umbral 30, ECochG 25, P300 25, cVEMP 20)
  con 2-3 pacientes cada una.
- Estación 4: las 6 tareas de marcaje (PEATC 25, cVEMP 20, ECochG 15, MLR 15,
  CAEP 15, P300 o MMN 10) con pacientes variantes y sus curvas.
- Estación 5: caso pediátrico (lactante que refiere en el tamizaje) en 2-3
  variantes de igual dificultad, con su estrategia y bonificaciones.
- Estación 6: caso integrado (PEATC + VEMP o PEATC + ECochG del mismo
  paciente) en 2-3 variantes, con la conclusión esperada de cada paciente.
- Pacientes nuevos que hagan falta para las variantes (casos con ECochG,
  bloque Central y VEMP).

Sistema:
- Escribir las indicaciones de cada caso (campo nuevo de la tarea).
- Probar el día completo de punta a punta con 17 números (sorteo, cadena,
  las 6 estaciones, panel de control, cierre automático, publicación).
- **Imágenes de los gafetes (tradición del curso, él pidió anotarlo):** cada
  año el gafete lleva el dibujo de un ser vivo con su nombre, de un tema que
  cambia por año, "para culturizar" (hace tres años peces, después un animal
  chileno, el año pasado dinosaurios). Los alumnos los guardan; los de 2026
  esperan el suyo. Falta: elegir el tema de 2026 (sin repetir), hacer las
  ilustraciones (una por número, 17+) con nombre común y científico, y
  ponerlas en la tarjeta (`admin/osce.php?tarjetas=1`) junto al número sin
  tapar el QR ni el código.
- Opcional: tabla consolidada de notas con exportación CSV; pauta en papel de
  respaldo por si falla la red.
