# H24. Rinomanometría anterior

:::objetivos En esta herramienta
- Explicar qué mide la rinomanometría (presión y flujo del aire que respira la nariz) y por qué la resistencia no es un número fijo sino una curva.
- Deducir de la física del flujo por qué la resistencia se informa a una presión de referencia y por qué las dos fosas se combinan como resistencias en paralelo.
- Montar la rinomanometría anterior activa: máscara, adaptador nasal, tubo de presión y comprobación del sello.
- Medir cada fosa en reposo y, si hace falta, después del vasoconstrictor.
- Calcular la resistencia unilateral y total a 150 Pa, compararla con el valor de referencia y leer la curva.
- Distinguir una obstrucción vasomotora, mixta y mecánica por lo que cambia con el vasoconstrictor.
:::

La nariz es la puerta de entrada del aire y, cuando se tapa, el paciente lo nota antes que cualquier examen. Pero "tengo la nariz tapada" es un síntoma, y lo que se ve en una rinoscopía (→ H23) es una forma. La rinomanometría mide lo que falta entre las dos cosas: **cuánto aire pasa realmente por cada fosa y cuánta presión cuesta hacerlo pasar**. Esta herramienta enseña a medirlo, a escribirlo y, sobre todo, a entender por qué se hace como se hace.

## Para qué sirve

La rinomanometría anterior responde tres preguntas:

1. **¿Cuánta resistencia opone cada fosa nasal al aire?** Es un número, en pascales por centímetro cúbico por segundo, que se puede comparar con un valor de referencia, entre un lado y el otro, y entre un día y otro.
2. **¿La obstrucción es de la mucosa o de la estructura?** Se mide en reposo y otra vez después de un vasoconstrictor. Lo que el vasoconstrictor quita era mucosa hinchada; lo que queda es esqueleto: tabique, válvula, hueso.
3. **¿Cuánto mejoró (o empeoró) la nariz?** Antes y después de un tratamiento, de una cirugía o de una provocación nasal, el mismo examen permite comparar con números.

Se pide cuando el síntoma y lo que se ve no calzan: un tabique desviado que no molesta, o una nariz de aspecto normal que el paciente siente tapada. También para decidir si un paciente necesita cirugía o tratamiento médico, y para controlar el resultado.

Tiene límites. Es un examen **funcional**: dice cuánta resistencia hay, no **por qué**. Para eso están la rinoscopía (→ H23), la endoscopía y las imágenes, y la rinometría acústica, que mide la geometría de la fosa (→ H25). Además, depende de que el paciente respire con naturalidad y de que la nariz esté en condiciones: una nariz en pleno resfrío o con el ciclo nasal en un extremo da un resultado que no representa al paciente. Y mide resistencia al aire, no la **sensación** de obstrucción: puede haber discordancia entre las dos, y ese hallazgo también informa.

## Fundamento

La rinomanometría es física de fluidos aplicada a una nariz. Para leerla bien conviene entender cuatro cosas: qué relaciona la presión con el flujo, por qué esa relación no es una recta, de dónde sale el número que se informa y qué hace la mucosa que lo cambia. La anatomía nasal está en B1 y la fisiología en B2; aquí va lo justo.

### Presión y flujo: la nariz como una resistencia

El aire entra por la nariz porque el tórax baja la presión en la nasofaringe: entre el aire de afuera y el de adentro aparece una **diferencia de presión** (ΔP). Esa diferencia empuja un **flujo** (V̇) de aire. La relación entre las dos es la **resistencia**, igual que en un circuito eléctrico la tensión, la corriente y la resistencia:

**R = ΔP / V̇**

Con ΔP en pascales (Pa) y V̇ en centímetros cúbicos por segundo (cm³/s), la resistencia queda en **Pa/(cm³/s)**. En la literatura a veces aparece como cmH₂O/L/s: 1 Pa/(cm³/s) equivale a unos 10,2 cmH₂O/L/s.

La nariz es la parte más resistente de la vía aérea de un adulto que respira por ella: en el estudio clásico de Ferris y cols. (1964), la nariz aportaba alrededor de la mitad de la resistencia total al flujo de aire de las vías respiratorias. <!-- verificar: la cifra "alrededor de la mitad" es la que se cita de Ferris, Mead y Opie (1964); no se leyó el texto completo. --> Por eso un paciente con la nariz tapada respira por la boca: es el camino de menor resistencia.

### Por qué la curva no es una recta

Si el aire circulara por un tubo recto y liso, en capas paralelas (**flujo laminar**), la presión necesaria sería proporcional al flujo: el doble de flujo costaría el doble de presión, y la resistencia sería un número fijo. Pero la nariz no es un tubo liso. Tiene una **válvula** estrecha, cornetes que se interponen y curvas. A flujos mayores el aire se desordena en remolinos (**flujo turbulento**), y la presión que cuesta crece más rápido que el flujo: aproximadamente con su cuadrado.

La nariz real es una mezcla de las dos cosas. Una ecuación clásica, atribuida a Rohrer (1915), la describe sumando las dos: <!-- Rohrer 1915 confirmado en Crossref (doi:10.1007/BF01681259). -->

**ΔP = k₁·V̇ + k₂·V̇²**

