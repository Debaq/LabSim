# H7. Impedanciometría

:::objetivos En esta herramienta
- Explicar qué mide la sonda y por qué el timpanograma se hace con 226 Hz en el adulto y con 1000 Hz en el lactante.
- Hacer una timpanometría y leer en ella el volumen, la compliancia, la presión y la forma, sin quedarse solo con la letra.
- Buscar el umbral del reflejo estapedial ipsi y contralateral y reconocer los patrones que orientan al sitio de lesión.
- Hacer el deterioro del reflejo y las pruebas de función tubaria, con membrana íntegra y con membrana perforada.
- Informar la impedanciometría de modo que otro la lea igual que tú.
:::

La impedanciometría es el único examen de la batería que **no le pide nada al paciente**: no tiene que responder, solo quedarse quieto. En unos minutos dice cómo se mueve el oído medio y si funciona el arco reflejo que une la cóclea, el tronco y el nervio facial. Por eso acompaña casi a cualquier audiometría y es muchas veces el primer examen en un niño que no coopera.

## Para qué sirve

La impedanciometría reúne tres pruebas, cada una con su pregunta:

1. **Timpanometría.** ¿Cómo se mueve el sistema tímpano-cadena y a qué presión está el oído medio? Separa el oído medio sano del ocupado, del rígido, del flácido y del que tiene presión negativa.
2. **Reflejo estapedial.** ¿Hay un arco reflejo completo entre el oído estimulado y el músculo del estribo? Ayuda a ubicar la lesión: oído medio, cóclea, VIII par, tronco o facial.
3. **Pruebas complementarias.** El **deterioro del reflejo** (sospecha retrococlear) y la **función tubaria** (¿abre la trompa de Eustaquio?).

Se pide junto con la audiometría en toda hipoacusia, en el control de la otitis media con efusión, en la sospecha de lesión retrococlear y en el lactante que no pasa el tamizaje.

Tiene un límite que conviene tener claro: **no mide audición**. Un timpanograma normal no dice que el paciente oiga bien, y un reflejo presente no reemplaza un umbral. Sus resultados se leen siempre con la otoscopía y el audiograma (BSA, 2024).

## Fundamento

### Qué mide la sonda

La sonda se sella en el conducto y lleva tres conductos: un parlante que emite un **tono de sonda** continuo, un micrófono que mide cuánto de ese tono queda en el conducto y una bomba que cambia la presión del aire. Si el tímpano se mueve con facilidad, absorbe energía y en el conducto queda poco sonido: la **admitancia** es alta. Si está rígido, el sonido rebota y la admitancia es baja. → B1.

Con el tono de **226 Hz**, el oído medio del adulto se comporta casi solo como un resorte (rigidez), y la admitancia se puede expresar como el **volumen de aire equivalente**: a esa frecuencia los mL, los cm³ y los mmho son intercambiables (BSA, 2024). Por eso el equipo informa "compliancia" en mL. En rigor es admitancia, y en un oído enfermo o de lactante las dos cosas no son iguales.

### Por qué se barre la presión

El tímpano se mueve mejor cuando la presión es la misma a los dos lados. El equipo cambia la presión del conducto, por lo general de +200 a −400 daPa, y registra la admitancia en cada punto: eso es el **timpanograma**.

- En los extremos del barrido el tímpano queda tenso y casi no se mueve. Lo que se mide ahí es solo el aire del conducto: el **volumen equivalente** del conducto.
- El **pico** aparece cuando la presión del conducto iguala a la del oído medio. Su posición en el eje horizontal **estima la presión del oído medio**, y su altura, descontado el conducto, es la **compliancia** (admitancia compensada).
- La **forma** del pico (en punta, redondeada, ancha) agrega información: un oído sano da un pico único y agudo (BSA, 2024).

### El reflejo estapedial

Un sonido intenso contrae el músculo del estribo **de los dos lados**, sea cual sea el oído estimulado. La contracción tensa la cadena y baja la admitancia: el equipo lo ve como una **deflexión** de la curva mientras dura el estímulo. El arco tiene una rama aferente (cóclea y VIII par), un relevo en el tronco (núcleo coclear y complejo olivar superior de los dos lados) y una rama eferente (núcleo y nervio facial hasta el músculo del estribo) (Borg, 1973). El capítulo 11 lo dibuja y lo desarrolla.

Con eso se entienden las dos formas de medirlo:

- **Ipsilateral**: el tono y la sonda en el mismo oído. Recorre un solo lado.
- **Contralateral**: el tono entra por un oído (con un fono) y la contracción se mide con la sonda en el otro. Recorre la vía cruzada del tronco.

## Antes de empezar

### Equipo

- **Impedanciómetro** clínico o portátil, con sonda de 226 Hz y, para lactantes, de 1000 Hz.
- **Olivas** de varios tamaños, limpias, y un fono para el estímulo contralateral.
- **Otoscopio**, alcohol y algodón; el formulario y lápices rojo y azul.
- **Verificación diaria** en las cavidades de prueba: el equipo debe leer 0,5, 2,0 y 5,0 cm³ dentro de su tolerancia, con una línea horizontal. Si la línea sube con la presión, hay una fuga. Una vez al año, calibración completa (BSA, 2024).

### Conoce tu equipo: el impedanciómetro

Todos los impedanciómetros tienen la misma lógica: una pantalla que cambia según la prueba, unas **teclas bajo la pantalla** cuya función aparece rotulada en la última línea, y unos controles fijos para elegir el oído, la sonda y la intensidad. La figura muestra el de LabSim con un timpanograma recién hecho en el oído derecho de Carolina, la paciente con otoesclerosis que vas a ver más abajo.

