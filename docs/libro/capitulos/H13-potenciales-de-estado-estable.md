# H13. Potenciales de estado estable

:::objetivos En esta herramienta
- Explicar por qué un tono que "late" (modulado) produce una respuesta cerebral a la misma frecuencia con que late, y por qué eso permite estudiar muchas frecuencias a la vez.
- Distinguir las respuestas de 80 a 100 Hz (las del paciente dormido, de tronco) de las de 40 Hz (las del adulto despierto, más corticales).
- Entender cómo el equipo decide, con estadística y sin que nadie mire ondas, que hay una respuesta.
- Preparar al paciente, montar los electrodos y conducir un examen de estado estable de principio a fin.
- Pasar del umbral del examen (dB nHL) a una estimación del audiograma (dB eHL), sabiendo de dónde salen las correcciones y cuándo no se pueden usar.
- Reconocer los límites del examen: el oído normal, la neuropatía auditiva y los artefactos.
:::

Los **potenciales evocados auditivos de estado estable** (PEAee; en inglés *auditory steady-state responses*, **ASSR**) son una forma de estimar el umbral de cada frecuencia de cada oído sin pedirle nada al paciente. Se parece al ABR por tono breve (→ H10) en lo que responde y en cómo se pone al paciente, pero **el estímulo, la forma de leer la respuesta y el modo de decidir cuándo hay una respuesta son distintos**. Esta herramienta se detiene en esas tres diferencias, porque de ellas salen todas las ventajas y todos los cuidados del examen.

## Para qué sirve

El ASSR responde una pregunta: **¿cuál es el umbral de este oído en cada frecuencia?** Se pide cuando la audiometría no se puede hacer con confianza (BSA, 2023):

- **Lactantes y niños pequeños** que ya tienen un ABR con morfología normal y de quienes se necesita un audiograma estimado, sobre todo para **adaptar audífonos**. Para esta tarea los umbrales por frecuencia son los que importan: un lactante con una pérdida de agudos necesita saber cuánta ganancia pedirle a cada banda (→ H20).
- **Personas que no pueden o no quieren colaborar**: discapacidad cognitiva, pacientes bajo sedación o anestesia, o sospecha de una pérdida no orgánica (→ H3 y cap. 19).
- **Candidatos a implante coclear**, como alternativa al ABR para estimar cuánta audición residual queda.

Dos ideas separan el ASSR de una audiometría:

- **No mide cuánto oye la persona**: mide si el cerebro produce una respuesta que sigue al estímulo. Entre la una y la otra hay una diferencia que se corrige en promedio, pero que en cada paciente no es la misma.
- **No es una herramienta para encontrar causas.** No dice si la pérdida es conductiva o coclear salvo que se repita por vía ósea, y no muestra ondas: de la integridad del nervio y del tronco no dice nada.

## Fundamento

### Un tono que late

Un tono puro de 1.000 Hz es continuo y parejo: el nervio descarga en forma sostenida y no hay nada que el electrodo pueda separar del ruido. Si se hace **latir** el tono, subiendo y bajando su volumen a un ritmo regular de, por ejemplo, 90 veces por segundo, algo cambia. A ese tono se lo llama **portador** y a su ritmo de latido, **frecuencia de modulación**. En el ASSR el portador es la frecuencia que se quiere estudiar (500, 1.000, 2.000 y 4.000 Hz) y se modula casi siempre al **100 % en amplitud** (el volumen va de cero a su máximo). A veces se modula también la frecuencia: esa modulación **mixta** (amplitud y frecuencia a la vez) agranda levemente la respuesta (BSA, 2023).

Las neuronas auditivas descargan con más probabilidad en cada subida de la envolvente, de modo que, sumadas, producen una oscilación **al ritmo del latido** y no al del portador. Un electrodo en el cuero cabelludo no puede captar un tono de 1.000 Hz, pero sí esa oscilación lenta de la descarga de miles de neuronas. La respuesta que se registra es entonces una señal **exactamente a la frecuencia de modulación** (Picton y cols., 2003; BSA, 2023). Y como ese tono modulado tiene su energía concentrada en una banda angosta alrededor del portador, la respuesta nace de una región acotada de la cóclea: es **específica por frecuencia**.

:::imagen ilustraciones/h13-modulacion-espectro.svg ancho=96% De un tono modulado a un pico en el espectro. A: el portador sube y baja con una envolvente regular (línea punteada); la respuesta del cerebro sigue la envolvente. B: en el espectro del EEG de un oído hay un pico justo en cada frecuencia de modulación, sobre un piso de ruido que es parejo. Cada pico pertenece a un portador distinto.
:::

### Dos familias: 80 a 100 Hz y 40 Hz

Según el ritmo de modulación, la respuesta nace en lugares distintos (Picton y cols., 2003; BSA, 2023):

