# H10. Potenciales evocados auditivos de tronco

:::objetivos En esta herramienta
- Explicar de dónde sale cada onda del ABR y por qué hay que promediar miles de barridos para verla.
- Preparar al paciente, montar los electrodos y configurar el equipo sabiendo para qué sirve cada parámetro.
- Buscar el umbral de la onda V con click y con estímulos por frecuencia, y llevarlo de dB nHL a una estimación en dB HL.
- Medir latencias, interpicos y diferencia interaural, y reconocer los patrones conductivo, coclear, retrococlear y de neuropatía.
- Saber qué puede y qué no puede decir un ABR por vía ósea y un AABR de tamizaje.
- Reconocer los artefactos que se disfrazan de onda, incluida la falsa onda V.
:::

Los potenciales evocados auditivos de tronco (PEAT, PEATC o BERA; en inglés *auditory brainstem response*, **ABR**, que es como lo llama LabSim) son la respuesta eléctrica del nervio auditivo y del tronco cerebral a un sonido breve. No piden nada al paciente: puede estar dormido, sedado o ser un recién nacido. Por eso son el examen que responde cuando la audiometría no puede, y el que mira más allá de la cóclea cuando la audiometría no alcanza. A cambio, exigen técnica: la respuesta es tan chica que, mal registrada, cualquier ruido parece una onda.

## Para qué sirve

El ABR responde tres preguntas distintas, y cada una se hace de otra manera:

1. **¿Hasta qué intensidad responde la vía?** Es la búsqueda del **umbral de la onda V**: la intensidad más baja a la que la onda V aparece y se repite. Se usa para estimar la audición de quien no puede hacer una audiometría confiable: lactantes, niños pequeños, personas con discapacidad cognitiva y quienes exageran o simulan una pérdida (→ cap. 17 y 19).
2. **¿La señal viaja a tiempo?** Es el ABR **neurootológico**: a una intensidad alta se miden las latencias y los intervalos entre ondas para buscar un retraso en el nervio o en el tronco, como el de un schwannoma vestibular o una esclerosis múltiple (→ cap. 11 y 12).
3. **¿Este recién nacido necesita estudio?** Es el **AABR** de tamizaje: un equipo automático estimula a una sola intensidad y contesta PASA o REFIERE (→ cap. 16).

Conviene tener claros sus límites desde el principio:

- El ABR **no es una audiometría**. Mide si un grupo de neuronas descarga **sincronizado**, no si la persona oye. Una neuropatía auditiva puede dejarlo plano con un audiograma casi normal (→ cap. 13), y una lesión por encima del tronco puede dejarlo normal en alguien que no entiende nada.
- El click, que es el estímulo de rutina, informa sobre todo de la zona de **2 a 4 kHz** (Stapells y Oates, 1997). No dice nada de los graves: para eso hacen falta estímulos por frecuencia.
- Un ABR alterado **no dice la causa**. Un tumor del ángulo y un meningioma dan el mismo trazado: el ABR describe un patrón, y la imagen dice qué lo produce.

## Fundamento

### Una respuesta muy chica dentro de mucho ruido

Cuando un sonido breve llega a la cóclea, miles de fibras del nervio auditivo descargan casi al mismo tiempo. Esa descarga, y la de los núcleos que siguen, produce un campo eléctrico que llega hasta la piel. Unos electrodos en el vértex y detrás de la oreja lo recogen como una serie de ondas positivas en los primeros 10 ms. Jewett y Williston (1971) las describieron en el ser humano y les pusieron los números romanos que se usan hasta hoy.

El problema es el tamaño. La onda V de un adulto normal mide alrededor de **0,5 µV** (Da Silva Nunes y Gentile Matas, 2005). El EEG de fondo y la actividad de los músculos, en la misma banda, son varias veces más grandes. En un solo barrido la respuesta es invisible.

La solución es **promediar**. Se repite el estímulo miles de veces y se suman los tramos de señal que siguen a cada uno. La respuesta aparece siempre a la misma latencia y se suma; el ruido aparece al azar y se cancela. El ruido que queda (el **ruido residual**) baja con la raíz cuadrada del número de barridos: para dejarlo a la mitad hay que promediar **cuatro veces más** (Picton, 2010). Por eso no basta "un poco más": de 1.000 a 2.000 barridos el ruido baja solo un 30 %.

### Quién genera cada onda

Los registros intracraneales hechos durante cirugías permitieron asignar cada onda a una estación de la vía (Møller y cols., 1981; Møller y Jannetta, 1983):

- **Onda I**: la porción **distal** del nervio auditivo, junto a la cóclea.
- **Onda II**: la porción **proximal** del nervio, donde entra al tronco.
- **Onda III**: el **núcleo coclear**, en la parte baja de la protuberancia.
- **Onda IV**: el **complejo olivar superior**.
- **Onda V**: el **lemnisco lateral** al llegar al **colículo inferior**, en la parte alta del tronco.

Es un mapa útil, pero no literal: cada onda recibe aportes de varias poblaciones de neuronas, y una misma estación contribuye a más de una onda (Melcher y Kiang, 1996). Las ondas VI y VII son inconstantes y no se usan en la clínica.

:::imagen ilustraciones/h10-generadores.png ancho=100% La vía auditiva y el PEAT en labyrinthus3d, el simulador del autor (módulo Auditivo, pestañas Tronco y PEAT)
- @-2,90 | **Cóclea y nervio VIII**: la onda I sale de la porción distal del nervio y la II de la proximal, donde entra al tronco.
- @-2,68 | **Núcleo coclear**: la onda III.
- @22,57 | **Complejo olivar superior** (MSO, LSO y MNTB): la onda IV. Desde aquí la vía cruza y los dos oídos se comparan.
- @22,33 | **Lemnisco lateral** llegando al **colículo inferior**: la onda V.
- @50,22 | Cada onda aparece cuando la señal llega a su estación, con el retardo de cada tramo.
- @84,18 | La **V** es la más alta y la más estable: es la que se sigue al bajar la intensidad.
- @98,70 | Los **interpicos** miden el viaje dentro de la vía: I-III, III-V e I-V.
:::
<!-- Imagen: capturas de labyrinthus3d (hacer_h10_peat.py, montaje en la conversación del 2026-10-16). Las latencias de la tabla son del modelo del simulador, órdenes de magnitud docentes, no valores de referencia. Desde el 2026-10-16 labyrinthus3d usa la misma asignación de Møller que el texto (I y II nervio, III núcleo coclear, IV olivar, V lemnisco/colículo). -->

De ese mapa sale la lectura clínica de los **interpicos**:

- **I-III**: del nervio a la protuberancia baja. Se alarga en las lesiones del nervio, como el schwannoma vestibular.
- **III-V**: la parte alta del tronco.
- **I-V**: el **tiempo de conducción central**. Como empieza en la onda I, no depende de cuánto sonido llegó a la cóclea: es la medida más robusta del examen.

### Latencia e intensidad

Al bajar la intensidad, las ondas llegan **más tarde** y son **más chicas**. Las primeras en perderse son la I y la III; la V es la que llega más cerca del umbral, y por eso el umbral del ABR es el **umbral de la onda V**. La onda V pasa de unos 5 a 6 ms a 90 dB nHL a unos 8 a 9 ms a 20 dB nHL (ACNS, 2008).

