# H21 completar: software de adaptación/métodos prescriptivos y conectividad

Archivo: docs/libro/capitulos/H21-prueba-de-audifonos.md (solo ese; sin SVG nuevo). Dos subsecciones nuevas:
- "El software de adaptación en la práctica" (tras "Los métodos prescriptivos, como concepto").
- "Conectividad: protocolos, latencia y pila" (tras la tecnología, antes del molde).
Armado `hacer_libro.py H21 --sin-completo` OK; revisadas págs. 3-8 (tablas H21.1-H21.3 bien). Sin commit.
Verificación: abstracts PubMed (efetch) y Crossref; Keidser 2011 en texto completo (PMC4627149); AAA 2013 PDF leído (RECD); página de LE Audio del Bluetooth SIG leída.

## Afirmación -> referencia -> verificación
- NAL-NL2 usa edad, sexo, experiencia, idioma; 2 versiones (tonal: más graves); sexo ~2 dB; usuarios nuevos con pérdida moderada prefieren menos ganancia, adaptación gradual, ~2 años (muestra pequeña); niños más ganancia en entradas bajas; objetivos para 50/65/80 dB SPL; maximiza inteligibilidad con tope de sonoridad -> Keidser 2011 (doi:10.4081/audiores.2011.e24) -> texto completo PMC.
- DSL v5: audibilidad, evitar molestia, diferencias adulto-niño -> Scollie 2005 -> abstract PMID 16424945.
- RECD (definición, depende de edad y molde, valor medido o promedio por edad, repetir con cada molde nuevo, método pediátrico validado, conversión de umbrales con fonos de inserción) -> AAA 2013 -> PDF leído; Bagatto 2005 (abstract PMID 16424946).
- Primera adaptación: 64 % de 42 oídos a >10 dB del objetivo (NAL-NL1, 4 tipos de audífono); 83 % tras ajustar -> Aazh y Moore 2007 -> abstract PMID 18326152. Menos ganancia/salida en agudos con first-fit -> Valente 2018 (introducción). ECA 24 adultos: +15 % palabras / 7,7 % fonemas a 50 dB SPL, +4 % a 65, 79 % prefirió, sin diferencia HINT/SSQ -> Valente 2018 (PMID 30222541). Meta-análisis DME 0,59 (silencio), 0,15 (ruido), importancia clínica incierta -> Almufarrij 2021 (PMID 33899603).
- Aclimatación: mejora hasta 10 semanas -> Cox y Alexander 1992 (PMID 1397752); 6-12 semanas y cuestiona evaluaciones comparativas de corto plazo -> Gatehouse 1992 (PMID 1401514).
- NAL-NL2 vs DSL v5: sonoridad ~8 sones vs 18,6 normal, inteligibilidad predicha similar (DSL m[i/o] = algoritmo de DSL v5) -> Johnson y Dillon 2011 (PMID 21993050); sin diferencias SRT/APHAB, 43 pacientes retrospectivo -> Portelli 2024 (PMID 38546852); fórmulas pediátricas difieren 6-25 dB -> Pittman y Stewart 2023 (PMID 37254534); niños: DSL v4.1 para habla suave, NAL-NL1 para reducir ruido -> Scollie 2010 (PMID 20109089). Nota: Scollie 2016 y Johnson 2017 no se usaron (no se hallaron/necesitaron).
- Retardo: 3-5 ms notado 76 %, >10 ms objetable 90 % -> Agnew y Thornton 2000 (PMID 10858005); 20-30 ms "molesto" en simulación -> Stone y Moore 1999 (PMID 10386846); 14-30 ms aceptable -> Stone y Moore 2005 (PMID 15809547); abierto ~5-6 ms -> Stone y cols. 2008 (PMID 18469715).
- Asincronía natural audio-labios: 20 ms adelanto a 70 ms atraso (sílabas), 40/200 ms (material complejo) -> Schwartz y Savariaux 2014 (PMID 25079216). Se usa solo como referencia del habla natural, no como umbral perceptivo.
- Streaming bilateral > unilateral; ventaja sobre teléfono acústico solo con domos oclusivos -> Picou y Ricketts 2011 (PMID 20808225).
- LE Audio: radio LE vs Classic, LC3 con 50 % menos tasa que SBC, multi-flujo, difusión a receptores ilimitados, soporte de audífonos -> página LE Audio del Bluetooth SIG (leída 2026-10-19, sin fecha de publicación).
- Streaming en adolescentes: +2 h/día de uso, problemas de pila, conexión y compatibilidad -> Gross 2026 (PMID 41982943).
- Telebobina e IEC 60118-4: ya estaban en el capítulo (NIDCD 2019, IEC 2014).

## verificar abiertos (comentarios HTML en el .md)
1. Efecto de uni/bilateral sobre el objetivo (Keidser 2011 no lo detalla).
2. Que el programa admita LDL medido y cómo NAL-NL2 deriva el MPO (leer manuales de los métodos).
3. Por qué la primera adaptación queda bajo el objetivo (causa no cuantificada; propuestas: acústica promedio, ganancia reducida a propósito).
4. Tabla "De la queja a lo que se revisa": práctica clínica sin fuente única (Dillon 2012, ajuste fino).
5. NFMI y radio 2,4 GHz propietaria: sin fuente primaria cotejada (descripción mínima).
6. Cuántos audífonos usan Bluetooth clásico directo vs accesorio.
7. Cifras de latencia de streaming (Bluetooth clásico, LE Audio) y umbrales ITU-R BT.1359: no obtenidas, por eso no se dan cifras.
8. "Un cambio de teléfono/versión puede cortar la conexión" (compatibilidad), sin fuente.
Los verificar previos del capítulo (Canadian Audiologist 2024 para LE Audio 5.2, etc.) no se tocaron.

## Discrepancias con el protocolo
Ninguna nueva. El ojo clínico ya existente (comodidad no es criterio) queda reforzado por la nueva sección.
