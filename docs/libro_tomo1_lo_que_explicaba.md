# Lo que el tomo I del libro explicaba de LabSim

Texto que salió del tomo I del libro de ORL el 2026-10-19 (secciones "En LabSim" y recuadros o figuras propias del simulador), tal como estaba. Sirve para revisar que el manual del estudiante lo cubra y para reparar los límites que menciona. Las preguntas para practicar y los casos quedaron en el libro.


## H01-anamnesis-otoscopia-y-lavado-de-oidos

### Sección En LabSim

### La anamnesis: hablar con el paciente

Con la atención abierta, **Hablar con el paciente** abre la entrevista. El paciente contesta como lo haría en la consulta: según lo que sabe de sí mismo y **cuánta conciencia tiene de su problema**. Puede no saber que oye mal o no relacionar un fármaco con su acúfeno: si no preguntas, no te lo cuenta.

- Si viene **acompañado**, el encabezado dice a quiénes atiendes. No eliges a quién le hablas: **nómbralo al escribir** y contesta quien corresponda. A Benjamín puedes preguntarle si le duele el oído; las fechas de las otitis las sabe su mamá.
- **Ver ficha** muestra el **historial** del paciente, con lo que dijeron otros profesionales. Léelo antes de entrar, como en un box real.
- La conversación queda guardada con la atención y tu docente la lee. En **Cómo vas** se cuentan las preguntas que haces en la anamnesis.

### La otoscopía

El botón **OT** abre el otoscopio, con un visor para cada oído. Al pasar el mouse sobre el visor ves un círculo de luz que sigue al cursor, como el campo real: **recorre toda la membrana** y el conducto antes de decidir. **Cono pediátrico** y **Cono adulto** cambian el tamaño del campo.

En la pestaña **Informe** eliges el **hallazgo** (retracción, perforación, efusión, timpanoesclerosis, colesteatoma, inflamación, tubo, miringitis) y haces clic en el **cuadrante** donde lo viste: AS, AI, PI, PS o la pars flácida (PF). Después marcas el **conducto** (normal, cerumen, edema, otorrea, exostosis) y escribes tus **observaciones**. El esquema es el de la Figura H1.2: piensa en qué oído estás antes de marcar anterior o posterior.

### El lavado

El lavado no se simula: lo que practicas es **la decisión**. Si ves cerumen u otorrea, márcalo en el informe y decide si sigues con los exámenes.


## H02-acumetria

### Sección En LabSim

El botón **AC** del Box Audiología abre la acumetría, con diapasones de **500 y 1.000 Hz**. En **Rinne** eliges diapasón y oído, pruebas **mastoides** y **pabellón** y recién entonces puedes **preguntar dónde lo escucha más fuerte**. En **Weber** apoyas el diapasón en la frente y el paciente dice dónde lo escucha.

LabSim no te dice "positivo" ni "negativo": la conclusión es tuya. Escucha lo que dice el paciente en cada posición: con un falso negativo contesta "en la mastoides", igual que una conductiva, pero frente al pabellón **no oye nada**.

Las respuestas salen del audiograma del caso, con umbrales que tu docente puede ajustar. De fábrica, el Rinne es negativo con un gap de **15 dB**; es falso negativo cuando la aérea llega a **70 dB** y la ósea del otro oído es mejor; y el Weber lateraliza con **10 dB** de asimetría, sumando la diferencia de gap (empuja al oído con más gap) y la de vía ósea (empuja al de mejor cóclea). Son reglas de libro: en la clínica las respuestas son menos limpias (Stankiewicz y Mowry, 1979).


## H04-enmascaramiento

### Sección En LabSim

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


## H05-logoaudiometria-y-campo-dinamico

### Recuadro o figura

