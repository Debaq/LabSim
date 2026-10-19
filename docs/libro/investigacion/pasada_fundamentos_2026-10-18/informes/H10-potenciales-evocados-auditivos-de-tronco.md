# H10. Potenciales evocados auditivos de tronco

## Citas agregadas (respaldo encontrado)
- Cómo se informa / Qué se mide · diferencia interaural de la V anormal sobre 0,2 a 0,4 ms · (Selters y Brackmann, 1977) · doi:10.1001/archotol.1977.00780210037001 (PMID 849194; abstract: normal < 0,2 ms, tumores ≥ 0,4) · nueva en la lista: sí
- Cómo se informa / Qué se mide · en el oído normal la V es más grande que la I · (Musiek y cols., 1984) · doi:10.1097/00003446-198401000-00011 (PMID 6706028; V/I < 1 rara en normales y cocleares, 44 % en retrococleares) · nueva: sí
- Paso 8 / Vía ósea · el cráneo del lactante transmite peor de un lado al otro · (Yang y cols., 1987) · doi:10.1097/00003446-198708000-00009 (abstract: atenuación interaural ósea mayor en neonatos) · nueva: no (ya estaba)
- Fundamento · onda V ~0,5 µV · se cambió la cita a (Sanfins y cols., 2026), tabla de amplitudes: V 0,50 µV en 244 normoyentes (PMC13072904) · nueva: no
- Paso 8 / Vía ósea · la V ósea del lactante llega antes que la aérea · (Seo y cols., 2018) en vez de Yang 1987: el abstract de Yang no lo dice; Seo (texto completo, PMC5894486) sí, citando a Yang · nueva: no
- Referencias completadas con DOI, volumen y páginas (verificados en Crossref o PubMed): Don y Elberling 1994 y 1996, Stockard 1979, Da Silva Nunes 2005 (doi:10.5354/0719-4692.2005.48433), Jiang 1991 (autores, 80(1):60-4), Pinto y Matas 2007 (73(4):513-22), Stapells y Oates 1997, Seo 2018, Yang 1987 (8(4)), O'Beirne 1999, Jerger y Hall 1980, Delgado Hernández 2003 (2(1):13-8), Aguilar-Madrid 2016 (PMID), Gorga 1989, Rosa 2014 (autores, 26(2):117-21), Møller 1981 y 1983, Melcher 1996, Starr 1996, Berlin 1998.
- Comprobadas y sin cambios: Jiang 1991 (4-10 %, 9-13 %, 12-15 % de 10 a 90/s, en el abstract), Cargnelutti 2017 (V más grande con LS CE-Chirp, latencias iguales a 85 dB nHL), Jerger y Hall 1980 (0,2 ms y 10 % entre 25 y 55 años), Sanfins 2026 (IAD de la V 0,08 ms; medias de la tabla de LabSim; III, V e interpicos más cortos en mujeres), Seo 2018 (vibrador 45-55 dB nHL; ondas tempranas poco claras bajo 55 dB nHL), Elberling y Don 1984 (FSP), Starr 1996, Berlin 1998, Møller, Melcher y Kiang 1996.

