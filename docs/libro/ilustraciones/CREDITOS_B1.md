# Créditos de las figuras del capítulo B1 (Anatomía)

Todas las imágenes de terceros se bajaron el 2026-10-17 y se usan **sin modificar** (el libro solo las coloca en la página y les superpone globos numerados). Los archivos descargados se trataron como datos: no se ejecutó nada de ellos.

| Archivo en `ilustraciones/` | Fuente | Licencia (dónde se verificó) | Autor | Modificada |
|---|---|---|---|---|
| `b1-oido.png` | Servier Medical Art, "Ear" (Oreille.png) https://smart.servier.com/smart_image/ear/ | CC BY 4.0 (página de origen: "Servier Medical Art is licensed under CC BY 4.0") | Servier | no |
| `b1-oido-interno.png` | Servier Medical Art, "Inner ear" (Oreille_interne.png) https://smart.servier.com/smart_image/inner-ear/ | CC BY 4.0 (página de origen) | Servier | no |
| `b1-nariz-sagital.png` | Servier Medical Art, "Nasal cavity" (Cavite_nasale.png) https://smart.servier.com/smart_image/nasal-cavity/ | CC BY 4.0 (página de origen) | Servier | no |
| `b1-senos.png` | Servier Medical Art, "Paranasal sinuses" (Sinus.png) https://smart.servier.com/smart_image/paranasal-sinuses/ | CC BY 4.0 (página de origen) | Servier | no |
| `b1-coclea-openstax.jpg` | OpenStax, Anatomy and Physiology 2e, fig. 14.6 "Cochlea" https://commons.wikimedia.org/wiki/File:1406_Cochlea.jpg | CC BY 4.0 según Wikimedia Commons (API de metadatos). **Ojo:** el sitio de OpenStax declara hoy para el libro CC BY-NC-SA 4.0 (https://openstax.org/books/anatomy-and-physiology-2e/pages/preface); ambas son compatibles con un libro CC BY-NC-SA. | OpenStax (Rice University) | no |
| `b1-cae-gray907.png` | Gray's Anatomy, lámina 907 https://commons.wikimedia.org/wiki/File:Gray907.png | dominio público (Commons) | Henry Vandyke Carter, 1858/1918 | no |
| `b1-caja-gray911.png` | Gray's Anatomy, lámina 911 https://commons.wikimedia.org/wiki/File:Gray911.png | dominio público (Commons) | H. V. Carter | no |
| `b1-laberinto-gray920.png` | Gray's Anatomy, lámina 920 https://commons.wikimedia.org/wiki/File:Gray920.png | dominio público (Commons) | H. V. Carter | no |
| `b1-tabique-gray854.png` | Gray's Anatomy, lámina 854 https://commons.wikimedia.org/wiki/File:Gray854.png | dominio público (Commons) | H. V. Carter | no |
| `b1-pared-lateral-gray856.png` | Gray's Anatomy, lámina 856 https://commons.wikimedia.org/wiki/File:Gray856.png | dominio público (Commons) | H. V. Carter | no |

## Esquemas propios (SVG, sin IA)

Generados con `hacer_b1.py` (misma carpeta): `b1-pabellon.svg`, `b1-membrana.svg`, `b1-trompa.svg`, `b1-via-auditiva.svg`, `b1-via-vestibular.svg`, `b1-irrigacion.svg`, `b1-valvula.svg`. Las cifras que llevan salen de la bibliografía del capítulo (Ishijima y cols., 2000, para el largo de la trompa; Pirola y cols., 2025, para el ángulo y el área de la válvula nasal).

## Notas

- Los rótulos de las láminas de Gray y de OpenStax están en inglés (tal como vienen); los globos del libro los traducen.
- La versión en español de OpenStax "1406 Cochlea esp.jpg" figura como CC BY-SA 4.0 en Commons y no se usó.
- Las copias de Servier Medical Art en Wikimedia Commons figuran como CC BY-SA 3.0; se tomaron directamente de smart.servier.com, donde la licencia vigente es CC BY 4.0.
- Candidatas descartadas: "Auditory Pathway.png" de Peelle (CC BY 4.0, Commons) por tener rótulos en inglés y ser de otro autor; en su lugar se dibujó la vía con esquema propio.

## Imágenes propias hechas con labyrinthus3d (2026-10-19)

Software propio del autor, sin IA. Se generan con `hacer_b1_vias_simulador.py` (imágenes sueltas con globos) y `hacer_b1_laminas.py` (láminas de cuatro paneles): ambos sirven labyrinthus3d de solo lectura y leen el `<canvas>` de cada esquema con chromium sin cabeza (sin interfaz, sobre blanco; los paneles se recortan al esquema). Las constantes del simulador no son valores normativos: ninguna cifra del texto sale de él.

Imágenes sueltas (con globos): `b1-sim-auditiva.png` (Audición, Tronco), `b1-sim-vor.png` (Vía, laterales), `b1-sim-otolitos.png`, `b1-sim-mirada.png`, `b1-sim-percepcion.png` (Vía, filtros homónimos), `b1-sim-sacadas.png`, `b1-sim-seguimiento.png` (Oculomotor).

Láminas (`b1-lam-<nombre>.svg`, paneles A-D en JPEG dentro del SVG):

| Lámina | Paneles |
|---|---|
| `vor` | canal lateral derecho excitado e inhibido; planos LARP y RALP, con un impulso de cabeza |
| `oto` | utrículo y sáculo sanos; solo utrículo; solo sáculo; neuritis superior |
| `esp` | módulo Postural, Vía: vestibular inclinado y adelante-atrás; propioceptiva; integración |
| `flo` | neuritis izquierda fijando y ocluido, con y sin flóculos |
| `mir` | mirada y fase rápida en reposo, en sacada horizontal y vertical, y con integradores a medias |
| `perc` | tálamo y corteza: sano, neuritis reciente, pérdida compensada, corteza lesionada |
| `oc1`, `oc2` | Oculomotor: seguimiento, sacadas, supresión del VOR, optocinético; silla rotatoria girando y frenando, sacudida cefálica, sin nódulo |
| `aud`, `peat` | Audición: vía sana, schwannoma, olivar, colículo; y el PEAT de cada caso |
| `pat1`-`pat4` | Patología: neuritis superior e inferior, pérdida unilateral, AICA; núcleos vestibulares, INO, FRPP, nistagmo hacia arriba; degeneración cerebelosa, evocado por la mirada, hipofunción y arreflexia bilaterales; la neuritis a las 6 horas, 3 días, 2 semanas y 3 meses |

Los SVG `b1-via-auditiva.svg` y `b1-via-vestibular.svg` (esquemas propios de `hacer_b1.py`) siguen en el disco, sin uso en el capítulo.