:::imagen /docs/manual/img/estudiante/listas-de-palabras.png Las listas de palabras de LabSim
- @72,12 | **Lista abierta.** Arriba, las pestañas: *Disilabos (Palacios)* y, con las flechas, *Terminos Conocidos*.
- @68,20.4 | **Cada botón es una palabra.** Suena por el canal de habla y el paciente la repite, o dice otra cosa si no la entendió.
- @72,87.2 | **Lista 2 y Lista 3.** Una lista nueva en cada nivel: con la misma, el paciente acierta por memoria.
:::

### Recuadro o figura

:::comentario El roll-over en LabSim
En el simulador la caída pasado el máximo sale del **componente retrococlear** del caso, no del reclutamiento: un oído coclear baja poco (Hernán, índice 0,13) y uno retrococlear mucho (Raúl, 0,62), como describe la literatura (Jerger y Jerger, 1971; Gang, 1976). La caída se completa unos 25 dB sobre el máximo, o en los 100 dB del canal de habla, y la curva nunca llega a 0. Ningún índice decide solo: lo que orienta a una lesión retrococlear es una **discriminación pobre para el PTP**, asimétrica, con el resto de la batería (reflejos, deterioro tonal, PEAT) apuntando al mismo lado.
:::

### Sección En LabSim

1. Elige **Habla** en el canal 1, la salida y el nivel, y activa **Invertir** para dejar el canal abierto.
2. **SDT:** elige *pa pa pa* en *Comandos de voz*, da la instrucción **Escuche mi voz** con *Talkback* y presenta: el paciente levanta la mano cuando oye la voz. En los pacientes de práctica la levanta **5 dB bajo su SRT**.
3. **Palabras:** abre **Listas de Palabras** y haz clic en cada palabra. Anota cada acierto con **+1**; **Limpiar** antes de cada lista.
4. **Enmascarar:** **SN** en el canal 2, al otro oído, con *Invertir*.
5. **LDL:** vuelve a **Tono**, da la instrucción **Pitos fuertes** y presenta: el paciente dice "molesta" al llegar a su umbral de molestia.

El paciente simulado repite bien, en cada nivel, una cantidad fija de las 25 palabras, la que le corresponde según su curva: los porcentajes son siempre **múltiplos de 4**, y cuáles acierta cambia de una lista a otra. Su curva pasa la **mitad de su máximo en el SRT** del caso, que en los pacientes de práctica es el promedio de los dos mejores umbrales de 500, 1.000 y 2.000 Hz: el SRT que midas con palabras concuerda con el PTP. Arranca unos 10 dB bajo el SRT, a 20 dB sobre él ya está cerca de su máximo y lo alcanza en el nivel que fija el caso. Si no enmascaras, la voz cruza con 45 dB menos y contesta con el oído que mejor entienda; si enmascaras de más, el ruido cruza de vuelta y la curva se corre de a poco a la derecha. Con un ruido que no es de habla, el enmascaramiento rinde menos. Para el SDT, el ruido mínimo es unos 5 dB más que el de la fórmula: el oído no evaluado detecta la voz 5 dB antes de reconocerla.

:::comentario Lo que el simulador no tiene
Las palabras de LabSim están **grabadas**, con una sola voz: la voz viva no se practica. Las palabras desactivadas todavía no tienen grabación.
:::

Los pacientes de este capítulo están entre los de práctica (★): Carolina, Hernán, Raúl y Luis.


## H06-pruebas-supraliminares

### Recuadro o figura

:::imagen /docs/manual/img/estudiante/comandos-de-voz.png Las instrucciones de las pruebas supraliminares en LabSim
- @-3,15 | **Colocar fonos.** La de los umbrales, y también la del Stenger: al paciente no se le anuncia otra prueba.
- @-3,70 | **Pitos fuertes.** El umbral de molestia (LDL), antes de cualquier supraliminar (→ H5).
- @32.8,48 | **Dos pitos.** El Fowler. Después, *¿Sonidos iguales?* o *¿En qué oído?* para preguntar en cada comparación.
- @32.8,81 | **Cambie de volumen.** El SISI: el paciente dice "sí" cada vez que nota la subida.
- @103,15 | **Mano levantada.** El Carhart.
- @103,81 | **Rosemberg bilateral.** El Rosenberg (así se escribe en el botón).
- @103,70 | **Ruido blanco contralateral.** El STAT: tono fuerte en un oído y ruido en el otro.
- @103,26 | **Mano levantada en ruido.** El Carhart avisando el ruido en el otro oído.
:::

