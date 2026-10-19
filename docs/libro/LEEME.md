# Evaluación y rehabilitación en otorrinolaringología (libro de casos)

**El compilado es `libro.pdf`** (en esta carpeta). Se rearma solo cada vez
que se arma un capítulo, así que siempre está al día.

## Qué hay en cada carpeta

| Carpeta | Qué tiene |
|---|---|
| `capitulos/` | El texto: un `.md` por capítulo (B, H1-H30, 1-36) y su `.py`, que declara los casos y las figuras. |
| `preliminares/` | Prólogo, presentación, cómo usar el libro y abreviaturas. |
| `indice.md` | El índice y el plan de cada capítulo. |
| `casos/` | Un JSON por caso pedido por cuadro; `casos/generados/` es lo que armó el editor real de LabSim. |
| `figuras/` | Motor de figuras (`motor/`), `armar_casos.sh` y `hacer_figuras.py`. Los SVG salen a `figuras/salida/`. |
| `otoscopias/` | Fotos usadas en las fichas y sus créditos (`CREDITOS*.md`). Los bancos completos (`bancos/`) no se versionan. |
| `ilustraciones/`, `logos/` | Dibujos y logos de la portada. |
| `investigacion/` | La revisión bibliográfica de base. |
| `herramientas/` | Los scripts del libro (abajo). |
| `salida/` | PDF de capítulos sueltos para revisar. No se versiona. |
| `fuentes/` | Material privado del autor (protocolo 2019). No se versiona. |

## Comandos

```bash
# Un capítulo: casos + figuras + su PDF (salida/capitulo-11.pdf) + libro.pdf completo
python3 docs/libro/capitulos/11-asimetria-que-no-cierra.py
python3 docs/libro/capitulos/11-asimetria-que-no-cierra.py --solo-pdf   # sin rehacer figuras

# Solo armar PDF
python3 docs/libro/herramientas/hacer_libro.py            # libro.pdf completo
python3 docs/libro/herramientas/hacer_libro.py 11         # capítulo 11 y después libro.pdf
python3 docs/libro/herramientas/hacer_libro.py 11 --sin-completo   # solo el capítulo (rápido)

# Esqueleto de un capítulo nuevo desde indice.md
python3 docs/libro/herramientas/nuevo_capitulo.py H8
```

**Estado y pendientes: ver `ESTADO.md`.**

Las guías del docente (`:::docente`) van siempre dentro de cada caso: hay
**una sola edición** del libro.