El primer término es lo laminar; el segundo, lo turbulento. Dividiendo por V̇ queda **R = k₁ + k₂·V̇**: la resistencia **sube con el flujo**. Eso tiene una consecuencia directa y que se olvida seguido: **un valor de resistencia sin la presión a la que se leyó no significa nada**. La misma nariz tiene una resistencia a 75 Pa y otra, mayor, a 150 Pa.

Hay un segundo fenómeno que dobla la curva. Cuando el aire acelera por la válvula nasal, la presión de las paredes baja (principio de Bernoulli) y el tejido blando de la válvula puede cerrarse un poco. A mayor esfuerzo, el flujo deja de crecer: la curva forma una **meseta**. Por eso la curva normal tiene forma de S aplanada y no de recta.

:::imagen ilustraciones/h24-rs-colapso.svg ancho=100% Una válvula blanda, con inspiración forzada. La rama inspiratoria (la fosa derecha, en rojo, en el cuadrante I; la izquierda, en azul, en el II) se aplana en una meseta: por más presión que se haga, el flujo ya no sube. La espiratoria (cuadrantes III y IV) sigue creciendo. A 150 Pa, la resistencia de la fosa derecha es cerca de 0,6 Pa/(cm³/s) al inspirar y 0,36 al espirar. Paciente simulado; las cifras son del modelo, no normas. Imagen propia hecha con RinoSim (→ Simuladores, en las preliminares).
:::

:::imagen ilustraciones/h24-rs-curvas.svg ancho=100% La relación presión-flujo de cada fosa. A: las curvas en los cuatro cuadrantes; la derecha (rojo) pasa por I y III, la izquierda (azul) por II y IV; las líneas verticales de rayas marcan 75 y 150 Pa y la diagonal punteada es la recta de la resistencia de referencia (0,4): una curva que pasa por encima de ella tiene menos resistencia que esa. B: la misma información como resistencia contra presión, en inspiración: sube a medida que la presión crece. A 150 Pa la fosa derecha da 0,35 y la izquierda 0,29 Pa/(cm³/s); el total, 0,16. Paciente simulado; las cifras son del modelo, no normas. Imagen propia hecha con RinoSim (→ Simuladores, en las preliminares).
:::

### De ahí salen los cuatro cuadrantes

Cada fosa se mide por separado y su curva se dibuja con la **presión en el eje horizontal y el flujo en el vertical**. En inspiración, presión y flujo van en el mismo sentido; en espiración, los dos se invierten. Por eso la curva de una fosa pasa por **dos cuadrantes opuestos**, el primero y el tercero, y pasa por el origen. Los equipos suelen dibujar la otra fosa en espejo, en el segundo y el cuarto, de modo que ambas queden a la vista en un mismo gráfico. Una fosa muy abierta da una curva empinada, pegada al eje del flujo. Una obstruida da una curva baja, pegada al eje de la presión.

### De dónde sale el número: la presión de referencia

Como la resistencia cambia a lo largo de la curva, hay que leerla en un **punto fijo y común**. Lo habitual es una presión: 150 Pa, o 75 Pa cuando el paciente no alcanza los 150 (Clement, 1984; Wong y Eccles, 2014). <!-- verificar: Clement (1984) recomienda una presión fija; que sea 150 Pa y que se use 75 Pa como alternativa se confirmó en la introducción de Wong y Eccles (2014), no en el informe de 1984. --> En el ejemplo de la figura, la fosa derecha da 0,26 a 75 Pa y 0,35 a 150 Pa. Por eso el informe escribe **siempre** la presión.

¿Por qué 150 Pa y no menos? A presiones muy bajas, el flujo recién se está poniendo en marcha, la señal es chica y el ruido pesa mucho. Pero a presiones muy altas no todos los pacientes llegan, sobre todo los de nariz amplia. En una serie de 20.069 mediciones en reposo, entre 4,5 y 8,6 % no alcanzó los 150 Pa según la fase del ciclo respiratorio (Vogt y cols., 2016). 150 Pa es un compromiso: suficientemente alto para tener señal, suficientemente bajo para que casi todos lleguen.

### Broms: leer la resistencia en un radio, no en una presión

Broms y cols. (1982) propusieron otra manera de elegir ese punto fijo. La curva se traza como en la figura de arriba, presión contra flujo, y sobre el gráfico se dibuja un **círculo centrado en el origen**: el **radio de referencia** (en la bibliografía, el "radio 200"). La resistencia se lee en el punto donde el círculo corta la curva: es la pendiente de la recta que va del origen a ese punto.

:::imagen ilustraciones/h24-rs-broms.svg ancho=100% La idea del gráfico polar de Broms. Las dos fosas cortan el mismo círculo de referencia (el dibujo lo muestra como elipse porque los dos ejes no miden lo mismo por unidad); la resistencia de cada una es la pendiente de la recta del origen a su punto. Una pendiente más empinada es menos resistencia. Paciente simulado. Imagen propia hecha con RinoSim (→ Simuladores, en las preliminares).
:::

¿Qué se gana? Con un radio, cada nariz se mide a **una distancia similar del origen**, aunque el punto caiga a otra presión. Una nariz muy obstruida se lee a una presión más alta (en el dibujo, la fosa derecha, unos 118 Pa) y una muy abierta a una más baja (la izquierda, unos 43 Pa): la medición no depende de que el paciente alcance una presión fija. Es lo que hace el gráfico polar de los equipos que lo traen. El valor numérico del radio estándar depende de la escala con que el equipo dibuje los ejes. <!-- verificar: escala de ejes del "radio 200" de Broms y cols. (1982), no leída en el original. -->