La razón está en la cóclea. A intensidad alta, el click excita con fuerza la base, que responde primero. A intensidad baja, la respuesta depende de regiones más apicales, donde la onda viajera llega después, y además la descarga tarda más en sincronizarse. Los interpicos, en cambio, casi no cambian con la intensidad: todas las ondas se corren juntas detrás de la I. Por eso son el parámetro neurológico preferido.

La curva que une la latencia de la V con la intensidad es la **función latencia-intensidad**. No es una recta: es plana a intensidad alta y se empina a medida que se acerca al umbral, alrededor de 0,3 ms por cada 10 dB entre 70 y 50 dB nHL (Hood, 1998; Delgado Hernández y cols., 2003). Su forma cambia con el tipo de pérdida, y ahí está buena parte del diagnóstico (ver "Cómo se informa").

### dB nHL: el cero del ABR

Los estímulos del ABR duran microsegundos o milisegundos, y un sonido tan breve se oye peor que un tono continuo. Por eso el ABR no usa dB HL sino **dB nHL** (*normalized hearing level*): **0 dB nHL es el nivel al que un grupo de adultos jóvenes con audición normal detecta ese mismo estímulo**, en ese mismo equipo. Cada estímulo tiene su propio cero.

Un detalle importante: el umbral de la onda V no cae en 0 dB nHL en un oído normal, sino algo más arriba. El sistema nervioso necesita algo de nivel para descargar con la sincronía que el promedio puede detectar. Por eso, para estimar el audiograma, al umbral del ABR se le **resta una corrección** (ver "Umbral por frecuencia").

:::sabias ¿Sabías que?
El ABR no cambia con el sueño, con la sedación habitual ni con la atención del paciente (Hall, 2007). Lo que sí lo cambian son la edad, el sexo, la temperatura y algunos fármacos (→ cap. 14). Por eso puede hacerse a un recién nacido dormido en brazos de su madre.
:::

## Antes de empezar

### Equipo

- **Equipo de potenciales evocados**: un generador de estímulos, un **preamplificador** cerca del paciente y un promediador en el computador.
- **Electrodos** de superficie, **gel abrasivo**, **gel conductor** y cinta adhesiva; alcohol y algodón.
- **Fonos de inserción**, rojo para el oído derecho y azul para el izquierdo, con olivas de varios tamaños. Además del confort, tienen tres ventajas: aíslan mejor del ruido de la sala, el sonido cruza mucho menos al otro oído y el transductor queda lejos de los electrodos, así que produce menos artefacto.
- **Vibrador óseo** para el ABR por vía ósea.
- **Otoscopio**, una **camilla** y una **manta**. Se trabaja con la luz apagada.

Con fonos de inserción el sonido demora cerca de 1 ms en recorrer el tubo. Algunos equipos lo descuentan y otros no. Da lo mismo cómo lo haga el tuyo, siempre que los valores normales que uses se hayan medido con **el mismo transductor**: cada laboratorio debe construir su norma con el mismo equipo y protocolo que usa en la clínica (Sanfins y cols., 2026; ACNS, 2008).

### Conoce tu equipo: el ABR de LabSim

El ABR de LabSim tiene la lógica de cualquier equipo clínico: los parámetros a la izquierda, las curvas de cada oído al centro, los valores que mides a la derecha y, abajo, lo que está pasando mientras registras. La figura muestra un examen en curso: el OD ya está registrado de 80 a 20 dB nHL y el OI va en 40.

:::imagen /docs/manual/img/estudiante/abr.png El ABR de LabSim durante una búsqueda de umbral
- @-2.5,11 | **Estímulo y polaridad.** *Click*, *CE-Chirp* y *CE-Chirp LS* (de banda ancha), y los de frecuencia: *NB CE-Chirp LS* y *Burst* de 500 Hz a 4 kHz. La polaridad: alternada, condensación o rarefacción.
- @-2.5,17.5 | **Intensidad** en dB nHL y, debajo, el **Masking**: el ruido que va al oído contrario.
- @-2.5,26.5 | **Tasa** (estímulos por segundo) y **filtros**: *Pasa bajo* y *Pasa alto* fijan la banda de registro.
- @-2.5,34.3 | **Pinzar tubo.** Bloquea el tubo del fono de inserción: el sonido no llega, pero el artefacto eléctrico del transductor sigue.
- @-2.5,40.5 | **Promediación** (cuántos barridos va a sumar la curva) y **lado**.
- @63,5.7 | **Línea de estado** de la curva que se registra: nivel y oído, barridos, aceptados, FSP, ruido residual, replicabilidad (*repro*) y el veredicto del equipo.
- @38,12.5 | **Las ondas marcadas.** Se marcan con las banderas **A** y **A'**, que se arrastran sobre el trazo.
- @51.3,21 | **Rótulo de intensidad.** Un clic en él elige la curva con la que vas a trabajar.
- @88.5,5.6 | **Valores.** Latencia y amplitud de cada onda, por oído.
- @95.5,25.8 | **Variables**: los interpicos y la razón V/I se calculan solos. Lo que queda fuera de la norma se pinta en rojo.
- @10,79.5 | **EEG** en vivo de los dos canales. Si está sucio, el promedio va a salir sucio.
- @78.5,88 | **FSP y ruido residual** contra los barridos. La línea roja es el criterio de detección.
:::

Lo demás está en **Archivo → Parámetros avanzados**: el transductor, el montaje, los electrodos y sus impedancias, el rechazo de artefactos y el criterio de detección. El equipo **no viene configurado**: la tasa y las promediaciones arrancan con valores al azar, y dejarlo bien puesto es parte del examen.

### Preparar al paciente

**La quietud es todo.** El ABR no cambia con el sueño, pero el músculo tenso sí ensucia el registro. Por eso aquí el examen se hace con el paciente **dormido**, y si no duerme, no se hace. Las indicaciones se dan al citarlo:

- **Lactantes y niños pequeños**: dormir no más de 5 horas la noche anterior, no dejarlos dormir en el camino ni en la sala de espera y alimentarlos justo antes del examen (hay que traer la comida).
- **Adultos**: dormir no más de 5 horas la noche anterior, venir con ropa cómoda y no tomar café, bebidas estimulantes ni alcohol antes del examen.

El ABR diagnóstico toma alrededor de **una hora**.

Antes de poner un electrodo:

1. **Otoscopía** (→ H1). Un tapón de cerumen que ocluye el conducto suma una pérdida conductiva que no es del paciente y no deja poner el fono: se deriva para extraerlo y se reagenda.
2. **Anamnesis** (→ H1). En lactantes se agrega: semanas de gestación, enfermedades del embarazo, complicaciones del parto, días en UCI neonatal, fármacos y antecedentes familiares de hipoacusia.
3. **Explicar el examen**. Al adulto, o a quien acompaña al niño, se le dice qué se va a hacer y que la limpieza de la piel puede dejar la zona enrojecida, incluso con una costra, que desaparece en pocos días.

### Montaje de electrodos

Con el paciente acostado de espalda:

1. **Limpia la piel** con alcohol y luego con gel abrasivo, frotando en una sola dirección, en cada punto donde va un electrodo. El objetivo es bajar la impedancia entre la piel y el electrodo.
2. **Pon los electrodos** con gel conductor y fíjalos con cinta:
    - **activo** en el **vértex** (Cz; blanco en muchos equipos);
    - **tierra** sobre una ceja o en la frente (negro);
    - **referencias** en cada **mastoides**: rojo en la derecha y azul en la izquierda.
