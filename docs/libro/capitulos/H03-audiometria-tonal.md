# H3. Audiometría tonal

:::objetivos En esta herramienta
- Explicar qué es un umbral tonal y por qué se mide por vía aérea y por vía ósea.
- Seguir el camino del sonido por cada vía y deducir de él qué lesión deja ver cada una.
- Explicar por qué el audiograma se dibuja en dB HL, por qué el umbral se busca en ascenso y por qué se miden esas frecuencias.
- Buscar un umbral con el método ascendente (10 dB abajo, 5 dB arriba) y el criterio de 2 de 3.
- Poner fonos y vibrador sin fabricar pérdidas que el paciente no tiene.
- Dibujar el audiograma con los símbolos estándar y leer en él el tipo, el grado, la configuración, la simetría y la confiabilidad.
- Reconocer en qué cambia la técnica en la audiometría de screening, la ocupacional (PREXOR) y la de alta frecuencia.
:::

La audiometría tonal es el examen que más vas a hacer y el que sostiene a casi todos los demás. El nivel de la logoaudiometría, el ruido del enmascaramiento, las pruebas supraliminares y la lectura de un PEAT parten de un audiograma. Si los umbrales están mal tomados, todo lo que viene después hereda el error. Esta herramienta trata de cómo tomarlos bien y de cómo escribirlos para que otro los lea igual que tú.

## Para qué sirve

La audiometría tonal responde dos preguntas:

1. **¿Cuánto oye cada oído en cada frecuencia?** Es el umbral: el tono más suave que el paciente detecta, de 125 a 8.000 Hz.
2. **¿Dónde está el problema?** Comparando la vía aérea con la ósea se sabe si la pérdida es de transmisión (oído externo o medio), de la cóclea o del nervio, o de ambos.

Se pide frente a cualquier queja auditiva, acúfeno o vértigo; antes de indicar un audífono o una cirugía de oído; para seguir a quien está expuesto a ruido o a fármacos ototóxicos; en el examen preocupacional y en la evaluación médico-legal.

Tiene dos límites que conviene tener presentes desde el principio. Es una prueba **conductual**: depende de que el paciente entienda, coopere y responda con honestidad. Y mide **detección**, no comprensión ni sitio de lesión retrococlear. Por eso ningún audiograma se interpreta solo: se contrasta con la acumetría (→ H2), la logoaudiometría (→ H5) y la impedanciometría (→ H7).

Para aprender a leer el audiograma desde el principio, el capítulo parte con su radiografía y con Luis, el primer caso.

{{caso h3_p41}}

## Fundamento

### Radiografía de un audiograma

Todo lo que sigue termina en este gráfico. Es un audiograma con **todos** sus elementos juntos. Aquí solo se nombran; el resto del capítulo explica de dónde sale cada uno, y *Cómo se informa* enseña a sacar de él el tipo, el grado y la configuración. El derecho va siempre en <span class="od">rojo</span> y el izquierdo en <span class="oi">azul</span>.

:::figura h3radiografia audiograma
- @OD 125 | **Frecuencias**: graves a la izquierda, agudos a la derecha, de octava en octava. Las interoctavas (3 y 6 kHz) llevan un rótulo más chico.
- @OI 125 | **dB HL**: crecen hacia abajo; más abajo es oír peor. El 0 no es silencio, es lo que oye un joven normal. La franja gris, hasta 20 dB, es lo normal.
- @OD 250 | <span class="od">○</span> **aérea del OD sin enmascarar**, 25 dB. Los puntos de la aérea se unen con línea continua.
- @OD 1000 | <span class="od">△</span> **aérea del OD enmascarada**, 60 dB: con el tono tan fuerte, el OI podía oírlo por el OD y se le puso ruido (→ H4).
- @OI 1000 | <span class="oi">✕</span> **aérea del OI sin enmascarar**, 20 dB.
- @OI 2000 | <span class="oi">□</span> **aérea del OI enmascarada**, 60 dB.
- @OD osea 1000 | <span class="od">[</span> **ósea del OD enmascarada**, 20 dB. La ósea se une con línea punteada.
- @OD osea 4000 | <span class="od">&lt;</span> **ósea del OD sin enmascarar**, 65 dB: no hizo falta ruido porque la aérea y la ósea están juntas.
- @OI osea 500 | <span class="oi">&gt;</span> **ósea del OI sin enmascarar**, 10 dB; en 2 kHz, <span class="oi">]</span> enmascarada.
- @OD 500 | **Gap aéreo-óseo**: 55 − 20 = 35 dB en 500 Hz. En los agudos la aérea y la ósea van juntas: en el OD la pérdida es **mixta**.
- @OD 8000 | **Sin respuesta**: no oyó ni a la salida máxima del equipo. El símbolo va en el tope con una **flecha** hacia abajo.
- <span class="od">◢</span> <span class="oi">◣</span> **Triángulos rellenos de abajo**: el umbral de molestia (LDL), unidos con guiones (→ H5). En el OD, en 4 kHz no marcó molestia ni al máximo: lleva la misma flecha. En el OI, entre 95 y 105 dB.
:::

Para tomar bien un umbral hay que entender tres cosas: qué camino recorre el tono en cada vía, qué quiere decir "oír" justo en el límite de la audición y de dónde sale el cero del audiómetro. De esas tres sale casi todo el paso a paso: cada regla de la técnica responde a una de ellas. La anatomía está en B1, la fisiología en B2 y la física del decibel en B4. Aquí va lo justo para entender por qué la técnica es como es.

### El camino del sonido por vía aérea

El fono deja el tono en la entrada del conducto. Desde ahí el sonido recorre una cadena de estructuras, y cada una aporta algo:

1. **Pabellón y conducto.** Llevan el sonido hasta la membrana timpánica y lo refuerzan: el conducto resuena y le suma unos 15 a 20 dB a las frecuencias cercanas a 2,5-3 kHz (Shaw, 1974). Un conducto tapado por cerumen, por un cuerpo extraño o por un conducto blando que colapsa bajo el fono le quita sonido al tono antes de que llegue a ninguna parte.
2. **Membrana timpánica y cadena de huesecillos.** El sonido viaja por aire, y la cóclea está llena de líquido. Si el aire chocara directo con el líquido, casi toda la energía rebotaría. El oído medio adapta esa diferencia de impedancias: junta la fuerza que recibe la membrana, que es grande, sobre la platina del estribo, que es chica, y la cadena le suma un pequeño efecto de palanca. Medida en huesos temporales, esa ganancia real es de unos 20 dB, con su máximo cerca de 1 kHz (Aibara y cols., 2001; Merchant y cols., 1998).
3. **Ventana oval.** La platina del estribo empuja los líquidos del oído interno. La ventana redonda cede hacia el oído medio y deja que se muevan.
4. **Cóclea.** El movimiento del líquido hace vibrar la membrana basilar en una onda que viaja desde la base hacia el ápice y alcanza su máximo en un lugar distinto para cada frecuencia (Robles y Ruggero, 2001). Las **células ciliadas externas** amplifican esa vibración cuando el sonido es suave, en unos 40 a 50 dB (Dallos, 2008). Las **células ciliadas internas** la convierten en impulsos del nervio.
5. **Nervio y vía auditiva.** Llevan la señal al tronco y a la corteza, que es donde, al final, el paciente "lo oye" y aprieta el botón.

La vía aérea pone a prueba **todo** ese camino. Si el umbral aéreo es normal, todo el camino funciona, al menos para detectar un tono. Si está alterado, la falla puede estar en cualquier eslabón, y la aérea sola no dice en cuál.

### El camino por vía ósea: directo a la cóclea

El vibrador apoyado en la mastoides hace vibrar el cráneo. La cóclea está excavada en el hueso temporal y vibra con él, así que el sonido llega al oído interno **sin depender del conducto, de la membrana ni de la cadena**. Se suele resumir en tres mecanismos que actúan a la vez (Stenfelt y Goode, 2005):

- **Compresión de la cápsula.** Las paredes óseas de la cóclea se deforman con la vibración y desplazan los líquidos entre las dos ventanas.
- **Inercia.** Los líquidos de la cóclea y la cadena de huesecillos no están soldados al cráneo: cuando el cráneo se mueve, se quedan un poco atrás. Ese desfase es un movimiento relativo, y la cóclea lo detecta como sonido.
- **Radiación al conducto.** Las paredes del conducto vibran y emiten sonido dentro de él, que entra por el camino aéreo de siempre. Con el conducto abierto pesa poco. Si lo tapas, ese sonido queda atrapado y la ósea mejora en los graves: es el **efecto de oclusión** (→ H4).

Stenfelt y Goode (2005) agregan una vía por los líquidos del cráneo; el detalle está en B2. Para la técnica, lo que importa es esto: la vía ósea **se salta casi todo el oído externo y el medio**. En la práctica, mide la cóclea y lo que viene después de ella.

:::ojo Ojo clínico
La vía ósea **no es de un oído**. El cráneo vibra entero y el sonido llega a las dos cócleas casi con la misma intensidad: la atenuación transcraneal por vía ósea va de 0 a unos 10 dB (Stenfelt, 2012). Una ósea sin enmascarar refleja la **mejor cóclea**, esté donde esté el vibrador. → H4.
:::

### Qué deja ver cada vía: el gap

Si la aérea recorre todo el camino y la ósea solo el último tramo, al compararlas se sabe **en qué tramo se pierde el sonido**:

