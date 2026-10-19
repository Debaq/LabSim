# Pasada de contenidos — fase 2: llenar huecos en capítulos existentes

Libro: `/home/nick/Escritorio/Proyectos/LabSim/docs/libro/`. En la fase 1 se mapeó qué ítems del checklist de la carrera (`checklist_de_contenidos_del_libro_de_orl.md`) cubre el libro. Los informes, ítem por ítem con archivo y línea, están en `docs/libro/investigacion/pasada_contenidos_2026-10-18/` (`A.md`, `B.md`, `C.md`, `D.md`; resumen en `CONSOLIDADO.md`). Ahora se llenan los huecos **chicos y medianos** (párrafo, tabla, recuadro o sección de 1-3 págs.) dentro de capítulos que ya existen.

## Antes de escribir

1. Leé `docs/libro/herramientas/brief_agentes.md` entero (sintaxis, recuadros, honestidad, fuentes). Lo que dice sobre casos nuevos y armar el libro completo NO aplica: acá no se arman casos nuevos ni el libro completo.
2. Leé `docs/libro/herramientas/tanda_comun.md` puntos 4-7 y 9 (protocolo, clases, decisiones del autor, no editar archivos ajenos). Si te toca vestibular, también su sección "Vestibular".
3. Leé ENTEROS tus capítulos antes de tocarlos. Mirá en los informes de fase 1 todas las filas ◐/✗ que apuntan a tus archivos (grep del nombre del capítulo en los cuatro informes), no solo la lista de abajo.

## Reglas de esta pasada (además del brief)

- **Solo tus archivos** (lista abajo). Ningún otro capítulo, ni `herramientas/`, `indice.md`, `preliminares/`, `B02`. Si un hueco pide tocar otro capítulo, anotalo en el informe.
- **No borres ni reformules lo que ya está** salvo lo imprescindible para insertar lo nuevo. Lo que viene del protocolo del autor (`fuentes/protocolo.txt`) NO se elimina ni se corrige aunque la literatura diga otra cosa: si choca, lo nuevo va en `:::comentario Lo que dicen las normas` y el choque en tu informe.
- Insertá cada contenido donde corresponde en la secuencia del capítulo (Fundamento, Antes de empezar, Paso a paso, Cómo se informa, Errores... en H; Fisiología, Patología, Razonamiento en clínicos). No agregues un apéndice "lo que faltaba" al final.
- **Marco chileno** (decidido por el autor 2026-10-18): el texto explica el principio general y la norma chilena va en un recuadro `:::comentario En Chile` dentro del capítulo que la usa. Nombrá la norma con número y año, sin interpretarla más allá de su texto; verificá vigencia (bcn.cl, minsal.cl, suseso.cl, ispch.cl).
- **Fuentes**: cada dato nuevo con una referencia verificable (DOI o PMID cotejado en Crossref/PubMed, o norma/guía oficial con URL). Nunca inventes cifras ni referencias; lo dudoso va como `<!-- verificar: ... -->`. Hood (ABR) es referencia central: nunca quitar sus citas. Agregá las referencias nuevas a la lista numerada al final del capítulo, en el formato que ya usa.
- **Estilo**: tú, chileno neutro, sin "el laboratorio" ni instituciones en el texto visible, sin muletillas de narrador ("lo importante es", "aquí está la clave"...). Cada paso dice qué y por qué. Libro de aprendizaje, no de software: nada de tutoriales de simuladores. LabSim no hace vestibular (fuera de VEMP).
- **Profundidad**: la de una asignatura de pregrado de tecnología médica en ORL. Tablas cuando ordenan (tipos de equipo, escalas, fármacos por clase). Farmacología y tratamiento: informativo, la indicación es del médico.
- Figuras: no hagas figuras nuevas salvo que un esquema SVG propio sea indispensable (script en `docs/libro/ilustraciones/hacer_<capitulo>_contenidos.py`, estilo de `ilustraciones/hacer_h13.py`). Sin imágenes de IA.
- **Armado**: `cd /home/nick/Escritorio/Proyectos/LabSim && python3 docs/libro/herramientas/hacer_libro.py <N> --sin-completo` (N = 3, H3, B1...). Renderizá a tu scratch (`pdftoppm -r 60 -png docs/libro/salida/capitulo-<N>.pdf <dir>/p`) y MIRÁ las páginas que tocaste: tablas, recuadros, listas, columnas. No hagas commit.

## Informe (obligatorio)

Escribilo en `/home/nick/.claude/jobs/a1a88d9d/tmp/contenidos/fase2/<id>.md`. El coordinador verifica cada cambio contra su fuente antes del commit, así que tiene que poder hacerlo sin adivinar:

```
# <id> — capítulos ...

## Cambios
### <archivo> — <sección> (líneas aprox.)
- Ítem del checklist que cubre: ...
- Qué se agregó (1-2 líneas).
- Afirmaciones con cita: "<afirmación concreta, cifra incluida>" → <referencia completa, DOI/PMID/URL> [cómo la verificaste: abstract / texto completo / norma leída].

## Ítems que quedan ◐/✗ y por qué
## Choques con el protocolo o con decisiones del autor
## Cambios que otros capítulos necesitan
## verificar
```

Devolvé al terminar solo un resumen corto (cambios por archivo, cuántas referencias nuevas, verificar abiertos).