- **Alrededor de 80 a 100 Hz** (en los equipos, "90 Hz"). La respuesta viene sobre todo del **tronco**, como el ABR. Está presente desde el nacimiento y **casi no cambia con el sueño**, la sedación ni la anestesia. Es la que se usa en lactantes y en cualquier paciente dormido. Su costo es que es **más chica**.
- **Alrededor de 40 Hz**. Es similar a la respuesta de latencia media: más grande, pero **depende del estado de alerta** y **no se parece a la del adulto hasta la adolescencia**, aunque desde los 5 años ya se puede registrar (BSA, 2023). Es adecuada en adultos y niños mayores (más de unos 5 años) **despiertos**, y no sirve en recién nacidos ni se debe usar en quien duerme.

Por eso las pantallas de los equipos ofrecen protocolos distintos para el niño, el adulto dormido y el adulto despierto: no cambia el examen, cambia la familia de respuesta que se está buscando.

### Muchos estímulos al mismo tiempo

Como cada estímulo late a una frecuencia de modulación **distinta**, el equipo puede presentar a la vez, en un mismo oído, cuatro portadores (500, 1.000, 2.000 y 4.000 Hz) cada uno con su ritmo propio, y a los dos oídos, ocho estímulos en total. En el espectro del EEG cada uno aparece como un pico en su propio lugar, sin mezclarse con los demás (Lins y cols., 1996; BSA, 2023). Es la ventaja más grande del examen: **todo el audiograma de los dos oídos en una sola sentada**.

Hay condiciones. Si los portadores están a menos de media octava, uno achica la respuesta del otro; con **una octava o más de separación** cuatro estímulos simultáneos no pierden amplitud, y a intensidad alta las interacciones aumentan (John y cols., 1998). Por eso los equipos no dejan que los niveles de las frecuencias de un mismo oído difieran en más de unos 20 dB, y por eso a intensidades altas el examen pasa a una frecuencia por vez (BSA, 2023).

### Quién decide que hay respuesta: la estadística

En el ABR alguien mira la curva y marca una onda. En el ASSR **no hay curva que mirar**: el equipo analiza el EEG **en frecuencia** y hace una prueba estadística en cada frecuencia de modulación. La idea es simple:

- El ruido del EEG (músculo, actividad del cerebro) tiene energía en todas las frecuencias, de manera **aleatoria**: su fase cambia de un tramo a otro.
- La respuesta al estímulo, en cambio, ocurre **exactamente a la frecuencia de modulación** y con una **fase estable** de un tramo a otro, porque está amarrada al estímulo.

El equipo pregunta entonces, por ejemplo, si la energía en la frecuencia de modulación es mayor que la de las frecuencias vecinas (una **prueba F**) o si la fase se repite de un tramo a otro más de lo que el azar permite (**coherencia de fase**). Algunos equipos combinan las dos. El resultado se expresa como un **nivel de confianza**: con 95 % el equipo se equivoca y dice "hay respuesta" donde no la hay una de cada 20 veces; con 99 %, una de cada 100, a cambio de tardar más (BSA, 2023). El examen sigue promediando hasta que una de las dos cosas ocurre: la respuesta cruza el criterio o el ruido residual baja tanto que, si hubiera una respuesta, ya se vería.

Esto tiene una consecuencia que hay que recordar siempre: **cualquier cosa que se repita con el estímulo, con la misma fase, se cuenta como respuesta**, sea o no auditiva. Un artefacto del transductor o una respuesta anormal pasan el criterio igual que una respuesta verdadera (BSA, 2023). El ASSR no tiene el "ojo" del ABR para dudar de lo que ve.

:::sabias ¿Sabías que?
La amplitud de la respuesta crece con la intensidad y con la profundidad de la modulación, y su **fase** se atrasa a medida que el estímulo es más débil o más grave (Picton y cols., 2003). Esa dependencia regular con el nivel es parte de por qué el examen funciona como estimador de umbral: cerca del umbral la respuesta es pequeña, pero sigue estando donde debe estar.
:::

## Antes de empezar

### Equipo

- **Equipo de potenciales evocados con módulo de estado estable**: estimulador, preamplificador y un programa que analiza el EEG en frecuencia. Los equipos difieren bastante entre sí (estímulos, detección y estrategia de prueba), y por eso hay que seguir lo que trae el fabricante (BSA, 2023).
- **Electrodos** desechables, **gel abrasivo**, **gel conductor**, cinta adhesiva, alcohol y algodón.
- **Fonos de inserción**, rojo para el oído derecho y azul para el izquierdo. El **vibrador óseo** se usa para la vía ósea (ver "Límites").
- **Otoscopio**, camilla y manta; luz baja.

### Conoce el examen: la pantalla de un ASSR

LabSim no simula este examen (→ "En LabSim"). Estas son las partes de la pantalla de un equipo real, que son prácticamente las mismas en todos:

:::ayuda-ancho Qué muestra la pantalla de un ASSR
| Parte | Qué es | Cómo se lee |
|---|---|---|
| **Protocolo** | Niño (90 Hz), adulto dormido (90 Hz) o adulto despierto | Cada uno trae sus tasas de modulación y su criterio de parada. No se cambia a mano |
| **Cuadrícula** | Dos oídos y las cuatro frecuencias (500, 1.000, 2.000 y 4.000 Hz) | Cada casilla es un estímulo, con su propio nivel |
| **Código de colores** | Verde: respuesta detectada. Negro: nivel en curso. Rojo: sin respuesta confiable | En el ejemplo de la práctica, verde a 65 y 45 dB, negro a 35 y rojo a 25. El rojo **no es** "sordo": es "aún no se encontró" |
| **Estado de cada nivel** | Tiempo promediado, confianza estadística y ruido residual | Es el equivalente del FSP y del ruido residual del ABR (→ H10) |
| **Resultado** | Un audiograma con los umbrales estimados | Ya viene corregido a dB eHL por el fabricante; hay que saber con qué tabla |
:::