- **Aérea alterada y ósea normal.** El sonido se pierde antes de la cóclea, en el oído externo o el medio: **hipoacusia conductiva**. La diferencia entre las dos vías es el **gap aéreo-óseo**: lo que el tono pierde en el tramo que solo recorre la aérea.
- **Las dos alteradas y juntas.** El tramo de transmisión funciona y la falla está en la cóclea o más allá: **hipoacusia sensorioneural**.
- **Las dos alteradas, con gap.** Hay de ambas cosas: **hipoacusia mixta**.

:::imagen ilustraciones/h03-dos-vias.svg ancho=96% Las dos vías y lo que deja ver cada una. La aérea pasa por todo el oído; la ósea se salta el externo y el medio. Por eso la ósea dice cómo está la cóclea y la distancia entre las dos dice cuánto pierde la transmisión.
:::

Del mismo dibujo salen tres reglas que vas a usar todo el tiempo:

- **La ósea no puede ser peor que la aérea.** Todo lo que recorre la ósea lo recorre también la aérea. Una ósea 5 o 10 dB peor que la aérea cabe en la incertidumbre de dos umbrales. Si la diferencia es mayor, casi siempre hay un error de técnica (un vibrador mal puesto, el transductor equivocado en la pantalla) y se repite.
- **El gap tiene techo.** Cuando el tono por vía aérea es muy fuerte, el fono hace vibrar el cráneo y el sonido llega a la cóclea por vía ósea, aunque el oído medio no transmita nada. Por eso una pérdida puramente conductiva rara vez pasa de unos 60 dB. Una aérea mucho peor que eso con la ósea normal suele ser una ósea **sin enmascarar** que en realidad es la del otro oído (→ H4). <!-- verificar: techo de la hipoacusia conductiva en torno a 60 dB; es el GAP_MAX_DB de LabSim (respaldado en BibliografiaPatologias.php con Farahmand y cols., 2016, para la disyunción completa). Falta una fuente general para la frase. -->
- **El audiograma no separa la cóclea del nervio.** Una lesión de la cóclea y una del nervio dan las dos una sensorioneural, con la ósea junto a la aérea. Para separarlas están la logoaudiometría (→ H5), las pruebas supraliminares (→ H6), las emisiones (→ H9) y el PEAT (→ H10).

### La ósea también puede caer sin daño coclear

En la fijación del estribo la ósea empeora alrededor de 2 kHz aunque la cóclea esté sana: es la **muesca de Carhart** (Carhart, 1950). Se explica con el mecanismo de inercia de arriba: parte de la conducción ósea depende de que la cadena se mueva y resuene, y una cadena fija pierde esa resonancia (Homma y cols., 2009). La muesca se lee como transmisión, no como lesión del oído interno: después de una cirugía exitosa, la ósea vuelve a subir.

### El umbral es una probabilidad

Lejos por debajo del umbral, el paciente nunca oye el tono; bien por encima, lo oye siempre. Entre medio hay una franja de pocos decibeles en que **el mismo tono, al mismo nivel, a veces se detecta y a veces no**. La señal que llega al nervio compite con la actividad de fondo del propio sistema auditivo, y la atención del paciente sube y baja. La curva que une el nivel del tono con la proporción de veces que se detecta es la **función psicométrica**.

:::imagen ilustraciones/h03-funcion-psicometrica.svg ancho=96% El umbral como probabilidad de detección. Entre el nivel que nunca se oye y el que se oye siempre hay una franja de pocos decibeles; el umbral es el punto de esa subida en que se detecta la mitad de los tonos.
:::

Por eso el umbral se define en el medio de esa subida: el nivel en que el paciente detecta **la mitad** de los tonos. En la clínica no hay tiempo para presentar cien tonos por nivel, y el audiómetro avanza de a 5 dB. La forma práctica de estimar ese 50 % es la regla de las normas: **el nivel más bajo en que el paciente responde en al menos la mitad de las presentaciones en ascenso**, con un mínimo de 2 de 3 (ASHA, 2005; ISO 8253-1, 1989).

En ese punto también decide el paciente. Cada persona fija, sin darse cuenta, cuán segura tiene que estar antes de apretar el botón. El que espera a estar seguro corre su curva hacia la derecha y da umbrales peores que los reales. El que aprieta ante cualquier cosa responde también en los silencios. La instrucción y la técnica apuntan a las dos cosas: "aunque sea apenas" baja la exigencia del paciente, y los silencios irregulares dejan ver las respuestas falsas.

### El cero del audiómetro: dB HL

El oído no es igual de sensible en todas las frecuencias. Medido con un micrófono, en **dB SPL** (nivel de presión sonora), un oído joven normal necesita mucha más presión en los graves que en los medios. Con el fono TDH-39, el umbral normal está en 45 dB SPL a 125 Hz, en 25,5 a 250 Hz y en apenas 7 a 1 kHz (ISO 389-1, 2017). <!-- Valores de la tabla ISO 389-1 para el TDH-39, leídos en la hoja técnica del Interacoustics AT235 (la misma que usa Bibliografia.php, clave AT235). --> Si el audiograma se dibujara en dB SPL, un oído normal sería una curva, distinta para cada fono, y habría que memorizarla para saber si un umbral es normal.

El audiómetro resuelve eso trabajando en **dB HL** (*hearing level*, nivel de audición). En cada frecuencia, **0 dB HL** es el nivel que detecta un adulto joven típico, otológicamente normal, entre 18 y 25 años (ISO 389-7, 2019). <!-- verificar: el rango de 18 a 25 años se confirmó en la edición 1996 de la ISO 389-7; no se leyó la de 2019. --> El equipo guarda esa referencia para cada frecuencia y cada transductor, y la resta. Así, un oído normal dibuja una **línea recta cerca de 0**, y lo que el audiograma muestra es directamente cuánto le falta a ese oído respecto de lo normal.

:::imagen ilustraciones/h03-hl-spl.svg ancho=96% El mismo oído normal, en dB SPL y en dB HL. En SPL el umbral normal cambia con la frecuencia: los graves necesitan mucha más presión. En HL se resta esa referencia, el oído normal queda en 0 en todas y cualquier pérdida se lee como distancia a esa línea.
:::

De aquí salen varias cosas que se ven a diario:

- **El cero es de cada transductor.** Las referencias están en la serie ISO 389: una parte para los fonos supraaurales, otra para los de inserción, otra para el vibrador y otra para la alta frecuencia. Por eso el audiómetro se calibra con sus propios fonos, y cambiar de fono sin recalibrar desplaza todos los umbrales.
- **Un umbral de −5 o −10 dB HL es posible.** Es alguien que oye mejor que la mediana. No es un error.
- **El dB HL no es el dB SL.** El dB SL (*sensation level*) se mide desde el umbral del propio paciente: 20 dB SL es 20 dB por encima de su umbral. Lo usan la logoaudiometría y las supraliminares (→ H5, H6).

**¿Por qué el audiograma se dibuja "al revés"?** Porque lo que se grafica no es cuán fuerte oye el paciente, sino **cuánto hay que subir el tono para que lo detecte**. Los dB HL crecen hacia abajo: un punto más abajo es un oído que necesita más intensidad, es decir, que oye peor. Así, cuando la audición cae, la curva cae, y el audiograma se lee como una pérdida.

### Por qué el umbral se busca así

Cada detalle del método de búsqueda responde a cómo se comporta el oído cerca de su límite.

- **En ascenso.** El umbral se toma con tonos que aparecen después de uno que el paciente no oyó. Ya en los años treinta los clínicos notaban que un tono continuo se "apaga" (adaptación) y que las series ascendentes daban umbrales más estables. Hughson y Westlake dejaron por escrito el umbral en ascenso con tonos cortos contra silencio, y Carhart y Jerger (1959) le dieron su base al comparar la búsqueda ascendente con la descendente (Jerger, 2018). Una forma simple de entenderlo: al bajar, el paciente viene de oír el tono y sabe cómo suena, y la expectativa puede hacerlo responder a un nivel que ya no detecta; al subir, cada respuesta es una detección nueva.
- **Baja 10, sube 5.** Bajar de a 10 lleva rápido bajo el umbral con pocos tonos, y cada tono cuesta tiempo y atención del paciente. Subir de a 5 da la resolución con que se dibuja y se informa el audiograma. Es un compromiso entre precisión y tiempo.
- **Tonos de 1 a 2 segundos.** El oído suma la energía del tono durante sus primeras décimas de segundo: un tono muy corto necesita más intensidad para detectarse. Esa suma se completa en unos 30 a 70 ms en los agudos y en 125 a 175 ms en los graves (Watson y Gengel, 1969). Un tono de 1 a 2 s la supera con holgura, así que la duración deja de mover el umbral. Más largo tampoco conviene: el tono continuo se adapta y el examen se alarga. <!-- verificar: volumen y páginas de Watson y Gengel (1969), JASA 46(4B):989-97, citados de memoria en la investigación. -->
- **Pulsado o continuo.** Dan el mismo umbral y la misma repetibilidad, pero dos de cada tres pacientes prefieren el pulsado cuando el tono es suave o agudo (Burk y Wiley, 2004). El botón *Pulsado* del audiómetro es para eso.
- **Silencios irregulares, nunca más cortos que el tono.** Con un ritmo fijo el paciente aprende el compás y aprieta por anticipación. Si el silencio varía, una respuesta sin tono queda a la vista como lo que es: una respuesta falsa (ASHA, 2005; BSA, 2018).
- **Familiarización y aprendizaje.** La primera vez, el paciente no sabe qué tan suave es "apenas", y sus primeras respuestas tienden a ser peores. Un tono claro le muestra qué tiene que buscar. Repetir 1 kHz al final del primer oído mide si siguió aprendiendo en el camino: si la segunda vez sale mejor, las primeras frecuencias pueden estar subestimadas. La norma ISO pide, ante una mejora de 10 dB o más, volver a medir las demás frecuencias (ISO 8253-1, 1989).
- **El oído mejor primero.** Al llegar al oído peor ya conoces el otro, y puedes ver frecuencia por frecuencia si el tono puede estar cruzando hacia él (→ H4).