### Dos fosas: resistencias en paralelo

Las dos fosas conectan la misma nasofaringe con el mismo aire de afuera: están **sometidas a la misma diferencia de presión**, y el aire se reparte entre ellas. A una presión dada, **el flujo total es la suma de los flujos**:

V̇T = V̇D + V̇I

Como V̇ = ΔP / R, y ΔP es la misma, queda:

**1 / RT = 1 / RD + 1 / RI**

Es la fórmula de las resistencias en paralelo. Tiene dos consecuencias que sirven para leer un informe. La resistencia total es **siempre menor que la de la fosa más abierta**: dos caminos son mejores que uno. Y si una fosa se tapa del todo (resistencia infinita), el total queda igual a la resistencia de la otra. Una precisión: la fórmula vale cuando las dos resistencias se leen **a la misma presión**, por eso el informe da las dos a 150 Pa.

La técnica anterior mide cada fosa por separado, y la resistencia total se calcula con esta fórmula. En el apartado de ejercicios hay ejemplos con números.

### Cómo se mide la presión sin poner nada en la nasofaringe

Aquí está el truco de la técnica **anterior**. Para medir la fosa derecha, se tapa la izquierda con un adaptador conectado a un tubo de presión. Por la fosa izquierda tapada no circula aire, así que **no hay caída de presión** a lo largo de ella: lo que el sensor detecta en la narina izquierda es la presión de la nasofaringe, que llega a través de la coana. El flujo que atraviesa la fosa derecha se mide con un neumotacógrafo en la máscara. Con la presión de un lado y el flujo del otro se dibuja la curva de la fosa derecha. Después se invierte todo para medir la izquierda.

Por eso la técnica **requiere que el tabique esté íntegro**: una perforación septal deja pasar aire entre las fosas y el sensor ya no mide la nasofaringe. Tampoco sirve con una atresia coanal, ni durante un cuadro respiratorio agudo (una nariz en pleno resfrío no representa al paciente).

### El ciclo nasal: por qué una sola medida puede engañar

La mucosa de los cornetes y del tabique tiene una gran cantidad de vasos que se llenan y se vacían. Eso permite que una fosa se congestione un rato mientras la otra se abre, y después al revés: es el **ciclo nasal**, descrito desde fines del siglo XIX (Flanagan y Eccles, 1997). Una fosa que hoy aparece tapada puede estar, simplemente, en su fase congestionada. Es un cambio fisiológico, y lo normal es que el total se mantenga relativamente estable aunque los lados se compensen (Hasegawa y Kern, 1977). <!-- verificar: que la resistencia total se mantiene relativamente constante mientras los lados se alternan es la lectura habitual de Hasegawa y Kern (1977); no se leyó el texto completo. --> Lo que no es fisiológico es una asimetría que **no se compensa** con la otra fosa y se repite.

En un estudio de 52 voluntarios medidos cada hora durante ocho horas, solo 11 (alrededor de un quinto) cumplían una definición estricta de ciclo (Flanagan y Eccles, 1997), así que no se debe esperar un ciclo regular en todos. La consecuencia práctica es una sola: **una medición de una fosa en un solo momento es una foto**, y la comparación entre lados se hace con cuidado.

### El vasoconstrictor: separar mucosa de esqueleto

Una nariz está obstruida por dos tipos de cosas: las que cambian con la **mucosa** (el cornete hinchado por alergia, por un resfrío o por el ciclo) y las que son de **estructura** (un tabique desviado, una válvula colapsada, una concha hipertrófica ósea). Los vasoconstrictores, como la oximetazolina, actúan sobre los vasos de la mucosa: la contraen y la desinflan. Con eso se retira el componente mucoso, y la resistencia que queda es la **del esqueleto** (Broms, 1982b).

De ahí sale la lectura de la prueba. Si la resistencia vuelve a lo normal después del vasoconstrictor, la obstrucción era **mucosa**. Si no cambia, era **estructural**. Si baja pero no llega, había de las dos. En la práctica es una forma de preguntar qué parte del problema puede resolverse con tratamiento médico y qué parte solo con cirugía.

Es también la razón de varias reglas de la preparación: los vasoconstrictores, los antialérgicos y los descongestionantes **que el paciente tomó en los días previos** ya están cambiando la mucosa, de modo que la medición en reposo no mostraría el estado habitual, y la prueba perdería su sentido.

## Antes de empezar

### Equipo

- **Rinomanómetro** con máscara facial, tubo de presión y neumotacógrafo (ver *Conoce tu equipo*).
- Adaptadores nasales de varios tamaños; espéculos nasales; espejo frontal y lámpara de cuello flexible.
- Vasoconstrictor nasal en atomizador (oximetazolina).
- Pañuelos desechables, guantes, alcohol y algodón para limpiar, bandejas metálicas y el formulario de rinomanometría.
- Áreas limpias y sucias separadas, lavado de manos y guantes durante el examen.

El equipo se enciende y se configura antes de que entre el paciente, para que no sea el paciente el que espere. La duración es de unos 30 minutos.

### Conoce tu equipo: la rinomanometría anterior activa

