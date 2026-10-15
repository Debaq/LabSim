# Imágenes con licencia compatible para el libro de casos

Búsqueda hecha el 2026-10-15. Destino: libro gratuito CC BY-NC-SA 4.0.

**Cómo se verificó.** En Wikimedia Commons, la licencia y el autor se leyeron de la API (`extmetadata`: LicenseShortName/Artist) de cada archivo. En los artículos de PMC, la licencia salió del campo `license` de Europe PMC y del bloque `<license>` del XML completo del artículo. Si las dos fuentes no coincidían, se tomó la del XML. Las imágenes marcadas **(vista)** se bajaron a /tmp y se miraron. Las otras se juzgaron por el pie de figura. No se bajó nada al repo.

**Notas de licencia que importan:**
- **CC0, dominio público, CC BY y CC BY-NC**: se pueden usar y modificar dentro de un libro BY-NC-SA. Hay que atribuirlas.
- **CC BY-NC-SA**: misma licencia que el libro, así que no hay problema.
- **CC BY-SA**: se puede **incluir sin modificar**, como obra separada dentro de la colección, con su propia licencia en el pie. No conviene recortarla, rotularla ni traducirla, porque ese derivado tendría que ser BY-SA (no BY-NC-SA). Si hay que rotular, mejor usar la versión CC BY o PD equivalente cuando exista.
- Con las figuras de artículos hay que revisar el pie: algunas dicen "with permission of…" o "reproduced from…". Esas son de terceros y la licencia del artículo **no** las cubre. Ya se descartaron las que lo decían.
- Las figuras de Open-i se sirven a 512 px. La versión en alta resolución está en el artículo de PMC (`https://pmc.ncbi.nlm.nih.gov/articles/PMCxxxx/`).

Formato de atribución sugerido para artículos: *Autores (año). Título. Revista. doi. Fig. N. Licencia.*

---

## A. Otoscopía

### A.1 Glomus timpánico (masa roja retrotimpánica)

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Masa roja triangular detrás de una MT intacta, oído derecho. Rotulada "glomus jugulare", pero la imagen otoscópica es la misma que la del timpánico **(vista)** | https://commons.wikimedia.org/wiki/File:Glomus_Jugulare_Tumor.jpg · directa: https://upload.wikimedia.org/wikipedia/commons/e/e4/Glomus_Jugulare_Tumor.jpg | CC BY 4.0 | Michael Hawke MD, Wikimedia Commons | **sí** (la mejor: alta resolución, 2299×2279) |
| Fig. 1(a): masa roja bajo el cuadrante anterior de la MT, endoscopía **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC6652060/ · img: https://openi.nlm.nih.gov/imgs/512/272/6652060/PMC6652060_CRIOT2019-5780161.001.png | CC BY 4.0 | Ohki M, Kikuchi S (2019). A Small Glomus Tympanicum Tumor Resected by Minimally Invasive Transcanal Endoscopic Approach. Case Rep Otolaryngol. doi:10.1155/2019/5780161. Fig. 1 | **sí** (hay que recortar el panel a; la figura trae audiograma y TC) |
| Fig. 1 A–C: tres vistas endoscópicas preoperatorias de pacientes distintos, con masa redonda rojiza que toca la MT **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC8198089/ · img: https://openi.nlm.nih.gov/imgs/512/45/8198089/PMC8198089_jcm-10-02348-g001.png | CC BY 4.0 | Lee SJ et al. (2021). Treatment Outcomes of Patients with Glomus Tympanicum Tumors Presenting with Pulsatile Tinnitus. J Clin Med. doi:10.3390/jcm10112348. Fig. 1 | **sí** (tres ejemplos en una figura) |
| Fig. 1: "Otoscopic examination showing retrotympanic mass" de un paraganglioma timpanomastoideo, masa violácea **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC11048109/ · img: https://openi.nlm.nih.gov/imgs/512/158/11048109/PMC11048109_cancers-16-01466-g001.png | CC BY 4.0 | Yilala MH, Fancello G, Fancello V, Lauda L, Sanna M (2024). Long-Term Surgical Outcome of Class A and B Tympanomastoid Paragangliomas. Cancers. doi:10.3390/cancers16081466. Fig. 1 | **sí** |
| Fig. 1: MT izquierda intacta con tinte rojizo detrás **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC8856636/ · img: https://openi.nlm.nih.gov/imgs/512/150/8856636/PMC8856636_cureus-0014-00000021414-i01.png | CC BY 4.0 | Ghate G, Bhatnagar A, Mukhtar S (2022). Post-Embolization Excision of Glomus Tympanicum: A Case Report. Cureus. doi:10.7759/cureus.21414. Fig. 1 | **sí** (sutil, sirve para mostrar que no siempre se ve evidente) |
| Fig. 1A: imagen endoscópica de glomus Glasscock-Jackson I **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC10352693/ · img: https://openi.nlm.nih.gov/imgs/512/76/10352693/PMC10352693_jao-2022-00276f1.png | CC BY-NC 4.0 | Fountarlis AL et al. (2023). Endoscopic Management of Glomus Tympanicum Tumor: Report of Three Cases… J Audiol Otol. doi:10.7874/jao.2022.00276. Fig. 1 | dudoso (parece vista intraoperatoria con colgajo levantado y sangre, no otoscopía de consulta) |
| *Diagnóstico diferencial:* masa azul-rojiza no pulsátil detrás de una MT perforada (carótida aberrante) | https://pmc.ncbi.nlm.nih.gov/articles/PMC3628208/ · img: https://openi.nlm.nih.gov/imgs/512/361/3628208/PMC3628208_CRIM.OTOLARYNGOLOGY2013-743021.001.png | CC BY 3.0 | Muderris T et al. (2013). A potentially catastrophic anatomical variation: aberrant internal carotid artery in the middle ear cavity. Case Rep Otolaryngol. doi:10.1155/2013/743021. Fig. 1 | sí, como diferencial (no se miró la imagen) |