### Sección En LabSim

Cada prueba se hace con su instrucción de la figura H6.3, dada con *Talkback*, y el paciente responde como uno real:

- **SISI**: con el tono sonando, sube un clic de 1 dB y vuelve a bajarlo. Las subidas de 5 dB las nota siempre; con el portador bajo el umbral no nota ninguna.
- **Fowler**: en una frecuencia que no cumple los requisitos, el paciente contesta como un oído sin reclutamiento.
- **Deterioro tonal**: en el Carhart cada subida reinicia el minuto; en el Rosenberg el minuto es uno solo. El minuto es real: cronométralo. El Carhart se instruye con *Mano levantada* o, si quieres avisarle del ruido en el otro oído, con *Mano levantada en ruido*: es la misma prueba.
- **STAT**: el tono va a 100 dB HL en 500 y 2.000 Hz y a 105 dB HL en 1.000 Hz, con ruido blanco a 90 dB en el otro oído. A otro nivel, o sin el ruido, no hay resultado. Si el nivel llega a su LDL, el paciente dice "molesta" y en esa frecuencia tampoco. Un oído retrococlear baja la mano antes del minuto aunque le sobre margen sobre su umbral; uno coclear lo sostiene.
- **Stenger**: se instruye con *Colocar fonos*, como los umbrales. El paciente lo reconoce por el estímulo: el mismo tono, por vía aérea, en los dos oídos a la vez. Percibe el tono con más nivel de sensación sobre sus umbrales **verdaderos**, no sobre los que te dio.
- **Acufenometría**: todavía no está. El caso trae el acúfeno en su ficha (lado, tipo de sonido, si es permanente o pulsátil y una frecuencia aproximada) y el paciente lo cuenta en la anamnesis, pero no hay un acúfeno simulado que igualar con el audiómetro.
- **Orden**: el indicador de técnica espera las supraliminares entre la logoaudiometría y la vía ósea. Como la acufenometría no existe, revisa el orden sin ella.

:::comentario Lo que el simulador todavía no tiene
La IWA y la acufenometría no se practican en LabSim, y entre los pacientes de práctica no hay ninguno con pérdida no orgánica. El docente puede crear uno marcando el oído fingido (casilla Stenger del caso): sus umbrales son los que el paciente entrega, y el verdadero se supone igual al del otro oído, como en alguien que oye parejo y finge una pérdida de un lado. Lo que todavía no se puede es cargar el umbral verdadero del oído fingido, así que una pérdida real que el paciente exagera no se puede armar. El paciente simulado tampoco se cansa ni se confunde; uno real sí.
:::

Para practicar, Patricia y Raúl están entre los pacientes de práctica (★).


## H07-impedanciometria

### Sección En LabSim

El impedanciómetro se abre con la tecla **Z**. Tiene las cuatro pantallas de este capítulo: timpanograma (sonda de 226 o 1000 Hz), reflejos ipsi y contra, *Tone Decay* y *ETF*.

