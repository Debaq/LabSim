# Fichas de técnica pendientes

Borrador para que el docente lo corrija antes de escribir reglas. Cada ficha sigue el formato de T03 (tinnitumetría) en `labsim_backend/src/Bibliografia.php`: pasos cortos, cada uno verificable con lo que registra la app, más **lo que debería anotar** (el alumno informa por escrito y el sistema deduce el valor esperado desde las respuestas del paciente).

La técnica sale del libro (capítulos H, `libro-orl/texto/capitulos/`). El protocolo técnico ORL 2019 solo manda en el **procedimiento general de atención**, que el libro no cubre; en las demás fichas aparece cuando el libro mismo lo cita (partida del reflejo en 80 dB, SRT ascendente) o como respaldo. Lo que no dice ni el libro ni el protocolo va marcado **(propuesto)**.

Marcas al final de cada paso:
- **[registrado]**: ya está en `action_logs`; se puede escribir la regla.
- **[desde el informe]**: se verifica con lo que sube el informe del equipo (`reports`).
- **[en el chat]**: se verifica leyendo la conversación con el paciente (`llm_chat_logs`), con un LLM.
- **[falta registro: …]**: hay que agregar el registro en la app antes de evaluarlo.
- **(lector pendiente)**: el dato está en `action_logs` pero `AudiometriaRegistro.php` todavía no lo interpreta.

Ya evaluadas hoy (no van aquí): T00 orden de las pruebas, T01 umbrales aéreos, T02 umbrales óseos, T03 tinnitumetría.

## Resumen

| Área | Fichas | Estado |
|---|---|---|
| Atención y anamnesis | Procedimiento general, anamnesis | La anamnesis y la presentación se leen en el chat con LLM (ya existe `OirsEvaluator` sobre el mismo chat). Consentimiento firmado, entrega al docente y salida: falta registro. |
| Oído | Otoscopía, acumetría, timpanometría y reflejos, decay del reflejo, ETF | Acumetría e impedanciometría: casi todo registrado. Otoscopía: falta inspección externa, palpación y recorrido de la membrana. |
| Audiometría | SDT, SRT, concordancia SRT-PTA, discriminación (UMD), LDL, Fowler, IWA, SISI, Carhart, Rosenberg, STAT, Stenger | Todo en `action_logs`; falta que el lector interprete logo, alternado, cronómetro e incrementos del SISI. Es lo más rápido de convertir en reglas. |
| Electrofisiología | EOA, tamizaje con OEA, ABR, AABR, ECochG, VEMP, ASSR, MLR, CAEP, MMN/P300 | ABR y los que comparten su informe: se evalúan **desde el informe** (impedancias, montaje, FSP, réplica). EOA, VEMP y ASSR: solo resultados, falta registro de la técnica. |
| Rinología y sueño | Rinoscopía, rinomanometría, rinometría acústica, olfatometría, prick, espirometría, PSG/poligrafía, CPAP | La mayoría registrado (`ra_`, `rm_`, `olf_`, `prick_`, `esp_`, `psg_`, `cpap_`). Rinoscopía casi sin registro (solo `rs_mirada`). Faltan instrucciones al paciente, fármacos y contraindicaciones. |

Orden sugerido para escribir reglas:
1. Audiometría restante.
2. Acumetría e impedanciometría.
3. Anamnesis con LLM.
4. Rinología.
5. ABR desde el informe.
6. Lo que necesita registro nuevo: otoscopía completa, EOA, VEMP, procedimiento general.

---

## 1. Atención y anamnesis

### Procedimiento general de atención (fuente: protocolo.txt "Protocolo de atención al paciente – estudiantes"; H01 §El paciente)
- Resumen: antes y después del examen hay pasos fijos: presentarse, explicar, pedir consentimiento y cerrar con el docente.
- Pasos:
  1. Se verifica si el paciente es nuevo o ya tiene ficha, y se tiene la ficha si hay atenciones previas. [falta registro: apertura de la ficha antes de examinar]
  2. Se saluda, se hace sentar al paciente y el estudiante se presenta como estudiante de la carrera, diciendo que examina bajo supervisión de un docente, a quien presenta. [en el chat: lo puede marcar el LLM de la anamnesis]
  3. Se entrega el consentimiento informado y se refuerzan 4 ideas: examina un estudiante supervisado, no hay riesgo (no son invasivos), los resultados pueden usarse en investigación bajo anonimato, y en qué consiste el examen. [en el chat, si lo dice conversando: LLM; la firma, falta registro]
  4. Si el paciente es menor, lo acompaña su tutor, que firma con nombre y RUT. [falta registro; hay edad en el caso, pero no la firma del tutor]
  5. Antes de cada examen se explica al paciente qué se hará, con lenguaje simple, y se le pide avisar si hay molestia (consentimiento verbal, H01). [registrado en parte: ot_instruccion, ac_instruccion y z_instruccion registran las frases del talkback; no hay una instrucción general]
  6. Se hace la anamnesis según la prueba (la ve otra ficha). [fuera de esta ficha]
  7. Al terminar se explica al paciente qué sigue y se presentan los exámenes al docente antes de que el paciente se vaya; no hacerlo es "falta grave" según el protocolo. [en el chat lo que le explica al paciente; la entrega al docente, falta registro]
  8. Se acompaña al paciente a la salida y se verifica que no quede un accesorio olvidado (audífonos, aros, lentes). [falta registro; (propuesto) un check al cerrar la atención]
- Lo que debería anotar: nada propio del examen. Sería ficha con consentimiento verificado y quién supervisó (propuesto).
- Dudas para el docente:
  1. ¿Se evalúa con un check manual al finalizar o con botones de la app ("me presenté", "consentimiento firmado")?
  2. ¿Cuenta el consentimiento verbal del libro (H01) o el escrito del protocolo? El libro dice verbal en no invasivos.
  3. ¿"Presentar los exámenes al docente" se puede deducir de que el informe quede guardado?


### Anamnesis (fuente: H01 §La anamnesis, §De la anamnesis a las hipótesis, §Cómo se informa, §Errores frecuentes; protocolo 2019 §ANAMNESIS y §PROTOCOLO DE ATENCIÓN)
- Resumen: la entrevista con el paciente (y su acompañante) en el chat; se evalúa con un LLM que lee la transcripción contra la ficha del caso.
- Dónde se mide: `llm_chat_logs` (transcripción completa, con `speaker_label` cuando hay acompañantes). Ya existe un evaluador con LLM sobre el mismo chat, `OirsEvaluator`: juzga el **trato**, no el contenido. La anamnesis sería un segundo evaluador sobre el contenido clínico, con el mismo patrón: al cerrar la atención, una sola vez, de manera best-effort y respondiendo un JSON.
- Pasos (cada uno sería una regla que el LLM marca cumple/no cumple con una cita de la transcripción como detalle):
  1. Se presenta como estudiante y explica en qué consiste el examen (protocolo §Atención). [en el chat]
  2. Empieza con una pregunta abierta sobre el motivo de consulta, y las preguntas cerradas van después. [en el chat]
  3. Pregunta el motivo de consulta y quién lo deriva. [en el chat]
  4. Pregunta el tiempo de evolución, la forma de inicio (súbita, progresiva o fluctuante) y el lado. [en el chat]
  5. Pregunta por el acúfeno: lado, si es permanente u ocasional, y **si lo tiene ahora**. [en el chat]
  6. Pregunta por vértigo, otalgia, otorrea y plenitud. [en el chat]
  7. Pregunta por intolerancia a los sonidos, autofonía, diploacusia y dificultad en ruido (propuesto: solo si el caso tiene alguno, para no exigir el interrogatorio completo). [en el chat]
  8. Pregunta los antecedentes otológicos: otitis, perforación, cirugía, audífonos y exámenes anteriores. [en el chat]
  9. Pregunta los antecedentes mórbidos y los fármacos, en especial los ototóxicos (y los anticoagulantes si hay tapón). [en el chat]
  10. Pregunta por exposición a ruido, laboral y recreativa: horas, años y protección. [en el chat]
  11. Pregunta por antecedentes familiares de hipoacusia. [en el chat]
  12. En lactantes y niños: pregunta los indicadores de riesgo (gestación, peso, parto, UCI neonatal, tamizaje, lenguaje), dirigidos al acompañante. [en el chat]
  13. Le habla al paciente cuando puede contestar, y al acompañante cuando la historia la sabe él. [en el chat, con `speaker_label`]
  14. No se queda solo en preguntas cerradas, como si leyera un interrogatorio (H01 §Errores). [en el chat]
- Cobertura de la ficha (lo que más vale): el LLM recibe la `Anamnesis` del caso y marca qué datos **clave** obtuvo el alumno y cuáles quedaron sin preguntar. Por ejemplo: "no supo que el acúfeno estaba presente hoy", "no preguntó cirugía de oído y el paciente tenía una". El porcentaje sale de los datos clave obtenidos, y el docente ve la lista.
- Lo que debería anotar: el LLM redacta la anamnesis **tal como quedaría con lo que el paciente le contó en el chat**, ordenada como en H01 §Cómo se informa (motivo, evolución, síntomas, antecedentes otológicos, mórbidos, fármacos, ruido, familia, perinatales). Lo que no preguntó **no** aparece como negativo. El docente la ve al lado de la ficha del caso, igual que la tabla de la tinnitumetría.
- Lo que no se puede medir en el chat: la **observación** (cómo lo oye, malformaciones, actitud) y el paso de la anamnesis a las hipótesis (H01 §De la anamnesis a las hipótesis). Son escritas. Lo de las hipótesis se podría pedir como respuesta corta en la app (propuesto).
- Dudas para el docente:
  1. ¿Es obligatorio preguntar todo el listado de síntomas (paso 7), o solo lo que corresponde al motivo de consulta?
  2. ¿Pesa la cobertura de datos clave igual que los pasos de forma (pregunta abierta, presentarse), o más?
  3. ¿El docente quiere poder corregir el veredicto del LLM regla por regla (anularlo), como ya puede comentar el chat?

---

## 2. Oído: otoscopía, acumetría e impedanciometría

Fuente: libro H01, H02, H07 y protocolo.txt. Lo que no dice el libro va marcado "(propuesto)". Registros leídos en src/audiometria/Otoscopia.py, Acumetria.py y src/impedanciometria/Z.py.


