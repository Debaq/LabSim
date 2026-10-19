# 9. Hidrops

:::objetivos En este capítulo
- Explicar qué es la endolinfa, cómo se genera el potencial endococlear y qué cambia en la cóclea cuando la rampa media se distiende.
- Reconocer la enfermedad de Ménière por su historia (crisis de vértigo, plenitud, acúfeno grave y audición que fluctúa) y por su audiograma ascendente.
- Leer una electrococleografía: el potencial de sumación, el potencial de acción, su razón de amplitudes y su razón de áreas, y saber qué cambia cada electrodo.
- Demostrar el reclutamiento con el Fowler, el SISI y el fenómeno de Metz, y elegir entre ellos según el oído contrario.
- Describir la prueba de glicerol y saber qué significa un resultado negativo.
- Reconocer el hidrops retardado: el oído que enferma años después de una sordera profunda.
:::

La paciente cuenta que de pronto todo empezó a girar, que vomitó durante horas y que, antes de la crisis, sintió el oído lleno, "como con agua", con un zumbido grave que subía. Al día siguiente estaba bien. Semanas después, otra vez. Entre crisis oye casi normal algunos días y mal otros. Es el **hidrops endolinfático**: la cóclea y el vestíbulo de ese oído tienen más endolinfa de la que deberían, y la audición sube y baja con ella. En la consulta no hay nada que ver: la otoscopía es normal y la paciente llega, casi siempre, entre dos crisis. Lo que el audiólogo puede aportar es mostrar **dónde** está la lesión, en la cóclea y con reclutamiento, y buscar la huella del exceso de líquido en el registro eléctrico de la cóclea: la electrococleografía.

## Técnica en foco

Este capítulo usa cuatro herramientas: la **electrococleografía** (→ H11), las **pruebas de reclutamiento** (→ H6), el **VEMP cervical** (→ H12) y la **prueba de glicerol**, que se describe aquí. La audiometría, la logoaudiometría y la impedanciometría son las de siempre (→ H3, H5, H7), con una diferencia: en un hidrops cada audiograma es una foto de un oído que cambia.

### La electrococleografía, en lo justo

La electrococleografía (ECochG) registra la respuesta eléctrica de la cóclea y del nervio en los primeros milisegundos después de un estímulo. Es un potencial evocado como el PEAT (→ H10), pero con el **electrodo activo dentro del oído**, lo más cerca posible de la cóclea. En el trazo se ven tres cosas (→ Fisiología):

- **Microfónica coclear (MC).** Una oscilación que copia la forma del estímulo y se invierte al invertir su polaridad.
- **Potencial de sumación (PS).** Un desplazamiento de la línea de base que dura lo que dura el estímulo. Con click se ve como un **hombro** en la bajada hacia el PA.
- **Potencial de acción (PA).** La descarga sincrónica de las fibras del nervio auditivo. Es la misma **onda I** del PEAT, vista de cerca.

En un hidrops el PS **crece** y el PA no. Lo que se informa es la proporción entre los dos:

- **Razón de amplitudes PS/PA.** La altura del PS dividida por la del PA, las dos medidas desde la línea de base.
- **Razón de áreas PS/PA.** El área de todo el complejo, desde que se despega de la línea de base hasta que vuelve a ella, dividida por el área del PA (Devaiah y cols., 2003). Recoge además que, en el hidrops, el PS se **prolonga**: el complejo tarda más en volver a la base.
- **Diferencia de latencia del PA entre rarefacción y condensación.** Se registra una curva con cada polaridad y se mide cuánto se corre el PA de una a otra (Margolis y cols., 1995).

#### El electrodo

Cuanto más cerca de la cóclea, más grande la respuesta y menos promedios hacen falta. Hay tres posiciones:

- **Transtimpánico**: una aguja que atraviesa el tímpano y se apoya en el promontorio. Es el registro más grande, pero lo coloca un médico.
- **Timpánico**: un electrodo blando que se apoya sobre la membrana timpánica. Da un PA de unos pocos microvoltios y es el que se usa en este libro.
- **De conducto** (TIPtrode): un tapón con lámina conductora en el conducto. Es el más cómodo y el que da la respuesta más chica.

El electrodo cambia también el **límite normal** de la razón, porque cambia cuánto PS se capta respecto del PA. Los límites de LabSim son estos (Margolis y cols., 1995; Roland y cols., 1993; Wuyts y cols., 1997; Devaiah y cols., 2003):

Tabla: Límites de la electrococleografía con click, según el electrodo

| Electrodo | Razón PS/PA | Razón de áreas |
|---|---|---|
| Promontorio (transtimpánico) | 0,35 | 1,94 |
| Tímpano | **0,40** | **1,94** |
| Conducto (TIPtrode) | 0,50 | 1,94 |

Sobre el límite, la razón es compatible con hidrops. La separación del PA entre polaridades se considera alterada sobre **0,38 ms** (Satar y cols., 2003).

#### Cómo se registra en este libro

- **Electrodo timpánico** como activo, con la referencia y la tierra como en el PEAT (→ H10).
- **Click en polaridad alternada, a 90 dB nHL**, 11,1 por segundo y **1.500 barridos**.
- **Filtros de 5 a 3.000 Hz** y **ventana de 10 ms**.
- Si se usa **tone burst**, con envolvente de **1 ms de subida, 10 de meseta y 1 de bajada**, y la ventana en **20 ms**.

Cada parámetro tiene su razón:

1. **El pasa-alto va muy bajo.** El PS es un desplazamiento lento de la línea de base, casi continuo. Un pasa-alto de 100 Hz, el del PEAT, se come buena parte de él: en LabSim, un oído con una razón de 0,55 se mide 0,38 con el pasa-alto en 100 Hz y 0,08 en 200 Hz. El hidrops desaparece por el filtro, no por el oído.
2. **El nivel va alto.** El PA aparece desde cerca del umbral, pero el PS solo se hace medible con la cóclea bien empujada. Una razón medida a nivel bajo sale chica aunque haya hidrops, y el equipo no avisa.
3. **La polaridad va alternada.** La MC se invierte con la polaridad: al alternar se cancela y deja ver el PS y el PA. Para medir la diferencia entre rarefacción y condensación se registra además una curva con cada una.
4. **La ventana va en 10 ms.** La razón de áreas se integra hasta que el complejo vuelve a la línea de base, y en un hidrops marcado eso puede pasar después de los 5 ms. Con burst largo, el PS dura lo que el estímulo y hace falta una ventana de 20 ms.

:::ojo El PA va hacia abajo
En el PEAT las ondas se dibujan hacia arriba porque el electrodo activo está en el vértex. En la ECochG el activo está en el oído, y la negatividad del PA queda **hacia abajo**. No es un error del equipo: es el montaje.
:::

#### Cómo se marca

Se marca primero la **línea de base** (BL), antes de que llegue la respuesta. Después, el **PS**, en el hombro de la bajada, y el **PA**, en el fondo del valle. La amplitud de cada uno se mide desde la línea de base. Para la razón de áreas se marcan también el **inicio** del complejo y su **retorno** a la base. El hombro del PS no tiene un punto exacto con click, porque el PS y el PA se superponen; por eso conviene mirar las dos razones juntas.