3. **Revisa las impedancias**: todas **bajo 5 kΩ** y **parecidas entre sí**. El preamplificador resta lo que es común a los dos electrodos de cada canal, y esa resta funciona bien solo si los dos tienen una impedancia parecida (Picton, 2010). Una impedancia alta o desbalanceada deja entrar el zumbido de la red eléctrica.
4. **Pon los fonos de inserción**: rojo en el OD, azul en el OI, con la oliva del tamaño del conducto.
5. Apaga la luz, abriga al paciente y espera que se duerma.

:::imagen /docs/manual/img/estudiante/abr-avanzados-2.png ancho=50% Parámetros avanzados de LabSim: la pestaña Registro
- @80,14 | **Transductor**: fono de inserción, supraaural o vibrador óseo. Elegir el vibrador es lo que convierte el examen en un ABR por vía ósea.
- @88,19.7 | **Montaje**: Cz o Fz contra mastoides, o Cz contra lóbulo.
- @75,25.5 | **Ventana**: cuántos milisegundos se registran después del estímulo.
- @78,42.4 | **Filtro de red**: el notch de 50 Hz. Es el último recurso, no el primero: primero se arreglan las impedancias.
- @52,68 | **Electrodo activo** en el vértex (Cz).
- @86,68 | **Impedancia** de cada electrodo. Un número alto acá se paga en ruido.
- @52,76.5 | **Referencias**: A2 a la derecha y A1 a la izquierda (en el sistema 10-20, la zona de la oreja de cada lado).
- @52,85.1 | **Tierra** en la frente (Fpz).
:::

### Los parámetros de rutina

:::ayuda-ancho Configuración del ABR neurootológico y de búsqueda de umbral
| Parámetro | Valor de rutina | Por qué |
|---|---|---|
| Estímulo | Click (o CE-Chirp) | Banda ancha: sincroniza mucho nervio a la vez y da ondas claras |
| Polaridad | Alternada | Cancela el artefacto eléctrico del transductor y la microfónica coclear |
| Intensidad inicial | 80 dB nHL | En un oído normal se ven todas las ondas |
| Tasa | 21,1 estímulos/s | Rápida sin degradar las ondas; el decimal evita que el estímulo quede en fase con la red eléctrica |
| Filtros | 100 a 3.000 Hz | Deja pasar la energía del ABR; saca el EEG lento y parte del músculo |
| Ventana | 10 a 12 ms | Lo que tarda en llegar la onda V cerca del umbral (12 ms en LabSim) |
| Barridos | 2.000 por curva | Lo que hace falta para bajar el ruido residual (ver el paso 4) |
| Transductor | Fonos de inserción | Más aislación, menos artefacto |
:::

<!-- Protocolo ORL 2019: "Ventana de tiempo: 10 s". Es una errata: la ventana del ABR se mide en milisegundos (10 a 12 ms; Aguilar-Madrid y cols. 2016 registran 10 ms; Delgado Hernández y cols. 2003, 12 ms). Se corrigió a 10 a 12 ms. -->

La polaridad tiene un costo y hay que conocerlo. El click de **rarefacción** adelanta la onda I y la hace más clara que el de condensación; en la III y la V no hay diferencias constantes (Stockard y cols., 1979). En **condensación** las ondas I y III salen más chicas (Da Silva Nunes y Gentile Matas, 2005). Alternar cancela el artefacto, pero promedia dos respuestas de latencia apenas distinta y ensancha un poco las ondas. La norma que uses tiene que estar hecha con la misma polaridad.

## Paso a paso

### 1. Mira el EEG antes de promediar

Antes de apretar Iniciar, mira el EEG en vivo. Tiene que estar **tranquilo**: sin el serrucho del músculo, sin saltos por movimiento y sin la onda regular de la red eléctrica. Un promedio no limpia un EEG malo; solo tarda más en mostrar que es malo. Si está sucio, revisa las impedancias, acomoda la cabeza o espera que el paciente se duerma.

### 2. Empieza a 80 dB nHL y reconoce las ondas

Registra el primer oído a **80 dB nHL**. Ahí, en un oído normal, se ven las ondas I a V. Antes de marcar nada, **repite la curva**: una onda que no está en las dos curvas no es una onda. Lo mismo dicen los **subpromedios A y B** (el botón **AB** de LabSim): el equipo reparte los barridos en dos mitades, y una respuesta real aparece en las dos.

Para reconocer las ondas sirve el **canal contralateral** (el botón **C**), el que registra con la referencia del otro lado. Ahí la onda I falta o es mínima y la V sigue presente. Si dudas cuál es la I, la que desaparece en el contralateral lo es.

### 3. Busca el umbral de la onda V

Desde 80 dB nHL se **baja de 20 en 20** mientras la onda V siga presente. Cuando desaparece, se **sube de 10 en 10** hasta que vuelve. El **umbral** es la intensidad más baja con una onda V que se repite. Se repiten, como mínimo, la curva de intensidad máxima y la del umbral.

Ese esquema deja siempre un **escalón bajo el umbral sin onda V**. No es un registro perdido: es la prueba de que el nivel de arriba es el umbral y no un nivel más.

{{caso h10_p33}}

:::figura h10_p33 abr
- @OD 80 I | A 80 dB nHL la **onda I** llega a 1,4 ms, la **III** a 3,8 y la **V** a 5,7. Interpicos: I-III 2,4 ms, III-V 1,9 e I-V 4,3. Todo dentro de lo normal.
- @OD 40 V | A 40 dB la V llega a 6,9 ms y es más chica. La I y la III se achicaron mucho más que la V.
- @OD 20 V | A 20 dB queda solo una III mínima y la **V**, a 7,9 ms.
- @OD 10 V | A 10 dB la V es chica, a 8,3 ms, pero está en las dos réplicas (las líneas finas): es una respuesta.
- @OD 0 | A 0 dB no hay nada que se repita.
- El orden de registro fue **80, 60, 40, 20, 0** (sin V) y, subiendo 10, **10** (con V). **Umbral de la onda V: 10 dB nHL**.
- Mira cómo se corre la V: 0,4 ms de 80 a 60, pero 1,0 ms de 40 a 20. Esa es la **función latencia-intensidad**: plana arriba y empinada cerca del umbral.
:::

Si a 80 dB nHL no hay onda V, se sube a **90 o 100 dB nHL** antes de concluir que no hay respuesta. Más arriba los fonos no entregan sin distorsión (en LabSim, la vía aérea llega hasta 100 dB nHL).

### 4. Cuántos barridos: el FSP y el ruido residual

Decidir "hay onda" a ojo cerca del umbral es la fuente de error más común del examen. Los equipos ayudan con dos números:

- El **ruido residual**: cuánto ruido queda en el promedio, en nanovoltios. Mientras sea comparable con la onda que buscas, no puedes decidir nada.
- El **FSP** (*F single point*): la razón entre la varianza de la señal promediada y la del ruido de fondo (Elberling y Don, 1984). Si no hay respuesta, vale alrededor de 1. Un FSP de **3,1** o más equivale a una detección con un 99 % de confianza.