### Otoscopía (fuente: H01 §La otoscopía, §Cuándo no seguir, §Cómo se informa)
- Resumen: inspección externa, tracción del pabellón, espéculo adecuado, recorrido ordenado del conducto y la membrana, y registro por oído.
- Pasos:
  1. Antes de empezar se explica el examen y se pide avisar si hay dolor. [registrado: ot_instruccion]
  2. Se mira por fuera pabellón, surco retroauricular y entrada del conducto, y se palpa la mastoides. [falta registro: no hay acción de inspección externa ni palpación]
  3. Se tracciona el pabellón con suavidad y se presiona el trago; si duele, se sospecha otitis externa. [registrado en parte: ot_traccion (oído, arriba_cm, atras_cm, calidad); presión del trago no]
  4. Se empieza por el oído que menos probablemente esté alterado, según la anamnesis (si el izquierdo supura, primero el derecho). [registrado: orden de los ot_otoscopio por oído; falta comparar con el motivo de consulta del caso]
  5. Se elige el espéculo más grande que entre cómodo. [registrado: ot_especulo y ot_especulo_grande]
  6. La tracción es según la edad (adulto arriba y atrás) y se hace antes de entrar y se mantiene al entrar, sin llegar a la porción ósea. [registrado: ot_otoscopio con traccion, traccion_correcta, traccion_calidad, edad; ot_soltar]
  7. Se recorre el conducto y luego la membrana en orden fijo: referencias, cuadrantes, pars flácida. [falta registro: no se registra el recorrido ni la inspección]
  8. Se retira, se cambia el espéculo (nuevo si hubo infección) y se repite en el otro oído. [falta registro de cambio de espéculo entre oídos; (propuesto)]
  9. Ante dolor, sangre, mareo o hallazgo de derivación (otorrea, cuerpo extraño, tapón oclusivo, abombamiento) el alumno se detiene, no sigue con exámenes que pongan algo en el conducto y lo comunica. [falta registro: sí se puede cruzar el hallazgo del caso con exámenes posteriores (z_*, audiometría con inserción)]
  10. Se registra por oído, conducto y luego membrana, antes del siguiente examen. [falta registro: el informe escrito]
- Lo que debería anotar: por oído, conducto (cerumen, permeabilidad, piel) y membrana (integridad, posición, color, transparencia, referencias, placas/cicatrices, detrás). Si no se vio la membrana: "no visible por tapón", no "normal". Impresión diagnóstica aparte, como "sugerente de". El sistema deduce el valor esperado de la ficha del caso y las fotos.
- Dudas para el docente:
  1. ¿Se exige inspección externa y palpación como acción registrable, o basta con anotarlas en el informe?
  2. ¿Cómo se evalúa "empezar por el oído menos alterado" si el caso no tiene lado sintomático?
  3. ¿Se evalúa que no se siga con otros exámenes tras un hallazgo de derivación?


### Acumetría (fuente: H02 §Antes de empezar, §Paso a paso, §Cómo se informa, §Errores frecuentes)
- Nota: en prod también aparecen las acciones `ac_rinne_mastoides`, `ac_rinne_pabellon`, `ac_rinne_comparar` y `ac_weber`; el agente no las encontró en el código actual (puede ser una versión anterior de la app). Revisar antes de escribir reglas.
- Resumen: diapasón de 512 Hz, Weber primero y Rinne por oído empezando por el oído al que fue el Weber.
- Pasos:
  1. Se usa el diapasón de 512 Hz y se golpea tomado por el mango, una rama a dos tercios desde la base, contra algo acolchado, nunca contra la mesa. [registrado: ac_cambiar_diapason, ac_golpe (hz); el sitio del golpe y el armónico "Diapasón sonando con armónicos" se detectan en la app, pero falta confirmar que se registre]
  2. Se dan instrucciones claras: solo debe decir dónde lo oye o dónde más fuerte. [registrado: ac_instruccion (avise_si_escucha, avise_cuando_deje, compare_sonidos, diga_donde)]
  3. Weber primero: base en la línea media (frente, vértex, puente nasal o mentón), contrapresión atrás, hasta unos 4 s, y se pregunta dónde lo escucha. [registrado: ac_apoyo con zona linea_media y fuera_de_linea, desde_golpe_s, weber; ac_pregunta; falta confirmar el registro de la contrapresión]
  4. Rinne empieza por el oído al que lateralizó el Weber. [registrado: orden de ac_apoyo por oído, con weber previo]
  5. Rinne en aire: ramas a unos 25 mm de la entrada del conducto, alineadas con él, unos 2 s. [registrado: ac_apoyo zona pabellon con distancia_mm]
  6. Sin tocar las ramas, base firme en la mastoides, sin pelo, con contrapresión, otros 2 s. [registrado: ac_apoyo zona mastoides; falta registrar pelo y contrapresión]
  7. Se pregunta "dónde más fuerte, adelante o atrás", no "¿lo oye?". [registrado: ac_pregunta con la clave de la pregunta]
  8. Se repite en el otro oído. [registrado: ac_apoyo con oído]
  9. Si hay Rinne negativo en el oído contrario al Weber, se pregunta en qué oído oyó el diapasón en la mastoides, para detectar un falso negativo. [registrado en parte: ac_pregunta; falta clave si existe una pregunta "en qué oído"]
  10. El diapasón suena el tiempo necesario: el sistema avisa cuando el paciente "ya no lo escucha". [registrado: ac_deja_de_oir]
  11. Schwabach y Bing (opcionales; el libro los llama de apoyo y dice que hoy se piden menos). [falta registro: la app solo trae las zonas mastoides, pabellón y línea media; el Bing requiere ocluir el trago y el Schwabach pasar a la mastoides del examinador]
- Lo que debería anotar: frecuencia del diapasón (512 Hz); Weber (lateraliza a OD/OI, no lateraliza o "no lo oye"); Rinne por oído con (+), (−) o "falso (−)", rojo OD y azul OI. Ejemplo del libro: "Weber lateraliza al OD. Rinne negativo en el OD y positivo en el OI. Sugerente de componente conductivo en el OD; se complementa con audiometría tonal". El valor esperado sale de modelo.weber() y modelo.rinne() del caso (campos weber y rinne en ac_apoyo). El falso negativo se debe informar como tal: Weber al oído bueno con Rinne negativo en el malo no es conductiva.
- Dudas para el docente:
  1. ¿Se evalúan Schwabach y Bing? La app hoy no los permite.
  2. ¿Se exige un orden de Weber en la frente o vale cualquier sitio de la línea media?
  3. ¿Se evalúa la duración (2 s por posición, 4 s en Weber) o solo el orden y el sitio?


### Impedanciometría: timpanometría y reflejos (fuente: H07 §Antes de empezar, §Paso a paso 1-4, §El reflejo: umbral y Metz)
- Resumen: otoscopía antes de poner la sonda, timpanograma de 226 Hz y reflejos ipsi y contralaterales a la presión del pico, oído por oído.
- Pasos:
  1. Otoscopía primero: ella decide si se pone la sonda. No se mide con otorrea, otitis media aguda, otitis externa, cuerpo extraño, tapón impactado o atresia; en ese oído se informa "No realizable" con el motivo. [registrado: z_no_realizable; la otoscopía previa se puede cruzar con ot_otoscopio]
  2. Se pregunta por acúfeno que empeora con el ruido o molestia a sonidos fuertes antes de los reflejos. [falta registro: sin anamnesis específica]
  3. Se dan las instrucciones (se tapa y destapa, sonidos fuertes, no hablar ni tragar), se muestra la sonda y se dice por qué oído se empieza. [registrado: z_instruccion]
  4. Se empieza por el oído derecho. [registrado: z_side_change y el lado de z_stimulus_click]
  5. Se elige oliva que selle sin presión y se tracciona el pabellón, apuntando al tímpano; el fono contralateral va en el otro oído desde el principio. [falta registro: los z_* no registran oliva ni tracción]
  6. Timpanometría de 226 Hz: barrido de +200 a −300/−400 daPa, o −600 para un pico muy negativo; el barrido se repite si la curva es plana o rara. [registrado: z_stimulus_click screen tymp; z_probe_freq_change; z_dial_change leak (fuga); z_pressure_change]
  3b. El paciente no traga ni habla durante el barrido. [falta registro: no hay forma de saber si el paciente se movió]
  7. Reflejos sin sacar la sonda, a la presión del pico: ipsilateral primero en 500, 1000, 2000 y 4000 Hz; luego contralateral en las mismas frecuencias más ruido. [registrado: z_reflex_mode_change, z_reflex_freq_change, z_stimulus_click]
  8. Se parte en 80 dB y se sube de 5 en 5 hasta ver la deflexión (protocolo ORL; la BSA parte más abajo). [registrado: z_dial_change reflex con dB]
  9. Presencia: deflexión de al menos 0,02 mL con forma típica; se sube 5 dB para confirmar que crece, y se baja 10 para comprobar que el umbral se repite. [registrado: la secuencia de dB en z_stimulus_click; falta registrar si el alumno marcó la deflexión (z_move_mark, para posición)]
  10. Tope de 105 dB HL con tonos y 95 dB SPL con ruido de banda ancha. [registrado: dB en z_dial_change]
  11. Se pasa al oído izquierdo (sonda al OI, fono al OD) y se repite todo. [registrado: z_side_change y la secuencia]
- Lo que debería anotar: por oído, volumen, compliancia, presión del pico y forma (tipo de Jerger); umbral del reflejo ipsi y contra por frecuencia en dB SPL (en este libro), anotando siempre los dos oídos ("tono OD, sonda OI"); Metz si la distancia con el umbral tonal es menor de 60 dB (restando la corrección HL/SPL); "No realizable" con motivo cuando corresponda. Un timpanograma plano se lee con el volumen (efusión frente a perforación).
- Dudas para el docente:
  1. ¿Se parte en 80 dB (protocolo ORL) o en 70/60 dB (BSA 2024)? El libro da ambos y la ficha debería fijar uno.
  2. ¿Se debe poder registrar la elección y la colocación de la oliva, o se asume bien puesta?
  3. ¿El umbral esperado del alumno se compara en dB SPL con tolerancia de 5 dB (paso del dial)?


