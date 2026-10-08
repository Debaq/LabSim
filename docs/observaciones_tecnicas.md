# Observaciones: técnicas de audiometría frente a la literatura

Lo que la investigación del 2026-10-08 encontró distinto de las técnicas
T00, T01 y T02 (`Bibliografia::TECNICAS`), o que no se pudo verificar. Es
para investigarlo después; las técnicas no cambian por esto. Lo que sí
coincide quedó como fuente de cada paso en la Bibliografía.

Informe completo, con citas textuales y la tabla paso a paso:
`docs/investigacion/tecnica_audiometria_tonal/informe.md`. Notas por tema:
`docs/investigacion/tecnica_audiometria_tonal/notas/`.

## Pasos que las fuentes hacen distinto

### T01: umbrales aéreos

- **Frecuencia nueva 10 dB sobre el umbral anterior.** Ninguna fuente usa
  +10. BSA 2018 §6.7.5: "clearly audible level (e.g. 30 dB above the
  adjacent threshold)". ISO 1989: "estimated audible level, as indicated by
  the previous responses". ASHA 2005 parte "well below the expected
  threshold" en todas las frecuencias. Las ISP no lo mencionan.
- **Tolerancia de la repetición de 1 kHz: 10 dB.** ASHA, BSA, ISO 1989 y
  Gelfand usan 5 dB. Qué hacen si se pasa:
  - ASHA acepta el menor y re-mide al menos otra frecuencia;
  - BSA investiga la causa y puede repetir el oído completo;
  - ISO 1989 re-mide frecuencias hasta que concuerden a 5 dB.

  Las únicas reglas de "más de 10 dB" encontradas son de otra cosa: en la
  ISO 1989 §6.2.4.1, la dispersión de respuestas dentro de una frecuencia;
  en la ISP 2018 §2.1, la calibración subjetiva del audiómetro. Como
  contexto, Mahomed et al. 2013 dan una diferencia test-retest manual de
  1,3 dB (DE 6,1).
- **Repetición de 1 kHz en el segundo oído.** ASHA y BSA dicen que
  normalmente no hace falta. La técnica la hace en los dos, y el indicador
  la exige en los dos.
- **Dónde va la repetición de 1 kHz.** ASHA la hace después de 8 kHz y
  antes de 500 Hz; BSA e ISO 1989, al final, como la técnica.
- **Familiarización.** ISO 1989 (nota optativa), ISP 2018 e ISP 2012:
  40 dB, bajar de 20 en 20 hasta que no responda, subir de 10 en 10 y
  confirmar al mismo nivel. ASHA: 30 dB HL; si no responde, 50 dB y luego
  +10. BSA coincide con la técnica y agrega un tope de 80 dB HL. La ISP 2012
  la reserva para el primer examen o si no comprende, y la excluye en
  sorderas profundas y sospecha de pseudohipoacusia. La frase de la ISP 2018
  "a 20 dB del nivel más bajo" no dice si es por encima o por debajo.
- **Criterio.** BSA acepta 2 de 2, 3 o 4 (50 % o más); la técnica pide la
  mayoría (2 de 4 no cierra). Según Gelfand, Carhart y Jerger exigían 3
  respuestas. No se encontró ningún estudio que compare 2/3 con 3/5.
- **Intervalo entre estímulos.** ASHA, BSA e ISO 1989 piden variarlo (no
  menor que el tono) para que el paciente no lo anticipe. La técnica no lo
  dice y el indicador no lo mide.
- **Duración.** BSA usa 1 a 3 s variables; ASHA, ISO 1989 e ISP, 1 a 2 s
  como la técnica.
- **125 Hz.** ASHA la mide solo con pérdida en graves. La ISP 2018
  (vigilancia) no la incluye. BSA mide 3 y 6 kHz solo "where needed".
- **Por qué empezar por 1 kHz.** No se encontró justificación publicada ni
  estudios sobre efectos del orden. ASHA dice que el orden no influye
  significativamente en el resultado y que sirve para la consistencia.

### T02: umbrales óseos

- **Al final de la batería.** ISP 2012, NTP 285, INGESA y el protocolo TRTT
  la ponen justo después de la aérea. Las reglas de enmascaramiento de
  Yacullo (2000) usan la ósea del oído no evaluado para enmascarar la
  logoaudiometría y la vía aérea. Decisión docente: va al final para hacer
  primero todo lo que va con fonos y cambiar el transductor una sola vez.
  Sin datos: si las supraliminares o la tinnitumetría a niveles altos
  pueden dejar un cambio temporal de umbral que empeore la ósea medida
  después. No se encontró literatura.
