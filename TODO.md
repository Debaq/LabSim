# TODO

## Build más liviano y arranque más rápido (explorado 2026-09-24, sin hacer)

Medido sobre el build Linux (`dist/LabSim`, 431 MB) y con `-X importtime`.

**Tamaño (~90 MB recortables, solo en `LabSim.spec`, sin tocar código):**
PyInstaller mete todos los plugins de Qt y cada uno arrastra sus libs.
- Tema GTK (`plugins/platformthemes/libqgtk3.so`) -> GTK3, cairo, pango,
  harfbuzz, libxml2, glycin y una segunda ICU (v78, además de la 73 de
  PySide6): ~60 MB. No se usa: la app fuerza Fusion claro.
- QtQuick/Qml/QmlModels/VirtualKeyboard (~17 MB): los arrastra
  `platforminputcontexts/libqtvirtualkeyboardplugin.so`. Todo es Widgets.
- Qt6Pdf (~4,5 MB): lo arrastra `imageformats/libqpdf.so`.
- Plataformas wayland/eglfs/vnc/linuxfb + egldeviceintegrations (~3 MB):
  en Linux basta xcb.
- `translations/` (124 .qm, ~7 MB): a lo sumo las de español.
- imageformats tiff/webp/icns/tga/wbmp (~1,5 MB): bastan jpeg/svg/ico.

NO sacar: QtMultimedia + FFmpeg (audio del audiómetro), QtNetwork (lo pide
audio_player), QtOpenGL/QtSvg/QtTest (pyqtgraph los importa al cargar).
Probar después que la app instalada arranque y que suene el audio.

Windows: mismo criterio pero sin GTK; revisar Qt6Quick/Qml/Pdf,
traducciones y `opengl32sw.dll` (~20 MB). No medido: el build sale del
runner (bajar el artefacto para ver).

**Arranque (`import main` = 3,7 s, de eso `scipy.signal` = 2,1 s):**
Solo se usan `butter`, `sosfiltfilt`, `filtfilt` (ABR/VEMP),
`gaussian_filter1d` (abr/smooth.py) y `scipy.stats.ncf` (sorteo FSP), pero
`import scipy.signal` carga stats/interpolate/optimize/ndimage. Entra al
arrancar por main -> AabrMainWindow -> ABR_generator. Importarlo dentro de
las funciones (abr/ABR_generator.py, vemp/engine.py, abr/smooth.py) ahorra
~2 s; el costo pasa a la primera captura, y se puede precargar en un hilo
después del login. Otros: pyqtgraph 0,57 s, numpy 0,33 s, requests 0,2 s.

## Modo laboratorio (kiosko) y preferencias del alumno (2026-09-24, sin probar en Windows real)

- `LABSIM_KIOSKO=1` (variable de entorno del equipo, se lee solo en
  `src/core/kiosko.py`). En Windows, como admin: `setx LABSIM_KIOSKO 1 /M`.
  Hace tres cosas: actualiza sin preguntar, aplica el "mouse para zurdos"
  del alumno dentro de LabSim, y deja la ventana a pantalla completa sin
  botones de ventana ni forma de cerrarla (Alt+F4 tampoco); solo un
  docente logueado ve el botón de cerrar. `LABSIM_AUTO_UPDATE=1` sigue funcionando
  solo para la actualización.
- Preferencias en la cuenta (`users.prefs`, `UserPrefs.php`,
  `api/my_prefs.php`), llegan con el login: atajos de teclado propios y
  mouse para zurdos. Botón "Configuración" en la barra de acciones.
- Atajos (`src/core/atajos.py`): con el controlador LabSim conectado
  mandan las teclas del firmware (no se pueden cambiar); sin él, las del
  alumno sobre las por defecto (W sube / S baja). Mantener los ids iguales
  a `UserPrefs::ACCIONES`.
- Decisión: los atajos personales se aplican en cualquier equipo; el mouse
  para zurdos solo en kiosko, porque en un equipo propio el alumno lo tiene
  en el sistema y LabSim lo volvería a invertir.
- [ ] Probar en Windows real: detección del controlador (registro +
  cfgmgr32) y mouse para zurdos sobre ABR/VEMP (menú contextual de pyqtgraph).

## Informes de examen: guardado automático (2026-09-24, sin probar en la app real)

- **Causa de los ABR que no llegaban**: en la app instalada no existe
  `resources/local_cache/abr/temp` (`local_cache` está en `.gitignore`, el
  build del CI no la trae). El JPEG no se escribía, sin error, y la subida
  reventaba al abrir el archivo: el informe entero se perdía. Ahora se crea
  la carpeta y una imagen que falte no tira abajo el informe.
- `src/core/report_autosave.py`: cada 30 s sube lo que cambió de ABR, AABR,
  EOA, VEMP y Otoscopia; también al esconder el módulo y al cerrar la app o
  la sesión con la atención abierta. Contrato: `report_job()` en cada módulo.
- Atender a otro paciente con una atención real abierta ahora avisa y no
  deja: antes vaciaba los módulos sin subir nada.
- Retomar la atención recupera el ABR/ECochG guardado (`api/my_report.php`).
- [x] Recuperar al retomar también EOA, VEMP, AABR y Otoscopia
  (`restore_report` en cada módulo, lo reparte `ReportAutosave.recuperar`).
  VEMP ahora guarda el trazo de cada curva (`traza`, `ajustes`,
  `emg_suma`); un informe VEMP de antes de esto no trae trazo y sus curvas
  no se pueden redibujar. EOA recupera los resultados por prueba y oído,
  no los gráficos (las capturas ya están en el servidor).
- [ ] Subir al servidor: `api/my_report.php` (nuevo), `api/my_patient_reports.php`
  (hoy da 404 en producción) y `api/report_upload.php` (sin revisión).
- **Atención cerrada = congelada** (pedido 2026-09-24): ningún informe se
  vuelve a subir después de 'atendido' (report_upload.php 409 para todos;
  se borró ReportRevision). Las sesiones anteriores del ABR y "Mis
  pacientes → Exámenes → Ver en el ABR" son solo lectura. El PDF se ve
  solo en la web (portal del alumno / perfil del alumno para el docente).

## VEMP v2: probar en la app real (pendiente)

`src/vemp/` se rehizo entero (2026-09-12). Lo anterior se borró: no quedó
nada de `VEMP_generator_v1.py` ni de los `Vemp*.py` viejos. Lo que hay
ahora, y por qué:

- **Se promedian barridos de verdad** (`engine.MotorVemp.lote`). Antes había
  una curva objetivo y un factor de crecimiento que la iba revelando: la
  promediación era una animación. Ahora cada tick genera barridos, el equipo
  acepta o rechaza cada uno y la curva es el promedio acumulado de los
  aceptados; el ruido baja con la raíz de N porque se promedia, no porque se
  lo multiplique por un número.
- **La amplitud que compara es la CORREGIDA** (pico-pico / EMG rectificado,
  `session.Registro.p2p_corregida`). La cruda depende de cuánto contrajo el
  paciente, así que la asimetría de Jongkees se calcula con la corregida.
- **Con el músculo fuera de banda no entra ningún barrido**: el registro no
  avanza y se corta solo a los 8 ticks (`TICKS_SIN_AVANCE`). Antes avanzaba
  igual, sucio.
- **Vía ósea**: el módulo lee el gap 500/1000 Hz del audiograma del MISMO
  caso (`patient._gap_audiograma`, sobre `Aerea_mkg`/`Osea_mkg`), así que una
  conductiva apaga el VEMP aéreo y el vibrador lo recupera. La ventaja del
  vibrador (`protocol.OSEO_VENTAJA_DB = 15`) es un valor declarado, no
  normativo.
- **Sintonía frecuencial**: 500/750/1000 Hz, y un umbral muy bajo
  (`patient.UMBRAL_SINTONIA_INVERTIDA = 55`) invierte la sintonía y sube la
  amplitud por encima de la normativa.
- **Fatiga y recuperación del músculo**: sostener la contracción baja el EMG
  (`MANIOBRAS[...][2]`) y descansar entre curvas lo recupera al doble de esa
  velocidad (`RECUPERACION`).
- **Se marca haciendo clic en la curva** con el pico elegido en la barra, y
  la marca se pega al extremo de la polaridad correcta
  (`Registro.pico_cercano`). Los cursores A/A' y las celdas clicables de la
  tabla no existen más.
- El contrato con el backend NO se tocó: mismo `cases.data['VEMP']`, mismo
  `upload_report(appointment_id, 'VEMP', ...)`. `ReportPdfBuilder` ahora
  además imprime la p-p corregida por curva y el bloque de umbral.

Decisiones tomadas acá (no hay de dónde sacarlas):
- Escala del óseo en dB FL, 20-75, propia y separada de la aérea (dB SPL,
  50-125): el caso guarda un solo umbral, que es el aéreo.
- Tolerancia de la banda de picos del gráfico: `traces.ANCHO_BANDA_MS = 2`,
  declarada, porque el JSON normativo no trae desviación estándar por pico.
- El mVEMP queda con la normativa que ya tenía (experimental, la misma tabla
  del JSON): no se inventaron valores nuevos.

Pendiente:
- [ ] **Correr el módulo en la app de verdad, con un caso del editor.** Lo
      ejecutado hasta acá es offscreen (venv con PySide6/pyqtgraph/scipy):
      los 16 tests de `tests/test_vemp.py`, el ciclo de vida completo
      (atender, registrar, pausar, borrar, cerrar) y las tres pestañas
      renderizadas a PNG. Falta verlo dentro del MDI de LabSim.
- [ ] Confirmar el PDF con un informe real subido desde la app.
- [ ] Umbral y sintonía en la ficha del docente: hoy el caso guarda UN
      umbral por subtipo y la frecuencia lo corre con una regla declarada
      (`patient._CORRIMIENTO_FREQ`). Si se quiere que el docente arme un
      hidrops con la sintonía corrida a mano, hay que agregarle campos a
      `_vemp.php` y a `CaseForm::parseVemp`.
