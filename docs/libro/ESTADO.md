# Estado del libro y pendientes (traspaso 2026-10-15)

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
| Escritos y al día con los simuladores | H1-H10, 1, 2, 3, 4, 11 |
| Esqueleto (por escribir) | H11 ECochG, H12 VEMP, H13 vestibular (vol./sección futura), H14 PEAee, 5-10, 12-20 |
| Lo escribe una colega | B1 Fisiología auditiva |

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

### Para él (decisiones o datos)
1. **Token de la consola remota** (`./scripts/labsim_token.sh lsc_...`) para
   reproyectar en producción los casos guardados: reflejos ahora en dB SPL,
   SDT auto, tapones (B volumen bajo), perforaciones (volumen alto + ETF
   permeable) y corregir el caso 42 (UMD OD 20 → 0 %). Backup antes.
2. **Corte de LDL para el STAT:** el texto quedó en "si marca molestia bajo
   100 dB HL, no se hace", pero el STAT va a 105 dB HL en 1 kHz.
3. **H8:** ¿el paciente se sienta "de espalda a los parlantes" en campo libre?
   ¿y los colores con audífono por oído?
4. **H10:** el tope de la vía ósea del ABR es 55 dB nHL en el código
   (`BONE_MAX_OUTPUT_DB`, decisión docente); confirmar.
5. **Paciente 41** tiene otorrea en la historia pero membrana cerrada (B con
   volumen normal); ¿perforación abierta (volumen alto + ETF perforada) o se
   corrige la historia?
6. **Paciente 34 (Carolina):** la historia dice "hace 4 años control de
   embarazo" y la anamnesis "oye menos hace unos 3 años" (detalle menor).
7. **Inventario vestibular/nasal** (`investigacion/inventario_vestibular_nasal.md`):
   licencia de simHit (Apache vs MIT), DOI para labyrinthus3d, coautorías de
   colegas (Casanova, Poza, Uribe), alcance nasal.

### Errores del simulador detectados y aún NO arreglados
1. `paget` y `fijacion_congenita_estribo` traen `z ['A','As']` y la regla de
   coherencia (`CaseProfile::warnings`: curva A con gap ≥ 20) frena el
   guardado con la mayoría de las semillas: el generador y la regla se
   contradicen.
2. `kernicterus` no se puede armar: VEMP `type normal` con latencias
   alargadas, el editor lo rechaza.
3. El transitorio neonatal (`EOAS.atten_db`) no llega al caso guardado por el
   editor/armado (20 h y percentil 0,63 deberían referir y queda en 0).
4. TEOAE: el click viene a 60 dB SPL (protocolo: 80, no lineal), sin selector
   lineal/no lineal.
5. Motor de figuras del libro: la vía ósea del oído malo en una
   sensorioneural unilateral sale sin símbolo de enmascarada
   (`figuras/motor/audiograma.py`, `GAP_ENMASCARA_OSEA`); el rótulo del ABR
   marca una "V" sobre el ruido con amplitudes ~0,02 µV; `fig.abr()` no
   elige transductor, polaridad ni tasa; no hay figura de campo libre ni de
   umbrales con audífono.
6. `response_A.py` (ruta vieja, sin uso) conserva el SDT viejo; `CreatePatient.ear_volume`
   en `src/core/helpers.py` es una copia sin uso.
7. Armador: una lista numerada justo después de un `###` sale en letra chica
   (`h3 + ol li`); `hacer_figuras.py` reescribe `figuras/salida/index.html`
   compartido; cada `{{caso}}` abre página nueva (los capítulos quedan
   largos: 19-24 págs.).

### Libro, contenido
- Globo de H7 (`h7_p34`, reflejos): dice "gap de 45 dB" en 500-1000 Hz; los
  gaps de Carolina son 40 y 30.
- Ilustraciones pendientes (según el plan, no IA): H8 sala de VRA y banana
  S/A, H9 sonda en el conducto, H10 generadores I-V, cap. 2 trompa niño vs
  adulto, cap. 4 formas del reflejo; `ilustraciones/*.png` actuales son de
  Gemini y él las dio por "llenas de errores".
- Quedan comentarios `<!-- verificar -->` en todos los capítulos (citas sin
  texto completo leído, cifras de fuentes secundarias).
- Stenger positivo no ilustrable hasta poder cargar el umbral verdadero del
  oído fingido (TODO 45).
