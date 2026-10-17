# H11. Electrococleografía

:::objetivos En esta herramienta
- Distinguir en un trazo la microfónica coclear, el potencial de sumación (PS) y el potencial de acción (PA), y explicar de dónde sale cada uno.
- Explicar por qué un hidrops endolinfático agranda el PS y por qué el límite normal cambia según la distancia del electrodo a la cóclea.
- Elegir electrodo, estímulo, polaridad, filtros, ventana, tasa y número de barridos sabiendo para qué sirve cada parámetro.
- Marcar BL, PS, PA, inicio y retorno, y calcular la razón de amplitudes, la razón de áreas y la diferencia de latencia entre rarefacción y condensación.
- Leer el resultado contra el límite del electrodo que se usó, informarlo sin ponerle nombre de enfermedad y saber qué no descarta.
- Reconocer los errores de configuración y los artefactos que borran el PS o lo inventan.
:::

La electrococleografía (ECochG o ECoG) registra la respuesta eléctrica de la **cóclea** y de la porción más distal del **nervio auditivo** en los primeros milisegundos después de un sonido. Es un potencial evocado como el PEAT (→ H10), con una diferencia que lo cambia todo: el electrodo activo **no está en el vértex, sino dentro del oído**, a centímetros o a milímetros de la cóclea. Eso hace que la respuesta sea grande, de microvoltios, y que lo que se ve no sea una serie de ondas del tronco sino los potenciales del propio órgano de Corti.

La técnica nació como una forma de medir el umbral auditivo de manera objetiva (Eggermont, citado por Hornibrook, 2017). Hoy su uso clínico más frecuente es otro: buscar la huella eléctrica del **hidrops endolinfático** (→ cap. 9).

## Para qué sirve

La ECochG responde, sobre todo, una pregunta:

- **¿La cóclea de este oído tiene un potencial de sumación desproporcionado para su potencial de acción?** Una razón PS/PA alta apoya el diagnóstico de hidrops endolinfático, la lesión de la enfermedad de Ménière (Coats, 1981; Ferraro y Durrant, 2006). Se pide, junto con la audiometría, el reclutamiento y el VEMP cervical (→ H12), cuando hay crisis de vértigo con plenitud y acúfeno, o una pérdida que fluctúa.

También ayuda a ubicar **dónde** falla una respuesta ausente: una microfónica presente con un PA ausente o desorganizado apunta a la sincronía del nervio y no a las células ciliadas (→ H10 y cap. 13). Se usa además en el monitoreo durante cirugías del oído y en el estudio de pacientes con implante coclear (Hall, 2007), cosas que LabSim no practica.

Hay que tener claros sus límites desde el principio:

- **Normal no descarta.** Entre un cuarto y la mitad de los pacientes con Ménière tienen una ECochG normal (Lamounier y cols., 2014). Un registro alterado apoya el hidrops; uno normal no lo descarta.
- **No es una audiometría.** Mide qué hace la cóclea con un estímulo fuerte, no hasta dónde oye la persona.
- **Una razón alta no se lee sola.** Se lee con la historia, el audiograma, el reclutamiento y, si se pidió, el VEMP.
- **Es un examen de un momento.** El hidrops fluctúa, y la ECochG, que mide un oído un día determinado, también. La variabilidad de un mismo oído, medido semana a semana, existe (Roland y cols., 1993).

## Fundamento

### Tres potenciales en un trazo

Cuando llega un click a la cóclea, el electrodo del oído recoge la suma de tres señales que nacen en lugares distintos y se distinguen porque **se comportan distinto** (Ferraro y Durrant, 2006):

:::imagen ilustraciones/h11-componentes.svg ancho=100% Lo que registra el electrodo del oído con un click (izquierda) y los tres potenciales que lo forman (derecha). Fíjate en cómo se distinguen: la MC se invierte con la polaridad, el PS es un desplazamiento lento que no se invierte y el PA es la descarga del nervio. La razón PS/PA se calcula con las dos amplitudes medidas desde la línea de base.
:::

- **Microfónica coclear (MC).** Es una oscilación eléctrica que **copia la forma del sonido**: si el estímulo es un tono de 1 kHz, la MC es un tono de 1 kHz. Sale de las células ciliadas, sobre todo de las externas, cuando sus estereocilios se doblan y dejan entrar corriente (Dallos y Cheatham, 1976). No pasa por ninguna sinapsis, así que aparece apenas el sonido llega a la cóclea, y **se invierte cuando se invierte la polaridad del estímulo**: un click en rarefacción da una MC y uno en condensación da su imagen en espejo. Esa es su firma.
- **Potencial de sumación (PS).** Es un **desplazamiento lento de la línea de base** que dura mientras dura el estímulo. Tiene un origen mixto, en la respuesta no lineal de las células ciliadas (Dallos y cols., 1970; Durrant y cols., 1998). **No se invierte con la polaridad**, y por eso sobrevive cuando se alterna. Con un click se ve como un **hombro** en la bajada hacia el PA, porque es muy breve y se superpone con él; con un tone burst largo se ve como una **meseta**.
- **Potencial de acción (PA).** Es la suma de las descargas de miles de fibras del nervio auditivo al comienzo del estímulo: la misma **onda I del PEAT**, vista desde mucho más cerca (Ferraro y Durrant, 2006). Se ve como una espiga, y su pico negativo se llama **N1**. Después del N1 vienen una positividad y un segundo valle más chico, que el equipo usa para saber dónde termina el complejo.

