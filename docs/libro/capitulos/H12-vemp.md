# H12. VEMP

:::objetivos En esta herramienta
- Explicar por qué un sonido muy fuerte activa el sáculo y el utrículo, y por qué el VEMP es una respuesta muscular y no un potencial del nervio.
- Distinguir el cVEMP (sáculo, nervio vestibular inferior, esternocleidomastoideo) del oVEMP (utrículo, nervio vestibular superior, oblicuo inferior) y montar los electrodos de cada uno.
- Controlar la contracción del paciente, medir el EMG y corregir la amplitud, que es lo que hace comparable un oído con el otro.
- Configurar el estímulo (tone burst de 500 Hz, vía aérea u ósea), registrar con réplica y buscar el umbral.
- Medir P13-N23 y n10-p16, calcular la razón de asimetría y leerla junto con el audiograma.
- Reconocer los errores que fabrican un VEMP ausente, una asimetría falsa o una respuesta que no es vestibular.
:::

Los **potenciales evocados miogénicos vestibulares** (VEMP, del inglés *vestibular evoked myogenic potentials*) son la respuesta de un músculo a un sonido intenso. El sonido no se usa para que el paciente lo oiga: se usa porque, a niveles muy altos, también llega al vestíbulo y activa los órganos otolíticos, el sáculo y el utrículo. Si el órgano y su nervio funcionan, mandan una orden refleja a un músculo, y esa orden se ve como una onda pequeña en un electrodo de superficie. El VEMP es, entonces, de los pocos exámenes que dejan mirar los otolitos con un equipo de potenciales evocados, y lo hacen sin pedirle al paciente nada más que contraer un músculo.

El examen tiene dos versiones. El **VEMP cervical** (cVEMP) se registra en el músculo esternocleidomastoideo del cuello. El **VEMP ocular** (oVEMP) se registra bajo los ojos. Cada uno pasa por un órgano, un nervio y un músculo distintos, y por eso responden preguntas distintas. Hay buenas revisiones del tema en Welgampola y Colebatch (2005) y en Rosengren y cols. (2010).

## Para qué sirve

El VEMP responde tres preguntas:

1. **¿Funciona el sáculo y su nervio?** El cVEMP lo dice. Si la respuesta de un lado es mucho menor que la del otro, o falta, el sáculo, el nervio vestibular inferior o la vía hasta el músculo de ese lado están comprometidos. Es lo que se busca en el hidrops (→ cap. 9), en la laberintitis y en la sordera por paperas (→ cap. 7).
2. **¿Funciona el utrículo y su nervio?** El oVEMP lo dice, para el lado opuesto al oído que se estimuló. Junto con el cVEMP, permite saber si el daño toca una de las ramas del nervio vestibular o las dos (→ cap. 21).
3. **¿Hay una tercera ventana?** En la dehiscencia del conducto semicircular superior el vestíbulo se vuelve hipersensible al sonido: el VEMP sale con **umbral bajo** y amplitud grande, al revés que en las demás enfermedades (→ cap. 26).

Conviene tener claros sus límites desde el principio:

- El VEMP **no es una prueba de audición**. No necesita que el oído oiga: un oído sordo con el oído medio sano puede dar un VEMP normal, y un oído que oye bien puede dar uno ausente.
- **No mide los conductos semicirculares.** Para eso están la calórica y el vHIT (→ H16 y H17).
- Un VEMP alterado **no dice la causa**: describe qué parte de la vía falla, no por qué.
- Un VEMP **normal no descarta** una enfermedad. En un hidrops, por ejemplo, el cVEMP puede salir normal (→ cap. 9).
- Un VEMP **ausente** tampoco asegura que haya enfermedad: en adultos mayores, y sobre todo en el oVEMP, es frecuente que falte (ver "Cómo se informa").

## Fundamento

### Por qué un sonido llega a los otolitos

El oído interno es un solo laberinto con dos sistemas: la cóclea, que oye, y el vestíbulo, que registra el movimiento y la gravedad. Cuando entra sonido por el oído, la platina del estribo mueve el líquido del oído interno, y ese movimiento es mucho más eficiente para la cóclea que para el vestíbulo. Por eso, en la vida diaria, el sonido casi no activa los sensores del equilibrio: el vestíbulo está bien protegido de los ruidos del ambiente (Rosengren y cols., 2019).

Solo un sonido **muy intenso** logra activar las células ciliadas de los otolitos. Y entre los órganos del vestíbulo, el **sáculo es el más sensible al sonido**: su umbral es unos 15 a 20 dB más bajo que el del utrículo, y mucho más bajo que el de los conductos semicirculares. El sáculo responde mejor a sonidos de **500 a 1.000 Hz** (Rosengren y cols., 2019). Por eso el estímulo del VEMP es un tono breve de 500 Hz a un nivel cercano al límite de lo que un oído tolera sin daño. Es una ventana angosta: abajo no hay respuesta y arriba hay riesgo para la cóclea (ver "Cuánto sonido").

Con vibración del cráneo, en cambio, el sáculo y el utrículo se activan casi por igual (Rosengren y cols., 2019). Esa diferencia importa más adelante, cuando se elige entre sonido y vibrador.

### Dos reflejos, dos músculos

Cada órgano otolítico tiene su nervio: el **sáculo** manda sus fibras por el **nervio vestibular inferior** y el **utrículo**, por el **nervio vestibular superior**. Se atribuye el cVEMP al sáculo y el oVEMP al utrículo (Curthoys, 2010). Desde los núcleos vestibulares del tronco, la señal sigue por dos vías reflejas:

- **cVEMP, reflejo vestíbulo-cólico.** Sáculo, nervio vestibular inferior, núcleos vestibulares y, por la vía vestibuloespinal, las motoneuronas del nervio accesorio que mueven el **esternocleidomastoideo (ECM) del mismo lado** (Colebatch y cols., 1994). Es una vía corta e **ipsilateral**: el oído derecho se registra en el cuello derecho.
- **oVEMP, reflejo vestíbulo-ocular.** Utrículo y parte anterior del sáculo, nervio vestibular superior, núcleos vestibulares, un cruce hacia el lado opuesto y los núcleos de los músculos del ojo. La respuesta más clara se registra en el **músculo oblicuo inferior del ojo contrario** al oído estimulado (Iwasaki y cols., 2007; Curthoys y cols., 2012). Es una vía **cruzada**: el oído derecho se registra bajo el ojo izquierdo.

Para ver las dos vías juntas se usa **labyrinthus3d**, un simulador gratuito y libre del autor de este libro. En su pestaña "Vía", con la opción "utrículo y sáculo", dibuja el esquema de frente: a la izquierda de la figura queda el lado derecho del paciente. Aquí se sigue el **oído derecho** (figura siguiente).