#### Conoce tu equipo: la electrococleografía en LabSim

En LabSim la ECochG está dentro del equipo de PEAT: se elige en **Prueba**. El equipo pasa a un montaje timpánico con ventana de 10 ms y la tabla de valores cambia a la del ECochG. El electrodo, la ventana y la ganancia se eligen en *Archivo → Parámetros avanzados*, pestaña *Registro* (→ H10).

:::imagen /docs/manual/img/estudiante/ecochg.png La electrococleografía en LabSim, con el OI registrado y marcado
- @-2.5,8 | **Prueba: ECochG.** Cambia el montaje, la ventana y la tabla. Cambiar de prueba no borra el PEAT.
- @-2.5,15.6 | **Polaridad** alternada para medir las razones. Para la diferencia de latencia hace falta una curva en rarefacción y otra en condensación, al mismo nivel.
- @-2.5,31.3 | **Pasa alto** en 5 Hz. Con el corte del PEAT el PS se achica.
- @-2.5,37 | **Promediación.** Como en el PEAT, la tasa y los barridos parten al azar: configurarlos es parte del examen.
- @23,22.5 | La escala del gráfico sigue al electrodo. El botón **↕** invierte el eje si prefieres ver el PA hacia arriba.
- @57,51 | El PS y el PA marcados sobre el trazo. El PA va hacia abajo.
- @66,34 | La **línea de base** punteada, desde la marca BL.
- @102,34 | Las marcas: **BL**, **Ini**, **PS**, **PA**, **Fin** y **MC**. **Auto** marca la curva elegida, pero la marca se revisa.
- @102,44 | La **razón PS/PA**: 0,562, sobre el 0,40 del electrodo timpánico. La razón de áreas se calcula cuando están el inicio y el retorno.
:::

Las marcas automáticas de LabSim se apoyan en el trazo, no en el caso: si el filtro o el nivel están mal, marcan igual y la medida sale mal. Las medidas de tasa necesitan dos curvas del mismo oído a distinta tasa. El detalle de la técnica estará en H11.

:::comentario Lo que dicen las normas
El límite de la razón de amplitudes cambia de una serie a otra. Con electrodo timpánico, Margolis y cols. (1995) fijaron el criterio para un 95 % de especificidad, y las revisiones que los citan lo sitúan entre 0,40 y 0,49 según el nivel; con solo 12 controles, Satar y cols. (2003) llegaron a 0,32. Con electrodo de conducto, 0,50 es el valor más alto observado en sanos (Roland y cols., 1993), no un corte estadístico. Wuyts y cols. (1997) proponen 0,35 para el transtimpánico y 0,42 para el "extratimpánico", pero agrupan bajo ese nombre el tímpano y el conducto. La razón de áreas (límite 1,94) se publicó con electrodo timpánico (Devaiah y cols., 2003); con aguja en el promontorio no resultó más sensible que la de amplitudes (Baba y cols., 2009). La diferencia entre polaridades la recomiendan Margolis y cols. (1995), pero en la serie de Satar y cols. (2003) los Ménière definidos tuvieron un promedio normal y agregarla no mejoró el diagnóstico. En este libro se usan los límites de la tabla anterior.
:::

<!-- verificar: el rango 0,40-0,49 del límite de Margolis 1995 viene de fuente secundaria (EcochgReferences.php lo marca "a confirmar en el original"). -->

### El reclutamiento: Fowler, SISI y Metz

Un hidrops es una lesión de la **cóclea** y, como toda lesión coclear, recluta: el umbral sube y la molestia no (→ H6). Las pruebas supraliminares lo muestran, y cuál se usa depende del oído contrario:

- **Fowler.** Compara la sonoridad del oído enfermo con la del sano en la misma frecuencia. Necesita un oído de **referencia normal** en esa frecuencia y una diferencia de 20 a 40 dB entre los dos (→ H6). En un Ménière de un lado suele poder hacerse; en un paciente sin oído sano, no.
- **SISI.** Mide si el oído nota aumentos de 1 dB sobre un tono 20 dB por encima del umbral. **No necesita un oído sano**: se hace en cada oído. En LabSim, como en el audiómetro, se hace **a mano**: el tono portador sonando, un giro de la perilla de 1 dB hacia arriba y de vuelta al portador, veinte veces (→ H6).
- **Fenómeno de Metz.** En el impedanciómetro, el reflejo estapedial aparece **a menos de 60 dB sobre el umbral tonal**. Es un signo de reclutamiento que no depende de la respuesta del paciente (→ H7). Recuerda pasar el reflejo a dB HL antes de restar.

El **LDL** completa la lectura: en el oído que recluta queda cerca del del oído sano aunque el umbral sea peor, y el **campo dinámico se estrecha** (→ H5). Es lo que el paciente describe cuando dice que los ruidos fuertes le molestan por el oído que oye menos.

:::ojo Ojo clínico
En el hidrops, las pruebas de deterioro tonal salen como en cualquier lesión coclear: poco o ningún deterioro y un STAT negativo (→ H6). Si un paciente con crisis de vértigo y pérdida unilateral **deteriora**, la historia de Ménière no basta: el schwannoma vestibular también puede dar vértigo, acúfeno y una pérdida de un lado (→ cap. 11).
:::

### El VEMP cervical, en lo justo

El hidrops no se queda en la cóclea. El órgano del equilibrio que más se compromete después de ella es el **sáculo**, y el sáculo es lo que mide el **VEMP cervical** (cVEMP): un sonido fuerte estimula el sáculo y el reflejo llega al músculo esternocleidomastoideo, donde se registra una onda positiva a los 13 ms (P13) y una negativa a los 23 ms (N23). Como la amplitud depende de cuánto contrae el paciente el músculo, se compara la amplitud **corregida por el EMG**, y entre los dos oídos se calcula una **razón de asimetría** (→ H12). El VEMP no depende de la audición: se puede registrar en un oído sordo con el oído medio sano.

### La prueba de glicerol

El glicerol tomado por boca saca agua de los tejidos por ósmosis, también del oído interno. Si un oído tiene hidrops y todavía puede recuperarse, la audición **mejora** por unas horas (Klockhoff y Lindblom, 1966). Es una prueba larga, de unas cuatro horas, y se hace con indicación médica.

**Preparación.** El paciente llega con 12 horas de ayuno, que mantiene durante la prueba, y habiendo tomado poco líquido el día anterior. No toma diuréticos las dos semanas previas ni alcohol las 24 horas previas. Trae la glicerina, un limón y su peso exacto anotado. Se le avisan los efectos que puede tener: dolor de cabeza, mareo, náuseas, vómitos, sed y diarrea o más ganas de orinar. No se hace en diabetes, deshidratación, enfermedad cardíaca, renal o hepática, embarazo ni hipertensión arterial no controlada.