En LabSim los dos están en la pestaña *Promediación* de los parámetros avanzados, junto al **rechazo de artefactos** (±25 µV: el barrido que lo supera, por un movimiento o un músculo, no entra al promedio). Los dos sirven para decidir **cuándo parar**: se sigue promediando hasta que el FSP cruza el criterio o hasta que el ruido residual es tan bajo que, si hubiera una respuesta del tamaño esperable, ya se vería (Don y Elberling, 1996). Parar antes es la forma más rápida de inventar una pérdida.

:::ojo Barridos y umbral
En LabSim el umbral de cada caso está definido **con 2.000 barridos**. Si promedias menos, la respuesta cerca del umbral no alcanza a salir del ruido: **cada vez que partes los barridos a la mitad, el umbral que encuentras sube unos 6 dB**. Si promedias más, puedes encontrar respuesta algo por debajo del umbral del caso, y eso también es correcto: es lo que pasa en la clínica.
:::

### 5. Enmascara cuando el otro oído puede contestar

El sonido que entra por un oído también llega, más débil, a la cóclea del otro. Con fonos de inserción pierde unos 60 a 70 dB en el camino (LabSim usa 65); por vía ósea, casi nada. Si el oído que estudias oye mucho peor que el otro, la respuesta que ves puede ser del oído bueno: es la misma **curva sombra** de la audiometría (→ H4). La regla es la misma: si la intensidad del estímulo, menos lo que se pierde al cruzar, alcanza el umbral óseo del otro oído, se enmascara con ruido en el otro oído (el **Masking** del panel).

### 6. Si sospechas compromiso neural, sube la tasa

Al aumentar la tasa, las neuronas tienen menos tiempo para recuperarse entre estímulos: las latencias se alargan y las amplitudes bajan. En la serie de Jiang y cols. (1991), de 10 a 90 estímulos por segundo la onda I se alarga un 4 a 10 %, la III un 9 a 13 % y la V un 12 a 15 %. Un nervio o un tronco con la conducción comprometida se "fatiga" más que uno sano, y la tasa alta puede destapar un retraso que a 21,1 no se veía.

Por eso, cuando la historia o el primer registro sugieren una lesión neural, se repite el registro a **81,1 estímulos por segundo** y se compara con el de 21,1. Para comparar se miden las mismas ondas en las dos curvas: el alargamiento normal es el de la serie de Jiang; uno bastante mayor es el hallazgo.

<!-- Protocolo ORL 2019: "En el caso de sospecha de neuropatía, es necesario aumentar la tasa a 81,1". La tasa alta busca la fatiga de conducción de una lesión neural (retrococlear); en la neuropatía auditiva, con el ABR ausente, la maniobra que define el cuadro es registrar en rarefacción y en condensación por separado para ver la microfónica coclear (Berlin y cols., 1998; BSA, 2019). Se redactó como "compromiso neural" y la polaridad se agregó en el caso H10.5 y en el cap. 13. -->

### 7. Umbral por frecuencia: tone burst y NB chirp

El click estima la audición entre 2 y 4 kHz. Para un audiograma completo, sobre todo en un lactante que se va a equipar con audífonos, hacen falta **estímulos por frecuencia**:

- **Tone burst**: un tono breve de una frecuencia, con subida y bajada suaves (por ejemplo, 2 ciclos de subida, 1 de meseta y 2 de bajada). Excita una zona acotada de la cóclea, pero sincroniza peor que el click: a intensidad alta prácticamente **solo se identifica la onda V**, más ancha y más tardía (Pinto y Matas, 2007). Con un burst grave la V llega tarde: en Tomás, con burst de 500 Hz, la V de su umbral (20 dB nHL) llega a 10,2 ms. Con una ventana de 10 ms se habría salido de la pantalla.
- **Chirp**: un estímulo que manda primero los graves y después los agudos, para que todos lleguen a su lugar de la cóclea al mismo tiempo. Compensa el retraso de la onda viajera y sincroniza mejor: con el CE-Chirp LS de banda ancha la onda V sale más grande que con el click, sin cambiar su latencia a intensidad alta (Cargnelutti y cols., 2017). El **NB CE-Chirp LS** hace lo mismo dentro de una banda de frecuencia: mira la misma zona que el tone burst, con una V más clara.

#### De dB nHL a dB HL

El umbral del ABR queda por encima del umbral tonal del mismo oído. Para estimar el audiograma se le **resta una corrección** por estímulo y frecuencia, y el resultado se escribe en **dB eHL** (*estimated hearing level*). Las correcciones salen de comparar umbrales de ABR con audiometrías en los mismos sujetos (Stapells, 2000), y cada programa las publica en su propia tabla, con valores algo distintos según el equipo y la edad del niño (BSA, 2025; Ontario Infant Hearing Program, 2020; Hatton y cols., 2022).

:::ayuda Corrección nHL → eHL que usa LabSim
| Estímulo | Se resta |
|---|---|
| Burst 500 Hz | 20 dB |
| Burst 1 kHz | 15 dB |
| Burst 2 kHz | 10 dB |
| Burst 4 kHz | 5 dB |
| NB CE-Chirp LS 500 Hz / 1 kHz / 2 kHz / 4 kHz | 15 / 10 / 5 / 5 dB |
| Click | 10 dB |
| CE-Chirp y CE-Chirp LS | 5 dB |

En Tomás: 20 dB nHL con burst de 500 Hz − 20 = **0 dB eHL**, lo mismo que su audiograma en 500 Hz.
:::

{{caso h10_p36}}

:::figura h10_p36 abr
- Hernán tiene una pérdida sensorioneural de agudos: en el OD, 25 dB HL en 1 kHz, 40 en 2 kHz, 50 en 3 kHz y 60 en 4 kHz (su audiograma está en H3).
- @OD 80 V | Con click, a 80 dB nHL, la V llega a 6,3 ms: todavía dentro de lo normal para sus 74 años.
- @OD 80 III | **No hay onda I.** La I depende de la base de la cóclea, que es justo la zona dañada: es la primera onda que se pierde en una pérdida de agudos.
- @OD 60 V | A 60 dB la V sigue presente (6,9 ms). A 50 (no se muestra) ya no hay una V que se repita: **umbral con click, 60 dB nHL**.
- 60 dB nHL − 10 = **50 dB eHL**: un promedio de la zona de 2 a 4 kHz, donde el audiograma marca 40 a 60 dB HL.
:::

:::figura h10_p36 abr 2
- @OD 40 V | Con **burst de 1 kHz** la V aparece hasta 40 dB nHL (9,2 ms).
- @OD 20 | A 20 dB no hay nada: **umbral con burst de 1 kHz, 40 dB nHL**.
- 40 dB nHL − 15 = **25 dB eHL**: lo mismo que su audiograma en 1 kHz. El click solo habría dicho "50 dB" y escondido que los graves están casi normales.
:::

### 8. ABR por vía ósea

Cuando el ABR por vía aérea sale elevado, la vía ósea responde lo mismo que en la audiometría: **¿es transmisión o es la cóclea?** Es clave en el lactante con otitis media o con una malformación del oído (→ cap. 15 y 17).

