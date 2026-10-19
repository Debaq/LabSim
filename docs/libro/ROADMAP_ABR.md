# Roadmap del ABR en el libro

Pedido del autor (2026-10-16): H10 quedó corto y se complementa en los
capítulos de casos especializados en ABR. Este archivo reparte los temas y
dice qué entra en cada capítulo. Sirve de guía para escribir esos capítulos
y para no repetir lo mismo en varios.

Modelo de organización: *Clinical Applications of the Auditory Brainstem
Response* (Hood, 1998), en tres partes:

1. El ABR normal: cómo se registra y qué lo cambia.
2. Aplicaciones: diagnóstico neurológico, estimar la audición y el ABR en niños.
3. Casos e informes, más ejercicios de laboratorio.

Hood es la referencia central del autor para el ABR (él, 2026-10-18: "Hood
es mi diosa"): sus citas en el libro no se quitan ni se reemplazan. Lo único
pendiente es el índice completo (en papel o en la ficha de una biblioteca)
para citar capítulos o tablas puntuales; lo de arriba sale de la descripción
del editor.

## Regla general

- **H10 es la herramienta básica**: fundamento, montaje, parámetros de
  rutina, paso a paso, los cuatro patrones y cómo se informa. No crece más.
  En cada tema remite al capítulo que lo profundiza ("→ cap. 12").
- **Cada capítulo de casos profundiza un tema** en su "Técnica en foco", con
  sus propios casos armados en LabSim para mostrarlo.
- **Cada capítulo de ABR termina con ejercicios en LabSim**: el lugar de los
  "ejercicios de laboratorio" de Hood, y calza con la práctica offline de los
  pacientes del libro (ESTADO.md).
- **Informe**: cada caso de ABR cierra con un informe escrito según el patrón
  (los cuatro patrones de H10), para que el alumno vea el mismo formato
  repetido en distintas situaciones.

## Qué entra en cada capítulo

### H10 — Potenciales evocados auditivos de tronco (ya escrito)
- Se queda como está. Agregar solo las remisiones a los capítulos de abajo.
- Revisar que los "cuatro patrones" de *Cómo se informa* sean los mismos que
  usan los caps. 11-18.

### Cap. 11 — Asimetría que no cierra (diagnóstico neurootológico)
- Función latencia-intensidad de la onda V: cómo se ve en lo conductivo, lo
  coclear y lo retrococlear, con las tres curvas superpuestas.
- Diferencia interaural de la onda V y su corrección cuando hay pérdida
  coclear en agudos.
- Interpicos I-III, III-V e I-V; qué hacer cuando la onda I no aparece.
- Sensibilidad del ABR frente a la resonancia en tumores chicos: cuándo el
  ABR no alcanza y el informe tiene que decirlo.

### Cap. 12 — El tronco
- Razón de amplitud V/I.
- Efecto de la tasa de estimulación como prueba de esfuerzo de la vía.
- Patrones de ausencia de ondas según el nivel de la lesión (correlación con
  los generadores I-VII).
- Fisiología: generadores (Møller) y vía auditiva central.

### Cap. 13 — Oye pero no entiende (neuropatía)
- Microfónica coclear: cambio de polaridad (rarefacción y condensación),
  inversión del trazo.
- Pinzar el tubo para separar la microfónica del artefacto de estímulo.
- Emisiones y ABR juntos: el patrón de la neuropatía.

### Cap. 14 — Lo que mueve el ABR sin ser el oído
- Factores del paciente: edad (maduración), sexo, temperatura, fármacos.
- Valores normales por edad: qué tabla usar con un prematuro, un lactante y
  un adulto.

### Cap. 15 — Cuando también cae la ósea
- ABR por vía ósea: montaje, límite de salida del vibrador, cuándo sirve.
- Enmascarar en el ABR: cuándo puede contestar el otro oído.

### Caps. 16 y 17 — El recién nacido y el lactante
- AABR de tamizaje: protocolo y momento (cap. 16).
- Umbral por frecuencia con tone burst y NB chirp; corrección de nHL a eHL
  (cap. 17; fuentes en investigacion/tecnica_b.md §8).
- Sueño natural o sedación; orden de las pruebas para no perder el examen si
  el niño se despierta.
- Vía ósea del lactante.

### Cap. 18 — El ABR que engaña (técnica y artefactos)
- Filtros, ventana de análisis y efecto de la polaridad, con ejemplos de
  trazos mal tomados.
- Promediación, FSP y ruido residual; por qué el promedio mejora con la raíz
  del número de barridos.
- Rechazo de artefactos, artefacto de estímulo, respuesta postauricular,
  falsa onda V (fuentes en investigacion/tecnica_b.md §9).

### Cap. 19 — El paciente que no calza
- ABR mejor que el audiograma en la pérdida no orgánica.

### Herramientas vecinas
- **H11 ECochG**: SP/AP y microfónica; remite al cap. 9 (hidrops) y al 13.
- **H13 PEAee**: umbral por frecuencia en el lactante; complementa al cap. 17.

## Tablas de valores normales: en el Apéndice A

El índice ya prevé el **Apéndice A, "Tablas normativas del ABR y la ECochG
por población"**. Las tablas completas y ordenadas van ahí, no en H10 ni en
los capítulos:

- **Apéndice A**: una tabla por población (recién nacido de término y
  prematuro por edad corregida, lactante, niño de 1 a 3 años, niño mayor,
  adulto, adulto mayor; por sexo donde la fuente lo separa) con latencias I,
  III y V, interpicos I-III, III-V e I-V, límite (media + 2 DE), diferencia
  interaural de la V, alargamiento con tasa alta y correcciones de nHL a eHL
  por estímulo y frecuencia. Cada tabla dice el transductor, el estímulo, la
  tasa y la fuente.
- **Fuente de los números**: las mismas tablas que usa LabSim (la normativa
  ABR con su bibliografía, "la planilla de 27 fuentes manda"), para que lo
  que el alumno ve en el simulador coincida con el libro.
- **H10** conserva solo la tabla del adulto con fonos de inserción (Sanfins
  y cols., 2026), que necesita para enseñar a leer, y remite al Apéndice A.
- **Cada capítulo** cita solo la fila que usa su caso ("para 74 años, la V a
  80 dB nHL llega hasta X ms; tabla completa en el Apéndice A"), sin copiar
  la tabla.
- La ECochG (SP/AP por electrodo) va en el mismo apéndice; H11 y el cap. 9
  remiten ahí.

Así una corrección de un valor se hace en un solo lugar.

## Pendientes del simulador que afectan al ABR

- **Cada nivel sale dos veces**: es a propósito (réplica, confirmado por él el
  2026-10-16); también en la vista previa del editor de casos.
- Ítem 7 del realismo del ABR: rampa de atenuación del canal, otros
  potenciales y modificadores fisiológicos (sin hacer).
- TODO 48: conectar al modelo los 17 parámetros de `UNCONNECTED_SETTINGS`.

## Orden sugerido

1. Cap. 11 y cap. 12 (diagnóstico neurológico), que son los que más se apoyan
   en H10.
2. Cap. 18 (técnica y artefactos), antes de los de niños: allí se aprende a
   no confundir artefacto con respuesta.
3. Caps. 13, 14, 15, 16 y 17.
4. Ejercicios en LabSim al final de cada uno.