### Preparar al paciente

**El sueño es la mitad del examen.** La respuesta de 90 Hz es chica y el músculo tenso la entierra, así que se cita al paciente **cansado**, para que entre en sueño fisiológico:

- **Lactantes y niños pequeños**: como en el ABR (→ H10), que lleguen con sueño, sin dormirse en el camino, y alimentados justo antes del examen.
- **Adultos**: llegar cansados (dormir poco la noche anterior) y **sin maquillaje ni cremas** en la cara, que impiden que el electrodo se adhiera.

El examen dura alrededor de **una hora**. Antes de poner un electrodo:

1. **Otoscopía** (→ H1). Si el paciente usa lentes, se los saca. Un tapón de cerumen que ocluye se extrae antes de empezar (→ H1, lavado de oídos): un tapón suma una pérdida conductiva que no es del paciente.
2. **Anamnesis de electrofisiología** (→ H1 y H10): antecedentes del parto en lactantes, fármacos, y sobre todo si hay un ABR previo.
3. **Explicar el examen** al paciente o a quien lo acompaña: se va a registrar la respuesta de las ondas cerebrales a un sonido, para estimar cuánto oye. Se van a limpiar zonas de la cara y de la cabeza con alcohol y gel abrasivo, y eso puede dejar una leve irritación que se pasa. Después se colocan los electrodos y los fonos, y lo esperable es que se duerma.

### Montaje de electrodos

La preparación de la piel es lo que más pesa en la calidad del registro:

1. **Limpia con alcohol** cada punto y luego **exfolia con gel abrasivo**, con movimientos continuos y en un solo sentido, cuidando de no lastimar la piel.
2. **Pon los electrodos** (parches desechables, con cinta si hace falta):
    - **activo (positivo)** en el **vértex** (Cz) o en la línea del cabello (blanco);
    - **referencias (negativas)** en cada **mastoides**: rojo en la derecha y azul en la izquierda;
    - **tierra** (negro) en la frente, sobre la ceja izquierda; el sitio exacto importa poco.
3. **Mastoides lejos del pelo**: así, al retirar los parches no se tracciona el cabello.
4. **Revisa las impedancias**: idealmente **bajo 3 kΩ**. Si están altas, se repite la limpieza o se usa gel conductor.
5. **Pon los fonos de inserción** (rojo a la derecha, azul a la izquierda) y mira el **EEG**: debe verse con **amplitudes bajas** y poca actividad. Un EEG con mucho músculo no va a mejorar promediando.

:::comentario Lo que dicen las normas
**Impedancias.** La guía de la BSA pide impedancias **bajo 5 kΩ** y parecidas entre sí, con una diferencia **máxima de 2 kΩ** entre pares de electrodos, porque el artefacto eléctrico es proporcional a esa diferencia; en una sala bien aislada puede tolerarse algo más si son parecidas (BSA, 2023). Aquí se mantiene el límite de 3 kΩ como meta; lo que no cambia es que importa más que sean **bajas y parecidas** que cualquier cifra suelta. **Montaje.** La BSA ubica el positivo en el vértex o, en lactantes, en la frente alta cercana a Cz (evitando la fontanela), la referencia en la mastoides o el lóbulo del mismo lado y el común en el lado contrario o en la frente a más de 4 cm.
:::

## Paso a paso

### 1. Elige el protocolo

Se selecciona el módulo ASSR y el protocolo que corresponde al paciente: **niño**, **adulto dormido** o **adulto despierto**, los tres con modulaciones cercanas a 90 Hz en el protocolo base de este libro. Esa elección fija la familia de respuesta que se va a buscar (ver "Fundamento"). Los parámetros del estímulo vienen fijos por el fabricante y no se modifican; se cambia solo el protocolo.

:::comentario Lo que dicen las normas
En el **adulto despierto** la BSA recomienda la familia de **40 Hz**, que es la más grande en vigilia, y reserva los 90 Hz para quien duerme, sea sueño natural, sedación o anestesia general (BSA, 2023). Con 90 Hz en un adulto despierto el examen es posible, pero la respuesta es chica y el músculo tenso la tapa: por eso aquí se cita cansado a quien se va a registrar con ese protocolo. En 40 Hz, además, la guía advierte que no hay evidencia suficiente para fijar un criterio de "respuesta ausente", así que debe interpretarse junto con el resto del cuadro clínico.
:::

### 2. Mira el EEG antes de empezar

Con los electrodos y los fonos puestos, mira el EEG unos segundos. Tiene que estar **tranquilo**. Si el paciente aún no duerme, **espera**: iniciar con un EEG sucio solo alarga el examen. Hay una razón estadística: el equipo descarta los tramos que pasan de un límite de amplitud (rechazo de artefacto), y con un paciente inquieto descarta tantos que el promedio no avanza.