1. **Audiometría basal** completa (→ H3).
2. Se prepara **1,2 mL de glicerol por kilo de peso**, con la misma cantidad de agua y el jugo del limón, y el paciente lo toma **de una vez**.
3. **Controles**: dos, a la hora y media y a las tres horas de la toma; o tres, a la hora, a las dos y a las tres horas. En cada uno se mide la vía aérea, la logoaudiometría y el acúfeno.
4. **Lectura.** La prueba es **positiva** si una frecuencia del audiograma mejora 15 dB o más, si la discriminación mejora 12 % o más, si el promedio tonal aéreo mejora 10 dB o más respecto de la basal, o si disminuyen el acúfeno o la plenitud.

Un resultado **negativo no descarta** el hidrops (Basel y Lütkenhöner, 2013): la enfermedad fluctúa, y un oído medido en un buen día, o con un daño ya fijo, no tiene cuánto mejorar.

:::comentario Lo que dicen las normas
No hay un criterio único de positividad, y los que se han propuesto difieren mucho en sensibilidad y especificidad (Basel y Lütkenhöner, 2013). En la literatura se usa sobre todo la mejoría del umbral en las frecuencias graves, de 10 dB o más en varias frecuencias, o la de la discriminación, y no se suelen aceptar como criterio los síntomas que refiere el paciente, como el acúfeno o la plenitud. En este libro la prueba se lee con los cinco criterios de arriba, y en el informe se anota cuál se cumplió.
:::

<!-- Pasada de fundamentos 2026-10-18: la dosis de 1,2 mL/kg es la que usa la serie de 347 pacientes de Basel y Lütkenhöner (2013, resumen: "glycerol (1.2 mL/kg body weight) was orally administered"); ahí el mayor efecto fue a las 4 horas y casi igual a las 3. El resumen también dice "there is no consensus as to the definition of positive" y "a negative test result is of little diagnostic value". verificar: la frase del recuadro sobre qué criterios usa la literatura (10 dB en varias frecuencias graves, discriminación, síntomas no aceptados) no se pudo confirmar en un texto leído; Klockhoff y Lindblom 1966 no tiene resumen y no se leyó. -->

LabSim no tiene la prueba de glicerol: sus pacientes no cambian dentro de una atención.

:::ayuda Ayuda memoria
- ECochG: electrodo **timpánico**, click **alternado a 90 dB nHL**, **5-3.000 Hz**, ventana de **10 ms**.
- Razón PS/PA sobre **0,40** (tímpano) y razón de áreas sobre **1,94**: compatibles con hidrops.
- El pasa-alto alto y el nivel bajo **esconden** el PS.
- Reclutamiento: **Fowler** si hay un oído sano; **SISI** en cualquier oído; **Metz** en el impedanciómetro.
- cVEMP: el **sáculo**, con la amplitud corregida por el EMG.
- Glicerol: un **negativo no descarta**.
:::

## Fisiología

### Dos líquidos y una batería

El laberinto membranoso es un tubo cerrado lleno de **endolinfa**, sumergido en otro líquido, la **perilinfa**. La perilinfa se parece al líquido que rodea a cualquier célula: mucho sodio y poco potasio. La endolinfa es al revés: **mucho potasio y casi nada de sodio** (Wangemann, 2006). En la cóclea, la endolinfa llena la **rampa media**, limitada arriba por la membrana de Reissner y abajo por la membrana basilar, donde está el órgano de Corti. Los cilios de las células ciliadas están bañados en endolinfa; sus cuerpos, en un líquido parecido a la perilinfa.

La **estría vascular**, en la pared lateral de la rampa media, bombea potasio hacia la endolinfa y la mantiene cargada a unos **+80 mV** respecto de la perilinfa. Es el **potencial endococlear**, y es la batería de la cóclea (Wangemann, 2006). El interior de la célula ciliada es negativo. Entre la endolinfa positiva y la célula negativa hay una diferencia de potencial muy grande, y cuando el sonido inclina los cilios y abre sus canales, el potasio entra empujado por ella. Esa corriente de transducción es la que convierte el movimiento en señal. El potasio que sale de las células vuelve a la estría por las células de sostén y la pared lateral, y se recicla (→ cap. 10). El detalle está en B2.

La endolinfa se produce y se absorbe todo el tiempo, y su volumen se mantiene en un equilibrio fino. El **saco endolinfático**, unido al laberinto por el acueducto vestibular, participa en esa regulación (Salt y Plontke, 2010; → B1).

### Lo que registra un electrodo cerca de la cóclea

Cuando el sonido mueve el órgano de Corti, la corriente que entra a las células ciliadas genera potenciales que un electrodo cercano puede captar:

- La **microfónica coclear** sigue la forma de la onda del sonido, ciclo a ciclo. La generan sobre todo las células ciliadas externas.
- El **potencial de sumación** es la parte **continua** de la respuesta: un desplazamiento que dura lo que dura el estímulo. Aparece porque la transducción no es simétrica: los cilios abren más canales cuando se inclinan hacia un lado que los que cierran hacia el otro, y el promedio no da cero. Con un electrodo en la ventana redonda, el PS parece venir sobre todo de las **células ciliadas internas** (Durrant y cols., 1998).
- El **potencial de acción** es la suma de las descargas de las fibras del nervio auditivo que disparan juntas al comienzo del estímulo. Depende de que haya fibras y de que disparen sincrónicas.

### Lo que hace el hidrops

En el hidrops la endolinfa aumenta y la rampa media se **distiende**: la membrana de Reissner se abomba hacia la rampa vestibular y, en el hidrops avanzado, puede llegar a llenarla. En las vueltas apicales también se ha visto la membrana basilar desplazada hacia la rampa timpánica (Salt y Plontke, 2010). La explicación más usada del PS grande parte de ahí: con el órgano de Corti corrido de su posición de reposo, la transducción trabaja desde otro punto de partida y se vuelve más asimétrica, y **el PS crece**. En el cobayo, correr el órgano de Corti hacia la rampa timpánica con un gel inyectado en el ápice cambia ese punto de trabajo y agranda el PS (Salt y Plontke, 2010). El PA, que depende de las fibras, cambia poco. Por eso la **razón PS/PA sube** (Ferraro y Durrant, 2006). No es un mecanismo cerrado: en el hidrops experimental del cobayo el PS creció poco y solo al comienzo, y la presión de la endolinfa casi no sube (Salt y Plontke, 2010).

<!-- Pasada de fundamentos 2026-10-18: decía que "la presión de la rampa media desplaza también la membrana basilar hacia la rampa timpánica" y daba el mecanismo como hecho. Salt y Plontke (2010, texto completo PMC2923478): "Displacements of the basilar membrane in the apical segments of the cochlea have also been reported, in some patients to a degree where the basilar membrane contacts the bony wall of the scala tympani"; gel en el ápice: "sustained transducer operating point change, consistent with a displacement of the organ of Corti towards scala tympani", con "increases of summating potential" a tasas altas; pero "the increase of SP in hydropic guinea pigs was small and confined to the initial period after sac ablation" y "the role that pressure plays in endolymphatic hydrops is at best, limited". Se resolvió el verificar. Ferraro y Durrant (2006) no se leyó entero: queda solo como fuente de la razón PS/PA como medida del hidrops (resumen). -->

