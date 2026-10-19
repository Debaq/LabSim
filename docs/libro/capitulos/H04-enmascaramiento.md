# H4. Enmascaramiento

:::objetivos En esta herramienta
- Explicar por qué un tono o una palabra presentados en un oído pueden oírse en el otro, y cuánto atenúa el cráneo según el transductor.
- Decidir en qué frecuencias y en qué pruebas hay que enmascarar: vía aérea, vía ósea y logoaudiometría.
- Calcular el nivel mínimo y el máximo de ruido, y buscar el umbral con el método del plateau o con la técnica abreviada por pasos.
- Reconocer la curva sombra, el sobreenmascaramiento, el efecto de oclusión y el dilema de enmascaramiento.
:::

Los fonos te dan la ilusión de que estás midiendo un oído a la vez. No es así: cuando un oído oye mucho peor que el otro, el tono que mandas al oído malo atraviesa el cráneo y lo contesta el bueno. El paciente levanta la mano de buena fe y tú anotas un umbral que no es de ese oído. El enmascaramiento es la forma de **ocupar al oído que no estás evaluando** para que no conteste por el otro. Bien hecho evita errores diagnósticos graves; mal hecho, los produce (Coles y Priede, 1970).

## Para qué sirve

Responde una sola pregunta: **¿el umbral que anoté es de este oído o del otro?**

Se usa siempre que la diferencia entre los dos oídos pueda superar lo que el cráneo atenúa:

- **Pérdidas unilaterales o asimétricas**: el oído peor siempre corre el riesgo de que conteste el mejor.
- **Vía ósea**: el vibrador hace vibrar todo el cráneo y estimula las dos cócleas casi por igual. Cada vez que la ósea sale mejor que la aérea, hay que saber de qué cóclea es.
- **Logoaudiometría**: la discriminación se mide 20 a 40 dB sobre el umbral, así que la voz cruza con frecuencia.
- **Pruebas supraliminares** de un oído (deterioro tonal, SISI, STAT): trabajan sobre el umbral y cruzan con facilidad.

Un oído anacúsico sin enmascarar aparece como una pérdida leve a moderada; una hipoacusia mixta aparece como conductiva pura; un deterioro tonal "positivo" puede ser el oído sano contestando. Todos son errores que cambian la conducta: una cirugía, un audífono o una resonancia.

## Fundamento

### Por qué cruza el sonido

Un tono presentado por un fono pone a vibrar la caja del fono y, con ella, el cráneo. Esa vibración llega a la cóclea del otro lado **por vía ósea**. La diferencia entre el nivel presentado y el que llega a la cóclea contraria es la **atenuación interaural** (AI), también llamada pérdida de transmisión transcraneal (BSA, 2018).

:::imagen ilustraciones/h04-cruce-craneo.svg ancho=100% Por qué hay que enmascarar. A: el tono de un fono supraaural hace vibrar el cráneo y llega a la otra cóclea por vía ósea, atenuado entre 40 y 80 dB según la persona: es la atenuación interaural. B: con el vibrador óseo la atenuación es casi nula, y las dos cócleas reciben lo mismo. C: el fono de inserción casi no hace vibrar el hueso y atenúa 55 dB o más.
:::

De esta idea salen dos consecuencias que ordenan todo el capítulo:

1. El tono cruzado **lo oye la cóclea**, no el oído medio. Por eso lo que importa del oído no evaluado es su **umbral óseo**, no el aéreo (BSA, 2018).
2. El ruido que pones en el oído no evaluado **también cruza**, con la misma atenuación, y puede tapar al oído que estás midiendo. Ese es el límite de cuánto ruido puedes usar.

La fisiología de la conducción ósea y del oído medio está en el capítulo B2.

### Cuánto atenúa cada transductor

La atenuación interaural **varía de una persona a otra y depende del transductor**. Con fonos supraaurales o circumaurales va de 40 a 80 dB; con fonos de inserción bien puestos es al menos de 55 dB; con el vibrador óseo es mínima o nula (BSA, 2018; Munro y Agnew, 1999). Como no sabes cuánto atenúa el cráneo de tu paciente, **se usa el mínimo**: si supones más de lo que realmente atenúa, se te pasa el cruce.

:::ayuda-ancho Atenuación interaural por transductor
| Transductor | Atenuación interaural | Valor para decidir |
|---|---|---|
| Fono supraaural o circumaural | 40 a 80 dB | **40 dB** |
| Fono de inserción bien puesto | 55 dB o más; mayor en los graves | **55 dB** |
| Vibrador óseo | casi 0 dB | **0 dB** |
| Habla con fono supraaural | similar a la de los tonos de 1 a 2 kHz | **45 dB** |

