# Imágenes reales para los capítulos nasales (investigación de fuentes)

Fecha de la búsqueda: 2026-10-16. Solo se leyeron páginas (no se descargó ningún dataset).
Regla del libro: apto = CC0, dominio público, CC BY (cualquier versión). CC BY-NC apto, con aviso. CC BY-SA solo como figura separada sin modificar. "Solo investigación", sin licencia o dudosa = no apto. Todo lo que dice "no verificada" no se pudo comprobar en el origen.

Limitación: las descripciones de contenido de las figuras salen de los pies de figura y el texto, no de haber visto la imagen. Antes de usar cualquier archivo hay que abrirlo y confirmar que muestra lo que dice, y que no identifica a una persona.

## 1. Kaggle

| Fuente | URL | Licencia verificada | Hallazgos / n.º de imágenes | Apto | Notas |
|---|---|---|---|---|---|
| Datasets de endoscopia nasal / rinoscopia / pólipos nasales / tabique | kaggle.com (búsqueda) | no verificada | no se encontró ninguno | no | Varias búsquedas web restringidas a kaggle.com solo devolvieron datasets gastrointestinales (Kvasir, Hyper-Kvasir, GastroVision, esofágicos). La búsqueda interna de Kaggle es dinámica y no se pudo leer ni consultar por API sin credenciales. Si el usuario conoce un enlace concreto, hay que revisar subidor, si es el creador original, licencia declarada y ética a mano. |

Conclusión: no hay ningún dataset de Kaggle verificado y utilizable para este libro. Un espejo de Kaggle de 7-NasalEID o ENTRep no sería utilizable salvo que la licencia original lo permita (ver sección 2).

## 2. Datasets de investigación

| Fuente | URL | Licencia verificada y dónde se lee | Hallazgos / n.º de imágenes | Apto | Notas |
|---|---|---|---|---|---|
| 7-NasalEID (U-SEANNet) | https://arxiv.org/abs/2308.14081 | Ninguna: la página de arXiv dice "No license for this version due to withdrawn" (v3, retirado 2024-02-11). | 11.527 imágenes en el PDF v2 (la v3 dice 11.352): tabique desviado 2.338, rinitis alérgica 1.122, pólipos (CRSwNP) 1.305, hipertrofia adenoidea 1.530, rinosinusitis 980, carcinoma nasofaríngeo 776, normal 3.476. JPG 800x800 | no | Sin enlace de descarga ni declaración de disponibilidad. Hospital Afiliado Segundo de la U. de Shenzhen; datos desidentificados, sin consentimiento informado, con aprobación del comité. Sin licencia = no usable. Cubriría justo lo que falta, así que vale la pena escribir a los autores pidiendo una licencia explícita. |
| ENTRep (ACM MM 2025 Grand Challenge) | https://arxiv.org/abs/2508.04801 ; sitio del desafío https://aichallenge.hcmus.edu.vn/acm-mm-2025/entrep | El CC BY 4.0 de arXiv es del artículo, no del dataset. El dataset exige aceptar una "Dataset Usage Guideline" que no se pudo leer. | Hospital Thong Nhat, Ho Chi Minh. Test público 645 y privado 646; total de entrenamiento no indicado. Clases: oreja, nariz D/I, garganta, cuerdas vocales. Sin clases patológicas nasales finas | no | Uso restringido al desafío, términos no leídos. Ética y desidentificación no declaradas en el artículo. |
| UAAL (vía aérea superior, broncoscopia) | PMC12675523 ; Figshare https://doi.org/10.6084/m9.figshare.26342779.v4 | CC BY 4.0, leída en la API de Figshare (ficha del dataset, versión 4) y en el artículo de PMC. | 3.814 imágenes clínicas de 82 pacientes (8 clases anatómicas) + 2.746 de maniquí (9 clases). Son referencias anatómicas de la vía aérea (nariz a tráquea), no patología nasal | sí, con condición | Descarga 3,5 GB (no descargado). Consentimiento informado para uso y difusión pública, desidentificación y aprobación del CIRB SingHealth 2020-3021 declarados en el artículo. Útil solo para la cavidad nasal normal vista con broncoscopio; revisar que cada imagen elegida no muestre rasgos identificables. Atribución obligatoria a Hao et al. |
| NasalPolyp-CT-Sinonasal (Mendeley Data) | https://data.mendeley.com/datasets/ph4vffmzcn/1 | CC BY 4.0, leída en la ficha. | 453 TC (pólipos anterior y epitelial), Bangladesh | no (no es endoscopia) | Es tomografía; solo sirve como imagen de TC. Ética y consentimiento declarados. |
| Roboflow Universe, Zenodo, IEEE DataPort, PhysioNet | varias | no verificada | no se encontró ningún dataset de endoscopia nasal | no | Las búsquedas solo dieron pólipos gastrointestinales o cánula nasal en Roboflow. Un estudio piloto de pólipos (342 imágenes, 52 pacientes) no declara publicación. NPC-LES es privado. |

