# B4. Física

:::objetivos En este capítulo
- Describir un sonido con cinco números (frecuencia, período, longitud de onda, amplitud y fase) y decir qué energía lleva un tono puro, un tono modulado, un click, un burst, un chirp y cada tipo de ruido.
- Calcular con decibeles: sumarlos, restarlos, aplicar las reglas de 3, 6 y 10 dB y distinguir dB SPL, HL, SL, nHL, eHL y EM.
- Explicar con una analogía de masa, resorte y roce qué mide un impedanciómetro y por qué la sonda de 226 Hz y la de 1.000 Hz ven cosas distintas.
- Calcular cuánto baja el ruido al promediar y relacionar el ruido residual, el FSP y la reproducibilidad.
- Explicar por qué el tono puro no se usa en campo libre y qué piden una sala y un parlante para que una medición valga.
- Leer una curva de audífono (ganancia, salida máxima, distorsión, ruido interno) y calcular un nivel equivalente y una dosis de ruido.
- Explicar por qué la rinomanometría se lee a una presión fija y cómo un eco entrega el área de una fosa nasal.
:::

Los capítulos de herramientas usan la física sin detenerse a explicarla: dicen "3 dB es el doble de energía", "el ruido baja con la raíz de los barridos", "el tono puro forma ondas estacionarias". Este capítulo es el lugar donde esas frases se explican, con números. No es un curso de física. No hay más matemática que **logaritmos** y una **raíz cuadrada**, y cada idea lleva un ejemplo resuelto que puedes rehacer con una calculadora. Cuando otro capítulo escribe → B4, la explicación está aquí.

Tabla: Dónde se usa cada sección

| Sección | Se usa sobre todo en |
|---|---|
| El sonido (ondas, estímulos, ruidos, filtros) | H3, H4, H8, H9, H10, H13 |
| Decibeles y referencias | H3, H4, H5, H7, H10, H13, H23 |
| Del sonido a lo que se oye | H3, H5, H6, H15 |
| Impedancia y admitancia | H7, cap. 3, cap. 4 |
| Señal y ruido | H9, H10, cap. 18 |
| Acústica de sala | H3, H8, H21 |
| Electroacústica del audífono | H21, H22 |
| Ruido ocupacional | H23, cap. 6, cap. 33 |
| Flujo de aire en la nariz | H25, H26 |

:::ayuda Los logaritmos que necesitas
El logaritmo en base 10 (la tecla *log* de la calculadora) cuenta ceros: log 10 = 1, log 100 = 2, log 1.000 = 3, log 2 = 0,301. Convierte productos en sumas, log(a × b) = log a + log b, y divisiones en restas, log(a / b) = log a − log b. Con eso salen todas las cuentas de este capítulo. Para deshacer un logaritmo se usa la tecla *10^x*: 10^2,5 = 316.
:::

## El sonido

### Una onda de presión

Un sonido es una variación de presión del aire. Un parlante, un fono o las cuerdas vocales empujan y sueltan el aire de al lado, y ese empujón se pasa de capa en capa: **lo que viaja es la perturbación, no el aire**. En cada punto la presión sube un poco sobre la presión atmosférica (compresión) y baja un poco bajo ella (rarefacción). La atmósfera es de unos 101.000 Pa y un oído joven detecta variaciones de apenas 20 µPa a 1.000 Hz: dos diezmilmillonésimas de la presión que ya hay. Todo el capítulo gira sobre esa escala.

Cinco números describen un tono puro:

- **Frecuencia** (*f*, en hercios): cuántos ciclos de subida y bajada hay en un segundo. Es lo que el oído oye como grave o agudo.
- **Período** (*T*): lo que dura un ciclo, *T* = 1 / *f*. A 1.000 Hz dura 1 ms; a 125 Hz, 8 ms.
- **Longitud de onda** (λ): la distancia que recorre el sonido en un ciclo, λ = *c* / *f*, donde *c* es la velocidad del sonido. En el aire *c* es de unos **343 m/s a 20 °C** y cambia con la temperatura, *c* = 331,3 + 0,606 *T* (con *T* en °C): 331 m/s a 0 °C, 343 a 20 °C y 352 a 34 °C, la temperatura que alcanza el aire inspirado al llegar a la rinofaringe (Keck y cols., 2000; → H26).
- **Amplitud**: cuánto sube y baja la presión. Se puede dar de pico, de pico a pico o **RMS** (*root mean square*, la raíz del promedio de los cuadrados). El RMS mide la potencia del sonido y es el que usan los decibeles; para un tono puro vale 0,707 veces el pico.
- **Fase**: en qué punto del ciclo está la onda en un instante dado, de 0° a 360°.

:::imagen ilustraciones/b4-onda.svg ancho=96% Período, amplitud y fase de un tono puro. El período se lee en el eje del tiempo y la amplitud en el de la presión; la fase dice en qué punto del ciclo está la onda en cada instante.
:::

Tabla: Período y longitud de onda de las frecuencias del audiograma (aire, 20 °C)

| Frecuencia | Período | Longitud de onda | Por qué importa |
|---|---|---|---|
| 125 Hz | 8 ms | 2,74 m | más larga que una cabina: casi no se aísla y se refuerza o se apaga según el lugar |
| 250 Hz | 4 ms | 1,37 m | igual, algo menos |
| 500 Hz | 2 ms | 0,69 m | |
| 1.000 Hz | 1 ms | 0,34 m | un cuarto de onda mide 8,6 cm: eso es lo que cambia el nivel en una sala (→ Acústica de sala) |
| 2.000 Hz | 0,5 ms | 0,17 m | del tamaño de la cabeza: empieza la sombra |
| 4.000 Hz | 0,25 ms | 8,6 cm | la cabeza hace sombra |
| 8.000 Hz | 0,125 ms | 4,3 cm | del orden del largo del conducto (2,5 cm) |
| 226 Hz | 4,4 ms | 1,52 m | 60 veces el largo del conducto: la presión es pareja en todo él (→ Impedancia) |

**La fase se nota al sumar.** Dos tonos iguales y en fase suman sus presiones: ×2, es decir **+6 dB**. Con un desfase de 90° suman ×1,41 (+3 dB); con 120° la suma vale lo mismo que uno solo (0 dB); en oposición (180°) se **cancelan**. Esa es la razón de las ondas estacionarias (→ Acústica de sala), del **silbido** del audífono y de que el PEAT se registre con polaridad alternada: un estímulo de condensación y otro de rarefacción son el mismo sonido con la fase invertida, y el artefacto eléctrico del estímulo, que no se invierte con la respuesta, se cancela al promediarlos (→ H10).

### El espectro y los estímulos del examen

Todo sonido, por irregular que sea, se puede armar sumando tonos puros de distintas frecuencias y amplitudes. La lista de cuánto hay de cada frecuencia es su **espectro**. Hay una regla que lo gobierna todo: **cuanto más corto es un sonido en el tiempo, más ancho es su espectro** (el ancho de banda es del orden de 1 / duración). Un tono puro, que dura "para siempre", tiene una sola línea; un click, que dura una fracción de milisegundo, tiene energía en casi todas las frecuencias.

:::imagen ilustraciones/b4-estimulos.svg ancho=100% Forma de onda y espectro de los estímulos de los exámenes. Compara cada par: cuanto más corto es el estímulo en el tiempo, más ancho es su espectro.
:::

Tabla: Qué energía lleva cada estímulo y dónde se usa

| Estímulo | Qué es | Dónde está su energía | Se usa en |
|---|---|---|---|
| **Tono puro** | una sinusoide sostenida | una sola frecuencia | audiometría tonal (→ H3) |
| **Tono modulado** (FM, *warble*) | un tono cuya frecuencia sube y baja unos pocos por ciento, varias veces por segundo | una banda angosta alrededor de la frecuencia central | campo libre (→ H8) |
| **Click** | un pulso rectangular de unos 100 µs | casi toda la banda audible: plano hasta algunos kHz | PEAT, TEOAE (→ H9, H10) |
| **Tone burst** | un tono con subida, meseta y bajada (por ejemplo 2-1-2 ciclos) | una banda alrededor de su frecuencia | PEAT por frecuencia (→ H10) |
| **Chirp** | un barrido de graves a agudos | la misma banda que un click, repartida en el tiempo | PEAT (→ H10) |

Cuatro detalles de la figura valen un rato de lectura.

- **El click de 100 µs** tiene un espectro plano hasta unos 4 kHz (a 4,4 kHz cae 3 dB) y un primer nulo en 1 / 100 µs = **10 kHz**. Por eso el click es de "banda ancha". Qué zona del oído informa el PEAT con click no sale solo del estímulo: también cuentan la respuesta del fono y que la base de la cóclea responde primero y más sincrónica (→ H10).
- **El tone burst** de 5 ciclos dura 10 ms en 500 Hz, 5 ms en 1.000 Hz y 1,25 ms en 4.000 Hz. Como dura menos, su espectro es más ancho en términos absolutos: a −6 dB mide unos 180 Hz de ancho en 500 Hz, 370 Hz en 1.000 y 1.470 Hz en 4.000. El ancho relativo es el mismo (algo más de un tercio de la frecuencia), y es el precio de tener un estímulo corto que sincronice el nervio.
- **El chirp** y el click del dibujo tienen más o menos la misma energía por frecuencia. Lo que cambia es la **fase**: el chirp manda primero los graves y después los agudos, para que, descontado el tiempo que tarda la onda viajera en llegar a cada lugar de la cóclea, todas las frecuencias lleguen a la vez (Dau y cols., 2000). Es un ejemplo de que dos sonidos con el mismo espectro pueden ser distintos para el sistema auditivo. La forma dibujada es un ejemplo: cada equipo usa la suya.
- **El tono modulado** reparte su energía en una banda alrededor de la frecuencia central. Esa es toda su gracia: en una sala el tono puro se vuelve engañoso y la banda angosta no (→ Acústica de sala). Las normas fijan cuánto se desvía la frecuencia y a qué ritmo (IEC 60645-1, 2017; ISO 8253-2, 2009). <!-- verificar: desviación y ritmo exactos de la modulación (±5 % y unos pocos hercios) según la edición vigente de la IEC 60645-1. -->

### Ruidos

Un **ruido** es un sonido sin pauta: no se puede predecir su siguiente valor, así que solo se describe por su espectro. Los que usa este libro:

- **Ruido blanco** (*white noise*, WN): la misma energía en cada hercio. Como una octava de agudos tiene el doble de hercios que la octava anterior, el blanco **sube 3 dB por octava** cuando se mide por bandas de octava o de tercio de octava: suena silbante.
- **Ruido rosa** (*pink noise*, PN): la misma energía en cada **octava**. En densidad por hercio **baja 3 dB por octava**; por bandas de octava es plano. Suena más parejo y se parece más a lo que oímos en la vida.
- **Ruido de habla** (*speech noise*, SN): un ruido con el espectro promedio de la voz, con más energía en graves y medios y menos en agudos. Enmascara bien la palabra porque ocupa el mismo lugar que ella (→ H4, H5).
- **Ruido de banda estrecha** (*narrow band noise*, NBN): ruido filtrado a una banda alrededor de una frecuencia, de un tercio de octava o algo más según el equipo. Es el enmascarante de la audiometría y un estímulo de campo libre (→ H4, H8). <!-- verificar: ancho de banda del NBN que fijan IEC 60645-1 e ISO 389-4. -->