La polaridad merece una advertencia. En el PEAT las ondas se dibujan hacia arriba porque el electrodo activo está en el vértex. En la ECochG el activo está en el oído y la negatividad del PA queda **hacia abajo**. No es un error del equipo: es el montaje (→ cap. 9). LabSim trae un botón para invertir el eje.

### Por qué el hidrops agranda el PS

En la cóclea sana, la membrana basilar vibra alrededor de una posición de reposo. La respuesta de las células ciliadas a ese movimiento **no es una recta**: tiene forma de S, casi lineal en el medio y aplanada en los extremos. Si el movimiento cae justo donde la curva es simétrica, lo que sube y lo que baja se compensan y el promedio casi no se mueve. Si el punto de trabajo está en una zona más curva, el movimiento hacia un lado produce más respuesta que el movimiento hacia el otro, y **el promedio se corre**: ese corrimiento, que no oscila, es un potencial continuo, el PS.

:::imagen ilustraciones/h11-sesgo.svg ancho=100% La misma vibración de la membrana con dos puntos de trabajo. La respuesta de la célula ciliada tiene forma de S: si la membrana vibra en el tramo del medio, el promedio queda casi en el reposo y el PS es chico; si el hidrops corre el punto de trabajo, el promedio se desplaza y el PS crece. Es la explicación más difundida, no un hecho demostrado.
:::

En el hidrops, la presión de la endolinfa **empuja la membrana basilar** hacia la rampa timpánica y desplaza su punto de trabajo. La misma vibración produce entonces un promedio más corrido: un PS más grande. Esta es la explicación más difundida (Gibson y cols., 1977) y se apoya en experimentos en los que una polarización continua de la partición coclear cambió el PS (Durrant y Dallos, 1972). La fisiopatología del hidrops en general se revisa en Salt y Plontke (2010). Es una **hipótesis de trabajo**, no una medición directa del desplazamiento en el paciente.

El hidrops hace dos cosas más en el trazo. El PS no solo sube: **se prolonga**, porque el desplazamiento de la membrana tarda más en volver a la base, y por eso la razón de **áreas** puede detectar oídos que la de amplitudes todavía llama normales (Devaiah y cols., 2003). Y el PA, que depende de que las fibras descarguen a la vez, no crece con él: queda proporcionalmente más chico.

¿Por qué se informa una **razón** y no la amplitud del PS? Porque las dos amplitudes dependen de lo mismo: la distancia al electrodo, el contacto, el nivel y la ganancia. Dividir una por otra cancela una buena parte de eso y deja lo que es propio de la cóclea.

### La distancia al electrodo

Cuanto más cerca de la cóclea, más grande es todo, y por eso la técnica se hace con electrodos dentro del oído. Un electrodo lejano da una respuesta de alrededor de **una cuarta parte** de la que da uno en contacto con la cóclea (Hornibrook, 2017).

:::imagen ilustraciones/h11-electrodos.svg ancho=100% Las tres posiciones del electrodo activo: conducto, tímpano y promontorio. Cuanto más cerca de la cóclea, más grande es la respuesta; las barras muestran el orden de magnitud, no la escala.
:::

Pero el electrodo no solo cambia el tamaño: cambia **la razón**. El PA es un campo cercano y muy sincronizado, que se atenúa rápido con la distancia; el PS, que suma la actividad de muchas células, se atenúa menos. Por eso la misma cóclea da razones **más altas** medidas desde el conducto que desde el promontorio, y el límite normal es distinto en cada posición. Comparar una razón con el límite de otro electrodo es el error más fácil de cometer (ver "Cómo se informa").

### Click y tone burst

El **click** es el estímulo de rutina: dura microsegundos, excita toda la cóclea a la vez y da un PA grande y bien definido. Su costo es que el PS dura apenas lo que dura el click y queda **pegado** al PA, como un hombro sin un punto exacto donde marcarlo.

El **tone burst** es un tono breve, de 1 kHz por ejemplo, con subida y bajada suaves. Con un burst largo, el PS es una **meseta que dura lo que dura el estímulo**, y el PA queda como una espiga al comienzo, montada encima. Las dos cosas se separan y el PS se puede medir en el medio de la meseta, donde no llega el PA. Ese es el argumento para usarlo, y varias series reportan una sensibilidad mayor con burst que con click (Ferraro y Durrant, 2006; Hornibrook, 2017). A cambio, un burst sincroniza peor el nervio y entrega un PA más chico, y la meseta es lenta: exige filtros y ventana distintos (ver los parámetros).

## Antes de empezar

### Equipo

- **Equipo de potenciales evocados**: el mismo del PEAT (→ H10), con su preamplificador y su promediador.
- **Electrodo de oído**, de uno de los tres tipos, con su gel o su pasta conductora.
- **Electrodos de superficie** para la referencia y la tierra, gel abrasivo, alcohol, algodón y cinta.
- **Fonos de inserción** (o el tubo del propio electrodo de conducto) para entregar el estímulo.
- **Otoscopio**, para ver el conducto antes y para poner el electrodo del tímpano.
- Una **silla o camilla** cómoda. A diferencia del PEAT, aquí el paciente puede estar despierto.

### Conoce tu equipo: la ECochG de LabSim

