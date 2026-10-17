# Imagenología (TC, RM y radiografía) para el libro de casos

Búsqueda hecha el 2026-10-17 (tanda A: tres agentes en paralelo). Mismo criterio y método que `imagenes.md`: CC0, PD, CC BY, CC BY-NC y CC BY-NC-SA se pueden recortar y rotular; CC BY-SA solo sin modificar; ND descartado; figuras "with permission / reproduced from" fuera. Las marcadas **(vista)** se bajaron y se miraron. Al repo no se bajó ninguna imagen: las descargas de prueba estaban en una carpeta temporal y se borran; se vuelven a bajar con las URL y recetas de abajo. Los scripts de descarga y de corte de los datasets quedaron en `herramientas/imagenologia/` (`rzip.py URL` lista un zip remoto de Zenodo/figshare; `rzip3.py URL REGEX DESTINO` extrae solo lo que se pide; `render_*.py` cortan DICOM, NIfTI y NRRD a PNG).

Pie de foto para todas (como la TC del cap. 35): es otra persona, no el paciente del caso; la imagen la pide y la informa el médico; se muestra para que se vea la forma de lo que miden las pruebas.

## Lo importante

- **Radiopaedia no sirve sin permiso escrito.** Su página de licencia pone "Publishing a textbook" en la lista "Definitely not permitted" (sin distinguir libro gratuito), y sus Terms prohíben usar muchos casos para armar contenido parecido. Salida legal: pedir permiso al autor de cada caso, que conserva sus derechos.
- **Datasets abiertos que cortamos nosotros (CC BY 4.0, verificados y probados):** TCIA Vestibular-Schwannoma-SEG (VS-SEG-141: schwannoma intracanalicular pequeño con el CAI sano del otro lado en el mismo corte; VS-SEG-010: grande quístico del ángulo), ISLES 2022 (caso 0157 infarto cerebeloso, 0174 pontino, DWI/ADC), MSLesSeg (EM en FLAIR, caso P72), OpenEar v2 (Zenodo 1473724, CBCT de hueso temporal de cadáver a 0,125 mm), IE-Map (plantilla CISS de 63 sanos, rotular como plantilla), NasalSeg (TC de senos; ojos tapados por anonimización). No: IXI (BY-SA), CT-SCOPE (restringido), MedPix (pasó a ASNR, todos los derechos reservados).
- **Huecos:** ningún dataset trae una TC clínica de peñasco completa ni radiografías; para eso, PMC/Commons. Sin fuente libre: TC o RM nasal antes y después de vasoconstrictor, sagital normal de cerebro limpio (sacarlo de un dataset), TC coronal normal ya rotulada, Valvassori dibujado, radiografía simple de BAHA/Osia, TC de oído dedicada a Paget.

## Mejor candidata por capítulo

| Cap. | Necesidad | Mejor candidata | Licencia |
|---|---|---|---|
| B1 | TC axial normal rotulada | PMC8520521 Fig. 3 (4 cortes) | CC BY |
| B1 | RM del CAI, 4 nervios | PMC9324637 Fig. 4 (sagital oblicuo rotulado, con aplasia del mismo niño al lado); PMC11790716 Fig. 5c (plano de corte); IE-Map | CC BY |
| B1 | TC coronal normal | PMC11913933 Fig. 1A (sin rótulos) u OpenEar | CC BY |
| 1 | Atresia | PMC9831057 Fig. 2 (confirmada); PMC4661245 Fig. 2 (normal/estenosis/atresia) | CC BY / CC BY-NC |
| 3 | Colesteatoma | PMC11913933 Fig. 1 (normal, pars flaccida, pars tensa, OMC); PMC6775179 Fig. 2 (escudo sano vs erosionado) | CC BY |
| 4, 15 | Otoesclerosis | PMC3999364 Figs. 1 (fissula) y 12 (doble anillo); PMC10684447 Fig. 2 (fissula enferma vs normal) | CC BY |
| 4, 15 | Paget | PMC10366931 Fig. 31 (base de cráneo, CAI estrechados) | CC BY |
| 7 | Fractura del temporal | PMC3292638 Fig. 11 (respeta vs cruza la cápsula ótica); PMC6383528 Fig. 9 | CC BY-NC |
| 9, 23 | Hidrops | PMC11098000 Fig. 2 (hidrops vs oído control); PMC9909016 (grados 0/I/II con esquema) | CC BY-NC / CC BY |
| 10, 26 | Acueducto vestibular dilatado | PMC10066110 Fig. 4 (control vs DAV, Cincinnati medido); PMC10008926 Fig. 8 (TC + RM) | CC BY |
| 11, 20, 27 | Schwannoma | TCIA VS-SEG-141 y 010 (cortes propios); PMC10365083 Fig. 1 (Koos I-IV, T1+gd y T2) | CC BY |
| 11 | Diferenciales del ángulo | Epidermoide PMC3467374; meningioma PMC10246372 (con audiograma); asa de AICA PMC6417406 | CC BY-NC; CC BY-NC-SA; CC BY |
| 12 | Infarto de la AICA | PMC11390645 (DWI + audiograma + vHIT); ISLES 0174 (pontino) | CC BY |
| 12 | EM en el tronco | PMC7423083 (placa pontina + audiometría); MSLesSeg P72 | CC BY 3.0 / CC BY |
| 13, 17 | Nervio coclear | PMC9324637 Fig. 4; PMC12559043 Fig. 3 (aplasia, hipoplasia, normal) | CC BY |
| 17 | Malformaciones, CMV | PMC8520521 Fig. 9 (PI-I, II, III); PMC2765183 Figs. 5 y 7; PMC9406729 Figs. 4C y 7 | ver parte II |
| 21 | Infarto cerebeloso | ISLES 0157 (cortes propios); PMC5307938 (DWI negativa y luego positiva, AICA); PMC2503965 | CC BY / CC BY-NC / CC BY 2.0 |
| 24, 25, 32 | CANVAS | PMC8055326 Fig. 5; PMC8629873 (sagital T1 rotulado) | CC BY |
| 25 | Chiari I | PMC10380265 (caso con mareo); Commons Hellerhoff (BY-SA, sin modificar) | CC BY |
| 26 | Dehiscencia | PMC12178317 Fig. 2 (Stenvers y Pöschl vs lado normal, más CISS); PMC7385271 Fig. 1 (planos) | CC BY |
| 29 | Implante coclear | PMC9443830 Figs. 3 y 7; PMC13327508 Figs. 2-3 (Stenvers con esquema) | ver parte II |
| 29 | Conducción ósea | PMC9420306 Fig. 2 (TC de BAHA); PMC3844407 Fig. 3 (Bonebridge, cadáver) | ver parte II |
| 35, 36 | Senos | Concha bullosa (Commons, PD); pólipos PMC11505379 (Lund-Mackay); válvula PMC9422510; complejo osteomeatal (Häggström, CC BY); NasalSeg | ver parte III |

Las licencias "ver parte" están en la tabla de cada sección. Antes de usar una figura, confirmar en su fila que el pie no la marca de terceros.


---

# Parte I. Datasets abiertos y licencias

Revisión hecha el 2026-10-17 para el libro de casos (CC BY-NC-SA 4.0). Rige el mismo criterio de `docs/libro/investigacion/imagenes.md`: CC0, PD, CC BY, CC BY-NC y CC BY-NC-SA se pueden modificar; CC BY-SA solo se usa sin modificar; ND queda descartado.

**Método.** Las licencias se leyeron en la página oficial, en la API del repositorio (Zenodo, figshare, TCIA/NBIA) o en el archivo LICENSE que viene con los datos. Cuando la página ya no existe, se leyó la copia de la Wayback Machine. Todo lo bajado está en (carpeta temporal de la búsqueda, ya borrada) (unos 1,3 GB). Los scripts están en `herramientas/imagenologia/` y los PNG de prueba en `datasets/*.png`. Al repo no se bajó nada.

**Entorno.** Hay un venv en `datasets/venv` (`--system-site-packages`, con pydicom 3.0.2, nibabel 5.4.2 y pynrrd). Se ejecuta siempre con `python -I`.

**Truco para los zips grandes de Zenodo y figshare.** Los dos servidores aceptan `Range`. El script `scripts/rzip.py URL` lista el contenido de un zip remoto sin bajarlo. `scripts/rzip3.py URL REGEX DESTINO` extrae solo los archivos que coinciden con el patrón. Así se sacó un CBCT de 116 MB de un zip de 3,9 GB, y 3 casos de un zip de 1,7 GB.

---

### 1. Radiopaedia

**Qué es.** Un sitio de casos radiológicos aportados por usuarios. Cada caso tiene un rID y un DOI (10.53347/rID-xxxxx).

**Licencia verificada.**
- En https://radiopaedia.org/licence: *"we make all our cases available under a Creative Commons Non-Commercial Attribution, Sharealike license"* *"(currently CC-NC-BY-SA 3.0)"*. La misma página añade *"the modifications outlined in our Terms of Use"* y dice que los Terms son *"the single source of truth"*.
- En https://radiopaedia.org/terms (versión 4.2, *"Last Reviewed: 14 August 2026"*):
  - *"Creative Commons Attribution-Noncommercial-Share Alike 3.0 Unported licence"*, *"as such licence is modified in accordance with these Terms of Use"*.
  - *"Image Content (other than Image Content contributed by you) may not be modified, copied"* […] fuera de esa licencia modificada sin permiso escrito del autor o de Radiopaedia.
  - En *Fair Use of Content*: *"This does not extend, however, to copying entire sections of the site for reproduction in other websites or media."* y *"Nor is the use of numerous cases from Radiopaedia to create similar content considered fair use"*.
  - Prohíbe el scraping y la descarga masiva, y el uso para entrenar IA sin licencia escrita.
  - Las "modificaciones" a la licencia CC benefician a Radiopaedia (patrocinios, sublicencias, irrevocabilidad). No agregan permisos para terceros.
- **Lo decisivo.** En /licence, el ejemplo *"Publishing a textbook"* aparece en la lista **"Definitely not permitted"**, junto con cursos pagados y apps con paywall. No distingue entre libro gratuito y libro pagado. Tampoco define "commercial" de manera formal: da ejemplos (paywall, registro, anuncios) y advierte que *"we only monetize this to pay the bills"* no deja de ser comercial.
- **Licencia por caso.** La página de un caso (probé rID 22885) no tiene campo de licencia propio. Muestra la cita y el DOI, y la licencia es la general del sitio. No encontré casos con una licencia distinta.

**¿Se puede rotular o recortar?** La BY-NC-SA 3.0 permite obras derivadas, y una adaptación de 3.0 puede salir con una versión posterior de la misma licencia (4.0). Pero Radiopaedia excluye expresamente "publicar un libro de texto" del uso permitido sin licencia. Ojo: un libro de casos que reúne muchos casos también choca con la cláusula de *"numerous cases … to create similar content"*.

**La salida legal.** La sección *"Using your own images"* dice que el contribuyente conserva sus derechos (*"you are not changing the ownership of any intellectual property"*) y que puede autorizar su uso en un libro sin pasar por Radiopaedia. Por lo tanto, se puede escribir al autor de cada caso y pedirle permiso por escrito, idealmente "CC BY 4.0 o permiso para un libro CC BY-NC-SA 4.0, con rótulos y traducción". La otra vía es pedir una licencia a Radiopaedia (/licence → *Obtaining a license*).

**Atribución exigida.** *"Case courtesy of Dr Ian Bickle, Radiopaedia.org, rID: 198700"*: nombre del autor, Radiopaedia.org y el rID. En la versión en línea, con enlaces clicables. Mejor aún, con el DOI del caso: `Autor. Título. Case study, Radiopaedia.org. https://doi.org/10.53347/rID-NNNNN`.

**Descarga.** *"Individual images can be downloaded through the browser using the download from cloud icon in the viewer toolbar."* Además: *"We do not have an API for downloading cases."* Hay que hacerlo a mano, imagen por imagen, desde el visor del caso. Sale a la resolución publicada, en general de 512 a 1024 px por corte. No hay que automatizarlo, porque los términos lo prohíben.

**Probado.** No (no hay API y está prohibido automatizar).

**Veredicto: DUDOSO → NO, salvo con permiso escrito del autor de cada caso.** No conviene usarlo "porque es BY-NC-SA": la página de licencias nombra justo nuestro caso como no permitido.

---

### 2. TCIA: Vestibular-Schwannoma-SEG (Shapey et al. 2021)

**Qué es.** 242 pacientes con schwannoma vestibular antes de radiocirugía (Queen Square, Londres). Siemens Avanto de 1,5 T. Trae ceT1 MPRAGE/FLASH 3D (0,4 × 0,4 mm, 1–1,5 mm de corte) y **hrT2 3D CISS** (0,47 × 0,47 mm, 1–1,5 mm), más RTSTRUCT, RTDOSE y RTPLAN. Son 28,2 GB y 1.928 series, en DOI 10.7937/TCIA.9YTJ-5Q73, versión 2 (2021-03-17).

**Licencia verificada.**
- Página https://www.cancerimagingarchive.net/collection/vestibular-schwannoma-seg/: "CC BY 4.0". La API NBIA (`getSeries`) devuelve en las 1.928 series `LicenseName: "Creative Commons Attribution 4.0 International License"`.
- El LICENSE que viene dentro de la descarga dice: *"The Vestibular-Schwannoma-SEG collection is distributed under the CC BY 4.0"*.
- **Por qué aparecía "CC BY 3.0".** Es texto genérico de la política de TCIA que viene en el mismo LICENSE: *"Most data are freely available … as outlined in the Creative Commons Attribution 3.0 Unported License or the Creative Commons Attribution 4.0 International License"*. Esta colección es 4.0.
- **Acuerdo de uso (DUA).** No hay que firmar nada ni registrarse; el acceso es público. Sí rige la *TCIA Data Usage Policy*: no reidentificar, no generar *"facial images or comparable representations"* que permitan identificar, y citar el dataset en toda publicación. Los volúmenes ya vienen con la cara borrada (*defacing*); se ve en los PNG.

**¿Se puede rotular o recortar?** Sí (CC BY 4.0). Solo hay que evitar reconstrucciones 3D de superficie de la cara.

**Atribución sugerida.** *Shapey J, Kujawa A, Dorent R, et al. (2021). Segmentation of Vestibular Schwannoma from Magnetic Resonance Imaging: An Open Annotated Dataset and Baseline Algorithm (v2) [Data set]. The Cancer Imaging Archive. doi:10.7937/TCIA.9YTJ-5Q73. CC BY 4.0.* Se agrega el artículo: *Sci Data 8, 286 (2021). doi:10.1038/s41597-021-01064-w*.

**Receta (sin NBIA Data Retriever; la API REST es pública y no pide token):**
```bash
# 1) listar series (JSON, 1,5 MB)
curl -s "https://services.cancerimagingarchive.net/nbia-api/services/v1/getSeries?Collection=Vestibular-Schwannoma-SEG&format=json" -o vs_series.json
# 2) bajar una serie (zip de DICOM, 20-60 MB)
curl -s "https://services.cancerimagingarchive.net/nbia-api/services/v1/getImage?SeriesInstanceUID=<UID>" -o serie.zip && unzip serie.zip -d serie/
# 3) contornos del tumor en JSON (16 MB, sirven para elegir casos por tamaño)
curl -sL -A "Mozilla/5.0" https://www.cancerimagingarchive.net/wp-content/uploads/Vestibular-Schwannoma-SEG-contours-Mar-2021.zip -o contours.zip
```
Las series se abren con pydicom y se ordenan por `ImagePositionPatient[2]`. Ver `scripts/render_dcm.py`, `render_zoom.py` y `render_vs_contour.py`. Los contornos están en LPS: x < 0 es el lado derecho del paciente.