- El **timpanograma** quiebra en el pico, como uno real, y su ancho depende del tipo: el Ad es el más en punta y el Cs el más redondeado.
- El **volumen del conducto** dice dónde mide la sonda. Una perforación da una curva plana con volumen **alto**, porque la sonda suma el aire del oído medio, y en ella la prueba de membrana perforada muestra si la trompa es permeable. Un tapón de cerumen da una curva plana con volumen **bajo**: la sonda solo mide el poco aire que queda hasta el cerumen.
- Los **reflejos** siguen la audición del paciente: aparecen a su nivel normal en un oído sano, se acercan al umbral tonal en uno coclear, suben con el gap de un oído conductivo y faltan cuando la sonda está en un oído medio rígido o lleno. El dial y la ficha están en **dB SPL**.
- La **forma de la curva** del reflejo (normal, ON-OFF) la elige el docente para cada caso, y el **deterioro** depende de si el oído estimulado tiene un componente retrococlear.
- Si la otoscopía del caso no permite poner nada en el conducto (otitis externa, cuerpo extraño, conducto ausente; el docente puede marcar cualquier otro oído, como uno con otorrea), el caso trae ese oído como **no realizable**. El equipo no te avisa al elegir el oído: decidir no medir es parte del ejercicio, y sale de la otoscopía y la entrevista. Se informa "No realizable" con el motivo.
- Intentar medir en ese oído (con la sonda, o con el fono de un contralateral) es una **falta grave**. El equipo no mide, lo avisa en rojo, queda registrado en tu atención y el impedanciómetro queda **fuera de uso el resto de la atención, en los dos oídos**: la sonda que entró a un oído con secreción no puede ir al otro. Con el paciente siguiente el equipo vuelve limpio. La falta se muestra aparte y no cambia tu porcentaje de técnica.
- Una **perforación seca no es "no realizable"**: se mide, da su volumen alto y su función tubaria se hace con la prueba de membrana perforada. Lo que no entra es la sonda en un oído con secreción.
- En **ETF** eliges tú la prueba (membrana íntegra o perforada) según lo que viste en la otoscopía y el timpanograma.
- Si a un **lactante** le pones la sonda de 226 Hz, el equipo te deja hacerlo y dibuja un pico aunque el oído medio esté lleno. El simulador te deja cometer el error, como el equipo real.

:::comentario Lo que dicen las normas
La BSA no recomienda la timpanometría cuando la perforación se ve en la otoscopía, porque no agrega nada; sirve cuando la membrana no se ve bien (BSA, 2024). LabSim la deja hacer a propósito: el volumen alto es lo que tienes que aprender a reconocer, para cuando la perforación no se vea.
:::

:::comentario Lo que el simulador no tiene
Las pruebas de función tubaria salen siempre "de libro", sin la variabilidad de un paciente real. Y la fila de **ruido** (NBN) del contralateral se calcula con el promedio de los tonos: no sale más baja que ellos, como saldría con un ruido de verdad.
:::

Para practicar, los pacientes de práctica (★) de este capítulo son Carolina y Benjamín; Tomás (33) para ver un oído normal, con el ipsilateral en 90, 85, 90 y 90 dB SPL y el contralateral en 95, 90, 95 y 95; para el patrón diagonal, Raúl (39) y el paciente con cófosis (42).


## H08-audiometria-pediatrica-y-campo-libre

### Sección En LabSim

LabSim tiene pacientes pediátricos que llegan con un acompañante. La entrevista se le hace al adulto en la conversación: en el caso de Benjamín (★, 5 años), su mamá. Ahí se practica lo que más pesa en un niño: preguntar por el embarazo, el tamizaje, el desarrollo y cómo responde en la casa, antes de decidir la batería.

- El audiómetro tiene **FM** y **NBN**, los estímulos del campo libre.
- **C. libre** y **Simultáneo** aparecen en gris: el campo libre todavía no se practica.
- Las pruebas objetivas sí están: impedanciometría (→ H7), emisiones (→ H9) y PEAT (→ H10). Con ellas se hace la prueba cruzada de un niño.

:::comentario Lo que el simulador no tiene
El niño de LabSim responde al audiómetro como un adulto colaborador: levanta la mano en su umbral, sin juego, sin habituarse y sin respuestas falsas, tenga la edad que tenga. No hay observación conductual, ni refuerzo visual, ni canasta, ni audífonos. Si atiendes en el simulador a un niño más chico que Benjamín, recuerda que en la vida real **no te daría ese audiograma**: elige el método por su edad de desarrollo y piensa qué resultados podrías obtener de verdad.
:::