La ECochG de LabSim vive **dentro del equipo de PEAT**: en el combo **Prueba** se elige *ECochG*. El equipo cambia a un montaje de oído y la tabla de valores pasa a ser la del ECochG. La pantalla es la misma que la del PEAT (→ H10): parámetros a la izquierda, curvas de cada oído al centro, valores a la derecha y, abajo, lo que está pasando mientras registras.

:::imagen /docs/manual/img/estudiante/ecochg.png La ECochG de LabSim con el OI registrado y marcado
- @-2.5,8.4 | **Prueba: ECochG.** Cambia el montaje, la ventana y la tabla. Cambiar de prueba no borra el PEAT.
- @-2.5,14.5 | **Estímulo y polaridad.** *Click* o *Burst*. La alternada cancela la MC; para medir la diferencia rarefacción-condensación hacen falta dos curvas, una de cada polaridad.
- @-2.5,20 | **Intensidad**: 90 dB nHL. El PS se mide entero solo a nivel alto.
- @-2.5,26 | **Tasa**: 11,1 estímulos por segundo. Parte al azar: configurarla es parte del examen.
- @-2.5,32 | **Pasa alto** en 5 Hz. Con el del PEAT (100 Hz) el PS se achica.
- @-2.5,38 | **Promediación**: 1.500 barridos, que también parte al azar.
- @72,0.8 | **Línea de estado**: nivel, barridos, aceptados, FSP, ruido residual y el rechazo de artefactos.
- @17.4,25.9 | El botón **↕** invierte el eje: con él ves el PA hacia arriba, como en el PEAT.
- @57,51 | El **PS** y el **PA** marcados sobre el trazo del OI. El PA va hacia abajo.
- @66,34 | La **línea de base** punteada, desde la marca BL.
- @102,34 | Las marcas: **BL**, **Ini**, **PS**, **PA**, **Fin** y **MC**. **Auto** marca la curva elegida, pero la marca se revisa.
- @102,40 | **Amplitud del PS y del PA**, medidas desde la línea de base.
- @102,46 | **Razón PS/PA** (0,562, sobre el 0,40 del electrodo timpánico) y **razón de áreas**, que se calcula cuando están el inicio y el retorno.
- @102,52 | **Ancho del PA** y **duración del complejo**.
- @102,56.5 | **Δ latencia por tasa**: necesita dos curvas del mismo oído a distinta tasa.
:::

El electrodo, la ventana, la ganancia y las posiciones de la referencia y la tierra se eligen en *Archivo → Parámetros avanzados*, pestaña *Registro* (→ H10). Ahí el **montaje** ofrece tres opciones de ECochG: *Conducto / TipTrode*, *Timpánico* y *Transtimpánico / promontorio*. Si dejas un montaje de PEAT (Cz-mastoides) con la prueba en ECochG, el equipo registra un PEAT con otro nombre: no hay electrodo en el oído y el trazo sale sin PS.

### Preparar al paciente

El paciente **no necesita dormir**, pero sí estar **quieto y relajado**: el músculo del cuello, la mandíbula y el parpadeo ensucian el registro, que es mucho más lento que el del PEAT. Se le pide que no hable, que no trague ni apriete los dientes durante las curvas, y que relaje la mandíbula.

Antes de poner el electrodo:

1. **Otoscopía** (→ H1). Un tapón de cerumen aleja el electrodo de la cóclea, y una perforación, una otorrea o una inflamación del conducto cambian lo que se puede apoyar: en esos casos se consulta al médico antes de seguir.
2. **Revisa el audiograma**. El PS solo se mide entero con la cóclea bien empujada. Si el oído tiene una pérdida marcada, a 90 dB nHL el nivel sobre el umbral es poco y la razón sale chica, aunque haya hidrops (ver "Errores frecuentes").
3. **Explica el examen.** Un electrodo apoyado en el tímpano da sensación de cuerpo extraño y a veces de presión, y el click a 90 dB nHL es fuerte. Se le dice que dura unos minutos por oído y que si molesta, se detiene.
4. **Pregunta por el momento de las crisis.** Un oído en un buen día puede dar una ECochG normal (→ cap. 9). Anota cuándo fue la última crisis.

### Los tres electrodos

El electrodo activo se pone en el **oído que se estudia**. Hay tres posiciones, de la más lejana a la más cercana a la cóclea:

- **De conducto (TIPtrode).** Un tapón de espuma con una lámina de oro, que se inserta en el conducto como un fono de inserción y por cuyo centro llega el sonido (Roland y cols., 1993). Es el más **cómodo**, no necesita colocarse sobre el tímpano y lo puede poner cualquier examinador entrenado. Es el que da la respuesta más chica, y obliga a promediar más.
- **Timpánico.** Un electrodo blando, de punta de plata o de mecha húmeda, que se apoya **sobre la membrana timpánica** bajo visión otoscópica. Da un PA de unos pocos microvoltios y es el que se usa en este libro. Un contacto malo se nota en el trazo: el PA sale chico y el ruido sube (Simpson y cols., 2020).
- **Transtimpánico.** Una aguja que atraviesa el tímpano y se apoya en el **promontorio**. Da el registro más grande, decenas de microvoltios (Ge y Shea, 2002), pero lo coloca un médico, con anestesia local, y es el más invasivo.

:::comentario Lo que dicen las normas
En la literatura, "extratimpánico" suele agrupar todo lo que no atraviesa el tímpano: el electrodo sobre la membrana y el de conducto, que dan respuestas distintas. Aquí se separan en tres porque la razón normal cambia con cada uno. La separación entre el tímpano y el conducto no es unánime: algunos trabajos los juntan (Wuyts y cols., 1997), y hay quienes recomiendan el de conducto para el PEAT del recién nacido por su comodidad (Ferraro, 2010). El valor que se use tiene que corresponder al electrodo con el que se midió.
:::