- [ ] Impedancia de electrodos: no hay control (el motor no la usa). Si se
      agrega, entra como un campo más de `Ajustes`.

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
- [ ] UI de edición: ya no se escribe a mano -- es una entrada más en el
      registro `src/CourseParams.php` (grupos, filas, campos con min/max y
      defaults) y la card se pinta sola. Ojo: son parámetros que cambian cómo
      responde el paciente, no sólo cómo se informa -- conviene mostrar en el editor qué implica cada
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
- [x] **Ficha de estudio (2026-09-14):** vuelve la versión recortada, pedida
      de nuevo pero con otro enfoque -- no es "la ficha con menos secciones",
      es una ficha clínica real para repartir al alumno. `build(...,
      estudio: true)` (`?modo=estudio` en el endpoint, botón "PDF estudio" en
      Fichas Clínicas y "Ficha de estudio en PDF" en el editor) mantiene
      TODOS los exámenes con sus gráficos y números medidos, y saca solo lo
      que es la solución del caso o un mando del generador: el resumen de
      "Perfil auditivo" entero, la tabla de patrón retrococlear y la de
      "Captura y FSP" del ABR, "Perfil del oído" y "Caída del perfil" de la
      OEA, la patología cargada en el título de cada trazo (ABR y VEMP), las
      desviaciones cargadas a mano, la disposición del paciente (0-100), el
      aviso de "Borrador IA" y el de fichas sin decidir (ambos son para el
      docente). Sigue siendo un PDF solo para el docente -- el gate es el
      mismo `Auth::requireAdminSession()` de siempre -- es él quien decide
      cuándo y a quién repartírsela. La versión anterior (2026-09-10) se
      había sacado del todo por no tener caso de uso; esta vez el pedido fue
      explícito, así que si se vuelve a tocar este criterio, que quede
      anotado acá por qué.
      En impedanciometría (mismo día) el recorte por título no alcanzaba:
      compliance estática y presión del pico se guardan como RANGO (la app
      sortea el valor real ahí dentro, distinto por paciente) y ese rango sí
      es la respuesta del caso. La ficha de estudio no los saca: los reduce
      a un único valor -- el centro del rango, el mismo que ya usa la curva
      para dibujarse (`CaseCharts::valoresTimpanograma()['estatica'|'pico_dapa']`)
      -- como leería el alumno la pantalla de un equipo real. También se
      saca la gradiente recalculada "del equipo" (duplicado interno) y la
      morfología de los reflejos (sí es un hallazgo/respuesta).
      **La letra de Jerger NO se saca** (a diferencia de un primer intento
      el mismo día): se lee directo de la curva, así que no es una
      respuesta escondida. Va en las dos versiones, en la tabla y --desde
      este cambio-- también impresa sobre el propio gráfico del
      timpanograma, como en un equipo real: OD arriba a la izquierda en
      rojo, OI arriba a la derecha en azul, con margen (no pegada a la
      esquina, para no comerse la curva ni el eje).
      Ver el bloque final de `tests/test_case_sheet_pdf.php` --ojo ahí con
      dos trampas de encoding: una palabra con tilde nunca matchea contra el
      PDF (MiniPdf reescribe a WinAnsi/cp1252, bytes distintos del literal
      UTF-8 del test) y un paréntesis literal sale escapado en el content
      stream (`\(Jerger\)`), así que los needles van sin tildes y sin
      paréntesis.
      En audiometría se sumaron dos ajustes más, mismo criterio:
      - **Rótulo "LDL:" sobre el propio audiograma** (`CaseCharts::audiogram()`),
        no solo en la leyenda lateral: 125 Hz no mide ni vía ósea ni LDL (ver
        `FREQS_OSEA`), así que esa celda de la grilla queda libre y ahí va el
        texto, con margen del cruce de líneas. Es un rótulo, no una
        respuesta, así que va en **las dos versiones** del PDF (y es un
        cambio del audiograma en sí, no solo de la ficha de estudio).
      - **La tabla de enmascaramiento SÍ se saca** de la ficha de estudio (y
        con ella el aviso "El enmascaramiento lo infiere el motor, no se
        carga a mano" de al lado de la leyenda): a diferencia de la letra de
        Jerger, acá la tabla ES la cuenta hecha --el rango mín-máx de ruido
        útil por frecuencia-- que el alumno tiene que decidir solo en la
        cabina. Los umbrales del audiograma (círculo/cruz/corchetes) se
        quedan igual, es solo la tabla de abajo la que no va.

## UMD por niveles, no un solo punto (2026-09-14)

En logoaudiometría, la fila "UMD" del PDF (`CaseSheetPdf::logoaudiometria()`)
era un solo dato: "96 % a 70 dB". Cambia a como se prueba de verdad: el UMD
sube de 5 en 5 dB hasta el máximo, y esos escalones intermedios son parte
del examen, no un detalle de procedimiento a esconder.

Regla (confirmada con el usuario): hasta 3 niveles de 5 dB terminando en el
nivel del máximo, sin bajar de 45 dB (piso de la prueba). Si el máximo ya
sale a 45 dB no hace falta seguir probando y queda un solo nivel. Ejemplos:
máximo a 50 → 45,50; a 55 → 45,50,55; a 60 → 50,55,60 (la ventana se corre,
ya no lleva el 45). Implementado en `CaseSheetPdf::nivelesUmd()`.

Esto **solo pasa en este informe** (aclaración explícita del usuario): no
hay cambio en cómo el caso guarda el UMD (`data.UMD` sigue siendo un solo
`{int, percentage}` por oído, ver `case_create.php`) ni en el motor. Los
niveles intermedios se DERIVAN en el momento de armar el PDF, con la misma
curva por tramos que ya dibuja el logoaudiograma
(`CaseCharts::logogramPoints()`: plano en 0 hasta el SDT, recta hasta el
UMD, plano --o con rollover, cayendo-- de ahí en más). Nueva función
`CaseSheetPdf::pctEnNivelUmd()` replica esa misma curva para poder leer el
% en cualquier dB, no solo en el punto guardado.

Cada oído puede llegar a su máximo en un nivel distinto (ej. OD a 70,
OI a 65): la tabla trae la UNIÓN de los niveles de los dos oídos, así que
un nivel puede quedar "de más" para uno de los dos oídos -- para ese oído,
el % en ese nivel se lee de la misma curva (plano o con rollover más allá
de su propio UMD), nunca inventado ni "--". Ver los asserts nuevos al final
de `tests/test_case_sheet_pdf.php` para los números exactos con y sin
rollover.

Y en la ficha de estudio, la fila **"Rollover: Sí/No" se saca** (mismo día):
es el veredicto, no un dato de lectura. Con la ventana de niveles de arriba
ya puesta, el rollover se ve solo --el % de OI baja de 80 a 75 pasado su
propio UMD-- así que decirlo aparte sería resolverle el hallazgo al
alumno. La caída sigue estando en los números (eso no se toca, es el
examen); lo único que se corta es la etiqueta "Rollover".

Mismo día, tres veredictos más que se cortan de la ficha de estudio por el
mismo motivo (dicen la respuesta en vez de dejar que se lea del símbolo o
del trazo):
- **Weber, "Lateraliza a OD/OI"**: la flecha ya apunta para el lado que
  lateraliza -- decirlo también en texto sería sobrante. La flecha se
  queda igual en las dos versiones, se corta solo el texto de al lado
  (`CaseBuilder::WEBER_LABELS`).
- **Impedanciometría, fila "Función tubaria"**: es un veredicto cargado a
  mano (Normal/Disfunción tubaria), no algo que se lea de una curva del
  timpanograma -- no tiene ningún trazo propio en la ficha del que
  deducirse, así que se corta entera.
- **ABR, el párrafo "Trazo reconstruido de los parámetros del caso: sin
  ruido, sin promediación y sin artefactos..."**: mecánica del software
  (avisa que la curva es sintética y no una pantalla de equipo real), no
  algo que le sirva al alumno para leer el trazo.

## ABR: cada nivel repetido y escalón bajo el umbral sin V (2026-09-14)

La pila de trazos del click (`CaseSheetPdf::abr()`) mostraba un trazo por
nivel, terminando justo en el umbral. Pedido del usuario: los niveles van
DUPLICADOS (el equipo repite cada intensidad para confirmar que la V es
reproducible, no un artefacto de una sola pasada) y siempre tiene que haber
un nivel bajo el umbral que se quede SIN onda V -- así se decide que el
umbral de arriba es el umbral, y no un nivel más de la serie.

Implementado en `CaseSheetPdf::nivelesAbr()` (nueva, privada, solo para
esta pila de la ficha): toma `CaseWaveforms::serieIntensidades()` tal cual
(sin tocar esa función -- la comparte VEMP, que NO lleva este cambio) y le
agrega un escalón de 5 dB bajo el umbral (piso -10 dB) cuando hubo umbral
real (si fue "sin respuesta en todo el barrido" no hay umbral que
confirmar, así que no se agrega), y después duplica cada nivel de la
lista. El escalón sin V no es un truco de UI: con el modelo de amplitud de
`CaseWaveforms::ondasClick()` (`sl_min` de la onda V = -4), 5 dB bajo el
umbral el crecimiento da 0 exacto, así que el trazo sale plano de verdad,
no solo etiquetado como tal.

Como ahora hay hasta el doble de trazos (más el escalón extra), el alto de
la pila (antes fijo en 168pt) pasa a ser `max(168, cantidad_de_niveles *
26)`, calculado ANTES de dibujar (para que OD y OI, que pueden tener
umbrales distintos y por lo tanto distinta cantidad de niveles, compartan
la misma altura de caja). Verificado renderizando el PDF a PNG con
`pdftoppm` (no alcanza con leer el texto crudo para esto, hay que ver el
dibujo) -- sin superposición, el escalón bajo el umbral sale plano sin I/III/V
marcadas, en las dos versiones de la ficha (docente y estudio: esto no es
un veredicto que esconder, es cómo se ve un ABR real).

Tests: bloque nuevo en `tests/test_case_sheet_pdf.php` que prueba
`nivelesAbr()` por reflexión (duplicado, escalón, piso de -10 dB, caso sin
umbral real) y confirma con `CaseWaveforms::ondasClick()` que la amplitud
de la V cae bajo `AMP_VISIBLE` en el escalón de confirmación.

**Corrección el mismo día:** las dos réplicas de un mismo nivel salían con
la MISMA separación que entre niveles distintos -- parecían dos trazos más
de la serie, no un par. `CaseCharts::waveformStack()` ahora recibe un
`$replicasPorNivel` opcional (default 1, sin cambios para VEMP que no lo
pasa): agrupa de a N trazos con un hueco chico DENTRO del par (cerca, sin
pisarse) y el hueco grande de siempre ENTRE niveles distintos; el rótulo
del nivel se imprime una sola vez por par (dos números iguales pegados
leerían como un error de impresión). `abr()` llama con
`$replicasPorNivel = 2` y el alto de la pila pasa a calcularse por GRUPOS
(`ceil(niveles/2) * 34`), no por cantidad total de trazos. Verificado de
nuevo con `pdftoppm` -- ver captura del resultado en la sesión, pares
visiblemente juntos y niveles bien separados.

**Corrección 2026-09-15: el escalón de confirmación es de 10 dB, no de
5.** El usuario dio la regla real: la evaluación baja de 20 en 20 y, cerca
del umbral, de 10 en 10 -- nunca un paso de 5 ("nunca se hace un x5").
Con umbral a 30 dB la serie tiene que ser 80,60,40,30,20 -- el "20" es el
escalón de confirmación, a 10 dB del umbral, no a 5.

**Segunda vuelta, más importante:** el usuario preguntó "¿el nivel puede
llegar a 0, funcionará en algún caso?" -- al revisarlo aparece algo peor
que el 0 (que sí funciona bien: umbral 0 da -10,0,20,40,60,80, limpio).
El umbral del ABR se guarda redondeado a 5 dB (`CaseProfile::ABR_STEP_DB
= 5`), así que la MITAD de los casos el umbral YA es un "x5" (45, 35,
25...) -- de hecho el umbral de OD en `ficha_caso_demo()`, el fixture que
usan casi todos los tests, es 45. Con `$umbralClick - 10.0`, un umbral x5
se queda en la misma familia (45 → 35, sigue siendo x5) -- exactamente lo
que el usuario dijo que nunca pasa, y el primer arreglo no lo evitaba.

Fix real: `max(-10.0, floor(($umbralClick - 1) / 10) * 10)` -- el
PRÓXIMO MÚLTIPLO DE 10 de la grilla por debajo del umbral, no un
corrimiento relativo a él. Con umbral x0 eso da el mismo resultado que
"umbral - 10" (30 -> 20). Con umbral x5 da "umbral - 5" (45 -> 40): más
cerca de lo que uno esperaría, pero sigue siendo un múltiplo de 10 limpio
y sigue bien por debajo del `sl_min` de la onda V (-4), así que la
garantía de "esta curva no tiene V" no se pierde por el gap más chico.
`CaseWaveforms::serieIntensidades()` (la parte de 20 en 20 desde el
máximo) no se tocó en ninguna de las dos vueltas.

Tests: el ejemplo exacto del usuario (umbral 30 -> 80,60,40,30,20) y el
caso x5 real (umbral 45 -> 80,60,45,40, no 80,60,45,35) quedaron los dos
fijados -- el segundo es el que hubiera fallado con el primer arreglo.

## Impedanciometría: reflejos en dB SPL, no dB HL (2026-09-14)

El pie de la tabla de reflejos acústicos decía "Umbrales en dB HL"; los
reflejos se informan en dB SPL. Corregido el texto en las dos versiones
(`CaseSheetPdf::impedanciometria()`) -- no es un cambio de valores, los
números no se tocan, era la unidad mal puesta.

## Fowler: el criterio de calificación no va en la ficha de estudio (2026-09-14)

Cuando ninguna frecuencia califica para Fowler, el PDF explicaba la regla
completa ("Hace falta una diferencia interaural de 20 a 40 dB en una misma
frecuencia, con el oído bueno en rango normal y sin gap"). Es la mecánica
del test, no un dato de lectura -- se corta en la ficha de estudio
(`CaseSheetPdf::supraliminares()`, ahora con `$estudio`). Cuando SÍ
califica alguna frecuencia, la tabla con los niveles medidos se queda
igual en las dos versiones (eso es examen real, no la regla de detrás).

## UMD: la ventana es POR OÍDO, no la unión de los dos (2026-09-14)

Corrección sobre [[UMD por niveles, no un solo punto]] (más arriba, mismo
día): la primera versión armaba la tabla con la UNIÓN de los niveles de
los dos oídos y, para el oído "de más" en un nivel ajeno, calculaba el %
extrapolando su propia curva -- lo que hacía que un oído que ya llegó a su
máximo (sin rollover, sin motivo clínico para seguir) apareciera con la
intensidad "subiendo" en niveles que en realidad no se le probaron. El
usuario lo marcó como absurdo: las restricciones y la dinámica del UMD son
por oído.

Fix: `CaseSheetPdf::nivelesUmdEar(umdInt, recruit)` (nueva) es la ventana
de UN oído -- `nivelesUmd()` de siempre (≤3 escalones hasta el máximo) y,
SOLO si ese oído tiene rollover, un escalón más ARRIBA del máximo (ahí es
donde se ve la caída, así que ahí sí hay motivo para seguir subiendo). La
tabla sigue mostrando la unión de niveles como filas compartidas (para
leer los dos oídos uno al lado del otro), pero la celda de un oído en un
nivel que no es de SU PROPIA ventana queda en "--", no en un número
extrapolado.

Y el pedido que venía con la corrección: **cada punto de la tabla tiene
que verse en el gráfico**, no solo la curva continua. `CaseCharts::logogram()`
ahora dibuja un círculo chico en cada punto de `cfg['puntos']` (la lista la
arma `logoaudiometria()` con los mismos niveles y el mismo
`pctEnNivelUmd()` de la tabla, salvo el punto que coincide con el propio
UMD -- ese ya lo marca el triángulo). Verificado con `pdftoppm`: los
círculos caen sobre la curva en los niveles de la tabla, y en el oído con
rollover se ve el punto de la caída más allá del pico.

Tests: bloque de `tests/test_case_sheet_pdf.php` reescrito -- ya no se
espera el % extrapolado (ej. "51 %" para OD a 55 dB, que ahora es de OI),
se agregó el caso de "45 dB con rollover sigue a 50" además del de "45 dB
sin rollover se queda solo", y `nivelesUmdEar()` se prueba directo por
reflexión.

**Corrección importante el mismo día:** la curva del logoaudiograma es
CÚBICA (Fritsch-Carlson), no una recta entre SDT y UMD -- así que
calcular el % con una recta (lo que hacía la primera versión) daba un
número cercano pero el punto marcado en el gráfico quedaba visiblemente
AFUERA de la curva impresa. Nueva `CaseCharts::pctLogoEnDb(cfg, db)`: lee
el punto sobre los mismos segmentos bezier que dibuja `curvaSuave()`
(bisección sobre el parámetro t, la x de una cúbica no se invierte a
mano). `CaseSheetPdf::pctEnNivelUmd()` ahora es un `use` de esa función.
Cambia los números de la tabla (ver test actualizado: 74/90/96 % para OD
en vez del viejo 66/81/96, y 64/76/80/79 % para OI en vez de 57/69/80/75)
-- son los correctos, los viejos eran la aproximación lineal.

**Y la tabla ganó enmascaramiento (mismo día, pedido del usuario):** SDT,
SRT y cada UMD se prueban con su propio mkg si hace falta, mismas fórmulas
que el motor (`src/audiometria/logoaudiometry.py::CalculateLogo`, no una
versión inventada para el PDF) -- portadas a PHP en un rincón nuevo de
`CaseMasking.php`:
- `CaseMasking::AI_HABLA` = 45 dB (atenuación interaural del habla, fija,
  no por frecuencia como en tonal).
- `CaseMasking::boneSdt($osea)` = Fletcher (mejores 2 de 500/1k/2k Hz) al
  PISO de 5 dB (floor, no redondeo) -- replica uno a uno
  `CalculateLogo._bone_sdt()`, no es el BIAP ni ningún promedio de
  catálogo.
- `CaseMasking::logo($intensidad, $boneEstudiado, $boneNoEstudiado, $sdtNoEstudiado)`
  = `{cruza, min, max}`, mismas fórmulas que `_logo_vias()`/`_masking_range()`
  (CE en 0, el del Speech Noise, el ruido correcto para esta vía).

El mkg que se IMPRIME es un solo valor -- el mínimo efectivo (`min`), el
que de verdad se usaría (de más solo tapa y arriesga sobre-enmascarar) --
no el rango entero como en la tabla tonal (ahí sí importa mostrar el
rango completo porque el alumno tiene que encontrarlo). Formato de celda:
`"{dB propio} dB[/{mkg mínimo} dB] {%}"`, con la barra y el mkg solo
cuando `cruza` es cierto.

**Colores por tramo, no por celda:** el dB propio y el % van del color
del oído de la fila (rojo OD, azul OI); el mkg va del color del oído
CONTRARIO, porque el ruido que enmascara se pone en el auricular del otro
oído. `tablaEn()` pinta cada celda entera de un solo color, así que esta
tabla NO la usa: `CaseSheetPdf::tablaHablaColoreada()` (nueva, privada) la
dibuja a mano, con varios `$pdf->text()` seguidos por segmento (mismo
patrón que ya usan otras líneas sueltas del archivo, ej. "OD · tipo ·
umbral cargado" del ABR) y `$pdf->textWidth()` para no pisarlos.
**Ojo con esto al testear:** cada tramo de color es un `Tj` separado en el
content stream, así que un string armado como "65 dB/30 dB 90 %" NO
aparece contiguo en los bytes crudos del PDF -- un `strpos()` sobre eso
falla aunque el PDF esté bien. La cuenta se prueba con
`CaseMasking::logo()`/`boneSdt()` directo, y el layout se verificó
renderizando a PNG con `pdftoppm` (ver captura en la sesión).

**Iteración de layout, dos vueltas:** un intento en el medio armó la tabla
con 7 columnas (dB/mkg/% separados por oído) para darle más ancho, pero
eso empujó la sección a una página de más (la ficha pasó de 6 a 7 páginas,
rompiendo la paginación fija por examen) y además no era lo pedido -- el
usuario quería UNA columna combinada por oído con formato "dB/mkg %", no
columnas separadas. Se volvió a 3 columnas (rótulo, OD, OI) en la misma
posición de siempre (al lado del gráfico, ancho 40%), y el Rollover volvió
a ser la última fila de la MISMA tabla (no una tabla aparte): así entra
todo en las 6 páginas de siempre. Moraleja: cuando el layout se pone
difícil, el camino no es agrandar la tabla -- es achicar el contenido de
la celda.

## Audiograma: el símbolo óseo se corre de la intersección (2026-09-14)

Con umbral óseo igual al aéreo (lo más común, sin gap) el corchete óseo
quedaba dibujado EXACTAMENTE encima del círculo/cruz de la vía aérea, en
el mismo punto -- se tapaban. Pedido del usuario: correr el símbolo (no la
línea que lo une entre frecuencias) lo suficiente para que las dos marcas
se vean, OD hacia la izquierda y OI hacia la derecha.

`CaseCharts::DESPLAZAMIENTO_OSEA = 4.0` (pt): se resta a la X del corchete
de OD y se suma a la de OI (y a su flecha de "sin respuesta", que tiene
que moverse con el símbolo). La línea punteada que une los umbrales óseos
entre frecuencias NO se toca -- sigue pasando por la frecuencia real, es
el símbolo suelto el que se corre.

Espejado en `public/js/case/audiogram.js` (`BONE_OFFSET = 4`, mismo
criterio) para no romper la paridad PDF/editor que ya cuida
`tests/test_charts_vs_js.php` -- ese test no compara coordenadas exactas
(solo que ciertos patrones existan en el código), así que no hizo falta
tocarlo, pero la paridad visual real solo se sostiene si las dos copias
llevan el mismo desplazamiento. Verificado renderizando el PDF a PNG con
`pdftoppm`: antes las marcas se superponían al pixel, ahora quedan
separadas y las dos se leen.

## Audiograma: la vía ósea normal se esconde en la ficha de estudio (2026-09-14)

Pedido del usuario: en un examen real no se prueba vía ósea en una
frecuencia donde el aéreo de ESE oído ya está en rango normal (<=20 dB,
`CaseCharts::LIMITE_NORMALIDAD_DB`) -- no hay nada que diferenciar (no
puede haber gap si no hay pérdida), así que un audiólogo de verdad ni se
molesta en tomarla. Mostrarla en la ficha de estudio sería un dato que el
examen real nunca habría generado.

Nueva `CaseCharts::freqsOseaVisibles(freqs, aereaLado, estudio)` (pública,
para poder testearla directo): en la ficha docente devuelve `FREQS_OSEA`
completo (250-4000 Hz) sin importar el aéreo -- es el perfil que cargó el
generador, se sigue mostrando entero. En la ficha de estudio, recorta a
las frecuencias donde el aéreo de ESE oído (ojo: por oído, no compartido)
es > 20 dB. El límite es inclusive: exactamente 20 dB ya se esconde.

Se llama por separado para OD y OI (`audiogram()` ahora recibe `$estudio`
y arma `$freqsOseaPorLado['od']`/`['oi']` cada uno con su propio aéreo) --
un oído puede tener el aéreo normal en una frecuencia donde el otro no, y
la línea/símbolo de UNO no tiene por qué desaparecer solo porque el OTRO
se esconde ahí. El LDL usa su propia lista sin filtrar (`$freqsOsea`, sin
sufijo `PorLado`): no es vía ósea, la regla no le aplica.

Ojo con lo que SÍ se sigue mostrando igual en las dos versiones: la línea
punteada solo se corta en las frecuencias que desaparecen (no se estira
por encima saltándolas), y el símbolo desplazado (`DESPLAZAMIENTO_OSEA`,
ver más arriba) sigue su misma regla de posición cuando corresponde
dibujarlo.

Verificado renderizando a PNG con `pdftoppm`: en el caso de prueba (OI con
aéreo normal a 250 y 500 Hz), la ficha docente muestra la ósea completa de
OI y la de estudio la corta justo ahí, sin tocar la de OD (que no tiene
ninguna frecuencia normal en ese caso). No se puede probar por texto crudo
(es dibujo vectorial, no hay marca de texto) -- el test nuevo llama
`CaseCharts::freqsOseaVisibles()` directo.

## ABR del PDF: VI/VII/SN10, efecto de tasa y ruido de fondo (2026-09-14/15)

Pedido tras un análisis de brecha (fork, sin editar nada) comparando
`CaseWaveforms.php` (el mirror del PDF) contra el generador real
(`src/abr/ABR_generator.py`): "agregá VI/VII/SN10, el efecto de tasa y el
ruido, en serio quiero verlas realistas -- pero SOLO el PDF, no el
editor". Portado a PHP tal cual está en el generador real, no una versión
inventada -- mismas constantes, mismas fórmulas.

**SN10 y VII** (`ondasClick()`, después del loop de I/III/V): geometría
DERIVADA de la V ya final (con tasa, tipo y patrón neural aplicados), no
ondas con su propio crecimiento por SL:
- SN10 (el valle que sigue a la V, contra el que se mide su amplitud
  pico-a-valle): `lat = lat_V + 0.9 + sigma_V*2`, `amp = -amp_V * 0.45`,
  `sigma = 0.55 * (sigma_V / SIGMA['V'])` (el factor de ancho de V, ya que
  el PHP no guarda un `width` aparte -- va todo adentro de `sigma`).
- VII (bump tardío chico): `lat = lat_V + 2.5`, `amp = amp_V * 0.18`,
  `sigma = 0.40` fijo (NO escala con el ancho de V, así sale en el
  generador real).
- `trazo()` ya sumaba genérico sobre lo que tuviera `$ondas` -- agregarlas
  ahí alcanzó, sin tocar esa función. Los `foreach (['I','III','V'])` que
  marcan picos en el trazo (CaseSheetPdf::abr()) siguen sin tocar SN10/VII,
  a propósito: no se marcan con texto, son parte de la forma, no un pico
  que el alumno tenga que encontrar.

**Efecto de tasa** (`ondasClick()` gana `float $tasa = RATE_REF`):
`RATE_REF=21.1` (donde están medidos los valores normativos, ahí no
cambia nada), `RATE_LAT_SLOPE`/`RATE_AMP_DECAY` por onda (I la más
sensible, V la que mejor aguanta), y `RATE_NEURAL_FACTORES` que multiplica
el corrimiento/caída si el oído es neural (clave = `neural.sensibilidad_tasa`,
ya existía en el PHP). Verificado con números: a 90/s un oído normal
corre la V +0.41 ms y cae a 79 % (el generador real dice "~25-30 % y
~0.4-0.6 ms", justo en rango); un oído neural "severa" a la misma tasa
corre más y cae más.

**Corrección: sin fila extra en el PDF.** Un primer intento le agregó a
`CaseSheetPdf::abr()` un par MÁS a 80 dB con `TASA_ESTRES = 90.0` al final
de cada oído (rotulado "80·alta") para MOSTRAR el efecto. El usuario lo
frenó: el pedido era que la GENERACIÓN de la onda fuera sensible a la
tasa (que `ondasClick()` supiera calcularla si se le pide), no que
apareciera una curva nueva en la ficha -- y aparte "80·alta" no es
notación clínica reconocible ("soy experto en electro[fisiología] y no
tengo idea qué es", con razón). Se sacó la fila; `ondasClick()` sigue
siendo sensible a `$tasa` (con `RATE_REF` de default, o sea sin efecto si
no se pide otra cosa) y `CaseSheetPdf::abr()` vuelve a llamarla sin ese
argumento, como antes. `TASA_ESTRES` queda como valor de referencia SOLO
para los tests que ejercitan la sensibilidad del modelo, no para dibujar
nada.

**Ruido de fondo** (`CaseWaveforms::trazo()` gana `?int $ruidoSemilla`):
antes dos pasadas al mismo nivel salían pixel a pixel iguales, y una curva
"sin respuesta" salía perfectamente plana -- ninguna de las dos cosas pasa
en un registro real. `ruidoDeFondo()` es una textura determinística por
semilla (no una simulación de la promediación entera del generador real,
que tiene EEG pink+EMG, impedancia, rechazo de artefacto -- eso es
fidelidad al EQUIPO, no al examen, y el PDF a propósito no busca eso).

**Historia de ida y vuelta sobre cuánto ruido (mismo día):** con 5
sinusoides graves (0.6-8 ciclos en 12 ms) normalizadas por la SUMA de sus
pesos y `RUIDO_AMPLITUD_UV = 0.05`, el usuario lo vio "casi plana, eso no
pasa en el de PC" (con el generador real abierto al lado). Se probó una
versión más fuerte -- más componentes en frecuencias altas (2-36 ciclos) +
jitter de muestra a muestra, normalizado por RMS en vez de por la suma
(sumar sinusoides de fase independiente rara vez suma en fase, así que
dividir por la suma llana dejaba el resultado muy por debajo de lo
nominal) y `RUIDO_AMPLITUD_UV = 0.10` -- y esa versión el usuario la vio
"horrible", pidió deshacerla.

**Decisión final: volver a la primera versión** (5 sinusoides graves,
normalización por suma, `RUIDO_AMPLITUD_UV = 0.05`) -- es la que quedó.
No es que esa versión estuviera "mal" técnicamente; el juicio de cuánto
ruido se ve bien en una ficha impresa es del usuario, no algo que una
fórmula "correcta" (RMS vs. suma) resuelva sola. Si se vuelve a tocar esto,
confirmar con él antes de subir la amplitud de nuevo -- no asumir que
"más realista técnicamente" es "se ve mejor".

`CaseSheetPdf::abr()` arma la semilla con `crc32($caseId . '|' . $lado .
'|' . $i)`, `$i` el ÍNDICE dentro de la lista ya duplicada -- las dos
réplicas de un mismo nivel quedan con índices distintos, así que su ruido
sale distinto (se parecen, no son la misma pasada dibujada dos veces) y el
PDF sigue siendo reproducible (mismo caso -> mismo PDF byte a byte, ver
test nuevo).

**Ojo con el PRNG:** el primer intento usó un finalizador tipo Murmur3
(XOR + multiplicar por una constante de 32 bits) y PHP tiraba warnings
"not representable as an int" -- el producto de dos enteros de 32 bits se
pasa de los 64 con signo de un int de PHP en la mitad de los casos, cae en
punto flotante, y el `&` que sigue explota. Cambiado a un LCG de 32 bits
(Numerical Recipes, `estado = (estado*1664525 + 1013904223) % 2^32`): el
producto más grande que hace (2^32 * 1664525 ≈ 7*10^15) no se acerca ni de
lejos al límite de un int de 64 bits.

Tests: bloque nuevo en `tests/test_case_sheet_pdf.php` -- SN10/VII
(signo, proporción, orden de latencias), efecto de tasa (cero en RATE_REF,
neural degrada más que normal a la misma tasa), ruido (misma semilla =
mismo trazo, semillas distintas = trazos distintos, la diferencia es chica
frente a la señal) y reproducibilidad end-to-end (mismo caso, mismo PDF
byte a byte). Verificado además renderizando a PNG con `pdftoppm`: se ve
el valle+bump después de la V, las dos réplicas de un mismo nivel ya no
son idénticas a simple vista, y sigue en 6 páginas.

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

### Rangos de compliance y presión por letra (2026-09-11)

Los rangos que sortea la app venían mal y la ficha los imprimía tal cual:

- `Cs` sorteaba 0,01 a 1,3 mL, o sea una C normal con nombre de rígida: la
  ficha informaba "Cs, 0,01 a 1,30 mL" y dibujaba 0,66 mL, indistinguible de
  una C. Ahora `As` y `Cs` van 0,10 a 0,30 mL (rígidas de verdad) y no se
  solapan con `A`/`C`, que llevan la compliance normal 0,3 a 1,6 mL.
- El pico de `C`/`Cs` llegaba a -400 daPa, que es el borde mismo de la
  ventana de barrido: no quedaba pico que leer ni en la app ni en la ficha.
  Ahora va de -250 a -110 daPa.
- `Ad` llegaba a 4,0 mL. Topa en 3,0: igual queda sobre la escala de 2 mL y
  por eso la ficha lo rotula "pico sobre 2 mL, fuera de escala" --aviso que
  el PDF ya tenía y que ahora también muestra el editor.

Los tres rangos viven en tres copias (`FORMAS_JERGER` en
`src/impedanciometria/z_generator.py`, `CaseCharts::FORMAS_TIMPANOGRAMA`,
`SHAPES` en `public/js/case/tympanogram.js`) y `test_charts_vs_js.php` ahora
compara las tres --antes sólo comparaba PHP contra JS, que era por donde se
había colado el desfase.

La gradiente fija se arregló el mismo día: el ancho de la curva pasó a ser
función de la letra (`ANCHOS_JERGER`, en TW = ancho a media altura), en vez
de los 200 daPa fijos que daban 0,85 en cualquier curva con pico. Queda
A/As 80 daPa (la rigidez baja el pico, no lo angosta), Ad 60 (disyunción:
pico alto y en punta), C 100 y Cs 160 (la redondeada de la retracción con
efusión incipiente). El ancho es fijo por letra y no sorteado a propósito:
la ficha anticipa la gradiente que el alumno va a leer, y eso sólo se puede
prometer si no cambia entre barridos. Ahora el equipo informa 0,31 / 0,31 /
0,07 / 0,50 / 0,78.

El ancho viaja en el dataset (índice 6) porque al recargar una curva
guardada `Z.preCharger` la reconstruye con `manual=True` y ahí ya no hay
letra de dónde sacarlo.

Y la curva impresa de la ficha dejó de tener su propio ancho: se deriva del
mismo TW con `w = TW / (2 ln 2)` (`CaseCharts::anchoImpreso`). La forma
sigue siendo distinta a propósito --ápice en punta contra coseno alzado--
pero el ancho es un hallazgo y tiene que ser el mismo en la ficha y en la
pantalla. Por eso siguen siendo dos gradientes y dos filas.

- [ ] El sentido de la gradiente está invertido respecto de la clásica: acá
      1 es una curva ancha y 0 una en punta, y la de Brooks es al revés
      (`1 - esto`). No se tocó porque cambia lo que el alumno lee y la
      convención la define el docente, pero dar vuelta la resta en
      `Z_225._calc_gradient`, `Z.move` y `CaseCharts::gradienteDe` es todo
      lo que hace falta.

## Otoscopia: cono del espéculo e informe por cuadrantes (2026-09-11)

La ventana de otoscopia pasó a tener dos pestañas. "Otoscopio" es lo de
siempre (las dos fotos tapadas salvo el círculo que sigue al mouse) más dos
botones de tamaño de cono: pediátrico (radio 42 px, lo que se veía hasta
ahora) y adulto (84 px, el doble de diámetro). "Informe" es nueva: el
esquema de la membrana timpánica por oído, con los cuatro cuadrantes y la
pars flácida clickeables, una paleta de ocho hallazgos, las casillas del
CAE y observaciones libres.

El esquema y las claves (`anterior_superior`, `perforation`, `cae_cerumen`,
…) son los de OtoReport (proyecto aparte, `src/components/otoscopy/`) a
propósito: es la misma herramienta que el alumno va a usar en clínica, y
así un informe de LabSim se puede leer con lo que ya existe allá.

Decisiones que se tomaron sin preguntar:

- El informe viaja por el camino que ya existe para ABR/EOA/VEMP
  (`report_upload.php`, tabla `reports`) con un tipo nuevo `OTOSCOPIA`, y
  el docente lo ve como PDF desde admin/chat_detail.php igual que los
  otros. La alternativa era una tabla propia y una vista HTML aparte:
  misma información, el doble de superficie nueva.
- No se suben imágenes con este informe: lo que el alumno informa son las
  marcas, y la foto del caso ya la tiene el backend (`OtoscopiaPhoto.php`).
- El CHECK de `reports.tipo` no se puede ampliar con ALTER TABLE en
  SQLite: `Db::migrateReportsOtoscopiaIfNeeded()` reconstruye la tabla
  conservando los id (el PDF y las imágenes en disco se nombran a partir
  de `reports.id`). Corre desde admin → Base de datos → Aplicar schema.
  **Hasta que eso no se corra en el hosting, subir un informe de otoscopia
  falla con CHECK constraint.**

La subventana del MDI pasó de 520x340 a 940x580 y dejó de tener máximo
(`Layout::APPS['OT']`, `fix = [false, true]`): con dos pestañas y el
esquema por oído no entraba nada. El informe se acomodó para que quepa ahí
--esquema y paleta lado a lado, CAE en tres columnas-- y queda en 908x517
de mínimo. Como el layout viene del backend, esto solo cambia cuando se
despliega `Layout.php` y el cliente refresca su cache.

Los visores crecen con la ventana (Expanding), así que el círculo del cono
dejó de medirse en px y pasó a ser fracción del lado menor del visor
(0,19 pediátrico / 0,38 adulto): los 42 px de antes, sobre un visor de
220 px, eran ese 19%, pero con la ventana grande habrían dejado ver una
porción cada vez menor de la foto.

- [ ] Falta probarlo contra el backend real: el guardado se probó sin
      sesión (dice "no hay sesión iniciada con el servidor") y el PDF con
      el builder directo, no con una atención de verdad.
- [ ] No hay otoscopía neumática (movilidad de la membrana) ni checklist
      de hallazgos de membrana sin localización, que OtoReport sí tiene.
      Se dejó fuera porque el módulo de LabSim no simula insuflación.
- [ ] El informe no se guarda local: si el alumno lo llena sin conexión y
      cierra la atención, se pierde (sube best-effort, como los demás
      módulos). Distinto de ABR/EOA, ahí el informe al menos queda en
      pantalla para reintentar.

## Consola: los volcados de depuración solo para docente (2026-09-11)

Al empezar a atender, el impedanciómetro imprimía el caso entero
(`Z.preCharger` → `print(self.data)`: umbrales, letra del timpanograma,
volumen) y el motor de respuestas del paciente iba imprimiendo umbrales,
LDL y decisiones a medida que el alumno estimulaba. Para el alumno eso es
la respuesta del ejercicio servida antes de medir, y no alcanza con que la
consola no se vea: todo lo que pasa por `print()` queda además en el log
local (`core/Logger.py`).

`helpers.debug_print()` imprime solo si la sesión guardada es docente/admin
(lee `session.json`, cachea el permiso y lo invalida en
`reset_backend_session()`, que corre en cada login). Sin sesión no imprime:
el criterio seguro es callar. Se pasaron a `debug_print` los volcados de
`Z.py`, `h_z.py`, `response.py`, `Fowler.py` y el de la ficha en
`Agenda.py`.

- [ ] Los `print()` de los módulos de examen que quedan (ABR, EOA, VEMP)
      son mensajes de error, no volcados de datos, y siguen saliendo para
      todos. Si algún día imprimen datos del caso, tienen que pasar por
      `debug_print` también.

## Otoscopia: varios hallazgos por cuadrante (2026-09-11)

El informe guardaba un hallazgo por cuadrante (`cuadrantes[clave] = "x"`),
así que el segundo click pisaba al primero. En una misma zona se encuentra
más de una cosa --una perforación con timpanoesclerosis alrededor, una
retracción con placa-- y eso se estaba perdiendo.

Ahora cada cuadrante guarda una lista, y los hallazgos se dibujan según
qué clase de marca son (`TIPO_HALLAZGO` en OtoscopiaInforme.py):

- **De área** (retracción, efusión, timpanoesclerosis, colesteatoma,
  inflamación, miringitis): rellenan el cuadrante. Con varios, los 90° se
  reparten en franjas iguales -- con uno solo queda igual que antes. En la
  pars flácida son bandas verticales: un pie dentro de ese óvalo no se
  leería.
- **Puntuales** (perforación, tubo): marcador encima del relleno, a 0.78r
  para no caer sobre las siglas AS/AI/PS/PI, abiertos en abanico si hay
  más de uno. El tubo va como anillo y la perforación como disco: con dos
  discos del mismo tamaño y distinto color no se distinguen en el esquema
  chico.

La clasificación área/punto la decidió el código, no el docente: es cómo
se dibuja, no una afirmación clínica. Si alguna tiene que cambiar de clase,
es una línea en `HALLAZGOS`.

Click suma al cuadrante; volver a marcar el mismo hallazgo lo saca; sin
hallazgo elegido, el click vacía el cuadrante (está en el tooltip del
esquema). Al pasar el mouse, el tooltip dice qué hay marcado ahí: con
varios hallazgos encimados el dibujo solo no alcanza.

`ReportPdfBuilder::otoscopiaBody` acepta lista o string suelto, para que
los informes ya subidos con la primera versión sigan imprimiendo sus
hallazgos en vez de salir en blanco.

Los botones de la paleta son la leyenda del esquema, así que llevan el
mismo símbolo con que se dibuja el hallazgo (■ relleno de área, ● disco,
○ anillo) además del color, con el borde en 3 px para que el color se lea.
`glifo_hallazgo()` tiene que seguir a `_dibujar_marcador()`: si una marca
cambia de forma, cambian las dos. Los botones quedaron más anchos y la
subventana pasó de 940 a 1000 px (`Layout::APPS['OT']`).

## Consumo de la API del LLM (2026-09-12)

DeepSeek **no expone ningún endpoint de consumo**: su API solo devuelve el
saldo que queda (`GET /user/balance`), y el desglose por día o por modelo
vive únicamente en su panel web. Por eso la cuenta la lleva LabSim, llamada
por llamada, con el bloque `usage` de cada respuesta -- tabla `llm_usage` y
`src/LlmUsage.php`, panel en Admin -> IA Paciente.

Lo que se anota por llamada: tarea (`chat_paciente`, `sala`, `anamnesis`,
`oirs`, `prueba`), modelo, proveedor, curso, alumno, el corte de prompt
entre cache hit y miss, respuesta, razonamiento, total, la franja horaria y
si el texto salió usable.

Sobre el **horario diferido**: DeepSeek cobra precio pleno solo de lunes a
viernes, 01:00-04:00 y 06:00-10:00 UTC; el resto vale la mitad. En Chile
esa franja cae de madrugada, así que todo el horario de clases ya paga la
tarifa rebajada sin que haya que hacer nada. Se registra igual la ventana de
cada llamada porque el precio depende de CUÁNDO se hizo, y calcularlo
después con la franja en que uno mira el panel daría cualquier cosa.

Decisiones que quedaron tomadas, por si alguna hay que revisar:

- **Se guardan tokens, no plata.** El costo se calcula al mostrar con las
  tarifas de `llm_config` (tres: cache hit, cache miss y respuesta, en USD
  por millón, a precio pleno). Corregir una tarifa mal escrita arregla el
  histórico entero. Sin tarifas cargadas el panel cuenta tokens y no inventa
  ningún precio por defecto.
- **El prompt va separado en cache hit / miss.** Es lo que decide la
  factura: un token que pegó en cache cuesta unas 50 veces menos. Si el
  proveedor no reporta el corte, todo entra como miss -- de más, nunca de
  menos.
- **Una sola tarifa para todos los modelos.** Si conviven dos modelos con
  precios distintos (el general y el de anamnesis), el costo es una
  aproximación; el panel lo dice en la tabla por modelo.
- **Los días se cortan a medianoche hora de Chile**, no en UTC: con el corte
  en UTC "hoy" arrancaba a las 21:00 del día anterior. El desfase de una
  hora del horario de verano mueve una llamada de borde entre dos días, no
  el total, y no se persigue.
- **Retención de 365 días** (`LlmUsage::RETENCION_DIAS`), purgada al abrir el
  panel y no en cada INSERT: la limpieza no tiene urgencia y el camino del
  chat del alumno no debería cargar con un DELETE que no le sirve.
- **La llamada se anota aunque el texto no sirva** (`ok = 0`). El caso más
  caro de todos es el modelo de razonamiento que gastó miles de tokens
  pensando y devolvió `content` vacío: verlo subir es la señal de que hay que
  tocar el máximo de tokens.
- **`registrar()` nunca lanza.** Quedarse sin la estadística es molesto;
  cortarle la conversación a un alumno por no poder escribir una fila de
  contabilidad sería peor.
- Sin FK a `courses`/`users` en `llm_usage`: es contabilidad, y no tiene que
  bloquear el borrado de un curso o un alumno.

Pendiente:
- [ ] **Cargar las tarifas reales** en Admin -> IA Paciente (hoy quedan en 0,
  así que el panel muestra tokens y no costo).
- [ ] **Probarlo en el backend real**: nada de esto corrió contra la base
  viva -- acá no hay `pdo_sqlite` (solo `php -l`, balance de tags y el SQL
  validado aparte con `sqlite3`). Antes de mirar el panel hay que aplicar el
  schema en Admin -> Base de datos.

## Rediseño de la gestión de cursos en el backend (2026-09-12)

`admin/courses.php` llegó a 937 líneas en una sola vista de scroll: identidad,
tabla de alumnos, docentes, tablero de grupos, módulos, normativa ABR,
normativa VEMP y área de pruebas, todo apilado. Es insuficiente (no muestra
ningún **estado** del curso) y repetitivo:

| Repetición | Dónde |
|---|---|
| El roster dos veces | tabla "Alumnos" y tablero "Grupos" listan los mismos alumnos en la misma página |
| Normativa copy-paste | el bloque ABR y el VEMP son ~210 líneas gemelas (POST + render); la audiometría por curso (sección "Parámetros de audiometría configurables por curso") sería el tercero |
| Control de acceso | `require_course_access` clonada en `courses.php`, `inbox_send.php`, `group_move.php` y `agenda.php` |
| Selector curso -> grupo -> alumno | reimplementado en `agenda.php` y en `inbox_send.php` |
| N+1 en la lista de cursos | `Courses::teachers()` + `Courses::students()` por cada fila del `foreach` |

Decisión de diseño: **el tablero de grupos es el roster**. La tabla de alumnos
se elimina; lo único que aportaba y hay que conservar es el username, el
origen de Moodle, "quitar del curso" y la matrícula de candidatos.

### El tablero como única vista de personas

- Columnas: "Sin grupo" + un grupo cada una. La tarjeta del alumno lleva
  nombre, username en chico, badges de avance (citas pendientes / atendidas /
  última actividad) y menú (ver ficha en `student.php`, quitar del curso).
- Panel lateral "Matricular", colapsado: buscador, candidatos
  (`Courses::enrollableStudents()`) con los chips de origen Moodle que ya
  existen, alta manual y alta por texto. **Arrastrar un candidato al tablero
  matricula y asigna grupo en un solo gesto** (mismo `group_move.php` con
  `enroll=1`).
- Selección múltiple en el tablero: mover a grupo, quitar, generar códigos,
  exportar CSV.
- "Repartir en N grupos": crea los grupos y distribuye a los que están sin
  grupo. Hoy hay que crearlos de a uno y arrastrar cuarenta veces.
- Renombrar grupo en línea (`Courses::renameGroup()` ya existe y no está
  cableado a ninguna UI).

### El curso como hub con pestañas

`course.php?id=N&tab=...`, cada pestaña un partial en `views/course/_*.php` y
el POST centralizado en `src/CourseAdmin.php` (mismo patrón que el refactor de
`case_create.php`):

1. **Resumen** (nuevo): checklist de "curso listo" (módulos elegidos, al menos
   un docente, alumnos matriculados, grupos, citas futuras, LTI vinculado),
   próximos 7 días de agenda y alumnos sin actividad. Cada ítem enlaza a su
   pestaña.
2. **Personas**: el tablero de arriba, más docentes.
3. **Módulos y parámetros**: el checklist actual más las normativas unificadas.
4. **Agenda del curso**: `agenda.php` filtrada.
5. **Pruebas**: demo y limpieza de datos de prueba (ya existe).
6. **Vínculos**: contexto LTI (hoy vive en la vista de lista, donde no se
   encuentra).

### Un registro para las normativas por curso

`src/CourseParams.php` con la definición declarativa de cada key:

```php
'normative_data.abr' => [
    'module' => 'ABR', 'label' => ..., 'help' => ...,
    'shape' => [grupo => [campo => ['type' => 'number', 'step' => 0.0001, 'min' => 0]]],
    'defaults' => [...],
]
```

Un solo renderer (`views/course/_params.php`) y un solo handler genérico
(parseo, validación de rango, reemplazo completo del override, "volver a
default") sirven a ABR, VEMP y a la audiometría cuando llegue: agregar un
módulo pasa a ser una entrada en el registro, no otro card. Los defaults hoy
están copiados a mano del `normative_data.json` del cliente -- va un test que
falle si divergen (mismo criterio que `test_php_baseline.php`).

### Contexto de curso en el header

Selector "Curso: X" en `_layout.php` guardado en sesión; agenda, fichas,
dashboard y bandeja leen ese contexto y borran su propio `<select>`. Para un
docente con un solo curso, el selector no aparece.

### Fases

- [x] **F0** (2026-09-12): `Courses::canAdminister()` / `assertAdministers()`
      única (courses.php, inbox_send.php, group_move.php, agenda.php),
      `Courses::listWithCounts()` contra el N+1 de la lista, registro
      `src/CourseParams.php` + `views/course/_params.php` (los editores de
      ABR y VEMP salen del registro; `tests/test_course_params.php` compara
      los defaults contra los JSON del cliente y cubre `parse()`). De yapa:
      `rename_group`/`delete_group` ahora verifican que el grupo sea del
      curso (`groupBelongsTo()`), que era un agujero -- el `group_id` venía
      del POST sin comprobar.
- [x] **F2** (2026-09-12): el tablero es el roster. Se eliminó la tabla de
      alumnos; las tarjetas llevan usuario, citas asignadas, cerradas y
      última atención (`Courses::rosterProgress()`), link a la ficha y
      quitar del curso. Panel de candidatos al costado: arrastrar matricula
      (`group_move.php` con `enroll=1` -> `Courses::enrollStudent()`),
      marcar + botón para tandas, chips por curso de Moodle, alta manual y
      pegar lista. Además "repartir en N grupos"
      (`splitUngroupedIntoGroups()`) y renombrar grupo en línea. El JS salió
      a `public/js/course/board.js`.
- [x] **F1** (2026-09-12): `courses.php` pasó de 937 a ~195 líneas de
      controlador; la vista vive en `views/course/_{tabs,resumen,personas,
      modulos,agenda,vinculos,pruebas,lista,params}.php` y todo lo que
      escribe, en `src/CourseAdmin.php`. Cada pestaña carga solo sus datos
      (el tablero de personas es lo caro y no se arma para mirar la agenda).
      Dos decisiones al pasar: (a) la URL sigue siendo
      `courses.php?id=N&tab=...` y no `course.php`, para no romper los links
      que ya existen; (b) después de un POST se vuelve a la pestaña de donde
      salió el formulario, deducida de la acción
      (`CourseAdmin::TAB_BY_ACTION`), en vez de meter un `<input hidden
      name="tab">` en los diecisiete formularios. `tests/test_course_admin.php`
      cuida las dos costuras: acción sin pestaña y pestaña sin partial.
- [x] **F3** (2026-09-12): pestaña Resumen con `src/CourseOverview.php` --
      checklist de "curso listo" (docente, alumnos, módulos, citas por
      delante, y grupos/Moodle como opcionales), próximos 7 días de agenda y
      alumnos que todavía no atendieron a nadie. La ventana de fechas se
      resuelve en PHP porque `appointments.fecha` es texto `dd-MM-yy`; hay
      test, incluido el cruce de año.
- [x] **F4** (2026-09-12): curso en foco en el header
      (`admin_course_context()` en `_layout.php`, guardado en sesión,
      `?curso=N` / `?curso=todos`). Lo leen agenda (borró su `<select>` de
      curso; quedan los de grupo y alumno), bandeja de entrada (borró el
      suyo) y dashboard (antes mezclaba las dos cohortes de un docente con
      dos cursos en el mismo promedio). Entrar a la página de un curso lo
      pone en foco. **Fichas clínicas queda afuera a propósito**: una ficha
      no pertenece a un curso, se comparte, y esconderla por estar parado en
      un curso haría creer que hay que volver a armarla.
- [ ] **F5**: ciclo de vida -- `code`/`term`/fechas en `courses`, clonar curso
      para el semestre siguiente, purga de datos por semestre, export CSV del
      roster. **A conversar antes de tocar nada** (2026-09-12): cómo se llama
      un periodo acá, si "clonar" arrastra casos/agenda o solo la
      configuración, y qué pasa con los datos del semestre viejo.

Se arrancó por F0 y F2 (lo que estorbaba); F1 después, porque partir en
pestañas encima del código duplicado hubiera sido mover basura de lugar.
Nada de esto se probó todavía en el navegador (acá no hay `pdo_sqlite`): los
partials sí se renderizaron en seco con datos de mentira y `E_ALL` como
excepción, que es lo que cazó una clave `origin` faltante en las tarjetas.

## Bandeja de entrada: lo que reciben los alumnos (2026-09-12)

`admin/inbox_send.php` lista de corrido todo lo que llegó a la bandeja de
los alumnos del docente (avisos de OIRS + mensajes de cualquier docente del
curso), con filtros por alumno, tipo, leído y texto. El ámbito es
`Courses::studentScopeSql()` -- única copia de "sus alumnos", con test
(`tests/test_inbox_scope.php`): un docente nunca ve el buzón de un alumno de
otro curso, ni editando `course_id` o `alumno_id` en la URL.

Decisión de tamaño (no había una respuesta obvia): abre en **resumen de 5**
mensajes y, apenas se filtra, muestra **todas las coincidencias** con tope
duro de 500 por página. El tope existe porque un filtro ancho en un curso
grande mandaría miles de filas de una; pasado el tope el listado sigue
completo, paginado.

- [ ] Probar en el navegador (acá no hay `pdo_sqlite`): las consultas sí se
      corrieron contra `sql/schema.sql` en sqlite con datos de mentira.
- [ ] A conversar: "Todos mis cursos" usa `teacherCourseIds()`, que incluye
      cursos inactivos -- o sea también alumnos de cursos archivados. Queda
      así a propósito (es historial), pero depende de F5.

## Fichas Clínicas: orden de botones y Eliminar como ícono (2026-09-15)

Feedback del usuario sobre `patients.php` (biblioteca de fichas): no se
entendía la diferencia entre "Reagendar" y "+ Otra cita", el orden de los
botones no era lógico (Editar debería ir primero) y "Eliminar" -- un botón
de texto del mismo tamaño que los demás, pegado al lado -- era fácil de
apretar de refilón (borra el caso completo con citas/rondas/atenciones,
sin deshacer).

- **Orden nuevo:** Editar ficha → Agendar/Reagendar → + Otra cita → PDF →
  PDF estudio → Eliminar (al final, separado).
- **Diferencia aclarada con `title`:** "Reagendar" cambia la fecha/hora de
  la cita que YA tiene (la reemplaza); "+ Otra cita" agrega una cita nueva
  SIN tocar la existente (para una segunda ronda). No cambió el
  comportamiento, solo el texto del tooltip.
- **Eliminar pasa a ícono** (`.action-btn-icon` en `patients.css`, nuevo):
  un tacho chico, gris, con más margen a la izquierda que separa del resto
  de la fila, mudo hasta el hover/foco (ahí se pone rojo). Es el primer
  botón-ícono del panel admin -- no había ningún precedente en el resto de
  `public/admin/*.php` (todos los "Eliminar" de ahí son botones de texto
  `.danger`) -- así que si se homogeniza el resto más adelante, el patrón
  ya está acá para copiar.

**Corrección posterior (mismo día):** el usuario volvió sobre esto -- ni
con el tooltip aclarado tenía sentido tener DOS botones para crear citas
en la misma fila. Se colapsaron "Reagendar"/"Agendar" y "+ Otra cita" en
un solo botón **Agendar**, que siempre apunta a
`agenda.php?schedule=<id>` (sin `force_round`). La decisión de
reemplazar la cita existente vs. agregar una ronda nueva se mueve
adentro del modal de `agenda.php`, que YA la tenía resuelta: cuando el
caso tiene cita, el modal se abre en modo "editar esta cita" y ofrece
un link "agendar una cita nueva →" (línea ~679, con `force_round=1`) sin
tocar la existente. No hizo falta tocar `agenda.php` -- el fork ya
vivía ahí, solo sobraba la entrada duplicada desde `patients.php`.

## Ficha de estudio: anamnesis redactada con IA como ficha clínica real (2026-09-15)

Pedido del usuario: la página 1 de la ficha de estudio ("Quiénes vienen a
la consulta" y el resto de la anamnesis) se leía como campos de
formulario, no como una ficha clínica real. Se acordó explícitamente NO
mandar esto a través de un LLM en cada pedido -- se genera **una sola
vez** con IA y se **cachea en el caso**; las fichas siguientes reusan lo
guardado.

**Precedente que se reusó, no se reinventó:** `AnamnesisDraft.php` ya
hace algo parecido (convertir hallazgos del caso en prosa clínica vía
`LlmChat::reply()`), pero para OTRO fin -- inventa antecedentes plausibles
para que el docente arme el caso. Lo nuevo (`EstudioRedactor.php`) no
inventa nada: toma los hechos que el docente YA decidió y los redacta
como prosa. Reusa el modelo/presupuesto/reintento de `AnamnesisDraft`
(`maxTokens()`, `model()`, `retryBudget()`) en vez de agregar un campo de
configuración aparte -- es la misma categoría de tarea (varios párrafos,
capaz con un modelo de razonamiento de por medio).

**Tres decisiones tomadas con el usuario antes de programar** (por
`AskUserQuestion`, no asumidas):
1. **Sin verificación docente** (a diferencia de `Anamnesis.ia`, que
   bloquea agendar hasta que se verifica): el docente es el único que
   puede pedir esta ficha igual, así que si algo sale raro lo nota él
   mismo. Un paso de verificación de más no aporta acá.
2. **Invalidación automática por hash**, no un botón "Regenerar": se
   hashean los HECHOS de origen (`EstudioRedactor::fuente()`), no la
   redacción; si el docente edita el caso y algo del hash cambia, la
   ficha de estudio se regenera sola la próxima vez que se pida, sin que
   nadie tenga que acordarse.
3. **Diseñado extensible**: la clave en `cases.data` es
   `EstudioRedaccion.<sección>` (hoy solo `'clinica'`, la constante
   `EstudioRedactor::SECCION_CLINICA`) para poder sumar otras secciones de
   la ficha de estudio a este mismo mecanismo más adelante sin rehacer el
   cacheo.

**Cómo queda armado:**
- `EstudioRedactor::fuente($data)`: arma los hechos que puede ver el
  modelo -- el MISMO recorte "seguro para el alumno" que ya usa
  `CaseSheetPdf::clinica()`/`sala()` en la ficha de estudio (antecedentes
  marcados, medicamentos/cirugías/otros, acúfeno vía
  `CaseSheetPdf::acufeno()` -que pasó a `public`-, comportamiento general,
  y cada acompañante con su versión/comportamiento -- nunca umbral, tipo
  de patología, disposición, ni conciencia/confiabilidad/interrumpe). Por
  construcción el modelo nunca VE un dato interno: no hace falta
  pedírselo por prompt, ese dato no llega al mensaje.
- `EstudioRedactor::hash($fuente)`: sha256 de esos mismos hechos.
- `EstudioRedactor::generate()`: arma el mensaje (los hechos en JSON) y
  llama a `LlmChat::reply()` con el `SYSTEM_PROMPT` (pide un relato de
  ficha clínica real, en 2-4 párrafos, SIN agregar ni un hecho que no
  esté en lo que se le dio, sin mencionar umbrales/dB/diagnóstico -- esto
  último es cinturón y tirantes, ya es imposible por construcción de
  `fuente()`). Responde JSON `{"texto": "párrafo1\n\npárrafo2"}`, mismo
  pelado de ``` que `AnamnesisDraft::parse()`.
- `EstudioRedactor::ensureFresh($caseId, $data, $usuarioId)`: el único
  punto de entrada del endpoint. Compara el hash guardado contra el
  actual; si coinciden y hay texto, no hace nada (deja `$data` como
  está). Si no, intenta generar y persistir (`Cases::actualizarDatos()`,
  nuevo método -- mismo criterio que `Cases::snapshotBeforeAppointmentDelete()`:
  NO toca `updated_by`, porque quien escribe es el sistema, no un
  docente editando la ficha). **Si el LLM falla por lo que sea (sin
  api_key, sin red, proveedor caído), atrapa el `Throwable` y devuelve
  `$data` sin tocar** -- ni rompe la ficha ni borra un texto viejo que ya
  hubiera. Verificado con test: con hash desactualizado y sin LLM
  configurado, el texto viejo sigue ahí.
- `CaseSheetPdf::clinica()`: si `$estudio` y hay
  `data.EstudioRedaccion.clinica.texto`, lo imprime como prosa corrida
  (`explode("\n\n", ...)` + un `parrafo()` por cada uno, bajo el
  subtítulo "Historia clínica") y OMITE el detalle mecánico (campos de
  Historia, aviso de Borrador IA, "En la consulta", `sala()` entera). Sin
  texto guardado, cae al detalle mecánico de siempre -- la ficha NUNCA
  depende de que el LLM haya contestado. La ficha DOCENTE nunca usa la
  redacción, tenga o no el caso una guardada: sigue con el detalle
  completo de siempre (verificado con test).
- Otoscopia (fotos + texto por fase) **no se tocó**: son fotos reales con
  su propio texto por fase, ya se lee como hallazgo de examen, no como
  formulario -- no era lo que el usuario señaló como el problema.

**Sin ciclo de `require`:** `EstudioRedactor.php` sí requiere
`CaseSheetPdf.php` (para reusar `acufeno()`), pero `CaseSheetPdf.php` NO
requiere `EstudioRedactor.php` de vuelta -- la clave `'clinica'` va
escrita a mano en `clinica()` con un comentario que dice que tiene que
coincidir con `EstudioRedactor::SECCION_CLINICA`, en vez de referenciar
la constante (que sí crearía el ciclo).

**Pendiente:** probar en el navegador con un caso real y una API key de
verdad configurada (acá no hay red ni `pdo_sqlite`; todo lo de arriba se
probó con `EstudioRedactor::fuente()/hash()/parse()` y con
`CaseSheetPdf::build()` inyectando una redacción ya guardada a mano, no
con una llamada real al LLM).

## Ficha de estudio: párrafos de la anamnesis redactada, justificados (2026-09-15)

La prosa de `EstudioRedactor` (arriba) salía con `textBlock()` alineada
solo a la izquierda, con el borde derecho irregular -- se veía mal al
lado de una ficha con tablas de bordes rectos.

- `MiniPdf::textBlock()` suma un parámetro `bool $justificado = false`.
  Con `true`, cada línea salvo la última del bloque se dibuja con
  `drawJustifiedLine()` (nuevo, privado): usa el operador `Tw`
  (espaciado entre palabras) del content stream de PDF para estirar la
  línea hasta `$maxWidth` exacto, y lo resetea a 0 antes del `ET` --si
  no, el espaciado le queda pegado a texto no relacionado que se dibuje
  después en el mismo bloque. Una línea sin espacios (no hay dónde
  meter `Tw`) cae al dibujo plano de siempre.
- `CaseSheetPdf::parrafo()` suma el mismo parámetro y lo pasa directo.
- Solo se usa en `clinica()`, en el loop que imprime los párrafos de
  `EstudioRedaccion.clinica.texto`: `$this->parrafo($p, 8.5, null, null,
  true)`. Ningún otro `parrafo()` del documento cambió --la ficha
  docente (sin redacción IA) sigue con el detalle mecánico de siempre,
  sin justificar.
- Verificado con `pdftoppm` (borde derecho parejo, última línea de cada
  párrafo suelta) y con la suite completa (3740 asserts, sin
  regresión).

## Deterioro tonal: "/" en vez de "0" (2026-09-15)

Primer intento: tratar solo la clave AUSENTE (`Carhart`/`Stat`/`Rosemberg`
no existe en el JSON, caso de antes de esta prueba) como "no
administrado", asumiendo que 0 en una celda presente era un hallazgo real
("sostiene el tono de inmediato"). **El usuario corrigió la premisa
clínica completa:** el valor que se guarda es el nivel al que se
estimuló, y ESE nunca es 0 -- si fuera 0 no se habría hecho la prueba. La
ayuda del formulario que decía "0 = sin deterioro" estaba mal.

- `CaseSheetPdf::supraliminares()`: la regla es por CELDA, no por clave --
  cualquier valor `<= 0` (sea porque la clave no existe, sea porque el
  campo del formulario nunca se tocó) imprime "/" en vez del número,
  mismo símbolo que ya usan las tablas de enmascaramiento para "no
  aplica". Esto incluye a propósito los casos AUTO-DERIVADOS del perfil
  auditivo: `CaseProfile::toneDecay()` sigue devolviendo 0 para oídos
  normales (no se tocó, es el motor el que mira las fórmulas, no la
  ficha), así que un caso derivado con oído sano va a mostrar "/" donde
  antes mostraba "0" -- tradeoff explícito, aceptado por el usuario vía
  AskUserQuestion en vez de agregar un flag "administrado" aparte.
- Verificado con `pdftoppm` sobre el fixture de test (que ya trae ceros
  reales mezclados con valores reales) y con la suite completa (3740
  asserts, sin regresión).

## Weber: revisado, ya estaba correcto (2026-09-15)

El usuario preguntó por el color/lado de las flechas de Weber. Se
verificó con render (`pdftoppm`): flecha izquierda roja = lateraliza a
OD, flecha derecha azul = lateraliza a OI -- ya coincidía con la
convención pedida, sin necesidad de cambios en `CaseSheetPdf::acumetria()`.

## Weber: flechas grises en "sin lateralización" (2026-09-15)

En el caso "centrado" (sin lateralización) `acumetria()` dibujaba las DOS
flechas en gris (`GRIS_SUAVE`), reservando el color OD/OI solo para
cuando lateraliza. El usuario lo notó: cada flecha debe ir siempre del
color de su lado, lateralice o no -- el color identifica el LADO de la
flecha (posición fija: izquierda=OD, derecha=OI), no si ese lado "ganó".

- `CaseSheetPdf::acumetria()`: la flecha izquierda siempre
  `CaseCharts::COLOR_OD`, la derecha siempre `CaseCharts::COLOR_OI`,
  se dibuje o no dependía ya de si lateraliza o está centrado (sin
  tocar esa condición). Verificado con `pdftoppm` y con la suite
  completa (3740 asserts, sin regresión).

## EstudioRedactor: sin juicios de valor sobre acompañantes (2026-09-15)

El redactor con IA (ver sección de arriba) sacaba prosa como "la madre...
se muestra conversadora, se va por las ramas y hay que traerla de
vuelta" -- un juicio de valor sobre un TERCERO (el acompañante), no un
hallazgo del paciente que es el sujeto de la ficha. El campo
`comportamiento` de un acompañante existe en `Sala` para que el LLM DE
LA SALA sepa cómo actuar ese personaje en el chat -- no es contenido
para la ficha clínica.

- `EstudioRedactor::fuente()`: el campo `comportamiento_en_consulta`
  ahora SOLO se arma para la persona con `es_paciente = true`. Un
  acompañante nunca lo recibe -- por construcción, no por instrucción al
  modelo (mismo principio que ya usa el resto de esta clase: el dato
  simplemente no llega al mensaje).
- `SYSTEM_PROMPT`: además, explícito por si el dato volviera a filtrarse
  algún día -- de un acompañante entra SOLO su versión de la historia del
  paciente, nunca un comentario sobre su propia actitud/personalidad en
  la consulta.
- El comportamiento del PACIENTE (si lo hay) sigue entrando, porque es el
  sujeto del procedimiento y sí es clínicamente relevante.
- Cambia el hash de `fuente()`: casos con redacción ya cacheada se
  regeneran solos la próxima vez que se pida la ficha (el mecanismo de
  invalidación ya estaba pensado para esto).
- Verificado llamando `EstudioRedactor::fuente()` con un acompañante con
  `comportamiento` cargado y confirmando que no aparece en el JSON que
  ve el modelo; suite completa sin regresión (3740 asserts).

## Botón manual para regenerar la anamnesis de la ficha de estudio (2026-09-15)

`EstudioRedactor::ensureFresh()` solo regenera si cambian los HECHOS de
origen (hash). No se entera si lo que cambió fue el PROMPT (como la regla
de no opinar sobre acompañantes, arriba) ni sirve si el docente quiere
simplemente probar de nuevo con los mismos hechos porque la redacción
salió mediocre. Pedido explícito del usuario: un botón manual.

- `EstudioRedactor::regenerate($caseId, $data, $usuarioId)`: fuerza una
  redacción nueva IGNORANDO el hash guardado. A diferencia de
  `ensureFresh()`, NO atrapa el error del LLM -- quien aprieta el botón
  necesita saber si falló, no quedarse con la redacción vieja en
  silencio.
- `patients.php`: nueva acción POST `regen_estudio` (case_id), con
  try/catch que arma `$error`/`$success` como el resto de la página.
- UI: menú de "tres puntitos" nuevo por fila (`<details class="row-menu">`,
  sin JS propio -- reusa el mismo cierre-al-clickear-afuera que ya tenían
  los `nav-group` del header, ahora `_layout.php` cierra
  `nav-group, row-menu` genérico) con un único ítem por ahora: "Redactar
  de nuevo anamnesis (IA)". Se eligió menú y no otro botón visible más
  porque la fila ya tiene cinco acciones -- deja espacio para sumar otras
  acciones secundarias después sin volver a amontonar la fila.
- Estilos nuevos en `patients.css` (`.row-menu`, `.row-menu-btn`,
  `.row-menu-dropdown`, `.row-menu-item`), sin CSS nuevo compartido: es
  específico de esta tabla, igual que `.action-btn-icon`.
- Verificado con `php -l` en los tres archivos tocados, suite completa
  (3740 asserts) y una llamada directa a `EstudioRedactor::regenerate()`
  confirmando que propaga la excepción del LLM en vez de un fatal error
  (acá no hay red para probar el camino feliz).

## Otoscopia: sin "Fase N", fotos al doble de tamaño y centradas (2026-09-15)

`CaseSheetPdf::clinica()` imprimía cada fase de otoscopia como una fila
de tabla "Fase N | <hallazgo>" seguida de las dos fotos (108pt de ancho
cada una) pegadas al margen izquierdo. El usuario lo corrigió: "Fase N"
es la lógica interna con la que se PROGRAMÓ el caso (progresión de
hallazgos en el generador), no algo clínico -- y las fotos quedaban
chicas para todo el espacio libre de la hoja.

- El texto del hallazgo (si lo hay) se imprime como párrafo simple, sin
  el rótulo "Fase N".
- `fotosOtoscopia()`: ancho de cada foto pasa de 108pt a 216pt (el
  doble), y el bloque OD/OI se centra en `anchoContenido` en vez de
  arrancar en el margen izquierdo -- `$x = MARGEN + (anchoContenido -
  anchoTotal) / 2`, con `anchoTotal` calculado sobre la cantidad de
  fotos que realmente existan (1 o 2), así que si falta una queda esa
  sola centrada, no descuadrada a la izquierda.
- Verificado con `pdftoppm` generando dos fotos JPEG de prueba en
  `data/otoscopia_photos/` (borradas después, no se suben al repo) --
  salen centradas, simétricas respecto al margen, y el texto sin "Fase
  N". Suite completa sin regresión (3740 asserts).

## Otoscopia: mismo título con franja que el resto (2026-09-15)

`Otoscopia` usaba `subtitulo()` (texto simple, sin franja) como si fuera
una subsección de la anamnesis ("Historia", "En la consulta"). El
usuario lo notó: no es una subsección de la entrevista, es un examen
propio (como la audiometría o la impedanciometría) y debe llevar el
mismo título con franja de fondo (`titulo()`) que todos los demás.

- `CaseSheetPdf::clinica()`: `$this->titulo('Otoscopia')` en vez de
  `subtitulo()`. Reserva por defecto (60pt), sin pasarle una reserva más
  grande pensando en las fotos -- `fotosOtoscopia()` ya reserva su propio
  espacio antes de dibujar, duplicarlo ahí metía a la ficha de prueba en
  una séptima página de más (falló `test_case_sheet_pdf.php` hasta
  sacarlo: la ficha tiene que seguir siendo generales+anamnesis, tonal,
  impedanciometría, ABR, OEA, VEMP -- 6 páginas fijas).
- Verificado con `pdftoppm` (franja igual a "Perfil auditivo"/"Anamnesis
  y hallazgos clínicos") y suite completa sin regresión (3740 asserts,
  6 páginas).

## Impedanciometría: letra de Jerger más separada de la esquina (2026-09-15)

La letra de Jerger sobre el timpanograma (OD arriba-izquierda, OI
arriba-derecha) quedaba pegada al eje "2.0 mL" y muy cerca del borde del
gráfico. El usuario pidió duplicar el corrimiento hacia el centro (y de
paso, hacia abajo -- mismo margen gobierna las dos direcciones).

- `CaseSheetPdf::impedanciometria()`: `$margenLetra` de 10.0 a 20.0pt.
  Un solo valor controla el desplazamiento horizontal (hacia el centro,
  desde cada esquina) y el vertical (hacia abajo, desde el techo del
  gráfico) -- duplicarlo mueve la letra en ambos sentidos a la vez.
- **Corrección:** con 20.0 la letra de OD ("As") seguía sobre la línea
  del eje izquierdo -- `CaseCharts::plotBox()` corre el marco del
  gráfico `EJE_IZQ = 24.0`pt adentro de `$x`, así que un margen menor a
  eso todavía cae encima del borde. Subido a 35.0pt (deja ~11pt de aire
  antes del marco); OI no tenía este problema (su borde derecho queda
  mucho más cerca de `$x + $ancho` que lo que el margen le resta) pero
  se corre el mismo tanto por usar la misma variable para los dos lados.
- Verificado con `pdftoppm` (antes/después, recorte de cerca del borde
  izquierdo) y suite completa sin regresión (3740 asserts).

## ABR: catálogo real de estímulos y vía ósea que sí cambia el trazo (2026-09-20)

El combo de estímulos del ABR listaba "Chirp" y "Ls-chirp" como si fueran
dos chirps de banda ancha y no existía el NB CE-Chirp LS, que es el
estímulo frecuencia específico que se usa de rutina. Además, por vía ósea
los chirps caían al bloque del click del normativo: el alumno cambiaba el
estímulo y el potencial salía idéntico.

- `STIM_MAP`: 11 estímulos (Click, CE-Chirp, CE-Chirp LS, NB CE-Chirp LS
  500/1k/2k/4k, Burst 500/1k/2k/4k). `STIM_BY_BAND` agrupa los que llevan
  banda (burst y NB chirp) y `stim_key()` arma `<estimulo>_<freq>` para
  los dos. La vía sigue siendo del transductor (Parámetros Avanzados), no
  un ítem del combo: el mismo estímulo por aire y por hueso es otra curva.
- `resources/abr/normative_data.json`: `ls_chirp` -> `ce_chirp_ls` (mismos
  números, solo nomenclatura) y bloque nuevo `nb_ce_chirp_ls` por banda,
  derivado del burst de cada población (adelanto de la V de 0.90/0.55/
  0.30/0.15 ms según banda, menos en las ondas tempranas, y +35%/+25% de
  amplitud). Se generó con script, no a mano.
- `get_baseline_values()`: la cascada de fallback ahora termina en la vía
  AÉREA de la misma población. Los ratios son propiedad del estímulo, no
  de la vía -- sin esto el chirp por vía ósea era el click.
- Compatibilidad: `LEGACY_STIM_LABELS` (rótulos guardados) y
  `LEGACY_STIM_KEYS` (`ls_chirp` en la tabla de umbrales del caso y en la
  normativa por curso). Un caso viejo no puede quedar sin umbral por
  estímulo en silencio: eso es exactamente el bug que se está arreglando.
- Backend: `CaseProfile::STIM_WEIGHTS` / `STIM_NHL_CORRECTION` (NB chirp
  ~5 dB menos de corrección nHL->eHL que el burst de esa banda),
  `CourseParams` (editor de normativa por curso), `CaseSheetPdf`
  (`estimuloLabel`, y `conductual()` ahora SÍ da referencia conductual
  para el NB chirp, que es frecuencial; solo los de banda ancha van con
  "--") y el preview del perfil.
- La tabla de umbrales de la ficha pasó de 7 a 11 filas: se le agregó
  `espacio()` antes de dibujarla (`tablaEn()` no corta páginas) y en la
  versión del docente la primera columna va más ancha con cabecera corta.

**Pendiente (no pedido, anotado acá):**
- El vibrador óseo no tiene techo de salida. En el equipo real son ~45-50
  dB nHL; hoy se puede pedir un ABR óseo de 80 dB y el generador responde.
- La ficha PDF muestra solo los umbrales por vía aérea. El caso ya calcula
  `umbral_por_estimulo_oseo`, así que la tabla ósea es solo maquetación.
- Un override de normativa por curso guardado con la clave vieja
  (`ls_chirp`) se sigue aplicando en el cliente por el alias, pero el
  editor de `normativas.php` no lo muestra bajo "CE-Chirp LS".

## ABR: normativa anclada en bibliografía, con cita (2026-09-20)

El usuario aportó `labsim_backend/resources/normativa/ABR_valores_referencia_latencias_interpico.xlsx`
(483 filas, 27 fuentes). Reglas que fijó: bibliografía más fuerte primero,
cita en todo pero solo donde la ve el DOCENTE, lo que no está publicado se
calcula, y el vibrador óseo llega a 50 dB y eso no es un bug.

**Qué se reancló (cada valor con su fuente, en el JSON y en normativas.php):**

| | antes | ahora | fuente |
|---|---|---|---|
| Click adulto ♀ I/III/V | 1.62/3.68/5.47 | 1.46/3.65/5.54 | F01 Sanfins 2026, n=244 |
| Click adulto ♂ | 1.65/3.85/5.70 | 1.47/3.75/5.68 | F01 |
| Amplitudes adulto (♀) | 0.21/0.37/0.60 | 0.44/0.47/0.54 | F27 Da Silva, n=100 oídos |
| Razón V/I generada | 2.85 | 1.23 | publicada: 1.66 ± 0.89 (F01) |
| Click niño | 1.58/3.78/5.60 | 1.48/3.50/5.50 | F04 Chalak (70 dB, llevado a 80) |
| Click neonato | 2.10/4.70/6.80 | 1.79/4.56/7.00 | F25 Rosa + F07 |
| Click adulto mayor | 1.75/4.00/5.90 | 1.84/3.91/5.84 | F21 Aguilar, n=196 |
| CE-Chirp LS | +3% amplitud | +22%, V −0.08 ms | F24 Cargnelutti, n=60 oídos |
| `LAT_SHIFT_FACTOR` onda I | 0.85 | 1.15 | F26 Hood (serie 80→40) |
| Función L-I bajo 70 dB | 0.3 ms/10 dB | 0.28 (70-50) y 0.50 (<50) | F26 vs F22 Delgado |
| Tasa, onda V 10→90/s | +7.6% | +13.6% | F13 Jiang (publicado 12-15%) |
| Polaridad | ×1.1 a todas las ondas | I ×0.82 y III ×0.85 en condensación | F27 (mismo click, dos polaridades) |
| Vibrador óseo | sin techo | 50 dB nHL (`BONE_MAX_OUTPUT_DB`) | F18, que normaliza a 50/30/10 |

**El hallazgo de fondo (neonato):** lo teníamos al revés. El neonato real
tiene la periferia casi madura (onda I 1.79, contra 1.46 del adulto) y el
centro claramente inmaduro (I-V 5.21 contra 4.08). Nosotros le habíamos
puesto +30% en la onda I y +15% en el interpico. Con la regla de derivación
que entró antes (parte periférica escala con la onda I, parte central con
el I-V), ese error se propagaba a TODOS los estímulos del neonato.

**Lo que se calcula porque nadie lo publica:** ondas II, IV, VI y VII,
microfónica, amplitudes de niño y neonato, toda la vía ósea, el CE-Chirp de
banda ancha (no LS) y los cuatro NB CE-Chirp LS. Regla: conservar la forma
(posición relativa entre las ondas ancladas para la latencia, fracción de la
onda V para la amplitud) y fijar el nivel con lo que sí está publicado.

**Dos trampas que dejó el reanclaje, ya arregladas:** escalar la amplitud
onda por onda contra la tabla vieja dejaba la onda I más grande que la V en
vía ósea (dispara el criterio V/I en todo registro óseo), e interpolar la
amplitud de II y IV por posición las dejaba casi tan grandes como sus
vecinas. Las dos tienen test.

**Dónde se ven las citas:** `admin/normativas.php` (bloque "Fuentes", con n,
protocolo y enlace por fuente, y qué ancla cada población) y la ficha PDF
del docente, bajo la tabla de referencia. En la ficha de estudio y en el
panel del alumno NO aparece ninguna cita: el alumno lee un examen.

**Todo lo que el docente necesita está en el BACKEND, que es lo único que
él ve** -- el repo del cliente no lo abre nunca. Por eso la planilla vive en
`labsim_backend/resources/normativa/` (se descarga desde normativas.php, con
sesión de admin), las citas completas en `src/AbrReferences.php`, y los sets
publicados --Sanfins 2026, Aguilar-Madrid 2015, Hood, pediátrico (Chalak +
Rosa)-- aparecen en el selector de autor del caso junto con los suyos. Un
set publicado cubre solo lo que esa serie publica: el resto lo completa el
default campo por campo, y un set propio con el mismo id lo pisa. El JSON
del cliente conserva solo el ID de fuente por bloque, para no tener la cita
duplicada en dos repos.

**Pendiente:**
- El tramo de 1 a 3 años cae en `child`, que ya tiene valores de adulto;
  F11/F19 dicen que la equivalencia se alcanza entre los 9 meses y los 3
  años.
- Burst de 1-4 kHz: única fuente F23 en dB HL y sin click propio; nuestros
  valores siguen derivados. No usable sin el click de esa misma serie.
- Sexo y edad: nuestro salto ♂/♀ en la onda V (0.14) y el de adulto mayor
  quedaron dentro de lo publicado al reanclar; no hizo falta tocarlos.

## ABR: la forma de la onda cambia con el estímulo (2026-09-20)

Faltaba lo que el alumno ve antes que cualquier número: el burst de 500 Hz
tiene que dar ondas **anchas y romas** y el chirp, angostas. Hasta ahora el
estímulo solo movía latencia y amplitud, así que dos estímulos muy distintos
se dibujaban con la misma forma.

**Un solo motor**: cuánto se desparraman en el tiempo los aportes de la
partición coclear que el estímulo excita. Eso sale del retardo de la onda
viajera (tarde en el ápex, temprano en la base); el burst no lo compensa y
el chirp sí -- por eso el chirp "sincroniza". `STIM_DISPERSION` normaliza ese
desparramo al del burst de 500 Hz y `STIM_COMPENSATION` le resta lo que
compensa cada chirp (banda estrecha 0.5, banda ancha 1.0).

De ahí salen las dos consecuencias, con la misma cuenta:

- **Ancho** (`stimulus_width`, aplicado en `calculate_wave_parameters` junto
  al ensanchamiento por nivel y por desincronía). FWHM medido en el trazo:
  onda V 0.41 ms con click, 0.52 con NB chirp de 500 y 0.63 con burst de
  500; los chirp de banda ancha quedan apenas por debajo del click.
- **Amplitud de las ondas tempranas**. La tabla tenía el burst con la onda I
  **más grande** que la del click (ratios 1.05 a 1.52), al revés de F23
  (Pinto y Matas, n=40): *"con tone burst a 80 dB HL solo se identificó la
  onda V; las ondas I y III estuvieron ausentes en todas las frecuencias"*.
  Ahora la I del burst de 500 queda en 0.049 µV (0.11× la del click) y 2.2
  veces más ancha -- o sea, no se identifica. Se conserva gradiente por
  banda (a 4 kHz la I se sigue viendo) porque esa serie está en dB HL, que
  a 500 Hz es bastante menos nivel de sensación que a 4 kHz.

El NB CE-Chirp LS es el que muestra el argumento completo: misma banda que
el burst, pero la onda I vuelve a 0.146 µV (3× la del burst) y el trazo se
angosta de 1.15 a 0.84 ms. Eso es lo que el alumno tiene que poder ver.

F24 no reporta anchos, así que el afinamiento del chirp de banda ancha
(0.92 en la onda I, 0.96 en el resto) es derivado, no publicado, y está
marcado como tal.

## ABR: el caso registra con qué se construyó (2026-09-20)

Idea del usuario, y corrige algo que yo había planteado mal: no es que al
alumno se lo evalúe contra otro autor --nadie corrige sus marcas, la banda
normativa es ayuda de lectura-- sino que **el caso no dejaba rastro de con
qué set se armó**. Las desviaciones ya viajan con el offset autor-vs-default
adentro (ver `public/js/case/abr.js`, `buildValues`), así que después de
guardar un caso hecho con Hood y otro hecho con Sanfins son
indistinguibles, y la diferencia entre sets es del orden de la desviación
que el docente carga a mano.

Ahora `cases.data['ABR']['autor']` guarda `set`, `label`, `poblacion` y el
**baseline resuelto** -- no solo el id: los sets del docente se editan, y un
caso de hace seis meses tiene que poder decir con qué números se armó aunque
ese set ya no sea el mismo. El select del editor postea (antes no tenía
`name`) y vuelve a su valor al reabrir el caso. La ficha del docente lo
imprime bajo la tabla de referencia; la de estudio no.

**Bug que apareció haciendo esto:** `public/js/case/abr.js` tenía su PROPIA
copia de la tabla normativa por defecto, y se quedó vieja al reanclar (onda
I en 0.21 µV, neonato en 2.10 ms). O sea: los casos nuevos se armaban contra
una tabla que la app ya no usa. Había cuatro copias de los mismos números
--el JSON del cliente, `CaseWaveforms::CLICK_BASE`, `normativas.php` y el
JS--; quedan dos: la del cliente y la del backend, y las otras dos salen de
`AbrReferences::defaults()`, que las deriva de `CLICK_BASE`.

## ABR: rellenar los huecos de población y vía (2026-09-21)

Quedaban tres combinaciones sin cubrir, y una de ellas era la peor posible.

**1. Vía ósea en neonato y en adulto mayor: no existía.** Ninguno de los dos
tenía bloque óseo, así que caían a su propia vía aérea y devolvían la curva
**idéntica**: el vibrador dejaba de hacer efecto justo en el paciente donde
el ABR óseo *es* el examen -- el recién nacido que no pasó el screening y
hay que separarle transmisión de sensorineural. Ahora se deriva del aéreo de
su población con el mismo corrimiento que ya tenían adulto y niño (+0.20 ms
parejo, amplitud al 0.89).

**2. Sexo, solo entre 18 y 59.** Un hombre de 70 se dibujaba con la curva de
una mujer. `elderly` se parte en `elderly_male` / `elderly_female` con los
valores que F21 publica por sexo en su grupo de 45 o más (y con el III de
hombre-izquierdo corregido por la errata). En pediatría **no** se separa, y
eso no es un hueco: la diferencia por sexo aparece con la pubertad. La clave
vieja `elderly` sigue resolviendo (`LEGACY_POPULATIONS`) para los casos ya
guardados.

**3. De 1 a 3 años caía en `child`,** que ya tiene valores casi de adulto.
Población nueva `toddler`, interpolada entre el neonato de término y el niño
con una fracción por onda (0.88 la I, 0.84 la III, 0.80 la V: la onda V
madura última, F11 n=535 y F19). Control independiente: el I-V queda en 4.28
ms, entre los 4.81 que F25 mide a los 6 meses y los 4.02 del niño de 7 años.

Resultado: **7 poblaciones × 2 vías × 11 estímulos = 154 combinaciones, y
ninguna devuelve la curva del click**. Antes eran 5 poblaciones con dos de
ellas sin vía ósea.

**Trampa que apareció:** `CaseWaveforms::poblacion()` la comparte el VEMP,
cuya tabla no tiene ni `toddler` ni el adulto mayor por sexo -- caía al
fallback de mujer adulta en silencio. Se agregó `VEMP_POP_ALIAS`
(toddler -> child, elderly_* -> elderly) para que traduzca en vez de
perderse. El VEMP del cliente tiene su propia `Normativa.poblacion` y no se
toca.

Las franjas viven en tres lugares que tienen que decir lo mismo:
`ABR_generator.select_population`, `CaseWaveforms::poblacion` y
`public/js/case/abr.js`. Hay test en los dos primeros.

## Recién nacido: horas de vida y su transitorio (2026-09-21)

La edad se guardaba en años enteros, así que un bebé de seis horas y uno de
once meses eran los dos "0 años". No había forma de armar el caso más común
del screening neonatal, ni en el generador automático ni en la ficha.

**El campo.** `edad_valor` + `edad_unidad` (horas / días / meses) en la ficha
del paciente, solo cuando la edad va en 0. Se normaliza a `edad_horas` en
`cases.data` y vuelve a la unidad más legible al reabrir el caso (horas el
primer par de días, después días, meses pasado el mes y medio). La ficha PDF
imprime "6 horas de vida" en vez de "0 años".

**El hallazgo, que es el punto.** Antes de las 24 horas el conducto tiene
vérnix y restos de líquido amniótico y el oído medio todavía tiene
mesénquima: es una pérdida de transmisión REAL pero transitoria, que se
resuelve sola en dos o tres días. Por eso el screening con EOA antes de las
24 horas refiere mucho más que a las 48. `CaseProfile::neonatalTransientDb()`
lo modela como atenuación que decae exponencial (28 dB a las 0 h, τ = 24 h,
nada pasada la semana), y `project()` la reparte según lo que cada examen
atraviesa:

| horas | ABR aéreo | ABR óseo | atenuación EOA | lectura |
|---|---|---|---|---|
| 0 | 35 nHL | 20 nHL | 61.6 dB | EOA ausente |
| 6 | 35 nHL | 20 nHL | 48.0 dB | EOA ausente |
| 24 | 25 nHL | 20 nHL | 22.7 dB | EOA reducida |
| 48 | 20 nHL | 20 nHL | 8.3 dB | EOA presente |
| 168 | 20 nHL | 20 nHL | 0 dB | normal |

La EOA va al doble (cruza conducto y oído medio de ida Y de vuelta, mismo
criterio que la conductiva en `oae_attenuation_db`) y el ABR aéreo a 0.6. La
**vía ósea no se toca**: el vibrador saltea conducto y oído medio, y ese
contraste --aérea elevada, ósea normal-- es lo que dice que es transitorio y
no hipoacusia. El `type` del oído sigue siendo `normal`: si se derivara como
conductivo, el alumno leería una patología donde no la hay.

El cliente no necesitó cambios: la EOA ya lee `atten_db` del caso y el ABR
su `umbral_por_estimulo`, los dos proyectados por el backend.

**Pendiente de lo mismo:** la plasticidad craneal del neonato también hace
que el timpanograma de 226 Hz no sirva (hay que usar 1000 Hz) y que la vía
ósea neonatal tenga su propia calibración. Nada de eso está modelado: hoy el
timpanograma del recién nacido se dibuja como el de un adulto.

## Timpanometría del lactante: la sonda de 226 Hz no sirve (2026-09-21)

Segunda mitad del escenario neonatal. Bajo los 6 meses la pared del conducto
todavía es cartilaginosa y blanda, y su movimiento **domina** la admitancia
medida: con sonda de 226 Hz el equipo dibuja un pico que es de la pared, no
del oído medio. Un timpanograma "normal" a esa edad no descarta nada, y por
eso el estándar es sonda de **1000 Hz**.

El módulo ya tenía las dos sondas y `map_letter_for_probe()` ya convertía la
letra de Jerger en positivo/negativo para la de 1000. Lo que faltaba era el
error: a 226 Hz el lactante daba la letra real del caso, así que elegir mal
la sonda no tenía consecuencia y el hallazgo no existía.

Ahora, con sonda de 226 Hz y paciente bajo 6 meses, un oído cargado **B o N
se dibuja como A**. Las rígidas (As, Cs) se siguen leyendo como tales: lo que
la pared blanda agrega es movimiento, así que puede inventar un pico donde no
hay, pero no puede hacer que una compliance baja se vea alta.

El simulador tiene que **dejar cometer** el error: si a 226 Hz saliera plana,
el alumno nunca se entera de que eligió mal la sonda.

La edad sale de `edad_horas` cuando está (ver la sección anterior) y, si no,
de `edad` en años: con 0 se asume lactante, porque es el caso que hay que
poder armar. Con la edad exacta cargada, un bebé de 8 meses se comporta como
corresponde.

La ficha del DOCENTE lo avisa --si no, el caso parece mal armado cuando el
alumno informa timpanograma normal en un oído que el docente cargó lleno-- y
dice explícitamente cuál es el error que el ejercicio deja cometer. La ficha
de estudio no lo dice.

**Queda pendiente del mismo tema:** la calibración de la vía ósea del
lactante (suturas abiertas, menor atenuación interaural) sigue siendo la del
adulto.

## Vía ósea del lactante: calibración propia (2026-09-21)

Cierra el escenario neonatal. Los valores de referencia del vibrador --la
fuerza que equivale a 0 dB-- están definidos sobre **cráneo adulto**, en la
mastoides. El cráneo del lactante tiene las suturas abiertas y los huesos sin
fusionar, y eso lo hace más eficiente transmitiendo por vía ósea, sobre todo
en graves: el mismo nivel de dial le llega más fuerte a la cóclea.

`CaseProfile::INFANT_BONE_CALIBRATION_DB` = 15 dB en 500 Hz, 10 en 1 k, 5 en
2 k, 2 en 3 k y nada en 4 k. Se aplica pesando las mismas frecuencias que el
estímulo (un burst de 500 se lleva los 15 enteros, el click casi nada porque
lo domina la base coclear) y **solo a la vía ósea**: la aérea entra por el
conducto y no le importa el cráneo. Se desvanece con el cierre de las
suturas: completa bajo los 6 meses, nada pasados los 24, lineal en el medio.

Umbral óseo de un oído normal (10 dB HL parejo):

| edad | 500 Hz | 1 kHz | 2 kHz | 4 kHz |
|---|---|---|---|---|
| adulto | 30 | 25 | 20 | 15 |
| lactante 3 meses | 15 | 15 | 15 | 15 |
| 12 meses | 20 | 20 | 15 | 15 |
| 24 meses | 30 | 25 | 20 | 15 |

**La consecuencia es el punto:** como el gap se calcula restando, el lactante
normal muestra un **gap aéreo-óseo aparente de 15 dB en 500 Hz** que no es
conductivo, es de calibración. Es un error de lectura clásico en screening y
ahora el simulador lo reproduce. La ficha del docente lo avisa explícito; la
de estudio no, porque ahí es justamente lo que el alumno tiene que resolver.

Con esto el recién nacido queda coherente en los cuatro exámenes: EOA ausente
por el transitorio, ABR aéreo algo elevado, ABR óseo con su propia
calibración, y timpanograma que engaña con la sonda equivocada.

## Screening neonatal: calibrado contra tasas de pase publicadas (2026-09-21)

El usuario aportó las tasas de pase por franja horaria (TEOAE y AABR), los
modificadores y las 10 referencias. Eso cambia el modelo de raíz: **la
bibliografía no publica decibeles, publica porcentajes de pase**, así que
ahora la tabla manda y los dB son su consecuencia. La curva exponencial que
yo había estimado el día anterior queda reemplazada.

`NewbornScreening` (backend, con las 10 citas en el docblock):

| franja | TEOAE pasa | AABR pasa |
|---|---|---|
| 0-12 h | 0,40 | 0,85 |
| 12-24 h | 0,55 | 0,92 |
| 24-36 h | 0,75 | 0,95 |
| 36-48 h | 0,85 | 0,96 |
| 48-72 h | 0,93 | 0,97 |
| >72 h | 0,95 | 0,97 |

**Cómo se invierte.** Los dos umbrales en dB no se inventaron, se midieron
contra nuestros propios generadores: la TEOAE de este simulador cae bajo
criterio pasando los ~7,5 dB de atenuación total (o sea 3,75 dB de
conductiva, porque el sonido cruza de ida y vuelta), y el AABR de screening
a 35 dB nHL deja de pasar con ~25 dB de conductiva. Con esos dos puntos, la
función cuantil por tramos lineales reproduce **exactamente** las dos
columnas de la tabla en todas las franjas (verificado con 2000 percentiles
por franja, ±0,01).

**Cada oído tiene su percentil**, sorteado una vez y guardado en el caso: dos
recién nacidos de la misma edad no tienen la misma cantidad de líquido, y los
dos oídos del mismo bebé tampoco. Por eso uno puede referir y el otro no, que
es lo que se ve en el turno. Al reabrir el caso el percentil vuelve tal cual:
el mismo ejercicio no puede cambiar de resultado entre dos clases.

**Modificadores** (bloque "Recién nacido: circunstancias del parto" en la
ficha del paciente): cesárea (−12 h para la EOA, −4 h para el AABR: sin
trabajo de parto no se exprime el líquido), pretérmino tardío --derivado de
las semanas de EG, no es un campo aparte-- (−13 h / −6 h), pequeño para edad
gestacional (+8 h, pasa mejor), vérnix limpiado antes de medir (corta a la
mitad lo que refiere la EOA) y líquido persistente (deja de ser cuestión de
horas: 0,20 / 0,80).

**Tope de un mes**: pasado eso ya no es screening neonatal. El 5% que sigue
refiriendo a las 72 h es sonda, ruido y oído medio de verdad, no el
transitorio del parto; sin el tope, un bebé de ocho meses heredaba la tasa
del recién nacido.

La ficha del docente anticipa el resultado por oído con su porqué; la de
estudio no.

Lo que la tabla de "condición real" describe ya salía solo del modelo: la
hipoacusia sensorial ≥35-40 dB borra la EOA por el audiograma, y la
neuropatía deja la EOA normal con el ABR alterado (es el contraste que
`type = neural` ya hacía).

## A decidir: ¿los pacientes están congelados o envejecen? (2026-09-21)

Sale de querer "hacer nacer a un paciente X horas antes del turno del
alumno". Hoy el sistema no puede: no es una función que falte, es que nunca
se decidió qué es la edad de un paciente. **Hay que elegir una de las dos, no
las dos.**

**Cómo está hoy (congelado, aunque no esté escrito en ningún lado):**
- `edad` es un número estático en `cases.data`, puesto a mano por el docente.
- `fecha_nac` se DERIVA de la edad, con día y mes al azar (ver
  `views/case/_paciente.php`): es decoración para la ficha, no la fuente de
  verdad. Si el docente pone 30 años, la fecha se inventa para que cierre.
- Nadie recalcula nada con el paso del tiempo. Un caso de hace seis meses
  sigue teniendo 30 años.
- `edad_horas` (recién nacido) sigue el mismo criterio: son 6 horas para
  siempre, las abra el alumno hoy o el mes que viene.

O sea: lo que se implementó estos días es **coherente con el modelo
congelado**. Lo que no puede expresar es "nace X horas antes de la cita".

**Qué costaría el modelo que envejece.** No es solo cambiar un campo:

1. La fuente de verdad pasa a ser la fecha (y hora) de nacimiento, y `edad`
   se calcula. Eso invierte la relación actual y toca la ficha del paciente,
   la agenda y los PDF.
2. **El caso es un snapshot.** `api/sync.php` manda `cases.data` tal cual y
   solo re-manda lo que cambió (`updated_at > since`), así que una propiedad
   que depende del tiempo no puede vivir horneada adentro: al día siguiente
   está vieja y el sync no la refresca porque el caso no se editó.
3. Entonces el transitorio neonatal habría que resolverlo **en el momento del
   examen**, no al guardar: o el backend lo recalcula al entregar el caso, o
   el cliente lo hace al abrirlo. Lo segundo es lo único que sobrevive a la
   caché del sync, y obliga a portar `NewbornScreening` a Python (mismo
   patrón que `CaseWaveforms` espeja al generador, con test cruzado).
4. Hay que decidir **contra qué instante** se mide: la hora de la cita (que
   es lo que el docente quiere fijar) o el reloj real del alumno. Con la
   cita, "nace 6 h antes del turno" es exacto y el alumno que llega tarde ve
   un bebé de 6 h igual. Con el reloj real, el que llega dos horas tarde ve
   un bebé de 8 h -- más realista y más difícil de preparar.
5. Y lo incómodo: si los pacientes envejecen de verdad, un caso de "3 meses"
   guardado en marzo es un bebé de 9 meses en septiembre, y su audiograma
   pediátrico y su timpanograma dejan de corresponder. O los casos caducan,
   o envejece solo el recién nacido, o se congela todo salvo la edad exacta.

**Sugerencia para cuando se retome:** el híbrido más barato es congelar todo
como está y agregar UN campo al caso del recién nacido, "horas de vida al
momento de la cita", resolviéndolo contra la hora de la cita y no contra el
reloj. Cubre el caso de uso real (preparar el turno) sin abrir la lata de que
el resto del padrón envejezca.

## Vía ósea del ABR: ley por nivel, lactante invertido y solo onda V (2026-09-21)

Segundo aporte bibliográfico del docente (12 referencias: Beattie 1998, Cobb
y Stuart 2016 I y II, Yang 1987, Stuart 1993, Türkman 2018, Seo 2018).
Contraste contra lo que teníamos:

**Lo que ya estaba bien.** La onda V del click óseo del adulto cae dentro del
rango publicado en los tres niveles medidos (45, 30 y 15 dB nHL), con menos
de 0.1 ms de diferencia. Y el tope de salida del vibrador que pusimos ayer
(50 dB) coincide con el "45 a 55 dB nHL" de la revisión. Los interpicos por
edad también caen en rango: neonato 5.21 contra 4.9-5.3 publicado, 1-3 años
4.28 contra 4.2-4.5, adulto 4.08 contra 3.9-4.2.

**Lo que estaba mal: el signo del lactante.** El modelo le sumaba a TODAS las
poblaciones el mismo +0.2 ms por vía ósea. La bibliografía dice lo contrario
para el bebé: su onda V por vía ósea es **más corta** que por vía aérea, y
más corta que la del adulto. El cráneo sin suturar transmite mejor y el
vibrador saltea un oído medio que todavía tiene mesénquima, así que **por vía
ósea el bebé se parece mucho más a un adulto que por vía aérea**. Con el
offset de adulto, el neonato quedaba 0.5-0.6 ms tarde en los tres niveles --
justo en el examen que define su conducta clínica.

**Lo que faltaba: la corrección no es fija, depende del nivel.** Beattie
1998 (B-71): +0.3 ms a 40 dB, +0.4 a 30, +0.5 a 20, +0.8 a 10, y a 55 dB no
hace falta corregir. Es la misma idea que la función latencia-intensidad pero
de la VÍA: el vibrador rinde menos cerca del umbral. Ahora está como
`BONE_LAT_CORRECTION` e interpola entre esos puntos.

Al lactante no se le aplica esa corrección: su función latencia-intensidad
por vía ósea es más plana (0.45 contra 0.52 ms/10 dB en la tabla publicada).
Se pondera por cuánto cráneo sin suturar le queda (`INFANT_POPULATIONS`:
neonato 1.0, 1-3 años 0.5). Resultado: 6 de las 9 celdas de la tabla caen
dentro del rango y las otras tres se pasan por 0.03, 0.05 y 0.15 ms.

**Lo que faltaba: por vía ósea solo la onda V es confiable.** La I y la III
rara vez se identifican --menos energía, espectro más pobre en agudos (que es
la zona que genera la I) y el artefacto del transductor tapando los primeros
milisegundos--. `BONE_WAVE_AMP` las reduce y `BONE_WAVE_WIDTH` las ensancha.
En el trazo, click de 50 dB en adulta normal: por aire la onda I sale en
0.168 µV y por hueso en 0.018, bajo el piso de lectura, mientras la V
sobrevive (0.350 contra 0.368). Buscar interpicos en un registro óseo es un
error que el ejercicio ahora deja cometer.

**Dos cosas que NO toqué, porque son decisión del docente:**

1. **El chirp por vía ósea.** La fuente nueva da la onda V del CE-Chirp entre
   1.0 y 1.5 ms más corta que la del click, y ella misma aclara "depende de
   cómo el equipo referencia el tiempo cero". Eso contradice de frente a F24
   (Cargnelutti, click y chirp en los MISMOS sujetos), que no encuentra
   diferencia significativa de latencia. No son datos incompatibles: son dos
   convenciones de tiempo cero. Aplicar los 1.0-1.5 ms rompería el anclaje de
   F24 que ya está en el modelo. Hay que elegir qué equipo simulamos.
2. **La referencia de umbral de la vía ósea.** El dato de Cobb y Stuart es
   fuerte: adultos con audición normal dan 3.75 dB nHL por aire y **18.75 por
   hueso**, mientras los lactantes dan 3.75 y 1.25. O sea, en el adulto el
   0 dB nHL óseo está referenciado mucho más "duro" que el aéreo. Nuestro
   modelo hoy los deja comparables (mismo umbral por las dos vías en un oído
   normal). Adoptarlo tal cual significa que **todo adulto normal mostraría
   15 dB de gap aéreo-óseo en dB nHL**, que es real pero exige que el alumno
   sepa que cada vía tiene su propia referencia. Es un cambio de fondo en
   cómo se lee el examen y afecta todos los casos existentes.

## Vía ósea: referencia propia de 0 dB nHL y tope de 55 (2026-09-21)

Aplicado lo que quedaba pendiente del aporte bibliográfico. Cobb y Stuart
2016 miden con click y audición normal: **adultos 3,75 dB nHL por aire
contra 18,75 por hueso; lactantes 3,75 y 1,25**. O sea, el 0 dB nHL óseo no
está referenciado como el aéreo --la fuerza que lo define se mide sobre
cráneo adulto-- y el que muestra un gap aparente es el ADULTO, no el bebé.
Eso da vuelta la nota que yo había escrito el día anterior.

`boneNhlOffset()` pasa de +15 dB en el adulto a −2,5 en el lactante, con el
cierre de las suturas en el medio (entero bajo 6 meses, nada pasados los 24).
Reemplaza la tabla por frecuencia que yo había inventado: la fuente es de
click, así que se modela lo que la fuente mide y no una dependencia de
frecuencia sin respaldo.

Click, con el tope del vibrador en **55 dB nHL** (la revisión lo ubica entre
45 y 55; se toma el tope, decisión del docente):

| caso (dB HL aire/hueso) | aéreo | óseo | aire − óseo |
|---|---|---|---|
| adulto normal 0/0 | 10 nHL | 25 nHL | −15 dB |
| recién nacido 0/0 | 10 nHL | 10 nHL | 0 dB |
| conductiva 40/0 | 50 nHL | 25 nHL | +25 dB |
| conductiva 60/10 | 70 nHL | 35 nHL | +35 dB |
| sensorial 30/30 | 40 nHL | 55 nHL | −15 dB |
| **sensorial 35/35** | 45 nHL | **sin respuesta** | -- |
| mixta 60/30 | 70 nHL | 55 nHL | +15 dB |

**La ventana útil es angosta y esa es la enseñanza**: un adulto normoyente ya
gasta 25 de los 55 dB, así que con una sensorial de 35 dB HL el umbral óseo
se va del alcance del vibrador. Por vía ósea no se encuentra nada, y no es
un error del examen: el ABR óseo sirve para separar transmisión de
sensorineural en pérdidas leves y moderadas, y deja de servir enseguida.

**Bug previo que destapó esto.** El backend escribe `null` para decir "sin
respuesta" (ninguna frecuencia respondió, o el umbral se fue del vibrador),
pero el cliente lo leía como "sin dato" y caía al umbral escalar del oído:
dibujaba una respuesta que en el caso no existe. Ahora `case_threshold`
distingue la clave ausente (cae al escalar, como siempre) de la clave
presente en null (`NO_RESPONSE_DB`, no responde nunca). Afectaba también a
la vía aérea, no solo a la ósea.

## Enmascaramiento: la IA del ruido es la del fono, no la del estímulo (2026-09-21)

Bug que encontró el docente. El enmascaramiento se le entrega al oído
contrario **con un fono**, aunque el estímulo vaya por hueso. El modelo
usaba la atenuación interaural del ESTÍMULO para decidir cuánto ruido cruza
de vuelta al oído que se está midiendo, así que con vibrador (IA = 0)
cualquier nivel de masking sobreenmascaraba: 70 dB de ruido le subían el
umbral a 70 al oído en estudio.

Y entre fonos tampoco da igual. Conductiva en OD (óseo 30 nHL), estímulo de
55 por vibrador, ruido al OI:

| masking | inserción (IA 65) | copa TDH-39 (IA 45) |
|---|---|---|
| 70 dB | umbral 30, ok | umbral 30, ok |
| 80 dB | umbral 30, ok | **umbral 35, sobreenmascarado** |
| 90 dB | umbral 30, ok | **umbral 45, sobreenmascarado** |

Eso es el motivo clínico de preferir inserción cuando hay que enmascarar
fuerte, y ahora el simulador lo muestra. `masking_transducer` en la config
técnica; si no se declara, se usa el fono del estímulo, y con vibrador la
inserción (que es lo que se usa).

**Pendiente del mismo tema: el efecto de oclusión.** Tapar el oído contrario
con un fono de copa mejora su umbral óseo en graves 15-20 dB (con inserción
profunda, mucho menos). O sea, el fono que entrega el ruido cambia también
cuánto ruido hace falta. No está modelado, y para modelarlo bien habría que
decidir si el panel declara con qué fono se enmascara o se asume.

## A revisar: la respuesta justo en el umbral es demasiado clara (2026-09-21)

Salió comprobando el tope del vibrador. La amplitud de la onda V contra el
nivel de sensación, en oído normal:

| SL | amplitud | % de la de SL 40 |
|---|---|---|
| +40 dB | 0.480 µV | 100% |
| +20 | 0.378 | 79% |
| +10 | 0.279 | 58% |
| +5 | 0.216 | 45% |
| **0** | **0.150** | **31%** |
| −5 | 0.091 | 19% |
| −10 | 0.048 | 10% |

Estimulando JUSTO en el umbral del oído, la onda V sale en 0.113 µV con SNR
de 7.8 en un registro de 2000 barridos: se lee clara. Clínicamente, en el
umbral la respuesta es mínima y ambigua por definición -- es lo que obliga a
promediar más y a repetir para confirmar. Con esta curva, buscar umbral es
demasiado fácil y la maniobra pierde sentido.

Hay que empinar `WAVE_AMP_GROWTH` cerca del umbral (que a SL 0 quede en
~10-15% y no en 31%). Afecta TODOS los exámenes y todos los casos, no solo
la vía ósea, así que no se toca sin decidirlo: es de los cambios que
cambian la dificultad del ejercicio.

## Transductores: IA por población, topes de salida y artefacto EM (2026-09-21)

Tercer y cuarto aporte del docente. Contraste fila por fila:

| | nuestro | publicado | |
|---|---|---|---|
| IA inserción ER-3A | 65 dB | 60-70 | OK |
| IA supraaural TDH-39 | 45 dB | 40-50 | OK |
| IA vibrador, adulto | 0 dB | 0-10 | al borde → **5** |
| IA vibrador, **lactante** | 0 dB | **10-25, baja con la edad** | **no estaba** |
| Retardo supraaural vs inserción | −0.9 ms | 0.1 vs 0.9-1.0 → −0.8 | corregido |
| Tope aéreo | **el panel permitía 120** | 90-100 | **no estaba** |
| Tope óseo | 55 | 45-55 | OK |

**La IA ósea del lactante importa de verdad.** La cabeza es chica y el cráneo
sin suturar no conduce de lado a lado como el bloque rígido del adulto:
`interaural_attenuation()` da 5 dB en adulto, 13.5 a 1-3 años y 22 en
neonato. Es parte de por qué el screening óseo neonatal es viable sin
enmascarar en asimetrías moderadas.

**Topes de salida**: `AIR_MAX_OUTPUT_DB = 100`. El panel dejaba pedir 120 y
el generador lo tomaba como bueno; ningún fono entrega eso.

**Artefacto electromagnético.** El transductor es una bobina con un imán y la
corriente del click induce voltaje en los electrodos. Dos cosas nuevas:

1. **Se cancela con polaridad alternada** (se invierte con el estímulo, la
   respuesta neural en buena parte no). Ahora es la razón principal de
   alternar, más allá de la microfónica -- y explica por qué una onda I "que
   solo aparece en rarefacción" hay que mirarla con desconfianza. Antes el
   artefacto se sumaba igual en las tres polaridades.
2. **El vibrador es el peor de los tres y quedaba como el mejor.** La escala
   del artefacto se refería a 80 dB para todos, pero 80 está por encima de lo
   que el vibrador puede entregar: a su tope de 55 daba 0.02 µV, el más chico
   de los tres, cuando físicamente va apoyado SOBRE el hueso a centímetros
   del electrodo. Ahora cada transductor tiene su nivel de referencia (fonos
   80, vibrador 50) y en su nivel alto de trabajo queda:

   | transductor | nivel | artefacto | dura |
   |---|---|---|---|
   | inserción | 95 dB | 0.199 µV | 0.8 ms |
   | supraaural | 95 dB | 0.478 µV | 1.0 ms |
   | **vibrador** | **55 dB** | **0.475 µV** | **1.2 ms** |

   Sumado a que por vía ósea las ondas tempranas ya vienen reducidas
   (`BONE_WAVE_AMP`), eso es por qué se pierden tan seguido.

Y el supraaural es el caso feo por partida doble: artefacto grande Y casi sin
retardo acústico, así que el artefacto y la onda I quedan pegados en el
tiempo. A nivel alto la tapa o la deforma, y se lee una I temprana y grande
que es puro estímulo.

**Efecto colateral en un test previo:** `test_a_high_high_pass_eats_the_amplitude`
medía con polaridad alternada y su margen estaba calibrado con el artefacto
sumando. El artefacto es de baja frecuencia, así que el pasa-alto también se
lo comía y exageraba la diferencia. Se recalibró contra 500 y 750 Hz, donde
el efecto es inequívoco.

## Umbral, polaridad y sobreenmascaramiento: los cuatro puntos (2026-09-21)

**1. La respuesta en el umbral era demasiado clara.** Salía en el 31% de su
amplitud máxima estimulando JUSTO en el umbral, así que encontrar el umbral
era trivial. Ahora la ley es
`A(SL) = A_ref · (1 − e^(−SL/tau)) / (1 − e^(−SL_ref/tau))`, con el codo
suave reducido de 0.3·tau a 0.05·tau: queda en ~3% a SL 0 y 49% a SL 10.

Medido en una búsqueda de umbral real (oído de 30 dB, 2000 barridos):

| dB | SL | onda V | ruido | SNR | lectura |
|---|---|---|---|---|---|
| 40 | +10 | 0.184 | 0.012 | 15 | clara |
| 35 | +5 | 0.117 | 0.015 | 7.7 | clara |
| **30** | **0** | **0.023** | 0.011 | **2.0** | **dudosa** |

**Trampa que apareció**: anclar la normalización en SL 40 (como decía la
propuesta) invertía la razón V/I a nivel alto. Nuestras amplitudes
normativas están medidas a 80 dB nHL en oídos normales, o sea SL ~70, no 40.
Con el ancla en 40 cada onda crecía distinto por encima de ese punto --la
onda I, que arranca más tarde y satura más rápido, se iba 21% por encima de
su valor normativo-- y terminaba siendo más grande que la V. `AMP_SL_REF = 70`.

**2a. La cancelación del artefacto al alternar no es completa por vía ósea.**
El vibrador no es simétrico entre polaridades (empuja contra el hueso, que
no responde igual en los dos sentidos): queda un residuo del 15%
(`ARTIFACT_ALT_RESIDUAL`). En los fonos sí cancela.

**2b. Alternar ensancha las ondas** un 5%: promedia dos respuestas con
latencias apenas distintas.

**2c. La maniobra del tubo YA estaba** y es la que distingue artefacto de
respuesta: con el tubo pinzado el artefacto persiste y la onda V desaparece
(0.477 → 0.047 µV). Es el `ch_clamp` del panel, que se relee en cada tick de
la promediación.

**3. El sobreenmascaramiento se juzgaba contra el umbral equivocado.** El
ruido que cruza el cráneo llega a la cóclea **por vía ósea**, así que se
compara contra el umbral ÓSEO del oído medido. Con el aéreo se subestimaba
justo en las conductivas, que es donde el enmascaramiento importa. Conductiva
con aéreo 70 y óseo 25, estímulo aéreo de 80, ruido con inserción:

| masking | cruza | antes | ahora |
|---|---|---|---|
| 80 dB | 15 dB | ok | ok |
| 95 dB | 30 dB | ok (30 < 70) | **sobreenmascara** (30 > 25) |

**4. Efecto de oclusión: postergado**, con el aval del docente. Se concentra
bajo 1 kHz y el click y el chirp de banda ancha generan la respuesta desde
regiones más agudas; con inserción profunda además es chico. Solo va a pesar
cuando se agregue tone burst de 500 Hz por vía ósea con supraaural en el
oído contrario.

**Pendiente que quedó a la vista:** nuestro ruido residual es ~11 nV a 2000
barridos cuando el equipo tiene configurado un objetivo de 40 nV, y la
propuesta del docente usa 0.05 µV / √(barridos/1000) = 35 nV. O sea, el
trazo sale ~3 veces más limpio de lo que el propio equipo declara. Eso hace
el umbral más fácil de lo que debería incluso con la amplitud ya corregida.
No se tocó: la calibración del ruido tiene sus propios tests y toca FSP,
rechazo de artefacto y monitor de EEG.

## Ruido residual: calibrado y dependiente de los barridos (2026-09-21)

Dos defectos, y el segundo era peor que el primero.

**1. El trazo salía 3.7 veces más limpio de lo que el propio equipo
declaraba** (11 nV medidos con el objetivo en 40). El ruido se genera con
RMS 1 y DESPUÉS pasa por la banda de registro, que se queda con una
fracción -- el EEG es 1/f y el EMG es de alta, así que la mayor parte de su
energía cae fuera de 100-3000 Hz. El equipo mide el residual sobre el trazo
ya filtrado, así que la escala tiene que definirse ahí
(`NOISE_BAND_CALIBRATION`).

**2. El ruido dependía de la FRACCIÓN del objetivo, no de los barridos.**
El bloque era `objetivo / NOISE_BLOCKS`, así que al llegar al objetivo
siempre había los mismos bloques: pedir 4000 barridos daba exactamente el
mismo ruido final que pedir 1000. **Promediar más no servía de nada**, que
es justo la maniobra con la que se confirma una respuesta cerca del umbral.
Ahora el bloque es absoluto y el residual cae como 1/√N desde
`NOISE_REF_SWEEPS`.

Las dos cosas juntas cambian el ejercicio. Oído con umbral real de 30 dB,
SNR de la onda V:

| dB | SL | 1000 | 2000 | 4000 | 8000 |
|---|---|---|---|---|---|
| 45 | +15 | 5.4 | 8.9 | 13.0 | 18.9 |
| 40 | +10 | 4.1 | 6.6 | 11.2 | 13.3 |
| **35** | **+5** | **2.2** | **2.9** | **4.5** | **8.1** |
| 30 | 0 | 2.0 | 2.1 | 1.8 | 2.4 |

Con el criterio habitual (SNR ≳ 3), el alumno que promedia 1000 barridos
informa umbral 45; el que promedia 4000 llega a 35. El umbral real (30)
nunca se ve claro, que es la definición de umbral. Es exactamente lo que
pasa en la clínica y antes no pasaba.

**Tres tests se cayeron y los tres estaban midiendo el defecto:**

- El techo de seguridad del ruido (`NOISE_MAX_UV`) estaba expresado en
  unidades del ruido sin filtrar y quedó mordiendo en el caso normal: con
  la escala nueva, cualquier objetivo de 40 nV para arriba daba el mismo
  trazo y el ajuste del equipo dejaba de hacer efecto. Ahora está en
  unidades del trazo que se ve.
- El de rechazo de artefacto comparaba con el paciente QUIETO, donde
  apagar el rechazo casi no cambia nada. Ahora compara donde importa: con
  inquietud 0.8, el rechazo descarta 760 barridos y aun así deja el
  residual en menos de la mitad.
- El de la falsa onda V tenía margen de 1.5 calibrado contra el trazo
  demasiado limpio. Con el ruido real, la misma falsa onda pesa
  proporcionalmente menos: sigue siendo la pista, pero no tapa el
  registro.

## ABR: el FSP sale del trazo y el umbral del caso es el que se mide (2026-09-21)

Tres cambios encadenados que cierran el hueco que dejó la batería de
verificación (`verificacion_abr_eoa.md`, tests D6 y H1).

### 1. El FSP se calcula, no se declara

`fsp_puntos` del caso era el número que el equipo mostraba, degradado por
ruido y electrodos. Daba lo mismo con respuesta clara que sin respuesta, y
por eso D6 no salía solo. Ahora:

- `expected_fsp()` es la razón entre la señal que hay en la ventana de
  análisis (filtrada, como la ve el equipo) y el ruido residual medido
  sobre A−B: `1 + (A_rms / residual)²`.
- `observed_fsp()` sortea alrededor de ese valor con una F no central
  (df1 = 5, df2 = 250, la de Elberling & Don), así que dos registros
  iguales no dan el mismo número. Criterio 3.1.
- Que el FSP suba con el nivel, suba con los barridos y caiga con
  impedancias altas, paciente inquieto o banda mal elegida no se programa:
  sale de que todo eso ya está en el residual.

### 2. El ruido del paciente se declara por las CONDICIONES

`nivel_referencia` + `barridos_criterio` (N*) + `respuesta_en_referencia`
reemplazan al FSP declarado: "a tal nivel hicieron falta tantos barridos
para llegar al criterio". De ahí sale σ = A_rms·√(N*/2.1) y ese ruido vale
para todos los niveles. Los casos viejos se convierten al vuelo con
N* = 2.1·2000/(FSP@2000 − 1), que no depende del caso porque la amplitud
se cancela.

**El default del nivel de referencia es VACÍO = el propio umbral**, con
N* = 2000. Es lo que hace que las dos definiciones de umbral coincidan: el
umbral que declara el docente es el nivel donde el equipo dice "presente"
en la mitad de los registros con 2000 barridos. Correrse de 2000 es correr
el umbral que va a encontrar el alumno, y es la perilla para un paciente
más ruidoso o más quieto.

`residual_noise_nv` de Parámetros Avanzados dejó de escalar el ruido: es el
criterio con el que el alumno decide cuándo parar, no una propiedad del
paciente. Sigue siendo el respaldo del caso que declara AUSENTE la
respuesta en la referencia, donde no hay amplitud de la que despejar σ.

### 3. Umbral fisiológico ≠ umbral clínico

`PHYSIOLOGICAL_OFFSET_DB = 9.0`: la onda V se apaga 9 dB por DEBAJO del
umbral que informa el equipo, así que en el umbral clínico vale la mitad de
su amplitud. Sin esto, o la respuesta en el umbral era invisible (P de
detección 0.05, que era D6) o había que regalar amplitud.

El desfase solo corre el origen del nivel de sensación, así que **todo lo
que se mide lejos del umbral queda igual**: los `sl_min` de cada onda, el
ancla del normativo (`AMP_SL_REF`) y la referencia de la función L-I
coclear se corrieron los mismos 9 dB. El golden del modelo lo confirma:
solo se movió la onda V, y más cuanto más cerca del umbral (0.401 → 0.464
a 40 dB; 0.535 → 0.537 a 80).

El reclutamiento bajó de 0.65 a 0.8 de τ: contando el SL desde el umbral
fisiológico, un oído con umbral 60 estimulado a 80 dB llegaba al 95% de la
amplitud del oído sano, o sea se veía sano.

### 4. El zumbido de red se lleva puesto el FSP

Hallazgo al correr la regresión: sin tierra el equipo dibujaba el zumbido
pero el residual y el FSP no se enteraban, porque la interferencia se
generaba IGUAL para las dos mitades y se cancelaba exacto en A−B. Ahora se
reparte en cuadratura entre lo que sobrevive al promediado (`MAINS_COHERENT`
0.8, lo que se ve dibujado) y lo que entra con la fase de cada barrido
(`MAINS_INCOHERENT` 0.6, lo que no se cancela). Sin tierra: residual de 59
a 742 nV y FSP de 7.9 a 1.0.

### Barridos y umbral: 6 dB por cada mitad

Consecuencia medible del punto 3 y de la curva de crecimiento anclada en F1
(50 % de amplitud a 10 dB sobre el umbral fisiológico) combinada con el
1/√N del promediado: **cada vez que se parten los barridos a la mitad, el
umbral que encuentra el alumno sube unos 6 dB**. Medido sobre un umbral
declarado de 10 dB nHL: 500 barridos → 24,7 · 1000 → 17,7 · 2000 → 12,2 ·
4000 → 9,5.

El piso de esa serie no es el umbral declarado sino el **fisiológico** (1 dB
nHL en el ejemplo), así que promediando mucho se encuentra respuesta POR
DEBAJO del declarado y el escalón se va achicando (7,0 · 5,5 · 2,7 dB):
cerca del umbral fisiológico la amplitud tiende a cero y agregar barridos
rinde cada vez menos. Por eso el umbral del caso está **referido a 2000
barridos**, y el campo de la ficha lo dice.

Sirve para armar casos: con N* = 800 al nivel de referencia, el que se
detiene a los 400 barridos informa ~6 dB de más. Y explica por qué no hay
que empinar la curva de crecimiento para acortar esa diferencia: rompe F1,
que es la condición fuerte.

## Casos de recién nacido: se podían proyectar pero no armar (2026-09-21)

El motor neonatal estaba entero --transitorio por horas, tamizaje por franja,
referencia ósea del lactante, sonda de 1000 Hz-- pero el camino para ARMAR el
caso no llegaba hasta ahí. Lo que faltaba:

1. **`age = 0` bloqueaba el guardado** con "Falta la edad". O sea que ningún
   caso de maternidad se podía guardar, justo cuando la edad es el dato del
   ejercicio. Ahora 0 es válido si viene la edad exacta.
2. **El armado rápido no sabía de recién nacidos**: pedía años enteros y no
   escribía las horas de vida, así que el caso salía como "lactante de 0
   meses" sin transitorio ni tamizaje. Ahora tiene su bloque, y el botón
   sortea el turno (6-36 h, 37-41 semanas, 2700-3900 g) cuando la edad va en
   0 y el campo está vacío. Lo ya cargado no se pisa.
3. **El catálogo no filtraba por edad**: le ofrecía presbiacusia, NIHL y
   otoesclerosis a un bebé de diez horas, con los cuadros del turno perdidos
   entre setenta. `CaseProfile::SCENARIO_EDAD` (rangos) y `SCENARIO_NEONATAL`
   (los del turno, que van primero) más `scenariosParaEdad()`, espejados en
   `generator.js`.
4. **La población normativa iba por años enteros**: un bebé de ocho meses
   tomaba las latencias del recién nacido. Ahora las horas de vida mandan:
   menos de 3 meses `neonate`, hasta los 3 años `toddler`. Espejado en
   `select_population`, `CaseWaveforms::poblacion` y `abr.js`.
5. **La ficha del docente mentía sobre el tamizaje**: `resultado()` mira solo
   el transitorio, así que un GJB2 de 80 dB salía como "AABR pasa".
   `resultadoOido()` cruza transitorio, umbral ABR y estado de la EOA, y da
   el patrón que importa: neuropatía = TEOAE pasa + AABR refiere.

### Campos nuevos del nacimiento

`peso_g`, `torch` (+ `torch_sintomatica`), `uci_dias`, `ototoxicos` y
`exanguinotransfusion`, además de las semanas que ya estaban. De los números
salen los derivados, que no son campos aparte: `pretermino` (< 34 semanas,
distinto del tardío 34-36) y `muy_bajo_peso` (< 1500 g, JCIH 2019).

Los dos primeros mueven el tamizaje --prematuro −20 h TEOAE / −12 h AABR,
muy bajo peso −10 / −8, y se acumulan, que es la razón de que la UCIN refiera
varias veces más que la sala cuna--. **Las TORCH NO lo mueven**, y es a
propósito: no son líquido en el conducto, son riesgo de hipoacusia de verdad,
muchas veces progresiva o de aparición tardía. Un CMV que pasa el tamizaje y
a los seis meses ya no pasa es el caso que hay que poder armar, y taparlo con
un "refiere" al nacer lo arruinaría. Los indicadores de riesgo van a la ficha
del docente como antecedente y obligan a seguimiento; no inventan hipoacusia.

### Cuadros nuevos

`efusion_neonatal` (transmisión: el oído medio que no terminó de airearse, la
causa más común de "refiere" repetido en el rescreening), `pendred` /
acueducto vestibular dilatado (sensorial que puede PASAR el tamizaje y caerse
después) y `asfixia_perinatal` (neural: el otro camino a la neuropatía en la
UCIN, junto con la bilirrubina). Con eso el turno del recién nacido tiene
material en las tres categorías que hay que poder distinguir ahí --5
conductivas, 15 sensoriales, 5 neurales-- que es el ejercicio.

## Equipo de AABR (2026-09-21)

El backend razonaba en AABR --las tasas de pase de `NewbornScreening`, el
`resultadoOido()` de la ficha docente-- pero en la app no existía: el único
protocolo implementado era el ABR diagnóstico. El alumno podía emularlo
estimulando a 35 dB nHL y leyendo el rótulo del FSP, que es el mismo
estadístico, pero sin nada que le impidiera diagnosticar con un equipo de
tamizaje.

`src/abr/AabrMainWindow.py` es **otro equipo**, no un modo del ABR: comparte
generador, criterio y ruido del paciente, y no deja marcar ondas ni buscar
umbrales. Nivel fijo, y el equipo contesta PASA o REFIERE cuando el FSP cruza
el criterio o cuando se acaban los barridos.

**Un botón y una sola pantalla.** La secuencia la corre el equipo solo, en el
orden en que se toma de verdad, y se detiene donde falla:

1. **Sonda** — la comparte con el equipo de EOA, así que es la misma pantalla
   de probe fit (`oae/widgets/probe_check.py`) y el mismo sello del caso
   (`EOAS['sello_pct']`). Con el sello bajo 60 % se detiene ahí.
2. **Impedancias** — se muestran y listo, siempre OK a 20 kΩ. En tamizaje el
   límite es mucho más ancho que en el ABR diagnóstico, así que no frenan nada
   y no se modelan: el ejercicio del AABR no es el montaje.
3. **Registro** — promedia **mostrando la curva**: los equipos de tamizaje la
   muestran mientras registran. Lo que no hay es marcado de ondas ni escala de
   intensidades: una sola curva, al nivel del tamizaje.
4. **Resultado** — PASA o REFIERE, y el informe.

Al **ritmo real**: 900 barridos son unos 30 segundos, no uno. El tiempo sale de
la tasa (`EFICIENCIA_BARRIDOS`, ~1 de cada 3 barridos entra al promedio entre
el rechazo y las pausas del equipo), así que subir la tasa acorta la prueba
—que es la razón por la que los equipos de tamizaje estimulan tan rápido—.

Cambiar de oído vuelve al paso 1: la oliva se saca y se pone del otro lado.

### El informe

Un tamizaje no informa morfología, informa PASA o REFIERE; pero algo hay que
dejar escrito. El bloque de informe trae el resultado por oído precargado con
lo que dio y **editable** (informar distinto de lo que salió también es un
error y tiene que poder cometerse), las condiciones escritas solas (estímulo,
nivel, barridos, segundos, FSP, impedancias) y dos campos de texto:
observaciones y conducta.

Sube al cerrar la atención con tipo `AABR` --nuevo en `REPORT_TIPOS` y en
`ReportPdfBuilder`, que le dibuja su propio cuerpo sin curvas-- por el mismo
camino que los demás módulos de examen: `report_upload.php` resuelve la
atención con `appointment_id` + el alumno del token, así que el informe queda
colgado de SU atención. Sin tamizar y sin texto no se sube nada.

El panel de configuración queda a la vista y editable (nivel, estímulo,
transductor, tasa, barridos máximos, criterio, rechazo de artefacto, banda de
registro), que era el pedido: poder mover los parámetros delante del curso y
ver qué le pasa al resultado. "Restaurar valores de fábrica" los devuelve a
35 dB nHL / CE-Chirp / 6000 barridos / FSP 3,1.

### Cómo se habilita

`AABR` entra en `Layout::APPS` y en el Box de Electrofisiología, al lado de
ABR, pero **no** tiene switch propio en `Courses::MODULES`: se habilita con
ABR vía `MODULE_ALIAS` en `core/ui_helpers.py`. Ofrecer el tamizaje sin el
diagnóstico no tiene sentido, y así el docente prende una cosa y le aparecen
los dos botones. Es el primer alias de módulo; si aparece otro caso igual,
el patrón ya está.

### Lo que los tests fijan

Oído sano pasa y pasa rápido; hipoacusia real refiere; **neuropatía refiere
aunque la cóclea esté viva** (el patrón que justifica tamizar con AABR y no
solo con EOA); cortar el promedio antes de tiempo refiere a un sano --el
error de procedimiento que el ejercicio tiene que dejar cometer--; y el mismo
oído de umbral 45 refiere a 35 dB nHL y pasa a 60, así que subir el nivel
para "conseguir un PASA" se ve como lo que es.

### La hoja de tamizaje en el PDF

`CaseSheetPdf::aabr()`, **después de las OEA** y antes del VEMP: es la otra
mitad del mismo turno --se tamiza con las dos pruebas-- y se lee con los dos
resultados a la vista.

No repite el informe: dice qué tiene que contestar el equipo en este paciente
y **por qué**, que es lo que separa un rescreening de una derivación. La
columna "Por qué" distingue los tres caminos: transitorio de las primeras
horas, umbral por encima del nivel de tamizaje, o TEOAE presente con AABR
ausente (desincronía). En el recién nacido, debajo va el tamizaje esperado
por franja horaria con las circunstancias del parto y los indicadores de
riesgo del JCIH.

La hoja sale en todos los casos, también en un adulto: el AABR es un equipo
que el alumno puede usar con cualquier paciente y el docente necesita saber
qué debería dar. Lo que cambia es la nota de abajo.

## Parámetros avanzados del ABR: lo que faltaba (2026-09-21)

Los alumnos los buscaban y no estaban --el **2-1-2 del tone burst** es el
ejemplo que se repite--. Ahora el diálogo los tiene todos, repartidos en tres
pestañas (Estímulo, Registro, Promediación), pero **el modelo todavía no los
lee**: se dibujan, se guardan y viajan en el `technical_config` con la clave
con la que se van a leer.

Los que quedan pendientes están listados en `ABR_generator.UNCONNECTED_SETTINGS`,
que es documentación interna: **en pantalla no se distinguen** de los que sí
funcionan. Llegaron a estar en gris con un tooltip que decía que no afectaban
al trazo, y se sacó: es un equipo simulado y un equipo no le avisa al operador
cuáles de sus perillas están implementadas. Marcarlos rompe la simulación.

| pestaña | pendientes |
|---|---|
| Estímulo | duración del click, envolvente del burst (2-1-2, 2-0-2, 1-0-1, 2-2-2, 5-0-5, en ms), ventana (Blackman/Hanning/gaussiana/lineal), unidad de nivel, jitter de la tasa, presentación, ruido y offset de enmascaramiento |
| Registro | canales, ganancia, notch de red, pendiente del filtro, frecuencia de muestreo |
| Promediación | promedio ponderado, parada automática, ventana de análisis del FSP, suavizado |

**Conectar uno** es leerlo en el generador, darle su test, y sacarlo de
`UNCONNECTED_SETTINGS`: el test del diálogo exige que todo lo que siga en esa
lista esté dibujado y marcado, así que la lista se achica sola.

### El Storage de módulos se indexaba con len(APPS)

Abrir el AABR reventaba con `IndexError: list index out of range` en
`Storage.is_full`. La causa no era el módulo nuevo: `self.modules =
Storage(len(APPS))` asume que los `pos_z` del layout son un índice denso
desde 0, y no lo son --falta el 12, y los pos_z llegan hasta 21 con 21 apps--.
El último módulo del layout quedaba siempre justo afuera del Storage; hasta
ahora el máximo coincidía con `len(APPS) - 1` de casualidad. Ahora manda el
pos_z más alto, no cuántas apps hay.

## Oído sano de un chico: cero clavado (2026-09-21)

Generar "Normal para la edad" en un paciente joven daba umbrales de 0 a 10 dB
repartidos por frecuencia: la forma del cuadro (3-5 dB) más el jitter de ±4.
Eso es un normal de adulto. **A esa edad un oído normal oye en 0 dB HL en
todas las frecuencias y no hay otra forma**: la dispersión que trae la
audiometría del adulto es envejecimiento temprano, ruido y otitis viejas,
cosas que ese paciente todavía no tuvo. Dibujárselas le enseña al alumno un
normal que no existe.

`CaseProfile::EDAD_AUDICION_PERFECTA = 18`, expuesta en `CASE_CONST` y leída
por `generator.js` (`esCeroClavado`): bajo esa edad, el cuadro normal se
escribe en 0, sin jitter, sin norma por edad y sin gap. El corte va en 18 y no
en 15 porque es donde arranca ISO 7029 -- antes de esa edad la norma no dice
nada, justamente porque no hay nada que decir. Los demás cuadros no cambian:
un chico con otitis tiene su otitis sobre un oído de cero.

## Timpanograma de alta frecuencia en la ficha (2026-09-21)

El cliente ya modelaba la sonda de 1000 Hz --protocolo binario, positivo o
negativo, sin letra de Jerger-- pero la ficha no la mencionaba: el resultado
salía sorteado de la letra de 226 Hz con un gradiente de probabilidad, y el
docente no podía ni verlo ni fijarlo.

`Z1000_OD` / `Z1000_OI` en el caso, con tres valores: **derivado de la curva
de 226 Hz** (el default, y lo que traen los casos viejos), **positivo** y
**negativo**. El cliente lo respeta en `map_letter_for_probe(..., forzado=)`.

Es el mismo criterio que la SOAE: el caso que NECESITA un resultado concreto
--el lactante con el oído medio ocupado que a 226 Hz se ve normal y solo la
sonda de 1000 Hz delata-- no puede quedar librado a que la moneda acompañe.

## Recién nacidos: tres cosas que se notaron probando (2026-09-21)

### Las EOA salían presentes siempre

Un recién nacido de 14 horas con los dos oídos normales daba las EOA
presentes en todos los casos. La vista previa (`admin/case_project.php`)
proyectaba **sin las circunstancias del parto**, así que usaba el percentil
de líquido por defecto (0,5) -- y a esa edad 0,5 cae justo del lado que pasa.
Como al guardar **lo posteado le gana a la proyección**, ese default quedaba
escrito en el caso y el sorteo de `parseNacimiento` no se veía nunca.

Ahora la vista previa proyecta con `CaseForm::parseNacimiento($_POST)` --la
misma función que el guardado, ahora pública-- y el generador **sortea el
percentil de cada oído** al armar el caso y lo escribe en el formulario. Con
eso los dos caminos usan el mismo número y el turno del tamizaje vuelve a
tener sorpresa: a las 14 horas la TEOAE refiere en el 45 % de los recién
nacidos sanos, que es lo que dice la tabla.

### La madre habla y el bebé no

Bajo los 3 años (`Sala::EDAD_SIN_RELATO`, que ya era el corte de `CAP_NULO`)
el paciente no produce frases. Dos incoherencias:

- El acompañante podía quedar con "espera su turno: habla solo cuando le
  hablan a ella" mientras el paciente no puede hablar. `nivelInterrupcionCon()`
  lo fuerza a "contesta por el paciente" cuando el paciente es una guagua, y
  el generador escribe la tendencia a responder en 100.
- **Bug del prompt**: con conciencia bajo 40 --que es lo que le corresponde a
  un lactante-- el prompt le hacía decir al bebé que escucha bien y que la
  culpa es de la tele. Negar el problema es una conducta de RELATO: ahora esa
  línea solo entra si el paciente puede hablar. El generador además pone la
  conciencia en 0 por edad, no por cuadro.

## El informe de la TEOAE reventaba al cerrar la captura (2026-09-21)

`KeyError: 0` en `_store_report`, justo al terminar de medir el oído --con el
paciente en atención y la medición ya hecha--. `snr_per_band` y
`pass_per_band` vienen indexados **por frecuencia** (`{1000: 8.2, 2000: ...}`),
que es como los arma el generador recorriendo `normative['bands_hz']`, y el
informe los leía por posición.

No saltó antes porque el dibujo de las barras sí los trata como diccionario:
la pantalla se veía bien y el error aparecía solo al guardar. Ahora se leen
por frecuencia, tolerando la clave como texto (un caso guardado o un JSON la
pueden traer así), con tests que fijan que cada banda conserve SU número.

## Electrococleografía: el motor (2026-09-21)

`src/abr/ecochg.py` es el modelo del examen y `ABRGenerator.build_ecochg_curve`
el enganche. El ECochG cuelga de la ventana del ABR --mismo equipo, mismos
electrodos, mismo promediador, mismo ruido, mismo FSP-- y se separa solo en la
curva objetivo y en la ventana de análisis. La UI de medición y el bloque del
caso en el backend todavía NO están: ver "lo que falta" al final.

### Decisiones tomadas con el docente

- **El PA va hacia abajo.** El electrodo activo es el del oído (timpánico o de
  conducto), no el vértex, así que la negatividad coclear queda hacia abajo en
  pantalla. Es la convención opuesta a la del ABR de la misma ventana y es
  correcta: el montaje está invertido.
- **Se marca haciendo clic en la curva**, como en VEMP v2, con cuatro marcas:
  BL (línea de base), PS, PA y FIN (retorno a la base).
- **Las cuatro medidas**: razón de amplitudes PS/PA, razón de áreas, latencia y
  ancho del PA, y corrimiento por tasa.

### Decisiones de modelado (no había de dónde sacarlas)

1. **La altura del PS se despeja sobre la curva armada** (`calibrate_sp`), no
   con una fórmula cerrada. El hombro del PS cae sobre la rama ascendente del
   PA, así que en ese punto el trazo ya trae la cola de la gaussiana del PA; y
   con polaridad alternada el trazo es además el promedio de dos curvas con el
   PA en distinta latencia y amplitud. Con la fórmula cerrada un caso declarado
   en 0.55 se medía 0.43: el docente no podía poner un oído en el borde del
   límite y saber de qué lado iba a caer. Ahora lo medido es lo declarado
   (`test_the_measured_ratio_is_the_one_the_case_declares`, tolerancia 0.05).
   Se descartó calibrar a mano los coeficientes de la morfología: cualquier
   cambio posterior de anchos los habría vuelto a desalinear en silencio.
2. **La meseta se calibra SIEMPRE sobre la curva alternada**, sea cual sea la
   polaridad del equipo. Es la única sin microfónica encima, y la microfónica
   --que en una desincronía es más grande que el propio PS-- no tiene por qué
   cambiar cuánto PS produce esa cóclea. Así el PS es el mismo en las tres
   polaridades y lo único que cambia entre ellas es la MC, que es el punto del
   examen.
3. **La latencia de la MC sale de la normativa** (clave `MC` del bundle) más el
   retardo del transductor, y NO se deriva de la del PA. Derivándola del PA, la
   polaridad le corría 0.1 ms y la MC de rarefacción no cancelaba con la de
   condensación al alternar -- justo lo que el examen usa para separarla del PS
   y del PA. Era un bug real, no una simplificación.
4. **Las dos áreas se separan con una línea horizontal a la altura del PS**, no
   con un corte en el tiempo: área PS = lo que aporta la meseta, que corre por
   debajo de todo el complejo; área PA = lo que la espiga agrega por encima de
   esa meseta. Es la separación que reproduce los valores publicados (normal
   ~1.0, límite 1.94 con electrodo timpánico). Cortando por tiempo en el hombro
   la razón daba ~0.3 y no había contra qué compararla.
5. **El sumación se prolonga además de crecer** (`SP_TAIL_PER_RATIO`), desde la
   razón de un oído sano y no desde el límite. Sin eso, la razón de áreas y la
   de amplitudes decían exactamente lo mismo y la segunda no agregaba nada; con
   eso, el área cruza su límite un poco antes que la amplitud, que es el
   comportamiento clínico descrito.
6. **El límite de áreas se escala por electrodo** igual que el de amplitudes
   (1.94 timpánico → 2.43 de conducto → 1.46 transtimpánico). Un mismo oído no
   puede cambiar de diagnóstico al cambiar de electrodo
   (`test_the_electrode_moves_the_ratio_and_its_limit_together`).
7. **Ventana de 10 ms, no 5.** La razón de áreas se integra hasta que el
   complejo vuelve a la línea de base, y en un hidrops marcado la meseta se
   prolonga bastante más allá del PA: con 5 ms el examen no se podía terminar
   justo en el caso que interesa. Se descartó dejar 5 ms y que el alumno abriera
   la ventana: el equipo no avisa por qué no hay número, y el ejercicio pasaba a
   ser sobre la ventana en vez de sobre el hidrops.
8. **Ganancia del electrodo recalibrada**: 2.5 / 8.0 / 25.0 (conducto,
   timpánico, transtimpánico) contra el Cz-mastoides. El valor viejo de
   `tympanic` era 2.5 y con eso el ECochG salía con PEOR relación señal/ruido
   que un ABR, porque su banda (10-3000 Hz contra 100-3000) deja entrar unas 3
   veces más ruido. Un electrodo timpánico da PA de 1 a 5 µV, que es la razón
   clínica de meterse hasta la membrana.
9. **El PS necesita nivel** (`SP_SL_MIN` / `SP_SL_FULL`): el PA existe hasta el
   umbral pero el PS solo se hace medible con la cóclea bien empujada. Medir la
   razón a nivel bajo la da chica aunque el oído tenga hidrops, y el equipo no
   avisa: es el error que el ejercicio tiene que dejar cometer.
10. **Sin curva sombra ni canal contralateral.** Un electrodo timpánico está
    pegado a ESA cóclea; lo que capta del otro lado queda muy por debajo de su
    propia respuesta. El ECochG no es la prueba con la que se enseña
    enmascaramiento.

### Arreglo colateral: el pasa-alto sobre la época

`ABRGenerator.apply_filters` filtraba la época recortada con el padding corto de
`sosfiltfilt` (unas decenas de muestras), o sea le daba al filtro un tramo mucho
más corto que su propia respuesta al impulso (1/f = 100 ms para un corte de
10 Hz). Con eso el potencial de sumación --un desplazamiento DC de 2 ms dentro
de una ventana de 10-- desaparecía entero y el examen no se podía hacer. Ahora
la época se extiende con su propio borde (que es la línea de base, igual que en
el registro continuo del equipo) hasta cubrir tres constantes de tiempo del
corte, y después se recorta. Con cortes altos (100 Hz, ABR de 12 ms) el relleno
es corto y el resultado es el de antes: `tests/test_abr_generator.py` pasa igual.

### La medición (2026-09-21, misma tanda)

`src/abr/EcochgTable.py` es la tabla y el marcado vive en `AbrGraph`. Decisiones:

- **Las dos tablas conviven y se muestran según la prueba** (`apply_test_widgets`)
  en vez de una tabla que se reconfigura: el ABR y el ECochG no comparten ni una
  medida --ondas I-V e interpicos contra razones PS/PA-- y una tabla que sirviera
  para los dos iba a ser una con la mitad de las filas vacías siempre.
- **Solo el PA se pega al trazo.** La línea de base y el hombro del PS caen donde
  el alumno haga clic: ahí es donde decide, y de esa decisión sale la razón que
  informa. Pegarlos habría convertido el examen en apretar cuatro botones.
- **La marca recién puesta avisa solo en el ECochG** (`AbrGraph.notify_create`).
  En el ABR la marca la pone `measure_action` DESPUÉS de escribir la tabla con
  los valores de los cursores (latencia A, amplitud pico-pico A-B); avisar ahí
  habría pisado esos valores con la coordenada cruda del trazo.
- **El menú contextual "Eliminar marcas" se arma con las marcas de la prueba**
  y no con las cinco ondas fijas: un ECochG no tiene onda III.
- **El inicio del complejo no se marca**: es el último punto antes del PS en que
  el trazo seguía pegado a la base (dentro del 10% de la altura del PS). Pedir
  una quinta marca para un punto que el trazo ya define era ruido.
- **El corrimiento por tasa se arma con todas las curvas medidas del oído**, no
  con la seleccionada, y la fila dice entre qué dos tasas comparó: 0.3 ms entre
  11 y 21/s y entre 11 y 91/s no significan lo mismo.

Cubierto por `tests/test_ecochg_panel.py` (la costura completa: combo → equipo →
captura → marcas → tabla) y `tests/test_ecochg.py` (el modelo).

### El caso y el informe (2026-09-21, misma tanda)

El bloque `ecochg` viaja **dentro** del bloque ABR de cada oído
(`cases.data['ABR']['OD']['ecochg']`) y no en una clave propia: es la misma
prueba en el mismo equipo, una opción del combo de potenciales, y el cliente ya
lee ese diccionario como `preferences`. Tres campos: `sp_ap` (la razón medida
con electrodo TIMPÁNICO, que es la posición de referencia), `tasa` (cuánto más
se adapta el PA que uno sano) y `rar_cond_ms` (separación entre polaridades).

- **La microfónica no tiene campo propio**: se copia del patrón retrococlear
  (`neural.microfonica`). El ABR y el ECochG registran LA MISMA microfónica con
  distinto electrodo, y dos campos para el mismo potencial terminan
  contradiciéndose.
- **El eje `ecochg` del cuadro está solo en `meniere` e `hidrops_retardado`**,
  y el rango arranca sobre el límite pero pasa por el borde (0.42-0.68): un
  Ménière con la razón en 0.42 es tan real como uno en 0.65, y es el que obliga
  a mirar la razón de áreas. Un test verifica que ningún otro cuadro lo declare
  y que los rangos quepan en los topes del formulario.
- **Un oído sano tampoco sortea siempre el mismo número** (0.15-0.32): un valor
  calcado delata cuál es "el" valor normal.
- **Un campo fuera de rango se recorta, no rechaza el guardado**
  (`CaseForm::clampNum`): son parámetros de modelado, no datos clínicos, y
  frenar un caso entero por una razón en 1.5 cuesta más de lo que evita.
- **Cambiar de prueba en el combo borra las curvas, y pregunta antes.** El ABR y
  el ECochG no se apilan en el mismo gráfico (ventanas distintas, y el ECochG
  tiene el PA hacia abajo) y el informe se sube con UN tipo. Se descartó
  permitir sesiones mezcladas: el informe habría quedado mal rotulado o habría
  que subir dos, con las mismas imágenes en los dos.
- **El informe sube como `ELECTROCOCLEO`** y `ReportPdfBuilder::ecochgBody` lo
  imprime con sus medidas, sin el gráfico latencia-intensidad: el ECochG no se
  registra en serie descendente. El corrimiento por tasa va aparte porque es una
  comparación entre dos curvas, igual que la razón de asimetría del VEMP. El PDF
  no interpreta nada -- qué razón es patológica lo dice quien informa.

### "No veo que promedie": tres bugs del ruido (2026-09-21)

El docente probó y dijo que la curva se ve igual desde el primer barrido. Era
cierto, y detrás había tres cosas distintas. Un primer parche
(`ELECTRODE_NOISE_GAIN`: hacer que el electrodo de oído tomara más ruido) se
escribió y después se sacó -- tapaba el síntoma de la primera.

**1. El ruido del paciente dependía de qué prueba se corría.** `sigma` se
despeja de la referencia que declara el caso ("a tal nivel hicieron falta
tantos barridos"), y la curva de esa referencia se armaba con la morfología de
la prueba activa. Al nivel de referencia --que es el umbral-- el potencial de
sumación vale cero, así que la referencia del ECochG daba ~0, `sigma` caía al
piso (`MIN_PATIENT_SIGMA_UV`) y **el mismo paciente resultaba cuatro veces más
silencioso en ECochG que en ABR** (0.50 µV contra 2.22). Con la respuesta ocho
veces más grande, el complejo salía entero en el primer bloque. Ahora la
referencia se arma SIEMPRE con la morfología del tronco y se mide en la
ventana del tronco: el ruido es del paciente, no del examen.

**2. El rechazo de artefacto era el del ABR para todas las pruebas.** ±25 µV
con la banda del ECochG (10-3000 Hz, que deja entrar excursiones de base
mucho más grandes) descartaba dos tercios de los barridos. Eso no es un
paciente inquieto: es la banda, y se paga promediando el triple para nada.
Ahora cada protocolo trae el suyo (`Protocol.reject_uv`): 25 µV el ABR, 40 el
ECochG.

**3. El ancho de banda se cobraba como ruido parejo.** `band_noise_factor` dice
que con el pasa-alto en 10 Hz entra 3.16 veces más ruido que en 100, y ese
factor multiplicaba el ruido ENTERO. Pero en una ventana de diez milisegundos
no entra ni un ciclo de 10 Hz: lo que un pasa-alto bajo deja pasar son
períodos de 10 a 100 ms, o sea un escalón o una rampa por barrido, no pasto.
Se ve como una línea de base que se va para arriba o para abajo en cada
barrido --y en el promedio, como la ondulación lenta que tiene cualquier ABR
registrado en 3.3 Hz-- y una medida de base a pico se la come casi entera,
porque las dos marcas están a menos de un milisegundo y la ondulación las
mueve juntas.

Ahora el exceso entra con esa forma (`sweep_noise(band_factor=...)`: escalón,
rampa y un ciclo de seno/coseno, nada más rápido) y el RMS total sigue siendo
el mismo, así que el ruido residual que declara el equipo y el FSP no cambian.
Importa porque **la banda de 10 Hz es la obligatoria del ECochG**, no un error
del alumno: cobrándola como ruido de alta frecuencia, la razón PS/PA quedaba
con 40% de dispersión y no se podía separar un oído normal de uno con hidrops.

Resultado, a 2000 barridos con electrodo timpánico (12 capturas por fila):

| declarada | razón medida | razón de áreas |
|---|---|---|
| 0.25 | 0.232 ± 0.108 | 1.31 ± 0.52 |
| 0.40 | 0.380 ± 0.066 | 2.08 ± 0.80 |
| 0.55 | 0.546 ± 0.076 | 3.92 ± 1.80 |

Esa dispersión (±0.07-0.11) es la que reporta la bibliografía para el
test-retest de la razón de amplitudes, y es la razón de ser de la razón de
áreas. El ABR no cambia: con el pasa-alto en 100 Hz el residual sigue en 56 nV
y abrirlo lo sigue arruinando (77 nV en 33, 501 en 10, 928 en 3.3).

Cubierto por `test_the_trace_settles_while_it_averages`,
`test_getting_closer_to_the_cochlea_buys_signal_to_noise` y
`test_the_band_does_not_charge_high_frequency_noise_for_low_cuts`.

### Marcado automático (2026-09-21)

Botón `Auto` en la barra de marcas: pone las cuatro y de ahí salen las medidas,
como cualquier equipo real (el clínico corrige después). Detecta **sobre el
trazo** y nada más -- no mira el caso, ni la razón declarada, ni la latencia
que el modelo usó para dibujar. Con la banda mal puesta o el nivel bajo marca
igual y la medida sale mal, que es lo que tiene que pasar.

Cómo encuentra cada punto y por qué:

- **PA: el PRIMER mínimo hondo del rango fisiológico (0.8-3.5 ms), no el más
  hondo.** Con un sumación grande el N2 corre montado sobre la meseta y llega a
  medir el 91% de lo que mide el PA, así que el mínimo absoluto se iba al N2
  justo en los oídos con más hidrops, que son los que importan. Se acepta el
  primer mínimo local que llegue al 80% del más hondo.
- **FIN: el primer punto en que el trazo vuelve a pegarse a la base** (dentro
  del 10% de la profundidad del PA), no un cruce estricto: basta un poco de
  deriva lenta para que el trazo se quede del lado de abajo toda la ventana y
  el retorno no exista, justo en los registros donde importa.
- **PS: por convención, a `SP_SHOULDER_MS` del PA.** Se probaron tres
  detectores geométricos y ninguno aguantó: (1) caminar hacia atrás desde el
  pico hasta que la bajada afloje -- pone la marca encima del propio PA, porque
  acercándose a un mínimo la pendiente vuelve a cero sola; (2) el primer cambio
  de signo de la curvatura después de la caída más pronunciada -- no encuentra
  nada en los oídos normales y se dispara en los demás; (3) el punto menos
  empinado entre la caída y el pico -- queda pegado al PA (razón 0.75-0.92).
  El motivo de fondo: con un click el complejo entero dura alrededor de un
  milisegundo y los dos potenciales se superponen, así que el hombro no tiene
  firma geométrica confiable. Es una limitación real de la técnica con click
  --por eso los protocolos fijan el punto en vez de buscarlo-- y no del
  simulador. Fijar el INSTANTE no regala el resultado: la amplitud sale del
  trazo igual.

Qué tan bien anda, contra la razón que declara el caso (6 capturas por celda):
conducto ±0.13 (y a veces no encuentra el complejo), timpánico ±0.04,
transtimpánico ±0.02. Es el mismo orden que la dispersión del marcado manual:
el marcado automático no arregla un registro malo.

De paso quedó medido el efecto de la banda sobre la razón, con el marcado
automático como regla fija (declarada 0.55): pasa-alto en 10 Hz da 0.558, en
33 Hz da 0.580, en 100 Hz da 0.497 y en 200 Hz da 0.380. No es que el
sumación "desaparezca" con la banda del ABR --eso pasaba con el bug del padding
de la época, ya arreglado-- sino que se subestima, tanto más cuanto más alto el
corte. La constante de tiempo de un corte en 200 Hz es 0.8 ms y la meseta dura
un par de milisegundos.

Queda por decidir si el botón lo ve el alumno o solo el docente. Hoy lo ven los
dos: los equipos reales marcan solos y reconocer una marca mal puesta es parte
del examen. Sacarlo para el alumno es esconder el botón en `EcochgTable._build`.

### Mirarlo de verdad, y separar el generador (2026-09-21)

El docente probó otra vez: "no logro ver nada de electrococleo, no veo
promediaciones ni animación fluida". Todo cierto. Hasta acá se había validado
solo con tests headless, que confirman números y no miran el gráfico. Se
exportó el trazo a JPEG y se lo miró: **era ilegible**. Cinco cosas.

**1. El generador está separado** (`src/abr/ECochG_generator.py`), que es lo que
pidió el docente. Era una rama adentro de `ABRGenerator.generate_curve` y ahora
es su propio `generate_curve` con su propio flujo: sin curva sombra, sin canal
contralateral, sin falsa onda V, sin reflejo post-auricular, con su ventana de
FSP. Lo que sí se comparte es el EQUIPO --normativa, ondas, ruido, filtros,
electrodos, rechazo-- importando las piezas de `ABRGenerator`, porque ahí es
donde viven y duplicarlas era garantizar que se desincronizaran. `ABR_Curve`
volvió a ser solo del ABR.

**2. La escala del gráfico no seguía al electrodo.** El ABR se dibuja en 6 µV
de alto porque sus ondas son de medio µV. Un ECochG timpánico tiene el PA en
3.5 µV: se salía por abajo y se pisaba con la curva de al lado. Ahora la
escala sale del electrodo (`ecochg.display_scale_uv`: 2 µV por unidad de
ganancia, o sea 5 / 16 / 50 µV) y el apilado la sigue. Es lo primero que
cambia entre un registro y el otro y estaba clavado.

**3. La morfología estaba estirada para que diera un número.** `SP_TAIL_MS`
estaba en 1.35 ms para que la razón de áreas llegara al 1.94 publicado, y el
precio era que el trazo dejaba de parecerse a un ECochG: en vez de una espiga
con un hombro quedaba un bolsón ancho del que no se sacaba ni dónde estaba el
PA. Se bajó a 0.6 ms (que es lo que dura con click) y la ventana de 10 a 6 ms.
La razón de áreas terminó dando 1.95 en el límite de amplitudes igual, porque
el punto 5 mejoró la relación señal/ruido. Morfología primero.

**4. La promediación llegaba al tope en el 40% de la captura.** `graph()` pasaba
`count * total * 2.5` como avance, que crece con la cantidad de ticks: el
promedio se completaba a un tercio de camino y el resto de los ticks
redibujaban el mismo trazo. **Esto ya pasaba en el ABR.** Ahora pasa la
FRACCIÓN (`count / total`) y la promediación avanza pareja de punta a punta:
el ABR va de 24 a 2000 barridos aceptados con el residual cayendo de 554 a
63 nV, en vez de congelarse a mitad de camino.

**5. Tres cuadros por segundo.** `TIEMPO_ENTR_PROM` era 300 ms. Un tick cuesta
~30 ms de cálculo, así que había lugar de sobra: ahora es 100 ms y la cuenta de
ticks se multiplicó por tres (`CUADROS_POR_TICK_VIEJO`), así que la captura
dura exactamente lo mismo repartida en el triple de cuadros.

Cómo quedó, con el marcado automático sobre el trazo (8 capturas por celda):

| electrodo | declarada 0.25 | 0.40 | 0.55 |
|---|---|---|---|
| conducto | 0.308 ± 0.044 | 0.471 ± 0.047 | 0.526 ± 0.176 |
| timpánico | 0.232 ± 0.010 | 0.398 ± 0.015 | 0.532 ± 0.029 |
| transtimpánico | 0.182 ± 0.006 | 0.288 ± 0.005 | 0.399 ± 0.006 |

(las dos últimas columnas del conducto y del transtimpánico van contra sus
propios límites, 0.50 y 0.30, no contra 0.40)

Y el efecto de la banda, que es el ejercicio: con el pasa-alto en 10 Hz una
razón declarada en 0.55 se mide 0.532; en 100 Hz, 0.380; en 200 Hz, 0.080.

**Sigue sin probarse en la app corriendo de verdad.** Lo que se verificó acá es
el trazo exportado a JPEG desde la ventana real, con sus marcas y su tabla.

### Lo que falta

- Nada de esto se probó en la app real ni en el navegador todavía: el hosting
  local no tiene `pdo_sqlite`, así que las vistas PHP se validaron con `php -l`,
  balance de `<div>` y `node --check`.
- La **ficha de estudio** (PDF del docente) no muestra ECochG todavía.

## El test del timpanograma fallaba una de cada cuatro corridas (2026-09-21)

`tests/test_z_generator.py` era intermitente y venía de antes: en el árbol
anterior a todo el ECochG falla 8 de 25 veces, y en el de ahora 4 de 25. Es la
misma tasa -- la diferencia es el sorteo.

Importa porque una suite con un test que falla solo deja de servir para lo
único que sirve. En esta misma sesión mandó a buscar un bug inexistente en el
módulo de impedanciometría, que ni siquiera importa nada de `abr`.

Eran dos tolerancias puestas justo en el borde de la aleatoriedad que el
propio generador declara:

- **Compliance** (`test_el_mismo_paciente_lee_siempre_lo_mismo`): el jitter por
  barrido multiplica cada lectura por un uniforme en [0.97, 1.03], así que dos
  lecturas pueden diferir 6%, y la tolerancia era 5%. Además la compliance se
  informa redondeada a dos decimales, y en las curvas rígidas (As, Cs:
  compliance ~0.1) ese paso de 0.01 pesa más que el jitter, cosa que una
  tolerancia puramente relativa no cubre nunca. Ahora es `7% + 0.02`.
- **Gradiente** (`test_el_ancho_viaja_en_el_dataset`): se mide sobre la curva ya
  dibujada, que lleva ruido encima, así que reconstruirla no da el mismo número.
  En las rígidas el pico es chico y el ruido el mismo, así que son las menos
  reproducibles: sobre 300 reconstrucciones el percentil 95 da 0.08 y el peor
  caso 0.13. La tolerancia era 0.05; ahora es 0.15.

No se tocó el generador: la aleatoriedad es deliberada (el mismo paciente
tiembla un poco entre lecturas, que es lo que hace un equipo real). Lo que
estaba mal era lo que el test esperaba de ella. Medido: 0 fallas en 100
corridas.

## Y el del recién nacido fallaba media jornada (2026-09-21)

Mismo patrón que el del timpanograma, en el backend: `test_case_form.php`
exigía que un bebé de diez horas de vida hubiera nacido HOY. Qué día sea
depende de la hora a la que se corra la suite -- diez horas antes de las nueve
de la mañana es ayer --, así que fallaba durante las primeras diez horas de
cada día. A qué hora de pared corresponde eso depende de la zona que tenga
configurada el PHP donde corra: en este entorno de desarrollo es UTC, en el
hosting no se sabe (el repo no fija ninguna, sale del php.ini del servidor).

También venía de antes: se comprobó corriendo la suite en el árbol anterior a
todo el ECochG (4189 asserts, mismo fallo).

Ahora se exige lo que importa: que la fecha salga de las horas de vida y no de
un sorteo, que sea hoy o ayer según la hora, y que nunca caiga adelante.
Verificado a las 0, 3, 9, 10, 11, 18 y 23 horas.

**Los dos tests intermitentes juntos hacían que la suite completa no pudiera
usarse como semáforo**, que es exactamente para lo que hace falta cuando se
toca el motor compartido.

### El reloj: una sola zona, declarada, y un reloj para verla (2026-09-21)

`src/Clock.php`, `api/clock.php` y el bloque de reloj en admin/index.php
(Estado). Había tres relojes que no se hablaban:

1. **SQLite**: `CURRENT_TIMESTAMP` es UTC, siempre.
2. **PHP**: `date()` usa la zona del php.ini del hosting, que el repo no fijaba
   -- así que el mismo código daba fechas distintas en el servidor y en
   desarrollo, y no se podía saber cuál desde afuera.
3. **La pantalla**: algunas fechas se convertían a mano a America/Santiago
   (`patients.php`) y otras no (`CaseBuilder::fechaNacFromHoras`, con `date()`).

El síntoma era el test del recién nacido: un bebé de pocas horas podía quedar
con fecha de ayer según la hora y la zona del servidor.

**Lo que se hizo**: `bootstrap.php` fija la zona de la aplicación en cada
request, así que el php.ini deja de importar. Se guarda en UTC, se calcula y se
muestra en `Clock::ZONA`. Probado con cuatro hostings imaginarios muy separados
(Madrid, Tokio, UTC, Kiritimati): el mismo código da el mismo resultado en
todos (`test_clock.php`).

**Lo que NO se hizo, y es la parte importante de la decisión.** El docente
propuso que la app leyera la zona del PC y se hiciera un "match" con el
servidor. Para los DATOS eso es un error: las horas de una cita son del CURSO,
no del que las mira. Con render por zona del cliente, dos alumnos de la misma
clase con los relojes distintos verían horarios distintos para la misma cita, y
el que tuviera la zona mal configurada llegaría tarde convencido de que llegaba
a tiempo -- el error se volvería invisible en vez de evidente.

La zona del cliente sí se lee, pero solo para AVISAR que no coincide:
- `admin/index.php` muestra la zona de la app, la hora del servidor, la que
  trae el php.ini, si la base está realmente en UTC, y compara contra el reloj
  del navegador.
- `BackendClient.clock_skew()` hace lo mismo desde la app de escritorio,
  comparando contra el epoch UTC del servidor (lo único que no depende de
  zonas). Tolerancia de 2 minutos: menos que eso es latencia y deriva normal,
  más que eso mueve una cita de hora.

Queda por decidir DÓNDE avisa la app de escritorio: hoy `clock_skew()` existe y
está testeada pero no la llama nadie. El lugar natural es el arranque de sesión
o el mismo cartel que ya informa "sin conexión".

**Lo que sigue sin saberse, y no hace falta**: en qué zona está el php.ini del
hosting. Antes era necesario y no se podía averiguar; ahora el reloj de Estado
lo muestra y, sobre todo, ya no cambia el comportamiento.

## Biblioteca de fichas: carpetas y archivado (sin probar en el navegador)

`admin/patients.php` pasó de "una lista con todo" a una biblioteca que se
puede mantener: carpetas, archivado y acciones en tanda (`src/CaseLibrary.php`,
`cases.folder_id` / `cases.archived_at`, tabla `case_folders`). Lo decidido, y
por qué, para no rediscutirlo:

- **Una carpeta por ficha, no etiquetas.** Una ficha vive en un lugar, como un
  archivo, y así "mover" se entiende sin explicar. Si alguna vez hace falta que
  una ficha esté en dos lados a la vez, eso son etiquetas y es otra tabla, no
  este campo.
- **Carpetas planas, sin árbol.** Con doscientas fichas lo que ordena es
  separar por semestre o por práctica; un árbol obliga a navegar en vez de
  filtrar y esconde justo lo que se busca.
- **Borrar una carpeta no borra fichas**: quedan sueltas (`folder_id = NULL`).
  Que "eliminar carpeta" se llevara doscientos casos armados sería la peor
  sorpresa posible de esa pantalla.
- **Archivar es reversible y no toca nada más**: la ficha sale de la lista y
  del selector de "agendar caso nuevo" (`agenda.php`), pero sus citas,
  atenciones e historial quedan intactos, y una ficha archivada con citas
  vivas se sigue atendiendo. Es el lugar donde van a parar los casos de
  semestres pasados sin tener que decidir si se borran.
- **Archivadas es una VISTA aparte, no un filtro más de la barra**: lo
  archivado no se mezcla con lo vivo ni por accidente.
- **El borrado en tanda informa el impacto antes y después**: el confirm dice
  cuántas fichas, y el mensaje de vuelta cuántas citas y atenciones de alumnos
  se llevó puestas (`CaseLibrary::impactoDeBorrado`). Todo en una transacción:
  una tanda interrumpida no puede dejar casos sin citas y citas sin atenciones.
- **Densidad**: el comentario del docente tenía columna propia de 22rem y un
  párrafo por fila -- tres casos llenaban la pantalla. Ahora va recortado a
  una línea bajo el nombre, con el texto completo en el tooltip, y las nueve
  columnas quedaron en seis (Ficha, Estado, Uso, Autoría, Acciones).

**El orden de la migración importa**: `migrateCaseLibraryIfNeeded` va ANTES
del paso `schema.sql` en `admin/database.php`, porque ese archivo trae un
`CREATE INDEX ... ON cases(folder_id)` que en una base ya existente muere con
"no such column: folder_id" (pasó en el hosting). Y la migración se salta sola
si `cases` todavía no existe: en una instalación nueva la crea schema.sql, ya
con las dos columnas.

**Qué se probó y qué no**: acá no hay `pdo_sqlite`, así que las dos secuencias
(base existente con el schema viejo, y base vacía) se replicaron en SQLite con
Python, junto con las consultas nuevas -- carpetas, impacto del borrado, lista
filtrada, selector de agenda sin archivadas, borrado en tanda y borrar carpeta
sin perder fichas. Falta verlo en el navegador: la barra de acciones en tanda,
el menú de carpetas y la densidad de la tabla.
