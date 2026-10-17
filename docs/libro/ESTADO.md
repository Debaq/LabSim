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
- [x] Tanda 6 (2026-10-16, Sonnet + revisión + referencias): caps. 12 el tronco (21 págs., 5 casos de 8), 13 oye pero no entiende (18, 4), 14 lo que mueve el ABR sin ser el oído (17, 4; esquema propio de temperatura), 15 cuando también cae la ósea (19, 5 de 6). 17 rostros nuevos. Incongruencias #122-129 (#124: falta decidir el formato del informe con "patrón de neuropatía"). Tope del vibrador óseo: el código usa 55 dB nHL desde 84bc3f19 (decisiones.md decía 50: corregido). Quedan `verificar`: cap. 12 5, cap. 13 5, cap. 14 3, cap. 15 2. Pendientes menores: cap. 11 da para Jiang "I 8 %, III 11 %, V 14 %" y H10 "I 4-10, III 9-13, V 12-15 %" (unificar el 11); `cuadro()` no fija semanas ni peso al nacer (van en el relato); LabSim no tiene campo de temperatura.
- [x] Tanda 7 (2026-10-16, Sonnet + revisión + referencias): caps. 16 tamizaje (13 págs., 4 casos), 17 el lactante que se estudia (19, 4), 18 el ABR que engaña (18, 5 pacientes de práctica; figuras de artefactos calculadas con el generador real, `ilustraciones/hacer_cap18.py`), 19 el paciente que no calza (19, 4; esquema propio del Stenger). Incongruencias #130-138. H9 corregido (TEOAE antes de 48 h: más de un tercio refiere, no "más de la mitad"). Rostros: 7 nuevos (caps. 16 y 19); **faltan 2 del cap. 17** (rubéola: niña con cataratas, quitada la foto vieja de un niño; efusión neonatal) porque la API de imágenes respondió 402 (sin créditos). Quedan `verificar`: cap. 16 3, cap. 17 3, cap. 18 3, cap. 19 7. Pendiente del armador: `cuadro()` no fija los campos del parto (semanas, peso, UCI, TORCH): van en el relato; Stenger positivo sigue sin poder ilustrarse (TODO 45).
- [x] Tanda 8 (2026-10-16, Sonnet + revisión + referencias): caps. 20 VEMP (17 págs., 4 casos; figuras propias de ramas y vía ósea con el motor de LabSim), 21 vértigo agudo (18, 4; hojas de cabecera HINTS propias), 22 gira al acostarse (14, 4; esquemas de trazas + captura de labyrinthus3d), 23 crisis que vuelven (20, 4; esquemas propios). Incongruencias #139-143. Bug del editor arreglado (tasa de ECochG, commit e8b4b09f). H17: la disociación calórica-vHIT remite al cap. 23. **Rostros pendientes (API sin créditos):** 17 en cola (caps. 17, 20, 21, 22, 23): correr `herramientas/rostros.py`. Quedan `verificar`: cap. 20 1, cap. 21 1, cap. 22 1, cap. 23 11.
- [x] Tanda 9 (2026-10-16, Sonnet + revisión + referencias): caps. 24 cuando fallan los dos lados (20 págs., 4 casos; captura de trainHIT bilateral), 25 lo que viene de arriba (21, 4; trazas de labyrinthus3d), 26 una tercera ventana (14, 3; la dehiscencia en esquema propio porque el motor no la escribe), 27 mareo que no se va (19, 3; posturografía de labyrinthus3d). Además H24 y H25 pasaron a las curvas y pantallas de RinoSim (`ilustraciones/hacer_h2425_rinosim.sh`). Incongruencias #144-155. **Rostros pendientes (API sin créditos): 32 en cola** (caps. 17, 20-27): correr `herramientas/rostros.py`. Quedan `verificar`: cap. 24 6, cap. 25 2, cap. 26 4, cap. 27 9.
- [x] Tanda 10 (2026-10-17, Sonnet + revisión + referencias): caps. 28 el primer audífono (16 págs., 4 casos; campo dinámico y CROS en esquemas propios), 29 cuando el audífono no alcanza (17, 4; regla 60/60, NICE TA566, conducción ósea), 30 oír y no entender (19, 3; perfiles z propios), 31 compensar una neuritis (18, 3; hojas de seguimiento con el generador de H17 y balanceo de labyrinthus3d). Incongruencias #156-162. H14 remite al cap. 30 (no al 13). **Rostros pendientes (API sin créditos): 44 en cola.** Quedan `verificar`: cap. 28 5, cap. 29 3, cap. 30 12, cap. 31 2. Pendiente del armador: `fig.campo_libre()` no expone `audifono`; `cuadro()` no fija el LDL; `autoinmune` no tiene grado profundo.
- [x] Tanda 11 (2026-10-17, Sonnet + revisión + referencias): caps. 32 volver a caminar sin miedo (20 págs., 3 casos; trazas posturales de labyrinthus3d), 33 el trabajador expuesto a ruido (12, 3), 34 el caso médico-legal (18, 3; fórmulas AMA y SUSESO, ver "Para él"), 35 nariz tapada (16, 3; curvas de RinoSim y una TC CC BY de PMC). Incongruencias #163-166. **Rostros pendientes (API sin créditos): 56 en cola.** Quedan `verificar`: cap. 32 3, cap. 33 5, cap. 34 5, cap. 35 2.
- [ ] Tanda 12 (en curso desde 2026-10-17): cap. 36 rinitis y vasoconstrictor, B1 anatomía, B4 física (él, 2026-10-17: de las Bases solo anatomía y física; B3 histología no se escribe por ahora, B2 es de la colega)
- Él, 2026-10-16 (noche): el loop paró al cerrar la tanda 9; el 2026-10-17 dijo "continuamos": siguen las tandas 10-12. Fin del loop al cerrar la tanda 12.

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
- **Cap. 34 (médico-legal): fórmulas de daño sin la fuente primaria leída.** La de las Guías AMA 5.ª ed. sale de una decisión del ECAB (EE. UU.) que la cita; la tabla SUSESO que pasa el promedio a % de daño (Circular 3G/40 y B33/47) no se pudo leer y el capítulo remite la conversión a la comisión. Conviene que alguien con acceso las coteje antes de publicar.
- **Créditos de la API de imágenes (Gemini) agotados** (402, 2026-10-16): faltan los rostros `cap17_rubeola_congenita` y `cap17_efusion_neonatal` (pedidos ya en pedidos.json; correr `herramientas/rostros.py` cuando haya saldo).
- **Nariz, decidido 2026-10-16:** los gráficos salen de **RinoSim** (`~/Escritorio/Proyectos/rinosim`, hecho 2026-10-16: rinomanometría anterior y rinometría acústica sobre la misma nariz paramétrica, 8 cuadros, errores de técnica, vasoconstrictor, 29 pruebas, Apache-2.0, `tools/figuras.mjs` para el libro; sin push ni URL: ¿se publica?). Sus constantes no son normas (`docs/MODELO.md` lista las cifras sin fuente). Las imágenes de hallazgos, de bancos con licencia verificada: lista en `investigacion/imagenes_nasales.md` (Kaggle: nada usable; 7-NasalEID sin licencia: se puede escribir a sus autores; Commons y PMC CC BY sí). Sin fuente libre: espolón septal puro, pus en meato medio, colapso valvular y fotos de máscara de rinomanometría y rinómetro: ¿fotos propias de los equipos del curso?
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
0. **PEAT "cada nivel dos veces"**: confirmado por él (2026-10-16): la réplica va a propósito: en el libro como las dos líneas finas (subpromedios) de cada nivel, en la ficha PDF como dos trazos por nivel, y ahora también en la vista previa del editor de casos (commit 7eef2cb5). No es un bug.
1. **Inventario vestibular/nasal** (`investigacion/inventario_vestibular_nasal.md`):
   detalles menores (licencia de simHit, DOI de labyrinthus3d, coautorías).