:::imagen ilustraciones/h12-vias.png Captura de labyrinthus3d, software libre del autor: las vías del VEMP del oído derecho. Del sáculo y el utrículo salen las dos ramas del nervio vestibular hacia los núcleos vestibulares; de ahí, una vía baja al ECM del mismo lado (cVEMP) y otra sube por el fascículo longitudinal medial y cruza hacia el oblicuo inferior del ojo contrario (oVEMP).
- @14,88 | **Sáculo**: se atribuye a él el cVEMP (Curthoys, 2010).
- @46,92 | **Utrículo**: se atribuye a él el oVEMP (Curthoys, 2010).
- @15,79 | **Nervio vestibular inferior**: lleva las fibras del sáculo.
- @46,79 | **Nervio vestibular superior**: lleva las fibras del utrículo.
- @38,73 | **Núcleos vestibulares**: relevo de las dos ramas, en el tronco.
- @12,72 | **ECM del mismo lado**: aquí se registra el cVEMP; la vía es corta y no cruza (Colebatch y cols., 1994).
- @50,29 | **Fascículo longitudinal medial (FLM)**: por aquí sube la vía del oVEMP después de cruzar la línea media.
- @65,27 | **Oblicuo inferior del ojo contrario** (izquierdo, si se estimula el oído derecho): aquí se registra el oVEMP (Iwasaki y cols., 2007).
:::

Con esta misma figura se entiende por qué la neuritis de una rama deja normal el VEMP de la otra. En la figura siguiente, el simulador marca con una cruz el nervio vestibular **superior** derecho perdido: el utrículo queda sin camino hacia los núcleos y el oVEMP de ese oído se apaga, mientras que el sáculo y el nervio inferior siguen intactos y el cVEMP se conserva (→ tabla de interpretación, más abajo).

:::imagen ilustraciones/h12-vias-neuritis.png Captura de labyrinthus3d, software libre del autor: neuritis del nervio vestibular superior derecho. La cruz verde marca la rama perdida; la rama inferior, con el sáculo, no está tocada.
- @32,78 | **Rama superior interrumpida**: ninguna señal del utrículo llega a los núcleos; es la vía del oVEMP.
- @14,88 | **Sáculo y rama inferior intactos**: el cVEMP de este oído se conserva.
:::

<!-- verificar: "vía vestibuloespinal" y "motoneuronas del nervio accesorio" son descripción de libro de texto; las fuentes leídas (Rosengren 2019, Colebatch 1994) dan el trayecto sáculo-ECM sin nombrar cada relevo. Confirmar con Curthoys 2010 o con un tratado antes de la edición final. -->

### Un potencial que es una pausa

El ABR es una respuesta eléctrica de las neuronas (→ H10). El VEMP es otra cosa: es lo que **un músculo hace** después del estímulo, y lo que se ve en el electrodo es la actividad de ese músculo.

- El **cVEMP es una inhibición.** El estímulo hace que las unidades motoras del ECM **se detengan unos milisegundos** (Rosengren y cols., 2019). Eso se ve como una onda positiva a los 13 ms (**P13**) y una negativa a los 23 ms (**N23**) cuando el registro se dibuja con la polaridad habitual de este libro. La polaridad con que se dibuja depende del equipo (la convención neurofisiológica deja las negatividades hacia arriba): guíate por la latencia, que es siempre la misma, y no por el sentido de la onda.
- El **oVEMP es una excitación.** El estímulo hace que el oblicuo inferior se contraiga un instante. Se ve como una onda negativa a los 10 ms (**n10**) y una positiva a los 15 a 16 ms (**p16**). En la literatura se las llama también n10 y p15; LabSim usa p16.

Por eso las ondas del cVEMP se escriben con mayúscula inicial en las figuras del libro (P13, N23) y las del oVEMP con minúscula (n10, p16), como el equipo.

### Por qué la amplitud depende del músculo

Aquí está la diferencia que más cuesta entender cuando se viene del ABR. En el ABR, la respuesta no depende de lo que haga el paciente: dormido, sedado o despierto, da lo mismo. En el VEMP, la respuesta es **una modulación de una contracción que ya existe**.

Piensa en el cVEMP. Si el ECM está relajado, no hay actividad que interrumpir, y no hay respuesta que ver. Si está contraído, el estímulo detiene unas motoneuronas que estaban disparando, y se ve una pausa. Y mientras más actividad hay, más grande es la pausa: la amplitud del cVEMP crece **casi en línea recta** con la fuerza de la contracción (Colebatch y cols., 1994; Lim y cols., 1995; Rosengren y cols., 2019).

Eso tiene dos consecuencias:

1. **El paciente tiene que contraer el músculo**, de forma sostenida, durante todo el registro. Sin contracción el examen no es una prueba de la vía: es una prueba de si el paciente colaboró.
2. **La amplitud cruda no se puede comparar** entre un lado y otro, porque el paciente puede contraer más un ECM que el otro. Por eso se **mide la contracción** (el EMG) y se **corrige** la amplitud dividiéndola por ella. La amplitud corregida no lleva unidades: es una razón.

El oVEMP funciona igual, pero con la mirada: al mirar hacia arriba el oblicuo inferior se contrae más y además queda más cerca de los electrodos, y la respuesta crece casi en línea recta con el ángulo de la mirada (Rosengren y cols., 2019).

:::sabias ¿Sabías que?
El VEMP sirvió primero para comprobar que la respuesta era del vestíbulo. Colebatch y Halmagyi (1992) la registraron en el cuello antes y después de cortar el nervio vestibular en pacientes operados: tras la sección, la onda desaparecía del lado operado.
:::

## Antes de empezar

### Requisitos y contraindicaciones

El examen dura alrededor de **una hora**. Antes de citar al paciente:

- **Ropa cómoda**, porque se le pedirá girar y flectar el cuello.
- Si toma **antivertiginosos, antieméticos o ansiolíticos**, se le pide suspenderlos **48 horas antes**. Son fármacos que deprimen el sistema vestibular y la vigilia, y el examen busca lo que el oído hace, no lo que el fármaco le hace al oído.
- Debe traer un **examen funcional del VIII par** previo, es decir, una audiometría. Sin ella no se puede interpretar un VEMP aéreo (ver "Vía aérea u ósea").

<!-- verificar: efecto de los supresores vestibulares sobre el VEMP; la regla de las 48 horas es del examen vestibular en general y no se encontró una fuente específica del VEMP. -->

El examen **no se hace**, o se hace con la vía ósea, en estos casos:

:::ayuda Contraindicaciones del VEMP
| Caso | Por qué |
|---|---|
| **Hipoacusia de conducción** (los dos VEMP) | Un oído medio que no transmite le quita sonido al vestíbulo: el VEMP aéreo se apaga sin que el sáculo esté enfermo |
| **Limitación del cuello** (cirugía, tortícolis, problemas cervicales) | El cVEMP exige girar y levantar la cabeza varios minutos |
| **Limitación de la mirada** (oftalmoplejía, parálisis de músculos oculares) | El oVEMP exige mirar hacia arriba |
| **Nistagmo espontáneo** (oVEMP) | El movimiento del ojo ensucia el registro y cambia la amplitud |
| **Hipersensibilidad al sonido** | El estímulo es muy intenso |
:::

### Equipo

