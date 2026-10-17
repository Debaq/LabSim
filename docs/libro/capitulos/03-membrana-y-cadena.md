# 3. Membrana y cadena

:::objetivos En este capítulo
- Explicar qué aportan la membrana y la cadena a la audición, y por qué cada lesión deja un gap de tamaño y forma distintos.
- Leer la forma del gap: mayor en los graves (rigidez, perforación), plano y grande (cadena interrumpida) o mayor en los agudos (cadena dañada a medias).
- Reconocer una perforación por el volumen del conducto y elegir la prueba de función tubaria de membrana perforada.
- Separar un timpanograma As de un Ad, y un Ad con gap grande (cadena suelta) de uno sin gap (membrana cicatricial).
- Decidir cuándo una conductiva se controla, cuándo va a cirugía y cuándo hay que derivar sin esperar.
:::

El capítulo anterior trató de un oído medio que se llena de aire viciado y de líquido. Este trata de su estructura: la membrana que recibe el sonido y la cadena de huesecillos que lo lleva hasta la cóclea. Una membrana perforada, endurecida por placas o empujada por una masa, y una cadena suelta, fracturada o comida por un colesteatoma, dan todas una hipoacusia conductiva. Pero no la misma. El tamaño del gap, su forma a lo largo de las frecuencias y lo que hace el timpanograma permiten ubicar el problema con bastante precisión, y a veces dicen que hay que apurarse.

## Técnica en foco

Las herramientas son las mismas del capítulo 2: la **audiometría con vía ósea** (→ H3), la **impedanciometría** (→ H7) y la **acumetría** (→ H2). Lo nuevo es qué mirar en cada una.

### El gap: tamaño y forma

Con la ósea normal, todo lo que la aérea pierde es transmisión (→ H3). En un oído medio estructural interesan tres cosas del gap:

- **Cuánto mide.** Un oído medio con la membrana entera y la cadena cortada pierde unos 50 a 60 dB: es la conductiva más grande posible (Merchant y cols., 1998). Ninguna perforación ni placa llega ahí por sí sola. Un gap de 50 dB o más con la membrana entera apunta a la cadena.
- **Qué forma tiene.** Mayor en los graves y más chico en los agudos (configuración ascendente), plano, o mayor en los agudos. Cada forma habla de un mecanismo distinto (ver *Fisiología*).
- **El grado.** Se calcula igual que siempre, con el promedio BIAP de 500 a 4.000 Hz por vía aérea (→ H3). Una conductiva pura casi nunca pasa de moderada.

La ósea del oído enfermo se mide enmascarada (→ H4). En la acumetría (→ H2), el **Weber** se va al oído con gap y el **Rinne** se hace negativo en él.

### El timpanograma de la membrana y la cadena

En el capítulo 2 la pregunta era si la caja tenía aire. Aquí es **cuánto se deja mover** el sistema, y eso lo dice la compliancia:

- **As**: el pico está en su lugar, pero es bajo. El sistema está **rígido**: placas de timpanoesclerosis, una masa que se apoya en la membrana o la cadena, o un estribo fijo (→ cap. 4).
- **Ad**: el pico es muy alto, a veces se sale de la escala. El sistema está **laxo**. Hay dos causas, y el audiograma las separa: una **cadena suelta** (gap grande) o una **membrana cicatricial** delgada (monomérica), que se mueve mucho aunque la cadena esté sana (gap chico o nulo) (Lidén y cols., 1974; Jerger y cols., 1974). Comparada con un estribo fijo, la disyunción da más compliancia y más gap en 2 kHz (Cheon y cols., 2023).
- **B con volumen alto**: la sonda mide el conducto **más** la caja y la mastoides. Hay una **perforación** (o un tubo permeable). En el adulto, un volumen de 3,6 mL o más, distinto del otro oído, sugiere perforación (BSA, 2024).

:::ojo Ojo clínico
Una **perforación seca se mide**: da su B con volumen alto y su función tubaria. Lo que no se hace es meter la sonda en un oído **con secreción**: es impedanciometría **no realizable** (NR) y, en LabSim, intentarla es una falta grave que deja el equipo fuera de uso el resto de la atención. Lo decide la otoscopía, no la curva.
:::

:::comentario Lo que dicen las normas
La BSA (2024) no recomienda hacer timpanometría cuando la perforación se ve en la otoscopía: no agrega nada al diagnóstico, y su utilidad está en los oídos donde la membrana no se ve bien. En este libro y en LabSim **se hace igual**, a propósito: el volumen alto de una perforación que sí ves es lo que te va a permitir reconocerla el día que no la veas, y con esa misma sonda se hace la función tubaria de membrana perforada, que el otorrino pide antes de operar.
:::

### La función tubaria con membrana perforada

Con una perforación no hay timpanograma que correr: el conducto y la caja son una sola cavidad. Se lleva esa cavidad a una presión (en LabSim, por ejemplo, −200 daPa) y el paciente traga tres veces. Si la trompa abre, cada deglución deja escapar parte de la presión y el trazo sube por escalones hacia 0; si no abre, queda plano. Es la prueba de inflación-deflación (Smith y Tysome, 2015). En 192 oídos perforados, 117 tenían la trompa normal (Lee y cols., 2026): la mayoría de las perforaciones ventilan bien.

<!-- Protocolo ORL 2019: llamaba a esta prueba "Test de Bortnick". No se encontró fuente con ese nombre; el procedimiento descrito (presurizar a -200 y +200 daPa, tragar, Valsalva o Toynbee si no compensa) es la prueba de inflación-deflación (Smith y Tysome 2015; Lee y cols. 2026). Mismo criterio que el capítulo 2. -->

