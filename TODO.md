# TODO

## VEMP en el cliente: probar en la app (pendiente)

El pase por `src/vemp/` está hecho: el módulo lee el shape nuevo
(`cases.data['VEMP'][lado]['subtipos'][subtipo]`, con compatibilidad hacia
los casos viejos), dibuja la morfología bifásica, ya no extrapola la
amplitud por encima de 80 dB y el examen se puede completar (un oído por
vez, promediación en vivo, picos marcables, tabla y lat-int poblados,
razón de asimetría en el informe).

Lo que se agregó y no estaba: **la maniobra del paciente**. La amplitud del
VEMP escala con el EMG tónico del músculo registrador (ECM en el cVEMP,
mirada superior en el oVEMP, mordida en el mVEMP): con el paciente relajado
no hay respuesta. El combo arranca SIEMPRE en la posición sin contracción
--no es un default correcto precargado-- y el monitor de EMG muestra el
nivel y la banda válida. Ver `VEMP_generator_v1.MANIOBRAS` y `VempEmg.py`.

Pendiente:
- [ ] **Correr el módulo con un caso creado desde el editor nuevo.** Nada
      de esto se probó en la app: acá no hay PySide6/pyqtgraph/scipy, así
      que lo único ejecutado es el generador (tests/test_vemp_generator.py,
      con filtros pasa-todo). Toda la UI --captura, cursores, marcas,
      apilado, escalas, export a JPEG-- está sin ejecutar una sola vez.
- [ ] Confirmar el PDF con un informe real: `ReportPdfBuilder` ya imprime
      maniobra/EMG/pico-pico por curva y el bloque de asimetría, pero eso
      se leyó en el código, no se generó un PDF.
- [ ] Rangos normativos en la tabla (como `normative_limits` en el ABR):
      hoy la tabla muestra lo medido sin referencia. El JSON normativo no
      trae desviación estándar por pico, así que primero hay que decidir de
      dónde sale la tolerancia (la banda de la lat-int usa un valor
      declarado, `TOLERANCIA_LAT_MS = 1.5`, y lo dice).
- [ ] Umbral del VEMP como dato del informe: hoy el alumno lo deduce de la
      serie pero no hay dónde anotarlo.
- [ ] `impedance` está fija en 3.0 kOhm (no hay diálogo de parámetros
      avanzados como en el ABR). Si se agrega, entra por
      `control_setting['impedance']`, que el generador ya lee.

## Otoscopia: derivación + aprobación docente + fase por alumno

Ficha Otoscopia (case_create.php, antes de Audiometría) construida como N
fases (sin selector de modo aparte: 1 sola fase ya ES "única"), cada una
con imagen OD + imagen OI + texto libre describiendo qué pasó desde la
fase anterior — vacío en fase 1. Dato guardado en `cases.data.Otoscopia`.

Dinámica pedagógica real (no implementada aún): el paciente NO es un estado
compartido igual para todos los alumnos — cada estudiante avanza su propia
fase de otoscopia según sus propias derivaciones aprobadas por el docente.
Ej: alumno atiende, hace otoscopia (fase 1), encuentra tapón de cerumen,
deriva a lavado; si el docente aprueba esa derivación, la próxima vez que
ESE alumno atienda a ese paciente ve la fase 2 (con el texto "se realizó un
lavado"); si no derivó o no fue aprobada, sigue viendo la fase 1. Si un
alumno solo llega hasta fase 2 aprobada y no hay fase 3, siempre ve la 2.

Hoy: todo alumno ve fase 1 fija (hardcodeado), no hay derivación ni revisión.

Pendiente:
- [ ] Derivación del estudiante: campo/acción al cerrar atención
      (`attendance_action.php`, action `atendido`) para redactar la
      derivación, separado de la nota general de atención.
- [ ] Bandeja docente de revisión: UI nueva donde el profesor ve
      derivaciones pendientes por alumno-paciente y aprueba/rechaza.
- [ ] Tabla de progreso por alumno-paciente: qué fase de otoscopia tiene
      aprobada CADA estudiante para CADA paciente (no existe hoy — nueva
      tabla, ej. `patient_student_progress` o similar).
- [ ] Motor de selección de fase en el lado alumno: qué fase se muestra al
      abrir la ficha del paciente según el progreso aprobado de ESE
      alumno, clamp a la última fase disponible si no hay más.
- [x] Vista de otoscopia en la app de escritorio: botón "Otoscopia" en
      Box Audiología (a la izquierda de Acumetría, ver Layout::APPS en
      labsim_backend/src/Layout.php)
      y src/audiometria/Otoscopia.py) -- muestra la imagen OD/OI lado a
      lado ("Otoscopio sin batería" si no hay imagen subida). Hoy siempre
      trae la fase 1 (índice 0, `FASE_FIJA` en Otoscopia.py) para todos los
      alumnos, ni el texto libre de cada fase se muestra todavía.
- [ ] Aplicar el motor de selección de fase (punto anterior) también acá:
      hoy `FASE_FIJA = 0` está hardcodeado en src/audiometria/Otoscopia.py.
      Mostrar además el texto libre de la fase actual (hoy no se pide ni
      se muestra en la app, solo las imágenes).
- [ ] Notificación al alumno al aprobar/rechazar su derivación (posible
      tipo nuevo en `inbox_messages`, mismo patrón que OirsEvaluator).
- [ ] Historial/auditoría de derivaciones: quién derivó, cuándo, quién
      aprobó/rechazó.
- [ ] Reglas de reintento: qué pasa si el docente rechaza (¿queda en la
      misma fase?, ¿puede el alumno volver a derivar la misma cita?).

## Voces de respuesta logoaudiometria (ListWords.py)

Bug: paciente "no responde" en logoaudiometria. Causa real: `create_word_response`
(lib/h_audio.py) arma el nombre de archivo como
`audio/LP_palacios_r_{sex}{number}_{name}.mp3`, usando `gender`/`id` reales
de la ficha del paciente. Solo existen grabadas las voces `feme1` y `feme2`
(`resources/audio/LP_palacios_r_feme{1,2}_*.mp3`) — no hay ninguna voz `male`
grabada, y ningun otro numero de id tiene voz asociada. Si el archivo no
existe, Qt/ffmpeg falla en silencio ("No existe el fichero o el directorio")
y no suena nada, dando la impresion de que el paciente no responde.

Fix temporal aplicado en `ListWords.la_super` (src/ListWords.py): se fuerza
siempre `gender="feme"` e `id=1`, ignorando el genero/id real del paciente,
para que siempre use una voz que sí existe.