- **Rango 250 Hz a 4 kHz.** BSA 2018 §7.2 y §7.7: normalmente 500–2000 Hz.
  Bajo 500 Hz el umbral puede ser un armónico del vibrador; sobre 2000 Hz,
  solo en circunstancias excepcionales. Según BSA §7.6, el umbral
  vibrotáctil mastoideo es 25 dB a 250 Hz. Chordekar et al. 2026 (1000
  oídos): gaps falsos en el 43,5 % a 250 Hz y el 13,9 % a 4 kHz; concluyen
  que 250 Hz de rutina no aporta en adultos. Stenfelt y Wiman 2026: gaps
  sistemáticos a 250 y 500 Hz por distorsión y respuestas vibrotáctiles.
  De ambos estudios solo se leyó el resumen.
- **Repetición de 1 kHz.** BSA §7.2: "No retest is required at 1000 Hz" en
  vía ósea. ASHA la intercala antes de 500 Hz.
- **Frecuencia nueva.** BSA §7.3 toma como referencia del inicio el umbral
  aéreo de esa frecuencia, no el óseo de la anterior.
- **No tomarla en el oído sano.** La NTP 285 pone el corte en una vía aérea
  sobre 25 dB; el indicador usa 20 dB HL (configurable por curso). La ISP
  2012, INGESA y TRTT la piden en ambos oídos. ASHA dice "as needed", sin
  corte.
- **Por qué oído partir.** INGESA parte la ósea por el oído mejor.
- **"Luego el otro oído".** Con atenuación interaural cercana a 0 dB, la
  ósea sin enmascarar no distingue qué oído responde (BSA §7, §8.1). Queda
  para cuando el enmascaramiento sea regla (TODO 62).

### T00: orden de la batería

- Ninguna norma fija el orden completo. La ISO 2010 §4.1 solo pone la aérea
  antes que la ósea.
- TRTT (NCT01177137) es el único orden completo encontrado:
  1. tonal (aérea y ósea);
  2. SRT;
  3. tono y sonoridad del acúfeno;
  4. LDL;
  5. reconocimiento de palabras;
  6. OEA;
  7. inmitancia.
- BSA 2022 pide la LDL solo cuando está indicada.
- No se encontraron fuentes sobre dónde van el SISI, el ABLB, el tone decay
  y el Stenger dentro de la batería.
- ISO 2010 y BSA piden una pausa pasados unos 20 minutos de examen.

## Fuentes que no se pudieron leer

- ISO 8253-1:2010, cláusulas 6.2 (procedimiento manual) y 8 (vía ósea): de
  pago. La ISP 2018 cita su familiarización (6.2.2), lo que sugiere que
  mantiene la de 1989.
- ANSI/ASA S3.21-2004: de pago. Solo se le atribuye el mínimo de 2 de 3, vía
  ASHA.
- Carhart y Jerger 1959 (J Speech Hear Disord 24:330-345) y Hughson y
  Westlake 1944: solo a través de Jerger 2018 y Gelfand.
- NCh 2573/1: citada por la ISP 2012 para la familiarización;
  probablemente es la ISO 8253-1 adoptada en Chile. No se encontró el texto.
- AEDA 2002, "Normalización de las pruebas audiológicas (I): la audiometría
  tonal liminar" (Auditio 1): solo hay una copia en Scribd, bloqueada.
- Guías GES 56 y 59 (MINSAL): el servidor rechazó la conexión.
- Alegría, Navarrete, Papic y Salazar Bugueño (2005), "Comparación de
  metodología ascendente y descendente para la búsqueda de umbral en
  audiometría tonal", tesis de la U. de Chile: el repositorio bloqueó el
  PDF. Es la única evidencia empírica chilena identificada.
- Manuales de referencia: Katz 7.ª ed., Martin y Clark, Roeser, y Salesa,
  Perelló y Bonavida (Tratado de audiología, 2.ª ed.). Solo se encontraron
  sus registros.
- Estudios sobre la dirección de la búsqueda y el tamaño del paso: Tyler y
  Wood 1980, Marshall y Jesteadt 1986, entre otros. Solo se vieron títulos.
- Colombia (GATI-HNIR, Res. 2400) y México (NOM-011-STPS): no se obtuvieron
  los textos.
- Vigencia de la §2 (evaluación médico-legal) de la ISP 2012 y la URL
  oficial de la ISP 2018 en ispch.cl.