## H09-emisiones-otoacusticas

### Sección En LabSim

El emisor otoacústico (**EOAS**) tiene una pestaña por prueba: **TEOAE**, **DPOAE**, **SOAE**, **SFOAE** e **Informe**. Todas se usan igual: eliges el oído y los parámetros, aprietas **Iniciar**, el equipo chequea la sonda y registra, y al final muestra el resultado. En **Informe** escribes la descripción y la conclusión; las pruebas capturadas se adjuntan solas.

- Las emisiones siguen la **cóclea del paciente**: se achican con un daño de las células ciliadas externas, se apagan con una pérdida de transmisión (porque el sonido cruza el oído medio de ida y de vuelta) y **se conservan en una pérdida neural**, aunque el umbral esté elevado.
- El **sello de la sonda** y el **ruido del paciente** los fija el caso. Con un sello flojo, el estímulo y la emisión bajan; con un paciente inquieto, sube el piso de ruido. En los dos casos puede referir con una cóclea sana.
- En el **recién nacido**, mientras menos horas de vida, más probable es que la TEOAE refiera, con las tasas de la bibliografía.
- Las **SOAE** aparecen en cerca de la mitad de los oídos normales, por sorteo. Si el docente necesita un resultado fijo, las deja **presentes** o **ausentes** y puede cargar los picos a mano.

:::comentario Lo que el simulador no tiene
La TEOAE no tiene modo lineal o no lineal, y el tamaño de la emisión no depende del nivel del click (viene en 60 dB SPL; súbelo al del protocolo igual). Tampoco hay rechazo de barridos: el ruido se ve en la reproducibilidad y el piso. La supresión contralateral no está simulada.
:::

Pacientes de práctica (★): Tomás, Hernán, Benjamín y Valentina. A Benjamín, mídele antes el timpanograma; a Valentina, después el ABR.


## H10-potenciales-evocados-auditivos-de-tronco

### Recuadro o figura

:::ojo Barridos y umbral
En LabSim el umbral de cada caso está definido **con 2.000 barridos**. Si promedias menos, la respuesta cerca del umbral no alcanza a salir del ruido: **cada vez que partes los barridos a la mitad, el umbral que encuentras sube unos 6 dB** (así lo modela el simulador; el ruido residual, en cambio, sube solo 3 dB al partir los barridos a la mitad: → B4). Si promedias más, puedes encontrar respuesta algo por debajo del umbral del caso, y eso también es correcto: es lo que pasa en la clínica.
:::

### Recuadro o figura

:::comentario Por qué 55 dB en LabSim
El tope del vibrador no es un error del simulador: es el límite físico del transductor. La revisión de Seo y cols. (2018) lo ubica entre 45 y 55 dB nHL según el equipo, y hay series normativas que solo miden hasta 50 dB nHL porque su vibrador no entrega más. LabSim toma el extremo alto, 55 dB nHL. Si tu equipo llega solo a 45 o 50, la ventana útil de la vía ósea es todavía más angosta: un ABR óseo "sin respuesta" a su tope no es lo mismo que una cóclea sin función.
:::

### Sección En LabSim

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


## H11-electrococleografia

### Sección En LabSim

La ECochG de LabSim se maneja como un equipo real, y por eso se puede equivocar como uno real.

- **Está dentro del PEAT**, en el combo *Prueba*. Cada prueba es un registro aparte: cambiar de una a otra no borra nada, y las dos se guardan, cada una con su informe (el PEAT y la ECochG).
- **El equipo no viene configurado.** La tasa y las promediaciones arrancan al azar, y dejar bien el estímulo, la polaridad, el nivel, los filtros y la ventana es parte del examen. Quien enseña con LabSim encuentra el equipo ya en el estándar al elegir *ECochG*; el alumno no.
- **El paciente responde según su caso.** Su ECochG sale del perfil que se le asignó: un Ménière típico trae el PS agrandado y la cola prolongada en el oído enfermo. Los casos de Ménière de LabSim muestran siempre el hidrops **alterado**: el que tiene la ECochG normal, que existe en la clínica, se arma a mano.
- **Los errores se pueden cometer**: el pasa-alto del PEAT, el nivel bajo, la ventana corta, la polaridad equivocada, un montaje de PEAT con la prueba en ECochG.
- **La ficha del paciente** viene con las curvas y sus marcas, y el informe se sube como *electrococleografía*.
- **No hay glicerol**: los pacientes no cambian dentro de una atención.