### Por qué esas frecuencias

El audiograma mide de 125 a 8.000 Hz, en octavas y algunas interoctavas. Hay tres razones.

**Es el rango del habla.** Las vocales concentran su energía en los graves y los medios. Muchas consonantes, como la *s*, la *f* o la *ch*, la tienen en los agudos, y son las que más ayudan a distinguir una palabra de otra. Por eso una pérdida de agudos deja oír la voz y no entenderla (→ H5, cap. 5).

**Cada frecuencia examina un lugar de la cóclea.** La cóclea está ordenada por frecuencias: la base, junto a la ventana oval, responde a los agudos, y el ápice a los graves. La membrana basilar es angosta y rígida en la base, de unos 0,1 mm, y ancha y flexible en el ápice, de unos 0,5 mm; por eso cada tramo vibra mejor con una frecuencia distinta (Robles y Ruggero, 2001). <!-- verificar: anchos de la membrana basilar humana (~0,1 mm en la base, ~0,5 mm en el ápice); cifra clásica atribuida a Békésy, sin fuente primaria leída. Fuentes secundarias dan 0,08-0,2 mm en la base y 0,42-0,5 mm en el ápice. --> Sobre 500 Hz, cada octava ocupa un tramo parecido de la membrana (Greenwood, 1990). Por eso el eje de frecuencias del audiograma va en octavas: espacios iguales en el papel corresponden a tramos parecidos de cóclea. Un audiograma es, en el fondo, un mapa de la cóclea de la base al ápice.

:::imagen ilustraciones/h03-tonotopia.svg ancho=96% Dónde cae cada frecuencia del audiograma en la cóclea: los agudos en la base, junto a la ventana oval, y los graves en el ápice. Fíjate en el tramo de la base que queda sobre 8 kHz, fuera de la audiometría convencional.
:::

**La base se daña primero.** Las células de la base son más vulnerables: tienen menos defensas frente a los radicales libres y manejan más calcio (Sha y cols., 2001; Fettiplace y Nam, 2019). Por eso el ruido, la edad y los ototóxicos empiezan por los agudos. Y el tramo más basal, sobre 8 kHz, casi una quinta parte del largo de la cóclea, queda fuera de la audiometría convencional: es lo que agrega la audiometría de alta frecuencia cuando se vigila un ototóxico. Las interoctavas de 3 y 6 kHz se miden siempre porque ahí vive la muesca del ruido (→ cap. 6).

### Cuánto se repite un umbral

Como el umbral es una probabilidad, dos mediciones del mismo oído nunca son idénticas. Todo umbral tiene una incertidumbre de al menos ±5 dB (BSA, 2018). Al repetir una audiometría manual, la diferencia media entre una y otra es pequeña, pero su dispersión ronda los 6 dB (Mahomed y cols., 2013).

Eso tiene dos consecuencias prácticas. La primera: una diferencia de 5 dB entre dos audiogramas, o entre el primer y el segundo 1 kHz, no muestra ningún cambio. La segunda: para decir que una audición cambió hacen falta criterios que sumen varias frecuencias o confirmen con un nuevo examen, como los del seguimiento de ototóxicos (más abajo, en *Cómo se informa*).

## Antes de empezar

### Equipo

- **Audiómetro** con calibración objetiva vigente y una verificación subjetiva diaria: conexiones, cables, que salga tono por cada transductor y que un oyente conocido oiga donde siempre. En la vigilancia ocupacional la verificación es semanal, con uno de al menos dos sujetos de audición conocida: si difiere en más de 10 dB HL en alguna frecuencia se repite con el otro, y si persiste el equipo sale de servicio (ISP, 2026).
- **Fonos supraaurales** (por ejemplo, TDH-39) o **de inserción** (por ejemplo, ER-3A). Los de inserción aíslan más del ruido de la sala y dejan pasar menos sonido al otro oído (Munro y Agnew, 1999); eso pesa a la hora de enmascarar (→ H4).
- **Vibrador óseo** (por ejemplo, B-71) con su diadema.
- **Pulsador** de respuesta o una señal acordada (levantar la mano).
- **Cabina sonoamortiguada**. La norma ISO 8253-1 fija el ruido ambiente máximo que admite cada tipo de medición; la vía ósea, con los oídos destapados, es la más exigente.

<!-- Protocolo ORL 2019: remitía la verificación diaria a la ISO 8253-1:1989. Esa edición está anulada; la vigente es la ISO 8253-1:2010, que la reemplaza (ISO 8253-1:2010, prefacio). -->

### Conoce tu equipo: el audiómetro

Todo audiómetro clínico tiene la misma lógica: **dos canales** independientes, cada uno con su pantalla y sus controles, y un **centro** con lo que comparten los dos (la frecuencia, el paso, el cronómetro). Uno lleva el tono al oído que estás midiendo; el otro, cuando hace falta, lleva el ruido que enmascara al oído contrario. La figura muestra el audiómetro de LabSim armado justo así: tono por el canal 1 al oído derecho y ruido de banda estrecha por el canal 2 al izquierdo.

:::imagen /docs/manual/img/estudiante/audiometro.png El audiómetro de LabSim, listo para enmascarar: tono por el canal 1 al oído que mides, ruido por el canal 2 al oído contrario. Lee siempre las dos pantallas antes de presentar.
- @4,13 | **Pantalla del canal 1.** Intensidad (40 dB HL), transductor (*Aérea*), paso (5 dB), salida (*Derecha*) y estímulo (*Tono*). Léela antes de cada presentación: es lo que de verdad va a sonar.
- @40,10 | **Frecuencia y prueba.** 1.000 Hz, en *Umbrales*. Se cambia con las flechas de abajo.
- @51,22 | **Indicador de respuesta.** Se pone lila cuando el paciente levanta la mano. Es tu único dato: no mires al paciente, mira esto.
- @96,13 | **Pantalla del canal 2.** Ruido de banda estrecha (*Narrow Band Noise*) a 60 dB al oído izquierdo: es el enmascarante (→ H4).
- @10,30 | **Salida.** A qué oído va el canal. Un error aquí invierte el audiograma completo.
- @26,59 | **Estímulo.** Tono, tono modulado (FM), habla y los ruidos: blanco (WN), banda estrecha (NBN), rosa (PN) y de habla (SN).
- @36,52 | **Transductor.** Fonos (*Aéreo*) o vibrador (*Osea*). Al pasar a ósea, cambia también lo que tiene puesto el paciente.
- @42,43 | **Alta frecuencia.** Suma las frecuencias de 9 a 16 kHz para el monitoreo de ototóxicos.
- @42,53 | **Paso.** 1, 3 o 5 dB por clic de la perilla. Para buscar umbrales se usa 5.
- @42,61 | **Rango extendido.** Lleva la vía aérea de 100 a 120 dB HL.
- @8,78 | **Perilla del canal 1.** Sube y baja la intensidad del canal.
- @16.5,72.5 | **Pulsado e Invertir.** Pulsado: el tono suena en pulsos. Invertir: el canal queda sonando continuo; así se deja encendido el ruido enmascarante.
- @16.5,84 | **Estímulo (botón grande).** El tono suena **solo mientras lo mantienes apretado**. Uno a dos segundos, con pausas irregulares.
- @32.5,82 | **Talkback.** Le hablas al paciente dentro de la cabina, por ejemplo para darle la instrucción.
:::

:::ayuda Antes de cada tono, de izquierda a derecha
**Salida → transductor → estímulo → intensidad.** Cuatro datos en la pantalla del canal. Si uno está mal, el umbral que anotas es de otro oído, otra vía u otro sonido.
:::

### Paciente

- **Otoscopía primero** (→ H1). Un tapón de cerumen o un cuerpo extraño fabrican un gap; un conducto que colapsa bajo el fono supraaural, también.
- **Acumetría** antes de la audiometría (→ H2): da una hipótesis que el audiograma tiene que confirmar.
- Sin lentes, aros, audífonos ni cintillos. El pelo fuera del pabellón.
- Si viene por ruido laboral: **reposo auditivo de al menos 12 horas** (ISP, 2018).
- El paciente sentado de lado, sin ver el panel ni las manos de quien examina (ISP, 2018).

### Instrucciones

Se explican antes de poner los fonos, con palabras simples:

> "Vas a escuchar unos pititos, primero por un oído y después por el otro. Algunos van a ser muy suaves. Cada vez que escuches uno, aunque sea apenas, aprieta el botón (o levanta la mano) altiro."

Se le dice por qué oído se parte y se le pregunta si entendió. "Aunque sea apenas" y "altiro" son las dos frases que más cambian el resultado: el paciente que espera a estar seguro da umbrales peores que los reales.

### Fonos

Rojo en el derecho y azul en el izquierdo, con la membrana centrada sobre la entrada del conducto y los dos a la misma altura. Los pone quien examina, no el paciente (ASHA, 2005). Una vez puestos, el paciente no los toca.

![{IA} La audiometría en cabina. El fono rojo va en el oído derecho y el azul en el izquierdo, centrados sobre el conducto; el paciente responde con el pulsador y no ve el panel. Un fono corrido deja pasar menos sonido y el umbral sale peor de lo que es.](ilustraciones/h03-cabina-fonos.png)