- **Cómo**: el **vibrador** en la mastoides, el mismo montaje, y en LabSim el transductor *vibrador óseo* en Parámetros avanzados. El cráneo vibra entero, así que en el adulto el estímulo llega casi igual a las dos cócleas: hay que **enmascarar** el oído contrario. En el lactante el cráneo transmite peor de un lado al otro y el enmascaramiento pesa menos.
- **Hasta dónde**: el vibrador entrega poco. Los equipos llegan a unos **45 a 55 dB nHL** (Seo y cols., 2018); en LabSim, **55**. Y cada vía tiene su propia referencia: en el adulto normoyente el umbral del click por vía ósea queda unos **15 dB más arriba** que por vía aérea, mientras que en el lactante quedan casi iguales (Cobb y Stuart, 2016). Al adulto le sobra poco margen: con una pérdida sensorioneural de 35 dB HL, la respuesta ósea ya se sale del alcance del vibrador.
- **Qué se lee**: **solo la onda V**. La I y la III rara vez se identifican por vía ósea (Seo y cols., 2018): el estímulo trae poca energía aguda y el artefacto del vibrador, apoyado a centímetros del electrodo, tapa los primeros milisegundos. Buscar interpicos en un registro óseo es un error.
- **El lactante es distinto**: su onda V por vía ósea llega **antes** que por vía aérea, al revés que en el adulto (Yang y cols., 1987).

:::comentario Por qué 55 dB en LabSim
El tope del vibrador no es un error del simulador: es el límite físico del transductor. La revisión de Seo y cols. (2018) lo ubica entre 45 y 55 dB nHL según el equipo, y hay series normativas que solo miden hasta 50 dB nHL porque su vibrador no entrega más. LabSim toma el extremo alto, 55 dB nHL. Si tu equipo llega solo a 45 o 50, la ventana útil de la vía ósea es todavía más angosta: un ABR óseo "sin respuesta" a su tope no es lo mismo que una cóclea sin función.
:::

<!-- verificar: Cobb y Stuart 2016 (Ear Hear 37(6), partes I y II): autores, año y diseño confirmados en Bibliografia.php (A03); volumen y páginas sin confirmar en el original. -->

### 9. Mide y revisa la función latencia-intensidad

Con todas las curvas registradas, marca en cada una las ondas que se repiten: la latencia en el pico y la amplitud del pico al valle que lo sigue. Revisa la tabla de latencias e interpicos y el gráfico **latencia-intensidad** de las ondas I, III y V, que en LabSim está en su propia pestaña, sobre la banda normal para la edad del paciente.

:::ayuda Ayuda memoria
- Paciente dormido, piel bien limpia, impedancias **bajo 5 kΩ** y parecidas.
- Click alternado, 21,1/s, 100-3.000 Hz, ventana de 10-12 ms, fonos de inserción.
- **80 dB nHL**: ondas I a V, repetidas.
- Baja **20 en 20**; sin V, sube **10 en 10**. Umbral = la V más baja que se repite.
- Repite siempre el máximo y el umbral.
- Promedia hasta FSP ≥ 3,1 o ruido residual bajo; nunca menos por apuro.
- Sospecha neural: **tasa a 81,1/s**. Frecuencias: **burst o NB chirp** y corrección a dB eHL.
- Vía ósea: tope de **55 dB nHL** en LabSim, **solo la V**.
:::

### El AABR de tamizaje

El **ABR automatizado** (AABR) es otro equipo, aunque use el mismo principio. No busca umbrales ni deja leer ondas: estimula cada oído a un **nivel fijo**, típicamente **35 dB nHL**, y un algoritmo estadístico decide si hay respuesta. Contesta **PASA** o **REFIERE**.

Se hace en el recién nacido antes del alta, dormido en la cuna o en brazos, en unos 15 minutos:

1. Otoscopía y anamnesis del parto.
2. Limpieza de la piel y electrodos: vértex y ambas mastoides, más la tierra en la frente si el equipo la usa.
3. Impedancias parecidas y bajo el límite del equipo, que en tamizaje es más amplio que en el ABR diagnóstico.
4. La sonda u oliva en el primer oído.
5. Iniciar. El equipo revisa solo las impedancias, el sello de la sonda y el estímulo, y promedia hasta llegar al criterio o hasta agotar el tiempo (en algunos equipos, 120 segundos).
6. El otro oído.

Leer bien el resultado es la mitad del examen:

- **PASA** quiere decir que ese oído tuvo una respuesta a 35 dB nHL **ese día**. No descarta una pérdida leve, ni una que aparezca después.
- **REFIERE no es hipoacusia.** En las primeras horas de vida, el vérnix en el conducto y el líquido en el oído medio hacen referir a muchos oídos sanos (→ cap. 16). Refiere también el bebé que se movió. Lo que sigue es un nuevo tamizaje o un ABR diagnóstico.
- El AABR **detecta la neuropatía auditiva** y las emisiones otoacústicas no: en la neuropatía las emisiones pasan y el AABR refiere. Por eso a los recién nacidos con más de 5 días en UCI neonatal se les tamiza con AABR (JCIH, 2019).

:::imagen /docs/manual/img/estudiante/aabr.png ancho=75% El AABR de LabSim después de tamizar el OD
- @25,21.8 | **Estímulo**: CE-Chirp, el de fábrica.
- @29,26.5 | **Nivel**: 35 dB nHL.
- @25,31.1 | **Tasa**: los equipos de tamizaje estimulan rápido para terminar antes.
- @29,40.2 | **Criterio FSP** (3,1) y, arriba, los barridos máximos (6.000): lo que el equipo exige antes de decir PASA.
- @29.5,63 | **Restaurar valores de fábrica** devuelve el protocolo de tamizaje.
- @97.5,9.7 | Los **cuatro pasos** que el equipo hace solo: sonda, impedancias, registro y resultado.
- @89.5,32.3 | **Impedancias**: en el tamizaje el límite es amplio (≤ 20 kΩ en LabSim).
- @80,36.8 | **Barridos**: 1.882 de 6.000. Se detuvo antes porque cruzó el criterio.
- @41,45 | **FSP 3,13**: sobre 3,1.
- @80,53 | **PASA**.
- @59,68.7 | En el **informe**, el resultado de cada oído viene precargado, pero se puede cambiar.
- @88,80 | **Observaciones** del registro y **conducta**: rescreening, ABR diagnóstico o alta.
:::

:::ojo Subir el nivel para conseguir un PASA
El nivel del tamizaje es fijo por una razón: 35 dB nHL separa un oído que oye de uno que necesita estudio. Un oído con umbral de 45 dB refiere a 35 y pasa a 60. Subir el nivel "para que pase" no cambia el oído, solo esconde la pérdida. Lo mismo vale para cortar el registro antes de que el equipo termine: con pocos barridos, hasta un oído sano refiere.
:::

## Cómo se informa

### Qué se mide

- **Latencias absolutas** de las ondas I, III y V a 80 dB nHL, por oído.
- **Interpicos** I-III, III-V e I-V.
- **Diferencia interaural de la onda V** al mismo nivel. En normoyentes es de apenas 0,08 ms en promedio (Sanfins y cols., 2026); según el centro, se considera anormal sobre 0,2 a 0,4 ms. LabSim usa 0,4 ms.
- **Razón de amplitudes V/I**. En un oído normal la V es más grande que la I. Una V proporcionalmente chica (en LabSim, V/I menor que 1) es un hallazgo retrococlear.
- **Morfología y replicabilidad**: si las ondas son claras y se repiten.
- **Umbral de la onda V** por estímulo, en dB nHL, y su estimación en dB eHL.

### Contra qué se compara

