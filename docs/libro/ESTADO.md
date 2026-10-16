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
1. **Inventario vestibular/nasal** (`investigacion/inventario_vestibular_nasal.md`):
   detalles menores (licencia de simHit, DOI de labyrinthus3d, coautorías).

Cerrados el 2026-10-16 (producción reproyectada, pacientes 34 y 41, H8, H10):
`docs/decisiones.md`, "Pendientes del libro cerrados con él". El corte del
STAT terminó en un cambio del modelo: "LDL: la tolerancia es del paciente".

### Errores del simulador detectados
Los siete que había quedaron arreglados (2026-10-15); qué se decidió en cada
uno está en `docs/decisiones.md`, "Errores del simulador detectados al
escribir el libro". Para usar en los capítulos: `fig.abr()` ya elige
`transductor`, `polaridad` y `tasa`; hay `fig.campo_libre(ganancia=...)`; la
TEOAE del libro sale con click no lineal a 80 dB SPL. Los casos ya armados
no se rehicieron: un capítulo que se vuelva a armar puede cambiar de curva
(Paget/fijación con gap ya no salen A) o de fichas (cada caso no abre página).

### Libro, contenido
- **Rostros de los pacientes** (pedido 2026-10-16): todas las fichas muestran
  iniciales (`rostros/` no existe). Sintéticos realistas y coherentes con el
  caso: edad, sexo y signos visibles (Ramsay Hunt con la parálisis del lado
  que corresponde). Un paciente de práctica tiene la misma cara en todos los
  capítulos. Ver `hacer_libro.py`, `ficha()`.
- Ilustraciones pendientes (según el plan, no IA): H8 sala de VRA y banana
  S/A (en verde), H9 sonda en el conducto, H10 generadores I-V, cap. 2 trompa niño vs
  adulto, cap. 4 formas del reflejo; `ilustraciones/*.png` actuales son de
  Gemini y él las dio por "llenas de errores".
- Quedan comentarios `<!-- verificar -->` en todos los capítulos (citas sin
  texto completo leído, cifras de fuentes secundarias).
- Stenger positivo no ilustrable hasta poder cargar el umbral verdadero del
  oído fingido (TODO 45).
