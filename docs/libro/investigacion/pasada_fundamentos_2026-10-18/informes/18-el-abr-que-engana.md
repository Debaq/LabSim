# 18. El ABR que engaña

## Citas agregadas (respaldo encontrado)
- Fisiología, filtros (resuelve el `verificar` del corrimiento de latencia) · con filtros convencionales el pasa alto achica más las ondas y adelanta la V frente a un filtro de fase cero · (Kavanagh y Franks, 1989) · doi:10.1177/000348948909800704, PMID 2751210 · nueva sí. Abstract: "Conventional filters were found to decrease the height of the evoked response in the majority of waveforms compared to zero phase shift filters... A decrease in the mean along with an increase in the variability of wave IV/V latency was also noted with conventional compared to zero phase shift filters". No da una magnitud única en ms, así que el texto no da número. (Coincide con Stuart y Yang 1994, PMID 8028329, filtros analógicos en neonatos: "decreases in wave V latency... with the progressive increase in the high-pass filter cutoff"; no se agregó.)
- Resolución del caso 18.2 · pinzar el tubo separa artefacto de respuesta · (BSA, 2019) · ya estaba en la lista sin citar. PDF OD104-87: "the acoustic stimulus can be easily blocked during a control run by clamping the tube ... since in this condition the electrical artefact remains whilst the stimulus is effectively withdrawn".
- Fisiología, PAMR · latencia según intensidad (ver Corregidas) · (Purdy y cols., 2005) · ya estaba.
- Verificado sin cambios: Picton y cols. 1983, Don y Elberling 1994 y 1996, Elberling y Don 1984 (Crossref/PubMed, datos de la lista correctos), Stockard 1979 (efecto de la fase del click sobre las ondas; el detalle "la I sale antes y más clara en rarefacción" no está en el abstract, pero es el hallazgo clásico de ese trabajo), Purdy 2005.

## Corregidas (la literatura dice otra cosa)
- Fisiología, "Un músculo que contesta al sonido" (y su `verificar`) · decía "Con sonidos intensos se contrae... latencia cercana a 12 a 15 ms" y dudaba de si la latencia cambia con la intensidad → "con el sonido... primer pico entre 12,5 y 15 ms, según la intensidad y el tono del músculo; puede aparecer a menos de 20 dB del umbral subjetivo y crece mucho con la intensidad (O'Beirne y Patuzzi, 1999). Al bajar el estímulo se achica y su latencia se alarga (Purdy y cols., 2005)". O'Beirne y Patuzzi 1999 (abstract, PMID 10575120): "first peak latency of between 12.5 and 15 ms, depending on the stimulus intensity and PAM muscle tone... can be obtained with click and tone-burst stimuli within 20 dB of the subjective detection threshold... grows either linearly with the click level". Purdy 2005 (abstract, PMID 16379490): "PAMR amplitudes declined and latencies increased with decreasing click intensity".
- Patología, tabla "Lo que engaña" · la PAMR "**no migra** con la intensidad" → "Tarda 12 a 15 ms, mucho más que cualquier V; es ancha y más grande que el ABR, cambia con la tensión y la mirada del paciente y se achica al relajarlo". Mismas fuentes.
- Caso 18.3, guía docente · "registrar a un nivel menor (la respuesta muscular suele caer antes que la V)" + verificar → "registrar a un nivel menor y comparar latencias: la V se atrasa dentro de su ventana y la onda muscular sigue en 12 a 15 ms o más". Purdy 2005: "All normal-hearing subjects had PAMR when recording conditions were optimized and half had responses for the least optimal condition (20 dB nHL, monaural, eyes front)": no cae de forma fiable antes que la V.
- Ayuda memoria del capítulo · "La respuesta postauricular ... cae antes que la V" → "... cambia con la tensión del paciente".

## Quitadas o reformuladas (sin respaldo)
- Ninguna aparte de las anteriores.

## Quedan `verificar`
- Fisiología, "Qué hay entre los electrodos" · la cifra de 0,5 µV para la onda V atribuida a Da Silva Nunes y Gentile Matas 2005: el resumen confirma que miden amplitudes de I, III y V en 50 adultos, pero el texto completo (revfono.uchile.cl, detrás de una verificación antibots) no se pudo leer. Crossref solo lista como autora a "Da Silva".

## Para el autor (práctica que choca con la literatura, no editada)
- Figura `cap18-pam.svg` (globos @92,27 a @92,88) y Resolución del caso 18.3 · dicen que la onda muscular "no se atrasa al bajar la intensidad" y que "desaparece al bajar de 80 a 70 dB mientras la V verdadera sigue". Es lo que hace la PAMR de LabSim (latencia fija), pero O'Beirne y Patuzzi 1999 y Purdy 2005 muestran que su latencia se alarga al bajar el estímulo y que puede registrarse cerca del umbral. Lo que sí la separa de la V es la latencia absoluta (12,5-15 ms o más), el tamaño, el ancho y su dependencia del tono muscular y de la mirada. No toqué los globos ni la figura (regla del brief); conviene corregir el modelo de LabSim o el pie.
- Fisiología · LabSim rechaza a ±25 µV; Hatton 2022 (cap. 17) pide ajustar el rechazo para que no se pierda más del 5-10 % de los barridos y nunca superar ±25. No choca, solo para saberlo.

## Referencias de la lista con problemas
- Da Silva Nunes y Gentile Matas 2005 · el título en Crossref es "Audiometría de tronco encefálico utilizando diferentes polaridades de presentación del estímulo" (sin "acústico") · corregido. Los nombres de las autoras no se pudieron confirmar.
- Small y Stapells 2004 · existe, pero no se cita en el texto (trata de artefactos en el ASSR) · se dejó; decidir si se cita o se quita.
- Stockard y cols. 1979 · el DOI termina con punto final pegado ("...037006.") · igual que la de Da Silva; no se tocó el estilo.