- **Equipo de potenciales evocados** con amplificador, promediador y, si es posible, **medidor del EMG**: una ventana que muestra cuánto contrae el paciente mientras registras. No todos lo tienen, y eso condiciona cómo se informa (ver "Cómo se informa").
- **Fonos de inserción** con olivas del tamaño del conducto. Opcional: un **vibrador óseo** para la vía ósea.
- **Electrodos** de superficie, **pasta abrasiva**, **gel conductor**, cinta adhesiva, alcohol y algodón.
- **Otoscopio**, para la otoscopía previa, y una **camilla** con respaldo regulable.

### Cuánto sonido

El estímulo del VEMP se acerca al límite de lo que una cóclea tolera, porque el umbral promedio del VEMP en normoyentes es de unos **114 dB pkSPL** (Rosengren y cols., 2019). La seguridad se define en SPL, no en dB nHL, y por eso es importante saber cómo calibra el fabricante su nHL. Con la norma ANSI, para un tono de 500 Hz y fonos TDH49, se suman 13,5 dB al valor en HL para llegar al SPL equivalente (Rosengren y cols., 2019). Dos reglas prácticas:

- **No repitas más de lo necesario.** Cuando hay réplica clara, se cierra: cada barrido de más es sonido de más para el oído.
- **Busca el umbral con pocos niveles**: cada registro de más es otro paquete de sonido fuerte para el mismo oído.

:::ojo Un examen intenso
El VEMP se hace a niveles que en una audiometría serían dolorosos. Si el paciente tiene tinnitus, hiperacusia o una cóclea ya dañada, pregúntale antes y vuelve a preguntarle durante el examen. Y no subas el nivel más allá del tope del equipo.
:::

### Conoce tu equipo: el VEMP de LabSim

La pantalla de LabSim tiene a la izquierda lo que configuras (la prueba, el estímulo, el registro) y lo que pasa en el paciente (el EMG), al centro las curvas de cada oído y abajo las medidas y la asimetría. La figura muestra un cVEMP en curso: los dos oídos están registrados y marcados.

:::imagen /docs/manual/img/estudiante/vemp.png El VEMP de LabSim con los dos oídos de un cVEMP registrados
- @-2.5,18 | **Prueba.** El tipo de VEMP (cVEMP, oVEMP o mVEMP) y el **oído estimulado**. Cambiar de tipo cambia el músculo donde se registra.
- @-2.5,25.6 | **Maniobra.** Cómo contrae el paciente: relajado, girando la cabeza, empujando contra la mano o levantando la cabeza. Debajo dice el músculo y el lado del registro.
- @-2.5,41 | **Estímulo.** Transductor (inserto o vibrador), frecuencia del tone burst, polaridad, intensidad y tasa.
- @-2.5,60 | **Registro.** Barridos, rechazo de artefactos y filtros. Arrancan con valores al azar: dejarlos bien puestos es parte del examen.
- @-2.5,74 | **Registrar y Detener.** Con el músculo fuera de banda no entra ningún barrido y el registro se corta solo.
- @-2.5,85 | **EMG rectificado.** La contracción del paciente en µV, con su banda aceptable (30 a 150 µV en el cVEMP) y el aviso de si está bien, floja o excesiva.
- @33,31 | **P13.** Para marcar, pulsas el botón **P13** (o **N23**) y haces clic sobre la curva: la marca se pega al extremo de la polaridad correcta.
- @47,62 | **N23.** El valle del complejo, a unos 22 ms en esta curva.
- @74,38 | **El OI.** La misma maniobra, el mismo nivel: el complejo es mucho más chico y su escala (50 µV) es otra que la del OD (200 µV).
- @60,98 | **Medidas.** Latencias, amplitud pico a pico, el EMG de cada curva y la amplitud corregida (**p-p corr.**).
- @93,83.5 | **Asimetría.** La razón entre los dos oídos, calculada con las amplitudes **corregidas**: aquí 57 %.
:::

Lo demás está en las pestañas **Análisis** (crecimiento con la intensidad, sintonía y latencias) e **Informe**. Hay también un **mVEMP** (masetérico), que LabSim trae como experimental y este libro no trata.

### Montaje de electrodos: cVEMP

Se prepara la piel de cada punto con alcohol y luego con pasta abrasiva, frotando; después se ponen los electrodos con gel conductor y se fijan con cinta. El objetivo es el mismo que en el ABR: bajar la impedancia entre la piel y el electrodo (→ H10).

:::ayuda Montaje del cVEMP
| Electrodo | Posición |
|---|---|
| **Tierra** | Frente (Fpz) |
| **Común** (rotulado "activo" en el equipo) | Unión esternoclavicular |
| **Canal derecho** (rotulado "referencia derecha") | Tercio superior del ECM derecho |
| **Canal izquierdo** (rotulado "referencia izquierda") | Tercio superior del ECM izquierdo |
:::

Cada ECM es el canal del oído de su lado. El electrodo del músculo debe quedar **sobre el vientre del ECM**, a la altura del punto donde el músculo responde mejor, y a una distancia pareja en los dos lados, porque con el giro de la cabeza los electrodos se corren.

Se comprueba la impedancia de cada electrodo: **menos de 5 kΩ** y una diferencia entre electrodos **menor de 2 kΩ**.

:::comentario Lo que dicen las normas
**Los nombres.** Los equipos rotulan los electrodos de maneras distintas. Aquí el que el equipo llama "referencia" es el que va sobre el músculo, y el "activo" va común, en el esternón. La literatura lo nombra al revés (electrodo de registro sobre el ECM y referencia en el esternón o las clavículas), y no importa cuál nombre uses: lo que decide es la posición. El trazo de cada lado sale de la diferencia entre el electrodo del músculo y el común.

**El punto del músculo.** Rosengren y cols. (2019) recomiendan el electrodo sobre **el medio del haz anterior del ECM o un poco más arriba**, que es el punto donde el músculo responde con mayor amplitud y menor latencia. Más arriba o más abajo, las latencias se alargan y en los extremos del músculo la onda se invierte. El tercio superior de este libro cae en esa zona.

**La impedancia.** En el VEMP importa menos que en un potencial cortical, pero una impedancia mala deja entrar la red eléctrica, y esa interferencia se confunde con EMG e **infla la medida de contracción** (Rosengren y cols., 2019). Por eso se mantiene el límite.
:::

### Montaje de electrodos: oVEMP

:::ayuda Montaje del oVEMP
| Electrodo | Posición |
|---|---|
| **Tierra** | Frente (Fpz) |
| **Común** (rotulado "activo" en el equipo) | Mentón |
| **Canal izquierdo** (rotulado "referencia izquierda") | Bajo la pupila del **ojo derecho** |
| **Canal derecho** (rotulado "referencia derecha") | Bajo la pupila del **ojo izquierdo** |
:::

El canal "izquierdo" es el del oído izquierdo, y por eso va al **ojo derecho**: el oVEMP es cruzado. Un alumno que pone el electrodo del mismo lado registra el oído equivocado. La impedancia debe quedar **menor de 3 kΩ**, con una diferencia entre electrodos **menor de 1 kΩ**, más exigente que en el cuello: la señal del oVEMP es diez veces más chica.