Fuentes: BSA (2018), Munro y Agnew (1999), Sklare y Denenberg (1987), Smith y Markides (1981).
:::

<!-- Pasada de fundamentos 2026-10-18: la fila del habla decía "similar a la de los tonos graves". Se corrigió a "de 1 a 2 kHz": Sklare y Denenberg (1987) encontraron que la atenuación interaural del habla se aproxima a la de 1 a 2 kHz. -->
<!-- verificar: el valor de 45 dB para el habla con supraaural es la convención de la cátedra y de LabSim (docs/decisiones.md: "suele darse 45-50 dB"); Smith y Markides 1981 no tiene resumen en PubMed y el texto no se pudo leer. -->

<!-- Protocolo ORL 2019: tabla de AI aérea por frecuencia 35/40/40/40/45/45/50/50/50 dB (125 a 8000 Hz). Se presenta como regla el mínimo de 40 dB en todas las frecuencias con supraaural y 55 dB con inserción (BSA 2018, citando a Munro y Agnew 1999); la tabla por frecuencia queda como convención del simulador (sección En LabSim), que además usa 40 en 2000 Hz y 45 en 4000 Hz. -->

Lo que cambia con el inserto es el **contacto**: el fono supraaural apoya una caja grande sobre el pabellón y la hace vibrar contra el cráneo; el inserto mete un tapón de espuma blando en el conducto y casi no transmite vibración al hueso. Por eso, cuando hay que enmascarar fuerte, el inserto es la primera opción.

### La curva sombra

Si no enmascaras, el oído peor dibuja una **curva sombra**: una copia del oído mejor, desplazada hacia abajo en la cantidad que atenúa el cráneo (BSA, 2018). El paciente de práctica 42 lo muestra en su forma más pura.

{{caso h4_p42}}

:::figura h4_p42 audiograma
- @OD 1000 | Sin enmascarar, el OD "oye" a **40 dB** en 1 kHz. No es el OD: es el tono que cruza y llega a la cóclea del OI, que oye a 0 dB.
- @OD 8000 | La curva sombra copia la forma del OI y baja con la atenuación interaural: 35 dB en 125 Hz, 50 dB en 6 y 8 kHz.
- @OD osea 1000 | La ósea del OD sale en **0 dB**. El vibrador estimula las dos cócleas y contesta la mejor.
- @OI 1000 | El OI, normal, es el que contesta todo. Juntas, la aérea y la ósea del OD dibujan una **conductiva de 40 dB que no existe**.
:::

:::figura h4_p42 audiograma 2
- @OD 1000 | Con el OI enmascarado, el OD no responde ni al máximo del audiómetro. El triángulo es el símbolo de aérea enmascarada del OD.
- @OD osea 1000 | La ósea enmascarada tampoco responde al tope del vibrador: es una **cófosis**.
- Entre las dos figuras no cambió el oído, cambió el examen. El Weber de este paciente lateralizaba al OI en 500 y 1.000 Hz: ya avisaba que el OD no aportaba nada.
:::

:::ojo Ojo clínico
Una curva que **va paralela al oído bueno, a unos 40 a 50 dB de distancia**, con la ósea normal, es una curva sombra hasta que demuestres lo contrario. Enmascara antes de informar una conductiva unilateral grande.
:::

### El ruido que enmascara

Para tapar un tono basta el ruido que cae **en la banda de frecuencias que rodea al tono** (la banda crítica); el resto del espectro solo suma molestia. Por eso:

- Para **tonos** se usa ruido de **banda estrecha**, centrado en la frecuencia del tono y de un tercio a media octava de ancho (BSA, 2018).
- Para **habla** se usa **ruido de habla** (*speech noise*), con el espectro de la voz. Una banda estrecha dejaría pasar casi todas las frecuencias de la palabra.

El ruido de banda estrecha del audiómetro viene calibrado en **nivel efectivo de enmascaramiento** (dB EM): un ruido de 1.000 Hz a 50 dB EM sube el umbral de 1.000 Hz de ese oído a 50 dB HL (BSA, 2018). Esa equivalencia uno a uno es la que hace posible calcular. Si usas un ruido de banda ancha (blanco, rosa) para tonos, necesitas más nivel para lograr el mismo efecto; esa diferencia es el **coeficiente de enmascaramiento** (CE) que se suma al cálculo. Con banda estrecha calibrada en dB EM, el CE es 0.