Descartadas por licencia ND: PMC11760328 (IJSCR), PMC7814085 (J Otol) y PMC10696267 (WJORL), las tres CC BY-NC-ND. También PMC6039638 (bulbo yugular alto), CC BY-NC-ND.

### A.2 Hemotímpano (barotrauma / fractura de temporal)

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 1: endoscopía de MT derecha con hemotímpano azul oscuro (epistaxis espontánea) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC3051890/ · img: https://openi.nlm.nih.gov/imgs/512/280/3051890/PMC3051890_1865-1380-4-3-1.png (Fig. 2 = oído izquierdo: …-4-3-2.png) | CC BY 2.0 | Fidan V, Ozcan K, Karaca F (2011). Bilateral hemotympanum as a result of spontaneous epistaxis. Int J Emerg Med. doi:10.1186/1865-1380-4-3. Figs. 1–2 | **sí** (la más clara de todas; la causa no es trauma, pero la imagen es la típica) |
| Fig. 1: hemotímpano bilateral, rojo vinoso, en paciente anticoagulado **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC1601950/ · img: https://openi.nlm.nih.gov/imgs/512/356/1601950/PMC1601950_1746-160X-2-31-1.png | CC BY 2.0 | Balatsouras DG et al. (2006). Bilateral spontaneous hemotympanum: case report. Head Face Med. doi:10.1186/1746-160X-2-31. Fig. 1 | **sí** (baja resolución, 255×512) |
| Fig. 1: micro-otoscopía de hemotímpano posparto por Valsalva, mecanismo de **barotrauma** **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC10432077/ · img: https://openi.nlm.nih.gov/imgs/512/62/10432077/PMC10432077_CRIOT2023-3328895.001.png | CC BY 4.0 | Teitelbaum T et al. (2023). Hemotympanum as a Complication of a Valsalva Maneuver during Childbirth. Case Rep Otolaryngol. doi:10.1155/2023/3328895. Fig. 1 | dudoso (tira de 3 fotos chicas y oscuras, 512×134) |
| Figs. 1–5: hemorragia **dentro** de la MT y pequeña sangre retrotimpánica, seriadas en el tiempo **(vista Fig. 1)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC6218969/ | CC BY 4.0 | Kim CH, Shin JE (2018). Hemorrhage within the tympanic membrane without perforation. J Otolaryngol Head Neck Surg. doi:10.1186/s40463-018-0300-0 | dudoso (no es hemotímpano franco; sirve como diferencial o para mostrar cómo se reabsorbe) |
| Fig. 1: hemotímpano bilateral por trombocitopenia | https://pmc.ncbi.nlm.nih.gov/articles/PMC3791947/ | "Unrestricted non-commercial use is permitted provided the original work is properly cited", sin CC explícita | Wong P et al. (2013). Clin Med Insights Ear Nose Throat. doi:10.4137/CMENT.S11885 | dudoso (licencia no estándar: deja el uso no comercial, pero no habla de obras derivadas) |

Descartadas por ND: PMC12221757 (Radiol Case Rep 2025, la única con **fractura de temporal** y otoscopía antes y después) y PMC9449038 (Braz J ORL).

### A.3 Atresia aural congénita / estenosis del CAE (vista externa y otoscopía)

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 2: foto de un niño con conducto visible pero estenosis ósea severa (A) y otro con atresia completa y microtia (B), con su TC **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC9831057/ · img: https://openi.nlm.nih.gov/imgs/512/141/9831057/PMC9831057_fsurg-09-944223-g002.png | CC BY 4.0 | Truong MT et al. (2022). Integrated microtia and aural atresia management. Front Surg. doi:10.3389/fsurg.2022.944223. Fig. 2 | **sí** (justo lo que pide el caso: estenosis frente a atresia) |
| Fig. 1: ilustración de la clasificación de microtia (normal, I–IV) **(vista)** | misma página · img: …/PMC9831057_fsurg-09-944223-g001.png | CC BY 4.0 | Truong MT et al. (2022), Fig. 1 | **sí** |
| Fig. 2: fotos de pabellones con microtia grado III y atresia aural en varias familias (caras con barra negra) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC9885525/ · img: https://openi.nlm.nih.gov/imgs/512/73/9885525/PMC9885525_nihms-1864558-f0002.png | CC BY 4.0 | Quiat D et al. (2023). Damaging variants in FOXI3 cause microtia and craniofacial microsomia. Genet Med. doi:10.1016/j.gim.2022.09.005. Fig. 2 | **sí** |
| Fig. 1: oreja en copa tipo III, **estenosis del CAE**, fosetas preauriculares, más audiograma y timpanograma (síndrome branquio-otorrenal) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC10801012/ · img: https://openi.nlm.nih.gov/imgs/512/77/10801012/PMC10801012_fgene-14-1292085-g001.png | CC BY 4.0 | He J et al. (2023). A novel mutation in the EYA1 gene in a child with branchiootic syndrome… Front Genet. doi:10.3389/fgene.2023.1292085. Fig. 1 | **sí** (trae además audiograma y timpanograma del caso) |
| Microtia unilateral grado III en un adulto **(vista)** | https://commons.wikimedia.org/wiki/File:Microtia.jpg | CC BY 3.0 DE | Klaus D. Peter, Wiehl, Germany | **sí** |
| Microtia nivel III en un lactante de 8 meses **(vista)** | https://commons.wikimedia.org/wiki/File:Microtia_lvl3.jpg | Dominio público | Mulgamutt (en.wikipedia) | **sí** (240×180, muy chica) |
| Recién nacido con oreja derecha atrésica (asociación VACTERL) **(vista)** | https://commons.wikimedia.org/wiki/File:Ear-VACTERL.jpg | Dominio público (CDC) | CDC / Dr. James W. Hanson | **sí** |
| Niña con síndrome de Goldenhar, "lop ear" sin microtia **(vista)** | https://commons.wikimedia.org/wiki/File:Goldenhar_syndrome.png | CC BY 2.0 | De Golovine S, Wu S, Hunter JV et al. | dudoso (no hay atresia) |
| Estenosis **adquirida** del CAE (<75% de la luz), endoscopía con luz blanca y NBI **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC9519157/ · img: https://openi.nlm.nih.gov/imgs/512/219/9519157/PMC9519157_BJBMS-22-798-g003.png | CC BY 4.0 | Pace A et al. (2022). Thiersch graft follow-up with narrow band imaging for acquired atresia of the external auditory canal. Bosn J Basic Med Sci. doi:10.17305/bjbms.2021.6876. Fig. 1 | sí (para estenosis adquirida; no es congénita) |
| Fig. 1A: estenosis del CAE antes de resecar un tapón fibroso | https://pmc.ncbi.nlm.nih.gov/articles/PMC12777715/ | El XML dice "CC BY-NC 4.0" en el texto pero enlaza a CC BY 4.0. Las dos sirven | Mahawerawat K et al. (2025). Iran J Otorhinolaryngol. doi:10.22038/ijorl.2025.87421.3932 | dudoso (no se miró la imagen) |