**Probado.** Sí, con dos pacientes (~180 MB en total):
- **VS-SEG-010** (70 años): un SV quístico grande del ángulo pontocerebeloso derecho, que se ve muy bien en CISS y en T1 con gadolinio (`tcia_vs_t2_zoom.png`, `tcia_vs_t1.png`). El CAI contralateral es normal. Se ven las marcas fiduciales del marco estereotáctico de gamma knife (puntos blancos fuera del cráneo), que conviene recortar.
- **VS-SEG-141**: un **SV intracanalicular pequeño en el fondo del CAI izquierdo** (~0,07 mL, cortes 37–42 del CISS de 1 mm). En el mismo corte se ve el CAI derecho normal con LCR, la cóclea y el vestíbulo (`tcia_vs141_zoom.png`, corte 40). Sirve como imagen de "SV pequeño frente a CAI normal" en una sola figura.
- Con el script de volúmenes (sección 6) se ordenaron los 155 tumores por tamaño. Los más chicos (candidatos intracanaliculares) son VS-SEG-018, 141, 111, 112, 195 y 085.

**Veredicto: SÍ.** Es la mejor fuente para el SV y para el CAI normal contralateral en CISS. Muestra el nervio como un defecto de señal en el LCR del CAI, aunque a 1–1,5 mm no se separan bien los cuatro nervios.

#### 2b. Dataset longitudinal 2025: Vestibular-Schwannoma-MC-RC2 (arXiv 2511.00472)

- La página https://www.cancerimagingarchive.net/collection/vestibular-schwannoma-mc-rc2/ (DOI 10.7937/BQ0Z-XA62) dice **"CC BY 4.0"** y tiene acceso público. Versión 1 del 2025-11-05.
- Ojo: la etiqueta CC BY-NC-ND 4.0 de arXiv corresponde **al preprint**, no a los datos.
- Contenido: 190 pacientes, 621 controles y 1.157 estudios (543 T1CE, 481 T1, 133 T2), multicéntrico y de rutina clínica. Viene en **NIfTI**, no DICOM, y pesa 6 GB.
- Descarga: en la página es por IBM Aspera (plugin). No lo bajé, porque supera el presupuesto y requiere Aspera.
- Sirve para mostrar el **crecimiento en el tiempo** de un SV (vigilar y repetir RM).
- Atribución: *Wijethilake N, et al. (2025). Vestibular-Schwannoma-MC-RC2 (v1). TCIA. doi:10.7937/BQ0Z-XA62. CC BY 4.0.*
- **Veredicto: SÍ (licencia).** No está probado.

---

### 3. OpenEar (Sieber et al. 2019, Sci Data, doi:10.1038/sdata.2018.297)

**Qué es.** Ocho huesos temporales de cadáver (ALPHA a THETA), cada uno con:
- CBCT sin incluir y CBCT incluido en resina, en DICOM y NRRD registrado, a 0,125 mm isotrópico;
- micro-slicing fotográfico;
- segmentación de 13 estructuras: rampa timpánica, rampa vestibular, martillo, yunque, estribo, nervio coclear-vestibular, facial, cuerda del tímpano, membrana timpánica, CAE, seno sigmoide/duramadre, carótida y hueso;
- modelos PLY.

**Licencia verificada** (API de Zenodo):
- Zenodo **1342658** es la v1 (2018). Está **restringida**, sin archivos ni licencia pública. Por eso aparecía como "restricted".
- La versión nueva, **Zenodo 1473724** (2019-01-08, concept DOI 10.5281/zenodo.1342657), tiene `access_right: open` y `license: cc-by-4.0`. Archivos: ALPHA 7,3 GB, BETA 7,5, GAMMA 13,5, DELTA 14,0, EPSILON 4,0, ZETA 3,9, ETA 4,6 y THETA 4,4 GB.

**¿Se puede rotular o recortar?** Sí (CC BY 4.0).

**Atribución sugerida.** *Sieber DM, Erfurt P, John S, et al. (2019). The OpenEar library of 3D models of the human temporal bone based on computed tomography and micro-slicing. Sci Data 6, 180297. Datos: doi:10.5281/zenodo.1473724. CC BY 4.0.*

**Receta.** No hay que bajar los 4–14 GB del zip; se extrae solo el miembro que interesa:
```bash
python3 -I scripts/rzip.py "https://zenodo.org/api/records/1473724/files/ZETA.zip/content"     # lista
python3 -I scripts/rzip2.py "https://zenodo.org/api/records/1473724/files/ZETA.zip/content" \
   05_Registred_Slicer_Volumes/CBCT_Embedded.nrrd CBCT_Embedded.nrrd                         # 116 MB
```
Se abre con `pynrrd` (`nrrd.read`) o con 3D Slicer. La segmentación es `06_Segmentation/Segmentation.seg.nrrd` (5,8 MB, 13 segmentos con nombre en la cabecera).

**Probado.** Sí: ZETA, CBCT incluido (668×587×625 a 0,125 mm). Se ven cóclea, vestíbulo, canales semicirculares y mastoides neumatizada con una resolución excelente (`openear_crop.png`). Pero es **un bloque de hueso cortado dentro de un cilindro de resina**, y los cortes del volumen no siguen los planos clínicos (axial y Pöschl/Stenvers). No parece una TC de paciente.

**Veredicto: SÍ, con matices.** Sirve para anatomía fina del oído interno y medio, sobre todo junto con la segmentación, o para renderizar los modelos 3D. No sirve como "TC de peñasco normal de un paciente". Para eso hay que reformatear en un plano oblicuo y recortar el cilindro, y aun así el lector verá un espécimen.

---

### 4. Otros candidatos

#### 4a. Human Bony Labyrinth (Wimmer et al. 2019, Data in Brief), Zenodo 3355272
- **Licencia.** La API de Zenodo dice `cc-by-4.0`, acceso abierto. Son 23 especímenes, de 21 a 49 MB cada uno.
- **Contenido.** TC clínica (0,156 × 0,156 × 0,2 mm) y micro-TC (0,06 mm) corregistradas, más etiquetas, superficies PLY y landmarks. Formato NIfTI.
- **Receta.** `curl -sL "https://zenodo.org/api/records/3355272/files/F07.zip/content" -o F07.zip` y se abre con nibabel.
- **Probado.** Sí (F07, `bony_ct.png`). Es un recorte de solo ~15 × 12 × 20 mm alrededor del laberinto. Se ven la vuelta basal de la cóclea, el vestíbulo y los canales, pero no hay contexto (oído medio, CAE ni CAI completos).
- **Veredicto: SÍ** para recuadros ampliados del laberinto. **No** sirve para una TC de peñasco completa.
- Atribución: *Wimmer W, Vandersteen C, Guevara N, Caversaccio M, Delingette H (2019). Human bony labyrinth dataset… Data Brief 27:104782. Datos doi:10.5281/zenodo.3355272. CC BY 4.0.*

#### 4b. IE-Map (Ahmadi et al. 2021, Sci Rep), GIN `SpaceGinny/IEMap`
- **Licencia.** El LICENSE.txt dentro del zip es el texto completo de **CC BY 4.0** (*"Attribution 4.0 International"*).
- **Contenido.** Plantillas in vivo **CISS, T2 y T1** (0,2 mm isotrópico) del oído interno, promedio de 126 oídos de 63 sanos. También trae plantillas de TC y micro-TC, segmentación de subestructuras, mallas VTK y 94 landmarks.
- **Receta.** `curl -sL https://gin.g-node.org/SpaceGinny/IEMap/raw/master/IEMap_data_v_1_0.zip -o iemap.zip` (311 MB) y se abre con nibabel o 3D Slicer (trae la escena `.mrml`).
- **Probado.** Sí (`iemap_ciss.png`). Muestra un laberinto membranoso brillante en T2 y la cisterna del ángulo pontocerebeloso, en una imagen lisa de plantilla promedio.
- **Veredicto: SÍ** para una figura anatómica rotulada del laberinto en RM, con la aclaración "plantilla promedio, no un paciente".
- Atribución: *Ahmadi SA, Raiser TM, Rühl RM, Flanagin VL, zu Eulenburg P (2021). IE-Map… Sci Rep 11:3293. doi:10.1038/s41598-021-82716-0. CC BY 4.0.*

#### 4c. TC clínica de peñasco normal completa
No encontré un dataset abierto con TC de peñasco de pacientes en algoritmo óseo de alta resolución. Las opciones con licencia limpia son todas de especímenes (OpenEar, Bony Labyrinth) o plantillas (IE-Map, que trae una plantilla de TC). Lo más cercano a una TC de cabeza de paciente es **CQ500** (4e), pero es una TC de cerebro de 5 mm o fina, no de peñasco. Para TC de peñasco clínica, lo más práctico sigue siendo buscar una figura CC BY en PMC (método del archivo `imagenes.md`) o pedir permiso a un autor de Radiopaedia.

#### 4d. OpenNeuro (RM cerebral normal)
- **Licencia.** https://openneuro.readthedocs.io/faq.html dice *"all newly published datasets are released under CC0, as are new versions of previously released datasets"*. Algunos datasets antiguos pueden ser PDDL o CC BY; hay que revisar el campo `License` del `dataset_description.json` de cada uno.
- **Utilidad.** No encontré en OpenNeuro un dataset con T2 3D dedicado a los CAI (CISS o SPACE). Una T1 o T2 cerebral de rutina a 1 mm muestra el ángulo pontocerebeloso, pero no los nervios del CAI. Para ese fin conviene más el lado sano de Vestibular-Schwannoma-SEG (sección 2) o IE-Map (4b).
- **Veredicto: DUDOSO por utilidad** (la licencia CC0 está bien). No está probado.
- Aparte, **IXI** (600 sanos, T1/T2/PD/MRA/DTI) es *"Creative Commons CC BY-SA 3.0"* según https://brain-development.org/ixi-dataset/. Es BY-SA: solo se puede usar sin modificar. **NO** se puede rotular.

#### 4e. CQ500 (Qure.ai, TC de cráneo sin contraste, 491 estudios)
- **Licencia.** El sitio oficial headctstudy.qure.ai **ya no resuelve DNS** (2026-10-17). En la copia de la Wayback Machine del 2024-11-12 dice: *"CQ500 dataset by qure.ai is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. Any rights in individual contents of the dataset are licensed under the End User License Agreement (EULA)."* La descarga pedía nombre, institución y correo, y aceptar *"CC-BY-NC-SA and EULA"*.
- No pude leer el EULA, que se impone sobre los contenidos individuales, y el sitio oficial está caído. Hay espejos de terceros (por ejemplo, las etiquetas Seg-CQ500 en Zenodo 8063221, CC BY 4.0, pero solo son máscaras de hemorragia).
- **Veredicto: DUDOSO.** La licencia es idéntica a la del libro, pero hay un EULA sin leer y la fuente oficial ya no existe. No está probado.

#### 4f. ISLES 2022 (infarto, DWI/ADC/FLAIR), Zenodo 7153326
- **Licencia.** La API de Zenodo da v2.3 con `license: cc-by-4.0` y `access_right: open`. Las versiones 1.0 y 2.1 (6695025, 6761864) son restringidas: hay que usar 7153326.
- **Contenido.** 250 casos de entrenamiento en NIfTI/BIDS, con cráneo removido (*skull-stripped*), DWI b=1000 + ADC + FLAIR + máscara experta. Las imágenes son de baja resolución (DWI de 112 × 112 por corte, unos 2 mm), suficiente para una figura.
- **¿Hay infartos de fosa posterior?** Sí. Con un script sobre las 250 máscaras (el tercio inferior del volumen concentra la lesión) salieron más de 20 candidatos, y se miraron dos:
  - **sub-strokecase0157**: infarto **cerebeloso hemisférico** (~3,5 mL), con DWI brillante y ADC oscuro (`isles_0157.png`). Típico de PICA, relevante para el capítulo de vértigo central.
  - **sub-strokecase0174**: un infarto **pontino paramediano** pequeño (`isles_0174.png`).
  - Otros candidatos sin mirar: 0130 (4,4 mL), 0148, 0203, 0068.
  - Ojo con la orientación: con `as_closest_canonical` + `.T` + `origin="lower"` la imagen queda en convención neurológica (derecha del paciente a la derecha de la imagen). Para la convención radiológica hay que espejar.
- **Receta.**
  ```bash
  python3 -I scripts/rzip3.py "https://zenodo.org/api/records/7153326/files/ISLES-2022.zip/content" "_msk\.nii\.gz$" isles/msk      # 250 máscaras, 3,6 MB
  python3 -I scripts/rzip3.py "https://zenodo.org/api/records/7153326/files/ISLES-2022.zip/content" "strokecase0157_ses-0001_(dwi|adc|FLAIR)\.nii\.gz$" isles/img
  ```
  Se abre con nibabel. Ver `scripts/render_isles.py`.
- **Veredicto: SÍ.**
- Atribución: *Hernandez Petzsche MR, de la Rosa E, Hanning U, et al. (2022). ISLES 2022: A multi-center magnetic resonance imaging stroke lesion segmentation dataset. Sci Data 9:762. Datos doi:10.5281/zenodo.7153326. CC BY 4.0.*
- **ISLES 2015** (SMIR) requiere registro. No verifiqué su licencia; no hace falta teniendo ISLES 2022.

#### 4g. Esclerosis múltiple: MSLesSeg (Guarnera et al. 2025, Sci Data 12:920)
- **Licencia.** La API de figshare (artículo 27919209, DOI 10.6084/m9.figshare.27919209) da `license: CC BY` → https://creativecommons.org/licenses/by/4.0/. El artículo en PMC es CC BY-NC-ND, pero eso aplica al texto, no a los datos.
- **Contenido.** 75 pacientes y 115 estudios con T1, T2, FLAIR y máscara. Están en NIfTI registrado a MNI152 (182×218×182, 1 mm, LAS) y con cráneo removido. `MSLesSeg Dataset.zip` pesa 1,47 GB y el RAW 1,3 GB.
- **Receta** (por rangos, usando la URL de ndownloader, porque la URL S3 firmada vence en segundos):
  ```bash
  python3 -I scripts/rzip3.py "https://ndownloader.figshare.com/files/52771814" "test/P72/P72_(FLAIR|T2|MASK)\.nii\.gz$" mslesseg/
  ```
- **Probado.** Sí: P72, el de mayor carga lesional del test (`mslesseg_flair.png`). Se ven bien las lesiones periventriculares en FLAIR. La imagen es algo blanda por el registro a MNI. Para lesiones infratentoriales habría que buscar caso por caso con las máscaras.
- **Veredicto: SÍ.**
- Atribución: *Guarnera F, Rondinella A, et al. (2025). MSLesSeg… Sci Data 12:920. doi:10.1038/s41597-025-05250-y. Datos doi:10.6084/m9.figshare.27919209. CC BY 4.0.*
- **Otros.** ISBI 2015 pide registro y no lo verifiqué. Ljubljana (lit.fe.uni-lj.si) se anuncia CC BY, pero no lo verifiqué.

