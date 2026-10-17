# Estado del libro y pendientes (traspaso 2026-10-15, al día 2026-10-16)

Para retomar en una conversación nueva: leer este archivo, `LEEME.md`
(carpetas y comandos) e `indice.md` (plan). Las decisiones de fondo están en
`docs/decisiones.md` (buscar "Libro:" y las secciones del 2026-10-15).

## El libro

- **Título:** *Evaluación y rehabilitación en otorrinolaringología. Un libro
  de casos clínicos.* Un solo libro que crece por secciones (audición →
  equilibrio → nariz → rehabilitación). Gratis, CC BY-NC-SA 4.0. Primera
  edición, TecMedHub · UACh Sede Puerto Montt. Sin autores por ahora
  (previstos en `herramientas/hacer_libro.py`, `AUTORES_PREVISTOS`).
- **Una sola edición:** la guía del docente (`:::docente`) va dentro de cada
  caso.
- **Simuladores de apoyo:** LabSim (audición, VEMP); trainHIT y labyrinthus3d
  para lo vestibular (LabSim NO se expande a vestibular). Idea a validar con
  él: el motor del libro llama a labyrinthus3d por Node (sin portarlo a
  Python) y dibuja en Python; hacer primero una figura de prueba (nistagmo de
  neuritis).
- **Compilado:** `libro.pdf` (~420 págs.). Armar un capítulo rearma después
  el libro completo (~8 min, índice en dos pasadas).

## Capítulos

| Estado | Capítulos |
|---|---|
| Escritos y al día con los simuladores | H1-H10, 1-6, 11 (H3 y H6 ampliadas el 2026-10-16) |
| Esqueleto (por escribir) | H11 ECochG, H12 VEMP, H13 PEAee, 7-10, 12-20 |
| Esqueleto nuevo (2026-10-16) | B1 anatomía, B3 histología, B4 física (cada uno con "Qué tiene que tener"); H14 procesamiento auditivo central (capturas de AudioPAC); equilibrio H15-H19; rehabilitación aural H20-H21; salud ocupacional H22; nariz H23-H25 |
| Partes reservadas (esqueleto, 2026-10-16) | VIII equilibrio (21-27), IX rehabilitación auditiva (28-30), X rehabilitación vestibular (31-32), XI salud ocupacional (33-34), XII nariz (35-36); los integradores pasan a Parte XIII |
| Lo escribe una colega | B2 Fisiología auditiva y vestibular (con su lista de contenidos) |

Cómo se escribe uno: un agente por capítulo con `herramientas/brief_agentes.md`
(reglas, sintaxis, flujo) + el pedido del capítulo (casos del índice,
capturas de `docs/manual/img/estudiante/`, secciones del protocolo en
`fuentes/protocolo.txt`, privado), PUERTO distinto por agente, sin commit;
después se revisa el PDF (`salida/capitulo-N.pdf`), se commitea y queda
`libro.pdf` al día. Capítulos clínicos: formato ABP como el 2.

**Estilo (exigencias de él):** su práctica manda; los recuadros "Lo que dicen
las normas" exponen la norma en forma neutra y el texto argumenta la lógica
del laboratorio (nunca reforzar la norma contra su práctica). Errores
factuales del protocolo se corrigen con bibliografía en comentario HTML. No
nombrar el protocolo en el texto visible. Nada de imágenes de IA para
anatomía/esquemas (plan: Servier/OpenStax, SVG propio, capturas).

## Pendientes

### Cola de tandas (loop, decidido por él 2026-10-16)
Un agente por capítulo, tanda de hasta 4 en paralelo, puertos 8811-8814,
`LIBRO_SIN_COMPLETO=1` (cada agente arma solo su capítulo; libro.pdf lo
rearma el coordinador al cerrar la tanda). Al cerrar una tanda: revisar los
PDF, rostros nuevos (pedidos.json + `herramientas/rostros.py`), libro.pdf
completo, incongruencias a `incongruencias_protocolo.md`, commit en main y
marcar la tanda acá.