Para practicar, el paciente de este capítulo está entre los de práctica (★): **Patricia**, la 38.


<!-- Pasada de fundamentos 2026-10-18: se resolvieron los cinco verificar que había aquí. (1) Hall 2007 se reemplazó por Simpson y cols. 2020 (texto completo). (2) Las "decenas de microvoltios" del transtimpánico se reemplazaron por la razón de 5 a 10 veces de Simpson y cols. 2020; la anestesia local se quitó. (3) Hornibrook 2017 describe el mecanismo del punto de trabajo (lo atribuye a Gibson 1978); Gibson y cols. 1977 queda solo para la relación PS grande-hidrops, que es lo que dice su abstract. (4) Simpson y cols. 2020, leído completo: el contacto y la colocación bajo visión cambian la amplitud del PA. (5) Ferraro 2010, abstract: el electrodo de conducto para mejorar el PEAT del recién nacido; se quitó "por su comodidad". -->


## H12-vemp

### Sección En LabSim

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


## H13-potenciales-de-estado-estable

### Sección En LabSim

**LabSim no simula el ASSR.** El combo de pruebas de la ventana del ABR nombra el ASSR junto con otros potenciales que se planean, pero está **deshabilitado**: no genera una respuesta y no se puede registrar. Lo que aquí se describe lo vas a ver recién en un equipo real.

Lo que sí practica LabSim y que sirve directamente para este examen:

- **El mismo montaje y la misma preparación**: otoscopía, anamnesis de electrofisiología, limpieza de la piel, electrodos en el vértex y las mastoides, impedancias bajas y parecidas, y el EEG en vivo como termómetro de la calidad del registro (→ H10).
- **El umbral por frecuencia con el ABR por tono breve y *chirp* de banda estrecha**, con su corrección de dB nHL a dB eHL (→ H10, "Umbral por frecuencia"): es el mismo razonamiento de "el examen sobreestima el umbral y se corrige en promedio", con otras cifras.
- **Los criterios de parada**: el FSP y el ruido residual del ABR son el equivalente de la confianza estadística y del ruido residual del ASSR (→ H10).
- **El control con estímulo bloqueado**: pinzar el tubo, en el ABR.
- **Casos para comparar**: Hernán (pérdida coclear de agudos) y Tomás (audición normal) del capítulo del ABR permiten hacer el ejercicio de pasar de un umbral por frecuencia a un audiograma estimado.

:::comentario Lo que el simulador no tiene
No hay sueño que conseguir, ni modulación, ni análisis en frecuencia, ni la estrategia de niveles de un equipo real; tampoco el aviso de "no concluyente". Y sin ASSR, LabSim no puede mostrar lo más característico del examen: **ocho umbrales apareciendo a la vez**.
:::


## H14-potenciales-de-latencia-media-y-tardia

### Sección En LabSim

**LabSim no simula la latencia media, los corticales, la MMN ni la P300.** El selector de pruebas de la ventana del ABR nombra varios de estos potenciales entre los que se planean, pero no se pueden registrar: no generan respuesta. Lo que aquí se describe lo vas a ver recién en un equipo real.

Sí practica LabSim cosas que sirven de base para estas respuestas: la otoscopía previa, la preparación de la piel y el montaje de electrodos, las impedancias bajas y parejas, y el EEG en vivo como termómetro del estado del paciente y del ruido (→ H10).