:::imagen ilustraciones/b4-ruidos.svg ancho=96% Ruido blanco y rosa, por hercio y por banda de un tercio de octava. El mismo ruido se ve plano o inclinado según cómo se mida: fíjate en qué eje usa cada panel antes de compararlos.
:::

**Banda crítica.** Un tono no es enmascarado por todo el ruido que suene, sino solo por el que cae **cerca de su frecuencia**. Fletcher (1940) lo mostró así: si se ensancha un ruido alrededor de un tono, el enmascaramiento sube hasta cierto ancho y después ya no sube más. Ese ancho es la **banda crítica**, el equivalente en frecuencia de un filtro de la cóclea. Es de unos 100 Hz bajo 500 Hz y crece desde ahí, hasta cerca de un sexto de la frecuencia central, algo menos que un tercio de octava.<!-- Pasada de fundamentos 2026-10-18: decía "cerca de un quinto de octava". Con la fórmula de Zwicker y Terhardt (1980), 25 + 75 (1 + 1,4 f²)^0,69 (f en kHz), la banda vale 162 Hz en 1 kHz, 301 Hz en 2 kHz y 688 Hz en 4 kHz: un 15-17 % de la frecuencia; un quinto de octava sería el 14 % y un tercio de octava, el 23 %. --> A 1.000 Hz es de unos 160 Hz (Zwicker, 1961; Zwicker y Terhardt, 1980); con otra forma de medirla, el ancho rectangular equivalente (ERB) da 133 Hz (Glasberg y Moore, 1990).

:::imagen ilustraciones/b4-banda-critica.svg ancho=96% La banda crítica comparada con la banda de un tercio de octava: bajo 500 Hz el tercio de octava es más angosto que la banda crítica y sobre 500 Hz, más ancho.
:::

Dos consecuencias que se usan en el libro. Primera: **bajo 500 Hz un ruido de tercio de octava es más angosto que la banda crítica y sobre 500 Hz es más ancho**, así que el ruido de un enmascarante se cuenta por la energía que cae dentro de una banda crítica y no por el nivel total. Segunda: lo que enmascara es la **potencia dentro de la banda**, que se calcula sumando el nivel por hercio y 10 log del ancho (→ Decibeles). Un ruido de 20 dB SPL por hercio entrega en 160 Hz de ancho 20 + 10 log 160 = 42 dB SPL. Además, un ruido de graves enmascara más a los agudos que al revés, porque la cóclea filtra de forma asimétrica (Gelfand, 2017).

### Filtros, y por qué el PEAT se filtra

Un **filtro** deja pasar unas frecuencias y atenúa otras. Hay cuatro formas: **pasa altos** (deja pasar sobre una frecuencia), **pasa bajos** (bajo una frecuencia), **pasa banda** (entre dos) y **de muesca** o *notch* (saca una banda angosta, como los 50 Hz de la red eléctrica). Un filtro se describe con su **frecuencia de corte**, donde la señal ha caído 3 dB (la mitad de la potencia), y su **pendiente**: cada "orden" del filtro agrega 6 dB de caída por octava.

El electrodo del PEAT recoge, mezcladas, tres cosas. La respuesta del tronco mide menos de 1 µV y su energía está bajo unos 1.000 Hz: en el adulto tiene picos entre 0 y 200 Hz, en 500-600 Hz y en 900-1.000 Hz (Hall, 1986); en el lactante se carga todavía más a los graves (Sininger, 1995). El EEG de fondo es 10 o 100 veces más grande y su energía está en las frecuencias bajas. El músculo y la red eléctrica meten ruido en otras bandas. Un pasa altos de 100 Hz y un pasa bajos de 3.000 Hz dejan adentro el grueso de la respuesta y sacan buena parte de lo demás, y con eso el promedio necesita menos barridos para mostrar la onda (→ Señal y ruido). Con un pasa altos de 2.º orden, la red de 50 Hz queda 12 dB más abajo.<!-- Pasada de fundamentos 2026-10-18: decía "su energía está sobre todo entre 100 y 3.000 Hz". Se corrigió con el espectro medido en 25 adultos normales (Hall, 1986: "energy peaks in three main regions: 0 to 200 Hz, 500 to 600 Hz and 900 to 1000 Hz") y en lactantes (Sininger, 1995: "energy in the infant ABR is concentrated below 100 Hz"). -->

:::imagen ilustraciones/b4-filtros.svg ancho=96% Los filtros del PEAT: lo que dejan pasar y lo que sacan. La banda de la respuesta queda adentro; el EEG de fondo, en los graves, y buena parte del ruido muscular y de la red quedan afuera.
:::

Filtrar tiene un costo. Un filtro cambia la forma de la onda: subir el pasa altos achica y adelanta las ondas, y un filtro muy angosto agrega oscilaciones (Picton, 2010). Por eso **no se filtra para embellecer**, y una norma de latencias solo sirve con los mismos filtros con que se midió (→ H10). Un filtro además es una pieza de muchos otros instrumentos: la **ponderación A** del sonómetro es un filtro (→ Ruido ocupacional), el audífono tiene un filtro por canal y el equipo de emisiones filtra por banda de frecuencia.

## Decibeles

### Por qué una escala logarítmica

El oído humano percibe presiones desde 20 µPa hasta unos 200 Pa: un rango de **diez millones a uno**. Una escala lineal obligaría a escribir números desde 0,00002 hasta 200. Y además el oído responde a las **razones**, no a las diferencias: pasar de 1 a 2 unidades de presión se oye como un salto parecido al de pasar de 10 a 20. La escala logarítmica resuelve ambas cosas.

El **decibel** (dB) es la décima parte de un *bel* y mide una **razón**, nunca una cantidad absoluta:

- para potencias o energías: dB = 10 log (*P* / *P*₀);
- para presiones: dB = 20 log (*p* / *p*₀), porque la potencia sube con el cuadrado de la presión.

Un número en dB solo significa algo si se dice **respecto de qué** (*re* en inglés): "60 dB" a secas no es un nivel. Con la referencia de 20 µPa se obtiene el **nivel de presión sonora** (dB SPL).

:::ayuda-ancho Ejemplo resuelto: del pascal al decibel
Una presión sonora RMS de 0,2 Pa: 20 × log (0,2 / 0,00002) = 20 × log 10.000 = 20 × 4 = **80 dB SPL**. De vuelta: 60 dB SPL son 20 µPa × 10^(60/20) = 20 µPa × 1.000 = 20.000 µPa = **0,02 Pa**. En la figura siguiente: cada +20 dB multiplica la presión por 10.
:::

:::imagen ilustraciones/b4-decibel.svg ancho=100% La escala de dB SPL, las reglas de cada paso y cómo suben dos fuentes al sumarse. Cada +20 dB multiplica la presión por 10, y dos fuentes iguales suman solo 3 dB, no el doble de decibeles.
:::

### Las reglas de 3, 6 y 10 dB

Con la definición salen las reglas que se usan todos los días:

Tabla: Qué significa un cambio de nivel

| Cambio | Presión | Energía (potencia) |
|---|---|---|
| 1 dB | ×1,12 | ×1,26 |
| **3 dB** | ×1,41 | **×2** |
| **6 dB** | **×2** | ×4 |
| **10 dB** | ×3,16 | **×10** |
| 20 dB | ×10 | ×100 |
| 40 dB | ×100 | ×10.000 |

La regla de **10 dB "el doble de sonoridad"** es de otra naturaleza: no es física sino perceptiva. A niveles moderados y para un tono de 1.000 Hz, 10 dB más suenan más o menos el doble de fuerte (Stevens, 1955); la sección *Del sonido a lo que se oye* la matiza. Una pérdida de 40 dB significa que el oído necesita **cien veces más presión** (diez mil veces más energía) que uno normal para oír lo mismo.

### Sumar y restar decibeles

Dos fuentes de sonido independientes, que no tienen fase en común (dos máquinas, dos parlantes con ruido), suman **energías**, no decibeles:

*L* = 10 log (10^(*L*₁/10) + 10^(*L*₂/10))

:::ayuda-ancho Ejemplos resueltos: sumar y restar
- **Dos máquinas de 90 dB**: 10 log (10⁹ + 10⁹) = 10 log (2 × 10⁹) = 90 + 3 = **93 dB**, no 180. Tres de 80 dB: 80 + 10 log 3 = **84,8 dB**.
- **90 dB más 80 dB**: 10 log (10⁹ + 10⁸) = **90,4 dB**. La más débil casi no cuenta. Con 10 dB de diferencia se suma 0,4 dB; con 20 dB, 0,04 dB.
- **Restar el ruido de fondo.** Con la máquina encendida el sonómetro marca 66 dB; apagada, el fondo marca 60. La máquina sola es 10 log (10^6,6 − 10^6,0) = 10 log (3,98 × 10⁶ − 1,00 × 10⁶) = **64,7 dB**. Con 3 dB de diferencia entre "con" y "sin" hay que restar 3 dB; con 6 dB, 1,3 dB; con 10 dB o más, 0,5 dB o menos.
- **El promedio de niveles** también es de energía: el promedio de 80 y 90 dB es 10 log ((10⁸ + 10⁹) / 2) = **87,4 dB**, no 85. (Los umbrales de un audiograma, en cambio, se promedian como números porque son niveles de una referencia común: el promedio tonal del audiograma es una convención, → H3.)
:::

Si en vez de ruido son dos tonos iguales **de la misma frecuencia**, la suma depende de la fase (→ El sonido): de +6 dB en fase hasta la cancelación en oposición. Esa es la diferencia entre sumar energías y sumar presiones.

### Las referencias: SPL, HL, SL, nHL, eHL y EM

Cada escala de decibeles del libro es la misma cuenta con otro cero.