### Impedanciometría: decay del reflejo (fuente: H07 §Paso a paso 5 y §Patrones de reflejo)
- Resumen: tono sostenido 10 s a 10 dB sobre el umbral del reflejo, contralateral, para ver si la contracción se mantiene.
- Pasos:
  1. Solo se hace si hay sospecha retrococlear y el reflejo está presente (sin reflejo no hay qué deteriorar). [falta registro: la sospecha viene de la anamnesis y el caso; sí se puede verificar que el umbral exista antes: z_stimulus_click]
  2. Se usa el modo contralateral. [registrado: z_reflex_mode_change, z_stimulus_click screen decay con mode]
  3. Frecuencias 500 y 1000 Hz (no sobre 1000 Hz: también decaen los oídos normales). [registrado: z_decay_freq_change, freq en z_stimulus_click]
  4. Intensidad 10 dB sobre el umbral del reflejo. [registrado: dB en z_stimulus_click y z_dial_change; se compara con el umbral del caso]
  5. Dura 10 s, con la instrucción "vas a escuchar un sonido fuerte un rato; quédate quieto". [registrado: z_instruccion; duración no, falta confirmar]
  6. Se interpreta: normal si se mantiene (la mayoría pierde menos del 10 % a los 10 s); positivo si cae a la mitad (50 %) o menos dentro de los 10 s. [registrado: la verdad está en el caso; el alumno lo anota en el informe]
- Lo que debería anotar: por frecuencia, (+) o (−) y el porcentaje de caída; el valor esperado sale de la curva del caso. Se distingue del ON-OFF, que habla del oído medio.
- Dudas para el docente:
  1. ¿Se exige que el alumno haga el decay en ambos oídos o solo donde el reflejo contralateral estaba presente y la sospecha?
  2. ¿Qué tolerancia se acepta sobre "10 dB sobre el umbral" (5 dB)?
  3. ¿Si el alumno hace decay sin sospecha ni reflejo, cuenta como error?


### Impedanciometría: función tubaria (ETF) (fuente: H07 §Paso a paso 6)
- Resumen: la prueba cambia según el estado de la membrana (íntegra o perforada/con tubo), que se decide con otoscopía y timpanograma.
- Pasos:
  1. Se elige la prueba según el estado de la membrana (íntegra o perforada/con tubo). [registrado: z_etf_prueba_change con prueba; se cruza con la ficha del caso]
  2. Membrana íntegra: timpanograma basal y luego una maniobra (Toynbee o Valsalva), con un timpanograma de control después de cada una. [registrado: z_etf_test con prueba integra y maniobra; z_stimulus_click tymp]
  3. En Toynbee el pico se corre a presiones negativas y en Valsalva a positivas; si vuelve a la presión inicial la función es buena (+); si no, se pide tragar varias veces: si vuelve, regular (+/−); si no se mueve, mala (−). [registrado: z_etf_test; el resultado es del caso]
  4. Variante de Williams: conducto a +400 y −400 daPa con deglución, y timpanograma tras cada una. [falta registro: confirmar si z_etf_test soporta Williams; solo aparecen "integra" y "perforada"]
  5. Perforada o con tubo: se lleva el conducto a −200 daPa y se pide tragar al menos 3 veces; si no compensa, Valsalva. Luego +200 daPa: si no se libera sola, 3 degluciones y, si tampoco, Toynbee. [registrado: z_etf_test prueba perforada con pressure; z_dial_change etf pressure]
  6. Se informan la presión inicial y la final, y la conclusión: buena, regular o mala. [registrado: la verdad está en el caso]
- Lo que debería anotar: tipo de prueba, presión inicial y final por maniobra y la conclusión (buena, regular, mala; o (+), (+/−), (−)). La función tubaria es un momento, no un estándar de oro; se informa junto con la clínica.
- Dudas para el docente:
  1. ¿Cuál enseña como principal con membrana íntegra: Toynbee/Valsalva o Williams?
  2. ¿Se pide el timpanograma de control después de cada maniobra, y cuántas degluciones antes de pasar a "regular"?
  3. ¿Qué hace el alumno con una membrana perforada que el caso no declara?

---

## 3. Audiometría

Nota de registro: la app ya emite audio_logo_response, audio_logo_reset, audio_cronometro, audio_alternate_toggle, audio_paciente_dice, audio_pulsatil_toggle, audio_no_realizable. AudiometriaRegistro.php hoy solo interpreta talkback, estímulo, canal, intensidad, frecuencia, salida, transductor, prueba y respuesta de mano. Donde digo [registrado] el dato está en action_logs; si el lector de línea de tiempo aún no lo interpreta, se marca "(lector pendiente)".

### Detección de la voz, SDT (fuente: H05 §1)
- Resumen: "pa pa pa" 10 dB bajo el mejor umbral tonal de 250 a 4.000 Hz, subiendo de 5 en 5 hasta que avise.
- Pasos:
  1. Tener el audiograma tonal hecho antes (T01). [registrado]
  2. Cambiar a Habla (prueba Logoaudiometría) y elegir el oído evaluado. [registrado: audio_stim_select, audio_output_select, audio_prueba_change]
  3. Dar la instrucción "Escuche mi voz" (levantar la mano apenas oiga la voz, aunque no entienda). [registrado: audio_talkback_press escuche_mi_voz]
  4. Presentar "pa pa pa" (botón de estímulo o talkback pa_pa_pa) partiendo 10 dB bajo el mejor umbral de 250 a 4.000 Hz. [registrado: audio_stim_button, audio_intensity_change]
  5. Subir de 5 en 5 dB hasta la respuesta. [registrado: audio_intensity_change + audio_respuesta]
  6. Enmascarar con ruido de habla en el oído contrario si voz − PTP óseo del no evaluado >= 45 dB. [registrado: canal 2 en SN/invertido y su intensidad]
- Lo que debería anotar: SDT en dB HL por oído = primer nivel en que el paciente levantó la mano; esperado cerca de (mejor umbral 250-4000 Hz) + 0 a 10 dB.
- Dudas: (1) pa_pa_pa se excluye de "instrucción vigente" en el backend; confirmar que el docente acepta pa_pa_pa suelto como estímulo y no como instrucción. (2) ¿Se exige instrucción antes del primer estímulo o basta el talkback "Escuche mi voz" en la sesión? (3) ¿El SDT se enmascara siempre o solo si cumple la regla (el libro dice solo si cumple)?

### SRT con palabras compuestas (fuente: H05 §2)
- Resumen: desde el SDT, de a 5 dB con dos palabras familiares por nivel; SRT = primer nivel con una de dos repetida.
- Pasos:
  1. Instrucción "Dictar palabras compuestas". [registrado: talkback dictar_compuestas]
  2. Partir del SDT (propuesto: no más de 10 dB sobre él). [registrado: audio_intensity_change]
  3. Dictar dos palabras compuestas por nivel; el alumno marca +1 por acierto. [registrado: audio_logo_response, audio_paciente_dice] (lector pendiente)
  4. Subir de 5 en 5 dB si no repite ninguna. [registrado]
  5. Detenerse en el primer nivel con una de las dos repetida. [registrado: audio_logo_response vs. nivel]
  6. Comparar con el PTP (ver concordancia) y enmascarar si cumple la regla de 45 dB. [registrado]
- Lo que debería anotar: SRT en dB HL por oído = primer nivel donde el paciente repitió al menos una de dos (deducible del modelo de logo en response.py).
- Dudas: (1) el libro admite ascendente (protocolo) y descendente (ASHA); la app solo soporta ascendente, ¿se acepta cualquier método? (2) con "una de dos" el SRT sale bajo el 50 %, ¿criterio de corrección exacto o con tolerancia de 5 dB? (3) ¿Se exigen palabras distintas por nivel?

### Concordancia SRT-PTA (fuente: H05 §3; H06 "Pérdida no orgánica")
- Resumen: el SRT debe caer a +-10 dB del PTP (en curva descendente, de los dos mejores umbrales de 500/1.000/2.000).
- Pasos:
  1. Tener SRT y audiograma del mismo oído. [registrado]
  2. Calcular PTP (promedio de 500, 1.000 y 2.000 Hz; dos mejores si la curva desciende). [registrado: audiograma guardado]
  3. Informar diferencia; si > 10 dB, repetir/revisar antes de seguir (fono corrido, instrucción, respuesta). (propuesto: revisar = repetir SRT o umbral) [registrado]
  4. SRT mucho mejor que el PTP: informar sospecha de pérdida no orgánica y pasar a Stenger si es unilateral. [registrado: pruebas posteriores]
- Lo que debería anotar: concordancia sí/no con la diferencia en dB; si el caso es no orgánico, "SRT mejor que PTP, sospecha no orgánica".
- Dudas: (1) ¿PTP de 3 frecuencias o de las dos mejores como regla fija? (2) ¿Qué se evalúa: que el alumno la informe o que repita algo cuando discordó? (3) cortes distintos con curvas en rampa.

### Discriminación / UMD (fuente: H05 §4)
- Resumen: lista de 25 bisílabos a SRT + 20; sube 5 dB con lista nueva hasta 92 %, máximo tres listas por oído.
- Pasos:
  1. Instrucción "Dictar palabras" (repetir aunque no esté seguro). [registrado: talkback dictar_palabras]
  2. Limpiar el contador antes de cada lista. [registrado: audio_logo_reset]
  3. Presentar 25 palabras a SRT + 20 dB, contando +1 solo por palabra completa y exacta. [registrado: audio_logo_response, audio_intensity_change]
  4. Si < 92 % (menos de 23/25), subir 5 dB y usar una lista distinta (no repetir). [registrado: audio_step_change/lista] (lector pendiente: identificar lista usada)
  5. Parar con >= 92 % o tras tres listas, sin pasar el LDL. [registrado]
  6. Si la discriminación es pobre para la pérdida o asimétrica, una lista más 15-20 dB sobre el máximo (roll-over), sin pasar el LDL. [registrado]
  7. Enmascarar con ruido de habla en el contrario, sonando toda la lista, si voz − óseo del no evaluado >= 45 dB, con el ruido entre mínimo y máximo. [registrado: canal 2]
- Lo que debería anotar: máximo % por oído y nivel en que se alcanzó; si hubo roll-over, índice = (máx − mín)/máx (corte orientativo 0,45); "máximo no alcanzado" si la curva sigue subiendo en la 3a lista; material (voz grabada) y si se enmascaró.
- Dudas: (1) la app ¿distingue listas distintas por nivel? (2) ¿Se exige buscar roll-over siempre o solo si la discriminación es pobre/asimétrica? (3) corte 0,45 vs 0,35 en el informe.