<!-- Protocolo ORL 2019: CE de 0 dB para banda estrecha y 15 dB para ruido blanco. LabSim usa 10 dB para blanco. No se encontró fuente verificada para la cifra del blanco: verificar. -->

:::sabias ¿Sabías que?
Aun con los oídos separados, un ruido fuerte en un oído sube unos pocos dB el umbral del otro, sin cruzar: es el **enmascaramiento central**, que ocurre en el tronco y no en la cóclea. En el gráfico del plateau se ve como una pendiente suave, mucho menor que 1 dB por dB (BSA, 2018).
:::

### Efecto de oclusión

Cuando tapas un oído con oído medio sano, su umbral **óseo mejora en los graves**. El conducto abierto deja escapar la energía de baja frecuencia que el hueso irradia hacia el conducto; tapado, esa energía queda atrapada y sube la presión sonora frente al tímpano (Fagelson y Martin, 1998). Es el fenómeno en que se basa la prueba de Bing y el que lleva el Weber al oído tapado (capítulo H2).
<!-- Pasada de fundamentos 2026-10-18: decía "Es el mismo fenómeno de la prueba de Bing (capítulo H2)" cuando H2 aún no describía el Bing. Pasada de contenidos 2026-10-18: H2 ya describe el Bing (sección "4. Schwabach y Bing"); la remisión quedó correcta. -->

:::imagen ilustraciones/h04-efecto-oclusion.svg ancho=100% El efecto de oclusión. A: con el conducto abierto, la energía de baja frecuencia que el hueso irradia al conducto se escapa por la entrada. B: tapado por la copa de un fono, queda atrapada y sube la presión frente al tímpano: los graves se oyen mejor por vía ósea. C: cuánto mejora la ósea con fono supraaural, según la tabla de este capítulo; desde 2 kHz el efecto desaparece.
:::

Importa al enmascarar la ósea: el fono que lleva el ruido **tapa al oído no evaluado**, ese oído oye mejor el tono óseo que cruza, y hace falta más ruido para taparlo. Se suma al mínimo solo cuando:

- la frecuencia es **grave** (hasta 1.000 Hz), y
- el oído no evaluado **no tiene componente conductivo**. Un oído con gap ya se comporta como tapado y no gana nada más.

:::ayuda Efecto de oclusión con fono supraaural
| 250 Hz | 500 Hz | 1.000 Hz | 2.000 Hz y más |
|---|---|---|---|
| 15 dB | 15 dB | 10 dB | 0 dB |

Con un inserto bien profundo el efecto casi desaparece (Dean y Martin, 2000).
:::

<!-- verificar: la tabla 15/15/10/0 es la de la cátedra y la que usa LabSim. Otras tablas publicadas para supraaural crecen hacia los graves (del orden de 20 a 30 dB en 250 Hz; Studebaker y Yacullo, según docs/decisiones.md, sin cita completa). -->

## Antes de empezar

- **Umbrales sin enmascarar de los dos oídos**, aéreos y óseos. Las reglas se aplican sobre ellos; sin la ósea no puedes saber si hay cruce por vía aérea.
- **Audiómetro de dos canales**: el canal 1 lleva el tono al oído evaluado y el canal 2 el ruido al otro, con ruido de banda estrecha calibrado en dB EM y ruido de habla.
- **Transductor para el ruido**: para la ósea conviene un **inserto** en el oído no evaluado, por comodidad y por su mayor atenuación interaural; el fono supraaural se usa si no hay otra opción (BSA, 2018). El vibrador queda en la mastoides del oído evaluado, sin tocar el pabellón.
- **Instrucción**: el paciente va a oír un ruido constante que a veces sube; tiene que **ignorarlo** y avisar solo cuando oiga el tono, **en el oído que sea**. Nunca le digas en qué oído debería oírlo: si supiéramos dónde lo oye, no haría falta enmascarar (BSA, 2018).
- **Cuidado con los niveles altos**: sobre 80 dB EM de ruido o 100 dB HL de tono hay que avanzar con precaución, y en pacientes con acúfeno el ruido puede empeorarlo (BSA, 2018).
- Ten a mano una **planilla de enmascaramiento**: un gráfico con el ruido en el eje horizontal y el umbral en el vertical, en escala 1:1.

## Paso a paso

### 1. Decidir dónde enmascarar

Las reglas se aplican **frecuencia por frecuencia**. El oído evaluado es el que recibe el tono; el no evaluado es el que se enmascara (BSA, 2018).