Primero, el montaje. El dibujo muestra lo que se arma sobre el paciente: la máscara cubre la nariz y la boca; el neumotacógrafo, delante de la máscara, mide cuánto aire pasa; y el tubo de presión sale de la fosa contraria, tapada con el adaptador. En el equipo real el neumotacógrafo y los sensores van en un cabezal; el esquema separa las partes para que se vea cada una.

:::imagen ilustraciones/h24-montaje.svg ancho=100% La rinomanometría anterior activa, midiendo la fosa derecha
- @36,68 | **Máscara.** Cubre nariz y boca, con una presión leve: si deja escapar aire, el flujo medido es menor que el real. Cubre también la boca para que todo el aire pase por el neumotacógrafo: por eso el paciente debe tener la boca cerrada, porque el aire que entra o sale por ella ya no es el de la nariz.
- @29,47 | **Adaptador y tubo de presión.** Va en la fosa **contraria** a la que mides. Por ella no circula aire, así que el sensor detecta la presión de la nasofaringe. El tamaño no debe deformar la narina.
- @40,62 | **Neumotacógrafo.** Un tubo con una resistencia conocida (una malla, en este dibujo): el aire que pasa deja una pequeña diferencia de presión entre sus dos lados, y de ella el equipo calcula el flujo.
- @45,17 | **Transductor de flujo.** Convierte esa diferencia de presión en una señal eléctrica. Es el eje vertical de la curva.
- @68,74 | **Transductor de presión.** Recibe la presión del tubo nasal. Es el eje horizontal de la curva.
- @73,35 | **Registro.** El equipo cruza presión y flujo en cada instante y dibuja la curva; calcula la resistencia a la presión de referencia.
- @84,59 | **Fosa medida** (la derecha, en rojo): queda libre, sin nada dentro.
- @90.5,59 | **Fosa ocluida** (la izquierda, en azul): lleva el adaptador y el tubo de presión.
:::

Después, el resultado. Lo que entrega el equipo es la curva de las dos fosas y una tabla con la resistencia de cada una; los equipos reales lo dibujan con otra disposición, pero con los mismos elementos.

:::imagen ilustraciones/h24-rs-equipo.png ancho=96% El resultado de una rinomanometría anterior: curva de las dos fosas, resistencia según la presión y tabla. Paciente simulado con desviación y cornetes congestionados, 4 ciclos por fosa, en reposo (línea continua) y con vasoconstrictor (discontinua); las cifras son del modelo, no normas. Imagen propia hecha con RinoSim (→ Simuladores, en las preliminares).
- @84,19 | **Curva en reposo** de la fosa derecha (roja, continua): el promedio de los ciclos. Las líneas finas son cada ciclo.
- @75,11 | **Con vasoconstrictor** (discontinua): la misma fosa después de la prueba. Más flujo con la misma presión es menos resistencia.
- @80,69 | **Cuadrantes.** La fosa derecha (roja) va en I y III; la izquierda (azul), en II y IV. Presión en el eje horizontal, flujo en el vertical.
- @64,13 | **Recta de 0,4.** La diagonal punteada es la resistencia de referencia del libro: una curva que pasa por debajo de ella tiene más resistencia que 0,4.
- @59,62 | **75 y 150 Pa.** Las dos líneas verticales de rayas son las presiones en que se lee la resistencia.
- @76,77 | **Resistencia según la presión.** El gráfico pequeño es el B de la figura de las curvas, con la raya de referencia (0,4).
- @75,93.8 | **R 150.** Resistencia a 150 Pa de cada fosa: 150 Pa dividido por el flujo de la columna de al lado. En rojo lo que supera 0,4 (la derecha, 0,81); en verde lo que está dentro (la izquierda, 0,38).
- @92,94 | **R 150 con VC y cambio.** La derecha baja de 0,81 a 0,46 (−43 %): bajó, pero no llegó a 0,4, así que es **mixta** según la tabla de *Cómo se informa*. La izquierda ya estaba dentro de la referencia y, según el paso 7, no necesitaba la prueba.
- @-2,98.5 | **Total.** Las dos fosas en paralelo, 1 / RT = 1 / RD + 1 / RI: 0,26 en reposo y 0,18 con vasoconstrictor.
:::

Como ejemplo, el menú de un rinomanómetro sigue este orden, que otros equipos repiten con distinto nombre: *Measuring* → *Measuring of right nostril* → botón de tiempo (*t*) → contar los ciclos de la medición → *Continue with measuring* (cambiar el adaptador de fosa) → *Measuring of left nostril* → botón de tiempo → contar los ciclos → *Select documentation mode* → *Print result*. Memoriza la idea, no los nombres: **una fosa, un número de ciclos, la otra fosa, imprimir**.

### Paciente

Lo que se le dice al paciente al darle la hora:

- **Ningún vasoconstrictor, antialérgico ni descongestionante nasal en las 48 horas previas.**
- **No fumar ni beber alcohol en las 24 horas previas.**

Antes de medir, el paciente **se aclimata sentado 15 minutos** en la sala (cuentan los minutos de la anamnesis y de la rinoscopía). Se hace primero la anamnesis, la palpación y la rinoscopía anterior (→ H23). Una nariz recién llegada de la calle, con otro aire y otra temperatura, tiene la mucosa en otro estado que dentro de 15 minutos.