### LDL, umbral de molestia (fuente: H05 §6)
- Resumen: tonos cortos de 250 a 4.000 Hz desde 80 dB HL de 5 en 5 hasta que moleste; campo dinámico = LDL − umbral.
- Pasos:
  1. Instrucción "Pitos fuertes" (avisar apenas moleste, sin esperar a no aguantar). [registrado: talkback pitos_fuertes]
  2. Tonos cortos (< 1 s) por pulsos, no sostenidos. [registrado: audio_stim_button play/stop, duración]
  3. Partir en 80 dB HL. [registrado: audio_intensity_change]
  4. Subir de 5 en 5 hasta que avise o hasta el máximo. [registrado]
  5. Si hace un gesto/duda antes de avisar, detenerse y preguntar ("¿Molesta?", "Molesto ¿o?"). [registrado: talkback molesta/molesto_o]
  6. Repetir en cada frecuencia de 250 a 4.000 Hz (propuesto: ambos oídos). [registrado: audio_freq_change]
  7. Usar siempre la misma instrucción (no cambiar frase entre frecuencias). [registrado]
- Lo que debería anotar: LDL por frecuencia y oído = primer nivel en que respondió "molesta" (en la app es la tolerancia sorteada del paciente, 90-120); campo dinámico = LDL − umbral. "Solo si molesta" va a la misma prueba?
- Dudas: (1) "Solo si molesta" está en comandos_voz pero no aparece en PRUEBA: ¿es instrucción equivalente a "Pitos fuertes"? (2) ¿Se evalúa un orden (LDL antes de supraliminares, H06 dice "El LDL primero")? (3) límite de 80 dB HL: ¿penalizar partir distinto o el BSA a 60?

### Fowler / ABLB (fuente: H06 §Fowler)
- Resumen: compara sonoridad entre oídos en una frecuencia; referencia +20 dB y se iguala el oído en estudio de 5 en 5.
- Pasos:
  1. Verificar requisitos: referencia <= 20 dB HL, oído en estudio SNS sin gap, diferencia 20-40 dB, 250-4.000 Hz. [registrado: audiograma]
  2. Instrucción "Dos pitos" (decir si suenan igual o cuál más fuerte). [registrado: talkback dos_pitos]
  3. Dos canales, uno por oído, Tono y Alternado, partiendo en los umbrales. [registrado: audio_alternate_toggle, audio_output_select] (lector pendiente)
  4. Subir 20 dB la referencia y dejarla fija. [registrado]
  5. Subir el oído en estudio de 5 en 5 preguntando "¿Mismo volumen?" hasta que diga igual. [registrado: audio_intensity_change, talkback sonidos_iguales]
  6. Repetir subiendo la referencia de 20 en 20 hasta cerca del LDL o el máximo (sin pasar la molestia). [registrado]
  7. Preguntar por diploacusia ("¿Diferentes en forma?"). [registrado: talkback sonidos_distintos]
- Lo que debería anotar: pares de niveles igualados, tipo (sin reclutamiento / parcial / completo / sobrerreclutamiento) según se cierre o no la diferencia, y si hay diploacusia (según el caso del paciente).
- Dudas: (1) ¿"¿En qué oído?" forma parte de la técnica o es solo auxiliar? (2) la app ¿acepta pasos de 10 en la referencia? (3) ¿Fowler en una sola frecuencia basta o se piden dos?

### IWA, reclutamiento por vía ósea (fuente: H06 §IWA)
- Resumen: Weber audiométrico con vibrador en la frente subiendo hasta que se invierta.
- Pasos:
  1. Mismos requisitos que el Fowler. [registrado]
  2. Vibrador en la frente, tono a nivel umbral. [registrado: audio_output_select vibrador, talkback colocar_vibrador]
  3. Preguntar dónde lo escucha ("¿En qué oído?"). [registrado]
  4. Subir de 5 en 5 hasta que cambie o el máximo óseo. [registrado]
- Lo que debería anotar: lado donde lo oye en cada nivel y resultado (sin reclutamiento / centrado / sobrerreclutamiento).
- Dudas: (1) el libro lo marca "verificar"; no hay instrucción propia en comandos_voz ni respuesta en response.py: ¿se implementa o se omite de la evaluación? (2) ¿va antes de la vía ósea normal (orden H3)?

### SISI (fuente: H06 §SISI)
- Resumen: portador 20 dB SL, 8-10 incrementos de 5 dB de práctica y 20 de 1 dB; 5 % cada uno.
- Pasos:
  1. Instrucción "Cambie de volumen". [registrado: talkback cambie_de_volumen]
  2. Portador continuo 20 dB sobre el umbral del oído evaluado, en la frecuencia elegida. [registrado: audio_intensity_change, audio_reverse_toggle]
  3. Familiarización: 8-10 incrementos de 5 dB. [registrado: pulsos de incremento] (lector pendiente)
  4. Prueba: 20 incrementos de 1 dB, ~1 cada 5 s. [registrado: paso 1 dB]
  5. Contar los que el paciente notó (5 % c/u). [registrado: audio_respuesta]
  6. Repetir en cada oído y en las frecuencias de interés; enmascarar el contrario si el tono cruza. [registrado]
- Lo que debería anotar: % por oído y frecuencia (>=70 % coclear; 25-65 dudoso; <=20 sin reclutamiento).
- Dudas: (1) SISI manual: la app sube con la perilla a mano; ¿el alumno cuenta incrementos o se cuentan automáticos? (2) intervalo de 5 s: ¿tolerancia? (3) cortes "verificar" del libro.

### Deterioro tonal: Carhart (fuente: H06 §Carhart)
- Resumen: tono continuo en el umbral; si baja la mano antes de 60 s, +5 dB sin cortar y el minuto reinicia.
- Pasos:
  1. Instrucción "Mano levantada" (con ruido contralateral: "Mano levantada en ruido"). [registrado: talkback]
  2. Dos frecuencias contiguas de 500 a 4.000 Hz por oído. [registrado: audio_freq_change]
  3. Tono continuo en el umbral con Invertir encendido, y cronómetro iniciado. [registrado: audio_reverse_toggle, audio_cronometro]
  4. Si baja la mano antes de 60 s, subir 5 dB sin cortar el tono y reiniciar el cronómetro. [registrado: audio_intensity_change, audio_cronometro, audio_respuesta]
  5. Terminar al oír un minuto entero, o en el máximo o la molestia. [registrado]
- Lo que debería anotar: dB subidos hasta oír el minuto completo; o velocidad de deterioro (dB totales x 60 / s oídos) si llega al techo. Lectura: 0-5 normal; 10-25 coclear; >= 30 retrococlear.
- Dudas: (1) ¿se exigen dos frecuencias o una? (2) ¿Enmascarar contralateral siempre o según regla? (3) cortes sin fuente puntual.

### Deterioro tonal: Rosenberg (fuente: H06 §Rosenberg)
- Resumen: igual que Carhart pero un único minuto total, desde 5 dB sobre el umbral.
- Pasos:
  1. Instrucción "Rosemberg bilateral". [registrado: talkback rosemberg_bilateral]
  2. Partir 5 dB sobre el umbral, tono continuo y cronómetro en marcha. [registrado]
  3. Cada vez que baja la mano, subir 5 dB sin reiniciar el reloj. [registrado: audio_cronometro sin reinicio]
  4. Cortar a los 60 s totales. [registrado]
- Lo que debería anotar: dB subidos durante ese minuto (mismas lecturas que Carhart).
- Dudas: (1) nombre en la app "Rosemberg" vs libro "Rosenberg": unificar. (2) nivel de partida marcado "verificar" en el libro. (3) ¿"bilateral" en el rótulo significa ambos oídos a la vez? Aclarar.

### Deterioro tonal: STAT (fuente: H06 §STAT)
- Resumen: un nivel alto fijo 60 s, 100 dB HL (105 en 1.000 Hz), ruido blanco 90 dB en el otro oído.
- Pasos:
  1. Antes, tener el LDL: si LDL <= 100 dB HL (<= 105 en 1.000 Hz) en esa frecuencia, no se hace. [registrado: LDL de la sesión]
  2. Instrucción "Ruido blanco contralateral" y de deterioro (mano levantada). [registrado: talkback]
  3. Ruido blanco (WN) 90 dB en el canal 2, al oído contrario, siempre. [registrado: audio_stim_select, audio_intensity_change]
  4. Tono continuo en 500, 1.000 y 2.000 Hz a 100/105/100 dB HL por 60 s. [registrado: audio_cronometro, audio_intensity_change]
  5. Cada oído por separado. [registrado]
- Lo que debería anotar: por frecuencia y oído, si oyó el minuto completo (negativo) o no (positivo, sugiere VIII par).
- Dudas: (1) el libro habla de 110 dB SPL y de dB HL equivalentes; confirmar los valores. (2) ¿tolerancia en nivel (+-5 dB)? (3) si hay deterioro del caso, ¿se espera que se informe por frecuencia?

### Stenger (fuente: H06 §Stenger)
- Resumen: para pérdida unilateral o muy asimétrica (>= 20 dB); bueno +10, "malo" −10 del umbral informado; no responde = positivo.
- Pasos:
  1. Indicación: pérdida de un oído o asimetría >= 20 dB. [registrado: audiograma]
  2. Instrucción de umbrales ("Mano levantada"), sin anunciar la prueba. [registrado: talkback mano_levantada]
  3. Tono al oído bueno a su umbral + 10; el paciente responde. [registrado]
  4. Tono a ambos oídos: bueno +10, malo a umbral informado − 10 (canales con "Alternado" apagado). [registrado]
  5. Observar respuesta: responde = negativo; no responde = positivo. [registrado: audio_respuesta]
  6. Si positivo, subir el malo de a poco hasta que deje de responder para estimar el umbral real. [registrado]
- Lo que debería anotar: Stenger positivo/negativo en la frecuencia; si positivo, "pérdida no orgánica" y umbral real estimado.
- Dudas: (1) el libro menciona la versión con palabras; ¿se evalúa solo la tonal? (2) ¿se exige elegir una o más frecuencias? (3) relación con la concordancia SRT-PTA como disparador.

---

## 4. Electrofisiología

Leyenda: [registrado] = ya está en action_logs; [desde el informe] = verificable con lo que sube el informe; [falta registro: X] = necesita registro nuevo. "(propuesto)" = paso que el libro no dice.