:::imagen /docs/manual/img/estudiante/impedanciometro-timpanograma.png El impedanciómetro de LabSim en la pantalla de timpanograma
- @55.7,34 | **La curva.** Un pico muy bajo, apenas sobre la línea de base: un oído medio rígido.
- @89.8,11 | **Compliancia** (*Compliance*): la altura del pico, ya descontado el conducto. Aquí 0,18 mL.
- @89.8,18 | **Presión** (*Pressure*): dónde cae el pico. Aquí 18 daPa, prácticamente cero.
- @89.8,25.4 | **Volumen** (*Volume*): el del conducto, 1,24 mL. Se lee en los extremos del barrido.
- @89.8,32.5 | **Gradiente** (*Gradient*): un número para la forma del pico (ver "Cómo se informa").
- @24.6,59.5 | **Teclas bajo la pantalla.** Mueven el cursor al pico (*<-- -->*) y cambian la dirección del barrido, la escala (2 cc) y los límites (−400 a 200 daPa).
- @20.3,72 | **Pruebas.** Timpanograma, Reflejos, ETF (función tubaria) y Tone Decay (deterioro del reflejo).
- @66.7,63.4 | **Leak.** Se enciende si la oliva no sella: sin sellado no hay curva que leer.
- @49.7,92.9 | **Estímulo.** Inicia el barrido; otro clic lo detiene.
- @77.5,67.5 | **Control.** El oído (*OD/OI*) y la sonda (*226 Hz* o *1000 Hz*).
:::

<!-- verificar: la captura impedanciometro-timpanograma.png es anterior al cambio de la gradiente al sentido clásico (2026-10-15) y muestra Gradient 0,26; con la app actual el As da 0,58 (como la figura de Carolina más abajo). Conviene recapturarla. -->

### Paciente

- **Otoscopía primero** (→ H1). Ella decide si se puede poner la sonda en cada oído (recuadro de abajo). Si una perforación se ve, la timpanometría no agrega nada; si no se ve bien, el volumen del conducto puede delatarla (BSA, 2024).
- **Antes de los reflejos**, pregúntale si tiene acúfeno que empeora con el ruido o molestia a los sonidos fuertes. En esos pacientes los reflejos se hacen solo si importan para el diagnóstico y con su acuerdo (BSA, 2024).
- **Instrucciones**: "Te voy a poner una gomita en el oído. Vas a sentir que se tapa y se destapa, y después vas a escuchar unos sonidos fuertes. No tienes que hacer nada: quédate quieto, sin hablar ni tragar". Muéstrale la sonda antes de ponerla y dile por qué oído empiezas.

:::ojo-ancho Cuándo no se pone la sonda (o se posterga)
La otoscopía decide, oído por oído. No se mide, o se espera y se consulta al otorrinolaringólogo, cuando hay:

- **Otorrea activa**: contraindica la timpanometría siempre (BSA, 2024).
- **Otitis media aguda** con el tímpano rojo y abombado (BSA, 2024).
- **Otitis externa aguda** o un oído que duele al tocarlo: se parte por el oído sano y el adolorido se mide solo si el resultado cambia la conducta y el paciente acepta (BSA, 2024). Lo mismo con un **herpes zóster ótico** con vesículas o costras en el conducto: duele y contamina la oliva.
- **Cuerpo extraño** en el conducto: la oliva puede empujarlo. Primero se retira (BSA, 2024).
- **Tapón de cerumen impactado** que la oliva empujaría contra el tímpano (BSA, 2024).
- **Atresia o estenosis severa** del conducto: no hay dónde sellar. Con una estenosis leve o una microtia a veces sirve una oliva tipo paraguas sobre la entrada (BSA, 2024).
- **Cirugía de oído reciente**: solo con autorización del otorrinolaringólogo; la BSA sugiere no medir en los dos meses siguientes a una cirugía de cadena o de tímpano (BSA, 2024).

En ese oído no entra **ni la sonda ni el fono** del estímulo contralateral. Por eso no se hacen sus reflejos ipsilaterales, ni los contralaterales que se registran en él, ni los contralaterales que se estimulan por él. Del oído sano solo queda su timpanograma y su ipsilateral. En el informe se escribe **"No realizable"** y el motivo, por ejemplo: "OI: no realizable por otorrea activa".
:::

<!-- verificar: el herpes zóster ótico no aparece en la lista de la BSA 2024; se agregó por la misma lógica que la otitis externa (dolor y contaminación de la oliva). -->

## Paso a paso

### 1. La oliva y el sellado

Se empieza por el **oído derecho**. Se elige una oliva que selle sin entrar a presión, se tracciona el pabellón para enderezar el conducto (hacia arriba y atrás en el adulto) y se inserta con un pequeño giro, **apuntando al tímpano** y no a la pared. Si la sonda queda contra la pared, el equipo lee un conducto diminuto y una curva plana que no es del oído (BSA, 2024). El fono del estímulo contralateral se pone en el otro oído desde el principio.

### 2. Timpanometría de 226 Hz

- El barrido parte en **+200 daPa** y baja hasta que el pico, si existe, quede bien dibujado: hasta unos −300 o −400 daPa, y −600 si hay que buscar un pico muy negativo. Más lento es más exacto (50 daPa/s o menos) (BSA, 2024).
- Mientras barre, el paciente no traga ni habla: cada movimiento deja un artefacto.
- Si la curva es plana o rara, **se repite** y se revisa que la sonda no esté tapada con cerumen.
- Anota cuatro datos: **volumen, compliancia, presión del pico y forma**.

### 3. Reflejos del mismo oído

Con la timpanometría lista, sin sacar la sonda, se buscan los reflejos **a la presión del pico**, que es donde el tímpano se mueve mejor.