### 3. Inicia: dos oídos, cuatro frecuencias a la vez

Al iniciar, el equipo presenta los estímulos de ambos oídos al mismo tiempo, cada uno con su frecuencia de modulación, y empieza a probar niveles. Cada casilla de la pantalla (oído y frecuencia) sigue su propio camino: sube cuando no hay respuesta y baja cuando la hay, **hasta encerrar el umbral**.

Lo que sí decide la persona que conduce el examen es la **estrategia**: dónde empezar, cuándo repetir un nivel dudoso, cuándo dejar una frecuencia para después. En un recién nacido el nivel inicial se elige a partir del ABR previo, y se sigue un esquema simple (BSA, 2023):

- Sin respuesta en el nivel inicial: **subir de 20 en 20 dB** hasta que aparezca.
- Con respuesta: **bajar de 10 o 20 dB** hasta que desaparezca y precisar con pasos de **5 o 10 dB**.
- Pasados **80 dB nHL**, seguir **solo de a 5 dB** y con cuidado: ahí se pasa a una frecuencia por vez, porque la respuesta de varias frecuencias a la vez se achica con niveles altos y el artefacto es más probable.

### 4. Lee los colores y no apures el rojo

El **verde** es una respuesta detectada; el **negro**, lo que está en curso; el **rojo**, la ausencia de una respuesta confiable. Para dar un umbral no basta con ver el verde: hace falta además **saber dónde dejó de haber respuesta**. Un rojo que se alcanzó porque se acabó el tiempo, con el ruido todavía alto, **no es ausencia de respuesta**, es un resultado **no concluyente**; y un umbral construido sobre un no concluyente no es un umbral.

:::comentario Lo que dicen las normas
La BSA define tres resultados por nivel: **respuesta clara** (detectada con 95 o 99 % de confianza), **respuesta ausente** (no hay respuesta *y* el ruido residual es lo bastante bajo como para que una respuesta del tamaño esperable se hubiera visto) y **no concluyente** (no se cumple ninguna de las dos antes de que termine el tiempo). El **umbral** es el nivel más bajo con una respuesta clara replicada al 95 % (o única al 99 %), con otra respuesta clara 5 o 10 dB más arriba y una respuesta ausente 5 o 10 dB más abajo. Si no se consiguió la respuesta ausente, se informa con el signo **≤** (por ejemplo "≤ 45 dB nHL"); si no hubo respuesta clara, con **>** (BSA, 2023). Los equipos de la pantalla del protocolo resumen todo esto con sus tres colores; saber qué hay detrás de cada uno es lo que permite dudar de él.
:::

### 5. Una respuesta muy rápida o muy alta se repite

Si el equipo detecta respuesta en menos de un minuto, es más probable que sea un falso positivo, porque al principio el ruido residual es alto y fluctúa. Si el nivel importa para el resultado, **repítelo**: una respuesta verdadera aparece de nuevo igual de rápido. También hay que **repetir** cuando hay una respuesta solo en los niveles cercanos al máximo del estimulador: ahí puede ser un artefacto (ver "Errores frecuentes").

### 6. Cuando el examen termina

El equipo entrega un **audiograma estimado** con un umbral por oído y por frecuencia. Antes de darlo por bueno:

- **Mira cuáles casillas son no concluyentes** y que no entren como umbral.
- **Compara con el resto**: el ABR (→ H10), las emisiones y la timpanometría. Si el ASSR y el ABR se contradicen de manera importante, se confía en el ABR para el diagnóstico (BSA, 2023).
- Anota con qué **tabla de corrección** se pasó de nHL a eHL (ver "Cómo se informa").

Al terminar se **despierta** al paciente, si corresponde, y se retiran los electrodos.

:::ayuda Ayuda memoria
- Paciente **cansado y dormido** (90 Hz); sin maquillaje; impedancias **bajas y parecidas**.
- **ABR antes que ASSR**; si el ABR es ausente o anormal, no se hace ASSR.
- Protocolo: niño, adulto dormido o adulto despierto.
- EEG tranquilo **antes** de iniciar.
- Hasta 80 dB nHL varias frecuencias a la vez; sobre eso, de a una y de a 5 dB.
- Rojo ≠ sordo: distinguir **ausente** de **no concluyente**.
- Respuesta solo cerca del máximo: **control con estímulo bloqueado**.
- Informar en dB nHL y en dB eHL, con la tabla de corrección usada.
:::

## Cómo se informa

### De dB nHL a dB eHL: la corrección

El equipo presenta los estímulos en **dB nHL** y el umbral que encuentra queda **por encima** del umbral conductual del mismo oído. Para estimar el audiograma se le **resta una corrección** y el resultado se escribe en **dB eHL** (*estimated hearing level*). Las correcciones salen de comparar umbrales de ASSR con audiometrías en los mismos sujetos, y **no son iguales para todos**:

- Son **mayores en graves** y **en oídos normales o con pérdidas leves**, y **menores y menos variables cuanto mayor es la pérdida** (BSA, 2023, que cita a Lee y cols., 2016).
- Dependen del **equipo**, del **estímulo** y de la **edad** del paciente. En el recién nacido hay que descontar además el efecto de un conducto pequeño (que sube el nivel real del fono hasta 10 a 20 dB) y de un cráneo liviano con el vibrador, lo que según la BSA puede representar errores de hasta 30 dB (BSA, 2023).

Por eso la regla es: **usar la tabla del fabricante del equipo**, si está respaldada por estudios publicados (BSA, 2023). Cuando no existe, la BSA propone una tabla provisional para recién nacidos:

Tabla: Corrección provisional de la BSA para recién nacidos (hasta 12 semanas de edad corregida), en dB; se suma al umbral en dB nHL

| Transductor | 500 Hz | 1.000 Hz | 2.000 Hz | 4.000 Hz |
|---|---|---|---|---|
| Fonos de inserción | −20 | −20 | −15 | −15 |
| Fonos supraaurales | −25 | −25 | −20 | −25 |
| Vibrador óseo | no se usa | −5 | −15 | −15 |

Valen **solo para umbrales sobre 30 dB eHL** y son provisionales: la propia guía dice que no se han verificado y que el informe debe señalarlo (BSA, 2023). Con esa tabla, un umbral de 70 dB nHL en 500 Hz con fonos de inserción en un recién nacido queda en **50 dB eHL** (figura siguiente).

:::imagen ilustraciones/h13-correccion.svg ancho=96% De los umbrales del examen al audiograma estimado. Los círculos son los umbrales encontrados (en dB nHL); a cada uno se le resta la corrección de su frecuencia y los cuadrados son el audiograma estimado (en dB eHL).
:::

### Cuánto separan al ASSR de la audiometría

Las diferencias que se han medido entre el umbral del ASSR y el umbral conductual dependen de a quién se midió y con qué equipo. Para tener una idea del orden de magnitud:

Tabla: Diferencia promedio entre el umbral del ASSR y el umbral conductual, en dB (el ASSR queda por encima), según el grupo estudiado

| Grupo | 500 Hz | 1.000 Hz | 2.000 Hz | 4.000 Hz | Fuente |
|---|---|---|---|---|---|
| Adultos con audición normal | 14 | 12 | 11 | 13 | Lins y cols., 1996 |
| Adultos con hipoacusia sensorioneural | 14 | 8 | 10 | 3 | Herdman y Stapells, 2003 |
| Adultos, normales e hipoacúsicos juntos (modulación mixta) | 14 | 5 | 5 | 9 | Dimitrijevic y cols., 2002 |
| Lactantes menores de 2 años, resumen de 7 estudios | 9 | 7 | 6 | 7 | Huang y cols., 2025 |

Las cifras son promedios, y la dispersión individual es grande (desviaciones estándar de unos 8 a 13 dB en los estudios de adultos). Los lactantes del resumen muestran una variabilidad entre estudios muy alta, y los autores piden estudios más grandes (Huang y cols., 2025). Lo que sí se repite en la literatura:

- **Audición normal o casi normal**: el umbral conductual del lactante resulta típicamente **10 a 15 dB mejor** de lo que predice su ASSR (Rance y Rickards, 2002). En lactantes normoyentes de un estudio, la mitad tenía respuesta a 36, 30, 24 y 15 dB HL en 500, 1.000, 2.000 y 4.000 Hz, y el 90 % la tenía a 49, 45, 36 y 32 dB HL (Van Maanen y Stapells, 2009).
- **Pérdida moderada a profunda**: la relación en lactantes es **similar a la de adultos y niños mayores** (Rance y Rickards, 2002). En niños que no tenían ABR con click a nivel máximo, cuando había respuesta de estado estable el umbral conductual caía típicamente **dentro de 5 dB** del umbral del ASSR (Rance y cols., 1998).
- **Correlación**: con lactantes con audición normal e hipoacusia sensorioneural, la correlación entre ASSR y audiometría es mayor a 0,95 en cada frecuencia (Rance y cols., 2005).

No existe una tabla universal de "cuánto restar por grado de pérdida" que valga para cualquier equipo; lo que existe es la tabla de cada fabricante y la tendencia de arriba. Un informe honesto dice **qué tabla se usó**.

### Qué se informa

- **Datos del examen**: protocolo (90 o 40 Hz), estímulos, transductor, estado del paciente (dormido, sedado, despierto) y la calidad del registro (ruido residual, EEG, impedancias).
- **Umbral por oído y frecuencia en dB nHL**, con el signo **=** (umbral definido), **≤** (no se llegó a una respuesta ausente) o **>** (no hubo respuesta clara al máximo).
- **Estimación en dB eHL**, con la tabla de corrección y su fuente.
- **Concordancia con el ABR** y con lo demás.
- **Limitaciones**: un ASSR **no descarta neuropatía auditiva** y, en el lactante, la estimación se debe tomar con cautela.