## Paso a paso

### 1. Familiarización

Se parte por el **oído que el paciente siente mejor**; si dice que oye igual, por el derecho (ASHA, 2005; ISP, 2018). Se presenta 1 kHz a un nivel claramente audible, **40 dB HL** en alguien que oye bien. Si no responde, se sube de 10 en 10 hasta que responda (BSA, 2018). Esa primera respuesta muestra que entendió la tarea.

### 2. Búsqueda del umbral: 10 abajo, 5 arriba

- Cada tono dura **1 a 2 segundos**. El silencio entre tonos varía y nunca es más corto que el tono (ASHA, 2005; ISO 8253-1, 1989). Un ritmo fijo hace que el paciente "responda al reloj".
- **Si responde, se baja 10 dB.**
- **Si no responde, se sube 5 dB.**
- El umbral se busca **en ascenso**, porque así es más estable que bajando (ver *Por qué el umbral se busca así*, en el Fundamento).
- **Criterio**: el nivel más bajo con respuesta en al menos la mitad de los ascensos, con un mínimo de **2 de 3** (ASHA, 2005). Es la versión abreviada de la norma ISO; la completa pide 3 de un máximo de 5 (ISO 8253-1, 1989).

:::sabias ¿Sabías que?
Antes de este método, la audiometría usaba el método de límites: un tono continuo que se subía y se bajaba tres o cuatro veces, y el umbral era el punto medio entre los promedios; así lo describía Bunch en 1943. El tono corto contra silencio y el umbral tomado solo en ascenso lo reemplazaron en los años cuarenta, y desde Carhart y Jerger (1959) casi todas las normas conservan el esquema (Jerger, 2018).
:::

El ascendente no es la única forma de llegar al umbral. La **descendente** es el viejo método de límites de la psicofísica (Fechner, 1860), que Bunch (1943) llevó a la audiometría: baja de a 5 dB hasta que el paciente deja de responder. Es rápida, pero el paciente tiende a seguir respondiendo por inercia y el umbral sale más bajo de lo que es. La de **horquilla** es la otra que describe la ISO 8253-1 (1989): alterna series de 5 dB que suben y que bajan alrededor del umbral hasta completar tres de cada una, y el umbral es el promedio de los niveles más bajos que el paciente oyó en ellas; llega al mismo umbral que la ascendente, pero tarda más. La **combinada acortada** baja de a 10 mientras el paciente responde y sube de a 5 cuando deja de hacerlo, y en vez de repetir ascensos repite el tono al mismo nivel: el umbral es la mínima intensidad con 2 respuestas de 3 tonos.

<!-- verificar: horquilla según resúmenes de la ISO 8253-1 (tres series ascendentes y tres descendentes; promedio de los niveles más bajos oídos), no según la norma leída. Hughson y Westlake (1944) confirmada en catálogos y en la guía ASHA 2005 (Trans Am Acad Ophthalmol Otolaryngol 48 Supl:1-15; también edición aparte, Omaha, Douglas Print Co., WorldCat OCLC 221510216); texto completo no leído. Método en discusión con el equipo: docs/libro/incongruencias_protocolo.md, punto 13b. -->

:::imagen ilustraciones/h03-metodos-umbral.svg ancho=100% Cuatro formas de buscar el umbral, con el mismo umbral de 25 dB HL. Compara en qué dirección avanza cada una y en qué punto se juzga el umbral: la descendente arriesga que el paciente siga respondiendo por inercia.
:::

### 3. Orden de frecuencias

Se empieza en 1 kHz porque es la frecuencia más estable y la más fácil de oír. Luego se sube por los agudos y se termina en los graves:

**1 → 2 → 3 → 4 → 6 → 8 kHz → 1 kHz de nuevo → 500 → 250 → 125 Hz**

- **Repetir 1 kHz** es el control de confiabilidad. Si difiere en más de 5 dB de la primera vez, algo cambió: se vuelve a instruir al paciente y se repiten otras frecuencias (ASHA, 2005; BSA, 2018).
- En el segundo oído se sigue el mismo orden y ya no hace falta repetir 1 kHz (ASHA, 2005).
- Las **interoctavas** (750 y 1.500 Hz) se agregan cuando entre dos octavas vecinas hay un salto grande. <!-- verificar: ASHA 2005 da un salto de 20 dB o más entre octavas vecinas como indicación de interoctavas. -->
- Si el umbral aéreo de un oído supera a la ósea del otro en lo que el sonido pierde al cruzar el cráneo (unos 40 dB con fonos supraaurales), el otro oído puede estar contestando: hay que enmascarar. → H4.

### 4. Vía ósea

En este libro la vía ósea va **al final de la batería**: después de la vía aérea, la logoaudiometría, la acufenometría y las pruebas supraliminares. Es el orden que espera LabSim.

**Por qué este orden.** Todo lo que se hace con fonos va primero y el cambio al vibrador se hace **una sola vez**. Cada cambio de transductor obliga a entrar a la cabina, sacar y volver a poner los fonos, mover al paciente y recolocar el vibrador. Eso son minutos de examen, fatiga del paciente y oportunidades de dejar un fono corrido. Con un solo cambio, la batería es más corta y más estable.

:::comentario Lo que dicen las normas
Las normas y guías ponen la ósea **inmediatamente después de la aérea**:

- La ISO 8253-1:2010 (§4.1) recomienda empezar por la conducción aérea, "seguida de" la ósea.
- La guía técnica del ISP (2012) dice que, una vez terminada la aérea, "se realiza la evaluación por vía ósea".
- La NTP 285 (INSST, 1992) dice lo mismo.
- ASHA (2005) y la BSA (2018) la describen dentro de la misma audiometría tonal.

Las normas describen una secuencia; no prohíben otra. El orden de este libro responde a la lógica de arriba (un solo cambio de transductor, menos manipulación y menos fatiga) y el recuadro siguiente muestra cómo se decide el enmascaramiento mientras la ósea todavía no está medida, sin perder exactitud.
:::

:::ojo Cómo se trabaja con la ósea al final
Mientras no tengas la ósea, decide si enmascarar la aérea y la logoaudiometría comparando contra la **aérea del oído no evaluado**. La ósea nunca es peor que la aérea, así que esa comparación puede quedarse corta, pero nunca pide de más.

Cuando ya tengas la ósea, **revisa**: donde la ósea del oído no evaluado salió mejor que su aérea (un gap), vuelve a esa frecuencia y comprueba si la aérea del otro oído necesitaba ruido (→ H4).
:::

- **Dónde**: el vibrador va en la **mastoides**, lo más cerca posible detrás del pabellón **sin tocarlo** y sin apoyarse en pelo (BSA, 2018). La diadema pasa por arriba de la cabeza hasta el otro lado. Si toca la oreja o queda flojo, la ósea sale peor de lo que es y aparece un gap que no existe.
- **Qué oído primero**: el **peor** por vía aérea, porque es el que va a necesitar enmascaramiento (BSA, 2018; ISP, 2012).
- **El oído evaluado queda destapado.** Solo se pone un fono en el otro oído cuando se enmascara (ASHA, 2005). Tapar un oído mejora su ósea en los graves (efecto de oclusión). → H4.
- **Frecuencias**: de 250 a 4.000 Hz, con la misma técnica de la vía aérea (ASHA, 2005; ISP, 2012).
- **Dónde no**: en un oído con aérea normal, la ósea no agrega información y se puede omitir (INSST, 1992). En la evaluación médico-legal, en cambio, se mide en los dos oídos (ISP, 2012).

<!-- Protocolo ORL 2019 no fija tolerancia para repetir 1 kHz; se tomó la de 5 dB (ASHA 2005, BSA 2018, ISO 8253-1:1989). -->

![{IA} Dónde va el vibrador óseo: de plano sobre la mastoides, detrás del pabellón sin tocarlo y con el conducto libre. Sobre el pelo, tocando el pabellón o demasiado alto, el umbral óseo sale peor de lo que es.](ilustraciones/h03-vibrador-mastoides.png)

¿Por qué no se mide la ósea en 125 Hz ni sobre 4 kHz? El vibrador distorsiona en los graves y en los agudos irradia sonido por el aire. Además, en 250 Hz el paciente puede **sentir** la vibración antes de oírla: en la mastoides, el umbral táctil puede estar en 25 dB a 250 Hz, 55 dB a 500 Hz y 70 dB a 1 kHz (BSA, 2018). Una "respuesta" ósea por encima de esos niveles en graves puede ser tacto, y se anota así en el audiograma (ASHA, 2005).

:::comentario Cuando la audiometría no calza con los diapasones
Se repite la acumetría. Si sigue sin calzar, se hace un **Weber audiométrico**: el vibrador en la frente (fuera del seno frontal) y un tono de 500 Hz algo por encima del umbral óseo. Se anota con una flecha del color del lado hacia el que lateraliza.
:::

:::ayuda Ayuda memoria
- Oído mejor primero; 1 kHz a 40 dB para familiarizar.
- Tonos de 1 a 2 s, silencios irregulares.
- **Responde: −10. No responde: +5.**
- Umbral en ascenso: **2 de 3**.
- 1-2-3-4-6-8 kHz, **repetir 1 kHz**, 500-250-125 Hz.
- Ósea al final de la batería (un solo cambio de transductor): mastoides, sin tocar el pabellón, 250 a 4.000 Hz, oído peor primero.
:::