- **Ipsilateral primero**, en 500, 1000, 2000 y 4000 Hz; luego **contralateral** en las mismas frecuencias más un **ruido** (de banda ancha en muchos equipos; en LabSim, NBN).
- Se parte en **80 dB** y se sube de **5 en 5** hasta ver la deflexión.
- **Criterio de presencia**: una deflexión de al menos **0,02 mL**, con la forma típica (baja al empezar el tono, vuelve al terminar). Se sube 5 dB para confirmar que **crece**, y se baja 10 para comprobar que el umbral se repite (BSA, 2024).
- **Tope**: no pasar de 105 dB HL con tonos, por riesgo para la audición que queda (BSA, 2024). En un equipo que muestra dB SPL, como el de LabSim, eso es algo más: entre 105 y 117 dB SPL según la frecuencia y el transductor (ver "El reflejo: umbral y Metz").

El **umbral del reflejo** es la menor intensidad que da una deflexión repetible.

### 4. El otro oído

Se cambia la sonda al oído izquierdo (y el fono al derecho) y se repite todo: timpanograma, ipsilaterales y contralaterales.

:::ojo Ojo clínico
En el contralateral hay **dos oídos** en juego, el que recibe el tono y el que tiene la sonda. Muchos textos nombran el reflejo por el oído **estimulado**: "contralateral derecho" es tono en el derecho y sonda en el izquierdo (BSA, 2024). Algunos equipos lo nombran por la sonda. Para no equivocarte, **anota siempre los dos**: "tono OD, sonda OI".
:::

### 5. Deterioro del reflejo

Pregunta si el reflejo **se sostiene**. Una fibra del VIII par comprimida no mantiene la descarga y la contracción se apaga aunque el tono siga (→ cap. 11).

- **Cuándo**: si hay sospecha retrococlear y el reflejo está **presente** (sin reflejo no hay qué deteriorar).
- **Cómo**: tono **10 dB sobre el umbral del reflejo**, contralateral, durante **10 segundos**, en **500 y 1000 Hz**. Sobre 1000 Hz también decaen los oídos normales, por eso no se usa (Cook y cols., 1999).
- **Instrucción**: "Vas a escuchar un sonido fuerte un rato; quédate quieto".
- **Normal**: la amplitud se mantiene; un oído sano pierde menos del 10 % a los 10 s (Rosenhall y cols., 1979).
- **Positivo**: la amplitud cae a la **mitad (50 %) o menos** dentro de los 10 s (GSI). Se anota con un signo entre paréntesis: (+) o (−).

<!-- Protocolo ORL 2019: positivo si en 500 Hz cae un tercio y en 1.000 Hz la mitad. Se corrigió a 50 % en las dos frecuencias (guía de reflejos de GSI; Rosenhall 1979 para lo normal), igual que en el capítulo 11. -->

En los tumores del VIII lo más frecuente es que el reflejo esté **elevado o ausente**; el deterioro completa el cuadro: 95 de 97 oídos con tumor tenían una de las dos alteraciones (Hirsch, 1983).

:::imagen /docs/manual/img/estudiante/impedanciometro-decay.png Deterioro del reflejo sin decaimiento
- @46.4,40 | **La contracción**: empieza en el segundo 1, cuando arranca el tono, y se mantiene plana hasta el 11.
- @88.8,20 | **Lo que queda de la amplitud inicial**: 97 % a los 5 s y 94 % a los 10 s. Perdió 6 %: **negativo**.
- @24.6,59 | **Teclas**: 500 o 1000 Hz, *Inicio*, intensidad (aquí 95 dB) e *IPSI/CONTRA*. La captura es un ipsilateral del OI; la prueba clásica es contralateral, y el equipo permite las dos.
:::

### 6. Función tubaria

La trompa de Eustaquio ventila el oído medio: se abre un instante al tragar o bostezar e iguala su presión con la de la faringe. Si no abre, el gas del oído medio se va absorbiendo por la mucosa y la presión cae (Sadé y Ar, 1997). La prueba cambia según el estado de la membrana; **cuál corresponde lo decides con la otoscopía y el timpanograma**.

**Membrana íntegra.** Se mira cuánto se corre el pico del timpanograma después de una maniobra que abre la trompa:

- **Timpanograma basal**.
- **Toynbee**: con la nariz tapada y la boca cerrada, el paciente traga 2 o 3 veces y suelta la nariz. Al repetir el timpanograma el pico se corre hacia **presiones negativas**.
- **Valsalva**: con la nariz tapada y la boca cerrada, sopla como para inflar las mejillas. El pico se corre hacia **presiones positivas**.
- Después de cada maniobra se hace un timpanograma de control. Si **vuelve a la presión inicial**, la función es **buena** (+). Si no vuelve, se le pide **tragar** varias veces (saliva o agua): si entonces vuelve, la función es **regular** (+/−); si no se mueve, es **mala** (−).

La **prueba de presión y deglución de Williams** hace lo mismo con la bomba del equipo: timpanograma de base, luego el conducto a **+400 daPa** mientras el paciente traga y timpanograma; después a **−400 daPa** y lo mismo (Williams, 1975). Si la trompa abre, el pico se corre **al lado contrario** de la presión aplicada. Los corrimientos son chicos: en sanos, la diferencia máxima entre picos tuvo una mediana de 11 daPa (rango intercuartil 6 a 17), y con disfunción tubaria de 0 daPa (0 a 2) (Lu y Wang, 2026).

**Membrana perforada o con tubo.** Ya no hay pico que mirar: la presión del conducto **es** la del oído medio. Se presuriza el conducto y se mira si la trompa la libera (**prueba de inflación-deflación**):