:::imagen ilustraciones/cap09-hidrops.svg ancho=92% Corte de una espira de la cóclea. A, normal: la rampa media (endolinfa) es un triángulo entre la membrana de Reissner, la membrana basilar y la estría vascular. B, hidrops: la endolinfa aumenta, la membrana de Reissner se abomba hacia la rampa vestibular y la rampa media se agranda.
:::

El hidrops pesa más en el **ápice**, que es donde se codifican los graves: ahí se desplaza la membrana basilar y ahí se pierden primero las células ciliadas (Salt y Plontke, 2010). Por eso la primera pérdida es **ascendente**: graves peores que agudos (→ H3). <!-- Pasada de fundamentos 2026-10-18: decía "El hidrops empieza y pesa más en el ápice", sin cita. Salt y Plontke (2010): estereocilios de las CCE alterados "first occurring in the apical regions", pérdidas "greatest in the apical turns" y membrana basilar desplazada en los segmentos apicales. Que el hidrops "empiece" en el ápice no lo dicen (en el cobayo lo primero fueron sáculo, seno endolinfático y Reissner). --> La cóclea sigue comportándose como cóclea, con reclutamiento, y la discriminación se mantiene más o menos acorde a la curva mientras la pérdida no avance. Del laberinto posterior, el primero en comprometerse suele ser el sáculo, y después el utrículo y los canales (Young, 2013).

La relación entre el hidrops y los síntomas no es simple. Hay oídos con hidrops en el estudio histológico que nunca tuvieron crisis, y el hidrops podría ser más un marcador de la enfermedad que la causa directa de cada crisis (Merchant y cols., 2005; Salt y Plontke, 2010). La audición fluctúa, y la ECochG, que mide un oído en un momento, también.

:::sabias ¿Sabías que?
Prosper Ménière describió en 1861 que el vértigo con hipoacusia y zumbido podía venir del oído y no del cerebro, como se creía entonces (Baloh, 2001). Que la causa fuera un exceso de endolinfa no se vio hasta 1938, cuando Hallpike y Cairns encontraron la rampa media distendida en los huesos temporales de pacientes que la habían tenido (Hallpike y Cairns, 1938).
:::

## Patología

### Enfermedad de Ménière

Es el hidrops sin una causa conocida. Lo característico son las **crisis**: vértigo que gira, de minutos a horas, con náuseas y vómitos, acompañado en el oído afectado de **plenitud**, **acúfeno** (típicamente grave, un zumbido) y **baja de audición**. <!-- Pasada de fundamentos 2026-10-18: decía "casi siempre grave". Sin fuente para el "casi siempre"; lo que hay es que el tono del acúfeno coincide con la frecuencia peor del audiograma en el 64 % (Zhang y cols., 2016), que al comienzo son los graves. --> Entre crisis el paciente queda bien o con algo de inestabilidad, y la audición mejora en parte. Con los años, cada crisis deja algo más de pérdida.

Los criterios de la Sociedad Bárány (Lopez-Escamez y cols., 2015) piden, para un Ménière **definido**:

1. Dos o más crisis espontáneas de vértigo, de **20 minutos a 12 horas** cada una.
2. Una hipoacusia sensorioneural de **frecuencias graves y medias**, documentada con audiometría en el oído afectado, en algún momento antes, durante o después de una crisis.
3. Síntomas del oído **fluctuantes** en ese oído: audición, acúfeno o plenitud.
4. Que otro diagnóstico vestibular no lo explique mejor.

El criterio audiométrico es exigente: en dos frecuencias contiguas bajo 2.000 Hz, el oído afectado tiene que estar **al menos 30 dB peor** que el otro (Lopez-Escamez y cols., 2015). Una pérdida más leve, o medida en un buen día, no lo cumple aunque la historia sea típica. Por eso una sola audiometría normal no descarta el Ménière, y las audiometrías se **repiten**, idealmente cerca de una crisis.

El audiograma pasa por etapas. Al principio es **ascendente**, con graves peores y agudos conservados; después se **aplana** y puede llegar a severo (→ cap. 23). En una serie de pacientes con Ménière, el umbral medio fue de unos 45 dB, y la frecuencia del acúfeno coincidió con la peor del audiograma en dos de cada tres (Zhang y cols., 2016).

Lo que se espera encontrar en un Ménière típico, de un lado:

- **Audiometría**: sensorioneural, ascendente, de un oído. La ósea con la aérea.
- **Logoaudiometría**: discriminación algo menor que la del otro oído, a veces con caída a nivel alto.
- **Reclutamiento**: Fowler completo, SISI alto, Metz. Campo dinámico estrecho.
- **Deterioro tonal**: negativo.
- **ECochG**: razón PS/PA y de áreas sobre el límite.
- **VEMP cervical**: reducido o ausente del lado enfermo (Young, 2013).
- **Emisiones**: reducidas en la zona de la pérdida, que en el Ménière son los graves.

El hidrops también se puede ver en vivo, con una resonancia hecha horas después de inyectar gadolinio. No es parte de los criterios de 2015: la pide y la informa el médico.

:::imagen ilustraciones/cap09-rm-hidrops.jpg ancho=90% Resonancia para hidrops de un hombre de 31 años con Ménière del oído derecho; no es un paciente de este capítulo. Se muestra para que se vea la forma de lo que miden la ECochG y el VEMP. El espacio endolinfático agrandado se ve negro dentro de la perilinfa blanca. Rótulos originales: C, cóclea; S, sáculo; U, utrículo; *Right* y *Left*, oído derecho e izquierdo. Imagen: Young YH, Lin KT (2024), J Otolaryngol Head Neck Surg, doi:10.1177/19160216241250350, Fig. 2, CC BY-NC 4.0.
- @13,22 | **Oído con Ménière**: hidrops coclear grado II y sacular y utricular grado III (flechas continuas). Las manchas negras son la endolinfa agrandada.
- @91,48 | **El otro oído, de control**: sin hidrops (flechas punteadas). La perilinfa queda blanca alrededor de la cóclea y el vestíbulo.
:::

:::comentario Lo que dicen las normas
Los casos de LabSim muestran el Ménière **típico**: el de la etapa ascendente, con la ECochG y el VEMP alterados. En la clínica no siempre es así. Entre un cuarto y la mitad de los Ménière tienen la ECochG **normal** (Lamounier y cols., 2014); con electrodo extratimpánico, la sensibilidad fue de alrededor de 48 % y la especificidad de 84 % (Ayub y cols., 2019). En el hidrops retardado, el VEMP cervical salió normal en casi la mitad de los pacientes (Young y cols., 2002). Una ECochG o un VEMP normales **no descartan** el hidrops; uno alterado lo apoya.
:::

### Hidrops retardado