:::imagen /docs/manual/img/estudiante/impedanciometro-etf-perforada.png ancho=60% La función tubaria con membrana perforada en LabSim
- @62,40 | **Cada deglución sube la presión un escalón**, de −200 daPa hacia 0: la trompa se abrió y dejó salir parte de la presión.
- @86,24 | **Inicial y final**: −200 y −10 daPa. Si la trompa no abre, la presión no se mueve.
- @22,70 | **ETF** abre la pantalla; **Prueba** cambia a membrana perforada; la **perilla** elige la presión e **Inicio** lanza los 10 segundos.
:::

### Los reflejos

Con una lesión del oído medio el reflejo falla por los dos lados (Jerger y cols., 1974):

- **Con la sonda en el oído enfermo** no se registra. El estapedio se contrae, pero una membrana perforada, rígida o con la cadena suelta no transmite ese cambio a la sonda. Basta un gap chico.
- **Con el tono en el oído enfermo** el umbral sube lo que mide el gap, y con un gap grande no aparece.

En una conductiva unilateral suele quedar solo el ipsilateral del oído sano, más el contralateral con el tono en el oído enfermo en las frecuencias donde el gap es menor.

## Fisiología

### Para qué sirve el oído medio

El sonido viaja por el aire y la cóclea está llena de líquido. Si el aire empujara el líquido directamente, casi toda la energía rebotaría. El oído medio **adapta las impedancias**: junta la presión que recibe la membrana, que es grande, sobre la platina del estribo, que es chica, y la multiplica (Merchant y cols., 1998).

- **La relación de áreas.** La parte vibrante de la membrana tiene unas 17 veces el área de la platina. La misma fuerza sobre un área menor es más presión.
- **La palanca de la cadena.** El mango del martillo es algo más largo que la apófisis larga del yunque: la cadena gana un poco más, cerca de 1,3 veces.

<!-- verificar: 17:1 y 1,3:1 son los valores clásicos (Wever y Lawrence, 1954), citados por Merchant 1998; se tomaron de fuentes secundarias. -->

La cuenta teórica da unos 25 a 30 dB; lo medido en huesos temporales es menor, unos 20 dB, con el máximo cerca de 1 kHz (Aibara y cols., 2001). Además, la membrana entera **protege la ventana redonda**: el sonido empuja la cóclea por la ventana oval y no por las dos ventanas a la vez, donde se anularía.

Eso explica las dos lesiones extremas:

- **Cadena cortada con la membrana entera**: no hay transformador y la membrana además tapa el paso directo del sonido a las ventanas. Es la pérdida máxima, de 50 a 60 dB (Merchant y cols., 1998).
- **Perforación**: lo que se pierde no es tanto superficie como **diferencia de presión** entre las dos caras de la membrana, porque el sonido entra también a la caja por el agujero. Por eso el gap crece con el **tamaño** de la perforación, es mayor en los **graves**, es 10 a 20 dB mayor cuando la caja y la mastoides tienen poco aire, y casi no depende de **dónde** está el agujero (Mehta y cols., 2006).


### Rigidez y masa

El sistema tímpano-cadena se comporta como un resorte con peso. La **rigidez** frena sobre todo los **graves**; la **masa**, sobre todo los **agudos**. De ahí la forma del gap:

- **Más rigidez** (placas de timpanoesclerosis, estribo fijo, presión negativa): gap mayor en los graves, curva As.
- **Más masa o una unión floja**: gap mayor en los agudos. Una cadena **fracturada a medias**, unida por tejido fibroso, todavía mueve los graves, que arrastran la cadena entera, pero no sigue a los agudos. Un gap en 4 kHz 10 dB o más mayor que el de 250-500 Hz predijo una discontinuidad incompleta con una sensibilidad de 83 % y una especificidad de 92 % (Sarmento y cols., 2017; Farahmand y cols., 2016).
- **Cadena cortada del todo**: no pasa nada a ninguna frecuencia. El gap es grande y **plano**, o algo mayor en los graves (Farahmand y cols., 2016).

### Cómo llega la vía ósea

El vibrador no "se salta" el oído medio del todo. La cóclea recibe la vibración del cráneo por varios caminos a la vez: el sonido que el hueso irradia al conducto, la inercia de la cadena, la inercia de los líquidos del oído interno, la compresión de la cápsula ótica y el paso por el líquido cefalorraquídeo (Stenfelt y Goode, 2005). Por eso una lesión del oído medio puede mover un poco la ósea: la cadena fija pierde su componente de inercia y aparece la muesca de Carhart (→ cap. 4). En las lesiones de este capítulo la ósea queda normal, salvo cuando el daño llega a la cóclea.

## Patología

### Perforación timpánica

Viene de la **otitis media crónica** o de un **trauma** (una bofetada, un cotonito, una explosión). La traumática suele cerrarse sola en semanas; la crónica, no, y supura cuando entra agua o con un resfrío.

La pérdida es conductiva, mayor en los graves y proporcional al tamaño del agujero (Mehta y cols., 2006). Una perforación chica da un gap pequeño; una subtotal puede dar 40 o 50 dB en los graves. Si el gap es **mucho mayor** de lo que explica el tamaño, la cadena también está dañada. El tratamiento es quirúrgico y lo decide el otorrino: la **timpanoplastia** cierra la membrana y, si hace falta, reconstruye la cadena. Antes de operar se pide la audiometría y la función tubaria.

### Timpanoesclerosis y miringoesclerosis

Son depósitos de colágeno hialinizado y calcio que quedan después de inflamaciones repetidas del oído medio y de los tubos de ventilación. En la otoscopía se ven como **placas blancas**, a menudo en herradura.