:::comentario Lo que dicen las normas
El montaje clásico del oVEMP pone el electrodo de registro justo bajo el ojo y la referencia uno o dos centímetros más abajo, sobre la mejilla. Está pensado para captar el oblicuo inferior y restar la actividad de los músculos vecinos (Todd y cols., 2007). Una referencia **lejana**, como el mentón de este libro, da **amplitudes mayores**, porque no resta la señal del músculo, pero también deja pasar la de otros músculos del ojo y pierde especificidad (Rosengren y cols., 2019). Las dos formas son válidas; lo que importa es que la norma que uses esté medida con el mismo montaje.
:::

### Los parámetros de rutina

:::ayuda-ancho Configuración del cVEMP y del oVEMP
| Parámetro | cVEMP | oVEMP | Por qué |
|---|---|---|---|
| Estímulo | Tone burst 500 Hz, ventana de Blackman | Tone burst 1.000 o 500 Hz, Blackman | El sáculo responde mejor entre 500 y 1.000 Hz; el burst, a diferencia del click, concentra la energía en una banda |
| Polaridad | Rarefacción | Rarefacción | La del protocolo; LabSim ofrece también condensación y alternante |
| Intensidad | 100 dB nHL | 100 dB nHL | El más alto que la cóclea tolera: el umbral del VEMP es alto |
| Tasa | 5,1 estímulos/s | 5,1 estímulos/s | Sobre 10/s la amplitud del cVEMP cae; el decimal evita la red eléctrica (→ H10) |
| Filtros | 3 Hz a 1,5 kHz | 1 Hz a 1 kHz | Dejan pasar el EMG (40 a 60 Hz en el cuello, unos 100 Hz bajo el ojo) y sacan la deriva |
| Ganancia | 5.000 | 10.000 | El oVEMP es más chico |
| Ventana | 50 a 100 ms | 50 ms, con 10 ms antes del estímulo | Lo que se alcanza a ver del reflejo y su línea de base |
| Barridos | 100 a 200 por registro | 100 a 200 por registro | Menos, y la respuesta chica no sale del EMG |
:::

La **línea de base antes del estímulo** es parte del examen: sirve para medir el EMG de fondo y para saber cuánto ruido hay. Una respuesta confiable es la que supera con claridad lo que hay antes del estímulo (Rosengren y cols., 2019). Por eso el oVEMP lleva un retardo de −10 ms. En el cVEMP el protocolo no fija el retardo: asegúrate de que tu equipo registre al menos 10 a 20 ms antes del estímulo (Rosengren y cols., 2019).

:::comentario Lo que dicen las normas
**El nivel.** Con equipos que solo calibran en dB nHL, Rosengren y cols. (2019) proponen **95 dB nHL** como punto de partida, y aclaran que pueden hacer falta niveles mayores. El libro usa 100. Lo ideal es calibrar en SPL, porque solo en SPL se puede calcular la exposición de la cóclea.

**La frecuencia del oVEMP.** El oVEMP responde mejor a frecuencias más altas que el cVEMP, y en adultos mayores el 1.000 Hz da respuestas mayores que el 500 Hz (Rosengren y cols., 2019); por eso el protocolo admite las dos.

**La duración.** Rosengren y cols. (2019) recomiendan tone bursts de **hasta 6 ms**: más largos aumentan la amplitud, pero también el sonido que recibe la cóclea.

**Los barridos.** La recomendación es **100 a 200 por registro** y **dos registros por condición**, más largos mejor que muchos cortos. Con 50 barridos el EMG de fondo puede parecer una respuesta que no existe.

**El mismo lado.** Con un estímulo monoaural se evita que el otro oído sume su respuesta: en el cVEMP aparece a veces una respuesta cruzada, invertida, en el ECM contrario.
:::

## Paso a paso

### 1. Otoscopía y explicación

Mira ambos oídos (→ H1). Un **tapón de cerumen** que no deja pasar el sonido le quita nivel al estímulo y no se sabe cuánto: se extrae antes (→ H1). Anamnesis otoneurológica: crisis de vértigo, su duración, síntomas auditivos, mareo con ruidos fuertes, cirugías, traumatismos de cuello. Y explícale el examen en sus palabras:

> "El examen evalúa el equilibrio y la función vestibular del oído. Te pondremos electrodos en la frente y en el cuello, y te presentaremos por los fonos sonidos fuertes. Eso hace que un músculo se contraiga un instante, y los electrodos lo registran. Con esto vemos si los dos oídos responden de la misma manera."

Para el oVEMP: electrodos en la frente, el mentón y bajo los ojos, y la respuesta es de un músculo del ojo.

### 2. Montar y revisar

Montaje y impedancias como en "Antes de empezar". Coloca los fonos. **Antes de registrar**, mira la ventana del EMG: si el equipo no te la da, mira el trazo crudo.

### 3. El cVEMP: contrae el músculo y mídelo

El paciente va **semisentado** en la camilla (con el respaldo unos **30° sobre la horizontal**: Rosengren y cols., 2019 recomiendan entre 20° y 40°). Se le pide **anteroflexión de la cabeza y giro hacia el lado contrario al oído que se estimula**: para evaluar el OD, gira hacia la izquierda. Con ese giro el ECM del OD se contrae con fuerza y el del OI se relaja, así que cada oído se registra **por separado**, uno después del otro.

Lo que buscas es una contracción **moderada y pareja en los dos lados**, y no la máxima. Una contracción máxima cansa, tiembla y, al revés de lo que parece, deja residuos de EMG que se confunden con una respuesta chica (Rosengren y cols., 2019). Si el equipo mide el EMG, sírvete de él: LabSim acepta barridos solo cuando el EMG rectificado queda **dentro de una banda** (30 a 150 µV en el cVEMP), y descarta los que quedan fuera.

El ECM se **cansa**, y cada maniobra se cansa a su ritmo. En LabSim, levantar la cabeza desde la posición acostada da el EMG más alto y es la que más rápido se agota; la rotación sostenida de la cabeza da menos EMG y aguanta más tiempo. Por eso se registra por tandas cortas y se **descansa entre curvas**: el músculo recupera la fuerza al doble de la velocidad con que la pierde.

### 4. Registra y repite

Con el nivel a 100 dB nHL, registra el primer oído. Se hace un **segundo registro** para comprobar la replicabilidad: la P13-N23 de ambas curvas debe caer en las mismas latencias. Luego se pasa al oído contrario, con el giro al otro lado.

Un registro de 200 barridos a 5,1 por segundo dura unos 40 segundos. Si la respuesta es chica o falta, no registres muchas curvas cortas: haz **dos largas** (150 a 200 barridos) y compáralas.

{{caso h12_p33}}

:::figura h12_p33 vemp
- @OD P13 | El cVEMP del **OD** de Tomás tiene la P13 a **13,4 ms**. La amplitud pico a pico es de 295 µV, y **5,68** corregida por el EMG.
- @OD N23 | La N23 llega a los **23,3 ms**: el complejo P13-N23 tiene la forma de siempre, una subida y una bajada anchas, de unos 15 ms en total. Es un reflejo, no una onda de nervio.
- @OI P13 | El **OI** tiene la P13 a 12,9 ms y 287 µV, **5,63** corregida.
- @OI N23 | N23 a 23,1 ms. Los dos oídos se parecen: la **razón de asimetría** es de **0 %**.
- En estas figuras la contracción es la misma en los dos lados, así que la amplitud cruda y la corregida dicen lo mismo. En un paciente real no siempre pasa (ver el paso 3).
:::