Descartadas por ND: PMC4887586 (estenosis congénita completa, IJSCR), PMC9195010, PMC9764815, PMC6002619 y PMC3199842.

### A.4 Carcinoma del conducto auditivo externo

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 2: endoscopía del CAE izquierdo con masa carnosa polipoide en el techo del conducto óseo (flecha). Carcinoma escamoso inducido por radiación **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC12558706/ · img: https://openi.nlm.nih.gov/imgs/512/188/12558706/PMC12558706_S0022215125102569_fig2.png | **CC BY-NC-SA 4.0** | Needham C, Wu J, Nunez DA (2025). Bilateral radiation-induced squamous cell carcinoma of the external auditory canal… J Laryngol Otol. doi:10.1017/S0022215125102569. Fig. 2 | **sí** (la mejor, y con la misma licencia que el libro) |
| Fig. 3A: lesiones papilares en el CAE y la mitad posterior de la MT, en un carcinoma escamoso que siguió a un papiloma **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC12185161/ · img: https://openi.nlm.nih.gov/imgs/512/375/12185161/PMC12185161_cureus-0017-00000084755-i03.png | CC BY 4.0 | Ohta Y et al. (2025). An Extremely Rare Case of Squamous Cell Carcinoma Following Treatment for External Auditory Canal Papilloma. Cureus. doi:10.7759/cureus.84755. Fig. 3 | sí (el panel A es chico; ir a la figura en alta resolución de PMC) |
| Fig. 1b: vista endoscópica del CAE con carcinoma escamoso (síndrome de Netherton) | https://pmc.ncbi.nlm.nih.gov/articles/PMC13175543/ | CC BY-NC 4.0 | Hayashi M et al. (2026). Squamous Cell Carcinoma of the External Auditory Canal in a Patient with Netherton Syndrome. Case Rep Dermatol. doi:10.1159/000551088. Fig. 1 | sí, pendiente de mirar (el panel a es una foto facial que hay que recortar) |
| Fig. 1a: masa color carne en las paredes anterior e inferior del CAE profundo (carcinoma neuroendocrino cutáneo) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC3420451/ · img: https://openi.nlm.nih.gov/imgs/512/322/3420451/PMC3420451_CRIM.OTOLARYNGOLOGY2012-941065.001.png | CC BY 3.0 | Li YK et al. (2012). Cutaneous neuroendocrine carcinoma of the external auditory canal. Case Rep Otolaryngol. doi:10.1155/2012/941065. Fig. 1 | dudoso (no es escamoso; sirve como "masa del CAE") |
| Fig. 1A: vista endoscópica de un mioepitelioma maligno del CAE | https://pmc.ncbi.nlm.nih.gov/articles/PMC10809454/ | CC BY 4.0 | Mateášiková Z, Salzman R, Michálek J (2024). Malignant myoepithelioma of the external auditory canal. World J Surg Oncol. doi:10.1186/s12957-024-03317-5. Fig. 1 | dudoso (otro tipo histológico; no se miró) |

Revisadas sin foto otoscópica útil: PMC11374347 (Cureus, solo TC y RM), PMC3420775 (solo TC, RM e histología) y PMC10486369 (solo TC y RM). Descartada por ND: PMC6929568 (revisión de Lovin y Gidley, con buena otoendoscopía, pero CC BY-NC-ND).

