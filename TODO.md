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