- **dB SPL**: el cero es 20 µPa, la presión que se aproxima al umbral de un oído joven a 1.000 Hz. Es una escala **física**, sin oyente: la mide un micrófono. Con la ponderación A se llama dB(A) (→ Ruido ocupacional).
- **dB HL** (*hearing level*): el cero es el **umbral de un adulto joven otológicamente normal, en esa frecuencia y con ese transductor**. En cada frecuencia, dB SPL = dB HL + RETSPL. Por eso **0 dB HL no es 0 dB SPL**: con el fono TDH-39, 0 dB HL son 45 dB SPL a 125 Hz y 7 dB SPL a 1.000 Hz (ISO 389-1, 2017; → H3).
- **dB SL** (*sensation level*): el cero es el **umbral del propio paciente**. 20 dB SL son 20 dB sobre lo que él detecta. La logoaudiometría y las pruebas supraliminares lo usan (→ H5, H6).
- **dB nHL** (*normalized hearing level*): el cero es el nivel al que un grupo de adultos jóvenes normales detecta **ese mismo estímulo breve**, en ese equipo (ISO 389-6, 2007; IEC 60645-3). Un click o un burst se oyen peor que un tono sostenido porque el oído suma la energía durante unas décimas de segundo, así que cada estímulo corto necesita su propio cero. Los equipos de potenciales usan además el **dB peSPL** (SPL equivalente de pico a pico): el nivel del tono continuo que tiene la misma amplitud de pico a pico que el estímulo breve, que es como se expresan los umbrales de referencia de los estímulos breves (Poulsen y Legarth, 2008).<!-- Pasada de fundamentos 2026-10-18: decía "SPL de pico equivalente ... la misma amplitud de pico". La medida de la norma es de pico a pico (Poulsen y Legarth, 2008, abstract: "peak-to-peak equivalent threshold sound pressure levels (peETSPL)... part of the basis for the ISO 389-6 standard"). --> El 0 dB nHL de un click equivale a unos 30 a 40 dB peSPL, según el transductor. <!-- verificar: valor de peSPL del 0 dB nHL del click según ISO 389-6 e IEC 60645-3. -->
- **dB eHL** (*estimated hearing level*): no es una referencia física. Es la **estimación del umbral tonal** que se obtiene restando una corrección, publicada para cada estímulo y frecuencia, al umbral electrofisiológico en dB nHL. Con burst de 500 Hz, un umbral de 40 dB nHL queda en 40 − 20 = **20 dB eHL** (→ H10, H13).
- **dB EM** (*effective masking*, enmascaramiento efectivo): el nivel de un ruido **expresado como el dB HL del tono que ese ruido apenas enmascara** (ISO 389-4, 1994). Un ruido de banda estrecha de 40 dB EM sube a 40 dB HL el umbral de un tono de su banda. Lo que importa en la clínica es cuánto sube el umbral. Por eso el enmascarante se calibra en EM, y no en dB HL, que es lo que el ruido necesita para ser *detectado*, 5 a 10 dB menos (→ H4, H8). <!-- verificar: diferencia entre el nivel de detección de un ruido de banda estrecha y su nivel de enmascaramiento efectivo; las correcciones de la ISO 389-4 sobre el RETSPL (que se citan de memoria en unos 4 dB para tercio de octava y 6 dB para media octava) no se pudieron leer: la norma es de pago. -->

Tabla: Las referencias de los decibeles

| Escala | El cero es | Quién la "mide" | Se usa en |
|---|---|---|---|
| dB SPL | 20 µPa | un micrófono | calibración, ruido, audífonos, reflejos en LabSim |
| dB HL | umbral normal de ese transductor | el audiómetro, por calibración | audiometría tonal y logoaudiometría |
| dB SL | umbral del paciente | el audiómetro, con el umbral anotado | logoaudiometría, supraliminares |
| dB nHL | umbral normal de ese estímulo breve | el equipo de potenciales | PEAT, ECochG, ASSR |
| dB eHL | (estimación) | cálculo: dB nHL menos la corrección | informe de PEAT y ASSR |
| dB EM | el dB HL que el ruido enmascara | el audiómetro | enmascaramiento |

### RETSPL y calibración

El **RETSPL** (*reference equivalent threshold sound pressure level*) es el nivel de presión, medido en un acoplador específico con un transductor específico, que corresponde a **0 dB HL**. Está en tablas de la serie ISO 389: la parte 1 para fonos supraaurales, la 2 para los de inserción, la 3 para el vibrador óseo (donde la referencia no es presión sino **fuerza**, en dB re 1 µN), la 7 para campo libre y la 6 para estímulos breves. Es la tabla que el audiómetro guarda y resta.

Tabla: RETSPL de dos fonos (dB SPL; ISO 389-1 e ISO 389-2, este último en el acoplador de 2 cm³)

| Fono | 125 Hz | 250 Hz | 500 Hz | 1.000 Hz | 2.000 Hz | 4.000 Hz |
|---|---|---|---|---|---|---|
| TDH-39 (supraaural) | 45 | 25,5 | 11,5 | 7 | 9 | 9,5 |
| ER-3A (inserción) | 26 | 14 | 5,5 | 0 | 3 | 5,5 |

<!-- Pasada de fundamentos 2026-10-18: los valores del ER-3A (26; 14; 5,5; 0; 3; 5,5) coinciden con la tabla 1 de la ISO 389-2 para el acoplador IEC 126 (2 cm³); en el simulador de oído ocluido (IEC 711) son otros (28; 17,5; 9,5; 5,5; 11,5; 15). -->

:::imagen ilustraciones/b4-escalas.svg ancho=96% El mismo tono de 60 dB SPL en dB SPL, dB HL y dB SL. El sonido no cambia: cambia contra qué se compara, un micrófono, el oído normal o el umbral de este paciente.
:::

:::ayuda-ancho Ejemplo resuelto: qué pasa si se calibra para un fono y se usa otro
Un audiómetro calibrado para TDH-39 presenta "20 dB HL" a 1.000 Hz como 20 + 7 = 27 dB SPL, y a 125 Hz como 20 + 45 = 65 dB SPL. Si se le conecta un fono de inserción sin recalibrar, ese mismo nivel equivale, para el ER-3A, a 27 − 0 = 27 dB HL a 1.000 Hz y a 65 − 26 = **39 dB HL a 125 Hz**. El paciente oiría un sonido más fuerte que el que dice la pantalla, y todos sus umbrales saldrían **mejores de lo que son, en 7 dB a 1.000 Hz y en 19 dB a 125 Hz** (el cálculo es aproximado: los acopladores no son iguales). Por eso "el cero es de cada transductor" (→ H3).
:::

Calibrar es comprobar que el audiómetro entrega esos niveles. Hay tres niveles de control: la **verificación subjetiva diaria** (que suene, que un oyente conocido oiga igual que siempre; → H3), la **calibración objetiva** periódica (se mide la presión con un acoplador y un sonómetro, y la fuerza del vibrador con una mastoides artificial) y la **calibración exhaustiva**. Las tolerancias y la periodicidad las fijan la ANSI S3.6, la IEC 60645-1 y la norma local.

### Atenuación: interaural, del protector y del molde

Una **atenuación** es la diferencia de nivel, en dB, entre lo que llega y lo que pasa. Dos barreras en paralelo no se suman en dB: se suman las **energías que dejan pasar**, y la barrera más débil manda.

:::ayuda-ancho Ejemplo resuelto: una fuga pone el techo de un tapón
Un tapón que por sí solo atenúa 30 dB deja pasar 10^(−3) de la energía. Si tiene una fuga que por sí sola atenuaría 20 dB (10^(−2)), el sonido pasa por las dos vías: 10⁻³ + 10⁻² = 1,1 × 10⁻². La atenuación total es −10 log (1,1 × 10⁻²) = **19,6 dB**. El tapón de 30 dB, con una fuga, **no atenúa ni 20**. Esa es la razón de insistir en que el protector y el molde estén bien puestos (→ H21, H23).
:::

**Atenuación interaural.** Un fono pone a vibrar la caja del fono y, con ella, el cráneo; esa vibración llega a la cóclea contraria. La atenuación interaural es lo que se pierde en ese camino. Depende del transductor, de la frecuencia y del paciente, y se toma el mínimo: **40 dB** con fono supraaural, **55 dB** o más con inserción y casi 0 con el vibrador óseo (BSA, 2018; Munro y Agnew, 1999; Stenfelt, 2012). Los decibeles se restan porque son una diferencia de niveles.

:::ayuda-ancho Ejemplo resuelto: cuándo el otro oído "oye" el tono
Se presenta un tono de 80 dB HL al oído derecho. Con un fono supraaural (40 dB), llegan 80 − 40 = **40 dB** a la cóclea izquierda; si el umbral óseo del izquierdo es 30 dB, ese oído lo detecta y el umbral que se anota puede ser **del oído equivocado**. Con inserción (55 dB) llegan 80 − 55 = **25 dB**, bajo los 30 dB del umbral: el tono no cruza. Es la lógica de la decisión de enmascarar (→ H4).
:::

**Protector auditivo.** Su atenuación se mide, en personas, como la diferencia entre el umbral con y sin protector (ISO 4869-1, 2018). Crece con la frecuencia, porque las ondas cortas son las que mejor se frenan, y se pierde sobre todo por **fugas**. Lo que importa para el trabajador es el nivel que queda en el oído, que es el nivel del ambiente menos la atenuación *real*. Esa suele ser menor que la de la etiqueta, que se mide en laboratorio: NIOSH recomienda descontarle un 25 % en las orejeras, un 50 % en los tapones moldeables y un 70 % en los demás tapones (NIOSH, 1998; → H23).

**Molde del audífono.** Un molde cerrado y bien sellado se comporta como un tapón: el audífono queda aislado del exterior y los graves se acumulan en el conducto. Una **ventilación** es un tubo angosto que atraviesa el molde: deja salir los graves (más cuanto más ancha), mejora la oclusión y reduce la ganancia grave, y deja volver sonido al micrófono (→ H21, H22; Dillon, 2012).

## Del sonido a lo que se oye

La **psicoacústica** estudia la relación entre las características físicas de un sonido y lo que se percibe. Cada magnitud física tiene su pariente perceptivo, y **no se corresponden una a una**.

Tabla: Lo físico y lo percibido

| Físico | Se percibe como | Lo que hay que saber |
|---|---|---|
| Frecuencia | **tono** (agudo o grave) | el orden se conserva, pero no es una recta: hasta 2.000 Hz se distinguen cambios de menos del 0,6 % de la frecuencia (Sek y Moore, 1995) |
| Nivel | **sonoridad** (fuerte o suave) | depende también de la frecuencia (curvas de igual sonoridad) |
| Duración | **duración** | bajo unos 200 ms el oído suma la energía, y un tono más corto necesita más nivel para detectarse |
| Espectro y envolvente | **timbre** | es lo que distingue una vocal de otra, o un piano de una guitarra con la misma nota |

**Sonoridad y curvas de igual sonoridad.** Un tono de 125 Hz y uno de 1.000 Hz con el mismo nivel en dB SPL no suenan igual de fuertes: el oído es menos sensible en los graves, y el umbral de 125 Hz está en 45 dB SPL con el TDH-39 contra 7 dB SPL en 1.000 Hz (→ Decibeles). Fletcher y Munson (1933) midieron a qué nivel hay que poner un tono de cada frecuencia para que suene tan fuerte como uno de 1.000 Hz; cada curva se rotula con ese nivel de 1.000 Hz, en **fonos** (ISO 226, 2023). Al subir el nivel las curvas se aplanan: los graves "alcanzan" a los medios. Para medir cuánto más fuerte suena un sonido hay otra escala, el **sono**: 1 sono es la sonoridad de 40 fonos, y cada +10 fonos la duplica. Así 50 fonos son 2 sonos, 60 son 4, 70 son 8 y 80 son 16 (Stevens, 1955). Cerca del umbral, la sonoridad crece más rápido que eso, y por eso la regla de los 10 dB solo vale a niveles moderados y altos.