- Se lleva el conducto a **−200 daPa** y se le pide tragar al menos 3 veces. Si no compensa, se pide un Valsalva.
- Luego a **+200 daPa**. Una trompa buena puede liberarla sola; si no, 3 degluciones y, si tampoco, un Toynbee.
- Se informa la presión inicial y la final en cada caso, y la conclusión: buena, regular o mala.

<!-- Protocolo ORL 2019: la llamaba "Test de Bortnick". No se encontró fuente con ese nombre; el procedimiento descrito (presión en el conducto, degluciones, Valsalva/Toynbee) es la prueba de inflación-deflación (Smith y Tysome 2015; Lee y cols. 2026). -->

Ninguna prueba de función tubaria es un estándar de oro: todas miden un momento y se interpretan junto con la clínica (Smith y Tysome, 2015).

### Timpanometría de 1000 Hz en el lactante

Bajo los **6 meses de edad corregida** se usa la sonda de **1000 Hz** (BSA, 2024; Alaerts y cols., 2007). A esa edad la pared del conducto todavía es blanda y se mueve con la presión, y el oído medio pesa más en masa que en rigidez. Con 226 Hz el equipo dibuja un pico que es de la **pared del conducto**: un oído lleno de líquido puede dar un timpanograma "normal" (Kei y cols., 2003).

<!-- Protocolo ORL 2019: "se realiza en niños menores de 9 meses". La BSA 2024 y Alaerts 2007 ponen el corte en los 6 meses de edad corregida, y LabSim también. -->

- El bebé, tranquilo en brazos de su mamá o papá; idealmente dormido o comiendo. El llanto y el movimiento fabrican picos falsos.
- Barrido de +200 a −400 daPa (mejor −600), con una velocidad rápida (BSA, 2024).
- **El volumen del conducto no se lee** con 1000 Hz: no es exacto. Solo sirve para sospechar una sonda tapada (BSA, 2024).
- **Clasificación** (Baldwin, 2006, a partir de Marchant y cols., 1986): se traza una línea de base entre los extremos del barrido y se mira el pico principal. **Sobre la línea, positivo: normal. Bajo la línea o plano: anormal.** Si hay un pico positivo y uno negativo, se clasifica como normal (BSA, 2024).
- **Repetir** el trazo y comprobar que cae en la misma categoría (BSA, 2024).

:::imagen /docs/manual/img/estudiante/impedanciometro-etf.png Función tubaria con membrana íntegra
- @57.5,30 | **Tres timpanogramas superpuestos**: reposo (blanco), después de tragar a +400 (amarillo) y a −400 daPa (verde).
- @89.8,21 | **La presión de cada pico**: −18, −23 y −11 daPa. Tras +400 el pico se fue a lo negativo y tras −400 a lo positivo: la trompa **abre**. Entre −23 y −11 hay 12 daPa.
- @24.6,59 | **Teclas**: *Prueba* (íntegra o perforada), *Reposo*, *+400 trag* y *−400 trag*.
:::

### En operativos

En un operativo de screening (colegio, jardín, faena) se hace la **timpanometría** con la misma técnica, sin reflejos, y se imprime el resultado. El objetivo no es diagnosticar, sino decidir a quién derivar. En niños, la ASHA deriva con una compliancia bajo 0,2 a 0,3 mL, un pico demasiado ancho (más de 200 a 235 daPa a media altura) o un timpanograma plano con volumen sobre 1,0 mL (ASHA, 1997).

:::ayuda Ayuda memoria
- Otoscopía → sonda en el **OD** → timpanograma → reflejos del mismo oído → OI.
- Timpanograma: **volumen, compliancia, presión, forma**.
- Reflejos: **a la presión del pico**, ipsi y contra, 500-4000 Hz (+ ruido en contra), desde 80 dB de 5 en 5; presencia ≥ 0,02 mL que crece.
- Deterioro: +10 dB sobre el umbral, 10 s, 500 y 1000 Hz; **positivo si cae a la mitad**.
- Trompa: Toynbee y Valsalva (o Williams) con membrana íntegra; −200/+200 daPa y degluciones con perforación.
- Bajo 6 meses: **1000 Hz**; pico sobre la línea de base = normal.
:::

## Cómo se informa

### El timpanograma: tipos de Jerger

En Chile el timpanograma se clasifica con las letras de Jerger (1970). La letra resume, pero sola puede confundir a quien recibe el informe: la BSA recomienda escribirla **junto con los tres números** (volumen, compliancia y presión) y una descripción de la forma (BSA, 2024).

:::ayuda-ancho Tipos de timpanograma (226 Hz, adulto)
| Tipo | Pico | Compliancia | Presión del pico | Se ve en |
|---|---|---|---|---|
| **A** | único y agudo | 0,3 a 1,6 mL | entre −100 y +100 daPa | oído medio sano |
| **As** | bajo | menos de 0,3 mL | normal | otoesclerosis, timpanoesclerosis |
| **Ad** | alto | más de 1,6 mL | normal | disyunción de cadena, tímpano flácido o cicatricial |
| **C** | desplazado | normal | más negativa que −100 daPa | presión negativa, disfunción tubaria |
| **B** | **no hay pico** | — | — | efusión, perforación, sonda tapada |

La compliancia normal es la del 90 % de los adultos (BSA, 2024); en niños de 5 a 7 años va de 0,2 a 1,0 mL. En adultos, presiones hasta −100 daPa tienen poca importancia por sí solas, y en niños hasta −150 daPa (BSA, 2024). LabSim agrega el **Cs**: pico bajo y negativo, la rigidez de una retracción con líquido incipiente.
:::