Qué guarda hoy el informe (revisado en src/):
- ABR/ECochG/ASSR/MLR/CAEP/P300/MMN (AbrMainWindow.session_payload): `tecnica` (transductor, montaje, ventana, impedancias por electrodo, peor impedancia y desbalance, rechazo, criterio FSP, barridos presentados/aceptados/rechazados, FSP, ruido residual, replicabilidad, canal contralateral), `electrodos` (sitio y mm), `fonos` (canal-oído, profundidad, oliva), `preparacion_errores`, curvas con su técnica propia y marcas, hallazgos y conclusión. Es lo más completo.
- EOA: por oído y prueba. TEOAE: nivel del click, modo, nº de barridos, SNR y pass por banda. DPOAE: L1, L2, puntos (f2, DP, ruido, SNR, pass), n_pass/n_total. No guarda sello de sonda, otoscopía ni orden de pruebas.
- VEMP: por curva, lado, subtipo, intensidad, polaridad, transductor, tasa, filtros, maniobra, EMG, emg_ok, marcas P13/N23 o n10/p16, p2p y corregida, asimetría, umbral informado.
- AABR: veredicto informado vs medido, nivel, estímulo, barridos, segundos, FSP, y técnica (transductor, criterio FSP, rechazo, tasa, banda, barridos máx., impedancia, sello_sonda_ok). Sin curvas.
- ASSR: snapshot del panel (estadística por portadora, umbrales); sin curvas.
- No hay otoscopía, anamnesis ni explicación al paciente registradas en ningún módulo.

---

### EOA: TEOAE y DPOAE (fuente: H09 §Paso a paso 1-5, §Cómo se informa)
- Resumen: sonda bien sellada, SOAE en silencio, luego TEOAE no lineal a 80 dB SPL y DP-grama 65/55, siempre oído por oído, e informe por oído con calidad del registro.
- Pasos:
  1. Otoscopía antes de poner la sonda. [falta registro: acción de otoscopía en el módulo EOA]
  2. Oliva elegida por el tamaño del conducto y sonda firme, apuntando al tímpano. [falta registro: oliva/sonda puesta]
  3. Chequeo de sonda en verde o amarillo antes de medir; en rojo no se mide. [falta registro: resultado del chequeo por captura; hoy solo hay "sello_sonda_ok" en AABR]
  4. Orden SOAE, TEOAE, DPOAE, oído por oído. (orden: el libro lo da como el que "menos se estorban") [falta registro: marca de tiempo de cada captura]
  5. SOAE: registro en silencio de 30 s o más. [falta registro: duración SOAE]
  6. TEOAE: click, modo no lineal, 80 dB SPL. [desde el informe: modo_click, nivel_click_db_spl]
  7. TEOAE: la prueba llega al 100 % de barridos; si hay movimiento o ruido se repite. [desde el informe: n_barridos; falta registro: cuántas repeticiones]
  8. DPOAE: f2/f1 1,22 y L1/L2 65/55 dB SPL. [desde el informe: l1, l2; falta registro: relación f2/f1]
  9. DP-grama de 1 a 8 kHz (mínimo 1, 2, 3, 4, 6, 8). [desde el informe: puntos]
  10. Ambos oídos medidos. [desde el informe]
  11. Informe por oído: prueba, parámetros, bandas presentes o ausentes, calidad del registro, conclusión en términos de función coclear (no de umbral). [desde el informe: hallazgos y conclusión]
  12. Si el registro es malo, informar "no concluyente", no "ausente". [desde el informe: texto]
  13. Ausentes: mirar el oído medio antes de atribuir a cóclea (propuesto desde "Errores frecuentes").
- Lo que debería anotar: por oído, bandas TEOAE presentes (SNR ≥ 6 dB, 3 de 5 con reproducibilidad ≥ 70 % y estabilidad ≥ 80 %); DPOAE presentes (≥ 6 dB sobre ruido, 4 de 7 puntos); SOAE presentes/ausentes (ausencia es normal). Conclusión: "función de células ciliadas externas conservada/alterada" según el caso. Si el caso es neuropatía: OEA presentes no es audición normal.
- Dudas para el docente:
  1. ¿La supresión contralateral (opcional) se evalúa, o queda fuera de la ficha?
  2. ¿Es obligatorio hacer las tres pruebas o basta TEOAE en operativo/escolar?
  3. ¿El orden SOAE-TEOAE-DPOAE es exigible o solo recomendado?

### Tamizaje con OEA (fuente: H09 §Tamizaje)
- Resumen: el equipo decide pasa/refiere; el alumno controla otoscopía, sonda, niño tranquilo y el registro por oído.
- Pasos:
  1. Otoscopía y limpieza de vérnix/cerumen si hay. [falta registro: otoscopía]
  2. Sonda sellada y niño tranquilo. [falta registro: sello]
  3. Un resultado por oído, ambos oídos. [desde el informe]
  4. Se repite solo si el registro no fue confiable, no para conseguir un "pasa". [falta registro: nº de intentos por oído y su resultado]
  5. Recién nacido de más de 5 días en UCI: se deriva a AABR, no solo OEA. [desde el informe: conclusión]
  6. Operativo: solo TEOAE, oído por oído, conclusión en formulario. [desde el informe]
- Lo que debería anotar: pasa/refiere por oído y calidad del registro; en refiere, conducta (reescreening, ABR).
- Dudas: (1) ¿Ficha aparte del EOA clínico o un modo de la misma? (2) ¿Hay límite de reintentos aceptable? (3) ¿Operativo cuenta en los casos del simulador?

---

### ABR / PEATC clínico y umbral (fuente: H10 §Preparar al paciente, Montaje, Parámetros, Paso a paso 1-9, Qué lleva el informe)
- Resumen: paciente dormido, piel limpia, impedancias bajas, click alternado 21,1/s a 80 dB nHL, umbral de onda V con réplicas y suficientes barridos, informe con parámetros y conclusión.
- Pasos:
  1. Otoscopía y anamnesis (en lactante: gestación, parto, UCI, fármacos, antecedentes). [falta registro: otoscopía/anamnesis]
  2. Paciente dormido antes de registrar. [registrado: paciente_duerme]
  3. Piel limpia con alcohol y gel abrasivo antes de poner electrodos. [desde el informe: preparacion_errores]
  4. Activo en Cz, referencias en cada mastoides, tierra en la frente. [desde el informe: electrodos]
  5. Impedancias bajo 5 kΩ y parecidas entre sí. [desde el informe: impedancia_max, desbalance, en_norma]
  6. Fonos de inserción puestos en el oído correcto (rojo OD, azul OI) y hasta el fondo. [desde el informe: fonos]
  7. Se mira el EEG antes de promediar. [falta registro: EEG visto antes de iniciar; verificable solo indirecto por rechazo]
  8. Parámetros de rutina: click, polaridad alternada, 21,1/s, filtros 100-3.000 Hz, ventana 10-12 ms, rechazo ±10 µV o menos. [desde el informe: tecnica por curva]
  9. Primer oído a 80 dB nHL, con réplica de la curva. [desde el informe: curvas, replicabilidad]
  10. Umbral: baja de 20 en 20; sin V, sube de 10 en 10; queda un escalón bajo el umbral sin V. [desde el informe: secuencia de intensidades de las curvas]
  11. Se repiten la curva máxima y la del umbral. [desde el informe]
  12. Se promedia hasta FSP ≥ 3,1 o ruido residual bajo; no se corta antes. [desde el informe: fsp, barridos, ruido_residual]
  13. Sin onda V a 80: sube a 90-100 dB nHL antes de concluir. [desde el informe]
  14. Se usa el canal contralateral para identificar la onda I (propuesto como verificable). [desde el informe: canal_contralateral]
  15. Enmascara si el otro oído puede contestar (oído estudiado mucho peor). [falta registro: enmascaramiento no aparece en el informe]
  16. Sospecha neural: repite a 81,1/s y compara. [desde el informe: curvas con tasa]
  17. Marca ondas I, III, V solo si se repiten; mide latencias, interpicos, V. [desde el informe: marcas]
  18. Informe con registro, referencia, tabla, interpretación, conclusión (umbral en dB eHL), trazos. [desde el informe]
  19. Si ABR plano, mirar emisiones antes de decir "sordo". [desde el informe: texto]
  Fonos: gestos del oliva/llanto/comprimir se registran. [registrado: abr_fono_poner/sacar/oliva/comprimir/llanto, abr_montaje_asistido, abr_montaje_reinicio]
- Lo que debería anotar: latencias I, III, V (ms) a 80 dB nHL; interpicos I-III, III-V, I-V; umbral de V (dB nHL) y su paso a dB eHL; función latencia-intensidad; patrón (normal, transmisión, coclear, retrococlear, neuropatía); conclusión con la frase del libro ("examen sugiere...").
- Dudas:
  1. ¿Tone burst/NB chirp y vía ósea van en esta ficha o en fichas aparte?
  2. ¿Se exige el escalón 20-20/10 estricto, o basta con umbral con V y sin V debajo?
  3. ¿Cuánto es "dormido" aceptable si el caso lo trae despierto?

### AABR / tamizaje automatizado (fuente: H10 §El AABR de tamizaje; protocolo.txt PEAAT)
- Resumen: nivel fijo de 35 dB nHL, preparar piel e impedancias, esperar al criterio del equipo y no subir el nivel ni cortar para conseguir PASA.
- Pasos:
  1. Otoscopía y anamnesis del parto. [falta registro]
  2. Recién nacido dormido, en cuna o brazos. [registrado: paciente_duerme, si aplica al AABR]
  3. Piel limpia y electrodos en vértex, ambas mastoides, tierra en frente. [falta registro: AABR no guarda electrodos; solo impedancia fija]
  4. Impedancias bajo el límite del equipo. [desde el informe: impedancia_kohm es constante; falta registro: valor real medido]
  5. Sonda/oliva sellada en el primer oído. [desde el informe: sello_sonda_ok]
  6. Nivel 35 dB nHL sin subirlo. [desde el informe: nivel por oído]
  7. Se deja terminar el registro hasta el criterio (FSP 3,1) o el máximo de barridos. [desde el informe: barridos, segundos, fsp]
  8. Se hace el otro oído. [desde el informe]
  9. Veredicto informado coincide con el del equipo. [desde el informe: veredicto vs medido]
  10. REFIERE se informa como "refiere", no "hipoacusia"; conducta: reescreening o ABR diagnóstico. [desde el informe: conclusión]
  11. Más de 5 días en UCI: AABR, no solo OEA (propuesto en esta ficha). [desde el informe]