:::ayuda-ancho Cuándo enmascarar
| | Regla | Con supraaural | Con inserto |
|---|---|---|---|
| **Aérea (regla 1)** | diferencia entre los umbrales aéreos sin enmascarar de los dos oídos | 40 dB o más | 55 dB o más |
| **Ósea (regla 2)** | la ósea sin enmascarar es mejor que la aérea de cualquiera de los dos oídos | 10 dB o más | 10 dB o más |
| **Aérea (regla 3)** | la ósea de un oído es mejor que la aérea sin enmascarar del otro, aunque la regla 1 no se cumpla | 40 dB o más | 55 dB o más |
| **Logoaudiometría** | nivel de presentación menos el promedio óseo del oído no evaluado | 45 dB o más | — |
:::

La **regla 3** es la que más se olvida: dos oídos con la misma pérdida aérea no necesitan enmascarar por la regla 1, pero si uno tiene la cóclea sana (ósea buena), el tono del otro le llega igual. Recuerda que el cruce lo decide la **cóclea** del oído no evaluado (BSA, 2018).

<!-- Protocolo ORL 2019: en logoaudiometría decía "cuando la diferencia de la intensidad de evaluación supera en al menos una AI de la voz (45 dB)". Se precisó contra qué se compara: el promedio óseo del oído no evaluado, igual que en tonos (BSA 2018, regla 3 y notas). -->

### 2. Cuánto ruido: mínimo y máximo

El ruido tiene una ventana. Por debajo del **mínimo**, el oído no evaluado sigue oyendo el tono cruzado (**subenmascaramiento**). Por encima del **máximo**, el ruido cruza de vuelta y tapa al oído que estás midiendo (**sobreenmascaramiento**). El método de fórmula consiste en calcular los dos bordes y elegir un nivel al medio (Studebaker, 1964, 1967; Yacullo, 1999).

<!-- Pasada de fundamentos 2026-10-18: el verificar del punto medio se resolvió con Yacullo 1999 (resumen: "the goal is to select a masking level that falls at the middle of the masking plateau"). Studebaker 1964 y 1967 siguen como origen del método de fórmula; no tienen resumen en PubMed. -->

:::ayuda-ancho Fórmulas de nivel mínimo y máximo
**Vía aérea**

- Mínimo = UA evaluado − AI − UO no evaluado + UA no evaluado + CE (o sea, lo que cruza más el gap del no evaluado)
- Máximo = UO evaluado + AI

**Vía ósea** (el tono cruza sin atenuación; el ruido, por fono)

- Mínimo = UO evaluado − UO no evaluado + UA no evaluado + CE + efecto de oclusión
- Máximo = UO evaluado + AI del fono que lleva el ruido

**Logoaudiometría** (AI del habla, 45 dB; promedios tonales de las frecuencias del habla)

- Mínimo = nivel de presentación − 45 − PTP óseo no evaluado + PTP aéreo no evaluado
- Máximo = PTP óseo evaluado + 45

UA: umbral aéreo. UO: umbral óseo. AI: atenuación interaural. CE: coeficiente de enmascaramiento del ruido. PTP: promedio tonal.
:::

Cada término tiene una razón:

- **UA evaluado − AI** es lo que llega a la cóclea contraria. El ruido tiene que superar eso.
- **+ gap del no evaluado**: el ruido entra por vía aérea a un oído que, si tiene componente conductivo, lo atenúa. Hay que subirlo en lo que pierde.
- **Máximo = UO evaluado + AI**: el ruido que pones cruza con la atenuación del fono que lo lleva y llega a la cóclea evaluada por vía ósea. Mientras llegue por debajo de su umbral óseo, no la tapa.

<!-- Protocolo ORL 2019: para la vía ósea, "Máximo = umbral óseo del oído estudiado + atenuación interaural de la vía ósea" (0 dB), lo que deja el máximo igual al umbral óseo y vuelve imposible casi cualquier enmascaramiento óseo. Se corrigió a UO evaluado + AI del fono que entrega el ruido: el ruido va por fono y cruza con la atenuación del fono (BSA 2018, sección 8.9.4: el sobreenmascaramiento depende de la ósea del oído evaluado y es menor con inserto; Studebaker 1964). Es el mismo error que se corrigió en el simulador (docs/decisiones.md, "la IA del ruido es la del fono"). -->

**Un ejemplo con el paciente 41** (otitis crónica del OI, más adelante en este capítulo). En 1.000 Hz el OD tiene 0 dB aéreo y óseo; el OI, 50 dB aéreo y 25 dB óseo. Con supraaural y banda estrecha:

- Aérea del OI: mínimo = 50 − 40 − 0 + 0 = **10 dB**; máximo = 25 + 40 = **65 dB**. Un ruido de unos 40 dB EM en el OD está holgado.
- Ósea del OI: mínimo = 25 − 0 + 0 + 10 (oclusión, porque el OD es normal) = **35 dB**; máximo = 25 + 40 = **65 dB**. El ruido tiene que ir entre 35 y 65.

### 3. El método del plateau

Las fórmulas suponen que conoces los umbrales verdaderos, que es justo lo que estás buscando. El **método del plateau** no supone nada: sube el ruido de a poco y mira qué hace el umbral (Hood, 1960). Es el que recomienda la BSA (2018) para aérea y ósea.

![Gráfico de enmascaramiento en escala 1:1: eje horizontal "ruido en el oído no evaluado (dB EM)", eje vertical "umbral del oído evaluado (dB HL)". Una línea con cuatro tramos y sus rótulos: (a) corto tramo plano al inicio, "el ruido se oye pero aún no enmascara"; (b) subida a 45 grados, "subenmascaramiento: el umbral sube 1 dB por cada dB de ruido, contesta el oído no evaluado"; (c) tramo plano largo, "plateau: umbral verdadero"; (d) segunda subida a 45 grados, "sobreenmascaramiento: el ruido cruza y tapa al oído evaluado". Una flecha horizontal en el eje vertical marca el umbral sin enmascarar.](ilustraciones/h04-grafico-meseta.png)

1. **Vuelve a buscar el umbral sin ruido**, para que el paciente recuerde qué escuchar. En la ósea es obligatorio, porque necesitas el umbral con el oído no evaluado ya tapado por el fono.
2. **Pon el ruido** en el oído no evaluado, partiendo de un nivel igual a su umbral aéreo en esa frecuencia. Espera unos segundos por si contesta al ruido.
3. **Busca el umbral** con el ruido puesto. Ese es el umbral para ese nivel de ruido.
4. **Sube el ruido 10 dB** y vuelve a buscar el umbral.
5. **Repite** hasta tener al menos cuatro mediciones y **tres seguidas con el mismo umbral** (o una que se aleje solo 5 dB de las otras dos). Eso es el **plateau**: el umbral que más se repite es el verdadero (BSA, 2018).

<!-- Protocolo ORL 2019: subir el ruido de 5 en 5 dB y pedir una meseta de 4 intensidades. Se corrigió al procedimiento de la BSA 2018 (sección 8.8): pasos de 10 dB, al menos 4 mediciones y 3 seguidas con el mismo umbral (±5 dB); pasos de 5 dB solo cuando la meseta se acorta. -->

Cómo se lee el gráfico (BSA, 2018):

- Si el umbral **no se mueve** desde el comienzo, no había cruce: el umbral sin enmascarar era el verdadero.
- Si **sube 1 dB por cada dB de ruido**, sigue contestando el oído no evaluado: falta ruido.
- Cuando **se aplana**, encontraste el umbral verdadero.
- Si después del plateau **vuelve a subir 1 dB por dB**, el ruido está cruzando: es sobreenmascaramiento. Pasa sobre todo cuando el oído evaluado tiene una conductiva con buena ósea y el no evaluado tiene al menos una pérdida moderada. Ahí conviene subir de a **5 dB** para no saltarse un plateau corto; a veces dos puntos bastan.
- Si sube **menos de 1 dB por dB**, de forma sostenida, es enmascaramiento central.

:::ayuda Ayuda memoria del plateau
**Pendiente 1:1** = falta ruido o sobra ruido. **Plano** = umbral verdadero. Lo que importa no es un número, es la **forma**.
:::

### 4. La técnica por pasos

Cuando hay que enmascarar varias frecuencias y el tiempo es poco, se usa una versión abreviada que solo mira si el umbral se mueve con saltos grandes de ruido:

1. **Ruido inicial**: 30 dB sobre el umbral aéreo del oído no evaluado para la vía aérea; 20 dB sobre ese umbral para la ósea, **más el efecto de oclusión** si el oído no evaluado es normal o sensorioneural (no si tiene componente conductivo). El efecto de oclusión se suma solo en este primer nivel.
2. **Busca el umbral** con ese ruido. Si no cambia, es el umbral verdadero.
3. Si **sube 15 dB o más**, sube el ruido **20 dB** y vuelve a buscarlo.
4. Repite hasta que un salto de 20 dB de ruido ya no mueva el umbral.