Cada laboratorio debe tener su propia norma, medida con su equipo, su transductor y su protocolo, estratificada por sexo y edad (Sanfins y cols., 2026; ACNS, 2008). En las mujeres las ondas III y V llegan 0,08 a 0,19 ms antes que en los hombres, y los interpicos son 0,07 a 0,15 ms más cortos (Jerger y Hall, 1980; Sanfins y cols., 2026). Con la edad adulta la V se alarga unos 0,2 ms entre los 25 y los 55 años y su amplitud cae cerca de un 10 % (Jerger y Hall, 1980). El recién nacido tiene la onda I casi de adulto y un I-V largo (Rosa y cols., 2014), que se acorta hasta llegar a valores de adulto entre los 9 meses y los 3 años (Gorga y cols., 1989; Sharma y cols., 2016). La temperatura también cuenta: la hipotermia alarga el I-V (→ cap. 14).

:::ayuda-ancho Valores de referencia que usa LabSim en el adulto (click a 80 dB nHL, en ms)
| | Hombre: media | Hombre: límite | Mujer: media | Mujer: límite |
|---|---|---|---|---|
| Onda I | 1,47 | 1,87 | 1,46 | 1,86 |
| Onda III | 3,75 | 4,19 | 3,65 | 4,09 |
| Onda V | 5,68 | 6,18 | 5,54 | 6,04 |
| I-III | 2,28 | 2,72 | 2,19 | 2,63 |
| III-V | 1,93 | 2,37 | 1,89 | 2,33 |
| I-V | 4,21 | 4,71 | 4,08 | 4,58 |

Medias de la serie de Sanfins y cols. (2026), con fonos de inserción. El límite es la media más 2 desviaciones estándar. LabSim tiene tablas propias para el recién nacido, el niño de 1 a 3 años, el niño mayor y el adulto mayor, y elige la del paciente por su edad y su sexo.
:::

### Cuatro patrones

:::ayuda-ancho Cómo se lee un ABR alterado
| | Latencias absolutas | Interpicos | Latencia-intensidad | Umbral |
|---|---|---|---|---|
| **Conductivo** | Todas largas, incluida la I | Normales | Corrida en paralelo, tanto como el gap | Elevado |
| **Coclear** | Casi normales a intensidad alta; la I puede faltar | Normales | Empinada: converge con la normal a intensidad alta | Elevado |
| **Retrococlear** | La I normal; III y V largas | **Largos** (I-III, I-V) | Corrida desde la I; empeora con tasa alta | Normal o elevado |
| **Neuropatía auditiva** | Sin ondas, o desorganizadas | No medibles | No medible | No estima la audición |

Una pérdida periférica (conductiva o coclear) alarga las latencias absolutas y deja normales los interpicos. Ese es el dato que separa lo periférico de lo retrococlear.
:::

{{caso h10_p34}}

:::figura h10_p34 abr
- @OI 80 V | El **OI** es normal: I a 1,5 ms, III a 3,6 y V a 5,6. I-V de 4,1 ms.
- @OD 80 I | En el **OD** la onda I llega a 2,9 ms: 1,4 ms tarde. La señal ya sale atrasada de la cóclea.
- @OD 80 V | La V llega a 6,8 ms. Pero los interpicos son normales (I-III 2,3, III-V 1,7, I-V 3,9 ms): la vía conduce bien; lo que se atrasó fue la llegada del sonido.
- @OD 60 V | A 60 dB ya solo queda la V, a 7,7 ms.
- Compara con Tomás a 40 dB nHL (caso H10.1): I a 3,0, III a 5,2 y V a 6,9 ms. El OD de Carolina a 80 se parece a un oído normal a 40: la otoesclerosis le **resta intensidad** al click antes de que llegue a la cóclea, y la cóclea responde como a un sonido más suave.
- La diferencia interaural de la V es de **1,2 ms**. Una conductiva la fabrica sola: antes de leerla como retrococlear, mira el audiograma y la timpanometría.
:::

{{caso h10_p39}}

:::figura h10_p39 abr
- @OI 80 V | El **OI** es normal: I a 1,5 ms, III a 3,8 y V a 5,6. I-V de 4,1 ms.
- @OD 80 I | En el **OD** la onda I llega a 1,4 ms, en su lugar: la cóclea entrega la señal a tiempo.
- @OD 80 III | La III llega a 4,2 ms: **I-III de 2,8 ms**, sobre el límite de 2,7.
- @OD 80 V | La V llega a 6,7 ms: III-V de 2,5 (límite 2,4) e **I-V de 5,2 ms** (límite 4,7). La diferencia interaural de la V es de **1,0 ms**.
- @OD 60 V | A 60 dB solo queda una V chica; la I y la III desaparecen.
- Raúl tiene 30 a 55 dB de pérdida entre 2 y 4 kHz en el OD. Una pérdida coclear así puede atrasar algo la V, pero **no alarga los interpicos**: el retraso está entre la I y la V, en el nervio. Es un **patrón retrococlear** (→ cap. 11).
:::

{{caso h10_p40}}

:::figura h10_p40 abr
- @OD 80 | A 80 dB nHL el OD no tiene ondas.
- @OI 80 | El OI tampoco. Valentina tiene un audiograma de 30 a 45 dB HL: con esa pérdida, un oído coclear daría una V clara a 80 dB.
- La falta de ondas no se explica por el umbral: la vía no descarga en sincronía.
:::

:::figura h10_p40 teoae
- @OD 2000 | Las **emisiones transitorias** del OD están presentes en 4 de 5 bandas, y las del OI en todas: las células ciliadas externas funcionan.
- **Emisiones presentes y ABR ausente**: es el patrón de la **neuropatía auditiva** (Starr y cols., 1996). El siguiente paso es registrar en **rarefacción** y en **condensación** por separado: la microfónica coclear se invierte con la polaridad y la respuesta neural no (Berlin y cols., 1998). Con polaridad alternada, la microfónica se cancela y no se ve (→ cap. 13).
:::

### Un ejemplo de informe

El informe describe primero lo que se vio a 80 dB nHL en cada oído y después el umbral; recién al final, la conclusión.

> **Potenciales evocados auditivos de tronco cerebral.** Click, polaridad alternada, 21,1 estímulos/s, filtros 100-3.000 Hz, fonos de inserción. Paciente en sueño fisiológico.
>
> **OD**: a 80 dB nHL se observan ondas I, III y V de buena morfología y replicabilidad. Latencias absolutas e interpicos I-III, III-V e I-V dentro de lo esperado. Umbral de onda V en 10 dB nHL.
>
> **OI**: a 80 dB nHL se observan ondas I, III y V de buena morfología y replicabilidad. Latencias absolutas e interpicos dentro de lo esperado. Umbral de onda V en 10 dB nHL.
>
> **Conclusión**: el examen sugiere audición normal en ambos oídos para el rango de frecuencias estudiado (2 a 4 kHz).

La conclusión dice qué tipo de audición **sugiere** el examen: normal, hipoacusia conductiva, sensorioneural o mixta, en qué oído y de qué grado aproximado en dB HL. Si hay un patrón retrococlear, se describe ("interpicos I-III e I-V prolongados en el OD, con diferencia interaural de la onda V de 1,0 ms") sin ponerle nombre de enfermedad. Se anota si se adjunta otro examen, como la impedanciometría.

<!-- Protocolo ORL 2019, ejemplo de informe: entre las conclusiones ofrece "Hipofunción sensorioneural". El término para el tipo de pérdida es "hipoacusia sensorioneural" (ASHA y BIAP); se dejó así. -->

## Errores frecuentes