- Lo que debería anotar: PASA/REFIERE por oído, nivel, FSP, barridos, conducta.
- Dudas: (1) ¿El límite de impedancia del tamizaje es el del equipo o uno fijo del curso? (2) ¿Se castiga cortar el registro antes? (3) ¿Cuántos reintentos son aceptables?

---

### ECochG (fuente: H11 §Preparar, Los tres electrodos, Montaje, Paso a paso 1-8)
- Resumen: electrodo timpánico en el oído estudiado, click alternado 90 dB nHL con filtros propios (no los del ABR), marcar BL/Ini/PS/PA/Fin y leer las razones PS/PA y de áreas.
- Pasos:
  1. Otoscopía y revisión del audiograma; preguntar por última crisis. [falta registro]
  2. Explicar que el electrodo en el tímpano da presión y el click es fuerte. (propuesto como evaluable) [falta registro]
  3. Piel limpia, referencia (mastoides/lóbulo) y tierra en frente. [desde el informe: electrodos, preparacion_errores]
  4. Electrodo de oído en el oído estudiado (timpánico, conducto o transtimpánico). [desde el informe: montaje]
  5. Impedancias bajas y parecidas; mira el EEG. [desde el informe: impedancias]
  6. Configuración correcta: click alternado, 90 dB nHL, 11,1/s, filtros 5 a 3.000 Hz, ventana 10 ms, 1.500 barridos. No usar los filtros del ABR. [desde el informe: tecnica y ecochg]
  7. Réplica de la curva (o subpromedios A/B). [desde el informe]
  8. Marca BL, Ini, PS (hombro), PA (fondo del valle), Fin; no confía ciegamente en Auto. [desde el informe: marcas]
  9. Lee ambas razones (PS/PA, áreas) y las compara con el límite del electrodo usado (timpánico 0,40 y 1,94). [desde el informe]
  10. Registra el otro oído como referencia. [desde el informe]
  11. Con burst: envolvente 1-10-1 ms, ventana 20 ms, PS en la mitad de la meseta, sin comparar con límites de click. [desde el informe: envolvente_burst, ventana]
  12. Si se pide: rarefacción vs condensación (límite 0,38 ms), tasa alta (91/s), control con glicerol. [desde el informe: polaridad, tasa]
  13. Informe: "normal no descarta, alterado apoya". [desde el informe: conclusión]
- Lo que debería anotar: PS/PA y razón de áreas por oído, comparadas con el límite del electrodo; latencia del PA; si hay hidrops sugerente o no; ante normal, que no lo descarta.
- Dudas: (1) ¿Qué electrodo es el obligatorio en el simulador? (2) ¿Se exige el control de glicerol o rarefacción-condensación? (3) ¿Qué ventana mínima se considera error?

---

### VEMP: cVEMP y oVEMP (fuente: H12 §Requisitos, Montaje, Paso a paso 1-7)
- Resumen: tone burst 500 Hz a 100 dB nHL con contracción moderada y pareja del músculo, EMG medido, replicar, marcar P13-N23 (o n10-p16), umbral del cVEMP y asimetría corregida.
- Pasos:
  1. Otoscopía, anamnesis otoneurológica y explicación. [falta registro: ninguna acción de VEMP]
  2. Se descarta contraindicación: hipoacusia de conducción, limitación de cuello/mirada, nistagmo (oVEMP), hipersensibilidad al sonido. [falta registro: revisión de audiograma/timpanograma]
  3. cVEMP: tierra en frente, común en esternón, canales en tercio superior de cada ECM; oVEMP: común en mentón, canal bajo la pupila del ojo contralateral (cruzado). [falta registro: el módulo guarda el montaje descrito (`montaje`) pero no si el alumno lo armó]
  4. Impedancias cVEMP < 5 kΩ y dif. < 2 kΩ; oVEMP < 3 kΩ y dif. < 1 kΩ. [falta registro: impedancias no se guardan en VEMP]
  5. Parámetros: tone burst 500 Hz (cVEMP) o 500/1.000 Hz (oVEMP), rarefacción, 5,1/s, 100 dB nHL, filtros 3 Hz-1,5 kHz (c) o 1 Hz-1 kHz (o), 100-200 barridos. [desde el informe: curvas con int, freq, pol, rate, filtros]
  6. cVEMP: semisentado ~30°, cabeza flexionada y girada al lado contrario del oído estimulado. [desde el informe: maniobra]
  7. EMG en banda 30-150 µV rectificados y pareja en ambos lados. [desde el informe: emg_uv, emg_ok]
  8. Registra una segunda curva por oído; las P13-N23 caen en las mismas latencias. [desde el informe: curvas]
  9. Marca P13/N23 (o n10/p16) y mide p2p y amplitud corregida. [desde el informe: LatAmp, p2p_corregida]
  10. Busca umbral del cVEMP: baja de 10 en 10, sube 5 al perder respuesta. [desde el informe: intensidades y umbral_informado]
  11. oVEMP: mirada hacia arriba ~30°, se registra a 100 dB nHL con réplica. [desde el informe: maniobra]
  12. Asimetría con Jongkees sobre amplitud corregida (significativa ≥ 35 % cVEMP, ≥ 33 % oVEMP). [desde el informe: asimetria]
  13. No repetir registros innecesarios (evita sonido de más). (propuesto) [desde el informe: nº de curvas]
- Lo que debería anotar: latencias P13 y N23 (cVEMP) o n10 y p16 (oVEMP), amplitud pico a pico y corregida por oído, umbral cVEMP, % asimetría; lectura (umbral bajo = tercera ventana; ausente no es "enfermo" si hay gap).
- Dudas: (1) ¿Se evalúa el EMG como "dentro de banda" o solo la pareja entre lados? (2) ¿La vía ósea queda en otra ficha o se ignora? (3) ¿Las contraindicaciones deben verificarse con el audiograma previo del caso?

---

### ASSR (fuente: H13 §Preparar al paciente, Montaje, Parámetros, Paso a paso 1-6, Cómo se informa)
- Resumen: paciente cansado/dormido, ABR antes, protocolo según edad/vigilia, EEG tranquilo, leer rojo como no concluyente hasta que el ruido sea bajo, informar en dB nHL y dB eHL con la tabla usada.
- Pasos:
  1. Otoscopía y anamnesis (en lactante, parto y ABR previo). [falta registro]
  2. Hay un ABR previo; si el ABR es ausente o anormal, no se hace ASSR. [falta registro: el informe ASSR no ve el ABR previo; sí podría cruzarse por atención]
  3. Paciente dormido (90 Hz); adulto despierto, 40 Hz. [registrado: paciente_duerme]
  4. Piel limpia; activo Cz, referencias en mastoides, tierra en frente. [desde el informe: electrodos]
  5. Impedancias bajo 3 kΩ (ideal) y parecidas. [desde el informe: tecnica]
  6. Protocolo elegido según paciente (niño, adulto dormido, adulto despierto). [desde el informe: assr snapshot]
  7. Se mira el EEG antes de iniciar. [falta registro]
  8. No se cambian los valores de estímulo del fabricante; rechazo ±20 µV (lactante, 90 Hz) o ≤ ±40 µV (40 Hz). [desde el informe: rechazo_artefacto_uv]
  9. Estrategia: sin respuesta sube de 20 en 20; con respuesta baja de 10-20 y afina de 5-10; sobre 80 dB nHL, de a 5 dB. [falta registro: secuencia de niveles por portadora; el snapshot solo trae el umbral final]
  10. Respuesta muy rápida (< 1 min) o solo a nivel alto: se repite; control con estímulo bloqueado. [falta registro: repetición/control]
  11. Distingue ausente de no concluyente; no da umbral sin respuesta ausente debajo (usa ≤). [desde el informe: umbrales]
  12. Informa dB nHL con signo =, ≤ o >, y dB eHL con la tabla de corrección. [desde el informe: conclusión]
  13. Concordancia con ABR y emisiones; si se contradicen, manda el ABR. [desde el informe: texto]
- Lo que debería anotar: umbral por oído y frecuencia (500, 1.000, 2.000, 4.000 Hz) en dB nHL y eHL; grado y configuración; limitaciones (no descarta neuropatía).
- Dudas: (1) ¿Qué tabla de corrección eHL se usa en el curso? (2) ¿El "ABR previo" es requisito evaluable? (3) ¿Cuánto tiempo mínimo antes de aceptar un nivel?

---

### Latencia media (MLR) (fuente: H14 §Antes de empezar, Paso a paso 1-4, §Presencia y ausencia)
- Resumen: despierto y relajado, C3 y C4, clic ~10/s con filtros 10-100 Hz y ventana de 100 ms, replicar Pa y comparar hemisferios y oídos.
- Pasos:
  1. Otoscopía y timpanometría primero. [falta registro]
  2. Paciente despierto y quieto, cuello relajado. [falta registro: estado vigilia; hay `vigilia.py` en src/abr, confirmar si lo guarda]
  3. Activos C3 y C4, referencia A1/A2 (lóbulo prefiere por reflejo postauricular), tierra en frente. [desde el informe: electrodos]
  4. Impedancias iguales entre sí, ≤ 5 kΩ. [desde el informe]
  5. Clic o tono breve, 60 dB nHL, 9-12/s. [desde el informe: tecnica]
  6. Filtros 10-100 Hz, ventana 100 ms, 1.000 barridos por registro, rechazo ≤ 10 %. [desde el informe: tecnica por curva]
  7. Se mira el EEG antes y durante. [falta registro]
  8. Pa aparece en su ventana y se repite en dos registros. [desde el informe: curvas, replicabilidad]
  9. Compara latencia y amplitud (Na-Pa) entre hemisferios y entre oídos. [desde el informe: efectos]
  10. No usa MLR para estimar umbral. [desde el informe: conclusión]
- Lo que debería anotar: latencia de Na y Pa y amplitud Na-Pa por electrodo y oído; asimetrías; no interpretar ausencia en niño como pérdida.
- Dudas: (1) ¿Qué referencia de latencias del libro es la oficial? (2) ¿Criterio de presencia: "dos registros con Pa"? (3) ¿La vigilia se evalúa?