### Montaje

Con el paciente sentado o semirrecostado:

1. **Limpia la piel** con alcohol y gel abrasivo en los puntos de superficie, como en el PEAT (→ H10).
2. **Pon la referencia y la tierra.** La tierra va en la frente (Fpz en LabSim) y la referencia en el mastoides o en el lóbulo. En LabSim las posiciones de referencia son A1 (izquierda) y A2 (derecha) y se eligen en los parámetros avanzados.
3. **Coloca el electrodo de oído.** Con el de conducto, el tapón se comprime entre los dedos, se inserta y se deja expandir, de modo que selle; el gel va sobre la lámina de oro. Con el timpánico, bajo el otoscopio, la punta, humedecida con solución salina o gel, se lleva hasta apoyarla suavemente sobre la membrana.
4. **Revisa las impedancias**: bajas y parecidas entre sí, como en el PEAT. Una impedancia alta en el electrodo de oído se paga en ruido y en un PA chico.
5. **Pon el fono de inserción** (si el electrodo no lleva el tubo) y comprueba que el estímulo llega.
6. **Mira el EEG antes de promediar.** Tiene que estar tranquilo, sin saltos de movimiento ni onda regular de la red eléctrica.

### Los parámetros de rutina

:::ayuda-ancho Configuración de la ECochG con electrodo timpánico
| Parámetro | Valor de rutina | Por qué |
|---|---|---|
| Estímulo | Click (o tone burst) | El click da el PA más grande; el burst separa el PS del PA |
| Polaridad | Alternada | Cancela la MC y deja ver el PS y el PA; las dos polaridades por separado, solo para la diferencia R/C |
| Intensidad | 90 dB nHL | El PS solo se mide entero con la cóclea bien empujada |
| Tasa | 11,1 estímulos/s | La respuesta es grande y no hace falta ir rápido; el decimal evita la fase con la red eléctrica |
| Filtros | 5 a 3.000 Hz | El PS es un desplazamiento casi continuo: un pasa-alto alto se lo come |
| Ventana | 10 ms (20 ms con burst) | El complejo vuelve a la base tarde en el hidrops; la meseta del burst dura 12 ms |
| Barridos | 1.500 por curva | Con el electrodo cerca de la cóclea la respuesta es grande y bastan menos que en el PEAT |
| Ganancia | 100.000 | La señal es mayor que la del PEAT |
:::

Cada parámetro tiene su razón, y se puede cometer el error de olvidarla:

1. **El pasa-alto va muy bajo.** Un pasa-alto de 100 Hz, el del PEAT, deja pasar la espiga del PA pero se come el PS: en LabSim un oído con una razón de 0,55 se mide en 0,38 con el filtro en 100 Hz y 0,08 en 200 Hz. El hidrops desaparece por el filtro, no por el oído.
2. **El nivel va alto.** El PA aparece desde cerca del umbral, pero el PS necesita nivel para hacerse medible. Una razón medida a nivel bajo sale chica aunque haya hidrops, y el equipo no avisa.
3. **La polaridad va alternada.** La MC, que se invierte con la polaridad, se cancela al alternar y deja el PS y el PA limpios. En una sola polaridad la MC se suma al PS y al PA y corre sus picos.
4. **La ventana va en 10 ms con click.** La razón de áreas se integra hasta que el complejo vuelve a la línea de base, y en un hidrops marcado eso ocurre bien después de los 5 ms. Con burst largo hace falta abrirla a 20 ms.
5. **La tasa baja y los barridos son menos.** Con 11,1 por segundo, 1.500 barridos toman algo más de dos minutos por curva.

:::comentario Lo que dicen las normas
No hay un protocolo único de ECochG. Las revisiones describen ajustes distintos de filtros, tasa, nivel y número de promediaciones, con estímulos de click o de tone burst y con distintas polaridades (Wuyts y cols., 1997; Ferraro y Durrant, 2006; Simpson y cols., 2020). Margolis y cols. (1995) registraron en condensación, rarefacción y alternado, y recomendaron mirar la diferencia entre polaridades; en la serie de Satar y cols. (2003) esa diferencia no mejoró el diagnóstico. En este libro se usa el estándar de la tabla, con el que están calculados los límites de LabSim.
:::

## Paso a paso

### 1. Configura el equipo antes de registrar

Elige la prueba **ECochG**, el montaje del electrodo que pusiste y, uno por uno, estímulo, polaridad, nivel, tasa, filtros, ventana y promediación. Nada en la pantalla te avisa si algo quedó mal: lo ves después, en el trazo. Revisa primero los dos filtros y la ventana.

### 2. Registra el primer oído a 90 dB nHL

Con el paciente quieto, apreta **Iniciar**. Mira el EEG mientras se llena la curva y la línea de estado: el **FSP** y el **ruido residual** (→ H10) te dicen cuándo la respuesta salió del ruido. Con 1.500 barridos el complejo es claro. **Repite la curva**, o mira los subpromedios A y B (botón **AB**): una respuesta real está en las dos mitades.

### 3. Marca el complejo

La ECochG se marca como el PEAT: eliges la curva con un clic en su etiqueta, mueves la bandera **A** y pulsas el botón de la marca en la tabla. Las marcas son seis:

- **BL**, la **línea de base**: un punto donde el trazo todavía no despega, antes de que llegue la respuesta. De ahí se miden las dos amplitudes.
- **Ini**, el **inicio** del complejo: donde el trazo se separa de la base. Lo usa la razón de áreas.
- **PS**, el potencial de sumación: en el **hombro** de la bajada hacia el PA. Con click no tiene un punto exacto, porque el PS y el PA se superponen; por eso conviene mirar las dos razones juntas.
- **PA**, el potencial de acción: en el **fondo del valle**.
- **Fin**, el **retorno** a la línea de base, después del N1. Lo usa la razón de áreas.
- **MC**, la microfónica, sobre la oscilación que sigue la forma del click (solo se ve bien en una sola polaridad).

Las amplitudes del PS y del PA se miden **desde la línea de base**. **Auto** marca todo menos la MC, apoyada en el trazo y no en el caso: si el filtro o el nivel están mal, marca igual y la medida sale mal. Revisa siempre lo que puso.

### 4. Lee las dos razones

La tabla calcula dos números:

- La **razón de amplitudes PS/PA**: la altura del PS dividida por la del PA, desde la base.
- La **razón de áreas**: el área del complejo entero (desde el inicio hasta el retorno) contra el área del PA (desde el inicio del N1 hasta el primer pico positivo que le sigue). Recoge que, en el hidrops, el PS no solo sube sino que se prolonga (Devaiah y cols., 2003).

Lo que sale del límite del electrodo se pinta en rojo. Compara con los límites de "Cómo se informa".

### 5. Si pide la diferencia rarefacción-condensación

Registra una curva en **rarefacción** y otra en **condensación**, al mismo nivel, estímulo y oído. La tabla compara el PA de las dos y mide cuánto se corre una respecto de la otra. Es una medida de **separación**, que se informa en valor absoluto: LabSim toma 0,38 ms como límite (Satar y cols., 2003).

### 6. Con tone burst: el PS en la meseta

Si cambias a *Burst* en el estímulo, cambia lo que mides. En los parámetros avanzados, elige la envolvente **1 ms - 10 ms - 1 ms** y abre la ventana a **20 ms**: con 10 la meseta no entra entera. Cuida el pasa-alto: con un filtro de primer orden, a 5 Hz la meseta de 12 ms pierde cerca de un tercio de su altura hacia el final, con 10 Hz pierde más de la mitad, y con 100 Hz desaparece.

:::imagen ilustraciones/h11-burst-filtro.svg ancho=100% El PS con click y con tone burst, y lo que le hace el pasa-alto. Con click, el PS es apenas un hombro antes del PA; con un burst de 1-10-1 ms es una meseta que dura lo que dura el estímulo. Un pasa-alto de 5 Hz la deja casi entera; uno de 100 Hz, el del PEAT, la borra.
:::

El PS se mide **en la mitad de la meseta**, donde ya no llega la espiga del PA, y el retorno se busca después. Con burst, el PA es mucho más chico que con click, y la razón de un oído sano sale muy por encima de los límites publicados, que son de click. Por eso LabSim, con burst, mide las razones pero **no las pinta en rojo**: no tienen un límite que aplicarles.

### 7. El otro oído, y la tasa

Repite en el otro oído: sirve de **referencia dentro del mismo paciente** y de control de que el equipo está bien configurado. Si el examen pide la medida de tasa, registra una segunda curva del mismo oído a una tasa mucho más alta (por ejemplo, 91 por segundo): la tabla calcula cuánto se corre el PA entre las dos. El límite que usa LabSim, 0,20 ms, sale del modelo y no de una serie publicada.

<!-- verificar: el corrimiento del PA por tasa (11,1 a 91/s, límite 0,20 ms) es "calculado" en EcochgReferences.php: sin cita primaria. Se dejó con la advertencia en el texto. -->

### 8. Si el médico pide un control con glicerol

El glicerol por boca saca agua del oído interno y, en un oído con hidrops, puede **achicar el PS negativo** (Moffat y cols., 1978, con electrodo transtimpánico en 13 pacientes). Por eso a veces se pide una ECochG antes y después de la toma. El procedimiento del glicerol está en el cap. 9. LabSim no lo hace: sus pacientes no cambian dentro de una atención.

:::ayuda Ayuda memoria
- Electrodo **timpánico** en el oído estudiado; tierra en la frente; impedancias bajas y parecidas.
- Click **alternado**, **90 dB nHL**, **11,1/s**, **5 a 3.000 Hz**, ventana de **10 ms**, **1.500** barridos.
- Con burst: **1 ms - 10 ms - 1 ms**, ventana de **20 ms**, el PS en la mitad de la meseta.
- El PA va **hacia abajo**.
- Marca **BL, Ini, PS, PA, Fin**; las amplitudes se miden desde la base.
- Límites del timpánico: PS/PA **0,40** y áreas **1,94**. Otro electrodo, otro límite.
- Normal **no descarta**. Alterado, **apoya**.
:::

## Cómo se informa

### Qué se mide

- **Amplitud del PS y del PA**, en microvoltios, desde la línea de base.
- **Razón PS/PA** y **razón de áreas**, por oído.
- **Latencia del PA** (el N1): alrededor de 1,4 a 1,5 ms con click a 90 dB nHL en LabSim.
- **Ancho del PA** y **duración del complejo**: en los casos de hidrops de LabSim el PA sale más ancho y el complejo tarda más en volver a la base.
- **Diferencia de latencia del PA entre rarefacción y condensación**, si se registraron las dos.
- **Medida de tasa**, si se registró.
- **Morfología y replicabilidad**: si el complejo es claro y se repite.