### Audiometría de screening

El screening no busca umbrales: presenta cada frecuencia a un **nivel fijo** y separa a quien responde a todo de quien no. En niños el nivel habitual es **20 dB HL** (ASHA, 1997). <!-- verificar: ASHA 1997 para niños, 1, 2 y 4 kHz a 20 dB HL. --> Quien no responde a alguna frecuencia **no "tiene" una pérdida**: se deriva a audiometría completa.

<!-- Protocolo ORL 2019: "se considera umbral si el paciente tiene la capacidad de escuchar todos los estímulos a 20 dB HL". El screening es pasa/no pasa a nivel fijo y no entrega umbrales (ASHA 1997); se corrigió la redacción. -->

En los **operativos en terreno** (colegios, faenas) se sigue la técnica completa, pero muchas veces sin cabina. El ruido de la sala tapa sobre todo los graves: un umbral elevado en terreno se confirma en cabina antes de informarlo. Con los más chicos se usa el condicionamiento por juego (→ H8).

### Audiometría ocupacional (Chile)

La vigilancia de los trabajadores expuestos a ruido la regula el **PREXOR** (MINSAL, 2013). El protocolo no describe la técnica: la delega en la guía técnica del ISP, que es la que exige la SUSESO (ISP, 2026; SUSESO).

PREXOR distingue cuatro audiometrías:

<!-- verificar: la columna "Cuándo" resume las definiciones de PREXOR de memoria; la columna "Qué mide" sí está cotejada con el texto (docs/investigacion/tecnica_audiometria_tonal/notas/normativa_chile_hispana.md). -->

Tabla: Las cuatro audiometrías de PREXOR

| Tipo | Cuándo | Qué mide |
|---|---|---|
| **Base** | al ingresar a la exposición | aérea de 500 a 8.000 Hz |
| **Seguimiento** | periódica, mientras dure la exposición | aérea de 500 a 8.000 Hz |
| **Confirmación** | cuando el seguimiento sale alterado | aérea de 250 a 8.000 Hz, en cámara |
| **Egreso** | al terminar la exposición | aérea de 250 a 8.000 Hz, en cámara |

La técnica de la guía ISP (versión 3.0, 2026) sigue a la ISO 8253-1, con tres diferencias con la clínica:

- **Familiarización**: 1 kHz a 40 dB; se baja de 20 en 20 hasta que no responda, se sube de 10 en 10 hasta que responda y se confirma al mismo nivel.
- **Orden**: 1, 2, 3, 4, 6 y 8 kHz, y luego 500 y 250 Hz, sin medir 125 Hz. Se parte a 30 dB HL o más, y 1 kHz se repite solo si hay duda sobre la curva.
- **Criterio**: método descendente-ascendente modificado de Carhart y Jerger; el umbral es el nivel más bajo donde responde **2 de 3** veces (ISP, 2026).
<!-- Guía ISP v2.0 (2018) pedía 3 de 5; la v3.0 (2026) la reemplaza (leída en ispch.cl, 2026-10-16). -->

Si una audiometría sale alterada, el trabajador va a la **evaluación audiológica médico-legal (EAML)**: vía aérea y ósea, logoaudiometría, diapasones e impedanciometría, más pruebas de adaptación, reclutamiento y simulación si hacen falta (ISP, 2018). La guía de 2012 describía su técnica, con la ósea de 250 a 4.000 Hz en cada oído (ISP, 2012).

### Audiometría de alta frecuencia

Mide sobre 8 kHz con **fonos especiales** y un audiómetro que tenga esa función; según el equipo, hasta 16 o 20 kHz. La técnica de búsqueda y los símbolos son los mismos. Se hace la audiometría convencional primero y después se cambian los fonos.

Su uso principal es **vigilar fármacos ototóxicos** (cisplatino, aminoglucósidos). El daño empieza en la base de la cóclea y aparece en la alta frecuencia antes de llegar a las frecuencias del habla. El esquema es siempre el mismo (Durrant y cols., 2009):

1. **Línea de base** antes del tratamiento, o lo más cerca posible de su inicio.
2. **Controles durante** el tratamiento.
3. **Control después** de terminado.

Los umbrales de alta frecuencia varían mucho entre personas y con la edad. Por eso cada control se compara contra **la línea de base del mismo paciente**, no contra una norma. <!-- verificar: AAA 2009 describe una versión abreviada que solo mide la zona de frecuencias más altas con respuesta ("sensitive range for ototoxicity"). -->

![Dos audiogramas de alta frecuencia del mismo oído, superpuestos: línea de base (gris) y control a las seis semanas de cisplatino (azul). De 250 Hz a 8 kHz las curvas coinciden; de 10 a 16 kHz el control cae 20 a 30 dB. Una franja marca el rango convencional y otra el de alta frecuencia.](ilustraciones/h03-alta-frecuencia.png)

## Cómo se informa

### Los símbolos

Los símbolos del audiograma son los de la ASHA (1990). En Chile, el derecho va en **rojo** y el izquierdo en **azul**; si los dos oídos tienen el mismo umbral, el símbolo del izquierdo se dibuja dentro del derecho (ISP, 2018).

:::imagen ilustraciones/h03-simbolos.svg ancho=86% Los símbolos del audiograma, del Fowler y de la acumetría. Rojo para el derecho, azul para el izquierdo; los óseos, corridos hacia el lado del oído, como si el paciente te mirara de frente.
:::

La aérea se une con línea continua; la ósea, cuando se une, con línea punteada, y el LDL con guiones. Los símbolos óseos del derecho van a la izquierda de la línea de frecuencia y los del izquierdo a la derecha: es el paciente mirándote de frente. Los de campo libre van en **verde** y centrados, porque no son de un oído: los oye el mejor. La lámina trae también los símbolos que se usan más adelante: el LDL (→ H5), la escalera del Fowler (→ H6) y el Weber y el Rinne de la acumetría (→ H2).


{{caso h3_p33}}

:::figura h3_p33 audiograma
- @OD 1000 | El **círculo rojo** es la aérea del OD: 0 dB HL en todas las frecuencias.
- @OD osea 1000 | El **< rojo** es la ósea del OD sin enmascarar. Va corrido a la izquierda de la línea de 1 kHz.
- @OI 2000 | La **✕ azul** es la aérea del OI.
- @OI osea 2000 | El **> azul** es la ósea del OI, corrida a la derecha.
- Todo está en 0: audición normal en los dos oídos. En un oído así la ósea no hacía falta; acá está para que veas dónde va cada símbolo.
- Para la minera, esta es la **audiometría de base**: cada control futuro de Tomás se va a comparar contra ella.
:::

### Leer un audiograma en orden

Un audiograma se lee siempre en el mismo orden, y cada paso usa un principio del Fundamento:

1. **¿Se le puede creer?** La confiabilidad va primero: si la prueba no es creíble, todo lo demás sobra (ver *La confiabilidad y sus signos*, más abajo).
2. **¿Es normal?** Cada oído por separado. En este libro, normal es un promedio BIAP de hasta 20 dB HL; pero mira también cada frecuencia, porque un promedio normal puede esconder una muesca en 4 o 6 kHz.
3. **¿Dónde se pierde el sonido?** El tipo, comparando la aérea con la ósea.
4. **¿Cuánto?** El grado.
5. **¿Qué forma tiene?** La configuración, que es el mapa de qué parte de la cóclea está dañada.
6. **¿Son iguales los dos oídos?** La simetría.
7. **¿Calza con lo demás?** Otoscopía, acumetría, logoaudiometría, impedanciometría y la conversación con el paciente.

### El tipo: leer el gap

:::ayuda-ancho Tipos de hipoacusia
| | Vía ósea | Vía aérea | Gap aéreo-óseo |
|---|---|---|---|
| **Conductiva** | normal | alterada | presente |
| **Sensorioneural** | alterada | alterada, junto a la ósea | ausente |
| **Mixta** | alterada | alterada, más que la ósea | presente |

Un gap de 5 o 10 dB cabe en la incertidumbre de dos umbrales. Lo que cuenta es un gap mayor y sostenido en varias frecuencias.
:::

Antes de aceptar un gap, descarta los que fabrica la técnica: un conducto que colapsa bajo el fono supraaural, un vibrador que toca la oreja o quedó flojo, una "respuesta" ósea en 250 Hz que en realidad es tacto. Y antes de aceptar que no hay gap, descarta el que borra la técnica: un fono olvidado sobre el oído evaluado mejora su ósea en los graves (efecto de oclusión) y achica un gap verdadero. Por último, recuerda las reglas del Fundamento: una ósea más de 10 dB peor que la aérea es un error, y una conductiva "de 80 dB" casi siempre es una ósea sin enmascarar.

{{caso h3_p34}}