- **Promediar poco.** Con pocos barridos la V cercana al umbral no sale del ruido y el umbral queda más alto de lo real. Es el error que más pérdidas inventa.
- **Marcar una onda que no se repite.** Si no está en las dos curvas, o en los subpromedios A y B, no es una onda.
- **Leer la latencia sin el audiograma.** Una conductiva o una pérdida de agudos alargan las latencias absolutas y la diferencia interaural. El retrococlear se decide con los **interpicos**.
- **Electrodos mal puestos.** Una impedancia alta o desbalanceada deja entrar la red eléctrica; un electrodo suelto deja la curva plana o llena de ruido.
- **Equipo sin configurar.** Filtros abiertos, tasa al azar o una ventana corta para el tone burst grave cambian las ondas o las dejan fuera.
- **Normas de otro protocolo.** Comparar contra valores medidos con otro transductor, otra polaridad u otra tasa.
- **Llamar "sordo" a un ABR plano.** Sin ABR y con emisiones presentes, puede ser una neuropatía.

### Lo que parece onda y no es

El promedio cancela lo que es aleatorio. Lo que **no** es aleatorio, lo que se repite con cada estímulo o se cuela en una parte de los barridos, sobrevive al promedio y puede parecer una onda.

:::ayuda-ancho Artefactos del ABR
| Artefacto | Cómo se ve | Cómo se reconoce o se resuelve |
|---|---|---|
| **Artefacto de estímulo** | Una deflexión grande en el primer milisegundo, que crece con la intensidad. Peor con fono supraaural y con vibrador | Polaridad alternada lo cancela (por vía ósea, no del todo). Con fono de inserción, **pinzar el tubo**: el sonido deja de llegar y el artefacto sigue (BSA, 2019) |
| **Microfónica coclear** | Ondas desde el inicio que se **invierten** al cambiar de polaridad | Registrar en rarefacción y condensación por separado. Clave en la neuropatía (→ cap. 13) |
| **Respuesta postauricular** | Una onda grande hacia los 12 a 15 ms, a intensidad alta, en un paciente tenso (O'Beirne y Patuzzi, 1999) | Se **repite** en los subpromedios: replicar no la descarta. Se va relajando al paciente |
| **Red eléctrica** | Una onda regular cada 20 ms (50 Hz) en el EEG y en el promedio | Revisar impedancias y la tierra; el notch es el último recurso |
| **Movimiento y músculo** | EEG lleno de ruido; el rechazo descarta muchos barridos y el promedio no avanza | Esperar que duerma, acomodar la cabeza. Sin rechazo, esos barridos entran y arruinan el promedio |
| **Falsa onda V** | Una onda con forma y latencia de V en el promedio | **No se repite**: está en uno de los subpromedios y no en el otro. Repetir la curva la hace desaparecer |
:::

La **falsa onda V** merece una mención aparte porque engaña justo donde más importa, cerca del umbral. Es un artefacto que se metió en una parte de los barridos y que, por casualidad, cae donde se espera la V. El promedio la muestra; el FSP no la confirma, y el ruido residual sube. Lo que la delata son los **subpromedios A y B**: una respuesta real está en las dos mitades; la falsa V, solo en una. La respuesta postauricular es el contraejemplo: es real, se repite en las dos mitades, y aun así no es auditiva de tronco. Por eso la replicación es necesaria pero no suficiente: también hay que mirar **dónde** está la onda y **cómo** se comporta con la intensidad (→ cap. 18).

:::ojo Ojo clínico
Antes de informar un ABR, pregúntate si **calza con lo demás**: con el audiograma, con la timpanometría, con las emisiones y con cómo conversó el paciente. Un umbral de ABR peor que la audiometría hace sospechar un registro malo antes que una pérdida; uno mucho mejor hace sospechar una pérdida no orgánica (→ cap. 19). Y un ABR plano con emisiones presentes no es una sordera: es una neuropatía hasta que se demuestre lo contrario.
:::

## En LabSim

El ABR de LabSim se maneja como un equipo real, y por eso se puede equivocar como uno real.

- **El equipo no viene configurado.** La tasa y las promediaciones arrancan al azar y los filtros abiertos. Configurarlo es parte del examen, y nada en la pantalla te avisa qué está mal: lo ves en el trazo.
- **El paciente responde según su caso**: su audiograma, su tipo de pérdida y, si lo tiene, su patrón retrococlear. La población normativa (recién nacido, niño, adulto, adulto mayor; hombre o mujer) la elige el equipo por la edad y el sexo del paciente.
- **El umbral del caso está referido a 2.000 barridos.** Con menos, encuentras un umbral más alto; con más, puedes bajar un poco.
- **Los artefactos están**: el de estímulo (y la maniobra de pinzar el tubo), la red eléctrica sin tierra, el paciente inquieto, la respuesta postauricular y la falsa onda V, según lo que el docente haya puesto en el caso.
- **El AABR** es un equipo aparte, en el mismo grupo, y la **electrococleografía** está dentro del ABR, en el combo *Prueba* (→ H11).

El informe se guarda solo, con las curvas y sus marcas. Si el paciente tiene un ABR de una atención anterior, aparece en *Sesión* para mirarlo, pero no se puede editar.

:::comentario Lo que el simulador no tiene
En LabSim el paciente ya está acostado, con los electrodos puestos y casi siempre dormido cuando abres el equipo. En la clínica, conseguir ese sueño es la mitad del examen. Además, los filtros de LabSim no corren las ondas: los filtros de un equipo real, sobre todo con el pasa alto subido, pueden cambiar un poco las latencias y agregar oscilaciones (Picton, 2010). Por eso tu norma tiene que estar medida con los mismos filtros.
:::

Para practicar, los pacientes de este capítulo están entre los de práctica (★): Tomás, Hernán, Carolina, Raúl y Valentina.

:::pregunta Preguntas para practicar
1. En el caso de Tomás, ¿qué intensidades registrarías si a 20 dB nHL **no** hubiera onda V? ¿Cuál sería su umbral si a 30 sí la hay?
2. Promedias 500 barridos en un oído con umbral real de 30 dB nHL y encuentras la V hasta 45. ¿El oído empeoró? ¿Qué harías para saberlo?
3. Carolina tiene una diferencia interaural de la onda V de 1,2 ms y Raúl de 1,0 ms. ¿Por qué una es conductiva y la otra retrococlear? ¿Qué número de la figura lo decide?
4. Con los umbrales de Hernán (click 60 y burst de 1 kHz 40 dB nHL), estima su audición en dB eHL. ¿Qué le habría dicho a un médico un ABR solo con click?
5. Un lactante tiene un ABR por vía aérea con umbral de 50 dB nHL y por vía ósea no responde a 55. ¿Puedes concluir que la pérdida es sensorioneural? ¿Qué cambia si es un adulto?
6. En un AABR, un oído refiere dos veces. La enfermera propone subir el nivel a 60 dB "para que pase". ¿Qué le contestas?
:::

## Referencias

### Técnica

1. Picton TW. Human auditory evoked potentials. San Diego: Plural Publishing; 2010 (el editor la fecha en 2011).
1. Hall JW 3rd. New handbook of auditory evoked responses. Boston: Pearson; 2007.
1. American Clinical Neurophysiology Society. Guideline 9C: Guidelines on short-latency auditory evoked potentials. ACNS; 2008. Disponible en: https://www.acns.org/pdf/guidelines/Guideline-9C.pdf
1. Elberling C, Don M. Quality estimation of averaged auditory brainstem responses. Scand Audiol. 1984;13(3):187-97. doi:10.3109/01050398409043059
1. Don M, Elberling C. Evaluating residual background noise in human auditory brain-stem responses. J Acoust Soc Am. 1994;96(5 Pt 1):2746-57.
1. Don M, Elberling C. Use of quantitative measures of auditory brain-stem response peak amplitude and residual background noise in the decision to stop averaging. J Acoust Soc Am. 1996;99(1):491-9.
1. Stockard JE, Stockard JJ, Westmoreland BF, Corfits JL. Brainstem auditory-evoked responses: normal variation as a function of stimulus and subject characteristics. Arch Neurol. 1979;36(13):823-31.
1. Da Silva Nunes C, Gentile Matas C. Audiometría de tronco encefálico utilizando diferentes polaridades de presentación del estímulo acústico. Rev Chil Fonoaudiol. 2005;6(2):7-16.
1. Jiang ZD, et al. The effect of click rate on latency and interpeak interval of the brain-stem auditory evoked potentials in children from birth to 6 years. Electroencephalogr Clin Neurophysiol. 1991.
1. Cargnelutti M, Coser PL, Biaggio EP. LS CE-Chirp vs. click in the neuroaudiological diagnosis by ABR. Braz J Otorhinolaryngol. 2017;83(3):313-7. doi:10.1016/j.bjorl.2016.04.018
1. Pinto FR, Matas CG. A comparison between hearing and tone burst electrophysiological thresholds. Braz J Otorhinolaryngol. 2007. doi:10.1016/S1808-8694(15)30103-8 <!-- verificar: año, volumen y páginas (el año se dedujo del DOI). -->
1. Stapells DR, Oates P. Estimation of the pure-tone audiogram by the auditory brainstem response: a review. Audiol Neurootol. 1997;2(5):257-80.
1. Stapells DR. Threshold estimation by the tone-evoked auditory brainstem response: a literature meta-analysis. J Speech Lang Pathol Audiol. 2000;24(2):74-83.
1. Seo YJ, et al. Update on bone-conduction auditory brainstem responses: a review. J Audiol Otol. 2018;22(2):53-8. PMID 29471611.
1. Cobb KM, Stuart A. Neonate auditory brainstem responses to CE-Chirp and CE-Chirp octave band stimuli I y II. Ear Hear. 2016;37(6). <!-- verificar: páginas. -->
1. Yang EY, Rupert AL, Moushegian G. A developmental study of bone conduction auditory brain stem response in infants. Ear Hear. 1987;8:244-51.
1. British Society of Audiology. Recommended procedure: cochlear microphonic testing (OD104-87). BSA; 2019. Disponible en: https://www.thebsa.org.uk/wp-content/uploads/2023/10/OD104-87-Recommended-Procedure-for-Cochlear-Microphonic-Testing.pdf
1. O'Beirne GA, Patuzzi RB. Basic properties of the sound-evoked post-auricular muscle response (PAMR). Hear Res. 1999;138(1-2):115-32.

### Valores normales

1. Sanfins MD, Santillo MEA, Martins MFP, Silva DLdS, Gos E, Skarzynski PH, Hall JW III. The influence of sex, ear, and age on auditory brainstem responses recorded with the NeuroAudio system. Diagnostics. 2026;16(7):971. doi:10.3390/diagnostics16070971
1. Jerger J, Hall J. Effects of age and sex on auditory brainstem response. Arch Otolaryngol. 1980;106(7):387-91.
1. Hood LJ. Clinical applications of the auditory brainstem response. San Diego: Singular Publishing Group; 1998. Tabla 2-3. <!-- verificar: año y ciudad de la edición; la planilla de LabSim no los trae. -->
1. Delgado Hernández J, Zenker Castro F, Barajas del Prat JJ. Normalización de los potenciales evocados auditivos del tronco cerebral I: resultados en una muestra de adultos normoyentes. Auditio. 2003;2(1). doi:10.51445/sja.auditio.vol2.2003.0020
1. Aguilar-Madrid G, Torres-Valenzuela A, Hinojos-Escobar W, Cabello-López A, Gopar-Nieto R, Ravelo-Cortés PE, et al. Latencias de los potenciales evocados auditivos del tallo cerebral, por edad y sexo, en población adulta mexicana. Rev Med Inst Mex Seguro Soc. 2016;54(2):203-10.
1. Gorga MP, Kaminski JR, Beauchaine KL, Jesteadt W, Neely ST. Auditory brainstem responses from children three months to three years of age: normal patterns of response II. J Speech Hear Res. 1989;32(2):281-8.
1. Rosa LAC, et al. Auditory brainstem response: reference-values for age. CoDAS. 2014. doi:10.1590/2317-1782/2014469in
1. Sharma M, Bist SS, Kumar S. Age-related maturation of wave V latency of auditory brainstem response in children. J Audiol Otol. 2016;20(2):97-104.

### Umbral por frecuencia y tamizaje

1. British Society of Audiology. Recommended procedure: auditory brainstem response (ABR) testing in newborns (OD100). BSA; 2025, enmienda 2026. Disponible en: https://www.thebsa.org.uk/wp-content/uploads/2026/06/OD100-Auditory-Brainstem-Response-ABR-Testing-in-Newborns-March-2026.pdf
1. Ontario Infant Hearing Program. Protocol for auditory brainstem response-based audiological assessment (ABRA). Version 2018.02. Toronto; 2020. Disponible en: https://www.uwo.ca/nca/pdfs/clinical_protocols/2018.02%20ABRA%20Protocol_Oct%202020.pdf
1. Hatton JL, Van Maanen A, Stapells DR. British Columbia Early Hearing Program: auditory brainstem response protocol. Vancouver: BC Early Hearing Program; 2022. Disponible en: https://ehdi-pals.org/HostedMaterials/British%20Columbia%20ABR%20Protocol.pdf
1. Joint Committee on Infant Hearing. Year 2019 position statement: principles and guidelines for early hearing detection and intervention programs. J Early Hear Detect Interv. 2019;4(2):1-44. doi:10.15142/fptk-b748

### Fisiología

1. Jewett DL, Williston JS. Auditory-evoked far fields averaged from the scalp of humans. Brain. 1971;94(4):681-96. doi:10.1093/brain/94.4.681
1. Møller AR, Jannetta P, Bennett M, Møller MB. Intracranially recorded responses from the human auditory nerve: new insights into the origin of brain stem evoked potentials (BSEPs). Electroencephalogr Clin Neurophysiol. 1981;52(1):18-27.
1. Møller AR, Jannetta PJ. Interpretation of brainstem auditory evoked potentials: results from intracranial recordings in humans. Scand Audiol. 1983;12(2):125-33.
1. Melcher JR, Kiang NY. Generators of the brainstem auditory evoked potential in cat. III: Identified cell populations. Hear Res. 1996;93(1-2):52-71.
1. Starr A, Picton TW, Sininger Y, Hood LJ, Berlin CI. Auditory neuropathy. Brain. 1996;119(Pt 3):741-53.
1. Berlin CI, Bordelon J, St John P, Wilensky D, Hurley A, Kluka E, et al. Reversing click polarity may uncover auditory neuropathy in infants. Ear Hear. 1998;19(1):37-47.