- **Miringoesclerosis**: las placas están solo en la membrana. Casi nunca dan pérdida: en un modelo de la membrana, la placa aislada cambió el movimiento del umbo, pero no el de la platina (Gentil y cols., 2014).
- **Timpanoesclerosis**: las placas llegan a la caja y a la cadena. Rigidizan el sistema y dan un gap **mayor en los graves**, casi siempre bajo 40 dB (83 % de los casos limitados a la membrana; Kaur y cols., 2006), con curva As. Cuando fija el estribo, el gap puede pasar de 40 dB. La cirugía mejora sobre todo 0,5 a 2 kHz (Stankovic, 2009).

### Disyunción y fractura de cadena

La causa principal es el **traumatismo encefalocraneano** con fractura del temporal. La fractura que **respeta la cápsula ótica** (la "longitudinal" de la clasificación antigua) pasa por el oído medio: sangre detrás de la membrana (hemotímpano), a veces un desgarro de la membrana o del conducto, y una pérdida **conductiva**. La que **viola la cápsula** cruza el laberinto y da una pérdida sensorioneural profunda unas siete veces más seguido (Dahiya y cols., 1999).

En las fracturas que respetan la cápsula el gap es mayor en los graves, con un valle en 2 kHz, y es mayor cuando la cadena está comprometida (Kim y cols., 2016). La mayoría se recupera sola: en una serie, el gap bajó de 27 dB a las tres semanas a 20 dB a los casi tres meses, sin cirugía (Song y cols., 2017). Lo que **no se recupera** cuando se reabsorbe la sangre es la cadena:

- **Disyunción**: la cadena se desarticula, casi siempre entre el yunque y el estribo. Gap grande (45 a 60 dB) y plano, membrana íntegra, curva **Ad** y reflejos ausentes con la sonda en ese oído.
- **Fractura de cadena**: un huesecillo se rompe pero queda unido a medias (el mango del martillo, las cruras del estribo). Gap menor, cerca de 30 dB, **mayor en los agudos**, con curva A o Ad (Farahmand y cols., 2016).

También la puede desarticular una otitis crónica que necrosa el yunque, o un cotonito. Se trata con una osiculoplastia o un audífono.

### Colesteatoma

Es piel atrapada en el oído medio: el epitelio de una bolsa de retracción, casi siempre en el **ático** (la parte superior de la caja), se acumula como escamas de queratina, se infecta y **erosiona el hueso**. Da otorrea **fétida** a repetición e hipoacusia progresiva. En la otoscopía hay una bolsa de retracción o una costra en el ático, con material blanco.

El gap crece a medida que se come la cadena, sobre todo el yunque (Martins y cols., 2012), y suele ser más grande y plano que el de una perforación. Mientras la ósea esté normal, la cóclea está a salvo. El colesteatoma **no se cura con gotas**: el tratamiento es quirúrgico, y la audiometría sirve para planificarlo y seguirlo (Stankovic, 2008).

:::ojo Ojo clínico
Un colesteatoma puede abrir el laberinto (**fístula**), el canal del nervio facial o la duramadre. **Vértigo** al apretar el trago o al sonarse, **debilidad de la cara**, una **ósea que cae**, fiebre o dolor de cabeza fuerte con otorrea: se deriva el mismo día.
:::

### Glomus timpánico

Es un **paraganglioma**: un tumor benigno, muy vascular, que nace sobre el promontorio. Da **acúfeno pulsátil**, al ritmo del corazón, e hipoacusia conductiva; en la otoscopía se ve una **masa rojiza** detrás de la membrana íntegra, que puede latir. En 213 paragangliomas timpanomastoideos, el 80 % consultó por hipoacusia y el 77 % por acúfeno pulsátil (Yilala y cols., 2024). La masa rigidiza la membrana o la cadena: gap moderado, curva As o B; si crece, puede bajar la ósea (Baguley y cols., 1994). Todo **acúfeno pulsátil** se deriva para buscar su causa.


### Otitis media crónica y el oído operado

Una otitis crónica con años de otorrea no se queda siempre en el oído medio. La ósea cae, más en los agudos (Elzinga y cols., 2021), probablemente porque la inflamación pasa al oído interno por la ventana redonda. <!-- verificar: el mecanismo por la ventana redonda es la hipótesis más citada; confirmar que Elzinga 2021 lo discute. --> La pérdida se vuelve **mixta**. Después de una cirugía, el audiograma depende de lo que quedó: una timpanoplastia con un injerto laxo puede dar Ad, una cavidad abierta (mastoidectomía radical) un B con volumen alto, y la audición suele quedar mejor cuando se conserva la pared del conducto (Kim y cols., 2010).

## Razonamiento

### Del gap a la lesión

1. **¿Qué mostró la otoscopía?** Una perforación, placas blancas, una costra en el ático o una masa roja ya ubican el problema. **Si hay secreción, la impedanciometría no se hace.**
2. **¿Cuánto mide el gap?** Hasta 40 dB cabe en una perforación o en placas; 50 dB o más con la membrana entera es la cadena.
3. **¿Qué forma tiene?** Mayor en los graves: rigidez o perforación. Plano y grande: cadena cortada. Mayor en los agudos: cadena dañada a medias.
4. **¿Qué dice el timpanograma?** As: rígido. Ad: laxo. B con volumen alto: perforación. B con volumen normal: caja ocupada (líquido, sangre, colesteatoma).
5. **¿Y la ósea?** Normal: el problema es de transmisión. Baja en el oído enfermo: el daño llegó a la cóclea.

:::ayuda-ancho Seis oídos medios, lado a lado
| | Gap típico | Forma | Timpanograma | Volumen | Otoscopía |
|---|---|---|---|---|---|
| **Perforación** | 10 a 50 dB, según el tamaño | mayor en graves | B | **alto** | agujero en la membrana |
| **Timpanoesclerosis** | hasta unos 40 dB | mayor en graves | **As** | normal | placas blancas |
| **Disyunción** | 45 a 60 dB | **plano** | **Ad** | normal | membrana normal |
| **Fractura de cadena** | cerca de 30 dB | **mayor en agudos** | A o Ad | normal | normal, o cicatriz del trauma |
| **Colesteatoma** | crece con la erosión: 50 dB o más | bastante plano | B | normal si no hay perforación abierta | costra o bolsa en el ático |
| **Glomus timpánico** | moderado | parejo | As o B | normal | masa roja que late |
:::