Se descartan antes de empezar los impedimentos de la técnica: una enfermedad respiratoria aguda, una perforación del tabique y una atresia de coana. Tampoco se examina a quien acaba de fumar.

:::comentario Lo que dicen las normas
Este libro pide 48 horas sin vasoconstrictores y 24 horas sin fumar ni beber alcohol, y 15 minutos de aclimatación. Las normas de estandarización piden evitar los fármacos que cambian la mucosa y aclimatar al paciente, pero **los plazos varían** de una fuente a otra y no se encontraron cifras idénticas a estas en las fuentes consultadas (Clement y Gordts, 2005). <!-- verificar: plazos de suspensión de fármacos, de abstención de tabaco y alcohol y de aclimatación en el informe de consenso de Clement y Gordts (2005) y en el informe de 1984; no se pudo leer el texto completo. --> La lógica es la misma en todas: que la nariz esté como suele estar.
:::

## Paso a paso

### 1. Instrucciones al paciente

Se le explica en pocas palabras: va a respirar con **normalidad**, **solo por la nariz** y con la **boca cerrada**, mientras tenga la máscara puesta. Se le pide naturalidad: un paciente que respira más fuerte o más lento de lo normal cambia el flujo y, con él, la resistencia (recuerda: la resistencia depende del flujo).

### 2. Adaptador en la fosa contraria

Se elige el adaptador del **tamaño de la narina**: uno chico no sella y uno grande la deforma. Una narina deformada cambia la válvula nasal y, con ella, lo que se está midiendo. Se conecta el adaptador al tubo de presión y se pone en la fosa **contraria** a la que se va a examinar. Se **parte por la fosa derecha** (adaptador en la izquierda) y se termina con la izquierda.

### 3. Comprobar el sello

Con el adaptador puesto, se presiona con el dedo la fosa **sin adaptador** y se le pide al paciente que respire. **No debe pasar aire por el adaptador.** Si pasa, hay una fuga, y la presión que mide el sensor no es la de la nasofaringe. Se corrige antes de medir. La máscara va sobre la nariz y la boca, con una presión leve para que no se escape aire, pero sin aplastar la nariz.

### 4. Medir la primera fosa

En el equipo se elige *Measuring of right nostril* y se inicia la medición con el botón de tiempo. El paciente respira con normalidad mientras el equipo cuenta los ciclos que se le configuraron; la curva se promedia (los equipos suelen promediar varios ciclos, de 3 a 5, Vogt y cols., 2016). Se mira la curva mientras se registra: debe ser regular y sin interrupciones.

### 5. Cambiar de fosa y medir la segunda

Se saca el adaptador, se pone en la otra fosa y se repite el procedimiento (*Continue with measuring* → *Measuring of left nostril*). **Se vuelve a comprobar el sello.**

### 6. Documentar

Se elige el modo de documentación y se imprime el resultado. Los valores se pasan al formulario *Rinomanometría anterior*: fosa, presión de referencia, flujo, resistencia. Se anota también, siempre, **a qué presión** se leyó.

### 7. Decidir si se hace la prueba con vasoconstrictor

<!-- Protocolo ORL 2019: daba la unidad como "Pa/seg/cm". Se corrigió a Pa/(cm³/s) (equivale a Pa·s/cm³): la resistencia es presión sobre flujo volumétrico; "/cm" es un error de unidades (Clement y Gordts, 2005; Broms y cols., 1982). -->

El valor de referencia de este libro para la **resistencia unilateral a 150 Pa es 0,4 Pa/(cm³/s) o menos**. Si una fosa lo supera, se aplica el vasoconstrictor **en esa fosa** y se mide de nuevo. Si las dos están dentro del valor, el examen termina en reposo: la permeabilidad nasal es buena.

:::comentario Lo que dicen las normas
**El valor de 0,4 depende de la población, del equipo y de cómo se mide.** En un estudio de adultos sanos de China (505 sujetos), la resistencia unilateral a 150 Pa tuvo una media de 0,51 Pa/(cm³/s), con un intervalo de 95 % entre 0,09 y 0,94, y la total una media de 0,24 (intervalo entre 0,11 y 0,37) (Ren y cols., 2018). Otros grupos, con otras poblaciones y otros equipos, dan otras cifras. El mismo estudio señala que el mismo examen, a 75 Pa, da valores más bajos. Por eso este libro enseña esta cifra como **referencia de trabajo** y pide que el informe diga con qué se compara.

Hay además una crítica más de fondo. El grupo que desarrolló la **rinomanometría de 4 fases** (Vogt y cols., 2016) sostiene que el flujo (o la resistencia) a 150 Pa es una estimación y no una medición, porque sale de un solo punto de la curva, y que un porcentaje de pacientes ni siquiera llega a esa presión. Propone en cambio el **logaritmo de la resistencia efectiva (Reff)**, que integra toda la respiración, y clasifica la obstrucción en cinco grados según percentiles de una serie de 36.563 mediciones. El libro mantiene el método clásico a 150 Pa porque es el que se enseña aquí y el que trae casi todo equipo; si el tuyo ofrece los parámetros de 4 fases, son una segunda lectura válida.
:::

### 8. Aplicar el vasoconstrictor