:::comentario Lo que el simulador no tiene
No hay paradigmas con estímulos estándar y desviante, ni tareas que el paciente deba cumplir, ni cambios de la respuesta con el sueño, la atención o la edad. Tampoco hay niños ni lactantes cuya respuesta madure.
:::


## H15-procesamiento-auditivo-central

### Sección En LabSim

**LabSim no tiene módulo de procesamiento central**: no hay pacientes simulados con rendimiento alterado en gaps, patrones o dígitos dicóticos, ni pruebas centrales dentro del simulador. Lo que sí hace LabSim es la parte **periférica** que esta herramienta exige primero: audiometría tonal (→ H3), logoaudiometría (→ H5), impedanciometría (→ H7), emisiones (→ H9) y PEAT (→ H10).


## H21-prueba-de-audifonos

### Sección En LabSim

LabSim **no tiene un módulo de audífonos**: no hay software de adaptación, ni interfaz, ni audífono de prueba, ni cuestionarios. Lo que sí hay en el simulador sirve para practicar **las partes de esta herramienta que no son el audífono**:

- La **otoscopía** y el lavado del conducto (→ H1).
- La **logoaudiometría**, con listas de bisílabos, para el porcentaje de discriminación, y el **LDL** para el umbral de molestia (→ H5).
- La **conversación con el paciente**: la anamnesis de la prueba, qué le cuesta, qué espera, qué piensa de los audífonos.

La figura de campo libre con audífono del caso parte de los umbrales del paciente con una **ganancia de ejemplo**, no una que el simulador mida: el campo libre todavía no se practica en el audiómetro, y el audífono no existe.

:::comentario Lo que el simulador no tiene
El paciente de LabSim no usa un audífono ni responde con uno: el audiograma que ves es siempre sin amplificación. La curva con audífono de la figura sale de restar a los umbrales del paciente una ganancia de ejemplo, que **no es una prescripción**. Para una adaptación real hay que usar el programa del fabricante, los objetivos de un método prescriptivo y la medición en oído real.
:::

El paciente de este capítulo (★, el 36 de la práctica) llega diciendo que oye bien y que la gente "habla para adentro". Lo que se aprende con él es la **candidatura**: oye casi normal los graves y pierde los agudos, no quiere audífonos "porque son para viejos", y hay una esposa que lo trajo. Antes de hablar de modelos, hay que escuchar qué le cuesta y qué le gustaría poder hacer.


## H22-revision-y-medicion-electroacustica-del-audifono

### Sección En LabSim

:::comentario Lo que el simulador no tiene
LabSim **no simula audífonos ni cámaras de medida**: no hay estetoclip, ni acoplador, ni analizador.
:::

Lo que sí puedes practicar en LabSim es lo que rodea a estas revisiones: la otoscopía previa (→ H1), la audiometría tonal y la logoaudiometría que dicen cuánta ganancia necesita el paciente (→ H3, H5) y la audiometría en campo libre, donde se compara al paciente con y sin audífono (→ H8, H21). La adaptación completa se trabaja en los capítulos 28 y 29 del libro.


## H23-acufeno-impacto-modelos-y-terapias-sonoras

### Sección En LabSim

LabSim no simula el manejo del acúfeno: no hay cuestionarios ni terapias sonoras en el simulador. Los casos pueden traer acúfeno en la anamnesis (→ H1), y la acufenometría con el audiómetro se explica en H6 (→ H6). Los esquemas de este capítulo son imágenes propias para estudiar el modelo y el flujo del manejo.


## H24-audiometria-ocupacional-y-vigilancia-del-ruido

### Sección En LabSim

LabSim tiene el **audiómetro** completo de H3 y los dos pacientes del capítulo 6 en la práctica libre: **Tomás (paciente 33)**, que es la audiometría de base ideal, y **Jorge (paciente 37)**, que tiene la muesca de veintidós años de chancador. La técnica se practica igual que en H3: el indicador de técnica revisa la instrucción, el oído de partida, el 10 abajo-5 arriba y los umbrales que coinciden con los del paciente.