### Cuándo derivar

- **El mismo día**: colesteatoma u otitis crónica con vértigo, debilidad facial, caída de la ósea, fiebre o dolor de cabeza; trauma con pérdida sensorioneural, vértigo o parálisis facial.
- **A otorrinolaringología**: toda perforación, la otorrea fétida o a repetición, el acúfeno pulsátil con una masa detrás de la membrana, y una conductiva que no se cierra a los dos o tres meses de un trauma.
- **A control**: la miringoesclerosis sin gap y la perforación traumática pequeña, hasta que cierre.

:::pregunta Pregunta abierta
Dos pacientes tienen un timpanograma Ad. Uno tiene un gap de 50 dB y el otro un audiograma normal. ¿Qué tiene cada uno? ¿Qué le preguntarías a cada uno en la anamnesis?
:::

## Casos

Cada caso se trabaja en cuatro pasos, como en el aprendizaje basado en problemas: lee la entrevista, separa los datos que importan, plantea tus hipótesis y decide qué pedir **antes** de mirar los resultados. La resolución de cada caso está al final del capítulo.

{{caso cap03_perforacion}}

*Otoscopías: Zaka Ur Rehman, OtitisMediaKPJ (Kaggle, 2026), CC BY-NC-SA 4.0.*

:::pregunta Paso 1 · ¿Qué datos importan?
¿Qué datos de la historia te hablan de una perforación vieja y cuáles de una que está activa? Mira la otoscopía del OD: ¿qué tamaño tiene el agujero y se ve secreción?
:::

:::pregunta Paso 2 · Tus hipótesis
¿Qué forma esperas que tenga el gap? ¿Qué te haría pensar que, además de la membrana, está dañada la cadena?
:::

:::pregunta Paso 3 · ¿Qué pedirías y por qué?
¿Corresponde poner la sonda en el OD? ¿Qué volumen esperas? El otorrino pidió función tubaria: ¿cuál de las dos pruebas haces?
:::

#### Paso 4 · Los resultados

:::figura cap03_perforacion audiograma
- @OD 250 | La aérea del OD está en 50 dB en 125 y 250 Hz, con la ósea en 0: un gap de 50 dB en los graves.
- @OD 2000 | Hacia los agudos mejora: 25 dB en 2 kHz y 20 en 4 kHz. Es una conductiva **ascendente**, de grado **leve** (promedio BIAP de 31 dB).
- @OI 1000 | El OI es normal.
:::
:::figura cap03_perforacion timpanograma
- @OD pico | Plana, sin pico: **B**. Pero el volumen es de 3,70 mL, más del doble que el del OI: la sonda está midiendo el conducto **y** la caja.
- @OI pico | **A**, con el pico en −54 daPa, 0,87 mL de compliancia y 1,53 mL de volumen.
:::
:::figura cap03_perforacion reflejos
- @ipsi OD 1000 | Con la sonda en el OD no hay reflejo: la membrana perforada no deja registrarlo.
- @contra OI 2000 | Con la sonda en el OI y el tono en el OD aparece solo en 2 kHz (120 dB SPL) y 4 kHz (115), donde el gap es menor.
- @ipsi OI 1000 | El ipsilateral del OI es normal: 85 dB SPL en 1 kHz.
:::

En LabSim, la **función tubaria de membrana perforada** de Lucía es permeable: con cada deglución la presión del conducto se acerca a 0.

:::docente Guía del caso
- **Datos clave:** otitis de niña, otorrea solo cuando entra agua, seca hace más de un año, sin acúfeno ni vértigo; perforación central amplia y seca en el OD.
- **Hipótesis esperables:** perforación timpánica crónica simple; colesteatoma (lo descarta el otorrino en la otoscopía); daño de cadena asociado (el gap no lo sugiere).
- **Qué pedir:** audiometría con ósea enmascarada, impedanciometría con reflejos y función tubaria de **membrana perforada** (→ H3, H4, H7).
- **Errores esperables:** informar "curva B" sin el volumen; hacer la prueba de membrana íntegra; no meter la sonda "por si acaso" en un oído seco que sí se puede medir.
- **En LabSim:** caso armado para el libro; el docente puede crearlo con el cuadro *perforación timpánica* en el OD. La paciente pregunta si podrá nadar: la respuesta es del otorrino.
:::

{{caso cap03_timpanoesclerosis}}

*Otoscopías: Viscaino M, Auat Cheein F, Ear imagery database (figshare, 2020), CC0 1.0.*

:::pregunta Paso 1 · ¿Qué datos importan?
¿Qué antecedente de la infancia explica lo que se ve en la membrana izquierda? ¿Qué te dice que la pérdida haya llegado "de a poco"?
:::

:::pregunta Paso 2 · Tus hipótesis
Las placas blancas de la membrana, ¿alcanzan para explicar una pérdida? ¿Qué otra lesión puede estar escondida detrás de ellas?
:::

:::pregunta Paso 3 · ¿Qué pedirías y por qué?
¿Qué curva esperas: As, A o Ad? ¿Qué hallazgo del audiograma te haría sospechar que el estribo también está fijo?
:::

#### Paso 4 · Los resultados