1. **Explícale al paciente** qué le vas a hacer, para qué y qué va a sentir: el medicamento achica la mucosa y la nariz se siente más abierta. Si le escurre por la nariz, que **se seque con el pañuelo y no se suene**: sonarse fuerte cambia la mucosa y la medición.
2. Saca la tapa del frasco y **bombea el atomizador hasta que salga neblina**, para que la dosis salga bien.
3. Con la técnica de rinoscopía (→ H23), abre la fosa del paciente e introduce la punta del aplicador.
4. Aplica **dos disparos** ("puff") mientras el paciente **inspira por la nariz**: así el aerosol acompaña al aire hacia el interior de la nariz.
5. **Espera 15 minutos** para que el medicamento penetre y haga efecto. Puedes aprovechar el tiempo para repetir la rinoscopía (a los 10 minutos ya se puede).
6. Repite la medición con el **mismo procedimiento** del reposo, con el mismo adaptador y el mismo orden.

:::comentario Lo que dicen las normas
Este libro espera 15 minutos tras el vasoconstrictor. En la serie de Vogt y cols. (2016) la segunda medición se hizo **10 minutos** después de xylometazolina al 0,1 % en atomizador, y el consenso internacional pide estandarizar más estrictamente el procedimiento de descongestión (Clement y Gordts, 2005), sin que se haya confirmado aquí una cifra única. <!-- verificar: tiempo y dosis de descongestión que fija el consenso de Clement y Gordts (2005); la cifra de 10 minutos es de Vogt y cols. (2016). --> El principio es el mismo: esperar lo suficiente para que el efecto sea máximo y **medir siempre con el mismo tiempo** para poder comparar.
:::

:::ayuda Ayuda memoria
- **Ni vasoconstrictor ni humo antes.** Aclimatación sentado. Máscara sobre nariz y boca, sin fugas.
- **Adaptador en la fosa contraria**, del tamaño justo; comprueba el sello con el dedo.
- **Una fosa, luego la otra.** Respiración normal por la nariz, boca cerrada.
- **R = ΔP / V̇** a **150 Pa**. Unilateral de referencia: **≤ 0,4 Pa/(cm³/s)**.
- **1 / RT = 1 / RD + 1 / RI**.
- Alterada: vasoconstrictor en esa fosa, 2 puff inspirando, esperar, medir igual.
:::

## Cómo se informa

### La resistencia a 150 Pa

Para cada fosa, el equipo da la presión y el flujo en el punto de referencia, y la resistencia es su cociente. Se informa **en Pa/(cm³/s)**, indicando la presión. Por ejemplo, una presión de 150 Pa con un flujo de 250 cm³/s:

R = 150 / 250 = **0,60 Pa/(cm³/s)**

Eso, en la fosa derecha, está por encima del valor de referencia de 0,4: es una fosa con resistencia aumentada, y se pasa a la prueba con vasoconstrictor.

### Qué se informa en reposo

- **Dentro del rango de referencia** (≤ 0,4 por fosa): buena permeabilidad nasal.
- **Fuera del rango:** se hace la prueba con vasoconstrictor (PVC).

Siempre se **señala en qué fosa** se obtuvo cada resultado: fosa nasal derecha (FND), fosa nasal izquierda (FNI) o ambas.

### Después del vasoconstrictor

Se compara la resistencia de la fosa tratada con la de reposo:

Tabla: Qué indica la resistencia después del vasoconstrictor (PVC)

| Después del vasoconstrictor | Tipo de obstrucción | Por qué |
|---|---|---|
| Igual que en reposo | **Mecánica** (estructural) | No había mucosa que quitar |
| Baja, pero no llega al valor de referencia | **Mixta** | Había mucosa y estructura |
| Baja del todo, hasta el valor de referencia | **Vasomotora** (mucosa) | Todo era mucosa |
| Sube respecto del reposo | **Vasomotora**, sin descartar un componente mecánico ("efecto rebote") | Ver el recuadro |

:::imagen ilustraciones/h24-rs-vasoconstrictor.svg ancho=86% Las tres respuestas al vasoconstrictor en la fosa derecha, como resistencia según la presión: reposo (línea continua) y con vasoconstrictor (discontinua). La raya horizontal punteada es el valor de referencia (0,4) y las verticales, 75 y 150 Pa. A: vasomotora, a 150 Pa baja de 0,57 a 0,29 y queda bajo la referencia. B: mixta, baja de 0,80 a 0,46 sin llegar a la referencia. C: mecánica, 0,53 y 0,48: casi no cambia. Pacientes simulados; las cifras son del modelo, no normas. Imagen propia hecha con RinoSim (→ Simuladores, en las preliminares).
:::

:::comentario Lo que dicen las normas
**El "efecto rebote".** Este libro interpreta una resistencia que **sube** después del vasoconstrictor como vasomotora con un posible componente mecánico oculto ("efecto rebote"). Es la lectura del protocolo, pero conviene saber que el rebote de los vasoconstrictores (la congestión que sigue a su efecto) se describe como una consecuencia del **uso repetido y prolongado**, no de una sola dosis medida a los 15 minutos. <!-- verificar: no se encontró una fuente que describa efecto rebote a los 10 a 15 minutos de una dosis única; la explicación habitual es el uso crónico (rinitis medicamentosa). --> Ante un aumento después del vasoconstrictor, lo primero es descartar los motivos prácticos: un cambio del ciclo nasal entre las dos mediciones, un adaptador que ya no sella o un paciente que respira distinto. Si se repite con la técnica bien hecha, se informa como indica la tabla.