## 3. Wikimedia Commons

Licencias leídas en la API de metadatos de cada archivo en commons.wikimedia.org (campos LicenseShortName y Artist, que son los que declara el subidor). URL de cada archivo: https://commons.wikimedia.org/wiki/File:NOMBRE.

| Archivo | Autor | Licencia | Hallazgo | Apto | Notas |
|---|---|---|---|---|---|
| CHOANAL POLYP PerfectlyClear.jpg | Michael Hawke MD | CC BY 4.0 | pólipo coanal | sí | Confirmar que es imagen endoscópica. |
| Polyposis nasi 1.jpg | Klaus D. Peter, Wiehl | CC BY 3.0 de | poliposis nasal | sí | Atribución con nombre y enlace a la licencia. |
| Nasenscheidenwand.jpg | Leineabstiegsschleuse | CC0 | tabique nasal | sí | Contenido no confirmado, mirar el archivo. |
| Nasal Spaculum 00, 01, 02, 03, 05.jpg | SnowBink | CC0 | espéculo nasal (equipo) | sí | Cinco fotos del instrumento. |
| Examples of nasal speculum, both ancient and modern. Wellcome M0000167.jpg | Wellcome Images | CC BY 4.0 | espéculos nasales (grabado) | sí | Histórico. |
| Head of a man with nasal polyps, 14th C Wellcome L0037336.jpg | Wellcome | CC BY 4.0 | pólipos (ilustración medieval) | sí | Solo valor histórico. |
| Joseph Fayrer's casebook... Wellcome L0045485 / 86 / 87.jpg | Wellcome | dominio público | pólipos nasales (dibujos de caso) | sí | Histórico. |
| Ortenau Klinikum Sinuskopie.jpg | Ortenau Klinikum | CC BY 3.0 | esquema de endoscopia de senos | sí | Esquema, no imagen real. |
| Deviated septum MRI.jpg | Cajolingwilhelm (en.wikipedia) | dominio público | tabique desviado (RM) | sí | Es resonancia, no endoscopia. |
| Nasal endoscopy maxillary ostium recirculation.jpg | Dr atilla | CC BY-SA 4.0 | endoscopia, ostium maxilar | con condición | Solo sin modificar y como figura aparte. |
| Middle meatus polyp.jpg | Mustafakapadiya | CC BY-SA 4.0 | pólipo del meato medio | con condición | Sin modificar, figura aparte. |
| Polype nasal.jpg | MathieuMD | CC BY-SA 3.0 | pólipo en narina derecha | con condición | Sin modificar, figura aparte. |
| Septal Perforation.jpg | Dr. J.S. Bhandari | CC BY-SA 3.0 | perforación septal grande | con condición | Sin modificar, figura aparte. Puede identificar al paciente si hay cara. |
| 22 - NOSE PATHOLOGY - 07.jpg | Mike Gerkin | CC BY-SA 4.0 | patología nasal | con condición | Contenido no confirmado. |
| Deviated Septum.jpg | Rotterm1992 | CC BY-SA 4.0 | tabique desviado | con condición | Contenido no confirmado. |
| Thudichum's Nasal Speculum ENT Instrument Medical.jpg | Sarindam7 | CC BY-SA 4.0 | espéculo de Thudichum | con condición | |
| Miroir frontal - IHM-0567.jpg | personal del IHM (Lausana) | CC BY-SA 4.0 | espejo frontal de Clar | con condición | Único equipo de iluminación frontal hallado. |
| Adenoid hypertrophy.jpg | scientificanimations.com | CC BY-SA 4.0 | hipertrofia adenoidea | con condición | Probablemente ilustración. |
| 731 Nasal Cavity.jpg | OpenStax College | CC BY 3.0 | anatomía de cavidad nasal | sí | Ver sección 5. |