- Material de clases: `fuentes/clases/LEEME.md` dice qué clase sirve a qué capítulo (alcance, no copiar ni citar ni nombrar a quien la dictó).
- Secciones del protocolo (líneas de fuentes/protocolo.txt): H11 y H14 no tienen; H12 4342-4628 (cVEMP y oVEMP); H13 5567-5677; H15 3239-3666 (Frenzel 3239, VNG 3463); H16 3667-3820; H17 4629-4753; H18 4105-4341; H19 3821-4104; H20 2795-3176; H21 3177-3238; H22 1490-1830 (screening y operativo; "operativo" = operativo de salud, no ocupacional) más el ítem de ruido de la anamnesis (~178); H23 2452-2535; H24 2536-2652; H25 2653-2794.
- Instrucciones comunes de los agentes: `herramientas/tanda_comun.md` (cada pedido la nombra).
- [x] Tanda 1 (2026-10-16): caps. 7, 8, 9, 10 escritos (Opus), referencias cotejadas con Crossref/PubMed, 13 rostros. Arreglos del armador: ECochG de un oído sin complejo, "Hace 1 día", ancla del pico en timpanograma B (rehechos cap02 OMA y p35, cap03 p41, h7 p35, cap08), `:::figura ... campo_libre`, pausa y reintento al guardar casos en armar_casos.py, `LIBRO_SIN_COMPLETO=1`. Incongruencias #43-50. Quedan `verificar` (cap. 7: 2, cap. 8: 1, cap. 9: 4, cap. 10: 10). Los dos "Samuel" (caps. 6 y 9) se dejan: el nombre lo sortea el editor y cuadro() no lo fija.
- [x] Tanda 2 (2026-10-16, agentes Sonnet + revisión y verificación de referencias): H11 ECochG (15 págs., 4 esquemas propios), H12 VEMP (21), H13 estado estable (12, sin LabSim: 2 esquemas propios), H14 procesamiento central (22, capturas de AudioPAC corrido local con datos inventados y rotulados). Incongruencias #51-64. Placeholder pendiente: `ilustraciones/h12-vias.png` (vías cVEMP/oVEMP). Huecos al pie en H14 pp. 13-14 (pasada final). Cap. 9 dice "el detalle estará en H11": pasar a "(→ H11)" cuando se toque. Quedan `verificar`: H11 2, H12 4, H13 2, H14 5.
- [x] Tanda 3 (2026-10-16, Sonnet + revisión + referencias): H15 Frenzel/VNG (18 págs.), H16 calórica (11), H17 vHIT (17), H18 maniobras (17). Imágenes: capturas de labyrinthus3d (corrido local, solo lectura) y de trainHIT (de su manual), esquemas propios con scripts `ilustraciones/hacer_h15..h18*`. Incongruencias #65-84. Quedan `verificar`: H15 5, H16 4, H17 6, H18 4. Huecos al pie: H15 pp. 7 y 9, H17 p. 9. Capturas de trainHIT en tema oscuro (desentonan; rehacerlas en claro si el simulador lo permite).
- [x] Tanda 4 (2026-10-16, Sonnet + revisión + referencias): H19 rehabilitación vestibular (18 págs., labyrinthus3d postural), H20 prueba de audífonos (13), H21 medición electroacústica (11, esquemas propios), H22 audiometría ocupacional (20; guía ISP v3.0 2026, que también actualizó H3). Incongruencias #85-100. Además: LDL con triángulo vacío (relleno = algiacusia) en libro y app; lámina de símbolos de H3 en una sola página; H3.7 (escalera ascendente) quitada por repetida en la H3.8; H10.1 ahora es captura de labyrinthus3d (Tronco + PEAT). Quedan `verificar`: H19 8, H20 4, H21 3, H22 7.
- [x] Tanda 5 (2026-10-16, Sonnet + revisión + referencias): H23 anamnesis rinológica y rinoscopía (12 págs.), H24 rinomanometría anterior (11), H25 rinometría acústica (11). Sin simulador nasal: esquemas SVG propios (`ilustraciones/hacer_h23..h25.py`) y ejercicios numéricos calculados en H24. 39 referencias cotejadas (DOI en Crossref, PMID en PubMed); Rohrer 1915 completado. Incongruencias #101-121 (varias son de la clase, no del protocolo: valores de RA en mm/cm mezclados, "150 Pa = radio 2"). Arreglo del armador: un capítulo sin casos ya no llama a `hacer_figuras.py` sin nombres (rehacía todas las figuras del libro: era lo que colgaba los armados de las tandas 3-5). Quedan `verificar`: H23 15, H24 7, H25 7.
- Él, 2026-10-16: "las tandas continúan con los capítulos faltantes" (antes decía que el loop terminaba en la 5 y que los clínicos 12-36 no entraban). Capítulos clínicos: modelo único cap. 11 (ABP) y su .py; ABR según `ROADMAP_ABR.md` (Hood sin citar hasta tener su índice); vestibulares y nasales con las reglas de las tandas 3 y 5 (sin LabSim). Bases con ilustraciones libres (Servier, OpenStax) o SVG propio; B2 la escribe la colega y no entra.
- [ ] Tanda 6 (en curso desde 2026-10-16): caps. 12 el tronco, 13 oye pero no entiende, 14 lo que mueve el ABR sin ser el oído, 15 cuando también cae la ósea
- [ ] Tanda 7: caps. 16 tamizaje, 17 el lactante que se estudia, 18 el ABR que engaña, 19 el paciente que no calza
- [ ] Tanda 8: caps. 20 VEMP, 21 vértigo agudo, 22 gira al acostarse, 23 crisis que vuelven
- [ ] Tanda 9: caps. 24 cuando fallan los dos lados, 25 lo que viene de arriba, 26 una tercera ventana, 27 mareo que no se va
- [ ] Tanda 10: caps. 28 el primer audífono, 29 cuando el audífono no alcanza, 30 oír y no entender, 31 compensar una neuritis
- [ ] Tanda 11: caps. 32 volver a caminar sin miedo, 33 el trabajador expuesto a ruido, 34 el caso médico-legal, 35 nariz tapada
- [ ] Tanda 12: cap. 36 rinitis y vasoconstrictor, B1 anatomía, B3 histología, B4 física
- Fin del loop al cerrar la tanda 12.