Pendiente:
- [ ] Grabar voces `male1`/`male2` (set completo de palabras + `none1/2/3`).
- [ ] Decidir que representa realmente el numero de voz (¿variante de
      locutor, no el id de la ficha?) y mapear correctamente en vez de
      hardcodear a 1.
- [ ] Quitar el forzado temporal en `ListWords.la_super` una vez resuelto.

## Dilema de enmascaramiento: el motor lo ordena y lo acepta igual

`ResponseAudiometry._masking_calc` (src/audiometria/response.py) devuelve el
rango de ruido útil como `sorted([mkg_min, mkg_max])`. Cuando el mínimo
efectivo supera al máximo tolerable, ese `sorted` **invierte el rango en vez
de declararlo imposible**, y `_resolve_masked_threshold` lo trata como una
meseta válida: el paciente simulado entrega su umbral real y el alumno cree
haber enmascarado bien.

Clínicamente eso es el **dilema de enmascaramiento**: no existe un nivel de
ruido que enmascare al oído contrario sin cruzar de vuelta y tapar al oído
que se está midiendo. Es lo que pasa con gaps grandes bilaterales
(otoesclerosis bilateral, otitis media crónica bilateral): el caso NO se
puede resolver con auriculares supraaurales, y la salida real es el
inserto (que sube la atenuación interaural a ~70-85 dB) o informar el
umbral como no enmascarable.

Ejemplo reproducible: aéreo 60 / óseo 15 en ambos oídos, 1000 Hz.
```
mín = UAE - AI - UONE + UANE = 60 - 40 - 15 + 60 = 65 dB
máx = UOE + AI               = 15 + 40           = 55 dB
```
El rango sale `[65, 55]`, `sorted` lo entrega como `55 .. 65` y con
cualquier ruido en esa franja el motor responde el umbral real.

Hoy: el panel de depuración (DebugMkg) lo marca explícitamente
(`<<< DILEMA: la fórmula no deja rango válido (el motor lo invierte y lo
acepta igual)`), pero el motor sigue comportándose como antes. Se dejó así
a propósito: cambiarlo altera la respuesta de **todos** los casos con gap
grande bilateral que ya estén armados.

Pendiente (decisión pedagógica antes que técnica):
- [ ] Decidir qué debe pasar cuando no hay rango válido. Opciones:
      (a) dejarlo como está y que el panel sea el único que lo delate;
      (b) que el paciente deje de responder de forma consistente en toda la
          franja, para que el alumno vea que el umbral no se puede cerrar;
      (c) modelar el sobre-enmascaramiento como corrimiento gradual del
          umbral (como quedó la logoaudiometría en `CalculateLogo.get`), y
          que el dilema emerja solo sin necesidad de un caso especial.
- [ ] Si se elige (b) o (c): sacar el `sorted` de `_masking_calc` y revisar
      `_resolve_masked_threshold`, `response_aerea_w_msk`,
      `response_osea_w_msk` y el tone decay (`_decay_*`), que consultan el
      mismo rango.
- [ ] Revisar los casos ya armados con gap bilateral >= 40 dB antes de
      cambiar nada: hoy responden y pasarían a no responder.
- [ ] Considerar el transductor de inserto como salida del dilema (hoy la
      atenuación interaural es fija por frecuencia en `self.attenuations`,
      sin distinguir supraaural de inserto).

## Efecto oclusivo: decidido contra el gap del oído ocluido (hecho)

`ResponseAudiometry.oclusive_efect` tenía dos errores acumulados y se
corrigieron los dos (2026-09-10):

1. **Se evaluaba en el oído equivocado.** `_masking_calc` vía ósea llamaba
   `oclusive_efect(frecuency, o_e)`, el oído *estudiado*. En el montaje real
   el vibrador va en la mastoides del oído estudiado y el auricular con el
   ruido va en el **oído no estudiado**: ese es el que queda ocluido. Ahora
   se llama con `o_n`.
2. **La condición estaba invertida.** Devolvía el efecto cuando había gap
   (`diff > 5`) y 0 cuando el oído era normal. Es al revés: el efecto
   oclusivo existe sólo con oído medio sano — la oclusión atrapa la energía
   que normalmente escapa por el conducto. Un oído con patología de
   transmisión ya se comporta como ocluido y no gana nada más, que es
   exactamente por qué el Bing es negativo cuando hay gap.

En pérdidas **unilaterales** los dos errores se cancelaban entre sí (por eso
no saltaba a la vista): estudiando el oído con gap, el código daba efecto
porque *ese* oído tenía gap, y da la casualidad de que el contralateral sano
sí lo tenía que aportar. En bilaterales no se cancelan:

| caso                        | antes | ahora | correcto |
|-----------------------------|-------|-------|----------|
| ambos oídos normales        | 0     | EO    | EO       |
| gap bilateral               | EO    | 0     | 0        |
| gap sólo en el estudiado    | EO    | EO    | EO       |
| gap sólo en el no estudiado | 0     | 0     | 0        |

**Por qué se descartaron las otras dos opciones** (la decisión se tomó sin
consultar porque el montaje la define):

- *Evaluarlo en el oído estudiado*: sólo tendría sentido si el paciente
  llevara auricular también sobre el oído del vibrador. No es el montaje de
  la ósea enmascarada, donde ese oído queda destapado justamente para no
  ocluirlo.
- *Aplicarlo en los dos lados* (mínimo por el ocluido + mejora del umbral
  óseo del estudiado por su propia oclusión): modela un fenómeno que existe,
  pero **movería el umbral óseo real del caso**, no sólo el rango de ruido.
  El óseo lo define el docente en la ficha; que el motor lo baje 10-15 dB en
  graves por cuenta propia rompe los casos ya armados y hace que el
  audiograma no dé lo que el docente cargó. Si alguna vez se quiere, tiene
  que ser explícito en la ficha, no implícito en el motor.

### Valores por frecuencia: se dejan los de la docente (pendiente preguntar)

La tabla es `list_values = [15, 15, 15, 10, 0, 0, 0, 0, 0]` en
`ResponseAudiometry.oclusive_efect`, o sea 125/250/500 Hz: 15 dB;
1000 Hz: 10 dB; 2000 Hz y arriba: 0.

**Se mantiene tal cual porque es lo que enseña la docente.** No se toca sin
hablarlo con ella. Se probó cambiarla y se revirtió (2026-09-10).

Lo que llamó la atención y hay que preguntarle: los tres graves están
**planos** en 15 dB. Las tablas publicadas para auricular supraaural suelen
crecer hacia los graves, porque lo que la oclusión atrapa es la energía de
baja frecuencia que con el conducto abierto se disipa hacia afuera:

| Hz   | la docente | Studebaker | Yacullo |
|------|------------|------------|---------|
| 250  | 15         | 20         | 30      |
| 500  | 15         | 15         | 20      |
| 1000 | 10         | 10         | 10      |
| 2000+| 0          | 0          | 0       |

En 1000 Hz y en agudos las tres coinciden; la diferencia está sólo en
250-500 Hz.

Pendiente:
- [ ] **Preguntarle a la docente de dónde sale la tabla.** Puede ser una
      fuente distinta (hay bibliografía que promedia, y algunos protocolos
      usan un valor único para toda la zona grave), un criterio propio de
      la cátedra, o una simplificación deliberada para la enseñanza. Hasta
      entonces manda lo que ella enseña: el alumno tiene que poder resolver
      el caso con lo que le enseñaron.
- [ ] Anotar la fuente en el código cuando se sepa, para que nadie la
      vuelva a "corregir" (el comentario en `oclusive_efect` avisa que el
      cambio está pendiente de esa respuesta).
- [ ] Insertos: reducen mucho el efecto oclusivo (queda casi en 0 con
      inserción profunda). Hoy no hay transductor de inserto modelado --es
      el mismo pendiente que aparece en la nota del dilema-- así que la
      tabla asume supraaural siempre.
- [ ] `oclusive_efect` devuelve 0 para índices de alta frecuencia (>= 9) en
      vez de romper, pero la vía ósea no se administra ahí de todos modos.

Cubierto por `tests/test_masking_tonal.py::EfectoOclusivoTest` y
`::TablaOclusivaTest`.

## Parámetros de audiometría configurables por curso (futuro)

Disparado por la tabla del efecto oclusivo: distintos docentes enseñan
valores distintos para los mismos parámetros, y hoy están **hardcodeados en
el cliente**. Si un curso enseña otra cifra, el alumno resuelve bien el caso
según lo que le enseñaron y el simulador le dice que no. Fijar el valor "de
manual" tampoco sirve: la bibliografía tampoco se pone de acuerdo.

La infraestructura ya existe y no hay que inventarla: `app_config` en el
backend (`labsim_backend/src/AppConfig.php`, con override por curso resuelto
del lado servidor) sincronizado al cliente en `core/app_config_store.py`,
que ya sirve `normative_data.abr` y `normative_data.vemp` con la key
genérica `normative_data.<examen>`. Cuando no hay fila, `get()` devuelve el
default y quien llama sigue con su tabla local: el mismo patrón sirve acá.

Candidatos, todos hoy literales en el código:

| parámetro | dónde | valor actual | por qué varía |
|---|---|---|---|
| Efecto oclusivo por frecuencia | `response.py:oclusive_efect` | `[15,15,15,10,0,...]` | los de la docente; Studebaker y Yacullo dan otros (ver sección anterior) |
| Atenuación interaural aérea | `response.py:__init__` (`self.attenuations`) | `[35,40,40,40,40,45,45,50,50]` | hay cátedras que enseñan 40 dB plano para supraaural |
| Atenuación interaural ósea | `response.py:_masking_calc` | `0` | algunos textos usan 0-10 dB según frecuencia |
| Atenuación interaural del habla | `logoaudiometry.py` (`logo_attenuation`) | `45` | suele darse 45-50 dB |
| Coeficiente de enmascaramiento (CE) | `response.py:_masking_calc` (`ce`) | `0` | depende del tipo de ruido y del margen de seguridad que enseñe la cátedra (ver sección siguiente) |
| Promedio tonal (PTA) | `response.py:calc_sdt`, `logoaudiometry.py:sdt_calcule` | mejores 2 de 500/1000/2000 | hay cátedras con promedio de 3 y con promedio de 4 (agregando 4000) |
| Techo de transmisión | `DebugMkg.py:GAP_MAX_DB` y `CaseProfile.php` | `60` | ya está duplicado en cliente y backend |
| Gap significativo | `DebugMkg.py:GAP_SIGNIFICATIVO` | `15` | criterio de cuándo un gap es patológico (10 o 15) |

Pendiente:
- [ ] Definir una key, en la línea de las que ya existen: algo como
      `audiometry_params` (un solo blob con todo) o
      `audiometry_params.<parámetro>` si conviene editarlos por separado.
      Un solo blob es más simple para la UI y para el default local.
- [ ] Default local que siga mandando cuando no hay fila: hoy cada valor
      vive en el módulo que lo usa, así que conviene juntarlos en un solo
      lugar del cliente (un `audiometria/params.py`) y que ese lugar
      consulte `app_config_store` con el literal actual como default. Sin
      eso, cablear la config obliga a tocar cada archivo.
- [ ] UI de edición en `courses.php`, igual que se hizo con la normativa del
      ABR. Ojo: son parámetros que cambian cómo responde el paciente, no
      sólo cómo se informa -- conviene mostrar en el editor qué implica cada
      uno (mecánica, no clínica) y no dejar que se guarde algo imposible
      (AI negativa, CE enorme).
- [ ] Decidir qué pasa con los casos ya armados cuando un curso cambia un
      parámetro: los umbrales de la ficha no se tocan, pero el rango de
      enmascaramiento válido sí se mueve. Probablemente no haga falta
      migrar nada, pero hay que confirmarlo antes de habilitar la edición.
- [ ] `GAP_MAX_DB` está duplicado (cliente y backend): al centralizar,
      unificar contra la misma fuente.

## Tipo de ruido enmascarante y CE (cableado 2026-09-10)

El audiómetro ofrece cuatro ruidos (`config_audiometer.json:stim_list`):
índice 3 = Narrow Band Noise, 4 = Withe Noise [sic, así está en el JSON],
5 = Speech Noise, 6 = Pink Noise.

**Lo que estaba mal:** el motor tonal entraba en la rama de enmascaramiento
sólo con `if 3 in stim`. Enmascarar con ruido blanco, speech noise o pink
noise **sonaba pero no hacía nada**: el paciente respondía como si no
hubiera ruido, sin ninguna señal de que el enmascaramiento no se aplicaba.
El alumno veía la curva sombra y creía haber enmascarado bien.