Cerrados el 2026-10-16 (producción reproyectada, pacientes 34 y 41, H8, H10):
`docs/decisiones.md`, "Pendientes del libro cerrados con él". El corte del
STAT terminó en un cambio del modelo: "LDL: la tolerancia es del paciente".

### Errores del simulador detectados
- **RinoSim, cornete contralateral a una desviación** (cap. 35): lo modela como mucosa (se abre con vasoconstrictor); Berger 2000 encontró sobre todo hueso engrosado.
- **Cuadro `muesca_4k`** (cap. 33, 2026-10-17): siempre sale profunda (80-100 dB en 4 kHz); no hay forma de armar una muesca incipiente para la vigilancia precoz. Tampoco hay forma de armar el mismo paciente con base y control (otra semilla o cuadro = otra persona).
- **RinoSim (al pasar H24/H25 a sus curvas, 2026-10-16):** el círculo de Broms sale elíptico (ejes con distinta escala); los números de la app y de `tools/figuras.mjs` difieren en la segunda decimal (0,81 vs 0,80); en `cornetes` MCA1 sube de 0,45 a 0,67 con vasoconstrictor (el ejemplo de informe de H25 dice "MCA1 sin cambios"); en la figura de fuga la etiqueta "poco fiable" pisa el trazo; el área llega a ~9 cm² a 10 cm y el Vol 0-5 normal del modelo (~8 cm³) parece bajo; la tabla de la captura casi no se lee en la página. H24 "Leer la curva" corregido (fosa abierta = curva empinada): revisar.
- **Editor de casos, cuadro `meniere`** (2026-10-16): la tasa de ECochG sorteada salía con dos decimales y el campo avanza de a 0,1: el formulario no se enviaba. Arreglado en `generator.js` (redondeo a 0,1).
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