#### 4h. TC de senos paranasales: NasalSeg (Zenodo 13893419)
- **Licencia.** La API de Zenodo da `cc-by-4.0`, acceso abierto. Un zip de 224 MB con 130 TC en NRRD (`images/Pxxx_img.nrrd`, ~2 MB cada una) y etiquetas de fosas nasales, nasofaringe y senos maxilares.
- **Receta.** `python3 -I scripts/rzip3.py "https://zenodo.org/api/records/13893419/files/NasalSeg.zip/content" "images/P00[12]_img\.nrrd$" nasalseg/`, o bajar el zip entero. Se abre con pynrrd.
- **Probado.** Sí (P001, `nasalseg_P001.png`): 153×205×52 a 0,59 × 0,59 × 1,5 mm, recortada a la región nasosinusal. Se ven bien los cornetes, el septo, los senos maxilares, las celdillas etmoidales y el esfenoides en axial. El coronal, reformateado a 1,5 mm, se ve aceptable. **Los globos oculares vienen enmascarados en negro** (anonimización), lo que se nota en los cortes altos.
- **Veredicto: SÍ** para anatomía nasosinusal normal (axial, y coronal aceptable). No revisé si hay casos con ocupación sinusal.
- Atribución: los autores son los del artículo de NasalSeg (Sci Data 2024); hay que confirmar la cita exacta en el registro de Zenodo antes de publicar. Datos doi:10.5281/zenodo.13893419, CC BY 4.0.
- **CT-SCOPE** (Zenodo 15085103) es **restringido**, sin licencia pública: NO.

#### 4i. MedPix (NLM)
- https://medpix.nlm.nih.gov/ redirige a https://lhncbc.nlm.nih.gov/medpix.html, que dice que la base de imágenes está *"temporarily unavailable due to technical issues"*.
- La copia de la Wayback Machine del 2025-10-11 de /licensing dice: *"The MedPix® Medical Image Database, Teaching File, CME, and CUP functions are no longer available at NLM. Please visit their new home at the ASNR"*.
- La página de ASNR (Case of the Week) solo dice *"Copyright ©2005 – 2023 American Society of Neuroradiology. All Rights Reserved."*, sin licencia abierta.
- Según https://www.nlm.nih.gov/web_policies.html, las obras del gobierno de EE. UU. son de dominio público, pero los aportes de terceros (como los casos de MedPix) pueden tener copyright.
- **Veredicto: NO.** El servicio ya no está y no hay licencia abierta verificable.

---

### 5. Tabla resumen

| Fuente | Modalidad útil | Licencia verificada | ¿Rotular? | Probado | Veredicto |
|---|---|---|---|---|---|
| Radiopaedia | TC/RM/Rx de todo | CC BY-NC-SA 3.0 "modificada"; **"Publishing a textbook" = Definitely not permitted** | Solo con permiso del autor | No (sin API) | **DUDOSO → NO sin permiso escrito** |
| TCIA Vestibular-Schwannoma-SEG | RM ceT1 + CISS de SV (y CAI sano contralateral) | CC BY 4.0 (página + API + LICENSE) + política TCIA | Sí (sin reconstruir la cara) | Sí: VS-SEG-010 (SV grande) y 141 (intracanalicular) | **SÍ** |
| TCIA Vestibular-Schwannoma-MC-RC2 (2025) | RM longitudinal de SV, NIfTI | CC BY 4.0 (el preprint es BY-NC-ND, pero los datos no) | Sí | No (6 GB, Aspera) | **SÍ** (licencia) |
| OpenEar v2 (Zenodo 1473724) | CBCT 0,125 mm de espécimen + segmentación | CC BY 4.0 (la v1 1342658 es restringida) | Sí | Sí (ZETA) | **SÍ con matices** (espécimen en resina, no paciente) |
| Human Bony Labyrinth (Zenodo 3355272) | TC y micro-TC del laberinto | CC BY 4.0 | Sí | Sí (F07) | **SÍ** solo para recuadros ampliados |
| IE-Map (GIN) | Plantilla CISS/T2 del oído interno + TC | CC BY 4.0 (LICENSE) | Sí | Sí | **SÍ** (como plantilla) |
| OpenNeuro | RM cerebral | CC0 (FAQ) | Sí | No | **DUDOSO por utilidad** (no hay CAI) |
| IXI | RM cerebral sana | CC BY-SA 3.0 | **No** (solo sin modificar) | No | **NO** para figuras rotuladas |
| CQ500 | TC de cráneo | CC BY-NC-SA 4.0 + EULA (sitio caído, leído en Wayback) | Sí, pero hay un EULA sin leer | No | **DUDOSO** |
| ISLES 2022 (Zenodo 7153326) | DWI/ADC/FLAIR de infarto, con casos cerebelosos y pontinos | CC BY 4.0 (v2.3) | Sí | Sí: 0157 cerebelo, 0174 protuberancia | **SÍ** |
| MSLesSeg (figshare 27919209) | FLAIR/T2/T1 de EM | CC BY 4.0 | Sí | Sí (P72) | **SÍ** |
| NasalSeg (Zenodo 13893419) | TC de senos paranasales | CC BY 4.0 | Sí | Sí (P001; ojos enmascarados) | **SÍ** |
| CT-SCOPE (Zenodo 15085103) | TC de senos | Restringido | — | No | **NO** |
| MedPix (NLM → ASNR) | Varios | Sin licencia abierta; servicio retirado | — | No | **NO** |
| Radiografía simple | — | Ninguna de las fuentes probadas trae Rx de cabeza o cuello; queda Commons/PMC (`imagenes.md`) | — | — | Pendiente |

### 6. Archivos de esta revisión
- Scripts (fuera de las carpetas de datos), en `docs/libro/herramientas/imagenologia/`:
  - zips remotos: `rzip.py`, `rzip2.py`, `rzip3.py`;
  - renderizado: `render_dcm.py`, `render_zoom.py`, `render_vs_contour.py`, `render_nrrd.py`, `render_nrrd_crop.py`, `render_ct_nrrd.py`, `render_nii.py`, `render_isles.py`.
- PNG de verificación en (carpeta temporal de la búsqueda, ya borrada):
  - `tcia_vs_t2.png`, `tcia_vs_t2_zoom.png`, `tcia_vs_t1.png`, `tcia_vs141_t2.png`, `tcia_vs141_zoom.png`;
  - `openear_axial.png`, `openear_crop.png`, `bony_ct.png`, `iemap_ciss.png`;
  - `isles_0157.png`, `isles_0174.png`, `mslesseg_flair.png`, `nasalseg_P001.png`.
- Metadatos guardados en `datasets/web/`: lista de series TCIA, listados de zips y XML de MSLesSeg.
- Para elegir un SV intracanalicular, el volumen aproximado de cada tumor se calcula desde los contornos JSON (área del polígono × espesor). Los más chicos son VS-SEG-018, 141, 111, 112, 195 y 085.

---

# Parte II. Oído y hueso temporal

Búsqueda hecha el 2026-10-17. Destino: libro gratuito CC BY-NC-SA 4.0. Complementa `docs/libro/investigacion/imagenes.md` (otoscopía, anatomía ilustrada y técnica).

**Cómo se verificó.** Se usó el mismo método que en `imagenes.md`. En los artículos de PMC, la licencia se leyó del campo `license` de Europe PMC y del bloque `<license>` del XML completo. En todos los casos de esta lista las dos fuentes coincidieron. En Wikimedia Commons, la licencia y el autor salieron de la API (`extmetadata`: LicenseShortName/Artist). Para buscar se usó la búsqueda de Europe PMC en los **pies de figura** (`FIG:`) con filtro de licencia. Open-i (por modalidad) funcionó al principio y después empezó a devolver páginas de error, así que casi todo salió de Europe PMC. Se leyó el pie completo de cada figura para descartar "with permission", "adapted from" y "reproduced from". Las imágenes marcadas **(vista)** se bajaron a (carpeta temporal de la búsqueda, ya borrada) (nunca al repo) y se miraron. El nombre del archivo local va entre corchetes. La URL "img" es la figura a resolución completa en el CDN de PMC, que suele ser más grande que los 512 px de Open-i.

**Radiopaedia.** Su página de licencia dice que los casos son **CC BY-NC-SA 3.0** y pide esta atribución: "Case courtesy of <autor>, Radiopaedia.org, rID: <n>", con enlace. Las imágenes del visor no se pueden bajar por script (el sitio responde con un desafío anti-bot), así que los casos de Radiopaedia quedan como alternativa y **no** están vistos.

**Notas de licencia** (las mismas de `imagenes.md`): CC0, PD, CC BY y CC BY-NC se pueden usar y modificar con atribución. CC BY-NC-SA es igual al libro. CC BY-SA solo se puede usar **sin modificar** (no recortar, no rotular, no traducir). ND se descarta.

Formato de atribución: *Autores (año). Título. Revista. doi. Fig. N. Licencia.*

---

### 1. (B1) Anatomía normal: TC de temporal y RM del CAI