Un corrimiento de 10 dB queda en la zona gris: trátalo como corrimiento y da un paso más, porque una medición repetida solo admite una diferencia de 5 dB (BSA, 2018). Si el resultado sigue dudoso, vuelve al plateau.

<!-- Protocolo ORL 2019: el corte para subir el ruido era un corrimiento de 15 dB o más, sin decir qué hacer con 10 dB. Se agregó la indicación de la zona gris con el criterio de ±5 dB de la BSA 2018 (8.9.1). -->

<!-- verificar: no se encontró la fuente citable de la "técnica por pasos" (step masking) con ruido inicial de 30 dB (aérea) y 20 dB (ósea) y pasos de 20 dB. La BSA 2018 desaconseja técnicas distintas del plateau. -->

### 5. La vía ósea

En la ósea el cruce es la regla, no la excepción: con una atenuación casi nula, la ósea sin enmascarar es la de **la mejor cóclea**, esté donde esté el vibrador. El paciente 41 muestra qué pasa si no se enmascara.

{{caso h4_p41}}

:::figura h4_p41 audiograma
- @OI 1000 | Sin enmascarar, el OI marca **40 dB** en 1 kHz: la curva sombra del OD, que es normal.
- @OI osea 1000 | La ósea del OI sale en **0 dB**: la contesta la cóclea del OD.
- Leído así, el OI tiene una **conductiva pura**. Con gap de 40 dB, cóclea normal: un buen candidato a cirugía.
:::

:::figura h4_p41 audiograma 2
- @OI 1000 | Enmascarado, el aéreo del OI está en **50 dB**: 10 dB peor que lo anotado.
- @OI osea 1000 | La ósea enmascarada del OI está en **25 dB**, no en 0.
- @OI osea 4000 | En 4 kHz llega a **45 dB**: la cóclea del OI también está dañada. Es una **mixta**, con un pronóstico auditivo distinto.
:::

:::ojo Ojo clínico
La ósea sin enmascarar **nunca** te dice de qué oído es. Si vas a informar un gap, enmascara la ósea del oído con gap en al menos 500, 1.000 y 2.000 Hz.
:::

### 6. Logoaudiometría

La lógica es la misma, con habla y ruido de habla. El cruce se hace evidente en la discriminación, porque el oído bueno entiende casi todo con muy poco nivel.

:::figura h4_p42 logoaudiometria
- @OD 40 | Sin enmascarar, el OD anacúsico ya "entiende" el **20 %** a 40 dB, y a 45 dB la mitad: al OI llegan 0 dB, su SRT.
- @OD 80 | A 80 dB repite el **100 %**. Es la curva del OI corrida 45 dB: lo que llega al OI son 35 dB, y a 35 dB el OI entiende todo.
:::

:::figura h4_p42 logoaudiometria 2
- @OD 80 | Con ruido de habla en el OI, el OD no repite ninguna palabra a 80 dB.
- @OI 35 | El OI llega al 100 % desde 35 dB. Para medir el OD a 80 dB, el mínimo de ruido en el OI es 80 − 45 − 0 + 0 = **35 dB**.
:::

El umbral de discriminación (UMD) se mide 20 a 40 dB sobre el SRT. En un oído con pérdida y el otro normal, eso casi siempre cruza: **el UMD del oído peor se enmascara por regla**.

### 7. El dilema de enmascaramiento

En una pérdida conductiva **bilateral** con gaps grandes, el mínimo puede quedar **por encima** del máximo: el ruido que hace falta para tapar al oído no evaluado ya es suficiente para cruzar y tapar al evaluado (Naunton, 1960). No hay nivel correcto.

{{caso h4_dilema}}

:::figura h4_dilema audiograma
- @OD 250 | En 250 Hz el OD está en 50 dB aéreo y 0 óseo. El OI, en 55 y 0. Con supraaural, para medir el OD: mínimo = 50 − 40 − 0 + 55 = **65 dB**; máximo = 0 + 40 = **40 dB**. No hay ventana.
- @OI 250 | La diferencia aérea entre los oídos es de 5 dB y la regla 1 no se cumple. Pero la ósea del OD (0) está 55 dB mejor que el aéreo del OI: la **regla 3** obliga a enmascarar.
- @OD osea 500 | En la ósea pasa lo mismo: en 500 Hz el mínimo es 50 y el máximo 45.
- @OD 1000 | En 1 kHz el gap baja a 35 dB y la ventana se abre apenas: de 45 a 50 dB.
:::