**"Disminución total".** Una fosa puede quedar dentro del valor de referencia y seguir teniendo una estructura alterada que no molesta; la rinomanometría informa de resistencia, no de anatomía. El informe lo dice así, y la causa se busca con la rinoscopía y la endoscopía (→ H23).
:::

### Leer la curva

La curva dice más que el número. Una curva normal es regular, simétrica entre la inspiración y la espiración, y de forma de S aplanada: sube casi recta al principio y luego se aplana. Una curva empinada, pegada al eje del flujo, es una fosa muy amplia (también la de una nariz atrófica); una curva baja, pegada al eje de la presión, que casi no despega, es una fosa obstruida. <!-- Protocolo ORL 2019 / borrador: decía "muy plana y baja" para la fosa amplia, lo que contradice el Fundamento (fosa abierta = curva empinada, pegada al eje del flujo). Se corrigió al sentido del Fundamento. --> Una curva con **pausas** o saltos suele ser del paciente: respira a tirones, traga, o la máscara se mueve. En ese caso no se informa: se repite.

:::imagen ilustraciones/h24-rs-irregular.svg ancho=100% Una respiración irregular. Los ciclos sueltos (las líneas finas) no se parecen entre sí, tienen pausas y saltos, y el promedio (la línea gruesa) se quiebra. Los ciclos varían 15 % en la fosa derecha y 18 % en la izquierda: no son reproducibles y se repite la medición. Paciente simulado; las cifras son del modelo, no normas. Imagen propia hecha con RinoSim (→ Simuladores, en las preliminares).
:::

### Ejercicios: de los números al informe

Estos ejercicios no son de pacientes: son números inventados para practicar el cálculo. Todos se leen a **150 Pa**.

**Ejercicio 1. Una fosa.** Fosa derecha: 150 Pa y 250 cm³/s. R = 150 / 250 = **0,60**. Fosa izquierda: 150 Pa y 500 cm³/s. R = 150 / 500 = **0,30**.

**Ejercicio 2. El total.** Con las dos fosas del ejercicio anterior:

1 / RT = 1 / 0,60 + 1 / 0,30 = 1,667 + 3,333 = 5,0, por lo tanto **RT = 0,20**.

Se comprueba sumando flujos: 250 + 500 = 750 cm³/s, y 150 / 750 = 0,20. El total (0,20) es menor que la fosa más abierta (0,30).

**Ejercicio 3. Después del vasoconstrictor.** La fosa derecha, la de 0,60, recibe el vasoconstrictor y ahora, a 150 Pa, mide 400 cm³/s: R = 150 / 400 = **0,375**, o 0,38 redondeado. Bajó **37,5 %** y quedó bajo el valor de referencia de 0,4: la obstrucción de esa fosa era **vasomotora**. Con la izquierda sin tocar (0,30), la resistencia total queda en 1 / RT = 1 / 0,375 + 1 / 0,30 = 2,667 + 3,333 = 6,0, o **RT = 0,17**.

**Ejercicio 4. Mixta y mecánica.** Si la misma fosa derecha hubiera medido 330 cm³/s después del vasoconstrictor, R = 150 / 330 = **0,45**: bajó 24 %, pero no llegó a 0,4: **mixta**. Si hubiera medido 255 cm³/s, R = **0,59**: bajó 2 %, un cambio que cabe en la variación entre dos mediciones: **mecánica**.

**Ejercicio 5. Cuando el paciente no llega a 150 Pa.** Un paciente con una nariz muy amplia llega solo a 110 Pa con un flujo de 300 cm³/s: R = 110 / 300 = **0,37 a 110 Pa**. No se puede comparar con los valores de 150 Pa, porque la resistencia sube con la presión; se informa tal cual, con su presión, o se usa un método que lo resuelva (Broms; ver *Fundamento*).

**Ejercicio 6. Unidades.** 0,30 Pa/(cm³/s) equivale a 0,30 × 1000 / 98,07 ≈ **3,1 cmH₂O/L/s**. Y 600 cm³/s son 36 L/min.

### Ejemplo de informe

> **Rinomanometría anterior activa.** Reposo 15 minutos; sin vasoconstrictores 48 horas antes. Resistencia a 150 Pa en reposo: FND 0,60; FNI 0,30; total 0,20 Pa/(cm³/s). **FND fuera del valor de referencia** (≤ 0,4); FNI dentro. Se aplica oximetazolina, 2 puff, en FND; tras 15 minutos, FND 0,38. **Conclusión:** obstrucción nasal de tipo **vasomotora en la fosa nasal derecha**; fosa nasal izquierda con buena permeabilidad.

## Errores frecuentes