:::figura h3_p34 audiograma
- @OD 250 | El **triángulo** es la aérea del OD enmascarada: 55 dB en 250 Hz.
- @OD osea 250 | El **corchete [** es la ósea del OD enmascarada: 10 dB. Entre las dos hay un gap de 45 dB.
- @OD osea 2000 | En 2 kHz la ósea baja a 25 dB y luego vuelve a subir: es la **muesca de Carhart**, propia de la fijación del estribo.
- @OI 1000 | El OI es normal: es el que se enmascaró para medir el derecho.
- Ósea normal, aérea abajo y un gap amplio: **hipoacusia conductiva** del OD.
:::

{{caso h3_p36}}

:::figura h3_p36 audiograma
- @OD 4000 | En 4 kHz la aérea del OD está en 60 dB y la ósea en 55: van **juntas**, sin gap.
- @OI osea 1000 | En el OI pasa lo mismo: aérea y ósea en 30 dB en 1 kHz.
- @OD 500 | Los graves están casi normales y la pérdida crece hacia los agudos: configuración **descendente**.
- **Hipoacusia sensorioneural bilateral y simétrica**. La ósea se midió donde la aérea está alterada.
:::

El OI de Luis, el paciente de la radiografía del comienzo (caso H3.1), es el ejemplo de mixta:

:::figura h3_p41 audiograma
- @OI 1000 | El **cuadrado** es la aérea del OI enmascarada: 50 dB en 1 kHz.
- @OI osea 1000 | El **corchete ]** es la ósea del OI enmascarada: 25 dB. Hay gap, pero la ósea tampoco es normal.
- @OI osea 4000 | En 4 kHz la ósea llega a 45 dB: la cóclea también está dañada, sobre todo en los agudos.
- Las dos vías alteradas y un gap de 20 a 30 dB: **hipoacusia mixta** del OI.
:::

### El grado

El grado se calcula **por oído** con el promedio de 500, 1.000, 2.000 y 4.000 Hz por vía aérea (BIAP 02/1). Una frecuencia sin respuesta se cuenta como 120 dB.

¿Por qué esas cuatro? Porque son las que más pesan para oír y entender la voz (ver *Por qué esas frecuencias*): el grado busca resumir en un número cuánto le cuesta a esa persona la comunicación. ¿Y por qué 120 dB cuando no hay respuesta? Porque "no respondió al máximo del equipo" quiere decir que su umbral está, como mínimo, ahí; contarla como el máximo de un equipo menos potente subestimaría la pérdida.

:::ayuda Grados BIAP
| Promedio (dB HL) | Grado |
|---|---|
| hasta 20 | audición normal |
| 21 a 40 | leve |
| 41 a 70 | moderada |
| 71 a 90 | severa |
| 91 a 119 | profunda |
| 120 | cofosis |
:::

En el caso de Hernán (caso H3.4): el OD promedia (20 + 25 + 40 + 60) / 4 = **36 dB, leve**; el OI promedia (25 + 30 + 45 + 65) / 4 = **41 dB, moderada**. Dos oídos casi iguales quedan en grados distintos por un decibel. El grado resume, pero no reemplaza mirar la curva.

:::comentario Otras escalas de grado
La escala BIAP es la que usa este libro y la que calcula LabSim, pero no es la única. La Organización Mundial de la Salud (2021) usa el mismo promedio de 500 a 4.000 Hz, calculado en el **oído mejor**, con cortes distintos: audición normal bajo 20 dB HL; leve de 20 a menos de 35; moderada de 35 a menos de 50; moderadamente severa de 50 a menos de 65; severa de 65 a menos de 80; profunda de 80 a menos de 95, y completa desde 95. <!-- verificar: cortes de la escala OMS 2021 (World report on hearing), escritos de memoria. -->

La OMS clasifica a la **persona** para estudios de población; la BIAP clasifica **cada oído**, que es lo que necesita un informe clínico. Un mismo promedio puede caer en grados distintos según la escala: por eso el informe dice cuál usó y da el número, no solo el nombre del grado.
:::

El grado no es lo mismo que el **promedio tonal** de 500, 1.000 y 2.000 Hz que se usa para comparar con la logoaudiometría (→ H5). En una curva descendente, el promedio de tres frecuencias deja fuera los 4 kHz y da un número más bajo.

:::truco-ancho Truco del oficio: el promedio a ojo
Los umbrales van de 5 en 5 dB, así que el promedio se puede sacar sin sumar ni dividir: se trabaja en **escalones de 5 dB**. Ojo con la orientación: en el audiograma los dB crecen hacia abajo, así que bajar un punto es sumarle dB y subirlo es restarle.

![El promedio tonal a ojo. A la izquierda, nivelar: 30, 40 y 50 dB pasan a 35, 40 y 45 y luego a 40, 40 y 40, y esa línea es el promedio. A la derecha, el anclaje: 20, 30, 40 y 60 dB contados en escalones desde 30.](ilustraciones/h03-ptp-nivelar.svg)

- **Nivelar.** Sube un escalón el punto más bajo del gráfico y baja un escalón el más alto: el total no cambia. Repite hasta que queden en la misma línea; esa línea es el promedio. 30, 40 y 50 dan **40 dB**.
- **Anclar.** Elige una línea (la del medio o la que más se repite) y cuenta los escalones de cada punto: hacia abajo suman, hacia arriba restan. Reparte el neto entre las frecuencias. 20, 30, 40 y 60 con ancla en 30: −2, 0, +2 y +6 dan +6 escalones; entre 4 son 1,5 escalones (7,5 dB): **37,5 dB**.
- **Si no se nivela del todo**, quedan *k* puntos un escalón más abajo que el resto. Se suma a la línea:

| Puntos que sobran (*k*) | Promedio de 3 frecuencias | Promedio de 4 frecuencias |
|---|---|---|
| 1 | +1,67 | +1,25 |
| 2 | +3,33 | +2,5 |
| 3 | — | +3,75 |

Por ejemplo, 25, 35 y 55 se nivelan a 35, 40 y 40: línea 35 y dos que sobran, **38,33 dB**.

**Para comprobar:** con 3 frecuencias el resultado termina siempre en ,00, ,33 o ,67, y con 4 en ,00, ,25, ,5 o ,75; otro decimal es un error. Y si los puntos son simétricos alrededor del central (30, 40, 50), el promedio es el central.
:::

### La configuración

La configuración es la forma de la curva. Como cada frecuencia corresponde a un lugar de la cóclea, la forma dice **qué parte del oído interno está dañada** (o, en una conductiva, qué propiedad del oído medio cambió). Se describe con palabras, no con números. Junto con el tipo y el grado, orienta la causa, pero no la diagnostica.

:::ayuda Configuraciones del audiograma
| Forma | Hace pensar en |
|---|---|
| **Plana**: umbrales parecidos en todas las frecuencias | muchas conductivas (líquido en el oído medio, cadena interrumpida); la presbiacusia metabólica (→ caps. 2, 3 y 5) |
| **Descendente**: pierde hacia los agudos, en caída suave o brusca | la base de la cóclea, la primera en dañarse: presbiacusia, ototóxicos (→ caps. 5 y 8) |
| **Ascendente**: pierde en los graves y mejora hacia los agudos | el hidrops en sus primeras etapas; las conductivas por rigidez (→ caps. 4 y 9) |
| **En muesca**: cae en una frecuencia y se recupera en las vecinas | en la aérea, entre 3 y 6 kHz: el ruido (→ cap. 6); en la ósea, en 2 kHz: la muesca de Carhart (→ cap. 4) |
| **En cubeta**: cae en los medios y se recupera en los extremos | algunas hipoacusias hereditarias (→ cap. 10) |
:::

En el informe se describe cada oído por separado. Si la forma no calza con ninguna, se describe tal cual ("pérdida en 2 kHz con recuperación en 4 kHz"): un nombre forzado confunde más que una descripción.

### La simetría

Se compara un oído con el otro, frecuencia por frecuencia. En este libro, una diferencia de **15 dB o más en una o más frecuencias** es una asimetría (→ cap. 11).

La simetría importa porque separa dos grupos de causas. Lo que afecta a los dos oídos por igual, como la edad, el ruido, los ototóxicos o la herencia, da pérdidas **bilaterales y simétricas**. Una asimetría sensorioneural sin una causa que la explique obliga a descartar una lesión retrococlear (→ cap. 11).

Antes de llamarla asimetría, comprueba que sea real. Un fono corrido o un oído mal instruido la fabrican. Una curva sombra, al revés, la achica: el oído malo "responde" con la audición del bueno, 40 dB más abajo (caso H3.5).

### Sin respuesta y curva sombra

{{caso h3_p42}}

:::figura h3_p42 audiograma
- @OD 1000 | El OD "responde" en 40 dB. No es su audición: el tono cruzó el cráneo y lo oyó el OI. Con fonos supraaurales el sonido pierde unos 40 dB al cruzar.
- @OD osea 1000 | La ósea del OD "responde" en 0 dB: por vía ósea el sonido cruza casi sin perder nada.
- @OI 1000 | El OI es normal. Es el que estuvo contestando todo el tiempo.
- La curva del OD copia la del OI unos 40 dB más abajo: es una **curva sombra**. Con el OI enmascarado, el OD no responde ni al máximo del equipo y se dibuja con la flecha de "sin respuesta": **cofosis** del OD. → H4.
:::

### El audiograma ocupacional

{{caso h3_p37}}

:::figura h3_p37 audiograma
- @OD 4000 | El fondo está en 4 kHz: 55 dB en el OD.
- @OD 8000 | En 8 kHz el OD vuelve a 30 dB. Esa **recuperación** es la que separa la muesca por ruido de una caída por edad.
- @OI 4000 | El OI tiene la misma forma, con el fondo en 60 dB: es **bilateral y casi simétrica**, como el ruido laboral.
- @OD 1000 | Hasta 1 kHz la audición es normal. Por eso el promedio BIAP del OD da solo 21 dB, apenas leve.
:::

Se habla de **muesca** cuando 3, 4 o 6 kHz están al menos 10 dB peor que 1 o 2 kHz y que 6 u 8 kHz (Coles y cols., 2000). El grado por BIAP no refleja bien este daño. Para efectos médico-legales, la SUSESO usa el promedio de 1, 2, 3, 4 y 6 kHz y considera daño auditivo sobre 25 dB HL. En Jorge, ese promedio es 33 dB en el OD y 38 dB en el OI.