### Potenciales corticales / CAEP, umbral cortical (fuente: H14 §Paso a paso 1-6, §Presencia y ausencia)
- Resumen: despierto con ojos abiertos, estímulo cada 1-2 s, filtros 1-15 Hz y ventana larga, nunca menos de 10 promedios y siempre replicado; umbral con descensos 20 y 10.
- Pasos:
  1. Otoscopía y timpanometría. [falta registro]
  2. Despierto, ojos abiertos, relajado. [falta registro]
  3. Activo Cz, referencia mastoides, tierra; impedancias ≤ 5 kΩ y parecidas. [desde el informe]
  4. Estímulo tono con rampa 10-20 ms, meseta ~40 ms, 1 cada 1-2 s (adulto). [desde el informe]
  5. Filtros 1-15 Hz (no los del ABR), ventana 500-1.000 ms con tramo previo. [desde el informe]
  6. Parte en 60 dB HL; baja de 20 y luego de 10; con respuesta sube/baja con el mismo criterio. [desde el informe: curvas]
  7. No detiene el promedio al "ver" la onda; ≥ 10 en total y respuesta repetida en parciales. [desde el informe: barridos]
  8. La respuesta se achica y alarga al bajar el nivel; si no, desconfía. [desde el informe]
  9. Enmascara si el otro oído puede responder (nivel − atenuación interaural + 10 + gap). [falta registro: enmascaramiento]
  10. No usa FSP del ABR. [desde el informe: criterio]
  11. Umbral = nivel más bajo con respuesta, con ausencia ≤ 10 dB abajo; informa "≤" o ">" cuando corresponda. [desde el informe: conclusión]
- Lo que debería anotar: N1-P2, latencias y amplitud por nivel; umbral cortical por oído en dB HL.
- Dudas: (1) ¿Se pide enmascaramiento en el simulador? (2) ¿CAEP se evalúa solo en umbral o también en maduración? (3) ¿Quién califica la "tendencia esperada"?

### MMN y P300 (fuente: H14 §Paso a paso 2, 3, 7, §Presencia y ausencia)
- Resumen: paradigma oddball con probabilidad baja del desviante/blanco, suficientes ensayos, atención a lo correcto (ignorar en MMN, contar en P300), onda de diferencia o pico 280-420 ms.
- Pasos:
  1. Otoscopía y timpanometría. [falta registro]
  2. Montaje: MMN Fz, Cz, C3, C4, mastoides, ref nariz; P300 Fz, Cz, Pz, EOG vertical. [desde el informe: electrodos]
  3. MMN: tonos 50-150 ms, 80 dB SPL, ISI 500 ms-1 s, desviante 10-20 %. [desde el informe]
  4. P300: 500 Hz estándar, 1.000 Hz blanco, 70 dB SPL, ISI 1-2 s, blanco 10-20 %. [desde el informe]
  5. Filtros y ventana según prueba (MMN 0,1-30 Hz y 500 ms; P300 0,01-100 Hz y 1.000 ms). [desde el informe]
  6. Rechazo ±100 µV y por EOG. [desde el informe]
  7. MMN: ≥ 150 desviantes, paciente ignora los sonidos. P300: ≥ 36 ensayos limpios, paciente atiende y cumple la tarea con desempeño anotado. [desde el informe: conteo P300; falta registro: atención/tarea]
  8. MMN medida en la onda de diferencia; P300 como pico 280-420 ms. [desde el informe: marcas]
  9. No concluye ausencia de P300 si el paciente no pudo hacer la tarea; no usa MMN como diagnóstico individual. [desde el informe: conclusión]
- Lo que debería anotar: amplitud y latencia de la MMN (diferencia) y de la P300 por derivación; desempeño en la tarea; presencia/ausencia con calidad del registro.
- Dudas: (1) ¿Qué latencias de referencia por edad? (2) ¿Se evalúa la tarea del paciente? (3) ¿MMN y P300 comparten una ficha o van separadas?

---

### Cobertura resumida de electrofisiología
- Con informe suficiente: ABR, ECochG, MLR/CAEP/MMN/P300 (mismo payload rico), AABR, EOA (parámetros y resultado).
- Casi sin evidencia de técnica: VEMP (no guarda impedancias ni montaje armado), EOA (sin sonda/otoscopía), ASSR (sin secuencia de niveles).
- Faltan en todos: otoscopía, anamnesis, explicación al paciente, orden de pruebas, enmascaramiento y estado del paciente (salvo `paciente_duerme`).

---

## 5. Rinología y sueño

Marcas: [registrado] = la app lo deja en action_logs o en el informe; [falta registro: ...] = no se puede verificar hoy; (propuesto) = no lo dice el libro. Revisé el código de src/nasal: además de lo que ya hay en prod, el código ya registra olf_* (preparación, venda, presentar, puntaje), prick_* (marcar, puncionar, lanceta, secar, medir, resultado) y esp_* (pinza, boquilla, medir talla, verificar, cero, broncodilatador, iniciar, maniobra). Si en prod aparecen pocos es porque faltan atenciones, no porque no se registren.

### Rinoscopía anterior (fuente: H25 §Paso a paso 4 y §Cómo se informa)
- Resumen: se mira cada fosa en orden fijo, con tres inclinaciones de la cabeza, y se describe lo que se ve sin dar diagnóstico.
- Pasos:
  1. Con el paciente aclimatado (10 a 15 minutos sentado) y la nariz limpia. [falta registro: tiempo de aclimatación]
  2. Material y asepsia: guantes, bandeja limpia y bandeja sucia, espéculo en la mano izquierda. [falta registro: la app no simula material ni manos]
  3. Se parte por la fosa que el paciente dice que está mejor (truco del libro); si no se pregunta, primero la derecha. [registrado: orden de rs_mirada]
  4. Cada fosa se mira con la cabeza recta, a 30° y a 60°. [registrado: rs_mirada con grados]
  5. Se comparan las dos fosas (ambas miradas en las tres posiciones). [registrado: vistas por lado]
  6. Se informa fosa por fosa, en el orden vestíbulo, tabique, cornetes, meatos y mucosa, como hallazgo y no como diagnóstico. [registrado: informe de hallazgos por fosa; verificar con el docente cuántos campos guarda]
  7. Se mira antes de medir la rinomanometría. (propuesto) [falta registro: comparar horas de rs_ y rm_]
- Lo que debería anotar: por fosa, desviación del tabique (lado y tercio), espolón o perforación, tamaño y color del cornete inferior, secreción, masa. Un hallazgo de un solo lado o una masa se marca para derivar.
- Dudas para el docente:
  1. ¿Cuenta como correcta empezar por la derecha aunque el paciente diga que la izquierda es la mejor?
  2. ¿Se exige ver las tres posiciones en las dos fosas, o basta con las que muestran algo?
  3. La anamnesis y la palpación de senos las ve otra ficha; ¿la rinoscopía se evalúa sin ellas?

### Rinomanometría anterior (fuente: H26 §Paso a paso 1 a 8)
- Resumen: se mide la resistencia de cada fosa a 150 Pa con la contraria ocluida y se decide si hace falta vasoconstrictor.
- Pasos:
  1. Antes: el paciente sin vasoconstrictor 48 h ni tabaco o alcohol 24 h, y aclimatado 15 minutos; se pregunta. [falta registro: pregunta de fármacos y tabaco en esta ficha]
  2. Se le pide respirar normal, solo por la nariz y con la boca cerrada. [falta registro: instrucción al paciente]
  3. Se elige el adaptador del tamaño de la narina y se pone en la fosa contraria a la medida. [registrado: rm_adaptador con narina]
  4. Se parte por la fosa derecha (adaptador en la izquierda). [registrado: rm_registro / rm_adaptador, orden]
  5. Se comprueba el sello con el dedo antes de cada fosa. [registrado: rm_sello]
  6. La máscara va sobre nariz y boca, sin fuga. [registrado: rm_mascara, acomodar_mascara]
  7. Se mide la primera fosa con el número de ciclos del equipo y se cambia el adaptador. [registrado: rm_registro por lado]
  8. Se mide la segunda fosa y se vuelve a comprobar el sello. [registrado: rm_sello, rm_registro]
  9. Se documenta presión y resistencia de cada fosa. [registrado: informe]
  10. Solo si una fosa supera 0,4 Pa/(cm³/s), se aplica vasoconstrictor en esa fosa: dos disparos inspirando, 15 minutos de espera (puede saltarla) y se mide igual. [registrado: rm_indicacion, vasoconstrictor, saltar_espera]
  11. Se mide con el mismo adaptador y el mismo orden que en reposo. [registrado: comparar rm_adaptador y orden entre fases]
- Lo que debería anotar: por fosa, presión (150 Pa), flujo y resistencia en reposo; resistencia total en paralelo (1/RT = 1/RD + 1/RI), no el promedio; tras vasoconstrictor, tipo de obstrucción: igual = mecánica, baja sin llegar a 0,4 = mixta, llega a 0,4 = vasomotora.
- Dudas para el docente:
  1. Si ambas fosas están dentro de 0,4 y el alumno igual aplica vasoconstrictor, ¿es error o solo exceso?
  2. ¿Cuántos ciclos por fosa exige la ficha (el libro dice promediar 3 a 5)?
  3. ¿Se reprueba el aviso de aclimatación de 15 minutos aunque la app no lo mida?

### Rinometría acústica (fuente: H27 §Paso a paso)
- Resumen: se calibra el equipo y se miden las áreas de cada fosa con tres registros parecidos, antes y después de vasoconstrictor si hace falta.
- Pasos:
  1. Se calibra el equipo con el tubo calibrador antes de partir. [registrado: ra_calibrar]
  2. Se le pide al paciente quedarse quieto y en apnea durante cada registro. [falta registro: instrucción al paciente]
  3. Se elige el adaptador que calza con cada narina. [falta registro: ra_ no guarda el adaptador; revisar]
  4. Se parte por la fosa derecha. [registrado: ra_iniciar con lado]
  5. Transductor sin empujar el ala de la nariz, sellando, a 45° o más. [registrado: error_simulado / calidad del registro]
  6. Se registra en apnea. [registrado: ra_registro, ra_iniciar]
  7. Se repite hasta tener tres registros similares por fosa (diferencia de 0,03 o menos en MCA1 y MCA2). [registrado: ra_registro con calidad]
  8. Se marcan Dist 1, MCA1, Dist 2, MCA2, Vol 1 y Vol 2 y se promedian. [registrado: ra_marcar, ra_medicion]
  9. Se compara fosa por fosa con la referencia del equipo. [registrado: informe]
  10. Si una fosa está fuera de rango, vasoconstrictor (2 disparos inspirando, 15 minutos) y mismo procedimiento. [registrado: vasoconstrictor, saltar_espera]
