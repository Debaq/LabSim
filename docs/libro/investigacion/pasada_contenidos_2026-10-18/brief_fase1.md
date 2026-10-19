# Pasada de contenidos — fase 1: mapa de cobertura (solo lectura)

Libro: `/home/nick/Escritorio/Proyectos/LabSim/docs/libro/` ("Evaluación y rehabilitación en ORL. Un libro de casos clínicos", ~60 capítulos, ~480 mil palabras). Estructura: Bases B1-B4 (`capitulos/B0*.md`), caja de herramientas H1-H25 (`capitulos/H*.md`, una técnica por capítulo), capítulos clínicos 1-36 (`capitulos/NN-*.md`), preliminares (`preliminares/*.md`). Plan del libro: `indice.md`. Estado: `ESTADO.md`.

Checklist de contenidos de la carrera (14 asignaturas): `checklist_de_contenidos_del_libro_de_orl.md`. Te toca un grupo de asignaturas (abajo).

## Qué hacer

Para CADA ítem y subítem de tus asignaturas, buscá en el libro si está tratado (grep con varios sinónimos, español, abreviaturas; después LEÉ la sección encontrada, no te quedes con el grep). Clasificá:

- **✓ cubierto**: el libro lo explica con la profundidad que pide una asignatura de pregrado (definición, mecanismo o procedimiento, interpretación). Indicá dónde: `archivo.md` + título de la sección (y número de línea).
- **◐ parcial**: se menciona, se usa sin explicarlo, o se explica corto / solo una parte. Indicá dónde y QUÉ falta, concreto.
- **✗ ausente**: no está.
- **B2**: solo aparece en la lista "Qué tiene que tener" de B2 (fisiología, la escribe una colega; es un esqueleto). Indicá si además está en otro capítulo.

No marques ✓ por una mención de pasada. Si está repartido en varios capítulos, listalos todos.

Para cada ◐ y ✗, proponé **dónde iría** (capítulo existente + sección, o "capítulo nuevo X"), **tamaño aproximado** (párrafo / sección de 1-3 págs. / capítulo) y si choca con algo del libro. Algunas reglas del libro que condicionan la propuesta:
- LabSim no se expande a vestibular (VNG, vHIT, etc. usan trainHIT y labyrinthus3d como imágenes).
- El libro es de distribución mundial pero contiene marco chileno (PREXOR, ISP, SUSESO) en salud ocupacional.
- B3 histología es esqueleto ("fuera por ahora"); B2 la escribe una colega.
- Espirometría y SAHOS están fuera del índice por ahora (hay pptx en `fuentes/`): igual mapealos.

Material de alcance: `fuentes/clases/LEEME.md` (clases del autor, privado: solo para entender qué espera la asignatura; no citarlo).

## Reglas

- **SOLO LECTURA.** No edites ningún archivo del repo. No commits. Otros agentes trabajan en el mismo directorio.
- Escribí tu informe en `/home/nick/.claude/jobs/a1a88d9d/tmp/contenidos/informes/<grupo>.md`.
- En español.

## Formato del informe

```
# Grupo X — asignaturas N, M

## N. Nombre (código)
| Ítem | Estado | Dónde | Qué falta | Propuesta |
|---|---|---|---|---|
| Ítem principal / subítem (texto corto) | ✓/◐/✗/B2 | H7 "Reflejo estapedial" l. 210; cap. 4 "Fisiología" | ... | H7, sección nueva "...", 1 pág. |
...

## Resumen del grupo
- Conteo ✓ / ◐ / ✗ / B2.
- Huecos grandes (los que piden capítulo nuevo o sección de varias páginas), en orden de importancia.
- Huecos chicos (párrafo o tabla en un capítulo existente).
```

Al terminar, devolvé solo el resumen del grupo (el detalle queda en el archivo).