Hallado vacío en Commons: categorías Nasal polyps y Deviated septum (sin miembros con ese nombre), búsquedas de rinomanómetro, rinometría acústica, rinitis alérgica endoscópica, hipertrofia de cornetes y adenoides endoscópica. No hay, en lo encontrado, fotos de máscara de rinomanometría ni de rinómetro acústico. La categoría Nasal endoscopy como tal devolvió 404; solo apareció el archivo del ostium maxilar y dos SVG.

## 4. Artículos de acceso abierto CC BY (PMC / Europe PMC)

Licencia leída en la página del artículo en PMC. No se pudo consultar Open-i. Aviso general: si un pie de figura dice que se reproduce de otra fuente, esa figura puede tener otra licencia; leer el pie antes de usarla.

| Artículo | DOI / PMCID | Figura | Contenido | Licencia | Apto |
|---|---|---|---|---|---|
| Bilateral Nasolabial Cysts Mimicking Inferior Turbinate Hypertrophy... (Cureus 2026) | 10.7759/cureus.103058 / PMC12879257 | Figs. 3, 4, 5 | endoscopia intraoperatoria del piso nasal y cornete inferior | CC BY 4.0 | sí |
| Septochoanal polyp (Int J Surg Case Rep 2026) | 10.1097/rc9.0000000000000850 / PMC13544755 | Fig. 1 y Fig. 3 (panel superior) | perforación septal anterior y lesión del piso; vista endoscópica del pólipo | CC BY 4.0 | sí |
| Bifid inferior turbinate... (J Surg Case Rep 2026) | 10.1093/jscr/rjag689 / PMC13452474 | Fig. 2 | vista endoscópica de septoplastia y cirugía de cornete; Fig. 1 es TC con desvío septal e hipertrofia | CC BY 4.0 | sí |
| Clinical Impact of Nasal Obstructive Syndrome (Cureus 2025) | 10.7759/cureus.90762 / PMC12450431 | Figs. 3 y 4 | endoscopia en rinosinusitis crónica; endoscopia y rinometría acústica en estrechez | CC BY 4.0 | sí, tras verificar que no son figuras reproducidas |
| Improvement in nasal signs and eosinophils... SLIT (Front Immunol 2026) | 10.3389/fimmu.2026.1828695 / PMC13160792 | Fig. 4 | endoscopia de mucosa de ambas narinas y rinofaringe en rinitis alérgica, antes y después | CC BY | sí (cubre mucosa pálida/edematosa) |
| Adenoid/Nasopharynx Area Ratio... (OTO Open 2026) | 10.1002/oto2.70273 / PMC13312990 | Fig. 1 | endoscopia de adenoides en inspiración y apnea (paneles A-D) | CC BY 4.0 | sí |
| Nasal valve obstruction (Front Surg 2025) | 10.3389/fsurg.2025.1549915 / PMC11983596 | Figs. 1-2 | anatomía y esquemas de válvula nasal; sin fotos clínicas | CC BY 4.0 | sí, solo esquemas |
| Rhinomanometry: A Comprehensive Review (Cureus 2024) | 10.7759/cureus.61370 / PMC11214531 | Fig. 1 | tendencias; sin foto de equipo | CC BY 4.0 | sin utilidad para imágenes |
| Agreement Between Acoustic Rhinometry and CT (Diagnostics 2026) | 10.3390/diagnostics16020229 / PMC12839841 | Figs. 1-4 | planos de TC y curvas; sin foto del equipo | CC BY | sin utilidad para equipo |