<!-- Protocolo ORL 2019: "Curva B: peak entre -600 y -200 daPa y menor a 0,3 cc". La curva B no tiene pico: es plana (Jerger 1970; BSA 2024). Un pico bajo y muy negativo se informa como C (o Cs) con su presión. -->

### Un timpanograma plano: mira el volumen

Ante una curva **B**, el volumen del conducto es el que dice qué pasa (BSA, 2024):

- **Volumen normal**: la sonda está frente a un tímpano íntegro que no se mueve. Lo habitual es **líquido** en el oído medio.
- **Volumen alto** (en el adulto, sobre unos 3,6 mL y distinto del otro oído): se está midiendo el conducto **más el oído medio**. Hay una **perforación** o un tubo de ventilación permeable.
- **Volumen muy bajo**: la sonda está tapada con cerumen o apoyada en la pared, o un tapón de cerumen cierra el conducto y la sonda mide solo el aire que queda hasta él (→ cap. 1). Se corrige y se repite; con un tapón, primero se resuelve el conducto.

El rango del volumen en adultos es de 0,6 a 2,2 mL; en niños de 5 a 7 años, de 0,7 a 1,3 mL. Más que el número aislado, cuenta la **diferencia entre los dos oídos** (BSA, 2024).

### La gradiente

La gradiente es un número para la forma del pico. Se unen con una recta los dos puntos de la curva que están a 50 daPa de cada lado del pico, y se mide cuánto **sobresale el pico** por encima de esa recta, como fracción de su altura (Brooks, 1968): **cerca de 1, la curva es en punta; cerca de 0, ancha y redondeada**, y una curva plana da 0. En LabSim, el recuadro amarillo que el equipo dibuja sobre el pico mide 100 daPa de ancho y lo que el pico tiene de alto: la gradiente es la parte de su altura que queda por encima de la curva en los bordes del recuadro. En las figuras de este capítulo, el Ad da 0,68, la A 0,58 y la C 0,50.

<!-- Brooks 1968: datos verificados en Crossref; el texto completo no se leyó. La fórmula (pico sobre la recta a ±50 daPa, dividida por la altura) es la forma de cociente con que se enseña (ver Bibliografia.php, BROOKS1968). -->

No todos los equipos la calculan igual, así que antes de comparar con una tabla averigua cómo la calcula el tuyo. Por eso hoy se prefiere el **ancho timpanométrico** (TW): el ancho del pico, en daPa, a la mitad de su altura. De ocho formas de medir la forma del pico, fue la que se prefirió (Koebsell y Margolis, 1986). En niños de 1 a 7 años, un TW bajo 200 daPa se considera normal (Nozza y cols., 1994).

### El reflejo: umbral y Metz

En adultos con audición normal, el reflejo con tonos de 500 a 2000 Hz aparece entre **75 y 95 dB HL**; el contralateral sale 2 a 5 dB más alto que el ipsilateral, y el ruido de banda ancha unos 20 dB más bajo que los tonos (BSA, 2024; Wiley y cols., 1987). El de 4000 Hz puede faltar en oídos normales, y alrededor del 5 % de los adultos no tiene reflejos sin que haya patología (Golding y cols., 2007).

En una **hipoacusia coclear** el reflejo no sube en proporción a la pérdida: sigue apareciendo cerca de su nivel normal mientras la pérdida no pase de unos 50 dB HL, y suele faltar desde los 60 dB HL (Gelfand y cols., 1990). Por eso, en un oído coclear, la distancia entre el umbral tonal y el umbral del reflejo **se achica**. Cuando esa distancia es **menor de 60 dB**, se habla de **fenómeno de Metz**, y es un signo de reclutamiento (Jerger y cols., 1972; BSA, 2024). Ejemplo: umbral de 50 dB HL en 1 kHz y reflejo a 90 dB HL: 40 dB de distancia, Metz presente.

<!-- Protocolo ORL 2019: Metz "a intensidades iguales o menores a 60 dB sobre el umbral". La BSA 2024 dice "menos de 60 dB SL"; se dejó el criterio de la guía. -->

En nuestro laboratorio, el umbral del reflejo se **anota en dB SPL**, y así lo muestran el equipo y la ficha de LabSim. La razón es que el reflejo responde a la energía que realmente llega al oído, y lo que el equipo controla dentro de un conducto sellado, sobre todo en el ipsilateral, donde el tono sale de la misma sonda, es una presión sonora.

Para pasar de dB HL a dB SPL se suma la **corrección del transductor** que suena (su nivel de referencia, el RETSPL). En el ipsilateral el tono sale de la sonda; en el contralateral, de un fono supraaural, que necesita más presión para el mismo dB HL (Interacoustics, AT235):

| Corrección (dB) | 500 Hz | 1000 Hz | 2000 Hz | 4000 Hz |
|---|---|---|---|---|
| Ipsilateral (sonda) | 5,5 | 0 | 3 | 5,5 |
| Contralateral (fono TDH39) | 11,5 | 7 | 9 | 9,5 |

Por eso un oído sano de LabSim da el ipsilateral en **90, 85, 90 y 90 dB SPL** y el contralateral en **95, 90, 95 y 95 dB SPL**, y el ruido contralateral en 95: es el mismo reflejo de unos 85 dB HL, con la corrección de cada transductor y redondeado a 5 dB, el paso del dial. Para el **Metz**, resta primero la corrección: un contralateral a 95 dB SPL en 500 Hz son 83,5 dB HL, y es ese número el que se compara con el umbral tonal.