:::figura cap03_timpanoesclerosis audiograma
- @OI 250 | La aérea del OI está en 40 dB en 125 y 250 Hz, con la ósea en 0: el gap es mayor en los graves.
- @OI 2000 | Desde 500 Hz la aérea queda entre 25 y 30 dB. Conductiva **leve** (promedio BIAP de 29 dB), sin muesca en la ósea.
- @OD 1000 | El OD es normal.
:::
:::figura cap03_timpanoesclerosis timpanograma
- @OI pico | El pico está en su lugar (−12 daPa), pero mide solo 0,13 mL: **As**. El sistema se mueve poco.
- @OD pico | **A**, con 0,96 mL en −15 daPa. Volúmenes normales: membranas enteras.
- **Reflejos:** ausentes con la sonda en el OI; con el tono en el OI, solo en 4 kHz (120 dB SPL).
:::

:::docente Guía del caso
- **Datos clave:** otitis y tubos de niña; pérdida izquierda lenta, sin otorrea; placa blanca extensa en una membrana íntegra.
- **Hipótesis:** timpanoesclerosis; miringoesclerosis sola (no explica el gap); otoesclerosis (no calza con la historia).
- **Errores esperables:** atribuir el gap solo a la membrana; no buscar la muesca de Carhart; confundir As con B.
- **En LabSim:** cuadro *timpanoesclerosis / miringoesclerosis* en el OI.
:::

{{caso cap03_disyuncion_cadena}}

**Otoscopía de hoy.** OD: conducto sano; membrana íntegra y translúcida, sin sangre detrás. OI: normal.

:::pregunta Paso 1 · ¿Qué datos importan?
Ordena la historia en el tiempo. ¿Qué esperaba el médico que pasara con la audición y qué pasó? ¿Qué síntomas buscaste para saber si el golpe llegó al oído interno?
:::

:::pregunta Paso 2 · Tus hipótesis
La sangre ya se reabsorbió y la membrana se ve normal. ¿Qué puede seguir impidiendo que el sonido llegue a la cóclea?
:::

:::pregunta Paso 3 · ¿Qué pedirías y por qué?
¿Qué tamaño y qué forma de gap esperas si la cadena está cortada? ¿Y si está fracturada a medias? ¿Qué curva esperas en cada caso?
:::

#### Paso 4 · Los resultados

:::figura cap03_disyuncion_cadena audiograma
- @OD 500 | La aérea del OD está entre 45 y 55 dB en todas las frecuencias, con la ósea en 0: un gap de 45 a 55 dB.
- @OD 4000 | En 4 kHz el gap es casi el mismo que en los graves: es **plano**. Grado **moderado** (promedio BIAP de 49 dB).
- @OI 1000 | El OI es normal.
:::
:::figura cap03_disyuncion_cadena timpanograma
- @OD pico | Pico en −80 daPa con 2,92 mL, fuera de escala: **Ad**. Volumen normal (1,96 mL): membrana entera.
- @OI pico | **A**, con 0,47 mL en −52 daPa.
- **Reflejos:** solo el ipsilateral del OI. Ni con la sonda ni con el tono en el OD: el gap de 50 dB se come el estímulo.
:::

:::docente Guía del caso
- **Datos clave:** fractura del temporal que respeta la cápsula, hace cuatro meses; la sangre se fue y la pérdida quedó; sin vértigo ni parálisis facial.
- **Hipótesis:** disyunción; fractura parcial de cadena; hemotímpano residual (lo descarta la otoscopía); daño coclear (lo descarta la ósea).
- **Errores esperables:** dar por normal un Ad "porque tiene pico"; seguir esperando; no enmascarar la ósea con 50 dB de gap.
- **En LabSim:** cuadro *disyunción de cadena osicular* en el OD, grado moderado; la fractura está en la historia.
:::

{{caso cap03_colesteatoma}}

*Otoscopías: Zaka Ur Rehman, OtitisMediaKPJ (Kaggle, 2026), CC BY-NC-SA 4.0.*

:::pregunta Paso 1 · ¿Qué datos importan?
¿Qué tiene de distinto la otorrea de Sergio de la de Lucía (caso 3.1)? ¿Dónde está el hallazgo en la otoscopía izquierda?
:::

:::pregunta Paso 2 · Tus hipótesis
¿Por qué un oído que "supura cada tantos meses y oye cada vez menos" en un joven no es lo mismo que una perforación seca? ¿Qué síntomas lo harían urgente?
:::

:::pregunta Paso 3 · ¿Qué pedirías y por qué?
El oído está seco desde hace tres semanas. ¿Puedes poner la sonda? ¿Qué habría cambiado si hoy tuviera secreción?
:::

#### Paso 4 · Los resultados

:::figura cap03_colesteatoma audiograma
- @OI 125 | La aérea del OI está en 55 dB en 125 Hz y entre 40 y 50 en el resto, con la ósea en 0: un gap de 40 a 55 dB, bastante plano.
- @OI osea 2000 | La ósea está normal en todas las frecuencias: la cóclea todavía está a salvo. Grado **moderado** (promedio BIAP de 46 dB).
:::
:::figura cap03_colesteatoma timpanograma
- @OI pico | **B**, con un volumen de 1,56 mL, normal y parecido al del OD (1,23 mL): la sonda mide un conducto cerrado. No hay una perforación abierta.
- @OD pico | **A**, con el pico en −59 daPa y 1,06 mL.
- **Reflejos:** solo el ipsilateral del OD. Ni con la sonda ni con el tono en el OI: el gap se lleva el estímulo.
:::

:::docente Guía del caso
- **Datos clave:** otorrea **fétida** a repetición, pérdida progresiva, seco hoy; costra y material blanco en el ático; sin vértigo ni debilidad facial.
- **Hipótesis:** colesteatoma del ático; otitis media crónica simple (el olor, el ático y el gap apuntan a lo primero).
- **Errores esperables:** meter la sonda sin mirar si hay secreción; leer el B como "líquido"; dejarlo "en control" con un gap que crece.
- **En LabSim:** cuadro *colesteatoma (sin daño coclear)* en el OI. Con otorrea activa, la impedanciometría del OI pasa a NR.
:::