Sin figura clínica utilizable de colapso de válvula nasal (Cottle) ni de secreción purulenta del meato medio dentro de lo revisado. Candidatos aún sin abrir: PMC13465222 (rinosinusitis pediátrica, endoscopia vs TC), PMC13472984 (ostium maxilar accesorio), PMC13392350 (sinequias del meato medio), PMC12971217 (videos de nasoendoscopia), PMC13486629 (endoscopia vs TC en rinosinusitis crónica). La licencia en esa lista es CC BY según el filtro de búsqueda, pero no se verificó en cada página.

## 5. Dibujos de anatomía

| Fuente | URL | Licencia verificada | Contenido | Apto | Notas |
|---|---|---|---|---|---|
| Servier Medical Art, "nasal cavity" | https://smart.servier.com/smart_image/nasal-cavity | CC BY 4.0, la página dice "Servier Medical Art is licensed under CC BY 4.0" y exige crédito | cavidad nasal (también hay categoría Sinuses: https://smart.servier.com/category/anatomy-and-the-human-body/respiratory-system/sinuses) | sí | Cita según https://smart.servier.com/how-to-cite-servier-medical-art/ . Existe también la vista sagital sin rótulos en anatomytool.org (nodo 61874), crédito Servier, no leída su licencia en el origen. |
| OpenStax Anatomy & Physiology, "731 Nasal Cavity" | https://commons.wikimedia.org/wiki/File:731_Nasal_Cavity.jpg | CC BY 3.0 (Commons); crédito OpenStax College, Connexions col11496 | cavidad nasal | sí | La licencia en el libro original de OpenStax no se verificó en su sitio. |
| Blausen 0872 UpperRespiratorySystem.png / Mouth and pharynx.png | Commons | CC BY 3.0 (BruceBlaus) | vía aérea superior | sí | La versión en español (-es) es CC BY-SA 4.0. |
| Gray153, Gray170, Gray859, Gray994-adenoid | Commons | dominio público | láminas anatómicas de Gray | sí | |

## Recomendación por necesidad del libro

- **H23 rinoscopía y hallazgos reales:** ninguna fuente masiva utilizable. Combinar las figuras CC BY de PMC (rinitis alérgica Fig. 4 de PMC13160792, adenoides Fig. 1 de PMC13312990, endoscopia de cornete/tabique de PMC12879257, PMC13544755 y PMC13452474) con los archivos CC0/CC BY de Commons (CHOANAL POLYP, Polyposis nasi 1). Los CC BY-SA (pólipo del meato medio, perforación septal, ostium maxilar) solo como figuras aparte y sin modificar.
- **Cobertura de clases:** hay imagen para pólipos, cornete inferior, rinitis alérgica, adenoides, perforación (BY-SA) y tabique (endoscopia intraoperatoria). Faltan, en lo hallado: espolón septal puro, secreción purulenta en el meato medio, colapso de válvula nasal.
- **Dataset grande:** 7-NasalEID cubre casi todas las clases (tabique 2.338, rinitis alérgica, pólipos, adenoides), pero hoy no tiene licencia. Conviene escribir a los autores (Univ. de Shenzhen) pidiendo permiso explícito CC BY o CC BY-NC. No usar nada de él mientras tanto.
- **H24/H25 equipos:** espéculo nasal en Commons (Nasal Spaculum 00-05, CC0; Wellcome CC BY). Espejo frontal solo CC BY-SA (Miroir frontal). No se encontró ninguna foto libre de máscara de rinomanometría ni de rinómetro acústico; las dos revisiones CC BY de PMC no traen fotos del equipo. Alternativa: fotografiar los equipos del laboratorio, o pedir permiso a fabricantes.
- **Casos (caps. 35-36):** las mismas figuras de PMC; para cavidad nasal normal, UAAL (CC BY 4.0) con condición de revisar identificabilidad.
- **B1 anatomía:** Servier "nasal cavity" (CC BY 4.0), OpenStax 731 Nasal Cavity (CC BY 3.0), láminas de Gray (dominio público), Blausen 0872 (CC BY 3.0).
- **Identificabilidad:** ningún dataset de la lista debe usarse con imágenes que incluyan rostro. Para fotos de Commons con paciente (perforación septal, pólipos), revisar la imagen antes de publicar.