Es un hidrops que aparece **años después** de una sordera profunda de un oído (Schuknecht, 1978). Esa sordera antigua viene de una infección o de un trauma; en más de la mitad de los casos es una sordera de un oído que se descubre en la infancia sin fecha de inicio, y en los huesos temporales estudiados el oído sordo muestra las lesiones de la laberintitis por **paperas** o por sarampión (Schuknecht y cols., 1990). <!-- Pasada de fundamentos 2026-10-18: decía "suele venir de una laberintitis viral, sobre todo por paperas, o de un trauma". Schuknecht 1978 (resumen): "usually from infection or trauma"; Schuknecht y cols. 1990 (resumen): "In more than half the cases... the profound hearing losses in the early phase are simply discovered to be present in early childhood without a known time of onset" y, en dos huesos temporales, cambios del oído sordo "similar to those known to occur in mumps and measles labyrinthitis". --> Tiene dos formas:

- **Ipsilateral**: el mismo oído sordo empieza a dar crisis de vértigo, sin cambios de audición que medir.
- **Contralateral**: el oído **que oía bien** empieza a fluctuar, con o sin crisis de vértigo. En una serie de 57 pacientes con esta forma, el oído con hidrops tuvo una pérdida fluctuante de graves, con un promedio de 41 dB, que rara vez llegó a severa (Albera y cols., 2021).

La forma contralateral tiene una gravedad propia: enferma el **único oído que oye**. Cada fluctuación, que en un Ménière de un lado el paciente compensa con el otro oído, aquí lo deja sin audición útil por días.

En el estudio hay dos detalles técnicos. El oído sordo exige **enmascarar** para medir el que oye, y el que oye, para confirmar que el sordo no responde (→ H4). Y las pruebas que comparan contra un oído sano, como el **Fowler**, no se pueden hacer: no hay un oído normal de referencia. El reclutamiento se busca con el **SISI** y con el **Metz**.

:::sabias ¿Sabías que?
Schuknecht propuso que el oído sordo y el que se enferma después podrían haber sufrido la misma infección viral en la infancia: en uno destruyó la cóclea de inmediato y en el otro dejó un daño silencioso que, años después, terminó en un hidrops como el del Ménière (Schuknecht y cols., 1990).
:::

<!-- Pasada de fundamentos 2026-10-18: se resolvió el verificar. La hipótesis está en Schuknecht y cols. (1990), no en el de 1978; resumen: "Meniere's disease may occur as a delayed sequela of inner ear damage sustained during an attack of subclinical viral labyrinthitis occurring in childhood" (lo atribuye igual Kamei, 2004, Int Tinnitus J 10:137-43). Decía además que el daño era de "la reabsorción de la endolinfa": eso es el mecanismo que Schuknecht da para la forma ipsilateral (atrofia u obliteración del sistema de reabsorción, según Kamei 2004); para la contralateral la fuente habla solo de un daño subclínico, y se dejó así. -->

## Razonamiento

### De las crisis a la hipótesis

Frente a un paciente con crisis de vértigo y síntomas de un oído, el razonamiento sigue cuatro preguntas:

1. **¿La historia calza?** Crisis de 20 minutos a 12 horas, con plenitud, acúfeno grave y audición que cambia, de un oído. Un vértigo de segundos al girar en la cama es otra cosa (→ cap. 22), y uno de días, sin síntomas del oído, también (→ cap. 21).
2. **¿El audiograma calza?** Sensorioneural, de graves, del oído de los síntomas. Si es plano o de agudos, o si hay gap, la historia no basta.
3. **¿La lesión es coclear?** Reclutamiento, sin deterioro tonal, con Metz. Si el oído deteriora o la discriminación es mucho peor que la curva, se busca el nervio (→ cap. 11).
4. **¿Hay huella de hidrops?** La ECochG con la razón alta, el VEMP cervical reducido de ese lado, la prueba de glicerol positiva. Que sean normales no descarta.

:::ayuda-ancho Crisis con un oído comprometido, lado a lado
| | Ménière | Hidrops retardado (contralateral) | Súbita con vértigo (→ cap. 7) | Schwannoma (→ cap. 11) |
|---|---|---|---|---|
| Historia | crisis repetidas de horas, plenitud, acúfeno grave | sordera profunda antigua del otro oído; después, fluctuación del que oye | una sola instalación, con fecha | lenta, sin crisis típicas |
| Audiograma | ascendente, fluctuante | ascendente en el oído que oía; el otro, profundo | variable, sin fluctuación | asimétrico, a menudo de agudos |
| Reclutamiento | presente | presente | presente | **ausente** |
| Deterioro tonal | negativo | negativo | negativo | **positivo** |
| ECochG | razón alta | razón alta en el oído que oye | sin hallazgo propio | sin hallazgo propio |
:::

### Lo que más se equivoca

- **Dar por normal un audiograma de un buen día.** El hidrops fluctúa: una sola audiometría entre crisis puede estar casi normal. La historia manda pedir otra.
- **Registrar la ECochG con los filtros del PEAT.** Con el pasa-alto en 100 Hz el PS se achica y el hidrops desaparece del trazo.
- **Medir la razón a nivel bajo.** El PS necesita nivel.
- **Leer la ECochG normal como "no es hidrops".** Una parte de los Ménière la tiene normal.
- **Intentar el Fowler sin un oído sano**, o con una diferencia de más de 40 dB.
- **Restar el reflejo en dB SPL del umbral en dB HL** al buscar el Metz (→ H7).
- **Atribuirle al Ménière cualquier vértigo con hipoacusia.** Un deterioro tonal positivo o una discriminación muy mala obligan a pensar en el nervio.

:::pregunta Pregunta abierta
Una paciente con tres crisis típicas de vértigo con plenitud izquierda tiene hoy un audiograma con 20 dB en los graves del OI y una ECochG con la razón PS/PA en 0,32. ¿Qué le dirías? ¿Qué harías para la próxima vez?
:::

## Casos

Cada caso se trabaja en cuatro pasos, como en el aprendizaje basado en problemas: lee la entrevista, separa los datos que importan, plantea tus hipótesis y decide qué pedir **antes** de mirar los resultados. La resolución de cada caso está al final del capítulo.

{{caso cap09_p38}}

:::pregunta Paso 1 · ¿Qué datos importan?
Separa en la entrevista de Patricia lo que pasa **durante** las crisis de lo que pasa **entre** ellas. ¿Cuánto duran? ¿Qué siente en el oído antes de cada una?
:::

:::pregunta Paso 2 · Tus hipótesis
Las voces le suenan "metálicas" por el OI y los gritos del recreo le molestan. ¿Qué te dice eso del sitio de la lesión? Plantea al menos dos hipótesis y qué esperas del audiograma en cada una.
:::

:::pregunta Paso 3 · ¿Qué pedirías y por qué?
El otorrinolaringólogo pidió evaluación auditiva y electrococleografía. ¿Qué pruebas de reclutamiento le puedes hacer, si su OD es normal? ¿Cómo vas a configurar la ECochG para no perder el potencial de sumación?
:::

#### Paso 4 · Los resultados

:::figura cap09_p38 audiograma
- @OI 500 | En los graves el OI está en **50 dB**, enmascarado (los cuadrados): la diferencia con el OD es de 45 dB.
- @OI 2000 | Hacia los agudos mejora: 30 dB en 2 kHz y 25 en 3, 4 y 6 kHz. Es una curva **ascendente**.
- @OI osea 1000 | La ósea va con la aérea: sensorioneural.
- @OD 1000 | El OD está entre 0 y 10 dB: es la referencia para el Fowler.
- Los triángulos son el LDL: **110 dB** en los dos oídos. El OI oye 45 dB peor en los graves y se molesta al mismo nivel: el campo dinámico se estrecha.
:::