> **Potenciales evocados auditivos de estado estable.** Protocolo de 90 Hz, estimulación simultánea de cuatro frecuencias por oído, fonos de inserción. Paciente en sueño fisiológico, EEG tranquilo, impedancias bajo 3 kΩ. Se realizó un ABR previo con morfología normal.
>
> **OD**: umbrales en dB nHL de 70 (500 Hz), 65 (1.000), 60 (2.000) y 60 (4.000), con respuesta ausente 10 dB más abajo en cada frecuencia. Con la corrección del equipo, el audiograma estimado queda en 50, 45, 45 y 45 dB eHL.
>
> **OI**: respuestas claras a 35 dB nHL en las cuatro frecuencias; en 500 y 1.000 Hz no se alcanzó respuesta ausente (≤ 35 dB nHL). Estimación: dentro de lo normal.
>
> **Conclusión**: el examen sugiere una hipoacusia moderada en el OD, de configuración plana, y audición normal en el OI para las frecuencias estudiadas. La estimación es provisional y debe confirmarse con la audiometría conductual cuando la edad lo permita.

:::comentario Lo que dicen las normas
El informe de ejemplo es de un recién nacido, y es el único contexto en que la BSA entrega una tabla de corrección; para otras edades remite al fabricante. En Inglaterra, desde 2021, los resultados se ingresan al sistema nacional **ya como dB eHL escritos por el clínico**, no corregidos por el programa, justamente porque cada fabricante corrige distinto (BSA, 2023).
:::

## Límites y comparación con el ABR

### Lo que el ASSR no hace bien

- **El oído normal.** La mayor dispersión está en la audición normal y en las pérdidas leves. En una pérdida coclear hay reclutamiento: un cambio pequeño de nivel lleva el sonido de inaudible a fuerte, y la respuesta aparece cerca del umbral; en el oído normal, sin reclutamiento, la respuesta crece de a poco y el umbral del examen se dispersa más (BSA, 2023). En lactantes normoyentes, la mitad tiene respuesta a 15 a 36 dB HL según la frecuencia y el 90 % recién a 32 a 49 dB HL, y por eso se toman como "normales" las respuestas a 50, 45, 40 y 40 dB HL en 500, 1.000, 2.000 y 4.000 Hz (Van Maanen y Stapells, 2009). Un ASSR **puede confirmar que el umbral está dentro de lo normal**, pero **distingue mal** un oído normal de una pérdida leve. <!-- Pasada de fundamentos 2026-10-18: decía "porque el sistema se recluta: pasar de inaudible a fuerte requiere cambios pequeños de nivel" (la BSA atribuye la menor dispersión de las pérdidas a su reclutamiento, no al oído normal) y "el 90 % ya tiene respuesta a 32 a 49 dB HL ... así que el ASSR de un oído normal no baja de ahí" (la mediana está en 15 a 36 dB HL; Van Maanen y Stapells, 2009). También decía "no distingue un oído normal de una pérdida de 20 a 30 dB", cifra sin fuente. -->
- **La neuropatía auditiva.** El ASSR **no puede diagnosticarla** y en ella **no predice el umbral conductual**: en 19 niños con pérdida de tipo neuropatía, los umbrales del ASSR no reflejaron el audiograma conductual (Rance y cols., 2005). Hay incluso casos en que el ASSR muestra respuesta a niveles bajos mientras el ABR está ausente, y se piensa que lo que se detecta es actividad previa al nervio (el potencial de suma) y no una respuesta neural (Biagio de Jager y cols., 2026). Una respuesta presente no basta para decir que hay audición.
- **Las intensidades altas.** La respuesta de varias frecuencias a la vez cae sobre unos 80 dB nHL y los artefactos aumentan; a más de 100 dB nHL por vía aérea las respuestas pueden ser vestibulares o del estímulo (BSA, 2023).
- **El lactante muy pequeño.** Las respuestas maduran: los umbrales mejoran unos 5 dB en las primeras semanas, y la BSA propone hacer el ASSR entre **2 semanas y 3 meses** de edad corregida y usar estimaciones conservadoras si se hace antes (BSA, 2023).

:::comentario Lo que dicen las normas
La BSA es más estricta que lo que cualquier manual de equipo dice: **primero un ABR**. El ABR permite mirar la morfología y descartar una neuropatía auditiva *antes* de apoyarse en un examen que, por la forma en que detecta, **no puede verla**. **Si el ABR está ausente o es anormal, no se hace ASSR**, porque el resultado "no sería útil e incluso podría ser engañoso", y si hay una diferencia importante entre ABR y ASSR **manda el ABR** para el diagnóstico (BSA, 2023). Coincide con la regla del tamizaje, en que el primer examen electrofisiológico del lactante es un ABR (JCIH, 2019).
:::

### Frente al ABR por tono breve

El ASSR no reemplaza al ABR por tono breve o por *chirp* de banda estrecha (→ H10, "Umbral por frecuencia"): se complementan.

Tabla: ABR por tono breve y ASSR frente a frente