### Contra qué se compara

El límite normal depende del **electrodo**. Estos son los de LabSim, con click alternado a 90 dB nHL:

Tabla: Límites de la ECochG con click, según el electrodo

| Electrodo | Razón PS/PA | Razón de áreas |
|---|---|---|
| Promontorio (transtimpánico) | 0,35 | 1,94 |
| Tímpano | **0,40** | **1,94** |
| Conducto (TIPtrode) | 0,50 | 1,94 |

Sobre el límite, la razón es compatible con hidrops. La separación del PA entre polaridades se considera alterada sobre **0,38 ms**. Los valores son los mismos del cap. 9, que además trae la discusión de cada uno (Margolis y cols., 1995; Roland y cols., 1993; Wuyts y cols., 1997; Devaiah y cols., 2003; Satar y cols., 2003). Los datos normativos completos por población están en el Apéndice A (→ Apéndice A).

:::comentario Lo que dicen las normas
Los límites cambian de una serie a otra. Con electrodo timpánico, Margolis y cols. (1995) fijaron el criterio para un 95 % de especificidad; Satar y cols. (2003), con 12 controles, llegaron a un límite más bajo, de 0,32. Con electrodo de conducto, 0,50 es el valor más alto observado en sanos (Roland y cols., 1993), no un corte estadístico. La razón de áreas (1,94) se publicó con electrodo timpánico (Devaiah y cols., 2003); con aguja en el promontorio no fue más sensible que la de amplitudes (Baba y cols., 2009), y LabSim aplica el mismo límite a los tres electrodos. Cada centro debería construir los suyos, con su equipo y su electrodo.
:::

### Un caso: Patricia

Patricia (paciente de práctica 38) tiene 46 años y una historia de Ménière del oído izquierdo: crisis de vértigo de horas, plenitud y zumbido grave antes de cada una, y una audición que fluctúa. Su ECochG se registró con electrodo timpánico, click alternado a 90 dB nHL, 5 a 3.000 Hz y ventana de 10 ms. El OD es la referencia.

{{caso h11_p38}}

:::figura h11_p38 ecochg
- @OD PA | El OD tiene un PA profundo y un PS chico: razón **0,31**, bajo el 0,40 del electrodo timpánico, y razón de áreas **1,19**, bajo 1,94. La latencia del PA es de 1,37 ms.
- @OD PS | El PS del OD es el hombro de la bajada hacia el PA, y mide menos de un tercio de él.
- @OI PS | En el OI el PS es casi tan grande como el PA: razón **0,60**, sobre el límite.
- @OI PA | El PA del OI llega a 1,50 ms y es ancho. Después no vuelve a la base dentro de la figura: el retorno está a 7,3 ms. Esa cola es el PS prolongado, y lleva la razón de áreas a **3,61**.
- Mismo electrodo, mismo nivel y mismos filtros en los dos oídos: la diferencia es del oído.
:::

### Un ejemplo de informe

El informe describe las condiciones, luego cada oído, y recién al final la conclusión. No interpreta más de lo que mide.

> **Electrococleografía.** Electrodo timpánico, click alternado a 90 dB nHL, 11,1 estímulos/s, filtros 5 a 3.000 Hz, ventana de 10 ms, 1.500 barridos por curva.
>
> **OD**: complejo PS-PA de buena morfología y replicabilidad. Razón de amplitudes PS/PA 0,31 y razón de áreas 1,19, bajo los límites del electrodo (0,40 y 1,94). Latencia del PA 1,37 ms.
>
> **OI**: PA ensanchado, con PS prolongado que no vuelve a la línea de base dentro de la ventana de análisis. Razón de amplitudes PS/PA 0,60 y razón de áreas 3,61, sobre los límites. Latencia del PA 1,50 ms.
>
> **Conclusión**: razones PS/PA y de áreas aumentadas en el OI, hallazgo compatible con hidrops endolinfático de ese oído; OD sin alteraciones. Se sugiere correlacionar con la clínica y los demás exámenes.

La conclusión **no le pone nombre de enfermedad**: "compatible con hidrops endolinfático" es lo que el examen puede decir; "enfermedad de Ménière" es un diagnóstico clínico, del médico. Se anota qué exámenes se adjuntan, y si el registro se hizo con un estímulo o un electrodo distintos del estándar, se dice. Una ECochG **normal** se informa como normal, sin "descarta hidrops".

## Errores frecuentes

- **Registrar con los filtros del PEAT.** Con el pasa-alto en 100 Hz, el PS se achica y el hidrops desaparece del trazo. Es el error más caro: no avisa.
- **Medir a nivel bajo.** El PS necesita nivel. A 60 dB nHL la razón sale chica en un oído con hidrops, y nada lo avisa.
- **Comparar con el límite de otro electrodo.** Una razón de 0,45 es alterada con aguja en el promontorio (0,35) y con electrodo en el tímpano (0,40), pero es normal para el de conducto (0,50).
- **Ventana corta.** Con 6 ms, el retorno de un complejo prolongado se sale de la pantalla y la razón de áreas no se puede calcular; con burst, la meseta se corta.
- **Marcar el PS en cualquier parte.** Con click el hombro no tiene un punto único: el PS se marca en el mismo lugar en los dos oídos, y se mira junto a la razón de áreas.
- **Confiar en el marcado automático.** Marca bien si el registro está bien; si no, marca igual.
- **Un electrodo mal apoyado.** Una respuesta chica y ruidosa casi siempre es de contacto: se reacomoda y se vuelve a medir antes de informar una razón. Sin electrodo en el oído, el trazo es un PEAT.
- **Una sola curva.** Sin replicar, no se sabe si el PS es del oído o del ruido.
- **Leer una razón normal como "no es hidrops".** Una parte de los Ménière la tiene normal.