:::figura cap09_p38 logoaudiometria
- @OD max | El OD llega al 100 % a 40 dB.
- @OI max | El OI llega al **88 %** a 70 dB y baja un poco, a 75 %, a 100 dB. Es algo menos que el OD, acorde a una pérdida coclear leve a moderada.
:::

Sobre el umbral, Patricia entrega lo que se vio en H6: **Fowler** en 1 kHz con reclutamiento completo (los dos oídos suenan igual a 70 dB HL), **SISI** de alrededor de 90 % en 1 y 2 kHz en el OI y de 0 % en el OD, **Carhart** con deterioro de 5 dB en el OI y sin deterioro en el OD, y **STAT** negativo en los dos oídos.

:::figura cap09_p38 reflejos
- @ipsi OI 500 | Con la sonda en el OI, el reflejo aparece a 90 dB SPL en 500 Hz, que son 84,5 dB HL: solo **34,5 dB sobre su umbral** de 50 dB. Es **Metz**.
- @ipsi OI 1000 | En 1 kHz, 85 dB HL contra un umbral de 40: 45 dB. También Metz.
- @ipsi OD 1000 | El OD tiene el reflejo en el mismo nivel, pero con un umbral de 5 dB: 80 dB de distancia, lo normal.
- Que los reflejos del OI salgan donde los de un oído sano, con 40 a 45 dB de pérdida, es el reclutamiento visto sin preguntarle nada a la paciente.
:::

:::figura cap09_p38 ecochg
- @OD PA | El OD tiene un PA profundo y un PS chico: razón **0,31**, bajo el 0,40 del electrodo timpánico, y razón de áreas **1,19**, bajo 1,94. Es la referencia.
- @OI PS | En el OI el PS es casi tan grande como el PA: razón **0,60**.
- @OI PA | Después del PA el trazo no vuelve a la base dentro de la figura: el retorno está a 7,3 ms. Esa cola es el PS prolongado, y lleva la razón de áreas a **3,61**.
- Click alternado a 90 dB nHL, electrodo timpánico, filtros de 5 a 3.000 Hz.
:::

:::figura cap09_p38 vemp
- @OD P13 | El cVEMP del OD tiene una P13 y una N23 bien formadas: 350 µV, 6,79 corregida por el EMG.
- @OI P13 | El del OI casi no se separa del ruido: 33 µV, 0,66 corregida.
- La razón de asimetría es de **82 %**: el sáculo del OI responde mucho menos. Es el compromiso sacular del hidrops.
:::

:::figura cap09_p38 dpoae
- @OI 1000 | En el OI el DP está ausente en 1 y 1,5 kHz, donde el umbral está en 40 dB o peor.
- @OI 3000 | Desde 2 kHz aparece, con su máximo en 3 kHz, donde la audiometría es casi normal.
- Con **4 de 7** el equipo dice "pasa", pero el DP-grama dibuja la curva ascendente: las células ciliadas externas de los graves dejaron de amplificar.
:::

:::docente Guía del caso
- **Datos clave:** 46 años; cuatro o cinco crisis de vértigo rotatorio de horas con vómitos en un año; antes de cada una, plenitud del OI y zumbido grave; voces "metálicas" (diploacusia) e hiperacusia por el OI; audición que fluctúa; betahistina y dieta baja en sal.
- **Hipótesis esperables:** enfermedad de Ménière del OI; migraña vestibular; schwannoma vestibular (menos probable con crisis de horas, pero hay que descartarlo).
- **Qué pedir:** audiometría con enmascaramiento, LDL, logoaudiometría, Fowler y SISI, deterioro tonal, impedanciometría con reflejos, ECochG y VEMP cervical (→ H3, H5, H6, H7, H11, H12). Emisiones como complemento.
- **Errores esperables:** registrar la ECochG con el pasa-alto del PEAT; no buscar el Metz; dar por normal la DPOAE del OI porque "pasa".
- **En LabSim:** es el paciente de práctica 38; se atiende desde "Práctica libre". El ECochG está dentro del PEAT; el VEMP, en el box de electrofisiología.
:::

{{caso cap09_hidrops_retardado}}

:::pregunta Paso 1 · ¿Qué datos importan?
¿Qué antecedente de la infancia de Samuel cambia la forma de mirar sus crisis? ¿Qué te dice que el oído izquierdo se tape **antes y después** de cada una?
:::

:::pregunta Paso 2 · Tus hipótesis
Plantea al menos dos causas para un oído que se tapa y oye menos por días, con crisis de vértigo, en alguien que solo oye por ese oído.
:::

:::pregunta Paso 3 · ¿Qué pedirías y por qué?
El OD no oye desde los seis años. ¿Qué vas a tener que enmascarar, y dónde? ¿Puedes hacerle un Fowler? ¿Qué prueba de reclutamiento usarías en su lugar?
:::

#### Paso 4 · Los resultados

:::figura cap09_hidrops_retardado audiograma
- @OD 1000 | El OD está entre 90 y 115 dB, con enmascaramiento en el OI (los triángulos). Sin enmascarar, habría respondido el OI.
- La ósea del OD, enmascarada, no responde al máximo del vibrador (los corchetes con flecha).
- @OI 500 | El OI está en **30 dB** de 125 a 500 Hz.
- @OI 1000 | En 1 y 2 kHz mejora a 20 dB: los graves están 10 dB peor que los medios, una curva **ascendente** leve.
- @OI 8000 | De 3 a 8 kHz baja de 25 a 35 dB: es la caída de la edad, a los 54 años (→ cap. 5).
- Este es el audiograma de **un día**: lleva un mes y medio sin crisis.
:::

:::figura cap09_hidrops_retardado acumetria
- @weber 500 | El Weber se va al **OI**, el que oye. En una pérdida sensorioneural el Weber va al oído mejor.
- @rinne OD 500 | El Rinne del OD sale negativo: el diapasón en la mastoides se oye mejor que frente al conducto. No es una pérdida conductiva: el vibrador derecho lo oye la cóclea izquierda. Es un **falso negativo**, y el audiograma enmascarado lo confirma.
:::

:::figura cap09_hidrops_retardado logoaudiometria
- @OI max | El OI llega al **96 %** a 50 dB y baja a 82 % desde 80 dB.
- @OD max | El OD, enmascarado, no pasa del 27 % a 100 dB: no le sirve para entender.
:::

Sobre el umbral, el **Fowler no se puede hacer**: no hay un oído de referencia normal y, donde el OI está en 20 dB, la diferencia con el OD es de 75 dB. En el OD no se puede hacer ninguna prueba supraliminar: su umbral está demasiado cerca del máximo del audiómetro y de su molestia.