:::comentario Lo que dicen las normas
La BSA prefiere expresar el estímulo del reflejo en **dB HL** y acepta dB SPL, siempre que se apliquen las correcciones para comparar con los valores normales (BSA, 2024). Las tablas de normalidad que se citan arriba (Wiley y cols., 1987; Gelfand y cols., 1990) y el cálculo de Metz están en dB HL: el umbral del reflejo se resta del umbral tonal, y los dos tienen que estar en la misma escala. El tope de 105 dB HL que recomienda equivale, con las correcciones de la tabla, a 105 a 110,5 dB SPL en el ipsilateral y a 112 a 116,5 dB SPL en el contralateral. El dial de LabSim llega a 120 dB SPL: el tope lo pones tú.
:::

### Patrones de reflejo

Una tabla de reflejos se lee **por oído estimulado y por oído con sonda**. Cada patrón señala una parte del arco (Jerger y Jerger, 1977; BSA, 2024):

:::ayuda-ancho Patrones de reflejo
| Patrón | Qué falla | Dónde está el problema |
|---|---|---|
| **Normal** | nada: reflejo en todas las casillas | arco completo |
| **L invertida** | los dos con la **sonda** en el oído enfermo, y el contralateral con el **tono** en ese oído (elevado o ausente) | **oído medio** de ese lado: la sonda no ve la contracción y el tono llega más débil |
| **Diagonal** | todo lo que se **estimula** por un oído (su ipsi y el contra con tono en ese oído) | **aferente**: cóclea muy dañada o VIII par de ese oído |
| **Vertical** | todo lo que se **registra** en un oído (su ipsi y el contra con sonda en ese oído) | **eferente**: nervio facial o músculo de ese lado |
| **Horizontal** | los dos contralaterales; ipsis normales | **tronco**, en el cruce de la vía |
| **Unibox** | una sola casilla | el menos específico; se interpreta con el resto de la batería |

Un oído medio enfermo **borra el reflejo cuando tiene la sonda**, aun con una pérdida conductiva leve (BSA, 2024; Jerger y cols., 1974).
:::

<!-- verificar: el protocolo asocia el patrón unibox a "alteraciones antes del entrecruzamiento (COS)" y la L invertida a transmisión mayor de 30 dB. No se encontró en las fuentes revisadas una definición del unibox con sitio de lesión; Jerger y Jerger 1977 describe los patrones, pero no se pudo leer el texto completo. -->

## Lectura en pacientes

El **patrón diagonal** es el de Raúl, el paciente con schwannoma del capítulo 11 (paciente de práctica 39): falla todo lo que se estimula por el OD, mientras que con el tono en el OI y la sonda en el OD el reflejo aparece a su nivel normal (90 a 95 dB SPL). Con solo 15 dB de pérdida en 1 kHz, no es la cóclea: es el VIII par. Una cófosis derecha (paciente de práctica 42) da el mismo patrón.

### La forma de la curva del reflejo

Además del umbral, mira la **forma** de la deflexión. La normal baja al empezar el tono y se mantiene hasta que termina. En el efecto **ON-OFF** aparece una deflexión breve al **comienzo** y otra al **final** del tono, en sentido contrario o sin la meseta del medio. Es muy frecuente en la **otoesclerosis incipiente** (Camicas, 1992) y se ve también en la disyunción de cadena y en algunas sensorioneurales, como la enfermedad de Ménière (Debruyne, 1992). Puede ser parcial o completo y, al avanzar la otoesclerosis, el reflejo termina por desaparecer (Colletti y Fiorino, 1987).


{{caso h7_p34}}

:::figura h7_p34 timpanograma
- @OD pico | **Tipo As**: pico en su lugar (18 daPa) pero de solo 0,18 mL, con volumen normal (1,24 mL). Es el oído de la captura del equipo.
- @OI pico | El OI es A (1,41 mL): la diferencia entre los dos oídos es el hallazgo.
:::

:::figura h7_p34 reflejos
- @ipsi OD 1000 | Con la sonda en el OD rígido faltan el ipsilateral y el contralateral que se registra ahí, aunque el tono entre por el OI sano.
- @contra OI 2000 | Con el **tono en el OD** el reflejo sube lo que pierde en el oído medio: 110 dB SPL en 2 kHz, 120 en 4 kHz, y ausente en 500 y 1000 Hz, donde el gap es de 45 dB.
- @ipsi OI 1000 | Solo el ipsilateral del OI sale normal. Tres filas alteradas en torno al OD: **L invertida**, conductivo.
:::

#### Un ejemplo de informe: Carolina

> **Impedanciometría.** OD: timpanograma tipo As (volumen 1,24 mL, compliancia 0,18 mL, presión 18 daPa). Reflejos ipsilaterales ausentes; contralaterales con sonda OD ausentes. OI: timpanograma tipo A (volumen 1,03 mL, compliancia 1,41 mL, presión −2 daPa). Reflejos ipsilaterales presentes a 90, 85, 90 y 90 dB SPL (500 a 4000 Hz); contralaterales con tono en OD ausentes en 500, 1000 Hz y ruido, presentes a 110 dB SPL en 2 kHz y 120 dB SPL en 4 kHz. Patrón de L invertida en torno al OD, compatible con alteración de oído medio derecho.

El informe describe; el diagnóstico lo hace el médico. En el formulario se dibuja la curva con el color de cada oído y se escriben al lado los números.

{{caso h7_p35}}

:::figura h7_p35 timpanograma
- @OD pico | **Tipo B** en el OD: no hay pico, la presión es indeterminada.
- @OI pico | El OI es igual: plano.
- Los volúmenes son de 0,42 y 0,70 mL, pequeños y propios de un conducto infantil: la sonda está frente a un tímpano cerrado. Plano con volumen normal es **efusión**, lo que calza con los tímpanos opacos con nivel líquido de la otoscopía.
:::

{{caso h7_retraccion}}