**Campo auditivo.** Es la región, en el plano frecuencia-nivel, que va de lo que apenas se oye (el umbral) a lo que molesta o duele: unas frecuencias de 20 a 20.000 Hz y unos niveles de 0 a 120 dB SPL. El habla ocupa una parte de ese campo (→ H3, H5).

**Los tres ceros.** Hay tres "ceros" que no hay que confundir: el **absoluto** (0 dB SPL, 20 µPa, una referencia física), el **audiométrico** (0 dB HL, el umbral normal de cada frecuencia y transductor) y el **relativo** al propio paciente (0 dB SL, su umbral). El primero es de un micrófono; el segundo, de una población; el tercero, de una persona.

**Duración.** El oído integra energía durante unas décimas de segundo: por eso con un tono de 1 a 2 s el umbral deja de depender de la duración (→ H3), y por eso un click necesita su propio cero (dB nHL).

**Lo que no es físico.** La percepción también depende de la **adaptación** (un sonido sostenido se "apaga"), de la **expectativa** y de la **atención**. Son la razón de que el umbral sea una probabilidad y no un número (→ H3), y de que la técnica use silencios irregulares y tonos pulsados.

**Enmascaramiento.** Un sonido hace inaudible a otro cercano en frecuencia. Su ancho es la banda crítica (→ El sonido), y es la razón de que el ruido del enmascaramiento sea de banda estrecha y se calibre en EM (→ Decibeles; H4).

## Impedancia y admitancia

### El oído medio como masa, resorte y roce

La **impedancia acústica** (*Z*) es cuánto se **opone** un sistema al paso del sonido: presión dividida por el flujo de aire que esa presión logra mover. Su inversa, la **admitancia** (*Y* = 1 / *Z*), es qué tan **fácil** le resulta al sonido pasar. Un tímpano que se mueve fácil deja pasar mucho sonido y tiene admitancia alta; uno rígido, admitancia baja. La unidad clásica es el *milimho* acústico (mmho). La impedancia tiene tres componentes, que se entienden con un objeto: una masa colgada de un resorte, con un amortiguador.

- **Rigidez** (inversa de la *compliancia*): el resorte. Se opone más a los movimientos **lentos**, es decir, a las frecuencias bajas. Viene de la membrana, de los ligamentos y del aire encerrado en el oído medio.
- **Masa**: lo que pesa. Se opone más a los movimientos **rápidos**, a las frecuencias altas. Viene de los huesecillos y del líquido.
- **Roce** (resistencia): el amortiguador. No depende de la frecuencia y gasta energía en forma de calor.

A una frecuencia el resorte y la masa se **anulan entre sí**: la oposición de uno compensa la del otro y solo queda el roce. Es la **frecuencia de resonancia**, *f*₀ = 1 / (2π √(*M* × *C*)), con *M* la masa y *C* la compliancia. En ella la admitancia es máxima. Un oído medio normal de adulto resuena por debajo de los 1.000 Hz: en 100 oídos normales la media fue de 935 Hz. Un oído **más rígido** sube su resonancia (en la otosclerosis la media fue de 1.190 Hz; Ogut y cols., 2008); uno **más laxo** (una cadena interrumpida) la baja.<!-- Pasada de fundamentos 2026-10-18: decía "resuena en torno a 1.000 Hz (Margolis y Goycoolea, 1993)" y "más rígido (otosclerosis, líquido)". El abstract de Margolis y Goycoolea no da el valor; se citó Ogut y cols. (2008), abstract: "Mean middle-ear resonant frequency for the otosclerotic group was found to be 1190 Hz and mean middle-ear resonant frequency of the control group was 934.6 Hz". Se quitó "líquido": no se encontró respaldo de que la efusión suba la resonancia de forma constante. -->

:::imagen ilustraciones/b4-resonancia.svg ancho=100% Masa, rigidez y roce, y la admitancia de tres oídos de juguete: uno normal, uno rígido y uno laxo. Mira cómo cambia el orden entre los tres al pasar de la sonda de 226 Hz a la de 1.000 Hz.
:::

La figura es un modelo de juguete con los mismos valores de masa y roce, para que se vea la idea, y no un oído real. Con la sonda de **226 Hz**, que queda bajo la resonancia, el oído se comporta casi como un resorte, y lo que se mide es la compliancia: el oído rígido da menos (0,4 veces el normal en el modelo), el laxo da más (2,3 veces). Son los timpanogramas tipo As y tipo Ad (→ H7). A **1.000 Hz**, cerca de la resonancia, el orden es otro: el normal queda en su máximo y el laxo, casi a su altura (3,7 contra 4,3), así que los tipos ya no se leen igual. Cada sonda ve algo distinto porque **mide otra parte de la curva**.

### Por qué 226 Hz y qué es un volumen equivalente

Una cavidad cerrada de aire tiene una compliancia que depende de su volumen, *C* = *V* / (ρ*c*²), con ρ*c*² = 1,4 × la presión atmosférica = 1,42 × 10⁶ dinas/cm². Su admitancia a una frecuencia *f* es *Y* = 2π*f* × *C*.

:::ayuda-ancho Ejemplo resuelto: por qué a 226 Hz un mL equivale a un mmho
Para 1 cm³ (1 mL) de aire a 226 Hz: *Y* = 2π × 226 / 1,42 × 10⁶ = **1,00 × 10⁻³** cm⁵/(dina·s), es decir, **1,00 mmho**. A 226 Hz, entonces, "1 mL de aire" y "1 mmho" son el mismo número, y la admitancia se puede informar como el **volumen equivalente**: el volumen de aire que tendría la misma compliancia. Es la razón de que el equipo informe en mL (→ H7). A **1.000 Hz**, en cambio, 1 mL equivale a 2π × 1.000 / 1,42 × 10⁶ = **4,43 mmho**: la equivalencia se pierde, y por eso con la sonda de 1.000 Hz no se lee el volumen del conducto en mL (→ H7).
:::

Hay una segunda razón para una sonda de frecuencia baja. A 226 Hz la longitud de onda es de **1,52 m**, 60 veces el largo del conducto (2,5 cm): la presión es pareja en todo el conducto y el sistema se puede tratar como un sistema simple de masa, resorte y roce. A frecuencias altas las ondas dentro del conducto empiezan a contar. De hecho el conducto, que es un tubo cerrado en un extremo por el tímpano, tiene su primera resonancia cuando mide un cuarto de longitud de onda: *f* = *c* / (4 *L*) = 343 / (4 × 0,025) = **3.430 Hz**. Con el largo efectivo real y la concha, cae a los 2,5 a 3 kHz de H3, que es el refuerzo que el conducto le da a esas frecuencias (Shaw, 1974).

**La sonda de 1.000 Hz en el lactante.** Bajo los 6 meses el oído medio pesa más en masa que en rigidez y la pared del conducto todavía cede con la presión (→ H7). A 226 Hz esas dos cosas deforman el timpanograma, y un oído con líquido puede dar un pico "normal". Con 1.000 Hz, la sonda queda cerca de la resonancia y ve al sistema donde la masa cuenta, y el timpanograma refleja mejor si hay líquido (Holte y cols., 1991; Kei y cols., 2003; Alaerts y cols., 2007). El costo es el que ya se vio: ya no se pueden dar los números en mL.

### La presión en daPa

Para medir la admitancia en cada presión el equipo cambia la presión del aire del conducto. La unidad es el **decapascal**: 1 daPa = 10 Pa ≈ 1,02 mmH₂O. El rango de +200 a −400 daPa son +2.000 y −4.000 Pa, es decir, entre +2 % y −4 % de la presión atmosférica. Una presión de −100 daPa son −1.000 Pa, cerca de **un 1 % de la atmósfera** (−10 cmH₂O): una presión muy pequeña que ya basta para empujar el tímpano hacia adentro y cambiar su rigidez (→ H7). Esa es la razón de que el pico del timpanograma sea una medida tan fina de la presión del oído medio.

:::ayuda-ancho Ejemplo resuelto: de los números del equipo a la compliancia
En un timpanograma de 226 Hz, el equipo lee **1,2 mL** en el extremo (+200 daPa), donde el tímpano casi no se mueve y solo se mide el aire del conducto, y **1,9 mL** en el pico. La **compliancia del oído medio** (la admitancia estática) es la diferencia, 1,9 − 1,2 = **0,7 mL**, dentro de lo normal en un adulto (0,3 a 1,6 mL; → H7). El volumen del conducto es 1,2 mL. Si ese volumen fuera de 4,5 mL sin pico, el equipo estaría midiendo el conducto más una caja abierta: una perforación (→ H7).
:::

## Señal y ruido

### La relación señal/ruido

En un registro hay lo que se quiere medir (la **señal**) y lo que se mezcla con ella (el **ruido**). La **relación señal/ruido** (SNR) se da en decibeles: SNR = 20 log (*A*señal / *A*ruido) con amplitudes RMS, o 10 log de las potencias. Una SNR de 0 dB es una señal igual de grande que el ruido; 6 dB, el doble; 10 dB, 3,2 veces; 20 dB, diez veces. En las emisiones otoacústicas la regla de H9 es ≥ 6 dB: una emisión al menos el doble de grande que el ruido.

### Promediar: el ruido baja con la raíz de N

Si el estímulo se repite *N* veces y se promedian los tramos que siguen a cada uno, la señal, que es **igual en cada barrido**, queda igual. El ruido, que es **distinto** en cada barrido, se promedia hacia cero: sus amplitudes se suman como las varianzas, es decir, crecen con √*N* al sumar, y al dividir por *N* quedan en **σ / √N**. Por eso la SNR mejora √*N* veces, que en decibeles es **10 log *N***: cada vez que *N* se **cuadruplica**, el ruido se divide por 2 (y la SNR sube 6 dB), y cada vez que se duplica, el ruido se divide por √2 (+3 dB).

:::imagen ilustraciones/b4-promedio.svg ancho=100% Al promediar, el ruido residual cae con √N y aparece la señal
:::

Tabla: Una onda V de 0,5 µV con un ruido de 5 µV por barrido

| Barridos (N) | Ruido residual | Señal / ruido | Mejora sobre un barrido | Tiempo a 21,1 estímulos/s |
|---|---|---|---|---|
| 1 | 5,0 µV | −20 dB | 0 dB | 0,05 s |
| 100 | 0,50 µV | 0 dB | 20 dB | 4,7 s |
| 500 | 0,22 µV | 7 dB | 27 dB | 24 s |
| 1.000 | 0,16 µV | 10 dB | 30 dB | 47 s |
| 2.000 | 0,11 µV | 13 dB | 33 dB | 95 s |
| 4.000 | 0,079 µV | 16 dB | 36 dB | 190 s |
| 8.000 | 0,056 µV | 19 dB | 39 dB | 379 s |