- **Informar la resistencia sin la presión.** La resistencia cambia con la presión: sin ella, el número no se puede comparar.
- **Fuga en la máscara o en el adaptador.** El sensor no mide la nasofaringe y la curva sale mal. Por eso se comprueba el sello antes de cada fosa.
- **Adaptador que deforma la narina.** Cambia la válvula y, con ella, la resistencia de la fosa que quieres medir.
- **Paciente que respira distinto.** Un paciente que fuerza la respiración o respira por la boca da una curva que no es de su nariz. La instrucción lo previene.
- **Medir con el ciclo nasal o un resfrío.** Una fosa puede estar congestionada hoy por el ciclo; si el hallazgo no calza, se repite otro día.
- **Medicamentos o tabaco en las horas previas.** El resultado deja de representar a la nariz.
- **Cambiar el tiempo de espera del vasoconstrictor.** Si cambias el tiempo entre una medición y otra, comparas dos cosas distintas.
- **Interpretar una curva con pausas o saltos.** Son del paciente o de la máscara, no de la nariz. Se repite.
- **Promediar las resistencias de las dos fosas.** El total es en paralelo: el promedio de 0,60 y 0,30 daría 0,45, pero el total real es 0,20.

:::ojo Ojo clínico
**Una fosa "obstruida" en el examen no siempre molesta, y una nariz que molesta no siempre da un número alto.** La rinomanometría mide resistencia, y la queja del paciente es sensación. Cuando las dos no calzan, ese desacuerdo es un hallazgo. Y recuerda que el total puede estar normal con una fosa muy resistente si la otra compensa: **informa siempre cada fosa por separado**.
:::

:::pregunta Preguntas para practicar
1. Fosa derecha: 150 Pa y 600 cm³/s. Fosa izquierda: 150 Pa y 300 cm³/s. Calcula la resistencia de cada una y la total. ¿Cuál es la fosa más abierta y por qué la total es menor que las dos?
2. Una fosa mide 0,55 y, tras el vasoconstrictor, 0,52. Otra mide 0,55 y, tras el vasoconstrictor, 0,30. ¿Cómo se informa cada una? ¿Qué diferencia hay en lo que se puede ofrecer al paciente?
3. Un paciente llega con su vasoconstrictor habitual puesto hace una hora. ¿Qué pasa con la resistencia de reposo y qué pasa con la prueba con vasoconstrictor?
4. Explica con la ecuación ΔP = k₁·V̇ + k₂·V̇² por qué la resistencia a 150 Pa es mayor que a 75 Pa en la misma nariz.
5. Una fosa tapada del todo no deja pasar nada de aire. ¿Cuál es la resistencia total del paciente, si la otra mide 0,25?
6. Mides la fosa izquierda y, al comprobar el sello, pasa aire por el adaptador. ¿Qué mide el sensor y por qué no sirve la curva?
7. La fosa derecha de un paciente mide 0,60 hoy y 0,25 la semana siguiente, sin tratamiento. Da dos explicaciones posibles y una forma de distinguirlas.
8. ¿Por qué el total no es el promedio de las dos fosas? Demuéstralo con 0,60 y 0,30.
:::

## Referencias

1. Clement PA, Gordts F; Standardisation Committee on Objective Assessment of the Nasal Airway, IRS, and ERS. Consensus report on acoustic rhinometry and rhinomanometry. Rhinology. 2005;43:169-79. PMID: 16218509.
1. Clement PA. Committee report on standardization of rhinomanometry. Rhinology. 1984;22:151-5. PMID: 6505516.
1. Vogt K, Wernecke KD, Behrbohm H, Gubisch W, Argale M. Four-phase rhinomanometry: a multicentric retrospective analysis of 36,563 clinical measurements. Eur Arch Otorhinolaryngol. 2016;273:1185-98. doi:10.1007/s00405-015-3723-5. PMID: 26198284.
1. Vogt K, Jalowayski AA, Althaus W, Cao C, Han D, Hasse W, et al. 4-Phase-Rhinomanometry (4PR): basics and practice 2010. Rhinol Suppl. 2010;21:1-50. PMID: 20649107.
1. Broms P, Jonson B, Lamm CJ. Rhinomanometry. II. A system for numerical description of nasal airway resistance. Acta Otolaryngol. 1982;94:157-68. PMID: 7124382.
1. Broms P. Rhinomanometry. III. Procedures and criteria for distinction between skeletal stenosis and mucosal swelling. Acta Otolaryngol. 1982;94:361-70. PMID: 6183919.
1. Wong EH, Eccles R. Comparison of classic and 4-phase rhinomanometry methods, is there any difference? Rhinology. 2014;52:360-5. doi:10.4193/Rhino13.187. PMID: 25479215.
1. Ren L, Zhang L, Duan S, Zhang W, Zhang Y. Nasal airflow resistance measured by rhinomanometry in a healthy population of China. Int Forum Allergy Rhinol. 2018;8:1308-14. doi:10.1002/alr.22177. PMID: 29996010.
1. Flanagan P, Eccles R. Spontaneous changes of unilateral nasal airflow in man. A re-examination of the "nasal cycle". Acta Otolaryngol. 1997;117:590-5. PMID: 9288218.
1. Hasegawa M, Kern EB. The human nasal cycle. Mayo Clin Proc. 1977;52:28-34. PMID: 609283.
1. Ferris BG Jr, Mead J, Opie LH. Partitioning of respiratory flow resistance in man. J Appl Physiol. 1964;19:653-8. PMID: 14195575.
1. Rohrer F. Der Strömungswiderstand in den menschlichen Atemwegen und der Einfluss der unregelmässigen Verzweigung des Bronchialsystems auf den Atmungsverlauf in verschiedenen Lungenbezirken. Pflügers Arch. 1915;162:225-99. doi:10.1007/BF01681259.