- Lo que debería anotar: por fosa y por condición, Dist 1 y MCA1 (válvula), Dist 2 y MCA2 (cornete inferior), Vol 1 y Vol 2; respuesta al vasoconstrictor: igual (estructural), parcial (mixta), total (mucosa); si el área baja, repetir y revisar antes de informar.
- Dudas para el docente:
  1. La unidad del criterio de 0,03: ¿cm²? (el libro lo deja con "verificar").
  2. ¿Se exige que el alumno marque él mismo los mínimos o basta con el automático?
  3. ¿El vasoconstrictor es obligatorio solo si está fuera de rango, o se acepta hacerlo siempre?

### Olfatometría (Sniffin' Sticks completa) (fuente: H28 §Paso a paso 1 a 6)
- Resumen: umbral, discriminación e identificación con bolígrafos; TDI = T + D + I.
- Pasos:
  1. Se pregunta la preparación: una hora sin comer, fumar, perfumarse ni lavarse los dientes. [registrado: olf_preguntar_preparacion, esperar_preparacion]
  2. La olfatometría va antes de cualquier anestesia tópica. (en el libro es orden de exámenes) [falta registro: orden contra otros exámenes]
  3. Se explica que es de elección forzada y se vendan los ojos para umbral y discriminación. [registrado: olf_venda]
  4. Umbral: tríos desde el paso 16, dos aciertos bajan y un error sube, parada tras la 7.ª inversión; T = promedio de las últimas 4 inversiones. [registrado: olf_presentar, olf_puntaje]
  5. Discriminación: 16 tríos con venda, 20 a 30 segundos entre tríos. [registrado: olf_presentar]
  6. Identificación: 16 bolígrafos, 4 opciones, sin venda. [registrado: olf_presentar, olf_categoria]
  7. Se suma TDI y se anota cada subpuntaje y si fue con una narina o ambas. [registrado: olf_narina, olf_puntaje]
  8. Se tapan los bolígrafos de inmediato. [falta registro: cierre y tapas]
- Lo que debería anotar: T, D (de 16), I (de 16), TDI y su categoría (≤ 16 anosmia funcional; 16,25 a 30,5 hiposmia; 30,75 a 41,25 normosmia; ≥ 41,5 superior), sin causa ni diagnóstico; en el caso, la categoría debe coincidir con el olfato definido.
- Dudas para el docente:
  1. ¿Se evalúa solo con ambas narinas o también por separado?
  2. ¿Se descuenta si el alumno anota sin que el paciente haya elegido (olf_anotar_sin_eleccion)?
  3. Los cortes de 30,5 y 30,75: ¿cuál va en la ficha?

### Prick test (fuente: H29 §Paso a paso 1 a 11)
- Resumen: puntura de alérgenos con controles, lectura a los 15 a 20 minutos y criterio de 3 mm.
- Pasos:
  1. Se pregunta por fármacos y se anota la última dosis de antihistamínico. [registrado: prick_preguntar_farmacos]
  2. Hay adrenalina a la mano y consentimiento. [falta registro: ni adrenalina ni consentimiento]
  3. Antebrazo volar, lejos de muñeca y codo, puntos a 2,5 cm entre sí (mínimo 2). [registrado: prick_marcar con x, y y avisos]
  4. Una gota por marca; negativo primero, histamina al final. [registrado: prick_marcar con orden]
  5. Lanceta nueva por punción, a 90°, sin sangre. [registrado: prick_puncionar con lanceta y reusada, prick_lanceta]
  6. Se seca sin arrastrar. [registrado: prick_secar con arrastre]
  7. Se espera sin que el paciente se rasque. [registrado: prick_saltar_espera]
  8. Se lee a los 15 a 20 minutos (pápula, no eritema). [registrado: minutos en prick_medir / saltar_espera]
  9. Se mide diámetro mayor y perpendicular, en mm. [registrado: prick_medir con eje y mm]
  10. Primero se revisan los controles: negativo sin pápula, histamina de 3 mm o más. [falta registro: orden de lectura de los controles]
  11. Positivo si la pápula mide 3 mm o más (3 mm sobre el negativo si este reacciona). [registrado: prick_resultado con correcto]
- Lo que debería anotar: cada alérgeno con su pápula en mm, ambos controles, última dosis de antihistamínico, y "sensibilización" en vez de "alergia".
- Dudas para el docente:
  1. ¿El criterio de lectura es 15 o 20 minutos en el simulador?
  2. ¿Se pide la distancia de 2,5 cm exacta o basta con ≥ 2 cm?
  3. ¿Se evalúa el sitio del antebrazo (3 cm del pliegue)?

### Espirometría (fuente: H30 §Antes de empezar, §Paso a paso)
- Resumen: maniobras forzadas aceptables y repetibles, con control de equipo, y prueba broncodilatadora cuando corresponde.
- Pasos:
  1. Verificación diaria del equipo con jeringa de 3 L (±3 %) y calibración si hace falta. [registrado: esp_verificar, esp_calibrar]
  2. Flujo cero. [registrado: esp_cero]
  3. Se mide la talla sin zapatos (y el peso). [registrado: esp_medir]
  4. Se pregunta por broncodilatadores y contraindicaciones; se anota la última dosis. [falta registro: pregunta de contraindicaciones; broncodilatador sí]
  5. Pinza nasal y boquilla con filtro. [registrado: esp_pinza, esp_boquilla]
  6. Demostración y respiración tranquila de 3 a 5 volúmenes. [falta registro: demostración]
  7. Indicaciones durante la maniobra ("inspire al máximo", "sople de golpe", "siga, siga"). [registrado: esp_indicacion]
  8. Al menos 3 maniobras aceptables, máximo 8; FVC y FEV1 repetibles (≤ 0,150 L). [registrado: esp_maniobra, esp_marca]
  9. Se informa la mayor FVC y el mayor FEV1, con grado de calidad. [registrado: esp_maniobra con resultado]
  10. Broncodilatador (400 µg de salbutamol con aerocámara, 15 minutos) y se repiten las maniobras. [registrado: esp_broncodilatador, esp_saltar_espera]
- Lo que debería anotar: FVC, FEV1, FEV1/FVC, valor previsto, z-score o LLN, patrón (normal, obstructivo, no específico), gravedad por z-score, calidad de cada maniobra y respuesta al broncodilatador (> 10 % del previsto es significativa).
- Dudas para el docente:
  1. El libro usa el manual chileno (SER 2024); ¿la ficha sigue ese y no el ATS/ERS?
  2. ¿Se evalúa la verificación con jeringa cada atención o se da por hecha?
  3. ¿Se exige anotar los errores de la maniobra (esp_marca) o solo el resultado final?

### Polisomnografía y poligrafía respiratoria (fuente: H31 §Antes de empezar, §Paso a paso, §Cómo se informa)
- Resumen: se monta el estudio correcto, se registra la noche, se puntúan los eventos y se informa IAH y gravedad.
- Pasos:
  1. Se elige el estudio (polisomnografía o poligrafía) según la sospecha. [registrado: psg_estudio]
  2. Se monta cada sensor: EEG, EOG, EMG, ECG, flujo térmico y cánula, bandas, oxímetro, ronquido, posición. [registrado: psg_sensor con puesto]
  3. Biocalibraciones antes de apagar las luces. [falta registro: biocalibraciones]
  4. Se registra la noche con el montaje completo. [registrado: psg_registrar con montaje y faltan]
  5. Se revisa la calidad: cánula suelta, tramos a excluir. [registrado: excluir]
  6. Se marcan y clasifican los eventos (apnea, hipopnea) y su tipo (obstructiva, central, mixta) según las bandas. [registrado: agregar, cambiar, borrar con tipo y verdad]
  7. Se elige la regla de hipopnea (3 % o despertar, o 4 %) y se declara. [registrado: psg_regla]
  8. Se calcula IAH por hora de sueño (poligrafía: por hora de registro). [registrado: informe]
  9. Se informa la gravedad por IAH (< 5, 5 a 15, 15 a 30, ≥ 30). [registrado: psg_gravedad]
- Lo que debería anotar: IAH, IDO, tiempo total de sueño y arquitectura (polisomnografía), tipo de apnea, gravedad como descripción, sin diagnóstico.
- Dudas para el docente:
  1. ¿Se exige elegir el estudio antes del montaje o puede cambiarse después?
  2. ¿Qué se considera montaje mínimo suficiente en la poligrafía (presión nasal, bandas, oximetría)?
  3. ¿La clasificación pediátrica se enseña o se deja fuera?

### CPAP (instalación, titulación y seguimiento) (fuente: H32 §Antes de empezar, §Paso a paso 1 a 3)
- Resumen: interfaz bien ajustada, titulación con reglas por eventos y lectura de los datos del equipo.
- Pasos:
  1. Se parte de una indicación escrita (modalidad y forma de iniciar). [falta registro: indicación previa]
  2. Se elige la interfaz y la talla. [registrado: cpap_interfaz, cpap_empezar]
  3. Se revisa el sello con la boca cerrada, abierta y al hablar (propuesto). [falta registro: sello]
  4. Se empieza la titulación con el paciente despierto y presión baja. [registrado: cpap_empezar con presion]
  5. Se sube la presión según eventos: espera entre cambios y criterios de la guía. [registrado: cpap_presion con min_desde_cambio]
  6. Se puede pausar o cambiar la velocidad del registro. [registrado: cpap_pausa, cpap_velocidad]
  7. Se termina y se indica la presión elegida con el grado de la titulación. [registrado: cpap_terminar, cpap_indicar con grado]
  8. Se lee la descarga: horas de uso, IAH residual, fugas. [falta registro: lectura de la descarga]
- Lo que debería anotar: presión elegida (que controle apneas, ronquido y despertares, no solo apneas), grado de titulación (óptima, buena, adecuada, no adecuada), RDI < 5, saturación mínima > 90 %, fuga aceptable.
- Dudas para el docente:
  1. ¿Se evalúa el tiempo mínimo entre subidas de presión como error o solo se avisa?
  2. ¿La educación al paciente se evalúa o queda fuera de la app?
  3. ¿Se enseña también AutoCPAP o solo titulación manual?
