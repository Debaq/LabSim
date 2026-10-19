# Recuadro "Prevención" en los capítulos clínicos

Decisión del autor (2026-10-18, en `docs/decisiones.md`): la promoción y prevención entra **mixta**: una base nueva B5 "Salud pública y prevención en ORL" (la escribe otro agente ahora) y, en cada capítulo clínico, un recuadro corto que aplica esos conceptos al cuadro del capítulo y remite a B5.

## Qué hacer en cada uno de tus capítulos

1. Leé el capítulo (al menos Fisiología, Patología, Para cerrar) para saber qué cuadros trata.
2. Insertá **un** recuadro justo antes de `## Para cerrar`:

```
:::comentario Prevención
- **Primaria:** qué se puede evitar y cómo (si aplica).
- **Secundaria:** cómo se detecta antes (tamizaje, vigilancia, sospecha clínica temprana) y a quién.
- **Terciaria:** cómo se limita la discapacidad (audífono, implante, rehabilitación...).
- **Cuaternaria:** qué estudio o tratamiento de más se evita (si aplica).
- **Para el paciente:** el mensaje educativo concreto, en una o dos frases.

Una frase de epidemiología del cuadro principal (prevalencia o incidencia) con su cita, si hay una fuente verificable. Niveles de prevención y su marco: → B5.
:::
```

Solo los niveles que de verdad apliquen (2 a 5 viñetas); 6 a 10 líneas en total. Si el capítulo ya trae un recuadro "En Chile" con GES o programas, remití a él en vez de repetirlo.
3. Reglas: nada se afirma sin fuente verificable (DOI/PMID cotejado en Crossref/PubMed, o guía oficial: OMS, MINSAL, JCIH, AAO-HNS, NICE...). Si no hay evidencia de que algo prevenga, no lo digas. Reutilizá las referencias que el capítulo ya tiene cuando sirvan; las nuevas van a su lista numerada final con el formato del capítulo. Lo dudoso: `<!-- verificar: ... -->`. Estilo del libro: tú, chileno neutro, sin "el laboratorio" ni instituciones, sin muletillas de narrador. El tratamiento médico es informativo. No toques casos, `.py` ni otras secciones.
4. Armá cada capítulo: `cd /home/nick/Escritorio/Proyectos/LabSim && python3 docs/libro/herramientas/hacer_libro.py <N> --sin-completo` y mirá la página del recuadro (`pdftoppm -r 60 -png -f <p> -l <p> ...`). No hagas commit.
5. Informe en `/home/nick/.claude/jobs/a1a88d9d/tmp/contenidos/prevencion/<id>.md`: por capítulo, el texto del recuadro y cada afirmación con su referencia (DOI/PMID) y cómo la verificaste; `verificar` abiertos. Devolvé un resumen corto.