{{caso cap03_p41}}

**Otoscopía de hoy.** OD: membrana íntegra, con triángulo luminoso. OI: conducto seco, sin secreción; membrana opaca y engrosada.

:::pregunta Paso 1 · ¿Qué datos importan?
¿Qué datos de la historia de Luis vienen de la infancia y cuáles de los últimos cinco años? ¿Por qué importa que hoy el oído esté seco?
:::

:::pregunta Paso 2 · Tus hipótesis
Un oído con otorrea de años y una pérdida que crece. ¿Esperas una conductiva pura? ¿Qué parte del audiograma te diría que el daño llegó a la cóclea?
:::

:::pregunta Paso 3 · ¿Qué pedirías y por qué?
¿Qué volumen esperas si hay una perforación abierta? ¿Y si la membrana está cerrada?
:::

#### Paso 4 · Los resultados

:::figura cap03_p41 audiograma
- @OI 1000 | La aérea del OI está en 50 dB en 1 kHz y baja a 65 en 4 kHz y 70 en 8 kHz.
- @OI osea 1000 | La ósea del OI está en 25 dB en 500 y 1.000 Hz: hay gap (25 a 30 dB), pero la ósea **tampoco es normal**.
- @OI osea 4000 | La ósea cae hacia los agudos: 35 dB en 2 kHz y 45 en 4 kHz. Pérdida **mixta**, grado **moderado** (promedio BIAP de 56 dB).
:::
:::figura cap03_p41 timpanograma
- @OI pico | **B**, con 1,91 mL de volumen, normal y parecido al del OD (1,73 mL): hoy la sonda no está viendo la caja. La membrana está cerrada.
- @OD pico | **A**, con el pico en −86 daPa y 0,97 mL.
- **Reflejos:** ausentes con la sonda en el OI; con el tono en el OI, solo en 2 y 4 kHz (115 dB SPL).
:::

:::docente Guía del caso
- **Datos clave:** otitis y tubos de niño; otorrea amarilla y fétida del OI desde hace cinco años, que aparece con los resfríos y se seca con gotas (el último episodio, hace cuatro meses); pérdida progresiva y zumbido intermitente; sin vértigo; hoy el oído está seco.
- **Hipótesis esperables:** otitis media crónica con daño coclear; colesteatoma (la otorrea fétida obliga a pensarlo: lo descarta el otorrino); hipoacusia por ruido de chofer (no explica el gap).
- **Qué pedir:** audiometría con ósea y logoaudiometría enmascaradas, impedanciometría solo si el oído está seco (→ H3, H4, H5, H7).
- **Errores esperables:** informar "conductiva" sin mirar que la ósea cayó; meter la sonda un día con otorrea; leer el B con volumen normal como si fuera una perforación.
- **En LabSim:** es el paciente de práctica 41; se atiende desde "Práctica libre". El mismo Luis aparece en H3, H4 y H5: aquí se mira el oído medio. Le preocupa perder días de trabajo si lo operan.
:::

## Resolución de los casos

Intenta resolver cada caso con los pasos del aprendizaje basado en problemas antes de leer esta sección.

### Caso 3.1

#### Razonamiento

Una perforación central amplia, seca, con una conductiva ascendente de 50 dB en los graves y 20 dB en los agudos: es lo que hace un agujero grande en la membrana (Mehta y cols., 2006). El gap no pasa de lo que explica la perforación, así que no hay motivo para sospechar de la cadena. El B con volumen alto confirma que la sonda midió a través del agujero, y la prueba de membrana perforada muestra una trompa que ventila.

#### Diagnóstico y qué sigue

Hipoacusia conductiva leve del OD, ascendente, con timpanograma B de volumen alto (3,70 mL) y función tubaria permeable: compatible con **perforación timpánica crónica**. Se informa al otorrino, que decide la timpanoplastia; una trompa permeable es un dato a favor. Se controla la audición después de operar.

:::comentario Comentario
Mientras la membrana no se cierre, el agua es lo que reactiva la otorrea. Para la piscina, el otorrino suele indicar protección del oído; esa conversación es suya.
:::

### Caso 3.2

#### Razonamiento

Las placas blancas cuentan la historia: otitis y tubos en la infancia. Pero la miringoesclerosis sola casi no da pérdida, y Daniela tiene un gap de 25 a 40 dB, mayor en los graves, con una curva As. Eso es rigidez más allá de la membrana: la timpanoesclerosis llegó a la caja o a la cadena. La ósea sin muesca en 2 kHz y un gap bajo 40 dB no apuntan a un estribo fijo.

#### Diagnóstico y qué sigue

Hipoacusia conductiva leve del OI, de predominio en graves, con timpanograma As y reflejos ausentes con la sonda en el OI: compatible con **timpanoesclerosis**. Se informa al otorrino. La cirugía es una opción (mejora sobre todo 0,5 a 2 kHz; Stankovic, 2009) y un audífono, otra.

### Caso 3.3

#### Razonamiento

Una fractura que respeta la cápsula ótica da una conductiva por la sangre, y esa suele cerrarse cuando se reabsorbe (Song y cols., 2017). En Diego la sangre se fue y el gap quedó en 45 a 55 dB, **plano**, con la membrana entera y una curva Ad: la cadena está cortada. Una fractura de cadena a medias habría dado un gap menor y mayor en los agudos (Sarmento y cols., 2017). La ósea normal y la falta de vértigo dicen que el laberinto no se dañó.

#### Diagnóstico y qué sigue