### El seguimiento ototóxico

En cada control se compara con la línea de base. Hay un **cambio significativo** si se cumple cualquiera de estos criterios, confirmado con un nuevo examen (ASHA, 1994):

- 20 dB o más en una frecuencia;
- 10 dB o más en dos frecuencias vecinas;
- pérdida de respuesta en tres frecuencias seguidas que antes respondían.

Estos criterios detectan bien los cambios reales, siempre que se confirmen, por la variabilidad del retest (Konrad-Martin y cols., 2010). En niños con platino se usa además una escala de grados propia, la SIOP Boston (Brock y cols., 2012). Las recomendaciones actuales integran todo esto en un programa con cronograma fijo (Fernandez y cols., 2025).

### La confiabilidad y sus signos

Antes de leer el audiograma decides si se le puede creer, y el informe lo dice. Una prueba confiable deja estos signos:

- **El 1 kHz repetido cae dentro de 5 dB** del primero. Si sale mejor, el paciente siguió aprendiendo; si sale peor, puede ser fatiga o un fono que se movió.
- **Las respuestas son limpias.** El paciente responde mientras suena el tono, no en los silencios ni varios segundos después. Las respuestas en silencio son falsos positivos y las muy tardías hablan de una tarea que no se entendió o de un paciente que duda.
- **Cada umbral se repite dentro de su búsqueda.** Si los niveles mínimos de respuesta de una misma frecuencia se reparten en más de 10 dB, la medición es dudosa y se repite (ISO 8253-1, 1989).
- **El audiograma calza con el resto.** El umbral de la palabra concuerda con el promedio tonal (→ H5), los diapasones apuntan al mismo lado (→ H2) y el paciente conversó como su audiograma predice.
- **La curva sombra aparece donde tiene que aparecer.** Un oído muy malo, medido sin enmascarar, tiene que "responder" cuando el tono llega a cruzar al otro. Si no responde ni a esos niveles, algo no calza (→ H6).

Si faltan, primero se corrige lo que se puede: se vuelve a instruir, se hace una pausa, se revisan fonos y vibrador y se repite. Si persiste, se informa igual, pero con la confiabilidad declarada y el motivo ("respuestas inconsistentes; 1 kHz difiere en 15 dB"). La sospecha de una pérdida no orgánica tiene sus propias pruebas (→ H6).

### El informe

El informe ordena lo mismo que la lectura:

1. **Condiciones.** Transductor (fonos supraaurales o de inserción, vibrador), si se midió en cabina y qué se enmascaró.
2. **Confiabilidad**, con su fundamento.
3. **Cada oído:** tipo, grado (con el promedio y la escala) y configuración.
4. **Los dos oídos juntos:** si es bilateral o unilateral, simétrica o asimétrica.
5. **Observaciones:** frecuencias sin respuesta, respuestas óseas que pueden ser tacto, ósea no medida en un oído con aérea normal, acúfeno que dificultó la prueba.

Dos ejemplos, con los pacientes de este capítulo:

> **Audiometría tonal.** Hipoacusia sensorioneural bilateral, simétrica, de configuración descendente. Grado leve en OD (promedio BIAP 36 dB HL) y moderado en OI (41 dB HL). Sin gap aéreo-óseo. Prueba confiable: repetición de 1 kHz dentro de 5 dB.

> **Audiometría tonal** (fonos supraaurales, en cabina; OI enmascarado para medir el OD). Prueba confiable, concordante con la acumetría. **OD:** hipoacusia conductiva moderada (promedio BIAP 44 dB HL), de configuración ascendente, con gap aéreo-óseo de 30 a 45 dB entre 250 y 1.000 Hz y descenso de la vía ósea en 2 kHz. **OI:** audición normal (promedio BIAP 0 dB HL). Asimétrica.

El primero es el de Hernán (caso H3.4) y el segundo el de Carolina (caso H3.3). El informe dice qué se midió y cómo se ve, no el diagnóstico médico: "descenso de la vía ósea en 2 kHz" describe; "otoesclerosis" es un diagnóstico, y lo hace el médico tratante. Al paciente se le explican sus resultados en palabras simples.

## Errores frecuentes

- **Instrucción tibia.** Si el paciente no entiende que debe avisar "aunque sea apenas", espera a estar seguro y todos los umbrales salen peores.
- **Ritmo predecible.** Tonos a intervalos fijos generan respuestas al reloj. Hay que variar los silencios.
- **Pistas visuales.** El paciente ve tus manos, el panel o tu reflejo en el vidrio.
- **Fonos cruzados o corridos.** El rojo en el izquierdo invierte todo el audiograma. Un fono fuera del conducto eleva los umbrales, sobre todo en agudos.
- **Conducto que colapsa.** El fono supraaural aplasta un conducto blando y aparece un falso gap en agudos. La otoscopía lo anticipa; los fonos de inserción lo evitan.
- **Vibrador mal puesto.** Tocando la oreja, sobre el pelo o flojo, la ósea sale peor de lo real y se inventa un gap.
- **Oído evaluado tapado en la ósea.** El efecto de oclusión mejora la ósea en los graves y achica o borra un gap verdadero.
- **Tomar el tacto por audición.** Una ósea en 250 Hz sobre 25 dB puede ser vibración y no sonido.
- **Leer la curva sombra como umbral.** Una pérdida unilateral grande sin enmascarar nunca es la del oído malo (caso H3.5).
- **Leer la ósea sin enmascarar como de un oído.** Es la mejor cóclea, no la del lado del vibrador.
- **Saltarse la repetición de 1 kHz.** Es el único control de confiabilidad que tiene la prueba.
- **Cansancio.** La fiabilidad cae después de unos 20 minutos sin pausa (ISO 8253-1, 2010).

:::ojo Ojo clínico
Antes de informar, pregúntate si el audiograma **calza con todo lo demás**: con la otoscopía, con los diapasones, con cómo conversó el paciente en la entrevista. Un Weber que lateraliza al oído "bueno" en una pérdida que parece conductiva, o un paciente que conversa sin problemas con una curva de 60 dB, obligan a repetir antes de escribir.
:::

## En LabSim

El audiómetro de LabSim se maneja como uno real: elijes oído, transductor, frecuencia e intensidad, presentas el tono y miras si el paciente levanta la mano. Antes de cada prueba tienes que **darle la instrucción**: sin ella el paciente no sabe qué hacer.

- El paciente responde según sus umbrales verdaderos. Si no enmascaras cuando hace falta, contesta el otro oído y obtienes la **curva sombra**, igual que en la clínica.
- La vía ósea tiene los topes de un vibrador real: llega a 70 dB de 1 a 4 kHz y a menos en los graves. Si al tope no hay respuesta, se anota "sin respuesta".
- El **efecto de oclusión** también está: al poner el fono de enmascaramiento sobre un oído con el oído medio sano, su ósea mejora en los graves.
- Los casos guardan umbrales de 125 a 8.000 Hz: la alta frecuencia todavía no se practica en el simulador.

El **indicador de técnica** revisa cómo buscaste cada umbral: si diste la instrucción, por qué oído partiste, si terminaste un oído antes de pasar al otro, cuánto duró cada tono, si bajaste 10 y subiste 5, y si tus umbrales coinciden con la audición del paciente.

:::comentario Lo que el simulador no tiene
El paciente de LabSim no se distrae ni responde al azar: en su umbral contesta siempre. Un paciente real no. Practica igual el criterio de 2 de 3, porque es lo que vas a necesitar con personas.
:::

Para practicar, los pacientes de este capítulo están entre los de práctica (★): Tomás, Carolina, Hernán, Luis, Matías y Jorge.

:::pregunta Preguntas para practicar
1. Un paciente responde a 30, no a 20, sí a 25, no a 15, no a 20 y sí a 25. ¿Cuántos ascensos llevas? ¿Te alcanza para dar 25 dB como umbral con el criterio de 2 de 3?
2. Este libro toma la vía ósea al final de la batería y las normas la ponen justo después de la aérea. ¿Qué gana cada orden y qué tienes que revisar cuando la tomas al final?
3. En el caso de Carolina, ¿qué pasaría con su gap si le pones el vibrador tocando el pabellón? ¿Y si dejas el fono puesto sobre el oído derecho mientras mides su ósea?
4. Calcula el grado BIAP de Luis en el OI con los valores de la figura. ¿Cambia algo si usas el promedio de 500, 1.000 y 2.000 Hz?
5. En una audiometría de seguimiento de Tomás, dentro de cinco años, 4 kHz está en 30 dB en los dos oídos y 8 kHz en 10. Compárala con su audiometría de base: ¿qué forma está empezando a aparecer?
6. Un oído normal necesita 45 dB SPL para detectar 125 Hz y 7 dB SPL para 1 kHz. ¿Por qué en su audiograma los dos umbrales quedan en 0 dB HL? ¿Qué pasaría con sus umbrales si el audiómetro se calibró con otro modelo de fono?
7. Un paciente tiene la aérea del OD en 85 dB y la ósea, sin enmascarar, en 5 dB. ¿Puede ser una conductiva pura? ¿Qué está midiendo, probablemente, esa ósea?
8. Explica con la función psicométrica por qué un paciente que "espera a estar seguro" da umbrales peores que los reales. ¿Qué frase de la instrucción corrige eso?
:::

## Referencias

### Técnica