| | ABR por tono breve (→ H10) | ASSR |
|---|---|---|
| **Estímulo** | Tono breve o *chirp* de banda estrecha, uno por vez | Tono (o *chirp*) modulado, hasta 8 a la vez |
| **Qué se lee** | Ondas en el tiempo; la onda V | El pico espectral en la frecuencia de modulación |
| **Quién decide** | El examinador, con ayuda del FSP | Una prueba estadística, objetiva |
| **Información de nervio y tronco** | Sí: latencias, interpicos | No |
| **Neuropatía auditiva** | Se puede sospechar (microfónica, ausencia de ondas) | No se puede diagnosticar y engaña |
| **Artefacto de estímulo** | Se ve en la curva | No se ve: puede contar como respuesta |
| **Tiempo para 4 frecuencias y 2 oídos** | Más largo | Más corto con equipos de última generación: unos 20 min contra unos 32 min en un estudio con lactantes (Sininger y cols., 2018) |
| **Dependencia del sueño** | No | 90 Hz no; 40 Hz sí |
| **Diferencia con el umbral conductual** | Corrección conocida en cada protocolo | En lactantes, alrededor de 6 a 11 dB más alto que el ABR por tono en un sistema temprano (Van Maanen y Stapells, 2010); con detección de última generación, hasta 14 dB más bajo que el ABR (Sininger y cols., 2018) |

En la práctica, el ABR responde primero (¿hay una vía sana?, ¿qué umbral con click o con tono?) y el ASSR completa rápido el audiograma de los dos oídos cuando el ABR salió normal en morfología (BSA, 2023).

## Errores frecuentes

- **Empezar sin ABR en un lactante.** Puede dejar pasar una neuropatía auditiva que el ASSR no ve.
- **Leer el rojo como "no oye".** Rojo es "sin respuesta confiable hasta ahora"; distinguir *ausente* de *no concluyente* es la mitad del examen.
- **Dar un umbral sin la respuesta ausente debajo.** Se informa con ≤, no con "=".
- **Impedancias altas o desparejas.** El artefacto de red es proporcional a la diferencia de impedancias, y en el ASSR no se ve: solo produce falsas detecciones o descartes (BSA, 2023).
- **Paciente despierto en un protocolo de 90 Hz.** La respuesta es chica y el músculo la tapa; los tramos se descartan y el examen no avanza.
- **Una respuesta solo a nivel muy alto, creída.** Sin control con el estímulo bloqueado, un artefacto del transductor puede contar como respuesta, sobre todo con el vibrador óseo (Small y Stapells, 2004; BSA, 2023).
- **Subir el rechazo de artefacto para que avance.** Entra más ruido, el examen se alarga y el umbral pierde precisión (BSA, 2023).
- **Informar solo dB nHL, o solo dB eHL, sin decir con qué corrección.**
- **Usar una tabla de otro equipo o de otra edad.**
- **Creerle a una respuesta de lactante normal como si fuera de adulto.** Los umbrales del lactante son más altos que los del adulto aunque oiga normal.

:::ojo Ojo clínico
Un ASSR con respuestas a niveles bajos en las cuatro frecuencias **no basta** para decir que un lactante oye normal si el ABR no tuvo morfología normal o si faltan las emisiones. Y un ASSR **sin** respuesta no significa que no haya audición residual útil: en niños sin ABR con click a nivel máximo, los modulados pueden mostrar que hay resto auditivo (Rance y cols., 1998). Antes de informar, pregúntate si todo **calza**: ABR, emisiones, timpanometría y conducta.
:::

### Control con estímulo bloqueado

Para saber si una respuesta es del oído o del equipo, se repite el registro al **mismo nivel** pero **sin que el sonido llegue al oído**: se tapa la salida del fono (con masilla adhesiva) o se pinza el tubo del fono de inserción, o, con el vibrador, se lo separa unos milímetros de la piel. Si la respuesta persiste, es artefacto (BSA, 2023). Es la misma maniobra de **pinzar el tubo** del ABR (→ H10).

## En LabSim

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

:::pregunta Preguntas para practicar
1. ¿Por qué un tono de 1.000 Hz modulado a 90 Hz produce una respuesta cerebral a 90 Hz y no a 1.000?
2. Una adolescente de 14 años, despierta y colaboradora, se registra con un protocolo de 90 Hz y el equipo no avanza. ¿Qué dos cosas puedes cambiar sin cambiar el examen? ¿Qué familia de respuesta es más grande en vigilia?
3. En un recién nacido, el umbral del ASSR con fonos de inserción es de 65 dB nHL en 500 Hz y de 60 en 4.000 Hz. Usa la tabla provisional de la BSA y escribe su audiograma estimado. ¿Qué nota debe llevar el informe?
4. En 1.000 Hz el equipo muestra verde a 40 dB, a 30 dB rojo, y el registro de 30 dB se cortó a los 3 minutos con ruido alto. ¿Cuál es el umbral? ¿Con qué signo se informa?
5. Un lactante tiene un ABR plano con emisiones presentes, pero el ASSR muestra respuesta a 45 dB nHL en las cuatro frecuencias. ¿Qué concluyes? ¿Qué examen manda?
6. El ASSR de un lactante muestra respuestas hasta 40 dB HL en todas las frecuencias. ¿Es suficiente para decir que oye normal? ¿Qué más pedirías?
7. Un ASSR detecta respuesta a 100 dB nHL por vía aérea y a 40 dB por vía ósea en 500 Hz. ¿Qué dos sospechas tienes antes de creerlo?
:::

