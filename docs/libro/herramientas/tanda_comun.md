# Instrucciones comunes para los agentes de capítulo (loop del libro)

Repo: /home/nick/Escritorio/Proyectos/LabSim. Book dir: docs/libro/.

1. Read docs/libro/herramientas/brief_agentes.md COMPLETELY and follow it (rules, syntax, sources, honesty, workflow, build, final report). It wins over anything else except what is written here.
2. Read docs/libro/ESTADO.md, section "Cola de tandas", so you know where your chapter fits.
3. Use ONE model chapter only (the one named in your task). From its "Fundamento" learn how the book explains the physiology and physics of WHY a test is done that way; from "Conoce tu equipo" learn the screenshots-with-balloons pattern. Do not read the other models.
4. From the author's protocol (docs/libro/fuentes/protocolo.txt, private) read ONLY the line range given in your task. From the class material read only what docs/libro/fuentes/clases/LEEME.md assigns to your chapter (read the .txt, the .pdf only to see a figure). Classes define SCOPE: never copy them, cite them or name who taught them; verify every fact with bibliography.
5. Where there is neither protocol nor class: research on the web only with verifiable sources (standards, guidelines, papers with DOI or PMID). Never invent; anything doubtful goes as `<!-- verificar: ... -->`.
6. Respect the author's decisions recorded in docs/decisiones.md and what LabSim implements (search the file for your topic). The author's practice is the book's way, with the logic of why; alternatives go in `:::comentario Lo que dicen las normas`. Never write "el laboratorio" or name any institution in visible text.
7. Be consistent with chapters that already cover your topic (named in your task): don't contradict them; point to your chapter from the concept, not repeat whole sections. Do NOT edit other chapters; list needed changes in your report.
8. Build: `cd /home/nick/Escritorio/Proyectos/LabSim && LIBRO_SIN_COMPLETO=1 PUERTO=<your port> python3 docs/libro/capitulos/<your file>.py`. ALWAYS with LIBRO_SIN_COMPLETO=1 (other agents build at the same time; the coordinator builds libro.pdf). Render pages to your scratch dir and LOOK at every page (pdftoppm -r 60). No ✍ may remain in your .md. Do not commit.
9. Don't edit shared files (herramientas/**, figuras/**, indice.md, preliminares/**, rostros/**, other chapters). If the builder or the engine limits you, work around it in your chapter and report it.
10. Final report, short, in Spanish: what you covered; figures/screenshots used; protocol corrections (with source) and places where you kept the protocol and added the norms box (these are the "incongruencias"); `verificar` items; builder/engine problems; face requests (`<case name>: <English portrait description>`) if you invented patients with cuadro().
