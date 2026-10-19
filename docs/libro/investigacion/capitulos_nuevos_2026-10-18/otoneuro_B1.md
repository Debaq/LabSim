# Informe: otoneurología en B1 (vías centrales con labyrinthus3d), segunda ronda con láminas

Archivos tocados: `docs/libro/capitulos/B01-anatomia.md` (secciones de vías ampliadas; 14 láminas; tabla "Sitio de la lesión"; referencias; créditos), `docs/libro/ilustraciones/hacer_b1_vias_simulador.py` (imágenes sueltas con globos; su función `panel_svg` quedó superada por las láminas y los SVG `b1-sim-patologia-a/b` se borraron), `hacer_b1_laminas.py` (nuevo), `b1-sim-*.png` (7), `b1-lam-*.svg` (14, 6,9 MB en total), `CREDITOS_B1.md`. B1 pasó de 34 a 47 páginas. Armado con `hacer_libro.py B1 --sin-completo` (sin commit; libro.pdf completo NO rehecho). Revisé las páginas 15-40 renderizadas.

## Decisión: reemplazar o complementar
Los esquemas del simulador REEMPLAZAN a `b1-via-auditiva.svg` y `b1-via-vestibular.svg` en la página (siguen en disco). La estación de cada onda del PEAT pasó a una tabla. Se mantienen 7 imágenes sueltas con globos (anatomía) y se suman 14 láminas de 4 paneles (A-D) para no gastar páginas: cada una ocupa una página.

## Láminas (nombre, escena, qué enseña) — todas con pie "qué mirar" y rojo=excita/azul=inhibe
- `vor`: lateral der excitado / inhibido, LARP, RALP (con impulso de cabeza). Confirmé en el simulador el pareo de músculos de la tabla (anterior izq: recto superior izq + oblicuo inferior der).
- `oto`: ambos / solo utrículo (sin sáculos, lesión armada) / solo sáculo / neuritis superior (oVEMP cae, cVEMP queda).
- `esp`: módulo Postural > Vía: vestibular inclinado y adelante-atrás (incluye médula cervical y cuello), propioceptiva, integración.
- `flo`: neuritis izq. fijando/ocluido y con/sin flóculos (el freno rojo en T aparece solo fijando y con flóculo).
- `mir`: reposo, sacada horizontal, sacada vertical (modo Oculomotor), integradores a medias.
- `perc`: sano / neuritis reciente / pérdida compensada / PIVC izq. perdida (sensación de giro y vertical subjetiva en el propio esquema).
- `oc1`: seguimiento, sacadas, supresión del VOR, optocinético. `oc2`: silla girando, al frenar, sacudida cefálica, sin nódulo.
- `aud`, `peat`: vía auditiva sana / schwannoma (nervio) / olivar / colículo, y el PEAT del simulador de cada caso.
- `pat1`-`pat4`: neuritis sup., inf., pérdida unilateral compensada, AICA; núcleos vestibulares, INO, FRPP, upbeat; degeneración cerebelosa, evocado por la mirada, hipofunción y arreflexia bilaterales; compensación de una neuritis a 6 h, 3 d, 2 sem, 3 meses. Pedido del coordinador cubierto: los 12 casos armados menos "pérdida unilateral" que va (C de pat1); la comparación recién lesionada/compensada está en pat1 C, perc C y pat4.

Método: `hacer_b1_laminas.py [nombre ...]` (DevTools, reloj virtual, canvas `lab-via`/`lab-aud`/`lab-post`; recorte automático del blanco). Puertos 8921/9921.

## Limitaciones de las imágenes
- Los lienzos de Patología/Vía escriben encima "nistagmo grado X de Alexander" y otras cifras del modelo (ms, °/s, grados de vertical): quedan, con la advertencia en el pie ("son del modelo, no valores de referencia"). No las cito en el texto.
- Las escenas con tiempo (sacadas, silla, sacudida, impulsos) son un instante elegido por pasos de reloj; el pie describe qué estaciones mirar, no la fase exacta.
- El panel D del PEAT (colículo) muestra ondas sin cambio porque así lo modela el simulador; el texto lo dice como "el modelo no cambia las ondas" y no como hecho clínico (ver verificar 2).
- Páginas con espacio en blanco tras cada lámina (no caben dos por página).