### A.5 Retracción de la MT / bolsillo de retracción / atelectasia

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 1: MT izquierda totalmente retraída y adherida a los huesecillos y al promontorio, con estructuras rotuladas (a–g) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC7752458/ · img: https://openi.nlm.nih.gov/imgs/512/326/7752458/PMC7752458_CCR3-8-2701-g001.png | CC BY 4.0 | Tzoi E et al. (2020). Hydrodissection technique with t-tube placement in atelectatic ear. Clin Case Rep. doi:10.1002/ccr3.3242. Fig. 1 (la Fig. 5 es la misma MT después) | **sí** (atelectasia/otitis adhesiva de libro) |
| Fig. 1: otoscopía preoperatoria de un bolsillo de retracción grado III, fondo no visible, con erosión de la cadena **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC9899731/ · img: https://openi.nlm.nih.gov/imgs/512/244/9899731/PMC9899731_405_2022_7573_Fig1_HTML.png | CC BY 4.0 | Immordino A et al. (2023). Mastoidectomy in surgical procedures to treat retraction pockets. Eur Arch Otorhinolaryngol. doi:10.1007/s00405-022-07573-7. Fig. 1 | **sí** |
| Fig. 1: bolsillo de retracción de la pars tensa con erosión de la articulación incudoestapedial (flecha) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC8147081/ · img: https://openi.nlm.nih.gov/imgs/512/365/8147081/PMC8147081_medicina-57-00425-g001.png | CC BY 4.0 | Urík M, Tedla M, Hurník P (2021). Pathogenesis of Retraction Pocket of the Tympanic Membrane—A Narrative Review. Medicina. doi:10.3390/medicina57050425. Fig. 1 | **sí** |
| Endoscopía de una MT izquierda retraída | https://commons.wikimedia.org/wiki/File:Wiki_TM_retraction.jpg | CC BY-SA 3.0 | Adrian L James, Wikimedia Commons | sí (220×220, muy chica; incluir sin modificar) **(vista)** |
| Fig. 3a: retracción ática (pars flaccida) antes de la cirugía, más TC **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC5665617/ · img: https://openi.nlm.nih.gov/imgs/512/289/5665617/PMC5665617_41536_2017_10_Fig3_HTML.png | CC BY 4.0 | Yamamoto K et al. (2017). Middle ear mucosal regeneration by tissue-engineered cell sheet transplantation. NPJ Regen Med. doi:10.1038/s41536-017-0010-7. Fig. 3 | sí (recortar el panel A) |
| Bolsillos de retracción en niños, con figuras de otoscopía | https://pmc.ncbi.nlm.nih.gov/articles/PMC10903084/ | CC BY 4.0 | Urík M et al. (2024). Cartilage tympanoplasty for retraction pocket of the tympanic membrane in children. Front Pediatr. doi:10.3389/fped.2024.1314184 | dudoso (Europe PMC no devolvió las figuras; mirar a mano) |

Descartadas por ND: PMC7737861 (Otol Neurotol 2021, con la **clasificación de Sadé ilustrada con otoscopías I–IV**, que sería ideal pero es CC BY-NC-ND) y PMC9761154 (Ann Transl Med).

### A.6 Datasets abiertos de otoscopía (¿traen estas clases?)

| Dataset | Licencia | Clases | ¿Sirve para A.1–A.5? |
|---|---|---|---|
| Polat, "eardrum.zip" (Van Akdamar, Turquía), https://figshare.com/articles/dataset/eardrum_zip/13648166 | CC BY 4.0 | normal, OMA, cerumen, miringoesclerosis, tubos, OMC supurada, otitis externa (282 imágenes) | no |
| OtoMatch (Ohio State, Camalan/Moberly), https://zenodo.org/records/4558155 | CC BY 4.0 | efusión, normal, tubo | no |
| Ear Imagery Database (Viscaino, Chile) / ASAM-CNN, https://zenodo.org/records/22829694 | CC BY 4.0 | OMC, tapón de cerumen, miringoesclerosis, normal | no (Viscaino ya está en uso) |
| Sumotosima / OCASD (GitHub anas2908/Sumotosima) | ver repo | OMA, cerumen, OMC, miringoesclerosis, normal (sale de Polat y Viscaino) | no |
| Roboflow "Otoscopy" (AJeni) | CC BY 4.0 | normal, otitis externa aguda, OMA | no |

Ningún dataset abierto encontrado trae glomus, hemotímpano, atresia, carcinoma del CAE ni retracción como clase. Para retracción y atelectasia existe el set chino de Zeng et al. (PMC9988777, CC BY), pero el artículo solo publica mapas de activación y no libera las imágenes.

### A.7 Otros hallazgos de Commons de buena calidad (por si sirven)
- `Exostosen.jpg`, `Exostosen2.jpg` (Welleschik, CC BY-SA 3.0) y `Ostéome.jpg` (Didier Descouens, CC BY-SA 4.0): exostosis y osteoma del CAE.
- `HematomeConduit.jpg` (Didier Descouens, CC BY-SA 4.0): hematoma del CAE.
- `Traumatic Perforation of the Tympanic Membrane.jpg` y su control "3 weeks later" (Michael Hawke, CC BY 4.0): perforación traumática por bofetada, que sirve para el capítulo de trauma.
- `Adult Serous Otitis Media.jpg` (Hawke, CC BY-SA 4.0) y `Normal Tympanic Membrane Chorda Tympani Nerve Visible.jpg` (Hawke, CC BY 4.0).

Todas en https://commons.wikimedia.org/wiki/File:<nombre>.

---

## B. Anatomía y fisiología (ilustraciones)