La salida es el **inserto**. Con 55 dB de atenuación, en 250 Hz el mínimo baja a 50 − 55 − 0 + 55 = 50 dB y el máximo sube a 0 + 55 = 55 dB: hay ventana, angosta. Al subir la atenuación, el mínimo baja y el máximo sube a la vez. Si ni así se encuentra el plateau, se informa el umbral como **no enmascarable** (BSA, 2018).

:::sabias ¿Sabías que?
Con gaps iguales en los dos oídos, el dilema aparece cuando el gap **supera la atenuación interaural**: con supraaural, sobre unos 40 dB. Por eso las otoesclerosis bilaterales avanzadas y las otitis crónicas bilaterales son los casos clásicos.
:::

## Cómo se informa

- Cada umbral obtenido con ruido lleva el **símbolo enmascarado** (aérea: triángulo en el OD, cuadrado en el OI; ósea: corchetes). Un símbolo sin enmascarar le dice al lector que no hubo riesgo de cruce o que no se enmascaró.
- Si el oído no responde al máximo del equipo **con enmascaramiento**, se dibuja el símbolo enmascarado con la **flecha hacia abajo**, sin unirlo a la línea.
- Si el plateau no se pudo definir (dilema, molestia, tope del equipo), se marca en el audiograma y se dice en el informe: el umbral es **dudoso** o **no enmascarable** (BSA, 2018).
- Se anota el **transductor** del ruido y el **tipo de ruido**. Puede anotarse también el nivel de ruido con que se definió el plateau.
- En la logoaudiometría se anota el nivel de **ruido de habla** usado en cada medición.

:::comentario Un ejemplo de informe
*Audiometría tonal con enmascaramiento contralateral (banda estrecha) en OD. OD sin respuesta por vía aérea ni ósea al máximo del equipo. OI con audición normal. Logoaudiometría: OD 0 % de discriminación con ruido de habla contralateral; OI 100 % a 40 dB. Conclusión: cófosis del OD.*
:::

## Errores frecuentes

- **No enmascarar la ósea** "porque la aérea no lo pedía". La ósea cruza siempre: es el error que convierte una mixta en conductiva (Coles y Priede, 1970).
- **Comparar con el aéreo del oído no evaluado** en vez de con su óseo. Se pierde el cruce en los casos de la regla 3.
- **Usar una atenuación más alta que el mínimo**, "porque el paciente tiene la cabeza grande". La AI no se ve desde afuera.
- **Enmascarar con un solo nivel de ruido** y no mirar si el umbral cambia. Un nivel fijo puede quedar bajo el mínimo o sobre el máximo sin que lo notes.
- **Ruido equivocado**: banda estrecha para habla o ruido de habla para tonos sin corregir el CE.
- **Olvidar el efecto de oclusión** en la ósea grave, o sumarlo cuando el oído no evaluado tiene componente conductivo.
- **Decirle al paciente dónde va a oír el tono**. Contesta lo que esperas, no lo que oye.
- **Seguir subiendo el ruido después del plateau**: el umbral vuelve a subir por sobreenmascaramiento y lo anotas como verdadero.

:::ojo Ojo clínico
Antes de firmar un audiograma con una asimetría o un gap, haz una sola pregunta por cada símbolo: **¿pudo contestar el otro oído?** Si la respuesta es sí y el símbolo no está enmascarado, el audiograma no está terminado.
:::

## En LabSim

El audiómetro del simulador tiene dos canales. Para enmascarar, deja el tono en el canal del oído evaluado y en el otro canal elige un ruido (banda estrecha, blanco, rosa o de habla) y el oído no evaluado como salida. El paciente simulado contesta según de dónde le llegue el tono:

- Con el ruido **bajo el mínimo**, contesta por el otro oído: la curva sombra, que **sube dB a dB** a medida que subes el ruido. Es el tramo inclinado del gráfico del plateau.
- Con el ruido **dentro de la ventana** (entre el mínimo y el máximo), contesta su umbral verdadero y deja de moverse aunque subas el ruido: la **meseta**.
- Con el ruido **sobre el máximo**, el umbral vuelve a **subir dB a dB**: el ruido cruzó y está tapando el oído que evalúas. Lo sobreenmascaraste.

Por eso el método del plateau funciona igual que con un paciente real: sube el ruido de a 10 dB y mira si el umbral se mueve.

Lo que usa el simulador para calcular:

- **Atenuación interaural aérea**, fono supraaural: 35 dB en 125 Hz, 40 dB de 250 a 2.000 Hz, 45 dB en 3 y 4 kHz y 50 dB en 6 y 8 kHz. **Ósea**: 0 dB. **Habla**: 45 dB. La audiometría tonal no tiene todavía fono de inserción.
- **Coeficiente de enmascaramiento** para tonos: banda estrecha 0, rosa 5, blanco y ruido de habla 10 dB. Para habla: ruido de habla 0, blanco y rosa 5, banda estrecha 20 dB. Con el ruido equivocado el paciente sigue oyendo hasta que subes la diferencia.
- **Efecto de oclusión** en la ósea: 15 dB de 125 a 500 Hz y 10 dB en 1.000 Hz, solo si el oído no evaluado no tiene gap.
- En la **logoaudiometría**, el sobreenmascaramiento corre la curva de a poco, no de golpe.

Los audiogramas del libro que dicen "sin enmascarar" están calculados con la misma regla: aérea = la ósea del otro oído más la atenuación de la frecuencia; ósea = la mejor de las dos.

:::ojo Ojo con el dilema
Cuando el mínimo queda sobre el máximo, el simulador se comporta como el paciente real: **no hay meseta**. El umbral sigue subiendo con el ruido y, como mucho, pasa una vez por el valor verdadero sin quedarse ahí. Si no encuentras tres niveles seguidos con el mismo umbral, haz la cuenta: un mínimo mayor que el máximo es el dilema, y eso es lo que se informa.
:::

:::pregunta Preguntas para practicar
1. En el paciente 42, calcula el ruido mínimo en el OI para confirmar que el OD no responde a 110 dB en 1 kHz. ¿Cabe en un audiómetro clínico? ¿Qué cambia con un inserto?
2. En el paciente 41, mide la ósea del OI en 500 Hz con la técnica por pasos. ¿Con qué ruido partes? ¿Por qué sumas el efecto de oclusión?
3. En el paciente 34 (otoesclerosis del OD), la ósea sin enmascarar sale casi normal en todas las frecuencias. ¿De qué oído es? Calcula la ventana de ruido para la ósea del OD en 1 kHz.
4. Arma en LabSim un caso de otoesclerosis bilateral y busca una frecuencia con dilema. ¿Qué harías en el box real?
:::

## Referencias

1. British Society of Audiology. Recommended procedure: pure-tone air-conduction and bone-conduction threshold audiometry with and without masking [Internet]. BSA; 2018 ago [citado 2026 oct 15]. Disponible en: https://www.thebsa.org.uk/wp-content/uploads/2024/01/Recommended-Procedure-Pure-Tone-Audiometry-2018.pdf
1. Hood JD. The principles and practice of bone conduction audiometry: a review of the present position. Laryngoscope. 1960;70(9):1211-28. doi:10.1288/00005537-196009000-00001
1. Naunton RF. A masking dilemma in bilateral conduction deafness. Arch Otolaryngol. 1960;72(6):753-7. doi:10.1001/archotol.1960.00740010767008
1. Studebaker GA. Clinical masking of air- and bone-conducted stimuli. J Speech Hear Disord. 1964;29(1):23-35. doi:10.1044/jshd.2901.23
1. Studebaker GA. Clinical masking of the nontest ear. J Speech Hear Disord. 1967;32(4):360-71. doi:10.1044/jshd.3204.360
1. Munro KJ, Agnew N. A comparison of inter-aural attenuation with the Etymotic ER-3A insert earphone and the Telephonics TDH-39 supra-aural earphone. Br J Audiol. 1999;33(4):259-62. doi:10.3109/03005369909090106
1. Sklare DA, Denenberg LJ. Interaural attenuation for Tubephone insert earphones. Ear Hear. 1987;8(5):298-300. doi:10.1097/00003446-198710000-00008
1. Smith BL, Markides A. Interaural attenuation for pure tones and speech. Br J Audiol. 1981;15(1):49-54. doi:10.3109/03005368109108954
1. Coles RR, Priede VM. On the misdiagnoses resulting from incorrect use of masking. J Laryngol Otol. 1970;84(1):41-63. doi:10.1017/s0022215100071620
1. Fagelson MA, Martin FN. The occlusion effect and ear canal sound pressure level. Am J Audiol. 1998;7(2):50-4. doi:10.1044/1059-0889(1998/010)
1. Dean MS, Martin FN. Insert earphone depth and the occlusion effect. Am J Audiol. 2000;9(2):131-4. doi:10.1044/1059-0889(2000/011)
1. Yacullo WS. Clinical masking in speech audiometry: a simplified approach. Am J Audiol. 1999;8(2):106-16. doi:10.1044/1059-0889(1999/019). PMID 10646194.