## Corregidas (la literatura dice otra cosa)
- Fundamento / Latencia e intensidad · decía "la V pasa de unos 5 a 6 ms a 90 dB nHL a unos 8 a 9 ms a 20 dB nHL (ACNS, 2008)" → "pasa de 5,5 ms a 90 dB nHL a 8,2 ms a 20 dB nHL (Delgado Hernández y cols., 2003)". La guía ACNS 9C (PDF leído) no trae esas latencias y mide la intensidad en dB pe SPL · fuente: Delgado Hernández 2003, tabla II (PDF leído).
- Paso 8 / Vía ósea · los 15 dB de diferencia ósea-aérea del adulto con click se atribuían a Cobb y Stuart (2016) → (Stuart y cols., 1993). Cobb y Stuart usan CE-Chirp y en su trabajo de umbrales (JSLHR 2016;59(4):853-9) la diferencia del adulto es de 4 dB. Stuart 1993 (Am J Otol 14(2):176-82, PMID 8503493): adultos 3,75 aérea / 18,75 ósea; neonatos 3,75 / 1,25. Se reemplazó la referencia de Cobb (ya no se cita) y se resolvió el `verificar` de sus páginas.
- Cómo se informa / Contra qué se compara · decía "la onda I [del recién nacido] casi de adulto" y que el I-V llega "a valores de adulto entre los 9 meses y los 3 años (Gorga 1989; Sharma 2016)" → onda I "algo más tardía que la del adulto" (Rosa 2014: 1,79 ms al término); la V y los interpicos se acortan rápido hasta los 18 meses (Gorga 1989) y siguen más lento después de los 3 años (Sharma 2016: maduración completa a los 12 años).

## Quitadas o reformuladas (sin respaldo)
- Fundamento / función latencia-intensidad · se sacó la cita de Hood (1998) (instrucción del coordinador; índice no verificado). La cifra de 0,3 ms/10 dB entre 70 y 50 dB nHL queda sostenida solo por Delgado Hernández 2003 (V70 5,75 → V50 6,31 ms). Se quitó Hood de la lista de referencias.

## Quedan `verificar`
- Paso 5 / Enmascarar · atenuación interaural del click con fono de inserción "60 a 70 dB": Munro y Agnew (1999) solo dan tonos puros (mediana ~75-80 con inserción profunda; regla de enmascarar desde 55 dB). No se encontró serie con click de ABR; el rango viene de decisiones.md (aporte del docente 2026-09-21) sin fuente.

## Para el autor (práctica que choca con la literatura, no editada)
- (Fuera de mis archivos) `labsim_backend/src/Bibliografia.php`, ficha A03: atribuye a Cobb y Stuart 2016 los "~15 dB" óseo-aéreo del adulto que usa el generador; la fuente que lo dice con click es Stuart y cols. 1993 (Am J Otol 14(2):176-82). La ficha A03 también tiene volumen y páginas pendientes: Ear Hear 2016;37(6):710-23 (I) y 724-43 (II).
- (Fuera de mis archivos) `AbrReferences.php`, F17 "Nakhla V et al. ... PMC9444743" es el mismo artículo que F24 (Cargnelutti, Coser y Biaggio 2017, doi:10.1016/j.bjorl.2016.04.018); el autor "Nakhla V" no corresponde.
- Paso 7 / maduración: LabSim interpola la población 1-3 años; la literatura (Sharma 2016) muestra maduración de la V hasta los 12 años, más lenta después de los 3. No choca con el texto actual, pero la tabla del "niño mayor" debería considerarlo.

## Referencias de la lista con problemas
- Hood LJ 1998 · índice no verificado · quitada.
- Cobb KM, Stuart A 2016 · no sostenía la cifra; páginas faltantes · reemplazada por Stuart A, Yang EY, Stenstrom R, Reindorp AG 1993.
- Jiang ZD 1991 · incompleta (sin volumen ni páginas) · completada: 80(1):60-4, doi:10.1016/0168-5597(91)90044-x.
- Pinto FR, Matas CG · sin año/volumen/páginas (había `verificar`) · 2007;73(4):513-22.
- Sharma 2016 · páginas 97-104 → 97-101 (Crossref y PubMed).
- Rosa LAC 2014 · incompleta · 26(2):117-21 y autores.
- Delgado Hernández 2003 · sin páginas · 2(1):13-8 (Crossref fecha el DOI en 2021, es la digitalización del número de 2003).
- Da Silva Nunes 2005 · título con "acústico" de más según Crossref · corregido y con DOI.
- ACNS 2008 · el PDF existe (copyright 2008); la misma guía salió en J Clin Neurophysiol 2006;23(2):157-67 (doi:10.1097/00004691-200604000-00012). Se dejó como estaba.