## Referencias

### Técnica

1. British Society of Audiology. Practice guidance: auditory steady state response (ASSR) testing (OD104-115, v3). BSA; 2023. Disponible en: https://www.thebsa.org.uk/wp-content/uploads/2023/10/OD104-115-Practice-Guidance-for-ASSR-Testing-1.pdf
1. Picton TW, John MS, Dimitrijevic A, Purcell D. Human auditory steady-state responses. Int J Audiol. 2003;42(4):177-219. doi:10.3109/14992020309101316
1. John MS, Lins OG, Boucher BL, Picton TW. Multiple auditory steady-state responses (MASTER): stimulus and recording parameters. Audiology. 1998;37(2):59-82. doi:10.3109/00206099809072962
1. Small SA, Stapells DR. Artifactual responses when recording auditory steady-state responses. Ear Hear. 2004;25(6):611-23. doi:10.1097/00003446-200412000-00009
1. Joint Committee on Infant Hearing. Year 2019 position statement: principles and guidelines for early hearing detection and intervention programs. J Early Hear Detect Interv. 2019;4(2):1-44. doi:10.15142/fptk-b748

### Umbral estimado y correcciones

1. Lins OG, Picton TW, Boucher BL, Durieux-Smith A, Champagne SC, Moran LM, et al. Frequency-specific audiometry using steady-state responses. Ear Hear. 1996;17(2):81-96. doi:10.1097/00003446-199604000-00001
1. Dimitrijevic A, John MS, Van Roon P, Purcell DW, Adamonis J, Ostroff J, et al. Estimating the audiogram using multiple auditory steady-state responses. J Am Acad Audiol. 2002;13(4):205-24. doi:10.1055/s-0040-1715964
1. Herdman AT, Stapells DR. Auditory steady-state response thresholds of adults with sensorineural hearing impairments. Int J Audiol. 2003;42(5):237-48. doi:10.3109/14992020309078343
1. Rance G, Dowell RC, Rickards FW, Beer DE, Clark GM. Steady-state evoked potential and behavioral hearing thresholds in a group of children with absent click-evoked auditory brain stem response. Ear Hear. 1998;19(1):48-61. doi:10.1097/00003446-199802000-00003
1. Rance G, Rickards F. Prediction of hearing threshold in infants using auditory steady-state evoked potentials. J Am Acad Audiol. 2002;13(5):236-45. doi:10.1055/s-0040-1715967
1. Rance G, Roper R, Symons L, Moody LJ, Poulis C, Dourlay M, et al. Hearing threshold estimation in infants using auditory steady-state responses. J Am Acad Audiol. 2005;16(5):291-300. doi:10.3766/jaaa.16.5.4
1. Van Maanen A, Stapells DR. Normal multiple auditory steady-state response thresholds to air-conducted stimuli in infants. J Am Acad Audiol. 2009;20(3):196-207. doi:10.3766/jaaa.20.3.6
1. Van Maanen A, Stapells DR. Multiple-ASSR thresholds in infants and young children with hearing loss. J Am Acad Audiol. 2010;21(8):535-45. doi:10.3766/jaaa.21.8.5
1. Huang X, Kluk K, Perugia E. The relationship between auditory steady-state response and behavioural audiometry in hearing estimation for infants: a meta-analysis. Syst Rev. 2025;15(1):2. doi:10.1186/s13643-025-03003-x
1. Sininger YS, Hunter LL, Hayes D, Roush PA, Uhler KM. Evaluation of speed and accuracy of next-generation auditory steady state response and auditory brainstem response audiometry in children with normal hearing and hearing loss. Ear Hear. 2018;39(6):1207-23. doi:10.1097/AUD.0000000000000580

### Neuropatía auditiva

1. Biagio de Jager L, Lightfoot G, Michel F, Zanin J, Rance G. Auditory steady-state responses to low-level stimuli in children with auditory neuropathy: case series and theoretical considerations. Int J Audiol. 2026:1-11. doi:10.1080/14992027.2026.2665402

<!-- Pasada de fundamentos 2026-10-18: se cotejó en la BSA (2023, apéndice B) que da 12 dB (DE 14) en lactantes normales (Casey y Small, 2014) y 7 dB (DE 11) con hipoacusia sensorioneural (Aimoni y cols., 2018); no se usan en el texto visible, así que no se citan. La prueba F y la coherencia de fase están en la BSA (2023, §7.1). -->
<!-- Protocolo ORL 2019: "Paciente debe presentarse en cansado": errata por "presentarse cansado". "Impedancia idealmente inferior a 3Komh": errata por kΩ; se dejó 3 kΩ como meta del libro y la norma (BSA: 5 kΩ y diferencia de 2 kΩ) va en "Lo que dicen las normas". "Adultos despiertos, 90 Hz": se mantuvo; la BSA usa 40 Hz en vigilia (comentario en el paso 1). El protocolo no menciona ABR previo ni exclusión de neuropatía: se agregó con la BSA. -->
<!-- Informe de ejemplo: cifras inventadas para ilustrar; la corrección del OD (−20/−20/−15/−15) es la tabla provisional de la BSA para recién nacidos con fonos de inserción. -->