Hipoacusia conductiva moderada del OD, plana, con timpanograma Ad y reflejos ausentes con la sonda en el OD, cuatro meses después de una fractura del temporal: compatible con **disyunción de cadena osicular**. Se informa al otorrino, que decide entre la osiculoplastia y un audífono.

:::ojo Ojo clínico
Un Ad "tiene pico" y es fácil darlo por normal. Con 50 dB de gap y la membrana entera, un Ad es la firma de la cadena suelta.
:::

### Caso 3.4

#### Razonamiento

Otorrea fétida a repetición desde la adolescencia, una pérdida que crece y una costra con material blanco en el ático: es la historia del colesteatoma. El gap de 40 a 55 dB, bastante plano, dice que la cadena ya está erosionada (Martins y cols., 2012). El B con volumen normal dice que hoy no hay una perforación abierta a la caja: la lesión está detrás de una membrana retraída. La ósea normal es la buena noticia: la cóclea aún no se toca.

#### Diagnóstico y qué sigue

Hipoacusia conductiva moderada del OI, con timpanograma B de volumen normal y ósea normal: compatible con **colesteatoma del oído izquierdo sin compromiso coclear**, que el otorrino confirma con la otoscopía y la TC. El tratamiento es quirúrgico (Stankovic, 2008). Se le explica a Sergio que no debe esperar a que el oído vuelva a supurar para controlarse, y que el vértigo o la debilidad de la cara son motivo de urgencia.

:::imagen ilustraciones/cap03-tc-colesteatoma.jpg ancho=100% Tomografía coronal de los dos oídos de otra persona, no de Sergio: a la izquierda de la imagen está su oído derecho, con colesteatoma; a la derecha, el izquierdo, sano. La tomografía la pide y la informa el médico; se muestra para que se vea la forma de lo que miden las pruebas. Imagen: Gulati M, Gupta S, Prakash A, Garg A, Dixit R (2019), Insights Imaging, doi:10.1186/s13244-019-0782-y, Fig. 2, CC BY 4.0, sin modificar.
- @88,46 | **Escudo sano** (flecha amarilla): la punta de hueso donde se apoya el borde de arriba de la membrana.
- @79,70 | En el oído sano, la caja y el conducto tienen aire (negro).
- @15,60 | En el oído enfermo el escudo se borró, y la caja y el conducto están ocupados por partes blandas (gris) en vez de aire.
:::

### Caso 3.5

#### Razonamiento

Luis tiene dos problemas en el mismo oído. Hay un gap de 25 a 30 dB, que es el oído medio enfermo por años de otitis. Y la ósea también cayó, sobre todo en los agudos: la inflamación crónica llegó a la cóclea (Elzinga y cols., 2021). El B con volumen normal, igual al del otro oído, dice que hoy la sonda mide un conducto cerrado. Si hubiera una perforación abierta, el volumen sería alto, y si el oído supurara la impedanciometría no se habría hecho.

#### Diagnóstico y qué sigue

Hipoacusia **mixta** moderada del OI, con la ósea caída en los agudos, timpanograma B de volumen normal y reflejos ausentes con la sonda en ese oído: compatible con **otitis media crónica con compromiso coclear**. Se informa al otorrino, que estudia el oído (otorrea fétida: hay que descartar un colesteatoma) y decide la cirugía. Que la ósea haya caído hace que operar pronto importe más.

:::comentario Comentario
La pérdida de un chofer suele atribuirse al ruido del motor. Aquí no calza: el ruido no da gap. Lo que tiene Luis viene del oído medio, y la ósea dice cuánto le costó.
:::

## Para cerrar

:::pregunta Preguntas para discutir
1. Una perforación pequeña da un gap de 50 dB. ¿Qué más sospechas y por qué?
2. ¿Por qué una cadena cortada con la membrana entera pierde más que un oído medio sin membrana?
3. Un paciente tiene placas blancas en la membrana y un audiograma normal. ¿Qué curva esperas? ¿Lo derivas?
4. Un oído supura hoy. ¿Qué haces con la impedanciometría y qué anotas en la ficha?
:::

:::ayuda Ayuda memoria del capítulo
- **La cadena cortada con la membrana entera** da el gap más grande: 50 a 60 dB, plano, con **Ad**.
- La **perforación** da un gap mayor en los graves, que crece con el tamaño del agujero; curva B con **volumen alto**; función tubaria con la **prueba de membrana perforada**.
- La **rigidez** (timpanoesclerosis, masa) pierde los graves y da **As**; la **unión floja** pierde los agudos.
- **Ad con gap** = cadena; **Ad sin gap** = membrana cicatricial.
- **Secreción en el conducto = no se mide** (NR). Perforación seca sí.
- **Colesteatoma** con vértigo, debilidad facial o caída de la ósea, y todo **acúfeno pulsátil**: se derivan sin esperar.
:::

## Referencias

### Técnica