:::figura h7_retraccion timpanograma
- @OD pico | **Tipo C**: el pico tiene altura normal (1,39 mL) pero está corrido a −167 daPa. El oído medio está a presión negativa.
- @OI pico | El OI es A, con el pico cerca de cero.
- La gradiente del OD (0,50) es más baja que la del OI (0,58): su curva es más ancha.
:::

{{caso h7_disyuncion}}

:::figura h7_disyuncion timpanograma
- @OD pico | **Tipo Ad**: un pico de 1,97 mL, casi al tope de la escala, en −43 daPa. Sin la cadena que lo frene, el tímpano se mueve de más.
- @OI pico | El OI es A (1,46 mL): el OD tiene un pico más alto que el oído sano.
- La curva del OD es la más en punta de este capítulo: gradiente 0,68, la más alta. Con un gap aéreo-óseo de 50 a 60 dB, un Ad orienta a **disyunción de la cadena** (Lidén y cols., 1974).
:::

{{caso h7_lactante}}

:::figura h7_lactante timpanograma
- @OD pico | Con **226 Hz**, el OD dibuja un pico de 1,63 mL a −90 daPa. Parece un A.
- @OI pico | El OI también parece normal.
- A los 2 meses este pico es de la **pared del conducto**. No descarta nada.
:::

:::figura h7_lactante timpanograma 2
- @OD pico | Con la sonda de **1000 Hz**, el OD queda **plano**: no hay pico sobre la línea de base. Es un resultado **anormal**: el oído medio está ocupado.
- @OI pico | El OI tiene un pico claro sobre la línea de base: **positivo**, normal.
- Con 1000 Hz no se informa el volumen ni la compliancia en mL: solo si el pico está sobre o bajo la línea de base.
:::

## Errores frecuentes

- **Saltarse la otoscopía.** Se mete la sonda contra un tapón o en un oído con secreción.
- **Sonda contra la pared.** Volumen diminuto y curva plana: parece una B y es un error de colocación.
- **Leer la B sin el volumen.** Efusión y perforación dan la misma curva; solo el volumen las separa.
- **Paciente que traga o habla** durante el barrido o los reflejos: picos y deflexiones falsas.
- **Confundir el artefacto con un reflejo.** En el ipsilateral el tono sale de la misma sonda y a intensidades altas produce cambios que no son contracción. Por eso se exige que la deflexión crezca al subir 5 dB y se repita (BSA, 2024).
- **Restar el reflejo al umbral en escalas distintas** (SPL contra HL) para el Metz.
- **Confundir el ON-OFF con el deterioro.** El ON-OFF es una forma de la curva que habla del oído medio; el deterioro es una contracción que no se sostiene 10 s, y habla del nervio.
- **Usar 226 Hz bajo los 6 meses.** El timpanograma "normal" de un lactante con efusión es el error clásico.

:::ojo Ojo clínico
Antes de informar, haz calzar la impedanciometría con el audiograma. Un oído con reflejo ipsilateral presente **no debería tener un gap** importante: si lo tiene, revisa la vía ósea o piensa en una tercera ventana, como la dehiscencia del canal semicircular superior, que da gap con el reflejo conservado (BSA, 2024). Y un timpanograma normal no explica una hipoacusia conductiva.
:::

## En LabSim

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

:::pregunta Preguntas para practicar
1. Un adulto tiene un timpanograma plano en el OI con un volumen de 4,2 mL, y en el OD un tipo A con 1,1 mL. ¿Qué esperas ver en la otoscopía? ¿Qué prueba de función tubaria le harías?
2. En Carolina, ¿por qué el reflejo contralateral con tono en el OD aparece en 2 kHz y no en 500 Hz? Mira su audiograma en H3.
3. Un paciente con parálisis facial derecha y audición normal: dibuja su tabla de reflejos. ¿En qué se parece y en qué se diferencia del patrón de Raúl?
4. Un paciente tiene un umbral de 55 dB HL en 2 kHz y un reflejo a 95 dB HL. ¿Hay fenómeno de Metz? ¿Qué te sugiere sobre el sitio de lesión?
5. Si a Sara le hubieras hecho solo la timpanometría de 226 Hz, ¿qué habrías informado? ¿Qué consecuencia tendría para su seguimiento?
:::

## Referencias

### Técnica