### Para retomar (2026-10-16)
- Él pidió **no seguir con capítulos nuevos** por ahora (reemplazado por la cola de tandas de arriba).
- Siguiente propuesto (espera su visto bueno): la pasada de "fundamento
  fisiológico" en H1, H2, H4, H5, H7, H8, H9 y H10 (como se hizo en H3 y H6).
- `incongruencias_protocolo.md`: él lo decide con su equipo. Regla: se
  mantiene el protocolo y la literatura va en "Lo que dicen las normas"; solo
  se corrige lo que es error. Los "P · revertir" esperan su decisión; el
  método de búsqueda del umbral (13b) está en discusión.
- Sin "el laboratorio" en el texto (distribución mundial).
- Fotos de los pacientes 33-42 en LabSim: él las sube desde el panel con
  `rostros/demo-NN.jpg`.
- Práctica offline de los pacientes del libro (sin red ni cuenta): por
  diseñar.

### Para él (decisiones o datos)
- **Formato de página: decidido 2026-10-16.** A4; texto en Source Serif 4 a 9,5 pt, interlínea 1,3, justificado con partición; figuras del motor con los globos al costado (`TIPO`/`ORDEN` en hacer_libro.py). Libro: 780 → 700 págs. Pendiente para bajar más: achicar figuras del motor y conectar acomodar.py.
- **LDL en H3 (pedido 2026-10-16, sin empezar):** agregar a la lámina y al texto todas las convenciones (triángulo chileno, └ ┘ de la BSA, "m" en España, "U" en programas en inglés), decir que unir o no es elección y no protocolo, y que el símbolo cambia según el lugar (fuentes en investigacion/simbolo_ldl.md).
- **LDL unido con guiones**: lo pidió en la revisión del 2026-09-10; el audiograma de ejemplo de la clase de simbología lo deja sin unir. ¿Se une o no?
- **H19:** ejercicios oculomotores con la cabeza quieta (#85) y el "Test de Norré" (#90).
- **labyrinthus3d, PEAT con generadores de Møller** (2026-10-16, a su pedido): cambios sin commit en ese repo (js/auditiva.js, js/oido.js, textos, README, tests: 250 pasan). Ojo: `bump.mjs` metió en el importmap `js/oido3d.js`, que está sin seguimiento en git (de otro trabajo): comitear juntos o el test de versión falla. H10.1 ya recapturada con el simulador nuevo.
- **H18: restricciones después de la maniobra.** El protocolo manda dormir semisentado 2 noches; la AAO-HNS 2017 recomienda con fuerza NO indicarlas (grado A). Hoy: protocolo + recuadro (#81). También #83 (Lempert "apogeotrópico", quitado) y #68 (cortes de la calórica distintos entre secciones del protocolo).
- **Simuladores vestibulares** (no se tocaron): labyrinthus3d rotula la fase lenta en su tabla calórica (puede confundir: el nistagmo se nombra por la rápida); el libro nombra los simuladores como "software libre del autor" sin URL ni institución: ¿se agrega la URL?
- **H13: ¿ABR antes del estado estable?** El protocolo no lo pide; BSA 2023 lo exige (descartar neuropatía). Hoy va en recuadro de normas (#61).
- **LabSim, hallado al escribir H11/H12** (no se tocó el simulador): ECochG del paciente 33 arreglada (commit 4c22b2b7); VEMP con escala aérea propia en dB SPL (50-125, umbral normal ~60) en vez de nHL, banda de EMG 30-150 µV (la literatura pide ≥ 80), `resources/vemp/normative_data.json` sin fuente ni DE, sin impedancias y un solo umbral por tipo.
- **ABR según Hood (1998):** aprobado por él; plan en `ROADMAP_ABR.md` (caps. 11-19, para después del loop de las H). Falta el índice completo del libro de Hood antes de citarlo.
0. **PEAT "cada nivel dos veces"** (nota de él, 2026-10-16): es la pila duplicada del simulador (memoria labsim_abr_pila_duplicada), anotada en `ROADMAP_ABR.md` entre los pendientes del simulador.
1. **Inventario vestibular/nasal** (`investigacion/inventario_vestibular_nasal.md`):
   detalles menores (licencia de simHit, DOI de labyrinthus3d, coautorías).

Cerrados el 2026-10-16 (producción reproyectada, pacientes 34 y 41, H8, H10):
`docs/decisiones.md`, "Pendientes del libro cerrados con él". El corte del
STAT terminó en un cambio del modelo: "LDL: la tolerancia es del paciente".

### Errores del simulador detectados
- **ISO 7029:** resuelto 2026-10-16, el simulador usa ISO 7029:2017
  (decisiones.md). Los casos ya armados conservan su audiograma.
Los siete que había quedaron arreglados (2026-10-15); qué se decidió en cada
uno está en `docs/decisiones.md`, "Errores del simulador detectados al
escribir el libro". Para usar en los capítulos: `fig.abr()` ya elige
`transductor`, `polaridad` y `tasa`; hay `fig.campo_libre(ganancia=...)`; la
TEOAE del libro sale con click no lineal a 80 dB SPL. Los casos ya armados
no se rehicieron: un capítulo que se vuelva a armar puede cambiar de curva
(Paget/fijación con gap ya no salen A) o de fichas (cada caso no abre página).

### Orden y alcance (él, 2026-10-16)
- **Salud ocupacional** (H22, Parte XI) se escribe al final de todo.
- **Audiología aplicada** = casos clínicos (no audífonos): ya es el cuerpo
  del libro, Partes I-VII y los integradores (Parte XIII).
- Él va a pasar sus clases de **nasal** y **auditivo parte I** (no hay
  otras) como guía del alcance de los contenidos (referencia, no para copiar).

### Armador
- **Armado incremental** (hecho 2026-10-16): `armado_incremental.py`, lo usa
  `hacer_libro.py` para el libro completo. Capítulos con caché en
  salida/cache/ (huella = HTML + CSS + imágenes), compuestos en paralelo;
  números de página estampados, índice y marcadores rehechos. Desde cero
  ~2,5 min; sin cambios ~1,3 min. `--de-una-pieza` = el armado viejo.

- **Huecos al pie de página** (para la pasada final, él lo pidió así): ~85
  páginas con más de un tercio vacío, por figuras y recuadros que no caben y
  saltan enteros. `herramientas/acomodar.py` (sube el texto siguiente cuando
  una figura salta; acepta solo movidas que bajan el hueco) está hecho pero
  DESCONECTADO: es lento (H3: ~45 s) y en H3 bajó de 7 a 4 huecos; en otros
  capítulos los huecos son de recuadros. Retomar en la versión cerrada.

### Libro, contenido
- **Rostros** (hechos 2026-10-16): 38 personas en `rostros/` (JPG 512 px),
  uno por persona (`demo-NN` para los de práctica), pedidos en
  `rostros/pedidos.json`, generador `herramientas/rostros.py`. Gemini no
  dibuja malformaciones: la microtia de Ramón (cap. 1) va tapada con un
  gorro y el cráneo del Paget (cap. 4) sale apenas sugerido. El lado de un
  signo se pide según la imagen ("lado derecho de la imagen"), no según el
  paciente: así lo confundía.
- Ilustraciones pendientes (según el plan, no IA): H8 sala de VRA y banana
  S/A (en verde), H9 sonda en el conducto, H10 generadores I-V, cap. 2 trompa niño vs
  adulto, cap. 4 formas del reflejo; `ilustraciones/*.png` actuales son de
  Gemini y él las dio por "llenas de errores".
- Quedan comentarios `<!-- verificar -->` en todos los capítulos (citas sin
  texto completo leído, cifras de fuentes secundarias).
- Stenger positivo no ilustrable hasta poder cargar el umbral verdadero del
  oído fingido (TODO 45).