**Lo que se hizo:** los cuatro ruidos entran ahora en la fórmula, cada uno
con su CE (coeficiente de enmascaramiento), que es el término que ya existía
en `_masking_calc` y estaba fijo en 0. El CE dice cuántos dB de más hay que
subir, respecto del NBN, para lograr el mismo enmascaramiento sobre un tono:
lo que tapa un tono es la energía que cae **dentro de su banda crítica**, y
el NBN es el único que la concentra ahí (por eso su dial ya viene calibrado
en dB EM y su CE es 0). Un ruido de espectro ancho reparte la energía y
desperdicia la parte que queda afuera.

```python
CE_TONAL = {STIM_NBN: 0, STIM_PN: 5, STIM_WN: 10, STIM_SN: 10}
CE_LOGO  = {STIM_SN: 0, STIM_PN: 5, STIM_WN: 5, STIM_NBN: 20}
```

Ambas tablas viven en `src/audiometria/masking_params.py`, un modulo nuevo
que existe por dos razones: `response.py` ya importa (via `response_A`) a
`logoaudiometry.py`, asi que compartir constantes al reves cerraria el
ciclo; y es el lugar natural donde aterrizarian estos valores cuando se
hagan configurables por curso (ver la seccion de parametros configurables).

Sobre el **pink noise**: cae 3 dB por octava, así que en los graves tiene
densidad espectral parecida a la del NBN y en los agudos se parece más al
blanco. Por eso queda entre los dos. El speech noise está conformado al
espectro del habla (cae en agudos), así que para tonos rinde como el blanco
--y al revés, es el que corresponde en logoaudiometría.

Tocado: `_masking_calc` y `_resolve_masked_threshold` reciben `ce`,
`_canal_ruido()` ubica el canal enmascarante y su tipo,
`response_aerea_w_msk` / `response_osea_w_msk` ya no filtran por NBN, y el
tone decay con `contra == 'mask'` también aplica el CE. El panel muestra el
CE que se aplicó y cuánto sube el mínimo efectivo. Cubierto por
`tests/test_masking_tonal.py::TipoDeRuidoMotorTest` y
`tests/test_debug_mkg.py::TipoDeRuidoTest`.

**Los valores del CE son de arranque y falta confirmarlos**, igual que la
tabla del efecto oclusivo. Lo que no es opinable es el orden
(NBN < PN < WN/SN); las cifras exactas sí.

Pendiente:
- [ ] Confirmar los valores de `CE_TONAL` con la docente, y de paso
      preguntarle si en la cátedra se enseña un CE como margen de seguridad
      sobre el mínimo efectivo (hay protocolos que suman 5-10 dB fijos
      además de la corrección por tipo de ruido). Hoy el CE es sólo lo
      segundo.
- [ ] Que el CE dependa también de la frecuencia: la banda crítica se
      ensancha hacia los agudos, así que un ruido de espectro ancho
      desperdicia menos energía en 4000 Hz que en 250 Hz. Hoy es un escalar
      por tipo de ruido. Entra con los demás parámetros configurables por
      curso.
- [x] **Logoaudiometría: hecho.** Tenía el mismo bug que la tonal pero al
      revés: `Audiometer._mkg_intensity` exigía literalmente `"Speech
      Noise"`, así que enmascarar habla con NBN, blanco o pink sonaba y no
      llegaba al motor. Ahora el stim del canal enmascarante viaja por
      `datasignal_speech[7]` -> `ListWords.update_state` -> `playable[5]` ->
      `CalculateLogo.get(..., stim_mkg)`, y se aplica `CE_LOGO` con el orden
      invertido al tonal (SN 0, PN/WN 5, NBN 20: una banda estrecha deja
      pasar casi todo el espectro del habla). Sin `stim_mkg` se asume el
      ruido correcto, así que las llamadas y casos viejos no se penalizan.
      Cubierto por `tests/test_logo_masking.py::TipoDeRuidoLogoTest` y
      `tests/test_listwords_state.py` (la cadena entera).

      De paso salió un bug que tapaba todo esto: el constructor de
      `ListWords` llamaba a `la_super()` (que arma `self.prev` con el caso) y
      cuatro líneas después lo pisaba con `self.prev = None`. El caso que
      llega por el constructor se perdía y `calculate()` salía sin hacer nada
      hasta que `main._hydrate_modules()` volviera a llamar `la_super()`.
- [ ] Decidir si el equipo debería impedir directamente elegir un ruido que
      no corresponde a la prueba, o si tiene más valor pedagógico que el
      alumno lo elija mal y vea que necesita más nivel.

## Curva sombra en logoaudiometría: atenuación interaural plana

`CalculateLogo.get` usa una atenuación interaural única de 45 dB para todo
el espectro del habla: lo que cruza al oído contralateral se evalúa en su
curva a `intensidad - 45`, sin más. Con eso, un OD anacúsico con OI normal
da la progresión:

| habla en el OD | llega al OI | discrimina |
|---|---|---|
| 50 dB |  5 dB |   0% |
| 60 dB | 15 dB |   4% |
| 70 dB | 25 dB |  40% |
| 80 dB | 35 dB |  80% |
| 90 dB | 45 dB | 100% |

El 100% no está puesto a mano: es lo que ese OI da a 45 dB, porque su UMD
es 100% a 40 dB. La curva sombra es progresiva y sale de la curva real del
oído que recibe el cruce.

Lo que **no** está modelado: el cráneo no transmite plano. La atenuación
interaural por vía ósea es menor en los graves y mayor en los agudos (del
orden de 40 dB en 250 Hz y 50-55 dB en 4000 Hz). El habla que cruza llega
filtrada, con menos consonantes, así que la discriminación por curva sombra
debería ser algo peor que la que ese mismo oído lograría con habla
presentada directamente al mismo nivel de sensación.

Se dejó plano a propósito: el fenómeno clínico que el alumno tiene que
detectar es justamente que **el paciente con un oído muerto repite palabras
casi perfecto sin enmascarar**, y por eso el enmascaramiento es obligatorio
en logoaudiometría. Penalizar la sombra con un número inventado diluye ese
engaño sin ganar nada verificable.

Pendiente:
- [ ] Si se quiere el filtrado, la forma honesta es una atenuación
      interaural del habla por bandas en vez de un escalar (hoy
      `logo_attenuation = 45`), y derivar la penalidad de ahí en vez de
      restar un porcentaje fijo. Entra con los parámetros configurables por
      curso.
- [ ] Preguntarle a la docente qué discriminación espera de una curva
      sombra en un caso de anacusia unilateral: es la forma más directa de
      calibrar esto sin inventar.

## Catálogo de cuadros: lo que el motor todavía no puede armar