1. International Organization for Standardization. ISO 8253-1:2010. Acoustics — Audiometric test methods — Part 1: Pure-tone air and bone conduction audiometry. Ginebra: ISO; 2010.
1. International Organization for Standardization. ISO 8253-1:1989. Acoustics — Audiometric test methods — Part 1: Basic pure tone air and bone conduction threshold audiometry (anulada). Ginebra: ISO; 1989.
1. American Speech-Language-Hearing Association. Guidelines for manual pure-tone threshold audiometry [Guidelines]. Rockville (MD): ASHA; 2005. Disponible en: https://www.asha.org/policy/gl2005-00014/
1. British Society of Audiology. Recommended procedure: pure-tone air-conduction and bone-conduction threshold audiometry with and without masking (OD104-32). BSA; 2018. Disponible en: https://www.thebsa.org.uk/wp-content/uploads/2024/01/Recommended-Procedure-Pure-Tone-Audiometry-2018.pdf
1. American Speech-Language-Hearing Association. Guidelines for audiometric symbols. ASHA. 1990;32(Suppl 2):25-30.
1. BIAP. Recomendación 02/1: Clasificación audiométrica de las deficiencias auditivas.
1. American Speech-Language-Hearing Association. Guidelines for audiologic screening [Guidelines]. Rockville (MD): ASHA; 1997. doi:10.1044/policy.GL1997-00199
1. INSST. NTP 285: Audiometría tonal liminar: vía ósea y enmascaramiento. Madrid: Instituto Nacional de Seguridad e Higiene en el Trabajo; 1992.
1. Munro KJ, Agnew N. A comparison of inter-aural attenuation with the Etymotic ER-3A insert earphone and the Telephonics TDH-39 supra-aural earphone. Br J Audiol. 1999;33(4):259-62. doi:10.3109/03005369909090106
1. Mahomed F, Swanepoel DW, Eikelboom RH, Soer M. Validity of automated threshold audiometry: a systematic review and meta-analysis. Ear Hear. 2013;34(6):745-52.
1. Fechner GT. Elemente der Psychophysik. Leipzig: Breitkopf und Härtel; 1860.
1. Bunch CC. Clinical audiometry. St. Louis: Mosby; 1943.
1. Hughson W, Westlake HD. Manual for program outline for rehabilitation of aural casualties both military and civilian. Trans Am Acad Ophthalmol Otolaryngol. 1944;48(Suppl):1-15.
1. Carhart R, Jerger JF. Preferred method for clinical determination of pure-tone thresholds. J Speech Hear Disord. 1959;24(4):330-45. doi:10.1044/jshd.2404.330
1. Jerger J. The evolution of the audiometric pure-tone technique. Hearing Review. 2018;25(9):12-8. Disponible en: https://hearingreview.com/hearing-products/testing-equipment/testing-diagnostics-equipment/evolution-audiometric-pure-tone-technique
1. Burk MH, Wiley TL. Continuous versus pulsed tones in audiometry. Am J Audiol. 2004;13(1):54-61. doi:10.1044/1059-0889(2004/008)
1. International Organization for Standardization. ISO 389-1:2017. Acoustics — Reference zero for the calibration of audiometric equipment — Part 1: Reference equivalent threshold sound pressure levels for pure tones and supra-aural earphones. Ginebra: ISO; 2017.
1. International Organization for Standardization. ISO 389-7:2019. Acoustics — Reference zero for the calibration of audiometric equipment — Part 7: Reference threshold of hearing under free-field and diffuse-field listening conditions. Ginebra: ISO; 2019.
1. World Health Organization. World report on hearing. Ginebra: WHO; 2021. Disponible en: https://www.who.int/publications/i/item/9789240020481
1. Coles RR, Lutman ME, Buffin JT. Guidelines on the diagnosis of noise-induced hearing loss for medicolegal purposes. Clin Otolaryngol Allied Sci. 2000;25(4):264-73.

### Normativa chilena

1. Instituto de Salud Pública de Chile. Guía Técnica para la Evaluación Auditiva de Vigilancia de la Salud de los Trabajadores Expuestos Ocupacionalmente a Ruido, v3.0. Santiago: ISP; 2026. Disponible en: https://www.ispch.cl/wp-content/uploads/2026/04/Evaluacion-Auditiva.pdf
1. Instituto de Salud Pública de Chile. Guía Técnica para la Evaluación Auditiva de Vigilancia de la Salud de los Trabajadores Expuestos Ocupacionalmente a Ruido, v2.0. Aprobada por Res. Ex. N° 740 del 21-03-2018.
1. Instituto de Salud Pública de Chile (2012). Guía Técnica para la Evaluación Auditiva de los Trabajadores Expuestos Ocupacionalmente a Ruido, v1.0. §2: Evaluación Audiológica Médico Legal.
1. Ministerio de Salud de Chile (2013). Protocolo sobre normas mínimas para el desarrollo de programas de vigilancia de la pérdida auditiva por exposición a ruido en los lugares de trabajo (PREXOR). Norma Técnica N° 156, D.Ex. N° 1052.
1. Superintendencia de Seguridad Social (SUSESO). Compendio de Normas del Seguro Social de Accidentes del Trabajo y Enfermedades Profesionales, Libro IV, Título II, Letra F, Capítulo VIII. Disponible en: https://www.suseso.cl/613/alt-propertyvalue-485138.pdf

### Ototoxicidad y alta frecuencia

1. American Speech-Language-Hearing Association. Audiologic management of individuals receiving cochleotoxic drug therapy [Guidelines]. Rockville (MD): ASHA; 1994. doi:10.1044/policy.GL1994-00003
1. Durrant JD, Campbell K, Fausti S, Guthrie O, Jacobson G, Lonsbury-Martin BL, et al. American Academy of Audiology position statement and clinical practice guidelines: ototoxicity monitoring [Internet]. Reston (VA): AAA; 2009 Oct. Disponible en: https://www.audiology.org/wp-content/uploads/2021/06/AAA_OtoMonGuidelines_2009.pdf
1. Konrad-Martin D, James KE, Gordon JS, Reavis KM, Phillips DS, Bratt GW, et al. Evaluation of audiometric threshold shift criteria for ototoxicity monitoring. J Am Acad Audiol. 2010;21(5):301-14. doi:10.3766/jaaa.21.5.3
1. Brock PR, Knight KR, Freyer DR, Campbell KC, Steyger PS, Blakley BW, et al. Platinum-induced ototoxicity in children: a consensus review on mechanisms, predisposition, and protection, including a new International Society of Pediatric Oncology Boston ototoxicity scale. J Clin Oncol. 2012;30(19):2408-17. doi:10.1200/JCO.2011.39.1110
1. Fernandez K, Hoetink A, Konrad-Martin D, Berndtson D, Clark K, Dreisbach L, et al. Roadmap to a global template for implementation of ototoxicity management for cancer treatment. Ear Hear. 2025;46(2):286-97. doi:10.1097/AUD.0000000000001592

### Fisiología y psicoacústica

1. Shaw EA. Transformation of sound pressure level from the free field to the eardrum in the horizontal plane. J Acoust Soc Am. 1974;56(6):1848-61. doi:10.1121/1.1903522
1. Merchant SN, Ravicz ME, Voss SE, Peake WT, Rosowski JJ. Toynbee Memorial Lecture 1997. Middle ear mechanics in normal, diseased and reconstructed ears. J Laryngol Otol. 1998;112(8):715-31. doi:10.1017/S0022215100141568
1. Aibara R, Welsh JT, Puria S, Goode RL. Human middle-ear sound transfer function and cochlear input impedance. Hear Res. 2001;152(1-2):100-9. doi:10.1016/S0378-5955(00)00240-9
1. Robles L, Ruggero MA. Mechanics of the mammalian cochlea. Physiol Rev. 2001;81(3):1305-52. doi:10.1152/physrev.2001.81.3.1305
1. Dallos P. Cochlear amplification, outer hair cells and prestin. Curr Opin Neurobiol. 2008;18(4):370-6. doi:10.1016/j.conb.2008.08.016
1. Greenwood DD. A cochlear frequency-position function for several species--29 years later. J Acoust Soc Am. 1990;87(6):2592-605. doi:10.1121/1.399052
1. Fettiplace R, Nam JH. Tonotopy in calcium homeostasis and vulnerability of cochlear hair cells. Hear Res. 2019;376:11-21. doi:10.1016/j.heares.2018.11.002
1. Watson CS, Gengel RW. Signal duration and signal frequency in relation to auditory sensitivity. J Acoust Soc Am. 1969;46(4B):989-97.
1. Stenfelt S, Goode RL. Bone-conducted sound: physiological and clinical aspects. Otol Neurotol. 2005;26(6):1245-61. doi:10.1097/01.mao.0000187236.10842.d5
1. Stenfelt S. Transcranial attenuation of bone-conducted sound when stimulation is at the mastoid and at the bone conduction hearing aid position. Otol Neurotol. 2012;33(2):105-14. doi:10.1097/MAO.0b013e31823e28ab
1. Carhart R. Clinical application of bone conduction audiometry. Arch Otolaryngol. 1950;51(6):798-808. doi:10.1001/archotol.1950.00700020824003
1. Homma K, Du Y, Shimizu Y, Puria S. Ossicular resonance modes of the human middle ear for bone and air conduction. J Acoust Soc Am. 2009;125(2):968-79. doi:10.1121/1.3056564
1. Sha SH, Taylor R, Forge A, Schacht J. Differential vulnerability of basal and apical hair cells is based on intrinsic susceptibility to free radicals. Hear Res. 2001;155(1-2):1-8. doi:10.1016/S0378-5955(01)00224-6