### Artefactos

:::ayuda-ancho Artefactos de la ECochG
| Artefacto | Cómo se ve | Cómo se reconoce o se resuelve |
|---|---|---|
| **Artefacto de estímulo** | Una deflexión grande al comienzo, que crece con el nivel | Polaridad alternada. Con fono de inserción, **pinzar el tubo**: el sonido deja de llegar y el artefacto sigue (BSA, 2019) |
| **Microfónica sin cancelar** | Oscilación sobre el PS y el PA, que corre los picos | En una sola polaridad se invierte al cambiar de signo; alternando se cancela |
| **Red eléctrica** | Una onda regular cada 20 ms (50 Hz) | Impedancias y tierra primero; el notch es el último recurso |
| **Movimiento, mandíbula, tragar** | Saltos de base y barridos rechazados; el promedio no avanza | Pedir quietud y relajar la mandíbula |
| **Electrodo suelto o sin contacto** | PA chico, ruido alto, curva que se mueve entre barridos | Reacomodar y repetir antes de informar |
| **Línea de base que deriva** | La base sube o baja y no hay dónde marcar BL | Un pasa-alto algo más alto (con la advertencia del PS) o repetir la curva |
:::

:::ojo Ojo clínico
Una razón PS/PA alta **apoya** el hidrops pero no lo prueba, y una normal **no lo descarta**. Antes de informar, pregúntate si **calza con lo demás**: con el audiograma (una pérdida coclear de graves, ascendente, fluctuante), con el reclutamiento y con la historia. Y si es normal en un paciente con la historia completa, no es una contradicción: puede estar en un buen día, o su cóclea puede no mostrarlo (→ cap. 9).
:::

## En LabSim

La ECochG de LabSim se maneja como un equipo real, y por eso se puede equivocar como uno real.

- **Está dentro del PEAT**, en el combo *Prueba*. Cada prueba es un registro aparte: cambiar de una a otra no borra nada, y las dos se guardan, cada una con su informe (el PEAT y la ECochG).
- **El equipo no viene configurado.** La tasa y las promediaciones arrancan al azar, y dejar bien el estímulo, la polaridad, el nivel, los filtros y la ventana es parte del examen. Quien enseña con LabSim encuentra el equipo ya en el estándar al elegir *ECochG*; el alumno no.
- **El paciente responde según su caso.** Su ECochG sale del perfil que se le asignó: un Ménière típico trae el PS agrandado y la cola prolongada en el oído enfermo. Los casos de Ménière de LabSim muestran siempre el hidrops **alterado**: el que tiene la ECochG normal, que existe en la clínica, se arma a mano.
- **Los errores se pueden cometer**: el pasa-alto del PEAT, el nivel bajo, la ventana corta, la polaridad equivocada, un montaje de PEAT con la prueba en ECochG.
- **La ficha del paciente** viene con las curvas y sus marcas, y el informe se sube como *electrococleografía*.
- **No hay glicerol**: los pacientes no cambian dentro de una atención.

Para practicar, el paciente de este capítulo está entre los de práctica (★): **Patricia**, la 38.

:::pregunta Preguntas para practicar
1. Registras la ECochG de un oído con historia de Ménière con el pasa-alto en 100 Hz y la razón PS/PA sale 0,30. ¿Qué harías antes de informarla como normal?
2. Una razón PS/PA de 0,45 con electrodo de conducto y la misma razón con electrodo en el tímpano, ¿se informan igual? ¿Por qué?
3. Una razón de áreas de 3,6 con una de amplitudes de 0,60, ¿qué te dice la de áreas que no te dice la de amplitudes?
4. ¿Por qué la ECochG se registra con polaridad alternada, y cuándo registrarías una sola?
5. Al pasar de click a tone burst de 12 ms, ¿qué dos parámetros tienes que cambiar y por qué?
6. Patricia tiene una razón de 0,60 en el OI y de 0,31 en el OD. Si le registraras el OI otra vez con 60 dB nHL, ¿qué esperarías? ¿Qué le dirías al médico si solo tuvieras ese registro?
7. Un paciente con la historia completa de Ménière tiene la ECochG normal. ¿Descarta eso el diagnóstico?
:::

<!-- verificar: (1) Hall 2007 como fuente del uso intraoperatorio y en implante coclear: no se consultó el libro. (2) Ge y Shea 2002 para "decenas de microvoltios" y la anestesia local del electrodo transtimpánico: no se leyó el original; el orden de magnitud sale del modelo de LabSim (PA ~1, ~3,5 y ~20 µV por electrodo). (3) Gibson 1977 como origen de la explicación del sesgo de la membrana: no se leyó el original; Hornibrook 2017 lo atribuye a Gibson solo para el hallazgo del PS agrandado. (4) Simpson 2020 sobre el contacto del electrodo: no se leyó el texto completo. (5) Ferraro 2010 sobre el electrodo de conducto en el recién nacido: solo se leyó el resumen. -->