El backlog de `patologias_proximas.md` se volcó a `CaseProfile::SCENARIOS`
el 2026-09-10: el catálogo pasó de 21 a 70 cuadros (9 conductivas, 18
sensoriales --con las genéticas y congénitas--, 16 neurales que estrenan los
presets de ABR que ya existían, y 6 mixtas). Todo eso se valida en
`tests/test_case_profile.php` y **no se probó en el navegador**.

Lo que quedó afuera no es olvido: son cuadros que el motor no puede
escribir sin mentir. Ordenado por cuántos cuadros desbloquea:

- [ ] **Reflejo presente con gap** (`gap_con_reflejo` declarado por el
      cuadro). Hoy `reflexThreshold()` apaga el reflejo con cualquier gap
      >= `REFLEX_PROBE_GAP_DB` (10 dB), sin excepción. Sin esto no se
      pueden escribir la **dehiscencia del canal semicircular superior** ni
      el **acueducto vestibular dilatado**: el reflejo presente CON gap es
      justo lo que los separa de una otoesclerosis. Va de la mano del
      siguiente punto.
- [ ] **Ósea supranormal** (umbrales negativos, -5/-10 dB en graves). El
      generador recorta a 0 (`aCinco()` hace `Math.max(0, …)`). Misma
      familia que el anterior: la tercera ventana necesita los dos, más
      decidir si el VEMP de ese cuadro sale del rango por subtipo o del gap
      (hoy son excluyentes por test). Con eso entran también **Pendred** y
      **Mondini**.
- [ ] **Eje temporal / fluctuación.** Un caso es UNA foto. Sin esto, el
      Ménière y el `hidrops_retardado` no fluctúan, el `cmv_congenito` y la
      `nihl_cronica` no progresan, los `salicilatos` y el
      `toxico_metabolico` no revierten, y la **tuba abierta (patulous)** no
      se puede escribir en absoluto: su hallazgo es la fluctuación
      respiratoria del timpanograma, no el audiograma (que es casi normal).
      Es el cambio más grande de esta lista.
- [ ] **Asimetría declarada por el cuadro.** Hoy la asimetría solo se
      sortea cuando los dos oídos traen el mismo cuadro y el mismo grado.
      El `autoinmune` y el `cmv_congenito` son bilaterales asimétricos por
      definición y hay que armarlos a mano.
- [ ] **Otoscopia ligada al cuadro.** `otitis_media_aguda` (tímpano
      abombado), `colesteatoma`, `perforacion`, `glomus_timpanico` (masa
      retrotimpánica) y `estenosis_atresia_cae` tienen hallazgo otoscópico
      obligado, y hoy se carga aparte del cuadro.
- [ ] **Timpanograma "no registrable".** `Z_OPTIONS` no lo tiene. La
      atresia de CAE se escribe hoy con `B`, que es lo menos falso
      disponible pero sigue siendo falso: no hay dónde sellar la sonda.
- [ ] **Eje no orgánico** (respuestas inconsistentes, SRT que no cuadra con
      el PTA, Stenger positivo). No hay nada de esto en el perfil y es un
      ejercicio entero.
- [ ] **Procesamiento auditivo central**: audiograma normal con pruebas
      dicóticas alteradas. No hay módulo donde vivan esas pruebas.
- [ ] **Hiperacusia / misofonía**: el LDL es un campo del formulario, no un
      eje del perfil.

## Edad del paciente: qué examen existe a esa edad (pediátrico)

Hoy la edad solo alimenta `CaseProfile::ageNorm()` (el piso ISO 7029). Le
falta la otra mitad: **qué método es posible a esa edad**. Sin eso, el motor
puede devolver un audiograma tonal limpio de un lactante de cuatro meses, y
eso le enseña al alumno que se puede. Es el mismo criterio del fallback
sintético: sin datos válidos, no se genera nada.

| Edad | Conductual válida | Objetiva | Impedancia |
|---|---|---|---|
| 0-6 m | ninguna (observación, sin umbral) | ABR/ASSR, OEA | sonda 1000 Hz |
| 6 m - 2.5 a | VRA (refuerzo visual) | ABR/ASSR, OEA | 226 Hz ya sirve |
| 2.5 - 5 a | juego condicionado | ídem | ídem |
| 5 a+ | tonal convencional | ídem | ídem |

Cae solo de la misma tabla: la logoaudiometría necesita lenguaje (listas por
edad, no la del adulto), el SDT antes que el SRT y el SRT antes que la UMD,
y la sonda de 226 Hz en un lactante da una curva que no significa lo que el
alumno cree que significa.

### Tres capas, y cuál manda

1. **Ficha (docente): coherencia, no permiso.** Al guardar, el mismo tipo de
   chequeo que ya hace `CaseBuilder::normalCoherenceError()`: si la edad del
   paciente no admite tonal y el caso trae audiograma tonal cargado, se
   reclama como pendiente (vía `CaseCompleteness`). El docente puede armar
   un lactante; lo que no puede es armarlo con datos que ese paciente no
   puede dar.
2. **Equipo (alumno): la capa que importa.** El módulo tonal **se abre
   igual**. Lo que cambia es el paciente: un lactante no da respuestas
   replicables --falsos positivos sueltos, nada a 90 dB, respuestas que no
   se repiten en el descenso-- y el módulo **se niega a cerrar un umbral**.
   El alumno concluye solo que el método no aplica. Mismo mecanismo que el
   enmascaramiento obligatorio en logoaudiometría: lo aprende porque le
   falla, no porque un cartel se lo prohibió. Reusa lo que ya existe:
   `paciente_confiabilidad` y `conciencia` al piso por edad, y el
   acompañante (rama `feat/sala-acompanantes`) contestando por el niño en la
   entrevista, que además es la pista.