#### 1a. TC normal, axial y coronal

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 3: **4 cortes axiales de TC normal ya rotulados** (caudal a craneal): ACI, acueductos coclear y vestibular, CSP, CSL, CSS, vestíbulo, vueltas basal/media/apical de la cóclea, CAI, martillo, VII (laberíntico, timpánico, mastoideo), ganglio geniculado, trompa **(vista)** [PMC8520521_f3.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC8520521/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4d53/8520521/11d07439a901/11547_2021_1387_Fig3_HTML.jpg | CC BY 4.0 | Feraco P, Piccinini S, Gagliardo C (2021). Imaging of inner ear malformations: a primer for radiologists. Radiol Med. doi:10.1007/s11547-021-01387-z. Fig. 3 | **sí** (la mejor axial: ya rotulada, en abreviaturas inglesas que se pueden traducir) |
| Fig. 1 A–C: TC **normal** de oído derecho, coronal (escudo intacto, articulación incudoestapedial) y 2 axiales (epitímpano lateral aireado), en la misma lámina que colesteatoma pars flaccida, pars tensa y OMC **(vista)** [PMC11913933_f1.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC11913933/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/c964/11913933/8aa2ca73a56d/330_2024_11021_Fig1_HTML.jpg | CC BY 4.0 | Touska P, Connor SEJ (2025). ESR Essentials: imaging of middle ear cholesteatoma. Eur Radiol. doi:10.1007/s00330-024-11021-x. Fig. 1 | **sí** (coronal normal del oído medio; sirve también para el cap. 3) |
| Fig. 4: TC normal axial y coronal con **estructuras coloreadas** (cóclea, huesecillos, VII, CAI, vestíbulo, CSP, MT) en un lado y el otro lado sin color para comparar **(vista)** [PMC12302556_f4.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC12302556/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/fed5/12302556/5995504fafc5/ADVS-12-e00556-g019.jpg | CC BY 4.0 | Batts S, Pham N, Tearney G, Stankovic KM (2025). The State of High-Resolution Imaging of the Human Inner Ear. Adv Sci. doi:10.1002/advs.202500556. Fig. 4 | sí (muy didáctica, pero chica: 600×262. Ojo: el archivo es `g019`, no `g004`) |
| Fig. 2: TC axial normal con **rótulos** (huesecillos, cóclea, CAE, CAI, celdas mastoideas) y líneas **dibujadas** de fractura longitudinal, transversa y mixta **(vista)** [PMC12984264_f2.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC12984264/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/ac72/12984264/d2d4be4b621e/diagnostics-16-00718-g002.jpg | CC BY 4.0 | Edris OMK et al. (2026). Temporal Bone Fractures on High-Resolution CT. Diagnostics. doi:10.3390/diagnostics16050718. Fig. 2 | sí (el corte es normal y las fracturas son líneas "imaginarias". Sirve como esquema en B1 o en el cap. 7) |
| Fig. 9a: coronal normal, "**ojo de caracol**" (vueltas de la cóclea más los segmentos laberíntico y timpánico del VII) **(vista)** [PMC6775179_f9.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC6775179/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/8e99/6775179/b296eb88604e/13244_2019_782_Fig9_HTML.jpg | CC BY 4.0 | Gulati M, Gupta S, Prakash A, Garg A, Dixit R (2019). HRCT imaging of acquired cholesteatoma: a pictorial review. Insights Imaging. doi:10.1186/s13244-019-0782-y. Fig. 9 | sí (recortar el panel a; el b es patológico) |
| Serie axial completa de TC de cráneo normal (74 cortes) de Hellerhoff, "Temporal bone in computertomography case 001" **(vista: cortes 14, 20, 24 y 28)** [commons_CT-Felsenbein-*.jpg] | https://commons.wikimedia.org/wiki/Category:Temporal_bone_in_computertomography_case_001 (p. ej. https://commons.wikimedia.org/wiki/File:CT-Felsenbein-20.jpg) | CC BY 3.0 | Hellerhoff, Wikimedia Commons | dudoso (cráneo entero a 648×696; el temporal queda chico. Sirve si se recorta y se rotula) |
| *Alternativa Radiopaedia*: "CT temporal bone axial – labelling questions" (59 estructuras numeradas, con versión sin rótulos) | https://radiopaedia.org/cases/ct-temporal-bone-axial-labelling-questions | CC BY-NC-SA 3.0 | Case courtesy of Craig Hacking, Radiopaedia.org, rID: 63096 | sí, como respaldo (no vista) |
| *Alternativa Radiopaedia*: "CT temporal bone coronal – labelling questions" | https://radiopaedia.org/cases/ct-temporal-bone-coronal-labelling-questions | CC BY-NC-SA 3.0 | Case courtesy of Craig Hacking, Radiopaedia.org, rID: 63095 | sí, como respaldo (no vista) |
| *Alternativa Radiopaedia*: "Normal petrous temporal bone CT" | https://radiopaedia.org/cases/normal-petrous-temporal-bone-ct | CC BY-NC-SA 3.0 | Case courtesy of Andrew Dixon, Radiopaedia.org, rID: 32484 | sí, como respaldo (no vista) |

#### 1b. RM T2 de alta resolución del CAI (sagital oblicuo con los 4 nervios)

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 4: **sagital oblicuo del CAI rotulado**: oído normal con nervio facial, rama coclear y ramas vestibulares (a–b) frente al oído contralateral con aplasia coclear (c–d), en el mismo lactante **(vista)** [PMC9324637_f4.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC9324637/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/df46/9324637/9e9a9f5d79e7/jcm-11-03966-g004.jpg | CC BY 4.0 | Johansson M, Karltorp E, Edholm K, Drott M, Berninger E (2022). A Prospective Study of Etiology and Auditory Profiles in Infants with Congenital Unilateral SNHL. J Clin Med. doi:10.3390/jcm11143966. Fig. 4 | **sí** (la mejor: rotulada, con lo normal y lo patológico juntos; sirve para B1 y para el cap. 13/17) |
| Fig. 5c: **línea del plano sagital oblicuo** sobre el axial, **esquema de los 4 cuadrantes** (facial antero-superior, coclear antero-inferior, vestibulares posteriores) y el corte real a 7 T con los 4 nervios **(vista)** [PMC11790716_f5.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC11790716/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/0727/11790716/f5b33d23daec/10334_2024_1213_Fig5_HTML.jpg | CC BY 4.0 | Aphiwatthanasumet K et al. (2025). Morphology of the human inner ear and vestibulocochlear nerve assessed using 7 T MRI. MAGMA. doi:10.1007/s10334-024-01213-3. Fig. 5 | **sí** (enseña cómo se saca el corte; los paneles a–b muestran el VII y el VIII en axial) |
| Fig. 1 A–C: 3D-FIESTA axial con nervios coclear y vestibular y modiolo, más sagital oblicuo con los 4 nervios **(vista)** [PMC2765183_f1.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC2765183/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7d0e/2765183/eedbf48a4be7/IJRI-19-99-g001.jpg | CC BY | Gupta SS, Maheshwari SR, Kirtane MV, Shrivastav N (2009). Pictorial review of MRI/CT Scan in congenital temporal bone anomalies, in patients for cochlear implant. Indian J Radiol Imaging. doi:10.4103/0971-3026.50825. Fig. 1 | sí (el panel C, sagital, es chico) |
| Fig. 3: sagital (parasagital de cráneo entero) del CAI izquierdo normal con los 4 nervios; Fig. 2 = lado derecho sin nervio coclear **(vista)** [PMC11604252_f2/f3.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC11604252/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/edb3/11604252/e01f11f39f3c/cureus-0016-00000072582-i03.jpg | CC BY 4.0 | Khaladkar SM, Sharma O, Jain S, Varma A (2024). Silent Signals: Unveiling Cochlear Nerve Deficiency in a Child Through Imaging. Cureus. doi:10.7759/cureus.72582. Figs. 2–3 | dudoso (corte amplio: el CAI ocupa poco; hay que recortar mucho) |
| Fig. 6 A–B: sagital oblicuo del fondo del CAI: 3 nervios en el lado afectado (falta el coclear) frente a 4 en el sano, con flechas de color **(vista)** [PMC12813948_f6.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC12813948/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/6e45/12813948/ecc7207c399e/cureus-0017-00000099683-i06.jpg | CC BY 4.0 | Pinto Alberto K et al. (2025). Intellectual Developmental Disorder of Autosomal Dominant 61 Caused by a MED13 Variant… Cureus. doi:10.7759/cureus.99683. Fig. 6 | sí (alternativa a PMC9324637, con más ruido de imagen) |

---

### 2. (cap. 1) Atresia aural congénita en TC

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 2: foto más TC axial. (A) conducto visible con estenosis ósea severa (flecha larga) y conducto normal contralateral (flecha corta). (B) atresia completa con microtia, también con el lado normal **(vista)** [PMC9831057_f2.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC9831057/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/b86a/9831057/14b860939bd4/fsurg-09-944223-g002.jpg | CC BY 4.0 | Truong MT et al. (2022). Integrated microtia and aural atresia management. Front Surg. doi:10.3389/fsurg.2022.944223. Fig. 2 | **sí, confirmada** (la mejor para el caso: une la oreja con la TC y trae el lado sano. La TC es de cráneo entero; para ver la placa atrésica hay que recortar) |
| Fig. 2 A–C: TC axial del oído derecho **normal, con estenosis y con atresia**, en el mismo plano y la misma ventana **(vista)** [PMC4661245_f2.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC4661245/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/45be/4661245/69dfcffc3412/ceo-8-320-g002.jpg | CC BY-NC 3.0 | Qin FH, Zhang TY, Dai P, Yang L (2015). Anatomic Variants on Computed Tomography in Congenital Aural Atresia and Stenosis. Clin Exp Otorhinolaryngol. doi:10.3342/ceo.2015.8.4.320. Fig. 2 | **sí** (mejor que PMC9831057 para mostrar el hueso; las líneas de medición se pueden explicar o tapar) |
| Fig. 8A: coronal con hipoplasia del CAE, estenosis membranosa y ósea, conducto vertical y placa atrésica delgada. Fig. 8C: coronal con CAI estrechos **(vista)** [PMC6383528_f08.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC6383528/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/8831/6383528/28273b4c3523/rb-52-01-0054-g08.jpg | CC BY | Salata TM, Ribeiro BNF, Muniz BC, Antunes LO, Rosas HB, Marchiori E (2019). Hearing disorders – findings on computed tomography and magnetic resonance imaging: pictorial essay. Radiol Bras. doi:10.1590/0100-3984.2016.0213. Fig. 8 | sí (coronal; complementa a las axiales) |
| Figs. 1–4: TC de haz plano (fpVCT) de atresia: estribo, complejo martillo-yunque malformado, VII aberrante, placa atrésica, con rótulos numerados | https://pmc.ncbi.nlm.nih.gov/articles/PMC11618206/ | CC BY 4.0 | Müller-Graff FT et al. (2024). Improved radiological imaging of congenital aural atresia using flat-panel volume CT. HNO. doi:10.1007/s00106-024-01512-0 | dudoso (no vista; es técnico, sirve para Jahrsdoerfer más que para la clínica) |

---

### 3. (cap. 3) Colesteatoma en TC (escudo y ático)

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 1: lámina comparativa **normal / colesteatoma pars flaccida / pars tensa / OMC**. El escudo intacto (A) y el escudo erosionado con partes blandas en el espacio de Prussak (D–E) **(vista)** [PMC11913933_f1.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC11913933/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/c964/11913933/8aa2ca73a56d/330_2024_11021_Fig1_HTML.jpg | CC BY 4.0 | Touska P, Connor SEJ (2025). Eur Radiol. doi:10.1007/s00330-024-11021-x. Fig. 1 | **sí** (la mejor: trae lo normal y lo patológico, y además el diferencial) |
| Fig. 2: coronal **bilateral**: escudo normal a la izquierda (flecha) y escudo erosionado a la derecha con partes blandas en el oído medio y el CAE **(vista)** [PMC6775179_f2.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC6775179/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/8e99/6775179/6edd73c5f8e7/13244_2019_782_Fig2_HTML.jpg | CC BY 4.0 | Gulati M et al. (2019). Insights Imaging. doi:10.1186/s13244-019-0782-y. Fig. 2 | **sí** (lado sano y lado enfermo en el mismo corte) |
| Fig. 7: axial bilateral: "**cono de helado**" normal a la izquierda y perdido a la derecha, más defecto del tegmen sinodural | https://pmc.ncbi.nlm.nih.gov/articles/PMC6775179/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/8e99/6775179/71f61a0c9a7c/13244_2019_782_Fig7_HTML.jpg | CC BY 4.0 | Gulati M et al. (2019). Fig. 7 | sí (bajada pero no mirada a fondo; complementa a la Fig. 2) |
| Fig. 15 A–B: coronal con masa hipodensa en el epitímpano, destrucción del escudo y erosión inicial de la cadena | https://pmc.ncbi.nlm.nih.gov/articles/PMC10747582/ | CC BY 4.0 | Kloth C et al. (2023). Imaging of Pathologies of the Temporal Bone and Middle Ear… Pictorial Review. Tomography. doi:10.3390/tomography9060170. Fig. 15 | sí (no vista) |
| "Cholesteatom CT serie 1": serie de cortes de TC con el colesteatoma del ático **coloreado en rojo** **(vista)** [commons_Cholesteatom_CT_serie_1.jpg] | https://commons.wikimedia.org/wiki/File:Cholesteatom_CT_serie_1.jpg | CC BY 2.5 | Welleschik, Wikimedia Commons | dudoso (585×471, cortes chicos; vistosa pero poco clínica) |

Hellerhoff tiene en Commons un colesteatoma **del CAE** (`Cholesteatom CT Coronar KF.jpg`, `…Axial KF.jpg`), CC BY-SA 3.0. No es el colesteatoma de ático del caso.

---

### 4. (caps. 4 y 15) Otoesclerosis fenestral y coclear; Paget del temporal

#### 4a. Otoesclerosis

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 1: axial y coronal de oído derecho con **placa hipodensa en la fissula ante fenestram** (otoesclerosis fenestral) **(vista)** [PMC3999364_f1.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC3999364/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/f7dc/3999364/86f8e0d3aab8/13244_2014_313_Fig1_HTML.jpg | CC BY | Purohit B, Hermans R, Op de Beeck K (2014). Imaging in otosclerosis: A pictorial review. Insights Imaging. doi:10.1007/s13244-014-0313-9. Fig. 1 | **sí** (la de referencia para la fenestral) |
| Fig. 12: axial de ambos oídos con el **"doble anillo" pericoclear** (otoesclerosis coclear bilateral) **(vista)** [PMC3999364_f12.jpg] | misma página · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/f7dc/3999364/3b9086b4a296/13244_2014_313_Fig12_HTML.jpg | CC BY | Purohit B et al. (2014). Fig. 12 | **sí** (la de referencia para la retrofenestral) |
| Fig. 2: TC de ultra alta resolución. Fissula derecha hipodensa con ligamento anular engrosado, frente a fissula izquierda **normal** con ligamento fino **(vista)** [PMC10684447_f2.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC10684447/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4dfe/10684447/a3156739e2d1/13244_2023_1562_Fig2_HTML.jpg | CC BY 4.0 | Xu N et al. (2023). Comparative study of the sensitivity of U-HRCT and HRCT in the diagnosis of isolated fenestral otosclerosis. Insights Imaging. doi:10.1186/s13244-023-01562-y. Fig. 2 | **sí** (enfermo frente a sano, muy ampliado y nítido) |
| Fig. 1: otoesclerosis coclear grado 3 bilateral con doble anillo extenso, alta resolución (1600×1420), con muchas flechas de color **(vista)** [PMC13605418_f1.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC13605418/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/b159/13605418/9b9d20dcb010/diagnostics-16-02998-g001.webp | CC BY 4.0 | Tumeļkāns R, Eraslan C, Balodis A (2026). Extensive Cochlear Otosclerosis: CT-MRI Correlation… Diagnostics. doi:10.3390/diagnostics16182998. Fig. 1 | sí (caso avanzado; las flechas cargan la imagen) |
| Fig. 11: (A) focos fenestrales bilaterales; (B) hipodensidad pericoclear bilateral | https://pmc.ncbi.nlm.nih.gov/articles/PMC6383528/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/8831/6383528/ac1448e2b94a/rb-52-01-0054-g11.jpg | CC BY | Salata TM et al. (2019). Radiol Bras. doi:10.1590/0100-3984.2016.0213. Fig. 11 | sí (bajada, no mirada) |
| Fig. 7 de PMC3999364: **hendidura coclear** (variante normal que imita la otoesclerosis) | https://pmc.ncbi.nlm.nih.gov/articles/PMC3999364/ | CC BY | Purohit B et al. (2014). Fig. 7 | sí, como diferencial (no vista) |

#### 4b. Enfermedad de Paget

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 31: axial de base de cráneo con patrón mixto lítico-esclerótico "**en copos de algodón**", engrosamiento cortical y **estrechamiento de ambos CAI** (flechas) **(vista)** [PMC10366931_f31.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC10366931/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/70cf/10366931/30c72df78ba5/tomography-09-00097-g031.jpg | CC BY 4.0 | Battal B, Zamora C (2023). Imaging of Skull Base Tumors. Tomography. doi:10.3390/tomography9040097. Fig. 31 | **sí** (la mejor: se ve el Paget del temporal y además explica la hipoacusia por el CAI) |
| Fig. 12: coronal con **desmineralización pericoclear intensa** a la derecha (Paget de la cápsula ótica) **(vista)** [PMC6383528_f12.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC6383528/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/8831/6383528/a36599c803ac/rb-52-01-0054-g12.jpg | CC BY | Salata TM et al. (2019). Radiol Bras. doi:10.1590/0100-3984.2016.0213. Fig. 12 | sí (bueno para el diferencial con la otoesclerosis coclear) |
| Fig. 16: axial de base de cráneo en Paget. Cápsulas óticas hipodensas que imitan una otoesclerosis, con compromiso difuso de la base **(vista)** [PMC3999364_f16.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC3999364/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/f7dc/3999364/e79f8a6bb19b/13244_2014_313_Fig16_HTML.jpg | CC BY | Purohit B et al. (2014). Fig. 16 | dudoso (396×215, chica) |
| Fig. 2: radiografía lateral de cráneo con el patrón clásico "en copos de algodón" (Paget craneal avanzado con hipoacusia bilateral) | https://pmc.ncbi.nlm.nih.gov/articles/PMC13213082/ | CC BY | Goksoy Solak Y, Imre E, Gogas Yavuz D (2026). Severe hypocalcemia in a patient with extensive cranial Paget disease: a diagnostic challenge. JCEM Case Rep. doi:10.1210/jcemcr/luag100. Fig. 2 | sí, para radiografía simple (no vista) |

---

### 5. (cap. 7) Fractura del hueso temporal

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 11: (a) fractura limitada a la mastoides, **sin compromiso de la cápsula ótica**; (b) fractura que cruza el **CSL y el vestíbulo** (compromete la cápsula) **(vista)** [PMC3292638_f11.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC3292638/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/16d9/3292638/000a7307c838/13244_2011_126_Fig11_HTML.jpg | CC BY-NC 4.0 | Trojanowska A et al. (2012). External and middle ear diseases: radiological diagnosis based on clinical signs and symptoms. Insights Imaging. doi:10.1007/s13244-011-0126-z. Fig. 11 | **sí** (justo el par que pide el capítulo: respeta o compromete la cápsula) |
| Fig. 9: axial con **fractura longitudinal** derecha, subluxación de la articulación incudomaleolar y el lado izquierdo normal para comparar **(vista)** [PMC6383528_f09.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC6383528/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/8831/6383528/a731d98043ae/rb-52-01-0054-g09.jpg | CC BY | Salata TM et al. (2019). Radiol Bras. doi:10.1590/0100-3984.2016.0213. Fig. 9 | **sí** (extracapsular con lesión de la cadena, más el lado sano) |
| Fig. 1 a–b: **fractura transversa** desde el acueducto vestibular hasta el vestíbulo, con **neumolaberinto** (axial y coronal) **(vista)** [PMC11125930_f1.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC11125930/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/9800/11125930/b1caed8c4d78/tomography-10-00056-g001.jpg | CC BY 4.0 | Kohler R et al. (2024). Temporal Bone Fractures and Related Complications in Pediatric and Adult Cranio-Facial Trauma. Tomography. doi:10.3390/tomography10050056. Fig. 1 | **sí** (transversa con aire en el laberinto) |
| Fig. 3: fracturas longitudinal (A), transversa (B) y mixtas (C–D) en tres pacientes **(vista)** [PMC11111279_f3.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC11111279/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/529a/11111279/983b4e1b5ea9/EJHS3307-0979Fig3.jpg | CC BY 4.0 | Yimam EW, Nour AS, Debebe T, Endale T (2023). Imaging Patterns of Temporal Bone Fracture… Ethiop J Health Sci. doi:10.4314/ejhs.v33i6.8. Fig. 3 | sí (clasificación clásica en una lámina; calidad media) |
| Fig. 5: fractura transversa a través del segmento laberíntico del VII y de la vuelta basal de la cóclea, con sangre en el oído medio **(vista)** [PMC3676972_f5.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC3676972/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4df9/3676972/f86afff424a6/RRP2013-248039.005.jpg | CC BY 3.0 | Gupta S, Mends F, Hagiwara M, Fatterpekar G, Roehm PC (2013). Imaging the facial nerve: a contemporary review. Radiol Res Pract. doi:10.1155/2013/248039. Fig. 5 | sí (útil si el caso tiene parálisis facial) |
| Fig. 2: fractura transversa con compromiso del vestíbulo y el CAI, coronal y sagital | https://pmc.ncbi.nlm.nih.gov/articles/PMC10908707/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/3511/10908707/0fed6f9e9e82/12070_2023_4145_Fig2_HTML.jpg | CC BY 4.0 | Ostrowska M, Sisily Joseph A, Wróbel MJ (2024). Delayed Hearing Recovery After Transverse Temporal Bone Fracture with Otic Capsule violation. Indian J Otolaryngol Head Neck Surg. doi:10.1007/s12070-023-04145-x. Fig. 2 | sí (bajada, no mirada; el caso trae además audiometrías de 4 meses y de 13 años) |
| Figs. 4–5 y 10–11: luxación incudoestapedial e incudomaleolar en 2D y 3D, neumolaberinto, fractura que cruza las ventanas | https://pmc.ncbi.nlm.nih.gov/articles/PMC4877355/ | CC BY 4.0 | Maillot O et al. (2016). Post traumatic deafness: a pictorial review of CT and MRI findings. Insights Imaging. doi:10.1007/s13244-016-0490-9 | sí (no vista; buena para hipoacusia conductiva postraumática) |
| "Felsenbeinlaengsfraktur rechts 16M – CT – 001 – Annotation": fractura longitudinal derecha en axial a 0,67 y 2 mm, coronal y sagital, con puntas de flecha **(vista)** [commons_Felsenbeinlaengsfraktur_annot.jpg] | https://commons.wikimedia.org/wiki/File:Felsenbeinlaengsfraktur_rechts_16M_-_CT_-_001_-_Annotation.jpg | CC BY-SA 4.0 | Hellerhoff, Wikimedia Commons | sí (2043×1140, excelente resolución; **sin modificar**: el rótulo "0,67 mm" queda) |

---

### 6. (caps. 10 y 26) Acueducto vestibular dilatado

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 4: **control normal frente a malformaciones**, con el ancho del acueducto **en el punto medio y en el opérculo (criterios de Cincinnati)** dibujado en cada caso y la reconstrucción 3D del acueducto **(vista)** [PMC10066110_f4.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC10066110/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/fe9c/10066110/fbf9e255bb2c/405_2022_7681_Fig4_HTML.jpg | CC BY 4.0 | Weiss NM et al. (2023). Volumetry improves the assessment of the vestibular aqueduct size in inner ear malformation. Eur Arch Otorhinolaryngol. doi:10.1007/s00405-022-07681-4. Fig. 4 | **sí** (la mejor: criterio visible y control normal al lado) |
| Fig. 1: cómo se mide: "midpoint width" y "opercular width" rotulados en un DAV, segmentación y 3D **(vista)** [PMC10066110_f1.jpg] | misma página · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/fe9c/10066110/1e6006dbb4b5/405_2022_7681_Fig1_HTML.jpg | CC BY 4.0 | Weiss NM et al. (2023). Fig. 1 | **sí** (didáctica para explicar Cincinnati) |
| Fig. 7: axial con **DAV bilateral** (flechas), limpio **(vista)** [PMC6383528_f07.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC6383528/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/8831/6383528/a5da4fb21ba7/rb-52-01-0054-g07.jpg | CC BY | Salata TM et al. (2019). Radiol Bras. doi:10.1590/0100-3984.2016.0213. Fig. 7 | sí (simple y claro) |
| Fig. 8: **TC (A) y RM T2 (B)** del mismo niño con DAV bilateral y saco endolinfático grande **(vista)** [PMC10008926_f8.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC10008926/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/33b7/10008926/b0b57c38803b/fped-11-1027045-g008.jpg | CC BY 4.0 | Brotto D et al. (2023). Vestibular anomalies and dysfunctions in children with inner ear malformations: A narrative review. Front Pediatr. doi:10.3389/fped.2023.1027045. Fig. 8 | sí (TC y RM juntas; contraste bajo) |
| Figs. 11–12: DAV bilateral en axial y medición en reconstrucción coronal (>1,5 mm) | https://pmc.ncbi.nlm.nih.gov/articles/PMC8520521/ | CC BY 4.0 | Feraco P et al. (2021). Radiol Med. Figs. 11–12 | sí (no vista) |

No se encontró una figura abierta con el criterio de **Valvassori** (>1,5 mm en el punto medio) dibujado como tal. Cincinnati (punto medio >0,9 mm u opérculo >1,9 mm) está en PMC10066110. Si se quiere Valvassori, se puede rotular PMC10066110 Fig. 1, que es CC BY.

---

### 7. (cap. 26) Dehiscencia del canal semicircular superior (Pöschl y Stenvers)

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 2: dehiscencia del CSS derecho en coronal, **Stenvers** (B) y **Pöschl** (C), frente al **Pöschl izquierdo normal con techo óseo grueso** (D), más CISS en Pöschl de ambos lados (E–F) **(vista)** [PMC12178317_f2.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC12178317/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/86e2/12178317/42fe4250e1f8/cureus-0017-00000084477-i02.jpg | CC BY 4.0 | Reddy Y M, Pandey AK (2025). A Rare Case of Co-existent Superior Semicircular Dehiscence and Sigmoid Sinus Plate Dehiscence… Cureus. doi:10.7759/cureus.84477. Fig. 2 | **sí** (la mejor: dehiscente y normal en la misma lámina, TC y RM) |
| Fig. 1: axial con los **planos de Pöschl (línea continua) y Stenvers (punteada)** dibujados, más Pöschl y Stenvers de un CSS dehiscente **(vista)** [PMC7385271_f1.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC7385271/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/79b3/7385271/fbd38042ce9e/fneur-11-00695-g0001.jpg | CC BY | Noij KS, Rauch SD (2020). VEMP Testing for Diagnosis of Superior Semicircular Canal Dehiscence. Front Neurol. doi:10.3389/fneur.2020.00695. Fig. 1 | **sí** (enseña de dónde salen los planos) |
| Fig. 12: "**casi dehiscencia**": Stenvers con hueso fino y Pöschl con eminencia arcuata intacta, más audiograma, reflejos y umbrales de cVEMP **(vista)** [PMC8055857_f12.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC8055857/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4055/8055857/d392806a75b3/fneur-12-638574-g0012.jpg | CC BY | Eberhard KE et al. (2021). Current Trends… Superior Canal Dehiscence Syndrome. Front Neurol. doi:10.3389/fneur.2021.638574. Fig. 12 | sí (canal "cubierto" para contrastar; la Fig. 6 del mismo artículo queda **excluida**: "Adapted with permission from Wolters Kluwer") |
| Fig. 3: caso completo: oVEMP aumentado, cVEMP con umbral bajo, TC en Stenvers y Pöschl, y fotos de la cirugía por fosa media **(vista)** [PMC5408023_f3.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC5408023/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/ee90/5408023/72b86bee8e6c/fneur-08-00177-g003.jpg | CC BY 4.0 | Ward BK, Carey JP, Minor LB (2017). Superior Canal Dehiscence Syndrome: Lessons from the First 20 Years. Front Neurol. doi:10.3389/fneur.2017.00177. Fig. 3 | sí (VEMP más TC en una lámina; hay que recortar los paneles C–D) |
| Coronal de temporal izquierdo con dehiscencia antero-superior de 1 mm (flecha roja) **(vista)** [commons_SSCD_CT_f0.jpg] | https://commons.wikimedia.org/wiki/File:Superior_semicircular_canal_dehiscence_syndrome_-_CT_scan.gif | CC BY 4.0 | Han-Kuang Chen, Wikimedia Commons | sí (coronal simple, 589×425) |

---

### 8. (caps. 13 y 17) Nervio coclear, malformaciones del oído interno y CMV congénito

#### 8a. Aplasia o hipoplasia del nervio coclear

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 4: sagital oblicuo **normal (4 nervios rotulados) frente a aplasia del coclear (solo facial y vestibulares)** en el mismo lactante **(vista)** [PMC9324637_f4.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC9324637/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/df46/9324637/9e9a9f5d79e7/jcm-11-03966-g004.jpg | CC BY 4.0 | Johansson M et al. (2022). J Clin Med. doi:10.3390/jcm11143966. Fig. 4 | **sí** (la mejor) |
| Fig. 3: RM axial del CAI: **aplasia** (A), **hipoplasia** (B) y **nervio coclear normal** (C) **(vista)** [PMC12559043_f3.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC12559043/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/df25/12559043/e76eabc4f020/330_2025_11663_Fig3_HTML.jpg | CC BY 4.0 | Young YMC et al. (2025). Imaging of inner ear malformation in paediatric patients – a 10-year tertiary centre review. Eur Radiol. doi:10.1007/s00330-025-11663-5. Fig. 3 | **sí** (la serie de 3 grados en axial; la Fig. 4 hace lo mismo con el VIII completo) |
| Fig. 9 A–D: deficiencia del nervio coclear en 3D-FIESTA axial y **sagital oblicuo** (coclear casi invisible en el cuadrante antero-inferior) **(vista)** [PMC2765183_f9.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC2765183/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7d0e/2765183/eefd38d6f693/IJRI-19-99-g009.jpg | CC BY | Gupta SS et al. (2009). Indian J Radiol Imaging. doi:10.4103/0971-3026.50825. Fig. 9 | sí |
| Fig. 6: sagital oblicuo con 3 nervios frente a 4 [PMC12813948_f6.jpg] **(vista)** | ver sección 1b | CC BY 4.0 | Pinto Alberto K et al. (2025). Cureus. Fig. 6 | sí (alternativa) |
| Fig. 1: aplasia del coclear en sagital oblicuo (A) y ausencia del canal óseo del nervio coclear en TC (B) | https://pmc.ncbi.nlm.nih.gov/articles/PMC9607978/ | CC BY 4.0 | Choe G, Kim YS, Oh SH, Lee SY, Lee JH (2022). Functional Outcomes of Cochlear Implantation in Children with Bilateral Cochlear Nerve Aplasia. Medicina. doi:10.3390/medicina58101474. Fig. 1 | sí (no vista; une RM y TC) |

#### 8b. Malformaciones del oído interno (PI-II/Mondini, cavidad común)

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 9: **esquemas de PI-I, PI-II y PI-III** con su TC axial debajo **(vista)** [PMC8520521_f9.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC8520521/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4d53/8520521/956153521134/11547_2021_1387_Fig9_HTML.jpg | CC BY 4.0 | Feraco P et al. (2021). Radiol Med. doi:10.1007/s11547-021-01387-z. Fig. 9 | **sí** (dibujo y TC juntos; combina con la Fig. 3 normal del mismo artículo) |
| Fig. 7: **PI-II (Mondini)**: fusión de las vueltas media y apical, vestíbulo prominente y acueducto vestibular dilatado en TC, más 3D-FIESTA con saco dilatado y modiolo atenuado **(vista)** [PMC2765183_f7.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC2765183/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7d0e/2765183/ff657ff87050/IJRI-19-99-g007.jpg | CC BY | Gupta SS et al. (2009). Fig. 7 | **sí** |
| Fig. 5: **cavidad común** en TC axial **(vista)** [PMC2765183_f5.jpg] | misma página · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7d0e/2765183/58ff35ad794d/IJRI-19-99-g005.jpg | CC BY | Gupta SS et al. (2009). Fig. 5 | **sí** |
| Fig. 6: cavidad común en esquema y en un niño de 2 años | https://pmc.ncbi.nlm.nih.gov/articles/PMC8520521/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4d53/8520521/6547799fb6bd/11547_2021_1387_Fig6_HTML.jpg | CC BY 4.0 | Feraco P et al. (2021). Fig. 6 | sí (bajada, no mirada) |
| Figs. 3–4 y 6, 10: Michel, aplasia coclear, PI-I, cóclea aislada (barra ósea en la apertura coclear) | https://pmc.ncbi.nlm.nih.gov/articles/PMC2765183/ | CC BY | Gupta SS et al. (2009) | sí (resto del espectro, no vistas) |

#### 8c. CMV congénito

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 7: niño de 17 meses con CMV y **sordera posnatal**: **quistes temporales mesiales** y **alteración de la sustancia blanca periventricular** en FLAIR y T2 **(vista)** [PMC9406729_f7.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC9406729/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7448/9406729/d79b852e9235/children-09-01210-g007.jpg | CC BY 4.0 | Lucignani G et al. (2022). From Fetal to Neonatal Neuroimaging in TORCH Infections: A Pictorial Review. Children. doi:10.3390/children9081210. Fig. 7 | **sí** (justo el fenotipo de sordera con RM típica) |
| Fig. 4: ecografía (A), RM T2* (B) y **TC con calcificaciones periventriculares** múltiples y bilaterales (C) **(vista)** [PMC9406729_f4.jpg] | misma página · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7448/9406729/720c909ffe7e/children-09-01210-g004.jpg | CC BY 4.0 | Lucignani G et al. (2022). Fig. 4 | **sí** (el panel C es la calcificación de libro) |
| Fig. 5: TC de recién nacido con calcificaciones periventriculares y ventriculomegalia moderada **(vista)** [PMC10816506_f5.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC10816506/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/b9e1/10816506/129a4efe2f31/jcm-13-00640-g005.jpg | CC BY 4.0 | Pontes KFM et al. (2024). Cytomegalovirus and Pregnancy: A Narrative Review. J Clin Med. doi:10.3390/jcm13020640. Fig. 5 | sí (calcificaciones más sutiles) |
| Fig. 1: RM de CMV congénito "asintomático" (cuerpo calloso fino, polimicrogiria, sustancia blanca) | https://pmc.ncbi.nlm.nih.gov/articles/PMC12875864/ | CC BY | Swanson MR, Haisley LD, Dobyns WB, Schleiss MR (2025). Beyond hearing loss: exploring neurological and neurodevelopmental sequelae in asymptomatic congenital cytomegalovirus infection. Pediatr Res. doi:10.1038/s41390-025-04232-5. Fig. 1 | sí (no vista) |

---

### 9. (cap. 29) Implante coclear e implante de conducción ósea

#### 9a. Implante coclear

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Figs. 3 y 7: **radiografía transorbitaria AP** y **oblicua lateral a 45°** con el **espiral del electrodo** en la cóclea y el receptor-estimulador; las Figs. 1–2 y 5–6 muestran la posición del paciente **(vista)** [PMC9443830_f3.jpg, _f7.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC9443830/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/5551/9443830/62f753bf0e00/gr3.jpg · https://cdn.ncbi.nlm.nih.gov/pmc/blobs/5551/9443830/09a0e72cca0e/gr7.jpg | CC BY 4.0 | Molezini FD, Meira SG, Neto DL, Filho OA (2012). Cochlear implant radiography: technique adapted into a portable apparatus. Braz J Otorhinolaryngol. doi:10.1590/S1808-86942012000100005. Figs. 3 y 7 | **sí** (la mejor: la espiral se ve nítida; trae la marca "RBORL") |
| Fig. 2: **proyección de Stenvers modificada** (esquema de la rotación de 30° y la angulación de 10°, más la radiografía); Fig. 3: medición del **ángulo de inserción** en Stenvers, con esquema rotulado (E1–E12, modiolo, ventana redonda, CSS, vestíbulo) **(vista)** [PMC13327508_f2.jpg, _f3.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC13327508/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7d00/13327508/ed47acf0e83c/OHN-175-214-g003.jpg (Fig. 2) · https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7d00/13327508/70aad99ab770/OHN-175-214-g004.jpg (Fig. 3) | CC BY 4.0 | Rader T, Bühler H, Fabritius MP, Canis M, Spiegel JL (2026). Angular Insertion Depth for Cochlear Implantation: CT, MRI, and x-Ray. Otolaryngol Head Neck Surg. doi:10.1002/ohn.70248. Figs. 2–3 | **sí** (didácticas. Ojo: Fig. 2 = `g003` y Fig. 3 = `g004`) |
| TC axial de **implante coclear bilateral** (MIP) y reconstrucción con el electrodo dentro de la cóclea **(vista)** [commons_Cochleaimplantat_CT.jpg] | https://commons.wikimedia.org/wiki/File:Cochleaimplantat_beidseits_74M_-_CT_axial_-_001.jpg | CC BY-SA 4.0 | Hellerhoff, Wikimedia Commons | sí (1568×1066; **sin modificar**) |
| Fig. 7: TC de haz cónico del electrodo en las vueltas basal y media, más MIP 3D en oblicuo coronal | https://pmc.ncbi.nlm.nih.gov/articles/PMC12302556/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/fed5/12302556/2b0444f1a484/ADVS-12-e00556-g012.jpg | CC BY 4.0 | Batts S et al. (2025). Adv Sci. Fig. 7 (archivo `g012`) | sí (bajada, no mirada) |
| Fig. 3: radiografías AP y lateral de cráneo con el implante **(vista)** [PMC13367767_f3.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC13367767/ | CC BY 4.0 | Özdemir O, Kaygisiz I, Baran E, Celik R (2026). Cochlear Implantation Following Neurobrucellosis-Related Bilateral Profound SNHL. Cureus. doi:10.7759/cureus.110831. Fig. 3 | dudoso (la espiral casi no se distingue) |

#### 9b. Implante de conducción ósea

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 3: **Bonebridge** en TC de haz cónico y en TC convencional (dos cráneos de cadáver), con su relación con la fosa posterior **(vista)** [PMC3844407_f3.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC3844407/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/ddf2/3844407/bdf7abb3d49b/2047-783X-18-30-3.jpg | CC BY 2.0 | Güldner C et al. (2013). Visualisation of the Bonebridge by means of CT and CBCT. Eur J Med Res. doi:10.1186/2047-783X-18-30. Fig. 3 (la Fig. 2 trae el 3D del implante; la Fig. 4, el seno sigmoides) | **sí** (transductor transcutáneo activo bien visible) |
| Fig. 2: TC axial con el **tornillo de un BAHA** derecho (osteointegrado, percutáneo) **(vista)** [PMC9420306_f2.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC9420306/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/b69a/9420306/591f42d14111/cureus-0014-00000027436-i02.jpg | CC BY | Mock JA, Patel J, Gadre A, Greene S (2022). A Potential Interaction Between Bisphosphonates and Osseointegration of BAHA Implants… Cureus. doi:10.7759/cureus.27436. Fig. 2 | sí (TC de cráneo; el implante es chico en la imagen) |
| Fig. 5: TC posoperatoria de **Bonebridge (BB-FMT)** y **Osia (O-OSI)** sobre la planificación, en cadáver **(vista)** [PMC10156678_f5.jpg] | https://pmc.ncbi.nlm.nih.gov/articles/PMC10156678/ | CC BY 4.0 | Lui JT et al. (2023). Using augmented reality to guide bone conduction device implantation. Sci Rep. doi:10.1038/s41598-023-33523-2. Fig. 5 | dudoso (render de navegación, poco clínico) |
| Fig. 6: fotos de los dispositivos quirúrgicos de conducción ósea (BAHA con pilar, Ponto, Attract, Bonebridge, Osia) | https://pmc.ncbi.nlm.nih.gov/articles/PMC9831057/ | CC BY 4.0 | Truong MT et al. (2022). Front Surg. Fig. 6 | sí, como complemento (no es imagenología) |

---

### Descartadas por licencia o por material de terceros

**ND (CC BY-NC-ND o CC BY-ND):**
- Otoesclerosis: PMC12180549 (Acta ORL Ital), PMC8096512 (Int Arch ORL, revisión de imagen), PMC9349010 (J Otol, densidad de la fissula), PMC8267294 (Ann Transl Med), PMC11914994 (Braz J ORL), PMC13566390 (Otol Neurotol).
- Dehiscencia: PMC12716349 (Sultan Qaboos, CC BY-ND), PMC10773621 (Am J Case Rep, dehiscencia del CSS y del tegmen en un buzo).
- Malformaciones y nervio: PMC12554901 (Radiol Case Rep, laberintitis osificante que imita malformación), PMC12945661 (J Otol, formas de transición), PMC8448219 (IJRI), PMC6002563 (J Otol), PMC13217823 (Radiol Case Rep, PI-III), PMC13374130 (J Med Case Rep, Mondini), PMC13162032 (J Otol), PMC10097487 (Ear Hear), PMC11400648 (QIMS), PMC8518068 (Laryngoscope, quistes aracnoideos del CAI), PMC5963467 (J Otol), PMC12150163 (LIO).
- Anatomía y técnica: PMC4603126 (Medicine, CC BY-ND), PMC9764738 (LIO), PMC7801246 (WJORL), PMC12647951 (J Otol).
- Trauma: PMC12221757 y PMC8829517 (Radiol Case Rep), PMC11980961 y PMC12371857 (Laryngoscope).
- Colesteatoma: PMC12243516 y PMC12687318 (Pol J Radiol), PMC10723951 y PMC10723965 (IJRI), PMC10278117 (LIO), PMC12671230 (MRMS), PMC11063661 (JLO).
- Implante coclear: PMC12244962 (Otol Neurotol), PMC9958279 (Heliyon), PMC6734201 (Acta ORL Ital), PMC7575389 (Int Arch ORL).
- CMV: PMC13340454 (Pediatr Infect Dis J).
- Paget: PMC12796714, PMC9624800, PMC9107974, PMC9514261.

**Figuras de terceros dentro de artículos abiertos (excluidas aunque el artículo sea CC BY):**
- PMC8055857 Fig. 6 (clasificación de la dehiscencia del Mass Eye and Ear): "Adapted with permission from Wolters Kluwer".
- PMC10925929 Fig. 2 (clasificación de la dehiscencia según su ubicación): "Obtained with permission from Lookabaugh et al."
- PMC13207999 Fig. 3 (rasgos del CMV en RM): reproducida de la referencia [13]. Lo mismo la Fig. 2 (ecografía, de la ref. [10]).
- PMC12672709 Fig. 1 (esquema de terceras ventanas): "© Dr. med. Hergen Friedrich, all rights reserved". La Fig. 4 del mismo artículo viene de Rösch et al., CC BY 4.0, y se puede usar con esa atribución.
- PMC7118860 y PMC7119142: "Reprinted with permission… AMA".

---

### No encontrado

1. **TC normal de temporal en coronal ya rotulada** con todas las estructuras del ático y la mastoides en una sola lámina abierta. Hay axial rotulada (PMC8520521 Fig. 3) y coronales normales sin rótulos (PMC11913933 Fig. 1A, PMC6775179 Fig. 9a). Alternativas: rotular PMC11913933 Fig. 1A (CC BY) o usar Radiopaedia rID 63095 (CC BY-NC-SA 3.0, compatible pero sin ver).
2. **Criterio de Valvassori dibujado** sobre un DAV. Solo aparece Cincinnati (PMC10066110). Alternativa: rotular PMC10066110 Fig. 1 con la medida de Valvassori.
3. **Radiografía transorbitaria de implante de conducción ósea** (BAHA u Osia en placa simple). Solo hay TC o TC de haz cónico, la mayoría en cadáver (PMC3844407, PMC10156678) y una TC clínica de BAHA (PMC9420306). Alternativa: Radiopaedia ("bone-anchored hearing aid", "Bonebridge"; buscar el rID a mano) o una placa propia.
4. **Paget del temporal en TC de alta resolución dedicada al oído** (corte fino con cápsula ótica y cadena). Lo abierto es TC de base de cráneo (PMC10366931) y un coronal con desmineralización pericoclear (PMC6383528). Alternativa: Radiopaedia, buscando "Paget disease temporal bone".
5. **Fotos clínicas de Radiopaedia**: no se pudieron bajar ni mirar (desafío anti-bot), así que ningún caso de Radiopaedia está **(vista)**. Si el autor prefiere Radiopaedia para B1, conviene abrir los rID 63095, 63096 y 32484 en el navegador y capturar.
6. **Datasets**: no se buscaron en esta parte (le tocan a otro agente). Ninguna de las necesidades 1–9 parece requerir uno: todas tienen al menos una figura abierta y vista.

---

# Parte III. Retrococlear, central, hidrops y senos

Búsqueda hecha el 2026-10-17. Destino: libro gratuito CC BY-NC-SA 4.0. Mismo método que `docs/libro/investigacion/imagenes.md`.

**Cómo se verificó.** Las candidatas salieron de Open-i (https://openi.nlm.nih.gov), de Wikimedia Commons y de búsquedas en Europe PMC. En los artículos de PMC, la licencia se leyó del campo `license` de Europe PMC y del bloque `<license>` del XML completo. Si no coincidían, mandó el XML. En Commons, la licencia y el autor salieron de la API (`extmetadata`: LicenseShortName/Artist). En los pies de figura se buscó "permission / reproduced / adapted / reprinted / courtesy". Solo apareció en figuras que no se proponen (figs. 6–7 de PMC10380265). Las imágenes marcadas **(vista)** se bajaron a (carpeta temporal de la búsqueda, ya borrada) y se miraron. No se bajó nada al repo. Cuando hay URL `cdn.ncbi.nlm.nih.gov/pmc/blobs/...`, esa es la figura en alta resolución de PMC. Las de Open-i (`openi.nlm.nih.gov/imgs/512/...`) son de 512 px.

**Recordatorio de licencias:** CC0, PD, CC BY y CC BY-NC se pueden usar y modificar (con atribución). CC BY-NC-SA es la misma licencia del libro. CC BY-SA va **sin modificar**: sin recorte, sin rótulos y sin traducción. Ninguna figura ND sirve.

Formato de atribución: *Autores (año). Título. Revista. doi. Fig. N. Licencia.*

---

### 1. Schwannoma vestibular y diferenciales del ángulo (caps. 11, 20, 27)

#### 1.a Schwannoma: intracanalicular pequeño, grande en el APC, T2 de alta resolución

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| **Escala de Koos I–IV**: cada grado en T1 con gadolinio (ceT1) y T2 de alta resolución (hrT2), en pares, con flechas rojas. El grado I es intracanalicular y el IV es grande y comprime el tronco **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC10365083/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/da85/10365083/df696d5ae001/fradi-02-837191-g0001.jpg (680×850) | CC BY 4.0 | Kujawa A, Dorent R, Connor S, et al., Shapey J (2022). Automated Koos Classification of Vestibular Schwannoma. Front Radiol. doi:10.3389/fradi.2022.837191. Fig. 1 | **sí, la mejor**: en una sola figura están el intracanalicular, el grande y el par T1+gd / T2 de alta resolución. Se puede recortar por fila. Las imágenes vienen del dataset abierto Vestibular-Schwannoma-SEG (TCIA, CC BY 4.0) |
| Schwannoma intracanalicular muy pequeño en **FIESTA** axial: defecto de llenado en el CAI derecho, con el CAI izquierdo normal al lado **(vista)**. La Fig. 3 es la misma lesión en T1+gd con supresión grasa | https://pmc.ncbi.nlm.nih.gov/articles/PMC8929235/ · img Fig. 2: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7eb6/8929235/4d534ec6bec9/cureus-0014-00000022231-i02.jpg · Fig. 3: …/26b91adcb882/cureus-0014-00000022231-i03.jpg | CC BY 4.0 | Aktan SL, Finucane S, Kircher M, Moore D, Bashir M (2022). The Natural History of Small Vestibular Schwannomas. Cureus. doi:10.7759/cureus.22231. Figs. 2–3 | **sí** (franja angosta de los dos CAI; el T1+gd es oscuro) |
| Schwannoma intracanalicular derecho en **3D-SPACE** (T2 de alta resolución), flecha **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC12582803/ · img: https://openi.nlm.nih.gov/imgs/512/225/12582803/PMC12582803_medi-104-e45671-g002.png | CC BY 4.0 | Chen X, Chen S, Lei P, et al., Liu B (2025). Vestibular schwannoma presenting as vestibular neuritis-like attack… Medicine (Baltimore). doi:10.1097/md.0000000000045671. Fig. 2 | **sí**. El caso calza con el cap. 20/27: debutó como una "neuritis", con vHIT alterado en la Fig. 1 |
| Schwannoma intracanalicular **muy pequeño** en T1+gd axial (flecha amarilla) **(vista)** | https://commons.wikimedia.org/wiki/File:Vestibularis-Schwannom.jpg | Dominio público | MBq (de.wikipedia) | **sí** (618×470; trae texto de consola en los bordes) |
| Schwannoma intrameatal izquierdo en T1+gd, contorneado en rojo **(vista)** | https://commons.wikimedia.org/wiki/File:Akustikus-Schwannon_links_intrameatal_MRT_T1KM_axial_-_Annotation.jpg | CC BY-SA 3.0 | Hellerhoff | **sí, sin modificar** (BY-SA) |
| Schwannoma del APC derecho, sólido, de ~2 cm, en T1+gd axial **(vista)**. La serie trae coronal T1+gd y T2 axial | https://commons.wikimedia.org/wiki/File:Akustikus-Schwannon_rechts_MRT_T1KM_axial_001.jpg (también …_T1KM_coronar_001.jpg y …_T2_axial_001.jpg) | CC BY-SA 3.0 | Hellerhoff | **sí, sin modificar** (BY-SA). Imagen limpia y grande |
| Schwannoma **grande quístico** del APC derecho con compresión severa del tronco, en T1+gd (a) y T2 (b) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC9609800/ · img: https://openi.nlm.nih.gov/imgs/512/236/9609800/PMC9609800_SNI-13-441-g001.png | CC BY-NC-SA 4.0 | Ravindran PK, Kunst D, Waterval J, Hovinga K, Temel Y (2022). A rare complication after vestibular schwannoma surgery: Neurogenic pulmonary edema. Surg Neurol Int. doi:10.25259/sni_277_2022. Fig. 1 | sí (es quístico, no el sólido típico) |
| Schwannoma del APC izquierdo con realce periférico, en T1+gd **(vista)** | https://commons.wikimedia.org/wiki/File:Acoustic_schwannoma.jpg | CC BY 2.0 | Collins SP, Coppa ND, Zhang Y, et al. (2006). Radiat Oncol 1:46. doi:10.1186/1748-717X-1-46 (vía Commons) | dudoso (foto de placa, borrosa) |
| Schwannoma de 2 cm en T1+gd, con un círculo rojo **(vista)** | https://commons.wikimedia.org/wiki/File:Mri1BrughoekTumor2cm.jpg | Dominio público | Slingerjansen | no (foto de placa con tinte lila; hay mejores) |

#### 1.b Diferenciales del ángulo pontocerebeloso

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| **Quiste epidermoide** del APC derecho: T2 hiperintenso (A), T1+gd **sin realce** (B), **DWI muy brillante** (C) y la histología (D) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC3467374/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/8153/3467374/f17705bb782b/jkns-52-148-g001.jpg | CC BY-NC 3.0 | Chon KH, Lee JM, Koh EJ, Choi HY (2012). Malignant transformation of an epidermoid cyst in the cerebellopontine angle. J Korean Neurosurg Soc. doi:10.3340/jkns.2012.52.2.148. Fig. 1 | **sí, la mejor** (la Fig. 1 es el epidermoide inicial, antes de la transformación; recortar D) |
| Epidermoide del APC izquierdo: T1, T2, FLAIR, ADC y **DWI** (e) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC7591210/ · img: https://openi.nlm.nih.gov/imgs/512/280/7591210/PMC7591210_AJNS-15-573-g002.png | CC BY-NC-SA 4.0 | Singh R, Prasad RS, Singh A (2020). Evaluation of Cerebellopontine Angle Epidermoid Presenting with Cranial Nerve Deficit. Asian J Neurosurg. doi:10.4103/ajns.ajns_226_20. Fig. 2 | sí (calidad media) |
| Epidermoide del APC derecho en T2 | https://commons.wikimedia.org/wiki/File:Epidermoid_cyst_cerebellopontine_angle.jpg (de PMC3094668) | CC BY 4.0 (Commons) / CC BY (artículo) | Jiménez Caballero PE, Portilla Cuenca JC, Casado Naranjo I (2011). J Headache Pain. doi:10.1007/s10194-011-0326-4. Fig. 1 | sí, como extra (solo T2, sin difusión; no se miró) |
| **Meningioma del APC** derecho en T1+gd axial y coronal, en CISS y en TC, **junto al audiograma** (hipoacusia derecha) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC10246372/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/5256/10246372/dca32db815dd/SNI-14-174-g001.jpg | CC BY-NC-SA 4.0 | Francis CC, Kanaya K, Murase H, Hardian RF, Horiuchi T, Ohaegbulam SC (2023). Unexpected recovery from complete deafness to normal hearing post surgical excision of a cerebellopontine angle meningioma. Surg Neurol Int. doi:10.25259/sni_276_2023. Fig. 1 | **sí, la mejor** (trae el audiograma) |
| Meningioma del APC izquierdo con **cola dural**, compresión del tronco y extensión al CAI (flechas), en coronal y axial T1+gd **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC10977935/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/62f3/10977935/c769e0b0993c/cureus-0016-00000055075-i01.jpg | CC BY 4.0 | Van Havenbergh F, Schepens J, Torfs M, Van Havenbergh T (2024). Rare but Real: Severe Unilateral Macroglossia… After Skull Base Surgery. Cureus. doi:10.7759/cureus.55075. Fig. 1 | **sí** (muestra la cola dural, el rasgo que lo separa del schwannoma) |
| Meningioma incidental de fosa posterior: T2 con hendidura de LCR, T1 y T1+gd | https://pmc.ncbi.nlm.nih.gov/articles/PMC12621765/ · img: https://openi.nlm.nih.gov/imgs/512/290/12621765/PMC12621765_btrt-13-153-g001.png | CC BY-NC 4.0 | Kim MS, Park SH, Seo Y (2025). Spontaneous Regression of Incidental Meningioma in the Posterior Cranial Fossa. Brain Tumor Res Treat. doi:10.14791/btrt.2025.0012. Fig. 1 | sí, de reserva (no se miró) |
| **Asa de la AICA**, clasificación de Chavda tipos I–III en T2 de alta resolución, con flechas blancas **(vista)**. La Fig. 2 es la clasificación de Gorrie (relación con el nervio) | https://pmc.ncbi.nlm.nih.gov/articles/PMC6417406/ · img Fig. 1: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/43eb/6417406/3f6ee845c1e1/peerj-07-6582-g001.jpg · Fig. 2: …/73b973620dde/peerj-07-6582-g002.jpg | CC BY 4.0 | Kim SH, Ju YR, Choi JE, Jung JY, Kim SY, Lee MY (2019). Anatomical location of AICA loop in CPA as a prognostic factor for ISSNHL. PeerJ. doi:10.7717/peerj.6582. Figs. 1–2 | **sí** (paneles chicos, 697×233; sirven como esquema de grados) |
| Asa de la AICA contra el VIII par, sin compresión, en T2 axial (flecha) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC10472322/ · img: https://openi.nlm.nih.gov/imgs/512/207/10472322/PMC10472322_cureus-0015-00000042838-i03.png | CC BY 3.0 | O'Brien CA, Gupta N, Kasula V, Lamb M, Alexander R (2023). Vascular Loop of the AICA as a Cause of SNHL: A Case Report. Cureus. doi:10.7759/cureus.42838. Fig. 3 | sí (caso clínico con hipoacusia; la imagen es oscura) |
| Asa de la AICA, Chavda II y III, en 3D-CISS **(vista i05)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC11214648/ | CC BY 4.0 | G N, H S, Sajjan SS, et al. (2024). Prevalence of AICA Vascular Loop in CPA With 3D-CISS. Cureus. doi:10.7759/cureus.61393. Figs. 4–5 | dudoso (borrosa y sin flecha visible) |

---

### 2. Hidrops endolinfático en RM con gadolinio tardío (caps. 9 y 23)

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| **HYDROPS (substracción)**: oído derecho con Ménière, con hidrops coclear grado II y sacular/utricular grado III (C, S y U en negro), **frente al oído izquierdo de control** (perilinfa blanca, flechas punteadas) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC11098000/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7033/11098000/43b73b2b8631/10.1177_19160216241250350-fig2.jpg | CC BY-NC 4.0 | Young YH, Lin KT (2024). Potential Application of Hydrops MR Imaging: A Systematic Review. J Otolaryngol Head Neck Surg. doi:10.1177/19160216241250350. Fig. 2 | **sí, la mejor**: es justo la comparación hidrops/normal que se pidió, con rótulos C/S/U |
| 3D-FLAIR a las 4 h de gadolinio IV: grado 0 / I / II, cada uno **con su esquema dibujado al lado** (sáculo, utrículo, cóclea, CAI y acueducto; hidrops en rojo) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC9909016/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/85c2/9909016/b84b7d83bcac/fneur-14-1105461-g0002.jpg | CC BY 4.0 | Diorflar S, Guigou C, Daguet E, Bensimon JL, Toupet M, Bozorg-Grayeli A (2023). Confrontation of endolymphatic hydrops diagnosis on 3-Tesla MRI to clinical and audiovestibular findings in Meniere's disease. Front Neurol. doi:10.3389/fneur.2023.1105461. Fig. 2 (la Fig. 3 muestra la inversión sáculo/utrículo, SURI) | **sí** (muy didáctica por el esquema) |
| "Contralateral normal ear" frente a "cochlear and vestibular hydrops", en T2-FLAIR poscontraste y en substracción, a 3 T **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC8242163/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/8727/8242163/844a1b03224f/fsurg-08-680260-g0002.jpg | CC BY 4.0 | Alonso JE, Ishiyama GP, Fujiwara RJT, Pham N, Ledbetter L, Ishiyama A (2021). Cochlear Meniere's: A Distinct Clinical Entity With Isolated Cochlear Hydrops on High-Resolution MRI? Front Surg. doi:10.3389/fsurg.2021.680260. Fig. 2 | sí (comparación lado a lado, en 4 pares, ya rotulada; imagen pequeña) |
| Cisternografía T2 (a), hT2w-FLAIR PEI (b), substracción (c) y segmentación de sáculo y utrículo (d) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC4358992/ · img: https://openi.nlm.nih.gov/imgs/512/122/4358992/PMC4358992_pone.0120357.g001.png | CC BY 4.0 | Homann G, Vieth V, Weiss D, et al. (2015). Semi-quantitative vs. volumetric determination of endolymphatic space in Menière's disease… PLoS One. doi:10.1371/journal.pone.0120357. Fig. 1 | sí (muestra la técnica paso a paso) |
| Hidrops unilateral (derecho) frente a bilateral, en RM con contraste | https://pmc.ncbi.nlm.nih.gov/articles/PMC10809283/ · img: https://openi.nlm.nih.gov/imgs/512/328/10809283/PMC10809283_fneur-14-1348177-g003.png | CC BY 4.0 | Ueno Y, Imai T, Higashi-Shingai K, et al. (2023). Stratification of patients with Menière's disease… Front Neurol. doi:10.3389/fneur.2023.1348177. Fig. 3 | sí, de reserva (no se miró) |
| Grados 0/1/2 de hidrops en HYDROPS **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC9361122/ | CC BY 4.0 | Han SC, Kim YS, Kim Y, et al. (2022). Front Neurol. doi:10.3389/fneur.2022.937703. Fig. 1 | no (512×118, gris y sin contraste visible) |

---

### 3. Infarto de la AICA y placa de esclerosis múltiple en el tronco (cap. 12)

#### 3.a Infarto de la AICA (pontino lateral / pedúnculo cerebeloso medio) en difusión

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Caso representativo de **infarto de la AICA**: vHIT con ganancia baja en los dos lados (A), **audiometría con hipoacusia** (B) y DWI con infarto en el pedúnculo cerebeloso medio y el cerebelo (C) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC11390645/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/5496/11390645/f3696309f8d7/fneur-15-1448989-g001.jpg | CC BY 4.0 | Kim SH, Kim H, Lee SU, et al., Kim JS (2024). Bilaterally positive head-impulse tests can differentiate AICA infarction from labyrinthitis. Front Neurol. doi:10.3389/fneur.2024.1448989. Fig. 1 | **sí, la mejor para el cap. 12**: imagen, audiograma y vHIT del mismo paciente |
| DWI de un infarto territorial de la AICA izquierda (a), angio-RM con la AICA ausente (b) y BPAS (c) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC8323314/ · img Fig. 2: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/0298/8323314/3baf823fa984/12883_2021_2309_Fig2_HTML.jpg (Fig. 1: pedúnculo cerebeloso medio + cerebelo; Fig. 3: protuberancia inferolateral + pedúnculo) | CC BY 4.0 | Zhang ZY, Zhou Z, Zhang HB, Jiao JS (2021). Case report: the etiology of anterior inferior cerebellar artery infarction… BMC Neurol. doi:10.1186/s12883-021-02309-2. Figs. 1–3 | **sí** |
| TC normal (A), **DWI con lesión dorsolateral pontina** (B), angio-RM con estenosis (C) y **audiograma** con hipoacusia profunda derecha (D) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC10646485/ · img: https://openi.nlm.nih.gov/imgs/512/336/10646485/PMC10646485_fneur-14-1293102-g0002.png | CC BY 4.0 | Zhong Y, Li H, Liu G, et al., Ju Y (2023). Early detection of stroke at the sudden sensorineural hearing loss stage. Front Neurol. doi:10.3389/fneur.2023.1293102. Fig. 2 | **sí**: "súbita que era un ACV", justo el mensaje del capítulo |
| Infarto del laberinto/VIII par con hipoacusia y vértigo agudos | https://pmc.ncbi.nlm.nih.gov/articles/PMC6203587/ · img: https://openi.nlm.nih.gov/imgs/512/117/6203587/PMC6203587_medi-97-e12777-g005.png | CC BY-NC 4.0 | Byun S, Lee JY, Kim BG, Hong HS (2018). Acute vertigo and sensorineural hearing loss from infarction of the vestibulocochlear nerve. Medicine. doi:10.1097/md.0000000000012777. Fig. 5 | sí, de reserva (no se miró) |

#### 3.b Placa de esclerosis múltiple en el tronco

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| EM con **hipoacusia sensorioneural** como recaída: **lesión T2 nueva en el lado derecho de la protuberancia** (a, flecha gruesa), FLAIR periventricular (b) y lesiones que realzan (c, d). La Fig. 1 es la audiometría del caso **(vista Fig. 2)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC7423083/ · img Fig. 2: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4e51/7423083/846ca61adc5b/ijo-32-249-g002.jpg · Fig. 1: …/d6af966dd539/ijo-32-249-g001.jpg | CC BY 3.0 | Naser Moghadasi A, Poursadeghfard M, Kazemi T, Hosseini S (2020). Sensory-Neural Hearing Loss as an Early Rebound Relapse after Fingolimod Cessation in Multiple Sclerosis. Iran J Otorhinolaryngol. doi:10.22038/ijorl.2020.40858.2334. Figs. 1–2 | **sí, la única útil** (742×220, en escala de grises y chica; recortar el panel a) |
| EM con lesiones FLAIR en el bulbo derecho, el cerebelo izquierdo y la cara ventral de la protuberancia | https://pmc.ncbi.nlm.nih.gov/articles/PMC11316671/ · img: https://openi.nlm.nih.gov/imgs/512/50/11316671/PMC11316671_cureus-0016-00000064358-i01.png | no verificada (Cureus suele ser CC BY) | Cureus 2024. doi en PMC11316671 | dudoso (la EM es un diagnóstico discutido en ese caso; no se miró) |

---

### 4. Infarto cerebeloso (PICA) que imita una neuritis; difusión inicial negativa (cap. 21)

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| **Difusión negativa y luego positiva**: DWI **normal** al día 1 de vértigo recurrente con hipoacusia fluctuante (A), audiograma (B) y calórica con paresia derecha de 65% (C). Tres días después, la **DWI repetida muestra el infarto** en el territorio de la AICA (D) y el audiograma empeorado (E) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC5307938/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/6410/5307938/7e714eb0a04e/jos-2016-00857f1.jpg | CC BY-NC 4.0 | Kim HA, Lee H (2017). Recent Advances in Understanding Audiovestibular Loss of a Vascular Cause. J Stroke. doi:10.5853/jos.2016.00857. Fig. 1 | **sí, la mejor para "difusión negativa → positiva"** (es AICA, no PICA; sirve para el cap. 21 y también para el 12) |
| **Difusión negativa a las 24 h** (A–B, con la sola ausencia de vacío de flujo de la vertebral derecha) y **positiva 4 días después** (C–E: infarto bulbar derecho en T2, DWI y ADC) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC2503965/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/1028/2503965/3780d3fd668d/1757-1626-1-65-1.jpg | CC BY 2.0 | Rathakrishnan R, Sharma VK, Chan BP (2008). Diffusion-negative MRI in acute ischemic stroke: a case report. Cases J. doi:10.1186/1757-1626-1-65. Fig. 1 | **sí** (circulación posterior/vertebral: muestra que la DWI precoz puede fallar) |
| **Infarto de la PICA medial** en DWI (cerebelo caudal medial izquierdo), el patrón del vértigo aislado que imita una neuritis **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC2706413/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/df08/2706413/fad27440e930/jcn-5-65-g002.jpg | **dudosa**: Europe PMC dice CC BY-NC, pero el XML solo trae "Copyright © 2009 Korean Neurological Association", sin `<license>` | Lee H (2009). Neuro-otological aspects of cerebellar stroke syndrome. J Clin Neurol. doi:10.3988/jcn.2009.5.2.65. Fig. 2 | **dudoso por licencia** (es la imagen ideal; habría que confirmar con la revista, que hoy publica CC BY-NC) |
| Síndrome bulbar lateral con infarto del territorio de la PICA izquierda: T2 axial, flechas rojas al cerebelo y amarilla al bulbo **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC11622530/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7262/11622530/fd08ba25c811/cureus-0016-00000073118-i02.jpg | CC BY 4.0 | Canut I, Farooqui B, Hickman J (2024). From Dizziness to Dysphagia: A Complex Presentation of Lateral Medullary Syndrome. Cureus. doi:10.7759/cureus.73118. Fig. 2 | **sí** (limpia, 750×775; es T2, no DWI, aunque el pie menciona la difusión) |
| DWI y ADC **normales** al ingreso con hipoperfusión de PICA/AICA en la perfusión (Fig. 1); al día 3, infartos múltiples en la circulación posterior (Fig. 2) **(vista Fig. 2)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC9762102/ | CC BY 4.0 | Kim YS, Tehrani ASS, Lee HS, Lee HS (2022). Sudden unilateral hearing loss and vertigo following isolated cerebellar hypoperfusion without infarction due to vertebral artery dissection. BMC Neurol. doi:10.1186/s12883-022-03024-2. Figs. 1–3 | sí, como extra (las lesiones tardías no caen en PICA/AICA; enseña perfusión frente a DWI) |

---

### 5. Atrofia del vermis en CANVAS, Chiari I y sagital normal (caps. 24, 25, 32)

#### 5.a CANVAS (atrofia vermiana, sagital)

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Rasgos de RM en la enfermedad RFC1: gráfico de frecuencias (A) y **sagitales T2/FLAIR/T1 con atrofia del vermis** dorsal (flechas, B–C) y casos menos marcados (D–G) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC8055326/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/baee/8055326/191f385c5a10/NEUROLOGY2020122101FF5.jpg | CC BY 4.0 | Traschütz A, Cortese A, Reich S, et al. (2021). Natural History, Phenotypic Spectrum, and Discriminative Features of Multisystemic RFC1 Disease. Neurology. doi:10.1212/wnl.0000000000011528. Fig. 5 | **sí, la mejor** (los paneles B y C, T2 sagital, son de libro) |
| **Sagital T1 de CANVAS** con rótulos: vermis anterior, fisura primaria, vermis dorsal y fisura prepiramidal (B). Parasagital con fisuras ensanchadas (A) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC8629873/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/83d1/8629873/598d8ca035fb/12311_2020_1192_Fig1_HTML.jpg | CC BY 4.0 | Dupré M, Hermann R, Froment Tilikete C (2021). Update on CANVAS. Cerebellum. doi:10.1007/s12311-020-01192-w. Fig. 1 | **sí** (el sagital T1 que se pidió, ya rotulado; un poco oscuro) |
| CANVAS: FLAIR axial y **sagital** con atrofia vermiana dorsal (flechas amarillas). La Fig. 2 es la **audiometría** del caso (hipoacusia leve en pendiente) **(vista Fig. 1)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC11924976/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/a6b0/11924976/06905cfc1de9/toj-24-0056-figure1.jpg | CC BY 4.0 | Saibaba J, Selvaraj J, Viswanathan S, Pillai V (2025). CANVAS Coexisting With JAK2-Positive Polycythemia Vera and Myelofibrosis. Ochsner J. doi:10.31486/toj.24.0056. Figs. 1–2 | **sí** |
| RFC1: T2 axial con hemisferios conservados y atrofia vermiana; **FLAIR sagital y parasagital** con atrofia limitada al vermis **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC9171309/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/f4b0/9171309/0e4365ffc940/jmd-21117f2.jpg | CC BY-NC 4.0 | Kulshreshtha D, Ganguly J, Jog M (2022). Expanding the Clinical Spectrum of RFC1 Gene Mutations. J Mov Disord. doi:10.14802/jmd.21117. Fig. 2 | sí |

#### 5.b Malformación de Chiari tipo I

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| **Chiari I** en una niña de 13 años, T2 sagital: flecha roja en las amígdalas herniadas y línea azul en el agujero magno **(vista)** | https://commons.wikimedia.org/wiki/File:Chiari-1-Malformation_13W_-_MR_T2_sagittal_-_001a.jpg (sin rótulos: …_001.jpg) | CC BY-SA 3.0 | Hellerhoff | **sí, la más clara, sin modificar** (BY-SA) |
| Chiari tipo 1 en T1 **sagital** y T2 coronal. Niña de 13 años con **mareo e inestabilidad** de 18 meses **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC10380265/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4c52/10380265/106db05c5fba/jcm-12-04626-g002.jpg | CC BY 4.0 | Sahuquillo J, Moncho D, Ferré A, López-Bermeo D, Sahuquillo-Muxi A, Poca MA (2023). A Critical Update of the Classification of Chiari and Chiari-like Malformations. J Clin Med. doi:10.3390/jcm12144626. Fig. 2 | **sí** (CC BY, se puede rotular; calza con el vértigo central. Solo las figs. 6–7 del artículo traen permisos de terceros, y no se usan) |
| Chiari I en T1 sagital, con un asterisco en las amígdalas herniadas **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC4688315/ · img: https://openi.nlm.nih.gov/imgs/512/224/4688315/PMC4688315_jkns-58-454-g001.png | CC BY-NC 3.0 | Alkoç OA, Songur A, Eser O, et al. (2015). Stereological and Morphometric Analysis of MRI Chiari Malformation Type-1. J Korean Neurosurg Soc. doi:10.3340/jkns.2015.58.5.454. Fig. 1 | sí |
| T2 sagital con descenso amigdalino **menor de 3 mm** y síntomas tipo Chiari (flecha) **(vista)** | https://commons.wikimedia.org/wiki/File:Sagittal_MRI_scan_of_brain_of_patient_with_Chiari_malformation.jpg | CC BY 2.0 | Sekula RF Jr, Jannetta PJ, Casey KF, Marchan EM, Sekula LK, McCrady CS | dudoso (no cumple el criterio de 5 mm; sirve como "zona gris" o para contrastar) |

#### 5.c Sagital normal de comparación

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| T1 mediosagital de fosa posterior con las medidas a (clivus), b (línea de McRae) y c. Las amígdalas quedan **sobre** la línea del agujero magno **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC3873353/ · img: https://openi.nlm.nih.gov/imgs/512/94/3873353/PMC3873353_jkns-54-405-g001.png | CC BY-NC 3.0 | Hwang HS, Moon JG, Kim CH, Oh SM, Song JH, Jeong JH (2013). The comparative morphometric study of the posterior cranial fossa… J Korean Neurosurg Soc. Fig. 1 | dudoso (el pie no dice si es control o paciente; la imagen se ve normal) |
| RM sagital de cabeza en la línea media | https://commons.wikimedia.org/wiki/File:MRI_brain_sagittal_section.jpg | CC BY-SA 2.0 | everyone's idle | dudoso (BY-SA, sin modificar; no se miró) |

---

### 6. Nariz y senos paranasales (caps. 35 y 36)

| Qué muestra | URL página · img | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| **Concha bullosa bilateral** en TC coronal (asteriscos), limpia y de alta resolución **(vista)** | https://commons.wikimedia.org/wiki/File:Conchabullosa.jpg | Dominio público | MBq | **sí, la mejor** (1012×974; tiene texto magenta de consola que se puede recortar) |
| TC coronal con concha bullosa bulbosa derecha (flecha) y tabique desviado a la izquierda **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC9431850/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/10d8/9431850/e9e529e724ce/jksr-81-1377-g003.jpg | CC BY-NC 4.0 | Lee J, Park SM, Cha SW, Moon JS, Kim MS (2020). Does Nasal Septal Deviation and Concha Bullosa Have Effect on Maxillary Sinus Volume and Maxillary Sinusitis? Taehan Yongsang Uihakhoe Chi. doi:10.3348/jksr.2019.0169. Fig. 3 | **sí** (cara completa, buena para ubicar) |
| CBCT coronal con concha bullosa media derecha y tabique desviado a la izquierda (flechas) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC2938434/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/5b45/2938434/66938f0b54a2/IJD2010-404982.007.jpg (Fig. 1: concha bullosa aislada; Figs. 4–6: con sinusitis maxilar) | CC BY 3.0 | Smith KD, Edwards PC, Saini TS, Norton NS (2010). The prevalence of concha bullosa and nasal septal deviation and their relationship to maxillary sinusitis by volumetric tomography. Int J Dent. doi:10.1155/2010/404982 | sí |
| TC coronal con tabique desviado, concha bullosa izquierda con mucosa engrosada y sinusitis maxilar, junto a la endoscopía del pólipo dentro de la concha **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC1471777/ · img: https://openi.nlm.nih.gov/imgs/512/107/1471777/PMC1471777_1746-160X-2-11-1.png | CC BY 2.0 | Erkan AN, Canbolat T, Ozer C, Yilmaz I, Ozluoglu LN (2006). Polyp in concha bullosa: a case report. Head Face Med. doi:10.1186/1746-160x-2-11. Fig. 1 | sí (TC y endoscopía juntas) |
| **Rinosinusitis crónica con pólipos**: TC según Lund-Mackay, de normal/leve (A) a moderada (B) y **pansinusitis con opacificación total** (C), en cortes axiales, coronales y sagitales **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC11505379/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/22e7/11505379/ab6f18ce7c22/JAA-17-1027-g0001.jpg | CC BY-NC 3.0 (términos Dove) | Al-Ahmad M, Ali A, Dawood HA, Beshreda GM (2024). Effect of Dupilumab on Radiological Remission in Patients with CRSwNP. J Asthma Allergy. doi:10.2147/jaa.s478040. Fig. 1 | **sí** (la mejor para CRSwNP; recortar los paneles C) |
| TC axial y coronal de **rinosinusitis crónica** unilateral (opacificación maxilar y etmoidal) **(vista)** | https://commons.wikimedia.org/wiki/File:CT_of_chronic_sinusitis.jpg | CC0 | Mikael Häggström, M.D. | sí (chica, 330×325, pero CC0) |
| TC coronal del **complejo osteomeatal** rotulado (apófisis unciforme, hiato semilunar, bulla etmoidal, meatos y cornetes medio e inferior) con un esquema de ubicación **(vista)** | https://commons.wikimedia.org/wiki/File:CT_of_the_ostiomeatal_complex,_coronal_plane,_with_annotations.png (sin rótulos: …_no_annotations.png) | CC BY 4.0 | Mikael Häggström, M.D. (sobre imagen de Paşaoğlu L, Toprak U, Üstüner E, et al.) | **sí** (anatomía de base para el cap. 35; trae versión sin rótulos para traducir) |
| **Válvula nasal interna en TC coronal reformateada**: ángulo y área antes (A, C) y después (B, D) de una rinoplastía **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC9422510/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7371/9422510/c59c27e17c2e/gr2.jpg | CC BY 4.0 | Shafik AG, Alkady HA, Tawfik GM, Mohamed AM, Rabie TM, Huy NT (2020). Computed tomography evaluation of internal nasal valve angle and area and its correlation with NOSE scale… Braz J Otorhinolaryngol. PMC9422510. Fig. 2 | **sí** (la única TC de válvula hallada; antes/después quirúrgico, no farmacológico) |
| Cortes de TC para medir la válvula nasal interna (coronal y axial con la línea media) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC11375170/ · img: https://openi.nlm.nih.gov/imgs/512/3/11375170/PMC11375170_ceo-2024-00099f1.png | CC BY-NC 4.0 | Kim SJ, Bang JH, Lee KH (2024). Objective Parameters for Evaluating Internal Nasal Valve Compromise. Clin Exp Otorhinolaryngol. doi:10.21053/ceo.2024.00099. Fig. 1 | sí, de reserva (la Fig. 2 muestra las mediciones) |
| TC coronal con **hipertrofia del cornete inferior derecho** compensatoria a un tabique desviado a la izquierda, rotulada **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC6834714/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/16b4/6834714/7552fa5a5440/jdapm-19-307-g004.jpg | CC BY-NC 4.0 | Paramaswamy R (2019). Anesthesia for elective bilateral sagittal split osteotomy… J Dent Anesth Pain Med. Fig. 4 | dudoso (foto de placa con tinte azul; pero rotulada y correcta) |
| CBCT coronal con tabique desviado, hipertrofia del cornete derecho y congestión maxilar izquierda | https://pmc.ncbi.nlm.nih.gov/articles/PMC4320318/ · img: https://openi.nlm.nih.gov/imgs/512/345/4320318/PMC4320318_kjod-45-47-g006.png | CC BY-NC 3.0 | Gracco A, Perri A, Siviero L, Bonetti GA, Cocilovo F, Stellini E (2015). Korean J Orthod. doi:10.4041/kjod.2015.45.1.47. Fig. 6 | sí, de reserva (no se miró) |
| Endoscopía de CRSwNP recalcitrante antes y después de dupilumab (8 paneles) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC11277593/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/28b7/11277593/32d39449e63b/jpm-14-00735-g001.jpg | CC BY 4.0 | De Corso E, Settimi S, Penazzi D, et al. (2024). Dupilumab Improves Facial Pain… in CRSwNP and Recalcitrant Frontal Sinusitis. J Pers Med. doi:10.3390/jpm14070735. Fig. 1 | extra (no es TC; sirve para H23/rinoscopía) |
| RM con pansinusitis (serie T2 de Hellerhoff) **(vista -05)** | https://commons.wikimedia.org/wiki/File:Pansinusitis_MRT_-05.jpg (serie -00 a -12) | CC BY 3.0 | Hellerhoff | dudoso (se ve sobre todo el esfenoides; el libro necesita TC) |

---

### Descartadas por licencia (ND o sin licencia CC)

- **Schwannoma:** PMC4998729 (Medicine 2016, intrameatal T2+T1: buena, pero CC BY-NC-ND), PMC4898225 (Radiol Case Rep, "ice-cream cone", BY-NC-ND), PMC10988231 (J Neurosurg Case Lessons, Koos IV, BY-NC-ND), PMC153508 (BMC Neurol 2003, schwannoma gigante, sin bloque de licencia CC).
- **Diferenciales del ángulo:** PMC11930405 (epidermoide con DWI, Radiol Case Rep, BY-NC-ND), PMC11345106 (NMC Case Rep J, BY-NC-ND), PMC8593265 (BY-NC-ND), PMC6534685 (J Neurol Surg B, epidermoide pre/post con DWI, BY-NC-ND), PMC4898224 (meningioma del APC con cola dural y DWI, Radiol Case Rep, BY-NC-ND), PMC10205309 (meningiomas pre/retromeatales, BY-NC-ND), PMC9575104 (Chavda/Gorrie, LIO, BY-NC-ND), PMC9210264 (compresión neurovascular de la AICA en fusión 3D, BY-NC-ND).
- **Hidrops:** PMC12311983 (LIO 2025, hidrops con audiograma, BY-NC-ND).
- **Difusión negativa:** PMC5270759 (Am J Case Rep, **DWI negativa al día 3 y positiva al día 14 en el cerebelo**: era la ideal, pero es CC BY-NC-ND), PMC12344951 (Radiol Case Rep, BY-NC-ND, además supratentorial).
- **CANVAS:** PMC7879339 (Neurol Genet, T1 mediosagital, BY-NC-ND), PMC11438076 (BMC Neurol, BY-NC-ND), PMC12540548 (Cerebellum, BY-NC-ND).
- **Chiari:** PMC8730378 (Med Hypotheses, Chiari I frente a hallazgo incidental, BY-NC-ND).
- **Nariz:** PMC12484625 (Sci Rep 2025: **TC/RM del ciclo nasal con congestión alternante**, justo lo del cap. 36, pero BY-NC-ND), PMC12581283 (BMC Oral Health, hipertrofia de cornete inferior en TC, BY-NC-ND), PMC3146328 y PMC3468938 (Acta ORL Ital, BY-NC-ND), PMC5347520 (Pol J Radiol, "uso no comercial sin restricción", sin CC ni permiso de derivados), PMC7119142 (TC de resfrío común, "Reprinted with permission… AMA").
- **No usadas por licencia no estándar:** MedPix (MPX2348, intracanalicular <5 mm; MPX2453, meningioma con cola dural). Aparecen en Open-i, pero MedPix no publica bajo CC.

### No encontrado (o solo parcial)

- **Hidrops: técnica con gadolinio intratimpánico frente a IV**. No se buscó aparte. Las figuras halladas son todas IV a las 4 h, salvo PMC9270563 y PMC9270566 (J Otol, intratimpánico; J Otol suele ser BY-NC-ND, no se verificó).
- **Placa de EM en el tronco con ABR alterado en la misma figura**: no hay. Lo más cercano es PMC7423083 (placa pontina + audiometría, sin ABR). Alternativa: combinar esa RM con un ABR propio de LabSim, o buscar en Radiopaedia ("multiple sclerosis brainstem"). En Radiopaedia la licencia es por caso (suele ser CC BY-NC-SA 3.0), así que hay que anotar rID y autor caso por caso.
- **Infarto de la PICA puro en DWI con licencia limpia**: la mejor imagen (PMC2706413) tiene la licencia dudosa. Hay una con licencia limpia en T2 (PMC11622530). Alternativa: Radiopaedia "PICA infarct" (anotar rID) o escribir a J Clin Neurol, que hoy es CC BY-NC.
- **Difusión negativa → positiva en la PICA exactamente**: no hay con licencia libre. Se usan la de la AICA (PMC5307938) y la bulbar (PMC2503965).
- **Sagital normal limpio con licencia CC BY**: no apareció uno bueno. Alternativa: un corte mediosagital de un dataset abierto (IXI, CC BY-SA 3.0; OpenNeuro, CC0). Eso lo revisa el agente de datasets.
- **TC/RM antes y después de vasoconstrictor**: solo apareció el ciclo nasal de PMC12484625, que es ND. Alternativa: esquema propio o curvas de RinoSim (ya usadas en H24/H25). También se puede pedir permiso a los autores de PMC12484625 (Vithanage, Ginat, Dixon).
- **Pólipos nasales en TC coronal de un solo paciente, limpia**: solo está la figura compuesta por grados de PMC11505379 (CC BY-NC). Commons no tiene una TC de poliposis con licencia libre.