:::ayuda-ancho Ejemplo resuelto: cuánto cuesta bajar el ruido
Con 2.000 barridos el ruido residual es 5 / √2.000 = **0,11 µV**, y una onda V de 0,5 µV queda con una SNR de 20 log (0,5 / 0,11) = **13 dB**. De 1.000 a 2.000 barridos el ruido baja a 0,71 de lo que era (un 29 %), porque √2 = 1,41. Para dejarlo **a la mitad** hacen falta **4 veces** los barridos: de 2.000 a 8.000, que a 21,1 estímulos por segundo son 95 s contra 379 s. Cada mejora cuesta cuatro veces más que la anterior, y por eso en la práctica se promedia hasta lograr un criterio, no "lo más posible" (→ H10, cap. 18).
:::

El resultado vale solo mientras se cumplan tres supuestos, y sirve para entender qué hacer cuando no se cumplen:

- **El ruido es aleatorio y distinto en cada barrido.** Un artefacto atado al estímulo (el eléctrico del fono) no se promedia hacia cero. La polaridad alternada lo cancela (→ H10).
- **El ruido es de la misma magnitud en todos los barridos.** Un movimiento o una contracción del músculo mete barridos muy grandes que arruinan el promedio. El **rechazo de artefactos** (±25 µV en H10) descarta el barrido que supera un umbral.
- **El ruido no se repite al ritmo del estímulo.** La red eléctrica de 50 Hz es un ruido periódico: si la tasa de estímulos fuera de 25 por segundo, la red caería en la misma fase en cada barrido y **se sumaría** en vez de cancelarse. Con 21,1 estímulos por segundo, 50 / 21,1 = 2,37 no es entero: cada barrido ve la red en otra fase, y se promedia hacia cero. Por eso la tasa del PEAT es un número "raro" (→ H10).

### Ruido residual, FSP y reproducibilidad

Para saber cuánto ruido queda en el promedio no hay que adivinar. Si los barridos se reparten, uno a uno, en dos memorias, **A** y **B**, la **suma** (A + B) / 2 es el promedio completo (señal más ruido), y la **resta** (A − B) / 2 es un trazo donde la señal se cancela y queda **solo ruido**, con la misma magnitud que el ruido del promedio. El RMS de esa resta es el **ruido residual** del equipo, en nanovoltios (→ H10).

**La reproducibilidad entre A y B.** La señal es igual en las dos memorias y el ruido, distinto. La correlación entre ellas vale *r* = *S* / (*S* + *N*), con *S* y *N* las potencias de la señal y del ruido **de cada memoria**, de modo que SNR (por memoria) = *r* / (1 − *r*). Con eso se traducen las cifras de H9 y H10:

Tabla: De la reproducibilidad a la relación señal/ruido (por memoria)

| Reproducibilidad | SNR por memoria | Lectura |
|---|---|---|
| 5 % | −12,8 dB | no hay respuesta: A y B son dos ruidos distintos |
| 70 % | 3,7 dB | el límite que pide H9 para una TEOAE |
| 91 % | 10,0 dB | una emisión clara |

Al combinar las dos memorias en el promedio completo, el ruido baja a la mitad en potencia: la SNR del promedio es **3 dB más** que la de cada memoria. La regla de H10, "una onda que no está en las dos curvas no es una onda", es esto: el ruido no se repite y la respuesta sí.

**El FSP** (*F single point*; Elberling y Don, 1984) es una prueba estadística de que hay respuesta. Compara dos varianzas (la varianza mide cuánto se aleja un trazo de su promedio):

*FSP* = varianza del promedio en la ventana de análisis / varianza del ruido que queda en el promedio

El numerador incluye la señal y el ruido. El denominador se estima **en un solo punto del tiempo**: en una latencia fija, la señal vale lo mismo en todos los barridos, así que lo que varía de un barrido a otro en ese punto es **solo ruido**; esa varianza, dividida por *N*, es la del ruido del promedio. Sin respuesta, numerador y denominador miden lo mismo y el FSP vale **cerca de 1**. Con respuesta, el numerador crece. H10 usa **3,1** como criterio de detección del 99 % (Elberling y Don, 1984).

:::ayuda-ancho Ejemplo resuelto: un FSP, con números
Con 5 µV de ruido por barrido y 2.000 barridos, la varianza del ruido en el promedio es 5² / 2.000 = **0,0125 µV²** (0,11 µV RMS). Supón una respuesta cuya potencia en la ventana equivale a 0,2 µV RMS (0,04 µV²). El FSP es (0,04 + 0,0125) / 0,0125 = **4,2**: sobre el criterio de 3,1, hay respuesta. Con una respuesta de 0,1 µV RMS (0,01 µV²) el FSP baja a (0,01 + 0,0125) / 0,0125 = **1,8**: no alcanza, y la salida correcta es seguir promediando. Con 8.000 barridos el denominador baja a 0,0031 µV², y el mismo 0,01 µV² da (0,01 + 0,0031) / 0,0031 = 4,2: ahora sí se detecta.
:::

**Partir los barridos a la mitad.** Con la mitad de los barridos el ruido sube √2, o sea 3 dB. Para mantener la misma SNR hace falta una respuesta 3 dB más grande. Cuántos dB de intensidad del estímulo hay que subir para ganar esos 3 dB de amplitud depende de la pendiente con que crece la onda V con el nivel; en LabSim el efecto es de unos 6 dB de umbral por cada mitad de barridos (→ H10).

## Acústica de sala

### Ondas estacionarias

Cuando un tono puro suena en una sala con paredes, el sonido directo del parlante y el reflejado por la pared se **suman**. Donde llegan en fase, el nivel sube; donde llegan en oposición, baja. La presión del campo es *p* = *p*directo × (1 + *r* × e^(−j2*kD*)), con *r* el coeficiente de reflexión de la pared, *D* la distancia a ella y *k* = 2π/λ. El nivel oscila entre (1 − *r*)² y (1 + *r*)² en potencia, es decir, entre máximos y mínimos separados por 20 log ((1 + *r*) / (1 − *r*)) dB: **9,5 dB** con una pared que refleja la mitad de la presión (*r* = 0,5), **15,1 dB** con *r* = 0,7, **19,1 dB** con 0,8 y **25,6 dB** con 0,9. Entre un máximo y un mínimo hay un cuarto de longitud de onda: **8,6 cm a 1.000 Hz** y 2,1 cm a 4.000 Hz.

En una sala cerrada, además, hay frecuencias propias: entre dos paredes paralelas separadas *L*, hay ondas estacionarias en *f* = *n* × *c* / (2 *L*). Con *L* = 3 m son 57, 114, 172 Hz, etc., y en los graves esas frecuencias son pocas y bien separadas, por lo que la sala refuerza unas y apaga otras.

:::imagen ilustraciones/b4-onda-estacionaria.svg ancho=100% Un tono puro frente a una pared: el nivel cambia en pocos centímetros
:::

La consecuencia para el examen es directa. **Un umbral con tono puro en campo libre depende de dónde está la cabeza**: moverla 8 cm cambia el nivel en el oído varios decibeles, y no hay forma de que el paciente quede siempre en el mismo punto. Por eso en campo libre se usa un **tono modulado** o un **ruido de banda estrecha** (→ H8): con la energía repartida en una banda, los máximos y los mínimos de cada frecuencia caen en lugares distintos y se compensan. En el cálculo de la figura (una pared con *r* = 0,7, la cabeza entre 1,0 y 1,5 m), el nivel varía **15,1 dB** con un tono puro, **2,0 dB** con un tono modulado de 1.000 Hz ± 5 % y **1,8 dB** con un ruido de un tercio de octava. No llega a cero, y por eso las normas piden además condiciones de sala y un punto marcado para la cabeza (ISO 8253-2, 2009).

### La distancia y el ángulo del parlante

**Distancia.** En campo libre la presión baja con la distancia: **6 dB por cada vez que se duplica la distancia** (ley del inverso del cuadrado). Si la cabeza queda a 1 m y se mueve 10 cm, el nivel cambia entre +0,8 y −0,9 dB; a 0,5 m, la misma desviación cambia entre +1,6 y −1,9 dB. Por eso el parlante va a **1 m o más** del paciente (→ H8): a esa distancia un movimiento normal de la cabeza deja el nivel dentro de 1 dB, y el sonido directo domina sobre el reflejado.

**Ángulo.** Cuando la longitud de onda es menor que la cabeza, que tiene unos 18 cm, la cabeza hace **sombra**: sobre unos 1.900 Hz (343 m/s / 0,18 m) el oído lejano al parlante recibe menos nivel que el cercano, y la diferencia crece con la frecuencia; bajo 500 Hz, con ondas de 0,7 m o más, la cabeza casi no estorba (Shaw, 1974). Por eso el cero de campo libre se fija con el sonido llegando de frente (0°) y con los dos oídos, y por eso la posición del parlante respecto de la cabeza cambia el nivel que llega a cada oído (ISO 389-7, 2019; → H8).

### Ruido ambiente y cabina

Un ruido de fondo **sube el umbral**: enmascara el tono de prueba con el mismo mecanismo de la banda crítica. Importa el nivel del ruido **en la banda crítica del tono**, en el oído del paciente. Los instrumentos entregan ese nivel por bandas de octava o de tercio de octava, y para pasar de una a otra se resta **10 log 3 = 4,8 dB** (un ruido parejo repartido en tres tercios).

:::ayuda-ancho Ejemplo resuelto: cuánto sube un umbral un ruido de fondo (orden de magnitud)
Un ruido de 25 dB SPL en la banda de un tercio de octava de 1.000 Hz (232 Hz de ancho) tiene un nivel por hercio de 25 − 10 log 232 = 1,3 dB. Con una razón crítica de unos 18 dB (el nivel del tono apenas enmascarado menos el nivel por hercio del ruido; Hawkins y Stevens, 1950), el tono apenas enmascarado queda en 1,3 + 18 = **19 dB SPL**. El umbral de un oído normal a 1.000 Hz con el TDH-39 es de 7 dB SPL: el ruido lo subiría unos **12 dB**. Un ruido de ese nivel en el oído del paciente es demasiado para medir 0 dB HL. <!-- verificar: razón crítica en 1.000 Hz (se cita de memoria entre 18 y 20 dB; Fletcher, 1940; Hawkins y Stevens, 1950). -->
:::

Por eso las normas fijan un **ruido ambiente máximo** por banda de octava, según el tipo de medición (ISO 8253-1, 2010; ANSI S3.1, 2018). Los límites son más estrictos cuando el oído queda **sin cubrir** (la vía ósea, → H3) y más holgados cuando el fono tapa el oído: los fonos de inserción dan más aislamiento que los supraaurales (Berger y Killion, 1989).