## Referencias

### Técnica

1. Ferraro JA, Durrant JD. Electrocochleography in the evaluation of patients with Ménière's disease/endolymphatic hydrops. J Am Acad Audiol. 2006;17(1):45-68. doi:10.3766/jaaa.17.1.6
1. Ferraro JA. Electrocochleography: a review of recording approaches, clinical applications, and new findings in adults and children. J Am Acad Audiol. 2010;21(3):145-52. doi:10.3766/jaaa.21.3.2
1. Simpson MJ, Jennings SG, Margolis RH. Techniques for obtaining high-quality recordings in electrocochleography. Front Syst Neurosci. 2020;14:18. doi:10.3389/fnsys.2020.00018
1. Hall JW 3rd. New handbook of auditory evoked responses. Boston: Pearson; 2007.
1. Wuyts FL, Van de Heyning PH, Van Spaendonck MP, Molenberghs G. A review of electrocochleography: instrumentation settings and meta-analysis of criteria for diagnosis of endolymphatic hydrops. Acta Otolaryngol Suppl. 1997;526:14-20. doi:10.3109/00016489709124014
1. Ge X, Shea JJ Jr. Transtympanic electrocochleography: a 10-year experience. Otol Neurotol. 2002;23(5):799-805. doi:10.1097/00129492-200209000-00032
1. British Society of Audiology. Recommended procedure: cochlear microphonic testing (OD104-87). BSA; 2019. Disponible en: https://www.thebsa.org.uk/wp-content/uploads/2023/10/OD104-87-Recommended-Procedure-for-Cochlear-Microphonic-Testing.pdf

### Valores normales y diagnóstico

1. Margolis RH, Rieks D, Fournier EM, Levine SE. Tympanic electrocochleography for diagnosis of Menière's disease. Arch Otolaryngol Head Neck Surg. 1995;121(1):44-55. doi:10.1001/archotol.1995.01890010032007 PMID 7803022.
1. Devaiah AK, Dawson KL, Ferraro JA, Ator GA. Utility of area curve ratio electrocochleography in early Meniere disease. Arch Otolaryngol Head Neck Surg. 2003;129(5):547-551. doi:10.1001/archotol.129.5.547 PMID 12759268.
1. Satar B, Meteoğlu A, Yetişer S, Özkaptan Y. Endolenfatik hidropsta kulak zarından elektrokokleografi: klinik ve elektrofizyolojik ilişkinin araştırılması. Türkiye Klinikleri J ENT. 2003;3(1):30-39.
1. Roland PS, Rosenbloom J, Yellin W, Meyerhoff WL. Intrasubject test-retest variability in clinical electrocochleography. Laryngoscope. 1993;103(9):963-966. doi:10.1288/00005537-199309000-00004 PMID 8361316.
1. Baba A, Takasaki K, Tanaka F, Tsukasaki N, Kumagami H, Takahashi H. Amplitude and area ratios of summating potential/action potential (SP/AP) in Meniere's disease. Acta Otolaryngol. 2009;129(1):25-29. doi:10.1080/00016480701724888 PMID 19003588.
1. Lamounier P, Gobbo DA, de Souza TSA, de Oliveira CACP, Bahmad F Jr. Electrocochleography for Ménière's disease: is it reliable? Braz J Otorhinolaryngol. 2014;80(6):527-532. doi:10.1016/j.bjorl.2014.08.010
1. Hornibrook J. Tone burst electrocochleography for the diagnosis of clinically certain Meniere's disease. Front Neurosci. 2017;11:301. doi:10.3389/fnins.2017.00301
1. Coats AC. The summating potential and Meniere's disease: I. Summating potential amplitude in Meniere and non-Meniere ears. Arch Otolaryngol. 1981;107(4):199-208. doi:10.1001/archotol.1981.00790400001001
1. Moffat DA, Gibson WP, Ramsden RT, Morrison AW, Booth JB. Transtympanic electrocochleography during glycerol dehydration. Acta Otolaryngol. 1978;85(3-4):158-66. doi:10.3109/00016487809111922 PMID 636865.

### Fisiología

1. Dallos P, Schoeny ZG, Cheatham MA. Cochlear summating potentials: composition. Science. 1970;170(3958):641-4. doi:10.1126/science.170.3958.641
1. Dallos P, Cheatham MA. Production of cochlear potentials by inner and outer hair cells. J Acoust Soc Am. 1976;60(2):510-2. doi:10.1121/1.381086
1. Durrant JD, Wang J, Ding DL, Salvi RJ. Are inner or outer hair cells the source of summating potentials recorded from the round window? J Acoust Soc Am. 1998;104(1):370-7. doi:10.1121/1.423293
1. Durrant JD, Dallos P. Influence of direct-current polarization of the cochlear partition on the summating potentials. J Acoust Soc Am. 1972;52(2B):542-52. doi:10.1121/1.1913143
1. Gibson WPR, Moffat DA, Ramsden RT. Clinical electrocochleography in the diagnosis and management of Menière's disorder. Audiology. 1977;16(5):389-401. doi:10.3109/00206097709071852
1. Salt AN, Plontke SK. Endolymphatic hydrops: pathophysiology and experimental models. Otolaryngol Clin North Am. 2010;43(5):971-83. doi:10.1016/j.otc.2010.05.007
