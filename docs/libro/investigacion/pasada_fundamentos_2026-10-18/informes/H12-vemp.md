# H12. VEMP

El capítulo ya venía bien sostenido en Rosengren y cols. (2019), cuyo texto completo (PMC6430081) se leyó entero para esta pasada. Se confirmaron contra ese texto: umbral sacular 15-20 dB bajo el utricular, sintonía 500-1.000 Hz, 114 dB pkSPL, +13,5 dB ANSI/TDH49, 95 dB nHL de partida, tone burst hasta 6 ms, 100-200 barridos y dos registros largos (150-200), 50 barridos que fingen respuesta (Fig. 4), respaldo 20-40°, contracción máxima que deja residuos, 80 µV (Rosengren 2015), ejemplo 61/127 µV, ejemplo 46/156 µV → 49 % / 6,7 %, 35 %/46 % (Welgampola y Colebatch 2001) y 43 %/~30 % (McCaslin 2014), 5-15 % sin cVEMP sobre 60 años, umbral oVEMP 5-10 dB más alto, nivel bajo en rutina para la tercera ventana, saturación del cVEMP, 135 dB pkFL B-71, oVEMP óseo más robusto, lado chico = enfermo salvo tercera ventana e hidrops temprano, Jongkees con y sin valor absoluto, Ménière más grande a 1 kHz y SCD con sintonía ancha, estímulo débil como primer problema al implementar, oVEMP aéreo con más falsos positivos. Zhou 2012 (50/50 oído medio con VEMP aéreo ausente) confirmado en el resumen de PubMed.

## Citas agregadas (respaldo encontrado)
- Para qué sirve, límites · oído sordo con oído medio sano da VEMP normal · (Colebatch y cols., 1994) · doi:10.1136/jnnp.57.2.190 · nueva no
- Para qué sirve, límites · en el hidrops el cVEMP puede salir normal (30-50 % asimétricos) · (Rosengren y cols., 2019) · doi:10.1016/j.cnp.2019.01.005 · nueva no
- Dos reflejos, cVEMP · vía sáculo-ECM ipsilateral, disináptica, por el fascículo vestibuloespinal medial · (Kushiro y cols., 1999) · doi:10.1007/s002210050747 · PMID 10382625 · nueva sí
- Montaje oVEMP · señal del oVEMP diez veces más chica ("an order of magnitude smaller") · (Rosengren y cols., 2019) · nueva no
- Tabla de parámetros, tasa · sobre 10/s cae la amplitud del cVEMP · (Rosengren y cols., 2019, que cita a Sheykholeslami 2001) · nueva no
- Lectura en pacientes (Patricia) · en el hidrops el sáculo se daña antes que el utrículo · (Young, 2013) · doi:10.1002/lary.23640 · PMID 23070719 · nueva sí (ya estaba en BibliografiaPatologias.php)
- Cómo se informa, límites · límite de asimetría del oVEMP aéreo 34 % (media + 2 DE, 500 Hz a 95 dB nHL, 50 sujetos) · (Piker y cols., 2011) · doi:10.3766/jaaa.22.4.5 · PMID 21586257 · nueva sí

## Corregidas (la literatura dice otra cosa)
- Un potencial que es una pausa · "guíate por la latencia, que es siempre la misma" → "que no cambia con la forma de dibujar" · la latencia depende de la forma y del tiempo de subida del estímulo (Rosengren y cols., 2019; el mismo capítulo lo dice en "Contra qué se compara")
- Tabla de parámetros, filtros · "dejan pasar el EMG (40 a 60 Hz en el cuello, unos 100 Hz bajo el ojo)" → "dejan pasar la respuesta (su energía está hacia los 40 Hz en el cuello y los 100 Hz bajo el ojo)" · Rosengren y cols. (2019): "the oVEMP has higher frequency content than the cVEMP (around 100 Hz vs 40 Hz)"; es contenido de la respuesta, no del EMG, y no da 40-60
- Lo que dicen las normas (oVEMP) · "la falta de mirada hacia arriba es una causa frecuente de oVEMP ausente en adultos mayores" → "puede explicar malos resultados en adultos mayores y en pacientes con parálisis de la mirada" · Rosengren y cols. (2019): "can contribute to poor results in elderly patients and those with gaze palsies"
- Errores frecuentes · "Mirada insuficiente... Es la causa más frecuente de un oVEMP chico o ausente" → "Da un oVEMP chico o ausente (Rosengren y cols., 2019)" · la fuente la da como causa, no como la más frecuente

## Quitadas o reformuladas (sin respaldo)
- ¿Sabías que? · "en pacientes operados" → "antes y después de una sección del nervio vestibular": la carta de 1992 no tiene resumen y no se pudo leer; no se pudo confirmar cuántos pacientes eran
- Dos reflejos, cVEMP · "motoneuronas del nervio accesorio" → "motoneuronas que mueven el ECM" (con Kushiro 1999); se resolvió y retiró el verificar
- Paso 3 · "el músculo recupera la fuerza al doble de la velocidad con que la pierde" se dejó como dato del simulador ("en el simulador"): es `RECUPERACION` de LabSim (docs/decisiones.md, VEMP v2), no un dato fisiológico

## Quedan `verificar`
- Requisitos · suspensión de supresores vestibulares 48 h antes: sin fuente propia del VEMP (no se tocó; es práctica del autor)
- Contra qué se compara · origen de la tabla de valores normales de LabSim (resources/vemp/normative_data.json no declara fuente ni DE)

## Para el autor (práctica que choca con la literatura, no editada)
- Tabla de parámetros · ganancia del oVEMP 10.000 · Rosengren y cols. (2019) recomiendan 20.000 para el oVEMP · doi:10.1016/j.cnp.2019.01.005
- Montaje oVEMP · el comentario ya explica la referencia en el mentón; Piker y cols. (2011) cuantifican que la referencia infraorbitaria "contamina" y baja la amplitud ~30 % (18-43 %); podría sumarse al recuadro si el autor quiere
- Cómo se informa · límite 33 % del oVEMP: ahora con Piker 2011 (34 %) en el recuadro; no se cambió la cifra del protocolo

## Referencias de la lista con problemas
- Ninguna. Se verificaron en Crossref/PubMed: Papathanasiou 2014, Rosengren 2010 y 2019, Welgampola y Colebatch 2001 y 2005, Todd 2007, Iwasaki 2007, Colebatch 1994, Lim 1995 (Crossref escribe "Lee Lim" como apellido; se dejó Lim CL), McCaslin 2014, Colebatch y Halmagyi 1992, Curthoys 2010 y 2012 (PMID 22500066), Zhou 2012.