3. **Informe / stats (docente).** El intento queda registrado ("intentó
   tonal convencional en paciente de 7 meses, 14 min"). No es castigo
   automático: es lo que el docente necesita para corregir. Va con las
   stats que ya viven embebidas en `launch.php`.

**Decisión:** manda la capa 2; la 1 evita el caso incoherente y la 3 hace
visible el error. El bloqueo duro (que el módulo ni abra) queda como opción
**por curso**, apagada por default: si el tonal no se abre nunca, el alumno
nunca elige mal y nunca aprende a elegir -- y aprende, peor, que el software
decide por él.

### Antes de tocar nada hay que decidir

- [ ] **¿VRA y juego condicionado se implementan, o el caso pediátrico se
      resuelve solo por vía objetiva?** Sin VRA el alumno queda sin salida
      conductual y el ejercicio pediátrico se reduce a "hacé un ABR": mucho
      más barato y bastante más pobre.
- [ ] **¿La edad la fija el docente o la sortea el generador?** Es el punto
      urgente: los cuadros congénitos que entraron al catálogo el 2026-09-10
      (`gjb2`, `waardenburg`, `jervell_lange_nielsen`, `rubeola_congenita`,
      `kernicterus`, `prematuro`) caen naturalmente en lactantes, así que
      esto deja de ser hipotético apenas se use el catálogo nuevo.
- [ ] **Sonda de 1000 Hz:** ¿entra como opción del impedanciómetro o el
      lactante queda fuera de impedancia? Sin ella la timpanometría del bebé
      miente igual que el tonal.

## Ficha del caso en PDF (2026-09-10)

`case_sheet_pdf.php?id=<caso>` arma la hoja de respuestas completa del caso
--perfil, audiograma, acumetría, impedanciometría con timpanogramas,
reflejos, logoaudiometría, supraliminares, deterioro tonal, ABR, OEA y
VEMP-- con los mismos gráficos del editor. Entra por el botón "PDF" de
Fichas Clínicas y por "Ficha completa en PDF" al editar un caso.

Decisiones:
- **Se arma en cada pedido, no se cachea** (a diferencia de los informes de
  alumno, que sí se guardan en `ReportFile`): el caso se edita, y un PDF en
  disco quedaría mintiendo desde la primera edición.
- **Los gráficos se dibujan en PHP** (`CaseCharts`), no se exportan del
  navegador: el backend no tiene headless Chrome ni GD garantizado. La
  contra es que las escalas y los símbolos están escritos dos veces --acá y
  en `public/js/case/*.js`--, y cada función dice de cuál JS es espejo.
- **El ABR, la OEA y el VEMP se imprimen como lo que el caso DECLARA**
  (umbral por estímulo, desviación por banda, umbral por subtipo), no como
  una curva simulada: el generador de curvas vive en Python, en el cliente,
  y duplicarlo en PHP sería una segunda fuente de verdad.

### El hosting corre PHP 7.4

Salió a la luz con este PDF: `str_starts_with()` es de PHP 8.0 y allá es un
"Call to undefined function". Al buscar el resto apareció que
`ReportPdfBuilder` usaba `match` (también 8.0) en dos lugares, así que ese
archivo **ni siquiera parseaba** en el hosting: `report_pdf.php` devolvía 500
y el PDF de los informes del alumno nunca se generó ahí. Los dos `match`
ahora son `switch`/mapa.

`tests/test_php_baseline.php` escanea `src/` y `public/` y falla si vuelve a
entrar sintaxis de PHP 8. Es una red, no una garantía; la comprobación
completa es parsear con un 7.4 de verdad, y el comando está en el docblock
de ese test (la suite entera corre en `php:7.4-cli`).

Pendiente:
- [ ] **Probarlo en el navegador con un caso real.** Acá no hay pdo_sqlite:
      lo único ejecutado es `CaseSheetPdf::build()` sobre un caso sintético
      (tests/test_case_sheet_pdf.php) y la revisión visual del PDF que sale
      de ahí. El endpoint, los permisos por curso y los dos botones están
      sin ejecutar una sola vez.
- [x] Fotos incrustadas (2026-09-10): la del paciente en la portada y las de
      otoscopia debajo del texto de cada fase. Se guardan en webp y png, y el
      PDF solo lleva JPEG: convierte `src/PdfImage.php` con GD, en memoria y
      sin cachear (una foto se reemplaza desde el editor, y un JPEG guardado
      al lado quedaría mostrando la vieja). Sin GD, o con una foto ilegible,
      se omite esa foto en vez de tumbar la ficha.
- Versión "para el alumno" del PDF: **descartada** (2026-09-10). Se llegó a
      implementar (`?modo=alumno`, recortando perfil y mandos del generador)
      y el docente la sacó: no hay caso de uso. La ficha es del docente y se
      imprime entera. No reintroducir sin que la pida.
- [x] Revisión del docente sobre el PDF, 2026-09-10 (todo aplicado en el PDF
      **y** en la vista previa del editor donde correspondía):
      ósea unida con línea punteada y LDL con guiones más largos (dos
      discontinuas distintas); ósea y LDL solo de 250 a 4000 Hz, que es
      donde se miden; línea de 20 dB gruesa marcando el límite de la
      audición normal (sale de `CaseProfile::GRADES`, no de un 20 escrito a
      mano); logoaudiograma redondeado con cúbica monótona (Fritsch-Carlson,
      que no se pasa de 100 % ni baja de 0); promedios al paso de 5 dB y con
      las frecuencias entre paréntesis; timpanograma con eje Y al doble del
      pico de su curva, y la B --que no tiene pico-- tomando la escala del
      otro oído; reflejos en la tabla espejada del editor; acompañantes con
      su versión de la historia y sus rasgos de entrevista; la tabla de
      umbrales reemplazada por el detalle de enmascaramiento (`CaseMasking`,
      fórmulas copiadas de `response.py`/`DebugMkg.py`); curvas de ABR
      (serie del click por intensidad) y de VEMP (tres subtipos por oído),
      reconstruidas de los parámetros del caso en `CaseWaveforms`; y OEA con
      las cuatro pruebas --TEOAE, DP-grama, SFOAE y SOAE-- cada una en sus
      bandas y con su área normal (`CaseOae`).
- [x] Las escalas duplicadas entre PHP y JS ya no pueden separarse en
      silencio (2026-09-10): `tests/test_charts_vs_js.php` lee
      `public/js/case/*.js` y compara contra `CaseCharts` la tabla de
      atenuación interaural, el gap que enmascara la ósea, los rangos de los
      tres gráficos, las seis campanas del timpanograma y la fórmula del
      rollover. Unificarlos de verdad --que el editor lea las constantes
      desde PHP-- implicaba reescribir el dibujo del editor, que funciona;
      no vale el riesgo. Falla el test si alguien mueve un solo lado.

## El update mentía la versión (arreglado 2026-09-10)

Una docente reportó que la logoaudiometría seguía mal **después de
actualizar**: oído sano a 40 dB no entendía, y sólo entendía con 20 dB de
ruido en el oído malo. Esa conducta es el motor viejo de `CalculateLogo`
(rango `[mkg_min, mkg_max]` + curva sombra, hasta `ca161de`). En el motor
nuevo es **imposible**: `get()` devuelve `max(propio, cruce)` y el ruido
sólo aparece restando en los dos términos, así que enmascarar nunca puede
subir el puntaje.

El binario publicado estaba bien (verificado abriendo el PYZ del `LabSim`
de `rde8b2be`: el módulo `audiometria.logoaudiometry` trae el texto nuevo y
ya no trae `curva sombra`). El problema era el swap:

- `_UPDATER_SCRIPT` corre desacoplado con stdout/stderr a `/dev/null` y,
  después del `set +e`, ignoraba el resultado de cada `cp`.
- Al final escribía `BUILD_VERSION` **siempre**, hubiera copiado o no.

O sea: si la copia del ejecutable fallaba (permisos de una instalación con
sudo, disco lleno, lo que sea), el cliente quedaba con **código viejo y
etiqueta nueva**. Y como el updater compara contra `BUILD_VERSION`, el
update no se reintentaba nunca más: quedaba clavado ahí para siempre.

Ahora el script loguea a `resources/local_cache/update.log`, marca cada
copia fallida y sólo escribe `BUILD_VERSION` si no falló ninguna. Si falló,
la versión queda en la vieja y el próximo arranque vuelve a ofrecer el
update.

Para diagnosticar un cliente dudoso: `sha256sum LabSim` contra el hash de
`LabSim` en el `manifest.json` de la release que dice tener. Así se cazó
este caso: `BUILD_VERSION` decía `0.9.8-rde8b2be` y el ejecutable tenía el
sha de `rca161de`.

Y como el updater compara contra `BUILD_VERSION`, esa instalación **ya no
volvía a ver ninguna actualización**: quedaba clavada para siempre. Por eso
`check_for_update` ahora, cuando no hay nada más nuevo que ofrecer, compara
el sha256 del ejecutable contra el `manifest.json` de su propia release y
ofrece reinstalar el paquete completo si no coincide
(`_check_install_integrity`). Se hace una sola vez por build_id --marca en
`resources/local_cache/.install_verified`-- y si no se puede comprobar (sin
red, release sin manifest) no se molesta al usuario. Cubierto por
`tests/test_updater_integrity.py`.

Para destrabar a mano una instalación ya mentida, sin reinstalar: escribir
en `BUILD_VERSION` la versión real (la que diga el sha) y volver a abrir.

Pendiente de esta misma revisión (no tocado todavía):
- [ ] `Audiometer._mkg_on` exige `"Invertido"` en el canal del ruido. Si el
      alumno lo deja en Normal, el ruido **suena** pero llega
      `with_mkg=False`/`int_mkg=None` al motor y no enmascara nada: lo que
      se oye y lo que se simula no coinciden.
- [ ] `response.py:response_sdt_w_mkg` (mano levantada del SDT) exige
      literal `Speech Noise` (índice 5) → con cualquier otro ruido hace
      `downHand()` siempre; y sigue con el modelo viejo de rango + curva
      sombra, distinto del "mejor de las dos vías" que usa
      `CalculateLogo`. Son dos modelos para el mismo fenómeno.

### Los trazos del PDF no son el generador

`CaseWaveforms` (ABR y VEMP) y `CaseOae` reconstruyen la FORMA del examen a
partir de los parámetros del caso: mismas latencias normativas, misma
función latencia-intensidad (Hood, quiebre en 70 dB), mismas reglas del
patrón retrococlear --incluido que solo se aplican si el oído es neural, que
es lo que hace `if is_neural` en el generador-- y misma ley de atenuación de
la OEA. Lo que NO tienen es ruido, promediación, artefactos ni FSP: eso vive
en Python y sigue siendo la única fuente de verdad de la señal. El pie de
cada gráfico lo dice.

La copia de los normativos (`CLICK_BASE`, `CaseOae::TEOAE/DPOAE/SFOAE/SOAE`)
existe porque `resources/abr/` y `resources/oae/` no se despliegan con el
backend. Pendiente:
- [ ] Un test que compare esas constantes contra
      `resources/*/normative_data.json` del repo (como hace
      `test_charts_vs_js.php` con el JavaScript). Hoy se copiaron a mano y
      nada avisa si el JSON cambia.
- [ ] La normativa por curso (`AppConfig`, `normative_data.abr`) no se
      consulta: el PDF siempre dibuja con los valores por defecto. Si un
      curso tiene su propia tabla, su ficha debería usarla.

### Los chirp del ABR están mal catalogados

`CaseProfile::STIM_WEIGHTS` y el resto del módulo tratan "CE-Chirp" y
"LS-Chirp" como dos estímulos de banda ancha, y eso no existe: el CE-chirp
es de banda ancha y el **NB-chirp es frecuencial** (banda estrecha centrada
en una frecuencia), que es otra cosa y se lee contra el umbral de ESA
frecuencia. "LS" es el tipo de chirp (level-specific), no una familia
aparte: hay CE-chirp LS y NB-chirp LS.

Por eso la columna de umbral conductual de la ficha deja los chirp en `--`:
poner ahí un promedio de banda ancha sería tapar el error con un número.

- [ ] Decidir el catálogo real de estímulos (click, tone burst por
      frecuencia, CE-chirp de banda ancha, NB-chirp por frecuencia) y con
      qué umbral conductual se compara cada uno.
- [ ] Tocar los dos lados a la vez: `STIM_WEIGHTS` y `STIM_NHL_CORRECTION`
      en CaseProfile.php, y `STIM_MAP` en src/abr/ABR_generator.py, que son
      la misma lista escrita dos veces.

### La ficha de OEA no configura las transientes

El formulario guarda UN perfil de emisión por oído (tipo, umbral, caída por
banda, atenuación, ruido, sello, variabilidad) más el modo y los picos del
SOAE. Con eso el cliente arma las cuatro pruebas, pero **el TEOAE no tiene
ningún parámetro propio**, y son los que deciden si la prueba pasa o no:

- reproducibilidad (%) y estabilidad (%) del registro -- los normativos
  traen `min_reproducibility_pct` 70 y `min_stability_pct` 80, pero el caso
  no puede moverlos;
- nivel del click y número de barridos (`default_level_db_spl` 60,
  `default_n_sweeps` 260), que es lo que decide dónde termina el piso de
  ruido;
- jitter del estímulo y su tolerancia (`stim_jitter_db`), que es el control
  de que la sonda no se movió.

Un caso no puede, hoy, pedir un TEOAE con reproducibilidad baja: el
ejercicio de "la prueba no pasa porque el registro es malo, no porque el
oído esté mal" no se puede armar. Mismo hueco, más chico, en SFOAE
(supresor) y DP (niveles L1/L2).

- [ ] Agregar esos campos a la ficha de EOA (por oído, como el resto) y
      mandarlos en `cases.data['EOAS'][lado]`.
- [ ] Que el cliente los lea en lugar de sus defaults
      (`resources/oae/normative_data.json`), igual que ya hace con el
      umbral y las desviaciones.
- [ ] Mostrarlos en la ficha en PDF, al lado de los que ya están.

### La razón V/I normal es mayor que 1

Corregido el 2026-09-11: `NORM_VI_RATIO_MIN` estaba en 0.5, o sea daba por
normal una onda V de la mitad de la I. En un oído normal la V es MAYOR que
la I; por debajo de 1 la V está desproporcionadamente chica y ese es el
hallazgo retrococlear. Cambiado a 1.0 en los dos lados a la vez
(`src/abr/ABR_generator.py` y `CaseWaveforms::NORM_VI_RATIO_MIN`), porque si
se separan la ficha marca como alterado lo que el módulo da por normal.

Queda por revisar lo que cuelga de eso:

- [ ] `v_i_factor` del caso tiene default **0.45** y su ayuda dice "1.0 = sin
      caída" (ver ABR_NEURAL_DEFAULTS y views/case/_perfil.php). Con el
      criterio nuevo, un factor de 0.45 no es "la razón V/I" sino un
      multiplicador sobre la amplitud de la V; el nombre y la ayuda inducen
      a leerlo como la razón, que ahora tiene otro piso. Decidir si se
      renombra el parámetro o se recalibra su escala.
- [ ] `amplitude_v_i_ratio` en resources/abr/normative_data.json dice
      [2.5, 5.0] para la coclear: eso sí es una razón V/I de verdad y no la
      usa nadie para juzgar. Ver si el límite normal debería salir de ahí,
      por población y patología, en vez de una constante única.
- [ ] Los presets neurales (`ABR_NEURAL_PRESETS`) tienen v_i_factor entre
      0.30 y 1.0 pensados contra el piso viejo. Revisar si siguen dando el
      contraste que buscan.

### "Sin respuesta" (130) ya no es un umbral de 130 dB

Arreglado el 2026-09-11 en el backend. El audiómetro llega a 120: un 130
significa que el paciente no oyó ni al máximo, y tomarlo como número inflaba
los promedios 60 dB e inventaba gaps (restarle la ósea a un 130 da una
diferencia que nadie midió).

Qué hace ahora `CaseProfile::decompose`: recorta esos umbrales al tope del
audiómetro --ese oído es al menos así de malo, y eso sí es un dato-- y deja
la lista de frecuencias afectadas en `sin_respuesta`, para que quien derive
algo de ahí sepa que el número es un piso. El ABR de un estímulo cuyas
frecuencias no respondieron devuelve `null`, que la ficha y la vista previa
muestran como "sin respuesta"; lo que se guarda en `cases.data` sigue siendo
un entero (el tope), porque el cliente lee un número.

Pendiente, del lado del cliente:
- [ ] `src/audiometria/` y `src/abr/` siguen leyendo `Aerea`/`Osea` crudos.
      Si el alumno mide un caso con 130 cargado, el motor de la app va a
      tratarlo como 130 dB HL igual que hacía el backend.
- [ ] El formulario no distingue "no se midió" de "no hubo respuesta": los
      dos se guardan 130. En el LDL el 130 es "no se buscó" (lo pone el
      checkbox) y en la tonal es "no respondió". **No son lo mismo**: sin
      respuesta se anota con su símbolo y una flecha hacia abajo (ya se
      dibuja así en la ficha y en la vista previa, 2026-09-11), y no medido
      no se anota. Hoy sólo el LDL tiene cómo decir "no medido", con el
      checkbox por oído; la tonal necesita algo equivalente, por frecuencia
      --una casilla, o un valor reservado distinto del 130-- antes de que se
      pueda cargar un caso con frecuencias sin probar.


### La gradiente del timpanograma no discrimina nada

La ficha ya la muestra (2026-09-11), calculada igual que el equipo: altura de
la curva a ±50 daPa del pico sobre la altura del pico, entre 0 y 1
(`Z.move` en `src/impedanciometria/Z.py`, replicado en
`CaseCharts::gradienteTimpanograma`).

El problema es que da **0,85 en toda curva con pico**, sea A, As, Ad, C o Cs.
`Z_225.curve_z` arma la curva con `pressure_max = 200` fijo, así que todas
tienen el mismo ancho: a ±50 daPa del pico el coseno alzado siempre va en
`0,5 + 0,5·cos(π/4) = 0,854`. Lo único que la mueve es el ruido de medición,
y sólo en las curvas de compliance muy baja (As, Cs), donde el ruido pesa
respecto del pico; un B da 0,00 porque su compliance redondea a cero.

Además el sentido está invertido respecto de la gradiente clásica: acá 1 es
una curva ancha y 0 una en punta.

- [ ] Que el ancho de la curva salga de la letra y no sea fijo (un As/Cs
      rígido es ancho, un Ad puntiagudo) para que la gradiente signifique
      algo. Toca `Z_225.curve_z` y, en espejo, `CaseCharts::curvaTimpanograma`
      y `public/js/case/tympanogram.js`.
- [ ] Decidir si se informa la gradiente clásica (1 - esta) o se deja la del
      equipo. Hoy la ficha muestra las dos: la de la curva impresa, que sí
      distingue los tipos, y abajo la del equipo, que es la que el alumno lee
      en pantalla.

Decisión del 2026-09-11: la ficha **no** dibuja la curva de la app. Se probó
--el coseno alzado de ancho fijo, redondeado en el ápice-- y se volvió a la
curva impresa de siempre: ápice en punta, ancho por letra, eje fijo de 0 a
2 mL. Un timpanograma en papel se lee así, y esa es la convención de la
ficha; un Ad se sale por arriba de los 2 mL y se avisa en el rótulo, igual
que pasa en el equipo si el alumno no sube el cc. El costo es que hay dos
gradientes, y por eso están las dos filas.

### La compliance y la presión del timpanograma no se pueden anticipar

El caso guarda sólo la letra de Jerger. La compliance y la presión concretas
las sortea la app al abrir el equipo (`Z_225.create_auto`), con una semilla
`(id del paciente, oído, sonda)` que es un `random.Random` de Python y no se
puede reproducir desde PHP.

Por eso la ficha informa el **rango** por letra y dibuja el centro, en vez de
un número que no va a coincidir con el que vea el alumno.

- [ ] Si se quiere el número exacto en la ficha, hay que sortearlo en el
      backend al crear el caso y guardarlo en `cases.data`, y que la app lo
      lea en vez de sortear. Es el mismo patrón que ya se usa para todo lo
      demás del caso.