La **cabina** resuelve el problema con dos paredes separadas por aire y con **masa**: la ley de masas dice que el aislamiento sube **6 dB cada vez que se duplica la masa de la pared o la frecuencia** (Rossing, 2007). Por eso una cabina frena bien los agudos y mal los graves, y las bandas de 125 y 250 Hz son las primeras que el ruido del edificio (tráfico, ventilación) vuelve inutilizables. Por dentro, el revestimiento **absorbente** reduce los ecos de la propia cabina.

## Electroacústica del audífono

**Ganancia.** La ganancia de un audífono es la diferencia entre el nivel de salida y el de entrada, en dB: con 60 dB SPL de entrada y 90 dB SPL de salida, la ganancia es **30 dB**. Cambia con la frecuencia y, en los audífonos que comprimen, con el nivel.

**Salida máxima (OSPL90).** Ningún audífono puede dar más que cierto nivel, por más entrada que reciba. La **OSPL90** es el nivel de salida con 90 dB SPL de entrada, un sonido lo bastante fuerte para llevar al audífono a su techo (→ H22). El techo importa porque el oído del paciente también tiene uno (el nivel que le molesta, → H5).

:::imagen ilustraciones/b4-audifono.svg ancho=100% Entrada y salida de un audífono, y lo que agrega el recorte. El lineal sigue la recta hasta su techo y ahí recorta; el de compresión baja la ganancia antes de llegar a él.
:::

En el dibujo, un audífono **lineal** con 30 dB de ganancia sigue la recta hasta su techo y desde ahí **recorta**: a 90 dB de entrada daría 120 dB, y entrega 115. Uno con **compresión** baja su ganancia cuando sube la entrada: con una razón de compresión de 2:1 y desde una entrada de 45 dB, cada 2 dB de entrada dan solo 1 dB de salida, y con 90 dB de entrada la ganancia es de 7,5 dB.

**Distorsión.** Al recortar, el audífono **agrega** frecuencias que no estaban: los armónicos del tono (el doble, el triple…). La distorsión armónica total (THD) es la potencia de esos armónicos respecto del tono, que se da en % o en dB: 10 % = −20 dB; 3 % = −30,5 dB; 1 % = −40 dB. En el ejemplo de la figura, un tono recortado en el 80 % de su pico tiene un 9 % (−21 dB), con el tercer armónico a 8 % y el quinto a 3,5 %. Para el usuario la distorsión es un sonido áspero, y suele venir de una pila baja o de un volumen demasiado alto (→ H22).

**Ruido interno.** Todo circuito produce un siseo propio. Para compararlo entre audífonos con ganancias distintas se da como si viniera **de afuera**, el **ruido equivalente de entrada**: *EIN* = nivel de ruido a la salida − ganancia. Con 60 dB SPL de ruido a la salida y 35 dB de ganancia, *EIN* = **25 dB SPL**, un siseo que se oye en una sala silenciosa (que ronda los 30 dB SPL).

**El acoplador de 2 cm³.** Para medir hay que "cargar" el audífono con una cavidad que reemplace al oído. Un volumen de aire cerrado se comporta como un resorte: a bajas frecuencias, la presión que un receptor genera en él es inversamente proporcional al volumen, *p* ∝ 1 / *V*. El acoplador de 2 cm³ es una convención repetible, no un modelo del oído de nadie (IEC 60118-0, 2022). Un oído más chico, como el de un niño, queda con menos volumen y **recibe más presión con el mismo audífono**: con 0,6 cm³ en vez de 2, la diferencia es 20 log (2 / 0,6) = **10,5 dB**. Esa es la idea de la **RECD** (diferencia oído real-acoplador): la presión que el audífono hace en un oído real no es la del acoplador, y la diferencia crece mientras más chico es el oído (→ H22).

:::ayuda-ancho Ejemplo resuelto: por qué silba
El silbido es una **realimentación**: el sonido que sale del molde vuelve al micrófono y se amplifica de nuevo. Se mantiene mientras la ganancia del lazo supere 0 dB. Un audífono con 40 dB de ganancia y un molde que atenúa 45 dB el camino de vuelta tiene una ganancia de lazo de 40 − 45 = **−5 dB**: estable. Si la ventilación se ensancha y la fuga pasa a atenuar solo 35 dB, la ganancia de lazo es **+5 dB** y el audífono silba. Hay dos formas de arreglarlo: sellar mejor o bajar la ganancia (→ H21, H22).
:::

## Ruido ocupacional

**La ponderación A.** El oído oye menos los graves que los agudos a niveles moderados, y la ponderación A reproduce eso con un filtro que resta nivel a los graves: −16,1 dB a 125 Hz, −8,6 a 250 Hz, −3,2 a 500 Hz, 0 a 1.000 Hz, +1,2 a 2.000 Hz, +1,0 a 4.000 Hz y −1,1 a 8.000 Hz (IEC 61672-1, 2013). Por eso el mismo ruido da un número menor en dB(A) que en dB lineales.

:::ayuda-ancho Ejemplo resuelto: de las bandas al dB(A)
Un ruido de máquina mide, en bandas de octava, 90, 88, 85, 82, 78, 74 y 70 dB SPL en 125, 250, 500, 1.000, 2.000, 4.000 y 8.000 Hz. Sin ponderar, la suma de energías es **93,4 dB**. Con la ponderación A las bandas pasan a 73,9, 79,4, 81,8, 82,0, 79,2, 75,0 y 68,9, y la suma es **87,4 dB(A)**. El ruido es más grave que agudo, y la cifra que cuenta para la exposición es la ponderada.
:::