1. British Society of Audiology. Recommended procedure: tympanometry and acoustic reflex thresholds [Internet]. BSA; 2024 Feb (enmiendas menores feb 2025 y mar 2026) [citado 2026 oct 15]. Disponible en: https://www.thebsa.org.uk/wp-content/uploads/2026/03/BSA-Recommended-Procedure-Tympanometry-Acoustic-Reflex-Thresholds-March-2026-minor-revision.pdf
1. American Speech-Language-Hearing Association. Guidelines for audiologic screening [Guidelines]. Rockville (MD): ASHA; 1997. doi:10.1044/policy.GL1997-00199
1. Jerger J. Clinical experience with impedance audiometry. Arch Otolaryngol. 1970;92(4):311-24. doi:10.1001/archotol.1970.04310040005002
1. Brooks DN. An objective method of detecting fluid in the middle ear. Int Audiol. 1968;7(3):280-6. doi:10.3109/05384916809074333
1. Koebsell KA, Margolis RH. Tympanometric gradient measured from normal preschool children. Audiology. 1986;25(3):149-57. doi:10.3109/00206098609078381
1. Lidén G, Harford E, Hallén O. Tympanometry for the diagnosis of ossicular disruption. Arch Otolaryngol. 1974;99(1):23-9. doi:10.1001/archotol.1974.00780030027005
1. Nozza RJ, Bluestone CD, Kardatzke D, Bachman R. Identification of middle ear effusion by aural acoustic admittance and otoscopy. Ear Hear. 1994;15(4):310-23. doi:10.1097/00003446-199408000-00005
1. Jerger J, Jerger S, Mauldin L. Studies in impedance audiometry. I. Normal and sensorineural ears. Arch Otolaryngol. 1972;96(6):513-23. doi:10.1001/archotol.1972.00770090791004
1. Jerger J, Anthony L, Jerger S, Mauldin L. Studies in impedance audiometry. 3. Middle ear disorders. Arch Otolaryngol. 1974;99(3):165-71. doi:10.1001/archotol.1974.00780030173003
1. Jerger S, Jerger J. Diagnostic value of crossed vs uncrossed acoustic reflexes: eighth nerve and brain stem disorders. Arch Otolaryngol. 1977;103(8):445-53. doi:10.1001/archotol.1977.00780250039002
1. Wiley TL, Oviatt DL, Block MG. Acoustic-immittance measures in normal ears. J Speech Hear Res. 1987;30(2):161-70. doi:10.1044/jshr.3002.161
1. Gelfand SA, Schwander T, Silman S. Acoustic reflex thresholds in normal and cochlear-impaired ears: effects of no-response rates on 90th percentiles in a large sample. J Speech Hear Disord. 1990;55(2):198-205. doi:10.1044/jshd.5502.198
1. Interacoustics A/S. AT235 / AT235h impedance audiometer: technical specifications (tabla 2, valores de referencia del estímulo) [Internet]. Consultada 2026-10-15. Disponible en: https://doc.es.aau.dk/fileadmin/doc/labs_facillities/acoustics/man/AT235/Spec_AT235.pdf
1. Golding M, Doyle K, Sindhusake D, Mitchell P, Newall P, Hartley D. Tympanometric and acoustic stapedius reflex measures in older adults: the Blue Mountains Hearing Study. J Am Acad Audiol. 2007;18(5):391-403. doi:10.3766/jaaa.18.5.4
1. Grason-Stadler (GSI). Acoustic Reflex Testing (guía de pruebas). Consultada 2026-10-09. Disponible en: https://grason-stadler.com/education/guides/acoustic-reflexes
1. Cook RD, Ferguson MO, Hall JW 3rd, Grose JH, Pillsbury HC. The effects of amplitude modulation on acoustic reflex decay. Audiol Neurootol. 1999;4(2):104-13. doi:10.1159/000013827
1. Rosenhall U, Lidén G, Nilsson E. Stapedius reflex decay in normal hearing subjects. J Am Audiol Soc. 1979;4(4):157-62.
1. Hirsch A. The stapedius reflex tests in retrocochlear hearing disorders. Audiology. 1983;22(5):463-70. doi:10.3109/00206098309072807
1. Debruyne F. Clinical observations on the on-off effect of the acoustic stapedius reflex. Clin Otolaryngol Allied Sci. 1992;17(1):10-2. doi:10.1111/j.1365-2273.1992.tb00979.x
1. Camicas M. Interprétation acoustique et mécanique de l'effet «on-off». Rev Laryngol Otol Rhinol (Bord). 1992;113(4):355-8.
1. Colletti V, Fiorino FG. Stapedius reflex in the monitoring of NaF treatment of subclinical otosclerosis. Acta Otolaryngol. 1987;104(5-6):447-53.

### Función tubaria

1. Williams PS. A tympanometric pressure swallow test for assessment of eustachian tube function. Ann Otol Rhinol Laryngol. 1975;84(3 Pt 1):339-43. doi:10.1177/000348947508400309
1. Lu CY, Wang JJ. Functional assessment beyond type A tympanograms: pressure-swallow testing for chronic Eustachian tube dysfunction in a Taiwanese cohort. Diagnostics (Basel). 2026;16(17):2738. doi:10.3390/diagnostics16172738
1. Lee DH, Heo Y, Na HS, Lee S, Oh SJ, Choi SW. Clinical utility of modified inflation-deflation test in Eustachian tube function testing. Diagnostics (Basel). 2026;16(16):2534. doi:10.3390/diagnostics16162534
1. Smith ME, Tysome JR. Tests of Eustachian tube function: a review. Clin Otolaryngol. 2015;40(4):300-11. doi:10.1111/coa.12428

### Lactante

1. Kei J, Allison-Levick J, Dockray J, Harrys R, Kirkegard C, Wong J, et al. High-frequency (1000 Hz) tympanometry in normal neonates. J Am Acad Audiol. 2003;14(1):20-8. doi:10.3766/jaaa.14.1.4
1. Baldwin M. Choice of probe tone and classification of trace patterns in tympanometry undertaken in early infancy. Int J Audiol. 2006;45(7):417-27. doi:10.1080/14992020600690951
1. Marchant CD, McMillan PM, Shurin PA, Johnson CE, Turczyk VA, Feinstein JC, et al. Objective diagnosis of otitis media in early infancy by tympanometry and ipsilateral acoustic reflex thresholds. J Pediatr. 1986;109(4):590-5. doi:10.1016/s0022-3476(86)80218-9
1. Alaerts J, Luts H, Wouters J. Evaluation of middle ear function in young children: clinical guidelines for the use of 226- and 1,000-Hz tympanometry. Otol Neurotol. 2007;28(6):727-32. doi:10.1097/mao.0b013e3180dca1e5

### Fisiología

1. Borg E. On the neuronal organization of the acoustic middle ear reflex. A physiological and anatomical study. Brain Res. 1973;49(1):101-23. doi:10.1016/0006-8993(73)90404-6
1. Sadé J, Ar A. Middle ear and auditory tube: middle ear clearance, gas exchange, and pressure regulation. Otolaryngol Head Neck Surg. 1997;116(4):499-524. doi:10.1016/S0194-5998(97)70302-4