### 5. Marca y mide

Para cada oído, marca la **P13** (el primer pico positivo, hacia los 13 ms) y la **N23** (el valle que le sigue, hacia los 23 ms), y mide:

- **Latencia de la P13** y **de la N23**, en milisegundos, en el pico.
- **Amplitud pico a pico**, en µV: de la P13 a la N23. Es la altura total del complejo, no la de un pico suelto.
- **EMG**: la contracción de ese registro, en µV rectificados, medida en la **línea de base anterior al estímulo** (Rosengren y cols., 2019).
- **Amplitud corregida**: pico a pico dividida por el EMG.

La amplitud se corrige por la razón que vimos en el Fundamento. En la figura del equipo, el OD midió 420,7 µV con un EMG de 60 µV: 420,7 / 60 = **7,01**. El OI midió 116,5 µV con el mismo EMG: **1,94**.

:::ojo El EMG se mide antes del estímulo, no en el promedio
Medir la contracción en la curva ya promediada da un valor casi cero, porque el promedio elimina justamente el EMG que no se repite con el estímulo. La contracción se calcula con los tramos **anteriores al estímulo de cada barrido** y luego se promedia (Rosengren y cols., 2019). El equipo lo hace solo; si lo calculas a mano, que sea desde los barridos.
:::

:::comentario Lo que dicen las normas
**Sin medidor de EMG.** Medir y vigilar la contracción es parte de las recomendaciones internacionales (Papathanasiou y cols., 2014), pero muchos equipos no lo tienen. En ese caso es más importante usar siempre **la misma maniobra** en los dos oídos y fijar los límites de asimetría con una norma hecha **en las mismas condiciones** (Rosengren y cols., 2019).

**La contracción mínima.** Rosengren (2015, citado en Rosengren y cols., 2019) sugirió un mínimo de unos **80 µV de EMG rectificado**, y aclara que depende de la maniobra y de cómo se mida. La banda de LabSim (30 a 150 µV) es la del simulador: no es un valor normativo.

**Contracciones débiles y fuertes.** Una contracción muy débil da respuestas de menos de 20 µV o ausentes, o con picos tardíos. En un ejemplo publicado, un cVEMP ausente con 61 µV apareció, pequeño y normal, con 127 µV (Rosengren y cols., 2019).
:::

### 6. Busca el umbral

Una vez que hay respuesta a 100 dB nHL con réplica, se **baja de 10 en 10 dB** y se repite. Cuando la respuesta desaparece, se **sube 5 dB**. El **umbral** es el nivel más bajo en que la P13-N23 aparece y se repite. Después se repite todo con el otro oído.

El umbral importa por una razón concreta: en un oído normal es **alto**, y en una **tercera ventana** es mucho más bajo. Una amplitud grande a 100 dB nHL no distingue entre un sáculo normal y uno hipersensible; el nivel al que empieza la respuesta, sí. En el examen de rutina se incluye, además, un nivel **bajo**, cercano o por debajo del límite inferior normal del umbral (Rosengren y cols., 2019); si hay respuesta ahí, el paciente tiene una tercera ventana hasta que se demuestre lo contrario (→ cap. 26).

El cVEMP es un reflejo inhibitorio que **satura**: con niveles normales de estímulo, la amplitud no puede crecer más. Por eso, para detectar una tercera ventana, el umbral es más útil que la amplitud (Rosengren y cols., 2019).

### 7. El oVEMP

El paciente está **sentado** en la camilla. Se le pide que **mire hacia arriba, a unos 30°**, y que mantenga la mirada fija en un punto que le pongas a esa altura: un dedo tuyo, una cinta en la pared. Con la mirada hacia arriba el oblicuo inferior se contrae y queda más cerca del electrodo.

Se registra a 100 dB nHL y se repite para comprobar la replicabilidad. Luego, el oído contrario. El protocolo de este libro no busca umbral en el oVEMP: se registra al nivel máximo del equipo desde el principio, porque el oVEMP es más difícil de provocar que el cVEMP.

Mide la **n10** (la primera onda, negativa, hacia los 10 ms) y la **p16** (la positiva que le sigue, hacia los 16 ms), la **amplitud pico a pico** y la **amplitud corregida**. En el oVEMP no hay una corrección tan estandarizada como en el cVEMP; en LabSim se usa el EMG de referencia del oVEMP (40 µV).

:::figura h12_p33 vemp 2
- @OD n10 | El oVEMP del **OD** de Tomás se registra bajo el **ojo izquierdo**. La **n10** llega a **10,4 ms**.
- @OD p16 | La **p16** llega a **15,6 ms**. La amplitud pico a pico es de **23 µV**, diez veces menor que la del cVEMP: por eso el oVEMP pide más ganancia y se ensucia más fácil.
- @OI n10 | El **OI** tiene la n10 a 9,4 ms y la p16 a 15,6 ms, también con 23 µV.
- La razón de asimetría es de **1 %**. Los dos utrículos responden igual.
:::

:::comentario Lo que dicen las normas
**La mirada.** El oVEMP crece casi en línea recta con el ángulo de la mirada hacia arriba, y Rosengren y cols. (2019) recomiendan la mayor **mirada hacia arriba cómoda**; a los 30° del protocolo se suma una ventaja: es un ángulo fácil de repetir y de enseñar. La falta de mirada hacia arriba es una causa frecuente de oVEMP ausente en adultos mayores.

**El nivel.** El umbral del oVEMP es de **5 a 10 dB más alto** que el del cVEMP (Rosengren y cols., 2019), y por eso se parte desde el nivel máximo.

**La cara.** El ruido del oVEMP viene sobre todo de los músculos de la cara y de los ojos: se le pide al paciente que relaje la cara, que no hable y que no apriete la mandíbula.
:::

### Vía aérea u ósea

El protocolo del libro registra el VEMP por **vía aérea**, con fonos de inserción, y excluye a quien tiene una **hipoacusia de conducción**. La razón es simple: el sonido que no llega al vestíbulo no activa el sáculo, y la respuesta cae o se apaga aunque el órgano esté sano. Zhou y cols. (2012) hallaron el VEMP aéreo ausente en los 50 pacientes con patología de oído medio de su serie. En LabSim, el umbral del VEMP aéreo sube del orden del gap del audiograma.

La alternativa es la **vía ósea**: un vibrador en la mastoides (o en la frente) que hace vibrar el cráneo y llega al vestíbulo **sin pasar por el oído medio**. Con el vibrador, el VEMP se recupera aunque el oído esté conductivamente sordo. Pero cambian varias cosas:

- **El estímulo es bilateral**: el cráneo entero vibra, así que los dos oídos reciben la señal. La lateralidad se lee por el **músculo**, no por el estímulo: la respuesta del ECM del lado enfermo falta aunque se estimulen los dos oídos a la vez.
- **No es específico del sáculo**: la vibración activa sáculo y utrículo casi por igual. Una ausencia de cVEMP por vía ósea dice "otolitos", no "sáculo".
- **Se calibra en fuerza**, no en SPL (dB FL). Un vibrador B-71 en la mastoides con 500 Hz es efectivo alrededor de los 135 dB pkFL (Rosengren y cols., 2019). En LabSim la escala ósea es propia, de 20 a 75 dB FL, y se le declara al vibrador una ventaja de 15 dB sobre el sonido.
- **Para el oVEMP, la vía ósea da respuestas más robustas** que el sonido, y es mejor para detectar una pérdida vestibular; el sonido, en cambio, es mejor para detectar una tercera ventana (Rosengren y cols., 2019).

### Patrones: cómo se lee un VEMP

:::ayuda-ancho Cómo se lee un VEMP
| | cVEMP (sáculo, nervio inferior) | oVEMP (utrículo, nervio superior) | Qué sugiere |
|---|---|---|---|
| **Normal** | Presente, simétrico | Presente, simétrico | Vía conservada |
| **Sacular / nervio inferior** | Reducido o ausente de un lado | Conservado | Hidrops, o daño de la rama inferior |
| **Utricular / nervio superior** | Conservado | Reducido o ausente | Neuritis de la rama superior |
| **Laberinto completo o nervio entero** | Ausente de un lado | Ausente (del oído opuesto al estimulado) | Laberintitis, parotiditis, sección, tumor grande |
| **Latencia larga con amplitud presente** | P13 y N23 tardías | n10 y p16 tardías | Lentitud de la vía en el tronco o en la médula (también un electrodo mal puesto) |
| **Tercera ventana** | Umbral **bajo** y amplitud **grande** | Amplitud grande | Dehiscencia del conducto superior (→ cap. 26) |
| **Conductivo** | Cae por vía aérea; normal por vía ósea | Igual | Un oído medio que no transmite, no un órgano enfermo |
:::

Hay una trampa en la tabla. En una asimetría de amplitud, **el lado más chico suele ser el enfermo**, salvo en las terceras ventanas y en el hidrops temprano, donde puede ser el lado más grande (Rosengren y cols., 2019). La razón de asimetría dice que los dos lados son distintos, no cuál es el anormal: eso lo dicen la norma, el umbral y el audiograma.

## Cómo se informa

### Qué se mide

- **Latencia P13 y latencia N23** (cVEMP), **n10 y p16** (oVEMP), por oído.
- **Amplitud** pico a pico y, si hay medidor de EMG, **corregida**.
- **Umbral** del complejo P13-N23 (cVEMP).
- **Razón de asimetría**, calculada entre los dos oídos con la fórmula de Jongkees:

**Asimetría (%) = | A(OD) − A(OI) | ÷ ( A(OD) + A(OI) ) × 100**

La fórmula con el signo, sin el valor absoluto, indica **de qué lado** está la diferencia (positivo si el OD es mayor); con el valor absoluto el resultado es siempre positivo y el límite normal es otro (Rosengren y cols., 2019). Aquí se usa el valor absoluto, como LabSim, y la amplitud que se compara es la **corregida** por el EMG. Si tu equipo no mide el EMG, se usa la amplitud cruda, con un límite que sea de ese método.

**Valor significativo:** **35 %** o más en el cVEMP y **33 %** o más en el oVEMP.

:::comentario Lo que dicen las normas
**Por qué se corrige.** Un ejemplo publicado: en un voluntario sano, el ECM derecho se contrajo con 46 µV y el izquierdo con 156 µV. Las amplitudes crudas fueron de 109 y 320 µV, una asimetría de **49 %**; corregidas por el EMG, la asimetría fue de **6,7 %** (Rosengren y cols., 2019). Sin corregir, un sano parece enfermo. McCaslin y cols. (2014) mostraron lo mismo en una serie de sujetos normales: la normalización reduce las asimetrías.

**Los límites.** Los 35 % del protocolo coinciden con el límite del cVEMP corregido que dan Rosengren y cols. (2019), citando a Welgampola y Colebatch (2001): **35 %** con amplitud corregida y **46 %** con amplitud cruda. McCaslin y cols. (2014) dan 43 % con amplitud cruda y cerca de 30 % con la corregida. Un límite depende de cómo se midió, y por eso cada centro debe tener el suyo. Para el oVEMP, el límite de 33 % del protocolo no tiene una fuente en lo que se revisó para este capítulo.
<!-- verificar: límite de asimetría del oVEMP; no se encontró un valor publicado en las fuentes leídas. -->
:::

### Contra qué se compara

Los valores normales dependen del estímulo, de la contracción y del montaje. La **latencia** depende mucho de la forma del estímulo y de su tiempo de subida (Rosengren y cols., 2019); la **amplitud** y el **umbral**, de la edad. Con los años el cVEMP se achica y su umbral sube, y entre el 5 y el 15 % de las personas mayores de 60 años no tiene cVEMP aéreo; el oVEMP aéreo falta con más frecuencia aún. Por eso se compara contra una norma **de la edad del paciente** y, con un oVEMP aéreo ausente en un adulto mayor, se tiene cautela (Rosengren y cols., 2019).

:::ayuda-ancho Valores de referencia que usa LabSim (tone burst de 500 Hz, vía aérea)
| Población | cVEMP: P13 (ms) | cVEMP: N23 (ms) | cVEMP: p-p (µV) | oVEMP: n10 (ms) | oVEMP: p16 (ms) | oVEMP: p-p (µV) |
|---|---|---|---|---|---|---|
| Niño (6 a 17 años) | 11,5 | 21,0 | 360 | 8,8 | 14,5 | 23 |
| Hombre adulto | 13,0 | 23,0 | 290 | 10,0 | 16,0 | 19 |
| Mujer adulta | 12,8 | 22,5 | 320 | 9,8 | 15,8 | 20 |
| Adulto mayor (65 o más) | 14,5 | 24,5 | 205 | 11,5 | 17,5 | 13,5 |

Son valores medios, sin desviación estándar. La amplitud del cVEMP está referida a un EMG de 50 µV y la del oVEMP a uno de 40 µV. LabSim elige la tabla por la edad y el sexo del paciente.
:::

<!-- verificar: el origen de los valores de la tabla de LabSim (resources/vemp/normative_data.json) no está documentado en el repositorio; no hay desviación estándar. Declarar la fuente o reemplazarla por una serie publicada. -->

### Un ejemplo de informe

El informe describe primero lo que se vio en cada oído y recién al final concluye.

> **Potenciales evocados miogénicos vestibulares cervicales (cVEMP).** Se realiza la prueba a 100 dB nHL, mediante transducción aérea, con tone burst de 500 Hz, polaridad de rarefacción, y con contracción del esternocleidomastoideo por giro cefálico.
>
> **OD**: se observa complejo de ondas P13-N23 a 100 dB nHL. Latencia P13: 13,4 ms. Latencia N23: 23,3 ms. Amplitud: 295 µV (5,68 corregida por el EMG).
>
> **OI**: se observa complejo de ondas P13-N23 a 100 dB nHL. Latencia P13: 12,9 ms. Latencia N23: 23,1 ms. Amplitud: 287 µV (5,63 corregida por el EMG).
>
> **Razón de asimetría**: 0 % (no significativa).
>
> **Conclusión**: el examen es compatible con simetría vestibular para las estructuras estudiadas (sáculo y nervio vestibular inferior).