**El nivel equivalente y la dosis.** Un ruido real sube y baja. Se resume con el **nivel equivalente** (Leq): el nivel de un ruido constante que, en el mismo tiempo, trae la **misma energía total**: Leq = 10 log ((1/*T*) × Σ *t*ᵢ × 10^(*L*ᵢ/10)). Normalizado a una jornada de 8 horas se llama LEX,8h (→ H23).

**La tasa de intercambio de 3 dB.** Como +3 dB es el doble de energía (10 log 2 = 3,01), la misma energía se logra duplicando el nivel en 3 dB y dividiendo el tiempo por dos: es "la misma energía, el mismo riesgo". Con 85 dB(A) como punto de partida para 8 horas, el tiempo permitido es *T* = 8 h / 2^((*L* − 85)/3).

Tabla: Tiempo permitido con la regla de 3 dB, con 85 dB(A) en 8 h

| Nivel | 85 | 88 | 91 | 94 | 97 | 100 |
|---|---|---|---|---|---|---|
| Tiempo | 8 h | 4 h | 2 h | 1 h | 30 min | 15 min |

Con una **regla de 5 dB** (la que mantiene OSHA, con 90 dB(A) en 8 h) el tiempo se divide por dos cada 5 dB: 95 dB(A) en 4 h, 100 en 2 h, 105 en 1 h. Un mismo día de trabajo da exposiciones distintas según la regla (→ H23).

:::ayuda-ancho Ejemplo resuelto: dosis y nivel equivalente son lo mismo
Un trabajador pasa 4 horas a 91 dB(A) y 4 horas a 82 dB(A). Con la tabla de 3 dB, el tiempo permitido a 91 dB(A) es 2 h y a 82 es 16 h. La **dosis** es la suma de las fracciones del tiempo permitido: 4/2 + 4/16 = 2 + 0,25 = **2,25**, un 225 %. Su nivel para 8 horas es 85 + 10 log 2,25 = **88,5 dB(A)**. Por el otro camino, el nivel equivalente de la jornada es 10 log (½ × 10^9,1 + ½ × 10^8,2) = **88,5 dB(A)**. Son la misma cuenta. Y el trabajador tiene más del doble de la dosis permitida, aunque la mitad del día sea "tranquila".
:::

**El criterio de 85 dB(A).** No es un umbral de todo o nada: es el punto donde el riesgo ya es bajo y todavía no nulo. En el análisis de NIOSH para 40 años de exposición, el exceso de riesgo de hipoacusia es de 8 % a 85 dB(A) y de 25 % a 90 (NIOSH, 1998; → H23). Lo que ordena las normas es cuánto aceptan de ese riesgo. Los **ruidos de impulso** (golpes) se controlan además por su nivel de pico, en dB(C). El daño esperable para una exposición y una edad se estima con la ISO 1999 (2013; → cap. 6, cap. 33).

## Flujo de aire en la nariz

### Presión, flujo y resistencia

El aire entra por la nariz porque el tórax baja la presión de la nasofaringe. Esa **diferencia de presión** (ΔP, en Pa) empuja un **flujo** (V̇, en cm³/s), y su cociente es la **resistencia** (*R* = ΔP / V̇), como en un circuito eléctrico. Se mide en Pa/(cm³/s); 1 Pa/(cm³/s) son unos 10,2 cmH₂O/L/s (→ H25). La nariz es la parte más resistente de la vía aérea del adulto (Ferris y cols., 1964). <!-- verificar: Ferris y cols. (1964) no tiene abstract en PubMed y el texto completo no es de acceso libre; no se pudo leer qué fracción de la resistencia total atribuyen a la nariz. -->

**Una pequeña reducción del radio cambia mucho.** En un tubo recto y liso con flujo ordenado (laminar), la resistencia es proporcional a **1 / r⁴** (ley de Poiseuille). Si el radio baja un 20 %, la resistencia sube ×2,4; si baja a la mitad, ×16. La nariz no es un tubo liso, pero es la razón de que unos milímetros de mucosa hinchada tapen y de que un vasoconstrictor que los reduzca pueda destapar (→ H25).

### Por qué la resistencia depende de la presión, y por qué 150 Pa

Con flujos bajos el aire va en capas y ΔP crece con V̇. Con flujos altos aparecen remolinos (**turbulencia**), y ΔP crece más rápido, con V̇². La relación es ΔP = *k*₁ V̇ + *k*₂ V̇², y por lo tanto *R* = *k*₁ + *k*₂ V̇: **la resistencia sube con el flujo**. Si un valor de resistencia se da sin la presión a que se leyó, no significa nada.

El número de Reynolds dice dónde cambia el régimen: *Re* = ρ *v* *d* / μ. Con aire (ρ = 1,2 kg/m³, μ = 1,8 × 10⁻⁵ Pa·s), una válvula nasal de 0,6 cm² de área (cerca de un diámetro de 0,87 cm) y un flujo de 250 cm³/s, la velocidad es 4,2 m/s y *Re* ≈ **2.400**; con 430 cm³/s, *Re* ≈ 4.200. Por sobre unos 2.000 un flujo en un tubo recto ya no es ordenado (cálculo de orden de magnitud: la válvula real no es un tubo redondo). Con los flujos de la rinomanometría, entonces, la turbulencia ya cuenta.

:::imagen ilustraciones/b4-nariz.svg ancho=100% Presión contra flujo en una fosa nasal, y la resistencia de un tubo según su radio. La curva se dobla porque, al subir el flujo, la turbulencia pesa más; y basta achicar un poco el radio para que la resistencia se dispare.
:::

:::ayuda-ancho Ejemplo resuelto: separar lo laminar de lo turbulento con los números de H25
La fosa derecha del paciente de H25 tiene una resistencia de 0,26 Pa/(cm³/s) a 75 Pa y de 0,35 a 150 Pa. Los flujos son 75 / 0,26 = 288 cm³/s y 150 / 0,35 = 429 cm³/s (26 L/min). Como *R* = *k*₁ + *k*₂ V̇, restando las dos resistencias: *k*₂ = (0,35 − 0,26) / (429 − 288) = 6,4 × 10⁻⁴, y *k*₁ = 0,26 − 6,4 × 10⁻⁴ × 288 = **0,075**. La parte laminar es 0,075 / 0,26 = **29 %** de la resistencia a 75 Pa y 0,075 / 0,35 = **21 %** a 150 Pa. A medida que la presión sube, el componente turbulento pesa más, y por eso la resistencia **sube** con la presión.
:::

Un valor de referencia solo sirve si todos lo leen en el mismo punto, y 150 Pa es un compromiso: suficientemente alto para tener señal (con presiones muy bajas el flujo recién se pone en marcha y el ruido pesa), y suficientemente bajo para que casi todos los pacientes lleguen, con 75 Pa como alternativa (Clement, 1984; Clement y Gordts, 2005; Wong y Eccles, 2014; Vogt y cols., 2016; → H25).

**Dos fosas en paralelo.** El aire elige dos caminos, y los **flujos se suman** a la misma presión, es decir, se suman las inversas de las resistencias: 1 / *R*total = 1 / *R*₁ + 1 / *R*₂. Con 0,35 y 0,29, 1 / 0,35 + 1 / 0,29 = 2,86 + 3,45 = 6,31 y *R*total = **0,16**. La resistencia total es siempre menor que la de la fosa más abierta, y si una fosa se tapa del todo (*R* → ∞), el total es la resistencia de la otra: 0,35.

### Reflexión acústica y área de sección transversal

Un sonido que viaja por un tubo "siente" su sección. La impedancia de una onda plana en un tubo es ρ*c* / *A* (con *A* el área): si el área cambia, la impedancia cambia, y **parte de la onda se refleja**. Para un cambio de área de *A*₁ a *A*₂, la presión reflejada, respecto de la que llega, es el **coeficiente de reflexión**:

*R* = (*A*₁ − *A*₂) / (*A*₁ + *A*₂)

Si el tubo se **estrecha** (*A*₂ < *A*₁), *R* es positivo: el eco vuelve del mismo signo. Si se **ensancha**, *R* es negativo: el eco vuelve invertido (→ H26). Y la distancia sale del tiempo: el eco que vuelve demora *t* = 2*x* / *c* en ir y volver desde una distancia *x*.

:::imagen ilustraciones/b4-reflexion.svg ancho=100% Ecos de un tubo con un estrechamiento, y cuánto del pulso llega hasta lo de atrás. El estrechamiento devuelve un eco del mismo signo y el ensanchamiento, uno invertido; el tiempo del eco dice a qué distancia está cada cambio.
:::

:::ayuda-ancho Ejemplo resuelto: de un eco a un área
El tubo del equipo mide 1,5 cm² y una válvula nasal lo reduce a 0,6 cm², a 1,3 cm de la entrada. *R* = (1,5 − 0,6) / (1,5 + 0,6) = **+0,43**: vuelve el 43 % de la presión y el 18 % de la energía (*R*² = 0,18), y llega a los 2 × 0,013 / 343 = **76 µs**. Al revés, el programa deduce el área desde el eco: *A*₂ = *A*₁ × (1 − *R*) / (1 + *R*) = 1,5 × 0,57 / 1,43 = **0,60 cm²**. Cuando la sección vuelve a ensancharse, a 3,1 cm, la parte que llega allí y vuelve es de signo contrario y llega a los 181 µs. Su tamaño es −0,35, y no −0,43, porque el pulso ya perdió algo al pasar por la válvula. El equipo hace esta cuenta, corrigiendo lo que se perdió antes, en cada instante, y dibuja la **curva área-distancia** (Hilberg y cols., 1989; Jackson y cols., 1977; Fredberg y cols., 1980).
:::

Los límites del método que explica H26 salen de estas mismas cuentas. Después de un estrechamiento marcado, la energía que pasa y vuelve de lo de atrás es (1 − *R*²)². Con un estrechamiento a 0,4 del área del tubo, vuelve el 67 % de la energía; con 0,1, el **11 %** (−9,6 dB); con 0,02, el **0,6 %** (−22 dB). Una válvula muy cerrada deja casi a oscuras lo que hay detrás. Como la distancia depende de *c*, y *c* de la temperatura (0,6 m/s por °C, 0,18 % por grado), una sala a otra temperatura corre las distancias: 10 °C de error son un 1,8 % (→ H26).

## Preguntas para practicar

:::pregunta Preguntas para practicar
1. Un tono de 2.000 Hz en aire a 20 °C: ¿cuánto vale su período y su longitud de onda? ¿Y a 8.000 Hz?
2. Dos tonos iguales de 1.000 Hz suenan juntos con un desfase de 120°. ¿Qué nivel resulta, en comparación con uno solo? ¿Y si el desfase es de 60°?
3. Una máquina de 85 dB y otra de 82 dB trabajan juntas. ¿Qué nivel dan? Si apagas la de 82, ¿cuánto baja el total?
4. En una sala, con la máquina encendida el sonómetro marca 58 dB y con la máquina apagada marca 52. ¿Cuánto es de la máquina sola?
5. Un audiómetro presenta 50 dB HL con TDH-39 a 250 Hz. ¿Cuántos dB SPL son? ¿Cuántos dB SL son si el umbral del paciente en esa frecuencia es 20 dB HL?
6. Un burst de 2.000 Hz de 5 ciclos, ¿cuánto dura? ¿Cómo cambia su ancho de banda comparado con uno de 500 Hz de 5 ciclos?
7. Con la sonda de 226 Hz, un oído da 1,4 mL en el extremo y 1,7 mL en el pico. ¿Cuál es la compliancia? ¿Cuántos mmho son 1,4 mL a 1.000 Hz?
8. Un PEAT parte con 3 µV de ruido por barrido. ¿Cuántos barridos hacen falta para tener un ruido residual de 0,1 µV? ¿Cuánto tiempo toman a 20 estímulos por segundo?
9. Una TEOAE tiene una reproducibilidad del 80 %. ¿Qué relación señal/ruido tiene cada memoria? ¿Y el promedio de las dos?
10. Un paciente de campo libre mueve la cabeza 10 cm hacia el parlante, que estaba a 1 m. ¿Cuánto cambia el nivel? ¿Y si el parlante estaba a 0,5 m? ¿Por qué se pide 1 m o más?
11. Un audífono con 35 dB de ganancia tiene un molde que atenúa 38 dB el camino de vuelta. ¿Qué pasa si la ventilación baja esa atenuación a 30 dB?
12. Un trabajador pasa 2 horas a 94 dB(A) y 6 horas a 82 dB(A). Con la regla de 3 dB, ¿qué dosis tiene? ¿Y qué LEX,8h?
13. Con la resistencia de la fosa derecha en 0,35 y la izquierda en 0,5 Pa/(cm³/s), ¿cuánto vale la resistencia total? ¿Y si el radio de la fosa izquierda baja un 10 %?
14. Un eco de +0,2 vuelve de un estrechamiento en un tubo de 1,5 cm². ¿Cuánta área tiene el estrechamiento? ¿A qué distancia está si el eco demora 117 µs?
:::

:::ayuda-ancho Respuestas
1. 0,5 ms y 17 cm; 0,125 ms y 4,3 cm.
2. Con 120° la suma vale lo mismo que uno solo (0 dB); con 60°, 2 cos 30° = 1,73 veces, es decir **+4,8 dB**.
3. 10 log (10^8,5 + 10^8,2) = **86,8 dB**; al apagar la de 82, bajan 1,8 dB (a 85).
4. 10 log (10^5,8 − 10^5,2) = **56,7 dB**.
5. 50 + 25,5 = **75,5 dB SPL**; 50 − 20 = **30 dB SL**.
6. 5 / 2.000 = **2,5 ms**; es 4 veces más corto y 4 veces más ancho (en proporción de la frecuencia, el ancho relativo es el mismo).
7. 1,7 − 1,4 = **0,3 mL**; 1,4 × 4,43 = **6,2 mmho**.
8. 3 / √*N* = 0,1 → *N* = 900; a 20 por segundo, **45 s**.
9. *r* / (1 − *r*) = 4 → **6 dB** por memoria y **9 dB** en el promedio completo.
10. A 1 m, 20 log (1 / 0,9) = **+0,9 dB**; a 0,5 m, 20 log (0,5 / 0,4) = **+1,9 dB**. A 1 m o más, un movimiento normal de la cabeza deja el nivel dentro de 1 dB.
11. Con 38 dB, el lazo es 35 − 38 = −3 dB: estable. Con 30 dB, es +5 dB: **silba**.
12. 2 / 1 h (94 dB(A) permite 1 h) + 6 / 16 = 2 + 0,375 = **2,375**, 237 %; LEX,8h = 85 + 10 log 2,375 = **88,8 dB(A)**.
13. 1 / (1 / 0,35 + 1 / 0,5) = **0,206**; con el radio de la izquierda en 0,9, su resistencia sube ×1,52 (1 / 0,9⁴), a 0,76, y el total pasa a 1 / (2,86 + 1,32) = **0,24**.
14. *A* = 1,5 × 0,8 / 1,2 = **1,0 cm²**; *x* = 343 × 117 µs / 2 = **2,0 cm**.
:::

## Referencias

### Normas

1. International Organization for Standardization. ISO 389-1:2017. Acoustics — Reference zero for the calibration of audiometric equipment — Part 1: Reference equivalent threshold sound pressure levels for pure tones and supra-aural earphones. Ginebra: ISO; 2017.
1. International Organization for Standardization. ISO 389-2:1994. Acoustics — Reference zero for the calibration of audiometric equipment — Part 2: Reference equivalent threshold sound pressure levels for pure tones and insert earphones. Ginebra: ISO; 1994.
1. International Organization for Standardization. ISO 389-4:1994. Acoustics — Reference zero for the calibration of audiometric equipment — Part 4: Reference levels for narrow-band masking noise. Ginebra: ISO; 1994.
1. International Organization for Standardization. ISO 389-6:2007. Acoustics — Reference zero for the calibration of audiometric equipment — Part 6: Reference threshold of hearing for test signals of short duration. Ginebra: ISO; 2007.
1. International Organization for Standardization. ISO 389-7:2019. Acoustics — Reference zero for the calibration of audiometric equipment — Part 7: Reference threshold of hearing under free-field and diffuse-field listening conditions. Ginebra: ISO; 2019.
1. International Organization for Standardization. ISO 8253-1:2010. Acoustics — Audiometric test methods — Part 1: Pure-tone air and bone conduction audiometry. Ginebra: ISO; 2010.
1. International Organization for Standardization. ISO 8253-2:2009. Acoustics — Audiometric test methods — Part 2: Sound field audiometry with pure-tone and narrow-band test signals. Ginebra: ISO; 2009.
1. International Organization for Standardization. ISO 226:2023. Acoustics — Normal equal-loudness-level contours. 3.ª ed. Ginebra: ISO; 2023.
1. International Organization for Standardization. ISO 1999:2013. Acoustics — Estimation of noise-induced hearing loss. Ginebra: ISO; 2013.
1. International Organization for Standardization. ISO 4869-1:2018. Acoustics — Hearing protectors — Part 1: Subjective method for the measurement of sound attenuation. Ginebra: ISO; 2018.
1. International Electrotechnical Commission. IEC 60645-1:2017. Electroacoustics — Audiometric equipment — Part 1: Equipment for pure-tone and speech audiometry. Ginebra: IEC; 2017.
1. International Electrotechnical Commission. IEC 60645-3:2020. Electroacoustics — Audiometric equipment — Part 3: Test signals of short duration. 3.ª ed. Ginebra: IEC; 2020.
1. International Electrotechnical Commission. IEC 61672-1:2013. Electroacoustics — Sound level meters — Part 1: Specifications. Ginebra: IEC; 2013.
1. International Electrotechnical Commission. IEC 60118-0:2022. Electroacoustics — Hearing aids — Part 0: Measurement of the performance characteristics of hearing aids. Ginebra: IEC; 2022.
1. Acoustical Society of America. ASA/ANSI S3.6-2025. Specification for audiometers. Melville (NY): ASA; 2025.
1. Acoustical Society of America. ANSI/ASA S3.1-1999 (R2018). Maximum permissible ambient noise levels for audiometric test rooms. Melville (NY): ASA; 2018.
1. British Society of Audiology. Recommended procedure: pure-tone air-conduction and bone-conduction threshold audiometry with and without masking (OD104-32). BSA; 2018.
1. National Institute for Occupational Safety and Health. Criteria for a recommended standard: occupational noise exposure, revised criteria 1998. Cincinnati (OH): DHHS (NIOSH) Publication No. 98-126; 1998. Disponible en: https://stacks.cdc.gov/view/cdc/6376

### Libros

1. Gelfand SA. Hearing: an introduction to psychological and physiological acoustics. 6.ª ed. Boca Raton: CRC Press; 2017. doi:10.1201/9781315154718
1. Plack CJ. The sense of hearing. 3.ª ed. Londres: Routledge; 2018. doi:10.4324/9781315208145
1. Moore BCJ. An introduction to the psychology of hearing. 6.ª ed. Leiden: Brill; 2013. ISBN 978-90-04-25242-4
1. Rossing TD, editor. Springer handbook of acoustics. Nueva York: Springer; 2007. doi:10.1007/978-0-387-30425-0
1. Picton TW. Human auditory evoked potentials. San Diego: Plural Publishing; 2010 (el editor la fecha en 2011).
1. Hall JW 3rd. New handbook of auditory evoked responses. Boston: Pearson; 2007.
1. Dillon H. Hearing aids. 2.ª ed. Sídney: Boomerang Press; Nueva York: Thieme; 2012. ISBN 978-1-60406-810-8
1. Cole B. A summary of ANSI S3.22 tests [Internet]. Etymonic Design / Audioscan; 2006. Disponible en: https://docs.audioscan.com/library/misc/ANSI-S3_22-Tests-Summary.pdf

### Sonido, psicoacústica y calibración

1. Fletcher H, Munson WA. Loudness, its definition, measurement and calculation. J Acoust Soc Am. 1933;5(2):82-108. doi:10.1121/1.1915637
1. Fletcher H. Auditory patterns. Rev Mod Phys. 1940;12(1):47-65. doi:10.1103/RevModPhys.12.47
1. Hawkins JE, Stevens SS. The masking of pure tones and of speech by white noise. J Acoust Soc Am. 1950;22(1):6-13. doi:10.1121/1.1906581
1. Zwicker E. Subdivision of the audible frequency range into critical bands (Frequenzgruppen). J Acoust Soc Am. 1961;33(2):248. doi:10.1121/1.1908630
1. Zwicker E, Terhardt E. Analytical expressions for critical-band rate and critical bandwidth as a function of frequency. J Acoust Soc Am. 1980;68(5):1523-5. doi:10.1121/1.385079
1. Glasberg BR, Moore BCJ. Derivation of auditory filter shapes from notched-noise data. Hear Res. 1990;47(1-2):103-38. doi:10.1016/0378-5955(90)90170-T
1. Stevens SS. The measurement of loudness. J Acoust Soc Am. 1955;27(5):815-29. doi:10.1121/1.1908048
1. Sek A, Moore BCJ. Frequency discrimination as a function of frequency, measured in several ways. J Acoust Soc Am. 1995;97(4):2479-86. doi:10.1121/1.411968
1. Shaw EA. Transformation of sound pressure level from the free field to the eardrum in the horizontal plane. J Acoust Soc Am. 1974;56(6):1848-61. doi:10.1121/1.1903522
1. Berger EH, Killion MC. Comparison of the noise attenuation of three audiometric earphones, with additional data on masking near threshold. J Acoust Soc Am. 1989;86(4):1392-403. doi:10.1121/1.398699
1. Munro KJ, Agnew N. A comparison of inter-aural attenuation with the Etymotic ER-3A insert earphone and the Telephonics TDH-39 supra-aural earphone. Br J Audiol. 1999;33(4):259-62. doi:10.3109/03005369909090106
1. Stenfelt S. Transcranial attenuation of bone-conducted sound when stimulation is at the mastoid and at the bone conduction hearing aid position. Otol Neurotol. 2012;33(2):105-14. doi:10.1097/MAO.0b013e31823e28ab
1. Dau T, Wegner O, Mellert V, Kollmeier B. Auditory brainstem responses with optimized chirp signals compensating basilar-membrane dispersion. J Acoust Soc Am. 2000;107(3):1530-40. doi:10.1121/1.428438
1. Poulsen T, Legarth SV. Reference hearing threshold levels for short duration signals. Int J Audiol. 2008;47(10):665-74. doi:10.1080/14992020802203330

### Impedancia y admitancia

1. British Society of Audiology. Recommended procedure: tympanometry and acoustic reflex thresholds [Internet]. BSA; 2024 Feb (enmiendas menores feb 2025 y mar 2026) [citado 2026 oct 15]. Disponible en: https://www.thebsa.org.uk/wp-content/uploads/2026/03/BSA-Recommended-Procedure-Tympanometry-Acoustic-Reflex-Thresholds-March-2026-minor-revision.pdf
1. Margolis RH, Goycoolea HG. Multifrequency tympanometry in normal adults. Ear Hear. 1993;14(6):408-13. doi:10.1097/00003446-199312000-00006
1. Holte L, Margolis RH, Cavanaugh RM Jr. Developmental changes in multifrequency tympanograms. Audiology. 1991;30(1):1-24. doi:10.3109/00206099109072866
1. Kei J, Allison-Levick J, Dockray J, Harrys R, Kirkegard C, Wong J, et al. High-frequency (1000 Hz) tympanometry in normal neonates. J Am Acad Audiol. 2003;14(1):20-8. doi:10.3766/jaaa.14.1.4
1. Alaerts J, Luts H, Wouters J. Evaluation of middle ear function in young children: clinical guidelines for the use of 226- and 1,000-Hz tympanometry. Otol Neurotol. 2007;28(6):727-32. doi:10.1097/mao.0b013e3180dca1e5
1. Chasin M. Back to basics: a primer on equivalent volume, impedance, and couplers for hearing aids. Hear Rev. 2015;22(12).
1. Ogut F, Serbetcioglu B, Kirazli T, Kirkim G, Gode S. Results of multiple-frequency tympanometry measures in normal and otosclerotic middle ears. Int J Audiol. 2008;47(10):615-20. doi:10.1080/14992020802178656

### Señal y ruido

1. Elberling C, Don M. Quality estimation of averaged auditory brainstem responses. Scand Audiol. 1984;13(3):187-97. doi:10.3109/01050398409043059
1. Don M, Elberling C. Evaluating residual background noise in human auditory brain-stem responses. J Acoust Soc Am. 1994;96(5 Pt 1):2746-57. doi:10.1121/1.411281
1. Picton TW, Hillyard SA, Krausz HI, Galambos R. Human auditory evoked potentials. I: Evaluation of components. Electroencephalogr Clin Neurophysiol. 1974;36(2):179-90. doi:10.1016/0013-4694(74)90155-2
1. Hall JW. Auditory brain stem response spectral content in comatose head-injured patients. Ear Hear. 1986;7(6):383-9. doi:10.1097/00003446-198612000-00007
1. Sininger YS. Filtering and spectral characteristics of averaged auditory brain-stem response and background noise in infants. J Acoust Soc Am. 1995;98(4):2048-55. doi:10.1121/1.413321

### Nariz

1. Clement PA, Gordts F; Standardisation Committee on Objective Assessment of the Nasal Airway, IRS, and ERS. Consensus report on acoustic rhinometry and rhinomanometry. Rhinology. 2005;43:169-79. PMID: 16218509.
1. Clement PA. Committee report on standardization of rhinomanometry. Rhinology. 1984;22:151-5. PMID: 6505516.
1. Wong EH, Eccles R. Comparison of classic and 4-phase rhinomanometry methods, is there any difference? Rhinology. 2014;52:360-5. doi:10.4193/Rhino13.187
1. Vogt K, Wernecke KD, Behrbohm H, Gubisch W, Argale M. Four-phase rhinomanometry: a multicentric retrospective analysis of 36,563 clinical measurements. Eur Arch Otorhinolaryngol. 2016;273:1185-98. doi:10.1007/s00405-015-3723-5
1. Ferris BG Jr, Mead J, Opie LH. Partitioning of respiratory flow resistance in man. J Appl Physiol. 1964;19:653-8. doi:10.1152/jappl.1964.19.4.653
1. Hilberg O, Jackson AC, Swift DL, Pedersen OF. Acoustic rhinometry: evaluation of nasal cavity geometry by acoustic reflection. J Appl Physiol. 1989;66(1):295-303. doi:10.1152/jappl.1989.66.1.295
1. Jackson AC, Butler JP, Millet EJ, Hoppin FG Jr, Dawson SV. Airway geometry by analysis of acoustic pulse response measurements. J Appl Physiol. 1977;43(3):523-36. doi:10.1152/jappl.1977.43.3.523
1. Fredberg JJ, Wohl ME, Glass GM, Dorkin HL. Airway area by acoustic reflections measured at the mouth. J Appl Physiol. 1980;48(5):749-58. doi:10.1152/jappl.1980.48.5.749
1. Keck T, Leiacker R, Riechelmann H, Rettinger G. Temperature profile in the nasal cavity. Laryngoscope. 2000;110(4):651-4. doi:10.1097/00005537-200004000-00021