:::ayuda-ancho Lo que entrega Samuel sobre el umbral (OI en estudio)
| Prueba | OI |
|---|---|
| SISI, 500 y 1.000 Hz | **90 %**: reclutamiento |
| Carhart, 500 a 4.000 Hz | deterioro de 0 a 5 dB |
| STAT, 500, 1.000 y 2.000 Hz | (−) |
:::

:::figura cap09_hidrops_retardado reflejos
- @ipsi OI 500 | Con la sonda en el OI, el reflejo aparece a 90 dB SPL en 500 Hz, 84,5 dB HL: **54,5 dB sobre su umbral** de 30. Metz, por poco.
- @ipsi OD 1000 | Con la sonda en el OD no hay reflejo ipsilateral: el tono no llega a ninguna cóclea que lo oiga.
- @contra OI 1000 | Tampoco con el tono en el OD y la sonda en el OI. En cambio, con el tono en el OI y la sonda en el OD, el reflejo está a su nivel normal: el oído medio derecho está sano. Falla todo lo que se estimula por el OD.
:::

La electrococleografía, con el mismo protocolo del caso anterior, da:

:::figura cap09_hidrops_retardado ecochg
- @OI PS | En el OI el PS es grande frente al PA: razón PS/PA **0,45**, sobre el límite de 0,40 del electrodo timpánico.
- @OI PA | La razón de áreas es **2,88**, sobre 1,94. Latencia del PA, **1,43 ms**.
- En el OD no hay complejo que medir: a 90 dB nHL, en una cóclea que no oye, no aparecen ni PS ni PA.
- Click alternado a 90 dB nHL, electrodo timpánico, filtros de 5 a 3.000 Hz.
:::

:::figura cap09_hidrops_retardado vemp
- @OI P13 | El cVEMP del OI es pequeño: 32 µV, 0,62 corregida por el EMG.
- @OD P13 | El del OD también: 50 µV, 0,98 corregida.
- La razón de asimetría es de **22 %**: los dos lados se parecen, pero porque **los dos** responden poco. Compáralos con el OD sano de Patricia, con el mismo equipo y al mismo nivel: 6,79. Una asimetría baja no significa dos sáculos sanos.
:::

:::docente Guía del caso
- **Datos clave:** sordera profunda del OD desde las paperas a los seis años; ocho meses de crisis de vértigo de horas; OI que se tapa y oye menos por días, antes y después de cada crisis; sin acúfeno; es su único oído útil.
- **Hipótesis esperables:** hidrops endolinfático retardado contralateral; Ménière del OI (sin el antecedente, sería el diagnóstico); hipoacusia súbita del único oído; schwannoma del OI.
- **Qué pedir:** audiometría con enmascaramiento de los dos lados, logoaudiometría, SISI y deterioro tonal en el OI, impedanciometría con reflejos, ECochG y VEMP cervical (→ H3, H4, H6, H7, H11, H12). Controles seriados.
- **Errores esperables:** intentar el Fowler; anotar el Rinne del OD como conductivo; leer el VEMP como normal por la asimetría baja; tranquilizar al paciente porque el audiograma de hoy está "casi normal".
- **En LabSim:** no está entre los pacientes de práctica; se crea con el cuadro *Hidrops endolinfático retardado (contralateral)* en el OI. El editor propone solo el oído contrario, entre parotiditis, laberintitis y fractura transversal: para este caso, *Parotiditis* en el OD.
:::

## Resolución de los casos

Intenta resolver cada caso con los pasos del aprendizaje basado en problemas antes de leer esta sección.

### Caso 9.1

#### Razonamiento

Patricia cumple la historia completa del Ménière: crisis de vértigo de horas, repetidas, con plenitud y zumbido grave del OI, y una audición que fluctúa. El audiograma es el de la etapa temprana: **ascendente**, de un oído, sensorioneural. Todo lo que se mide sobre el umbral dice **cóclea**: el campo dinámico estrecho, el Fowler completo, el SISI alto, el Metz y la ausencia de deterioro. La ECochG muestra la huella del hidrops con las dos razones sobre el límite, y el cVEMP del OI casi desaparece: el sáculo de ese lado también está comprometido. Hasta las voces "metálicas" calzan: es la diploacusia de un oído coclear.

#### Diagnóstico y qué sigue

Hipoacusia sensorioneural del OI, ascendente, leve a moderada, de características cocleares. Electrococleografía del OI con razón PS/PA de 0,60 y razón de áreas de 3,61, sobre los límites. VEMP cervical del OI con amplitud muy reducida. El conjunto es compatible con un hidrops endolinfático del OI; con su historia, el médico podrá plantear una enfermedad de Ménière definida. La evaluación vestibular completa, que no se hace en LabSim, se ve en el cap. 23. Se sugiere **control audiométrico seriado**, idealmente también cerca de una crisis, para documentar la fluctuación.

:::comentario Comentario
El DP-grama del OI dice "pasa" con 4 de 7. Si solo se hubiera mirado el resultado global, se habría informado normal una cóclea que no amplifica los graves. Como en el ruido (→ cap. 6), las emisiones se leen frecuencia por frecuencia.
:::

### Caso 9.2

#### Razonamiento

La clave está en el antecedente: un oído **sordo desde la infancia por paperas** y, décadas después, crisis de vértigo con fluctuación del **otro** oído. Es la forma contralateral del hidrops retardado (Schuknecht, 1978). El OI muestra lo mismo que el de Patricia, más suave: graves algo peores, reclutamiento por SISI y por Metz, sin deterioro tonal y una ECochG con las dos razones sobre el límite. Lo técnico del caso está en el oído sordo: obliga a enmascarar, hace aparecer un Rinne falso negativo, impide el Fowler y deja al VEMP sin un lado sano contra el cual comparar.

#### Diagnóstico y qué sigue

OD: hipoacusia sensorioneural profunda, antigua. OI: hipoacusia sensorioneural leve, con graves 10 dB peor que los medios y caída de agudos acorde a la edad, de características cocleares, con buena discriminación. Electrococleografía del OI con razón PS/PA de 0,45 y razón de áreas de 2,88, sobre los límites; sin respuesta en el OD. VEMP cervical de amplitud reducida en ambos lados. Compatible con un hidrops endolinfático del OI en un paciente con cofosis derecha. Como es su **único oído útil**, se sugiere control audiométrico seriado y consulta precoz ante cualquier baja de audición, y conversar desde ya las opciones de rehabilitación si la audición del OI empeora (→ Parte IX).

:::ojo Ojo clínico
El audiograma de hoy está casi normal y es fácil tranquilizar al paciente. Pero el hidrops fluctúa: lo que Samuel cuenta de los días en que "no entiende a los clientes" no se ve en un examen hecho un mes y medio después de la última crisis. El informe tiene que decir **cuándo** fue la última crisis.
:::

## Para cerrar

:::pregunta Preguntas para discutir
1. ¿Por qué el hidrops hace crecer el potencial de sumación y no el potencial de acción?
2. Registraste una ECochG con el pasa-alto en 100 Hz y la razón PS/PA salió 0,30 en un oído con historia de Ménière. ¿Qué harías antes de informarla como normal?
3. ¿Por qué a Patricia se le puede hacer un Fowler y a Samuel no? ¿Qué pruebas de reclutamiento les quedan a los dos?
4. Un paciente con Ménière típico tiene la ECochG normal. ¿Descarta eso el diagnóstico? ¿Por qué?
5. ¿Qué significa una prueba de glicerol negativa? ¿Y una positiva?
6. En Samuel, la razón de asimetría del VEMP es de 22 %. ¿Por qué no basta para decir que sus sáculos están sanos?
:::