**Lo que LabSim no tiene.** No simula el **reposo** ni el desplazamiento temporal: el paciente responde con su audición permanente, sin importar cuándo fue su última exposición. No mide el ruido de la sala ni el estado de calibración, y no guarda una audiometría **de base** para comparar con un control posterior: hay que llevar los números de una a la otra. Ni el protocolo de seguimiento ni los niveles de periodicidad están modelados. Lo que sí permite practicar es tomar umbrales **bien** en 3, 4 y 6 kHz y mirar la forma de un oído expuesto.


## H25-anamnesis-rinologica-y-rinoscopia

### Sección En LabSim

**LabSim no tiene simulador nasal.** No hay rinoscopio, ni nariz virtual, ni paciente con síntomas nasales, y por eso esta herramienta no tiene casos para atender. Lo que sí puedes practicar es la **conversación y la mano**, y para eso no hace falta un programa:

- **La anamnesis con un compañero.** Uno hace de paciente con un guion corto (por ejemplo, "obstrucción bilateral hace 3 años, usa un descongestionante, última dosis ayer") y el otro recorre la lista. Cambien de papel y de guion. La pregunta que casi todos olvidan es la del descongestionante.
- **La rinoscopía con un compañero**, con guantes y con el material de verdad, y con la supervisión del docente. Una persona sana ya tiene tabique, cornetes y ciclo nasal que mirar, y las dos fosas no se ven iguales.
- **Una lista de cotejo**, hecha por quien observa, con los ocho pasos de la rinoscopía y los ítems de la anamnesis. Es más útil que cualquier simulador para encontrar **dónde** te saltas algo.
- **La destreza del espéculo y la luz** se parece a la de la otoscopía de H1: luz en el eje de la mirada, mano apoyada en la cara del paciente, avisar antes de tocar. Si la dominas allí, esto sale más rápido.

:::comentario Lo que el simulador no tiene
LabSim no genera datos nasales, y lo que registra de la anamnesis auditiva no incluye los ítems rinológicos. Tampoco hay dibujo de la fosa, ni modelo de la mucosa. Lo que vimos aquí se aprende en el compañero y en el aula, con el docente al lado.
:::


## H28-olfatometria

### Sección En LabSim

LabSim no simula la olfatometría: no hay pantalla ni caso para este examen. Las figuras de este capítulo son esquemas propios, y la escalera de umbral se calculó con la regla de la propia prueba.


## H29-prick-test

### Sección En LabSim

LabSim no simula el prick test: no hay pantalla ni tutorial para este examen. Las figuras de este capítulo son esquemas propios para practicar la lectura de la pápula y la hoja de registro.


## H30-espirometria

### Sección En LabSim

LabSim no simula la espirometría: no hay pantalla ni tutorial para este examen. Las figuras de este capítulo son esquemas propios, calculados con un modelo sencillo, para practicar la lectura de las curvas.


## H31-polisomnografia-y-poligrafia-respiratoria

### Sección En LabSim

LabSim no simula polisomnografías ni poligrafías: no hay pantalla ni tutorial para este examen. Las figuras de este capítulo son esquemas propios, calculados con un modelo sencillo, para practicar la lectura de los trazos y del informe.


## H32-cpap-y-dispositivos-de-avance-mandibular

### Sección En LabSim

LabSim no simula este tratamiento: no hay pantalla de equipo, descarga ni titulación. Las figuras de este capítulo son esquemas propios, con datos de ejemplo, para practicar la lectura de una titulación y de una descarga.


## H11-electrococleografia (frases sueltas)

- "En este libro se usa el estándar de la tabla, con el que están calculados los límites de LabSim."
- "LabSim aplica el mismo límite de razón de áreas a los tres electrodos" (la razón de áreas de 1,94 se publicó con electrodo timpánico; Devaiah y cols., 2003).