1. International Organization for Standardization. ISO 8253-1:2010. Acoustics — Audiometric test methods — Part 1: Pure-tone air and bone conduction audiometry. Ginebra: ISO; 2010.
1. American Speech-Language-Hearing Association. Guidelines for manual pure-tone threshold audiometry [Guidelines]. Rockville (MD): ASHA; 2005. Disponible en: https://www.asha.org/policy/gl2005-00014/
1. British Society of Audiology. Recommended procedure: pure-tone air-conduction and bone-conduction threshold audiometry with and without masking (OD104-32). BSA; 2018. Disponible en: https://www.thebsa.org.uk/wp-content/uploads/2024/01/Recommended-Procedure-Pure-Tone-Audiometry-2018.pdf
1. BIAP. Recomendación 02/1: Clasificación audiométrica de las deficiencias auditivas.
1. British Society of Audiology. Recommended procedure: tympanometry and acoustic reflex thresholds [Internet]. BSA; 2024 Feb (enmiendas menores feb 2025 y mar 2026) [citado 2026 oct 15]. Disponible en: https://www.thebsa.org.uk/wp-content/uploads/2026/03/BSA-Recommended-Procedure-Tympanometry-Acoustic-Reflex-Thresholds-March-2026-minor-revision.pdf
1. Jerger J, Anthony L, Jerger S, Mauldin L. Studies in impedance audiometry. 3. Middle ear disorders. Arch Otolaryngol. 1974;99(3):165-71. doi:10.1001/archotol.1974.00780030173003
1. Lidén G, Harford E, Hallén O. Tympanometry for the diagnosis of ossicular disruption. Arch Otolaryngol. 1974;99(1):23-9. doi:10.1001/archotol.1974.00780030027005
1. Smith ME, Tysome JR. Tests of Eustachian tube function: a review. Clin Otolaryngol. 2015;40(4):300-311. doi:10.1111/coa.12428
1. Lee DH, Heo Y, Na HS, Lee S, Oh SJ, Choi SW. Clinical utility of modified inflation-deflation test in Eustachian tube function testing. Diagnostics (Basel). 2026;16(16):2534. doi:10.3390/diagnostics16162534

### Fisiología

1. Merchant SN, Ravicz ME, Voss SE, Peake WT, Rosowski JJ. Toynbee Memorial Lecture 1997. Middle ear mechanics in normal, diseased and reconstructed ears. J Laryngol Otol. 1998;112(8):715-31. doi:10.1017/S0022215100141568
1. Aibara R, Welsh JT, Puria S, Goode RL. Human middle-ear sound transfer function and cochlear input impedance. Hear Res. 2001;152(1-2):100-9. doi:10.1016/S0378-5955(00)00240-9
1. Stenfelt S, Goode RL. Bone-conducted sound: physiological and clinical aspects. Otol Neurotol. 2005;26(6):1245-61. doi:10.1097/01.mao.0000187236.10842.d5

### Patología

1. Mehta RP, Rosowski JJ, Voss SE, O'Neil E, Merchant SN. Determinants of hearing loss in perforations of the tympanic membrane. Otol Neurotol. 2006;27(2):136-143.
1. Kaur K, Sonkhya N, Bapna AS. Tympanosclerosis revisited. Indian J Otolaryngol Head Neck Surg. 2006;58(2):128-132. doi:10.1007/BF03050766
1. Stankovic MD. Hearing results of surgery for tympanosclerosis. Eur Arch Otorhinolaryngol. 2009;266(5):635-640.
1. Gentil F, Garbe C, Parente M, Martins P, Ferreira A, Jorge RN, Santos C, Paço J. Analysis of eardrum pathologies using the finite element method. J Mech Med Biol. 2014;14(3):1450034. doi:10.1142/s0219519414500341
1. Farahmand RB, Merchant GR, Lookabaugh SA, Röösli C, Ulku CH, McKenna MJ, de Venecia RK, Halpin CF, Rosowski JJ, Nakajima HH. The audiometric and mechanical effects of partial ossicular discontinuity. Ear Hear. 2016;37(2):206-215. doi:10.1097/AUD.0000000000000239
1. Cheon D, Kim D, Kim SH, Choi JY, Bae SH. Diagnostic value of the air-bone threshold gap in stapes fixation. Audiol Neurootol. 2023;28(4):255-261.
1. Sarmento KMA Jr, Sampaio ALL, Santos TGT, Oliveira CACP. High-frequency conductive hearing loss as a diagnostic test for incomplete ossicular discontinuity in non-cholesteatomatous chronic suppurative otitis media. PLoS One. 2017;12(12):e0189997.
1. Song SW, Jun BC, Kim H. Clinical features and radiological evaluation of otic capsule sparing temporal bone fractures. J Laryngol Otol. 2017;131(3):209-214.
1. Dahiya R, Keller JD, Litofsky NS, Bankey PE, Bonassar LJ, Megerian CA. Temporal bone fractures: otic capsule sparing versus otic capsule violating clinical and radiographic considerations. J Trauma. 1999;47(6):1079-1083. doi:10.1097/00005373-199912000-00014
1. Kim SY, Kim YJ, Kim YH, Park MH. Audiologic patterns of otic capsule preserving temporal bone fracture: effects of the affected subsites. Clin Exp Otorhinolaryngol. 2016;9(3):206-211. doi:10.21053/ceo.2015.01116
1. Martins O, Victor J, Selesnick S. The relationship between individual ossicular status and conductive hearing loss in cholesteatoma. Otol Neurotol. 2012;33(3):387-392. doi:10.1097/MAO.0b013e3182487fb0
1. Stankovic MD. Audiologic results of surgery for cholesteatoma: short- and long-term follow-up of influential factors. Otol Neurotol. 2008;29(7):933-940.
1. Yilala MH, Fancello G, Fancello V, Lauda L, Sanna M. Long-term surgical outcome of class A and B tympanomastoid paragangliomas. Cancers (Basel). 2024;16(8):1466.
1. Baguley DM, Irving RM, Hardy DG, Harada T, Moffat DA. Audiological findings in glomus tumours. Br J Audiol. 1994;28(6):291-297. doi:10.3109/03005369409077313
1. Elzinga HBE, van Oorschot HD, Stegeman I, Smit AL. Relation between otitis media and sensorineural hearing loss: a systematic review. BMJ Open. 2021;11(8):e050108. doi:10.1136/bmjopen-2021-050108
1. Kim MB, Choi J, Lee JK, Park JY, Chu H, Cho YS, Hong SH, Chung WH. Hearing outcomes according to the types of mastoidectomy: a comparison between canal wall up and canal wall down mastoidectomy. Clin Exp Otorhinolaryngol. 2010;3(4):203-206.