**Fuentes generales verificadas:**
- **Servier Medical Art** (https://smart.servier.com/category/anatomy-and-the-human-body/auditory-system/): el sitio actual declara **CC BY 4.0**. Ilustraciones del sistema auditivo: `ear`, `smart-ear`, `inner-ear`, `cochlea`, `organ-of-corti`, `eardrum`, `hammer`, `anvil`, `stirrup` y `auditive-nerve`, cada una en https://smart.servier.com/smart_image/<nombre>/. Atribución: "Servier Medical Art (smart.servier.com), CC BY 4.0". Las copias viejas en Commons figuran como CC BY-SA 3.0. Conviene bajar del sitio de Servier, que da CC BY.
- **OpenStax Anatomy & Physiology 2e**: el libro en línea hoy declara **CC BY-NC-SA 4.0**. Lo verifiqué en la página del cap. 14.1 y en la API de OpenStax. Es compatible. Las copias de la 1.ª edición en Commons figuran como CC BY 4.0 / 3.0 y son más cómodas.
- **Gray's Anatomy 1918** (H. V. Carter): dominio público.
- **Blausen Medical**: CC BY 3.0 en Commons. Cita pedida: *Blausen.com staff (2014). "Medical gallery of Blausen Medical 2014". WikiJournal of Medicine 1(2). doi:10.15347/wjm/2014.010*.

### B.1 Oído externo, medio e interno (general)

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Oído externo, medio e interno (OpenStax Fig. 14.5) | https://commons.wikimedia.org/wiki/File:1404_The_Structures_of_the_Ear.jpg | CC BY 4.0 | OpenStax, Anatomy & Physiology | **sí** |
| Anatomía del oído completa (Blausen 0328) | https://commons.wikimedia.org/wiki/File:Blausen_0328_EarAnatomy.png | CC BY 3.0 | Blausen.com staff (2014) | **sí** |
| Oído medio, **rotulado en español** (Blausen 0330) | https://commons.wikimedia.org/wiki/File:Blausen_0330_EarAnatomy_MiddleEar_-_Espa%C3%B1ol.png | CC BY 3.0 | BruceBlaus / Blausen.com staff (2014) | **sí** |
| Oído interno, **rotulado en español** (Blausen 0329) | https://commons.wikimedia.org/wiki/File:Blausen_0329_EarAnatomy_InternalEar-es.png | CC BY-SA 4.0 | BruceBlaus, traducción Ortisa | sí (incluir sin modificar). Alternativa CC BY en inglés: `Blausen_0329_EarAnatomy_InternalEar.png` |
| Oído y mastoides | https://commons.wikimedia.org/wiki/File:Ear_Anatomy_and_Mastoid_Bone.png | CC BY-SA 4.0 | BruceBlaus | sí |
| Corte del oído (Gray 904 y 907) | https://commons.wikimedia.org/wiki/File:Gray904.png · https://commons.wikimedia.org/wiki/File:Gray907.png | Dominio público | Henry Vandyke Carter, Gray's Anatomy (1918) | **sí** |
| Oído, Servier (dos versiones) | https://smart.servier.com/smart_image/ear/ · https://smart.servier.com/smart_image/smart-ear/ | CC BY 4.0 | Servier Medical Art | **sí** |

### B.2 Huesecillos y membrana timpánica

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Martillo, yunque y estribo, **rotulado en español** | https://commons.wikimedia.org/wiki/File:Illu_auditory_ossicles-es.svg | Dominio público | Original del gobierno de EE. UU.; SVG y traducción de Angelito7 | **sí** |
| Cadena osicular y ligamentos en corte frontal (Gray 919) | https://commons.wikimedia.org/wiki/File:Gray919.png | Dominio público | H. V. Carter, Gray's Anatomy | **sí** |
| MT con martillo y cuerda del tímpano (Gray 912) y estribo (Gray 918) | https://commons.wikimedia.org/wiki/File:Gray912.png · https://commons.wikimedia.org/wiki/File:Gray918.png | Dominio público | H. V. Carter | **sí** |
| Transmisión del sonido por la cadena hasta la cóclea (OpenStax Fig. 14.6) | https://commons.wikimedia.org/wiki/File:1405_Sound_Waves_and_the_Ear.jpg | CC BY 4.0 | OpenStax | **sí** (adaptación de impedancias) |
| Tres vistas del oído medio | https://commons.wikimedia.org/wiki/File:Three_views_of_the_middle_ear.png | CC BY-SA 4.0 | RWhitwam (sobre Blausen) | sí |
| Martillo, yunque, estribo y tímpano por separado (Servier) | https://smart.servier.com/smart_image/hammer/ · …/anvil/ · …/stirrup/ · …/eardrum/ | CC BY 4.0 | Servier Medical Art | **sí** |

### B.3 Cóclea, órgano de Corti y células ciliadas

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Corte de la cóclea con el órgano de Corti (OpenStax Fig. 14.7) | https://commons.wikimedia.org/wiki/File:1406_Cochlea.jpg (versión **en español**, CC BY-SA 4.0: `1406_Cochlea_esp.jpg`) | CC BY 4.0 | OpenStax | **sí** |
| Célula ciliada y apertura de canales (OpenStax Fig. 14.8) | https://commons.wikimedia.org/wiki/File:1407_The_Hair_Cell.jpg | CC BY 4.0 | OpenStax | **sí** |
| Codificación de frecuencia y tonotopía (OpenStax Fig. 14.10) | https://commons.wikimedia.org/wiki/File:1408_Frequency_Coding_in_The_Cochlea.jpg | CC BY 4.0 | OpenStax | **sí** (vulnerabilidad de la base) |
| Órgano de Corti, **rotulado en español** | https://commons.wikimedia.org/wiki/File:Organ_of_corti.es.png | CC BY-SA 3.0 | Madhero88; derivado de Ortisa | sí (sin modificar) |
| Corte de la cóclea, **en español** | https://commons.wikimedia.org/wiki/File:Cochlea-crosssection_es.jpg | CC BY-SA 3.0 | Oarih (en.wikipedia) | sí |
| Estructura de cóclea y órgano de Corti (Kelley MW) | https://commons.wikimedia.org/wiki/File:Structure_of_the_cochlea_and_organ_of_Corti.png | CC BY 4.0 | Kelley MW | **sí** |
| Tonotopía (Pavlinkova) | https://commons.wikimedia.org/wiki/File:Tonotopic_organization.png | CC BY 4.0 | Pavlinkova G | **sí** |
| Canales de mecanotransducción en la célula ciliada | https://commons.wikimedia.org/wiki/File:Mechanically_gated_ion_channels_in_hair_cells.png | CC BY 4.0 | Qiu X, Müller U | **sí** |
| CCE con célula de Deiters | https://commons.wikimedia.org/wiki/File:Outer_hair_cell_and_Deiter%27s_cell.svg | Dominio público | Inductiveload | sí (electromotilidad) |
| **Circulación de K⁺ y potencial endococlear** en la pared lateral | https://commons.wikimedia.org/wiki/File:Diagram_showing_potassium_and_other_ion_circulation_and_the_formation_of_the_EP_within_the_lateral_wall.jpg | CC BY 4.0 | Furness DN | **sí** (cap. "Potasio y conexina 26") |
| Ganglio espiral y conexión de las células ciliadas con los núcleos cocleares | https://commons.wikimedia.org/wiki/File:Auditory_neurons_form_the_spiral_ganglion_in_the_cochlea_and_connect_hair_cells_in_the_organ_of_Corti_to_cochlear_nuclei_in_the_brain_stem.png | CC BY 4.0 | Pavlinkova G | **sí** |
| Órgano de Corti y cóclea (Servier) | https://smart.servier.com/smart_image/organ-of-corti/ · https://smart.servier.com/smart_image/cochlea/ | CC BY 4.0 | Servier Medical Art | **sí** |
| Órgano de Corti histológico (Gray 931) y corte longitudinal de la cóclea (Gray 928) | https://commons.wikimedia.org/wiki/File:Gray931.png · https://commons.wikimedia.org/wiki/File:Gray928.png | Dominio público | H. V. Carter | sí |
| Ductus coclear y estría vascular, esquemas en alemán | https://commons.wikimedia.org/wiki/File:Ductus_cochlearis_schema.jpg · https://commons.wikimedia.org/wiki/File:Stria_vascularis1.jpg | CC BY-SA 3.0 | Welleschik | dudoso (rótulos en alemán) |

### B.4 Vía auditiva central

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Vía auditiva de la cóclea a la corteza | https://commons.wikimedia.org/wiki/File:Auditory_pathway.svg | CC0 | Wittiko | **sí** (SVG, se puede traducir libremente) |
| Esquema de la vía auditiva | https://commons.wikimedia.org/wiki/File:Auditory_Pathway.png | CC BY 4.0 | Jonathan E. Peelle | **sí** |
| Núcleos terminales del nervio coclear y sus conexiones superiores (Gray 760); núcleos vestibulares (Gray 761) | https://commons.wikimedia.org/wiki/File:Gray760.png · https://commons.wikimedia.org/wiki/File:Gray761.png | Dominio público | H. V. Carter | **sí** (cap. "Generadores del ABR") |
| Nervio auditivo (Servier) | https://smart.servier.com/smart_image/auditive-nerve/ | CC BY 4.0 | Servier Medical Art | sí |

### B.5 Sistema vestibular y otolitos

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Máculas y aceleración lineal / inclinación (otolitos) (OpenStax Fig. 14.11) | https://commons.wikimedia.org/wiki/File:1409_Maculae_and_Equilibrium.jpg | CC BY 3.0 | OpenStax College | **sí** |
| Canales semicirculares, cúpula y rotación (OpenStax Fig. 14.12) | https://commons.wikimedia.org/wiki/File:1410_Equilibrium_and_Semicircular_Canals.jpg | CC BY 3.0 | OpenStax College | **sí** |
| Laberinto membranoso (Gray 925) | https://commons.wikimedia.org/wiki/File:Gray925.png | Dominio público | H. V. Carter (G. Retzius) | sí |
| Sistema vestibular, rotulado en español | https://commons.wikimedia.org/wiki/File:VestibularSystem.png | CC BY-SA 3.0 | Thomas Haslwanter; derivado de Ortisa | sí (300×229, chica) |

### B.6 Vía del VEMP (vestibulocólica / vestíbulo-ocular)

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 1: vías del cVEMP y del oVEMP (oblicuo inferior, III par, FLM, ECM) | https://pmc.ncbi.nlm.nih.gov/articles/PMC13535002/ | CC BY-NC 4.0 | Zhou S et al. (2026). Unveiling Otolith Mystery: Contemporary Testing Approaches… World J Otorhinolaryngol Head Neck Surg. Fig. 1 | **sí** (no se miró) |
| Fig. 4: proyecciones de los 5 órganos vestibulares al esternocleidomastoideo (según Uchino) | https://pmc.ncbi.nlm.nih.gov/articles/PMC11794123/ | CC BY 4.0 | Kjærsgaard JB, Hougaard DD, Kingma H (2024). Thirty years with cervical vestibular myogenic potentials. Front Neurol. Fig. 4 | **sí** (no se miró) |
| Fig. 7: esquema de la vía neural del cVEMP, con núcleos vestibulares | https://pmc.ncbi.nlm.nih.gov/articles/PMC12691058/ | CC BY 4.0 | Georgescu M et al. (2025). Diagnosis of Isolated Saccular Dysfunction Using Trapezius cVEMP. Diagnostics. Fig. 7 | sí (no se miró) |
| Ondas del VEMP (registro tipo) | https://commons.wikimedia.org/wiki/File:VEMP_%C2%B4s_waves.png | CC BY 3.0 | Lamounier P (2017). Electrophysiology in Ménière's Disease. InTech | sí (registro, no vía) |

---

## C. Fotos de técnica

### C.1 Uso del otoscopio

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Médica examinando el CAE con otoscopio: tracciona el pabellón hacia arriba y atrás y apoya la mano (CDC PHIL) **(vista)** | https://commons.wikimedia.org/wiki/File:Exploraci%C3%B3_f%C3%ADsica.jpg | CC0 | Amanda Mills (CDC) | **sí** (la mejor) |
| Estudiante haciendo otoscopía a otro **(vista)** | https://commons.wikimedia.org/wiki/File:Performing_an_Otoscopic_exam.jpg | CC BY-SA 4.0 | MohmmadRjab | sí |
| Partes de un otoscopio rotuladas | https://commons.wikimedia.org/wiki/File:Otoscope_Spengler_SMARTLED_5500.png | CC BY-SA 4.0 | Rouibi Dhia Eddine Nadjm | sí |
| Otoendoscopio, impedanciómetro y herramientas (Fig. 4A) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC7176302/ | CC BY 4.0 | Simpson MJ, Jennings SG, Margolis RH (2020). Techniques for Obtaining High-quality Recordings in Electrocochleography. Front Syst Neurosci. doi:10.3389/fnsys.2020.00018 | dudoso (fotos de equipo, no de uso) |

### C.2 Colocación del vibrador óseo

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 2A–B: **foto** de un paciente con el vibrador B81 en la mastoides (cVEMP) y en posición de oVEMP, con electrodos **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC9131004/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/619c/9131004/d1f9dcd96d39/fneur-13-881682-g0002.jpg | CC BY 4.0 | Zhang Y et al. (2022). B81 Bone Vibrator-Induced Vestibular-Evoked Myogenic Potentials: Normal Values and the Effect of Age. Front Neurol. doi:10.3389/fneur.2022.881682. Fig. 2 | **sí** (sirve para vibrador y para C.5) |
| Fig. 4: ilustración del B81 sobre el temporal, 50–55 mm detrás de la oreja, con vincha | https://pmc.ncbi.nlm.nih.gov/articles/PMC10565869/ | CC BY 4.0 | Irwansyah, Otsuka S, Nakagawa S (2023). Unilateral crosstalk cancellation via bone conduction. MethodsX. Fig. 4 | sí (no se miró; contexto de investigación) |

No encontré una foto clínica de audiometría con el vibrador en la mastoides y licencia abierta (ver "No encontrado").

### C.3 Montaje de electrodos del ABR

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 3: lactante en sueño natural con electrodos y fonos de inserción durante un ABR **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC9831057/ · img: https://openi.nlm.nih.gov/imgs/512/141/9831057/PMC9831057_fsurg-09-944223-g003.png | CC BY 4.0 | Truong MT et al. (2022). Integrated microtia and aural atresia management. Front Surg. Fig. 3 | **sí** (cara tapada con barra negra) |
| Fig. 2: ilustración de los montajes vertical y horizontal (A2 conducto, M1, Fz, tierra) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC10740558/ | CC BY 4.0 | McFarlane KA, Sanchez JT (2023). Exploring Electrode Placements to Optimize the Identification and Measurement of Early Auditory Evoked Potentials. Audiol Res. Fig. 2 | **sí** |
| Fig. 1: seis montajes (lóbulo/Cz, lóbulo/Fz, conducto/Cz…) para ABR y ECochG | https://pmc.ncbi.nlm.nih.gov/articles/PMC13355502/ | CC BY 4.0 | Beaud-Henry L et al. (2026). Clin Neurophysiol Pract. Fig. 1 | sí (no se miró) |
| Fig. 3: colocación de electrodos y curvas normales del BAEP (Cz, Ai, Ac) | https://pmc.ncbi.nlm.nih.gov/articles/PMC11046378/ | CC BY 4.0 | Portell Penadés E, Alvarez V (2024). A Comprehensive Review and Practical Guide of the Applications of Evoked Potentials in Neuroprognostication… Cureus. Fig. 3 | sí (no se miró) |
| Fig. 1: esquema de cabeza con Fz, Cz, Ai y Ac **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC11440015/ | CC BY 4.0 | Singh M et al. (2024). Cureus. Fig. 1 | dudoso (muy esquemático) |
| Recién nacido durante el tamizaje auditivo | https://commons.wikimedia.org/wiki/File:NeonatalHearingScreening.jpg | CC BY-SA 4.0 | Liannadavis | dudoso (no se miró; no se sabe si es AABR u OEA) |
| Tamizaje auditivo neonatal, Oude Pekela (serie 01–04) | https://commons.wikimedia.org/wiki/File:Newborn_hearing_screening,_Oude_Pekela_(2019)_01.jpg | CC BY-SA 4.0 | Donald Trung Quoc Don | dudoso (no se miró) |
| Recién nacido durante un test de audición (USAF) | https://commons.wikimedia.org/wiki/File:New_Born_Hearing_Test_160823-F-VS498-002.jpg | Dominio público | U.S. Air Force, A1C Travis Beihl | dudoso (no se miró) |

### C.4 Electrodo de ECochG (timpánico / TIPtrode)

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 6: electrodo timpánico comercial en el conducto (A) y vista video-otoscópica del electrodo sobre la MT (B) **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC7176302/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/8a30/7176302/13b6b7007378/fnsys-14-00018-g0006.jpg | CC BY 4.0 | Simpson MJ, Jennings SG, Margolis RH (2020). Front Syst Neurosci. doi:10.3389/fnsys.2020.00018. Fig. 6 (Fig. 5: el electrodo de cerca) | **sí** (la mejor) |
| Fig. 2: dibujo del electrodo TM con punta de gel contra la MT, fijado por la sonda de inserción **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC7931016/ | CC BY 4.0 | Coraci LM, Beynon AJ (2021). Use of an Extra-Tympanic Membrane Electrode to Record Cochlear Microphonics… Audiol Res. Fig. 2 | sí (la Fig. 1 queda **excluida**: "with permission of Interacoustics") |
| Fig. 1d: posición del paciente durante la ECochG, con el equipo | https://pmc.ncbi.nlm.nih.gov/articles/PMC11247444/ | CC BY-NC 4.0 | Behzad H et al. (2024). Iran J Otorhinolaryngol. Fig. 1 | dudoso (foto chica, solo de contexto) **(vista)** |
| Registro tipo de ECochG (SP/AP) | https://commons.wikimedia.org/wiki/File:EcochG.png | CC BY 3.0 | Lamounier P (2017). InTech | sí (registro, no técnica) |

No encontré una foto de TIPtrode con licencia abierta.

### C.5 cVEMP: electrodos y activación del ECM

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| Fig. 1: **fotos** de un sujeto sano con electrodos sobre el ECM (cVEMP) y el trapecio, en contracción **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC12520153/ · img: https://cdn.ncbi.nlm.nih.gov/pmc/blobs/aeaf/12520153/70d71270636d/jiao-21-5-241836_f001.jpg | CC BY-NC 4.0 | Satar B, Karababa E, Karaçaylı C (2025). The VEMP test over the Trapezius Muscle. J Int Adv Otol. Fig. 1 | **sí** |
| Fig. 2A: foto del montaje del B81-cVEMP con cabeza rotada y electrodos sobre el ECM **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC9131004/ | CC BY 4.0 | Zhang Y et al. (2022). Front Neurol. Fig. 2 | **sí** |
| Fig. 1: ilustración del montaje cVEMP con fonos y electrodos sobre el ECM **(vista)** | https://pmc.ncbi.nlm.nih.gov/articles/PMC13040205/ | CC BY 4.0 | Cortese E et al. (2026). Cervical vestibular evoked myogenic potential asymmetry… Front Neurol. Fig. 1 | sí |
| Fig. 1: montaje del mVEMP (masetero), como contraste | https://pmc.ncbi.nlm.nih.gov/articles/PMC11512666/ | CC BY 4.0 | Kumar C B et al. (2024). Cureus. Fig. 1 | dudoso (otro músculo) |

### C.6 Sonda de timpanometría

| Qué muestra | URL página | Licencia | Atribución | Sirve |
|---|---|---|---|---|
| **Video**: colocación de la sonda de timpanometría (se pueden sacar cuadros) | https://commons.wikimedia.org/wiki/File:Tympanometry_-_placing_the_probe.webm | CC BY 4.0 | AraujoLN | **sí** (sacar un fotograma) |
| Video: cómo se hace la timpanometría | https://commons.wikimedia.org/wiki/File:Tympanometry_-_how_to_perform.webm | CC BY 4.0 | AraujoLN | sí |
| Ilustración de la timpanometría (5333×3808) | https://commons.wikimedia.org/wiki/File:Tympanometry.png | CC BY 4.0 | AraujoLN | sí |
| "Examen tympanogramme" en un hospital de Camerún | https://commons.wikimedia.org/wiki/File:Hopital_Laquintini-4993_32.jpg | CC BY-SA 4.0 | Max MBAKOP | dudoso (no se miró) |
| Videos del impedanciómetro AZ7: presión, fuga, reflejo | https://commons.wikimedia.org/wiki/File:AZ7_Tympanometer_stapedial_acoustic_reflex.webm | CC BY-SA 4.0 | LiJacob | dudoso (muestran el equipo, no la sonda en el oído) |

### C.7 Extra: diapasones (no pedido, pero aparecieron)
- `Rinneversuch.png` y `Weberversuch.png` (Ziyun518, **CC0**): dibujos de Rinne y Weber.
- `Weber Test.jpg` (DrSaltMD, CC BY-SA 4.0): foto real del Weber.

---

## No encontrado (le toca al autor)

1. **Hemotímpano postraumático** (fractura de temporal o barotrauma de buceo/vuelo) con licencia compatible. Las únicas otoscopías de fractura (PMC12221757) son CC BY-NC-ND. Las compatibles muestran hemotímpano **espontáneo** (anticoagulación, epistaxis) o por Valsalva. Son útiles para el aspecto, pero no para la causa. Lo ideal es una foto propia o pedir permiso.
2. **Clasificación de Sadé con otoscopías (grados I–IV)**: la serie completa (PMC7737861) es ND. Con licencia abierta hay atelectasia y bolsillos sueltos, sin serie graduada.
3. **Glomus en serie Glasscock-Jackson / Fisch** (A1→B): hay ejemplos sueltos, no una serie por clase.
4. **Atresia aural vista con otoscopio** (conducto ciego o membranoso): solo hay vista externa y TC. La foto otoscópica de una estenosis **congénita** (PMC4887586) es ND.
5. **Carcinoma escamoso del CAE en etapa temprana** (granulación que sangra y simula otitis externa), que es justo el caso que enseña la trampa. Solo hay masas avanzadas o papilares.
6. **Foto clínica del vibrador óseo en audiometría tonal** (B71/B81 con vincha en la mastoides, en la cabina). Solo aparece en contexto de VEMP o de investigación.
7. **TIPtrode** (electrodo de espuma dorada en el conducto): no hay ninguna imagen con licencia abierta.
8. **Foto de la sonda de timpanometría en el oído**: solo hay videos en Commons, de los que se puede sacar un cuadro. No hay foto fija.
9. **Montaje de ABR en adulto con foto real** (Fz/Cz, mastoides y tierra): solo hay ilustraciones y el lactante de PMC9831057.
10. **Vía del VEMP en español**: las ilustraciones encontradas están en inglés. Para traducirlas conviene partir de las CC BY o CC BY-NC (PMC11794123, PMC13535002), no de las BY-SA.
11. **Datasets abiertos** con estas clases: no existen (A.6). Las clases raras quedan para fotos propias del autor o de colegas con consentimiento.