:::ayuda Ayuda memoria del capítulo
- La endolinfa es rica en potasio y la estría la mantiene a **+80 mV**: es la batería de la transducción.
- En el hidrops la rampa media se distiende, el **PS crece** y la razón PS/PA sube.
- El Ménière: crisis de vértigo de **20 minutos a 12 horas**, plenitud, acúfeno grave y una pérdida **ascendente** que fluctúa.
- Es coclear: reclutamiento (**Fowler**, **SISI**, **Metz**) y sin deterioro tonal.
- ECochG: tímpano, click alternado a 90 dB nHL, **pasa-alto bajo**; límites **0,40** y **1,94**. Normal no descarta.
- Hidrops retardado: una sordera profunda antigua y, años después, el hidrops; en la forma contralateral, en el **único oído que oye**.
:::

## Referencias

### Técnica

1. Margolis RH, Rieks D, Fournier EM, Levine SE. Tympanic electrocochleography for diagnosis of Menière's disease. Arch Otolaryngol Head Neck Surg. 1995;121(1):44-55. doi:10.1001/archotol.1995.01890010032007. PMID 7803022.
1. Devaiah AK, Dawson KL, Ferraro JA, Ator GA. Utility of area curve ratio electrocochleography in early Meniere disease. Arch Otolaryngol Head Neck Surg. 2003;129(5):547-551. doi:10.1001/archotol.129.5.547. PMID 12759268.
1. Satar B, Meteoğlu A, Yetişer S, Özkaptan Y. Endolenfatik hidropsta kulak zarından elektrokokleografi: klinik ve elektrofizyolojik ilişkinin araştırılması. Türkiye Klinikleri J ENT. 2003;3(1):30-39.
1. Roland PS, Rosenbloom J, Yellin W, Meyerhoff WL. Intrasubject test-retest variability in clinical electrocochleography. Laryngoscope. 1993;103(9):963-966. doi:10.1288/00005537-199309000-00004. PMID 8361316.
1. Wuyts FL, Van de Heyning PH, Van Spaendonck MP, Molenberghs G. A review of electrocochleography: instrumentation settings and meta-analysis of criteria for diagnosis of endolymphatic hydrops. Acta Otolaryngol Suppl. 1997;526:14-20. doi:10.3109/00016489709124014.
1. Baba A, Takasaki K, Tanaka F, Tsukasaki N, Kumagami H, Takahashi H. Amplitude and area ratios of summating potential/action potential (SP/AP) in Meniere's disease. Acta Otolaryngol. 2009;129(1):25-29. doi:10.1080/00016480701724888. PMID 19003588.
1. Lamounier P, Gobbo DA, de Souza TSA, de Oliveira CACP, Bahmad F Jr. Electrocochleography for Ménière's disease: is it reliable? Braz J Otorhinolaryngol. 2014;80(6):527-532. doi:10.1016/j.bjorl.2014.08.010.
1. Klockhoff I, Lindblom U. Endolymphatic hydrops revealed by glycerol test. Preliminary report. Acta Otolaryngol. 1966;61(5):459-62. doi:10.3109/00016486609127084
1. Basel T, Lütkenhöner B. Auditory threshold shifts after glycerol administration to patients with suspected Menière's disease: a retrospective analysis. Ear Hear. 2013;34(3):370-84. doi:10.1097/AUD.0b013e31826d0c08

### Fisiología

1. Wangemann P. Supporting sensory transduction: cochlear fluid homeostasis and the endocochlear potential. J Physiol. 2006;576(Pt 1):11-21. doi:10.1113/jphysiol.2006.112888
1. Durrant JD, Wang J, Ding DL, Salvi RJ. Are inner or outer hair cells the source of summating potentials recorded from the round window? J Acoust Soc Am. 1998;104(1):370-7. doi:10.1121/1.423293
1. Salt AN, Plontke SK. Endolymphatic hydrops: pathophysiology and experimental models. Otolaryngol Clin North Am. 2010;43(5):971-83. doi:10.1016/j.otc.2010.05.007
1. Ferraro JA, Durrant JD. Electrocochleography in the evaluation of patients with Ménière's disease/endolymphatic hydrops. J Am Acad Audiol. 2006;17(1):45-68. doi:10.3766/jaaa.17.1.6

### Patología

1. Lopez-Escamez JA, Carey J, Chung WH, Goebel JA, Magnusson M, Mandalà M, et al. Diagnostic criteria for Menière's disease. J Vestib Res. 2015;25(1):1-7. doi:10.3233/VES-150549
1. Zhang Y, Liu B, Wang R, Jia R, Gu X. Characteristics of the cochlear symptoms and functions in Meniere's disease. Chin Med J (Engl). 2016;129(20):2445-2450. doi:10.4103/0366-6999.191767
1. Young YH. Potential application of ocular and cervical vestibular-evoked myogenic potentials in Meniere's disease: a review. Laryngoscope. 2013;123(2):484-91. doi:10.1002/lary.23640
1. Ayub A, Qi L, Nunez DA. A systematic review and meta-analysis of extratympanic electrocochleography in Ménière's disease diagnosis. Int J Audiol. 2019;58(9):533-540. doi:10.1080/14992027.2019.1606947
1. Schuknecht HF. Delayed endolymphatic hydrops. Ann Otol Rhinol Laryngol. 1978;87(6 Pt 1):743-8. doi:10.1177/000348947808700601
1. Albera A, Canale A, Boldreghini M, Lucisano S, Riva G, Albera R. Contralateral delayed endolymphatic hydrops: Clinical features and long term outcome. J Otol. 2021;16(4):205-209. doi:10.1016/j.joto.2021.02.003
1. Young YH, Huang TW, Cheng PW. Vestibular evoked myogenic potentials in delayed endolymphatic hydrops. Laryngoscope. 2002;112(9):1623-6. doi:10.1097/00005537-200209000-00018
1. Hallpike CS, Cairns H. Observations on the pathology of Ménière's syndrome. J Laryngol Otol. 1938;53(10):625-55. doi:10.1017/S0022215100003947
1. Merchant SN, Adams JC, Nadol JB Jr. Pathophysiology of Meniere's syndrome: are symptoms caused by endolymphatic hydrops? Otol Neurotol. 2005;26(1):74-81. doi:10.1097/00129492-200501000-00013. PMID 15699723.
1. Schuknecht HF, Suzuka Y, Zimmermann C. Delayed endolymphatic hydrops and its relationship to Ménière's disease. Ann Otol Rhinol Laryngol. 1990;99(11):843-53. doi:10.1177/000348949009901101
1. Baloh RW. Prosper Ménière and his disease. Arch Neurol. 2001;58(7):1151-6. doi:10.1001/archneur.58.7.1151