Para el oVEMP, el informe es el mismo, con n10 y p16, **sin umbral**, y la conclusión habla de las estructuras que éste estudia: **utrículo y nervio vestibular superior**.

La conclusión es una de estas: **simetría vestibular**, **asimetría leve no significativa**, o **hipofunción vestibular** del OD, del OI o bilateral, siempre "para las estructuras estudiadas". El VEMP no distingue el órgano de su nervio: una caída puede ser del sáculo o del nervio inferior. Si el umbral está bajo y la amplitud grande, la conclusión no es una hipofunción: se describe como **umbral bajo y amplitud aumentada** y se pide la imagen (→ cap. 26).

Cuando falta o está alterado el VEMP de un lado, se anota que la **otoscopía y el audiograma** del mismo oído están normales o no: un oído medio que no transmite explica lo que parece un órgano enfermo.

## Lectura en pacientes

{{caso h12_p38}}

Patricia tiene un Ménière del OI (→ cap. 9). Mira los dos VEMP juntos: el sáculo cae y el utrículo no.

:::figura h12_p38 vemp
- @OD P13 | El cVEMP del **OD**, el oído sano, tiene la P13 a 12,9 ms y 350 µV: **6,79** corregidos por el EMG.
- @OI P13 | En el **OI** el complejo casi no sale del ruido: **33 µV**, **0,66** corregidos. El sáculo del lado enfermo responde mucho menos.
- La razón de asimetría es de **82 %**, sobre el 35 % de corte, y el lado más chico es el enfermo: el **cVEMP del OI está alterado**.
:::

:::figura h12_p38 vemp 2
- @OD n10 | El oVEMP de Patricia: **24 µV**, **0,57** corregidos en un oído...
- @OI n10 | ...y **24 µV**, **0,55** en el otro. La razón de asimetría es de **1 %**.
- Con el cVEMP del OI alterado y el oVEMP simétrico, el compromiso es **sacular**: la rama inferior, no la superior. Es lo que se espera en un hidrops, donde el sáculo se daña antes que el utrículo (→ cap. 9).
:::

{{caso h12_p34}}

Carolina tiene una otoesclerosis del OD (→ H3 y H7). Su cVEMP **también** está alterado, y la razón es otra.

:::figura h12_p34 audiograma
- @OD 500 | El OD tiene 50 dB en 500 Hz por vía aérea...
- @OD osea 500 | ...y 10 dB por vía ósea: un **gap de 40 dB**. En 1.000 Hz es de 30 dB.
- El gap está en los graves, justo donde el VEMP se estimula.
:::

:::figura h12_p34 vemp
- @OD P13 | El cVEMP del **OD** es mucho menor: **109 µV**, **2,15** corregidos.
- @OI P13 | El **OI** tiene 340 µV, **6,81** corregidos.
- La razón de asimetría es de **52 %**, sobre el corte. Si la leyeras sola, dirías "hipofunción sacular del OD". Pero el umbral del OD es **30 dB más alto** que el del OI (90 contra 60 en la escala de LabSim), del tamaño del gap. El sonido llega atenuado al vestíbulo: la que falla es la **transmisión**, no el sáculo. Con el vibrador, en LabSim, la respuesta se recupera.
:::

{{caso h12_p42}}

Matías no oye por el OD desde los 6 años (→ cap. 7). Es el caso opuesto: ahí el VEMP faltante **sí** es del oído interno.

:::figura h12_p42 vemp
- @OD P13 | El **OD** no tiene complejo: las marcas del equipo caen sobre el ruido, y miden **19 µV**, **0,38** corregidos.
- @OI P13 | El **OI**, normal, da **290 µV**, **5,75** corregidos.
- La razón de asimetría es de **88 %**. El oído medio de Matías está sano (timpanograma A) y el nivel y la contracción son los mismos que los del OI. La falta de respuesta es del laberinto: la parotiditis que le quitó la cóclea le quitó también el sáculo.
:::

Dos puntos para tener presentes:

- El VEMP **no necesita que el oído oiga**: la sordera de Matías no es la razón de que falte su VEMP. Si su oído medio estuviera enfermo, sí lo sería. Lo que falta es el sáculo.
- Antes de llamar "ausente" a una respuesta que no sale del ruido, **repite con más barridos** y asegura la contracción. Una ausencia sin comprobar es un error frecuente (ver abajo).

## Errores frecuentes

- **Estímulo débil.** Con menos nivel del necesario, hay muchas respuestas chicas o ausentes. Es el primero que se nota al implementar el examen (Rosengren y cols., 2019).
- **Contracción floja o excesiva.** Floja: respuesta chica o tardía, o ausente. Excesiva: fatiga, temblor y residuos que parecen respuesta. Ni la más fuerte ni la más débil: una moderada y pareja.
- **Contracción distinta en los dos lados.** Fabrica una asimetría que no existe. Se mide el EMG y se corrige; si no, se usa la misma maniobra en los dos oídos.
- **Registrar pocos barridos.** 50 barridos de EMG de fondo pueden dibujar una respuesta donde no hay.
- **Medir el EMG en el promedio.** Da valores cercanos a cero y una amplitud corregida que no sirve (ver arriba).
- **Electrodo mal puesto o corrido.** Alarga las latencias y, en los extremos del músculo, invierte la onda. Un electrodo que se corre con el giro de la cabeza hace lo mismo.
- **Mirada insuficiente en el oVEMP.** Es la causa más frecuente de un oVEMP chico o ausente.
- **Poner el electrodo del oVEMP del mismo lado.** El oVEMP es cruzado: se registra el oído equivocado.
- **No mirar el oído medio.** Un cVEMP bajo con un gap aéreo-óseo y un umbral alto no es un sáculo enfermo (→ caso de Carolina).
- **Leer un oVEMP aéreo ausente como enfermedad.** Sobre todo en adultos mayores: es sensible a la edad y da más resultados falsamente alterados que el oVEMP por vía ósea.
- **Cegarse con la asimetría.** Un lado de amplitud grande puede ser el anormal (tercera ventana). La razón de asimetría no dice cuál.
- **Confundir "ausente" con "enfermo", o "presente" con "sano".** Una respuesta normal no descarta un hidrops.
- **Sonido de más.** Repetir registros sin necesidad expone la cóclea.

:::ojo Ojo clínico
Antes de informar un VEMP, pregúntate si **calza con lo demás**: con el audiograma y el timpanograma del mismo oído, con las crisis de vértigo y con el cVEMP junto al oVEMP. Un VEMP no es una prueba de la audición ni de los conductos, y un resultado aislado se interpreta junto con las otras pruebas del equilibrio (→ H15 a H17).
:::

## En LabSim

El VEMP de LabSim está hecho para equivocarse como uno real:

- **Se promedian barridos de verdad.** Cada tick el equipo genera barridos, acepta o rechaza cada uno según el EMG, y la curva es el promedio de los aceptados. El ruido baja con la raíz de los barridos.
- **El paciente parte relajado.** La primera maniobra de cada tipo es la **posición sin contracción**: con el EMG fuera de banda el equipo **no acepta barridos** y el registro se corta solo. Elegir la maniobra es parte del examen.
- **El EMG se mide por registro**, y la asimetría se calcula con la amplitud **corregida**.
- **Los parámetros del registro arrancan al azar**, como en el ABR.
- **La intensidad del cVEMP aéreo está en dB SPL**, en una escala propia de 50 a 125. No es la de dB nHL de este capítulo: no mezcles los números de la pantalla con los 100 dB nHL del protocolo.
- **El vibrador óseo** está en la escala de dB FL (20 a 75). Si el oído tiene un gap en el audiograma del mismo caso, la vía aérea cae y el vibrador la recupera.
- **La sintonía** (500, 750 y 1.000 Hz) cambia la amplitud, y un umbral muy bajo invierte la sintonía y sube la amplitud: es lo que el simulador usa como firma de la tercera ventana. En la literatura la tercera ventana tiene una sintonía más ancha, y el Ménière responde más a 1.000 que a 500 Hz (Rosengren y cols., 2019).

:::comentario Lo que el simulador no tiene
LabSim **no controla la impedancia de los electrodos**: un electrodo mal puesto no empeora el registro, y tampoco hay posición de los electrodos que equivocar. La contracción y la mirada son maniobras de una lista, y cada caso guarda **un solo umbral** por tipo de VEMP. El cansancio del músculo sí está. Y el VEMP del simulador no distingue entre el sáculo y su nervio, igual que el examen real.
:::

Para practicar, los pacientes de este capítulo están entre los de práctica (★): Tomás (33), Carolina (34), Patricia (38) y Matías (42).

:::pregunta Preguntas para practicar
1. En el cVEMP de LabSim, el OD midió 420,7 µV con un EMG de 60 µV, y el OI 116,5 µV con 60 µV. Calcula las amplitudes corregidas y la razón de asimetría. ¿Qué habría pasado con la asimetría si el EMG del OD hubiera sido de 120 µV, con la misma amplitud?
2. Un cVEMP del OD no sale del ruido con 100 dB nHL. Enumera, en orden, qué comprobarías antes de decir que el sáculo no funciona.
3. Carolina tiene una razón de asimetría de 52 %. ¿Qué dos datos de su audiograma y de su umbral te impiden leerla como hipofunción sacular? ¿Qué examen repetirías?
4. Patricia tiene un cVEMP del OI alterado y un oVEMP simétrico. ¿Qué rama del nervio vestibular está comprometida? ¿Qué cambiaría si fuera el oVEMP el alterado y el cVEMP el simétrico?
5. ¿Por qué el oVEMP del OD se registra bajo el ojo izquierdo? ¿Qué electrodo has invertido si el oVEMP del OD sale bajo el ojo derecho?
6. Un paciente con tinnitus pulsátil y autofonía tiene el umbral del cVEMP en un nivel mucho más bajo que el normal y una amplitud grande. ¿Qué examen de imagen esperas que pida el médico? ¿Por qué la razón de asimetría no basta?
7. Una paciente de 72 años tiene un oVEMP aéreo ausente y un cVEMP aéreo pequeño pero presente. ¿Qué conclusión no deberías sacar? ¿Qué cambiarías en el registro?
:::

## Referencias

### Técnica

1. Papathanasiou ES, Murofushi T, Akin FW, Colebatch JG. International guidelines for the clinical application of cervical vestibular evoked myogenic potentials: an expert consensus report. Clin Neurophysiol. 2014;125(4):658-66. doi:10.1016/j.clinph.2013.11.042
1. Rosengren SM, Colebatch JG, Young AS, Govender S, Welgampola MS. Vestibular evoked myogenic potentials in practice: methods, pitfalls and clinical applications. Clin Neurophysiol Pract. 2019;4:47-68. doi:10.1016/j.cnp.2019.01.005
1. Rosengren SM, Welgampola MS, Colebatch JG. Vestibular evoked myogenic potentials: past, present and future. Clin Neurophysiol. 2010;121(5):636-51. doi:10.1016/j.clinph.2009.10.016
1. Welgampola MS, Colebatch JG. Characteristics of tone burst-evoked myogenic potentials in the sternocleidomastoid muscles. Otol Neurotol. 2001;22(6):796-802. doi:10.1097/00129492-200111000-00014
1. Welgampola MS, Colebatch JG. Characteristics and clinical applications of vestibular-evoked myogenic potentials. Neurology. 2005;64(10):1682-8. doi:10.1212/01.wnl.0000161876.20552.aa
1. Todd NP, Rosengren SM, Aw ST, Colebatch JG. Ocular vestibular evoked myogenic potentials (OVEMPs) produced by air- and bone-conducted sound. Clin Neurophysiol. 2007;118(2):381-90. doi:10.1016/j.clinph.2006.09.025
1. Iwasaki S, McGarvie LA, Halmagyi GM, Burgess AM, Kim J, Colebatch JG, et al. Head taps evoke a crossed vestibulo-ocular reflex. Neurology. 2007;68(15):1227-9. doi:10.1212/01.wnl.0000259064.80564.21

### Contracción del músculo y amplitud corregida

1. Colebatch JG, Halmagyi GM, Skuse NF. Myogenic potentials generated by a click-evoked vestibulocollic reflex. J Neurol Neurosurg Psychiatry. 1994;57(2):190-7. doi:10.1136/jnnp.57.2.190
1. Lim CL, Clouston P, Sheean G, Yiannikas C. The influence of voluntary EMG activity and click intensity on the vestibular click evoked myogenic potential. Muscle Nerve. 1995;18(10):1210-3. doi:10.1002/mus.880181021
1. McCaslin DL, Fowler A, Jacobson GP. Amplitude normalization reduces cervical vestibular evoked myogenic potential (cVEMP) amplitude asymmetries in normal subjects: proof of concept. J Am Acad Audiol. 2014;25(3):268-77. doi:10.3766/jaaa.25.3.6

### Fisiología y patología

1. Colebatch JG, Halmagyi GM. Vestibular evoked potentials in human neck muscles before and after unilateral vestibular deafferentation. Neurology. 1992;42(8):1635-6. doi:10.1212/wnl.42.8.1635
1. Curthoys IS. A critical review of the neurophysiological evidence underlying clinical vestibular testing using sound, vibration and galvanic stimuli. Clin Neurophysiol. 2010;121(2):132-44. doi:10.1016/j.clinph.2009.09.027
1. Curthoys IS, Vulovic V, Manzari L. Ocular vestibular-evoked myogenic potential (oVEMP) to test utricular function: neural and oculomotor evidence. Acta Otorhinolaryngol Ital. 2012;32(1):41-5. PMID 22500066
1. Zhou G, Poe D, Gopen Q. Clinical use of vestibular evoked myogenic potentials in the evaluation of patients with air-bone gaps. Otol Neurotol. 2012;33(8):1368-1374. doi:10.1097/MAO.0b013e31826a542f