## Afirmaciones y respaldo (DOI cotejados en Crossref; resumen PubMed leído donde se indica)
- Dorsal coclear / localización con un oído: Oertel y Young 2004 (resumen). MSO-tiempo/LSO-nivel: Grothe y cols. 2010. Núcleo/cinturón cortical y geniculado ventral: Kaas y Hackett 2000 (resumen; primates).
- PEAT: Møller 1981/1983 (ya en B1), Melcher y Kiang 1996, Møller y cols. 1995 (DOI 10.1288/00005537-199506000-00007; solo el título respalda "cruzadas y no cruzadas").
- cVEMP ipsilateral, P13-N23: Colebatch 1994 (resumen); vía vestibuloespinal medial: Kushiro 1999 (usada en H12); oVEMP cruzado: Iwasaki 2007 (resumen).
- Flóculo, nódulo/úvula, vermis/fastigio: Kheradmand y Zee 2011 (resumen); descarga del almacenamiento y PAN sin nódulo: Waespe y cols. 1985 (resumen); almacenamiento: Raphan y cols. 1979; integradores: Robinson 1981, Cannon y Robinson 1987.
- PIVC y red tálamo-cortical: Lopez y Blanke 2011, zu Eulenburg y cols. 2012 (resúmenes); dominancia del hemisferio no dominante: Dieterich 2003 (resumen); vertical subjetiva ipsiversiva bajo el puente alto y contraversiva sobre él: Dieterich y Brandt 1993, Brandt y Dieterich 1994 (resúmenes, regla textual); desvío moderado contraversivo en PIVC: Brandt y Dieterich 1999 (resumen).
- INO: Keane 2005 (resumen; causas MS 34 % e infarto 38 %, no puse cifras). Neuritis y AICA: Taylor 2016, Lee 2002, Lee 2012 (ya en B1).
- Arco del VOR, FRPP/riMLF/omnipausa, vías de sacadas y seguimiento, supresión del VOR, flóculo y fijación, FRPP (parálisis de la mirada): Leigh y Zee 2015 (DOI del libro verificado; no cotejé páginas).

## `verificar` abiertos
1. Kaas y Hackett 2000 son primates; falta ubicar el núcleo auditivo humano en el giro de Heschl.
2. "Un PEAT normal no descarta una lesión por encima del mesencéfalo" y el panel D del PEAT (colículo sin cambio en el modelo): lectura habitual, sin cita; ojo, parte de la literatura da al colículo aporte a la onda V.
3. Tabla de músculos de los canales verticales: de Leigh y Zee (sin página); el simulador coincide.
4. Vestibuloespinal lateral/medial (Cullen 2012, sin cotejar página).
5. Møller 2013 (Hearing, 3.ª ed.): falta ISBN/editorial.
6. Filas nuevas de la tabla "Sitio de la lesión" sin cita propia: pérdida unilateral compensada (remite a cap. 31, H17, H18), tractos tegmentales ventrales ("nistagmo vertical puro, que la fijación no frena": H16), hipofunción/arreflexia bilateral (remite a cap. 24, H18). Revisar que esos caps. digan eso.
7. Pie de `esp`: lo que "se calienta o se enfría" en la vía vestibuloespinal es lectura del simulador, sin cita; el texto de la sección sigue a Cullen 2012 (verificar 4).

## Para otros capítulos
H10: `b1-lam-peat.svg`, `b1-sim-auditiva.png`. H12: `b1-lam-oto.svg`. H16: `b1-lam-oc1/oc2/mir/flo.svg`. H17/H18/cap. 21: `b1-lam-vor.svg`, `b1-lam-pat1.svg`. Cap. 25: `b1-lam-pat2/pat3.svg`, `b1-lam-perc.svg`. Cap. 31/H20: `b1-lam-pat4.svg` (compensación) y `b1-lam-esp.svg`. Cap. 24: `b1-lam-pat3.svg` panel D.
