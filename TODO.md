# TODO

Solo lo pendiente. El porqué de cada punto, y todo lo ya hecho, está en
`docs/decisiones.md`: el "§" de cada ítem es el título de la sección allá.
Al cerrar un ítem se borra de acá; si deja una decisión, va como sección nueva
en `docs/decisiones.md`.

Cada ítem tiene un número fijo para nombrarlo. Al cerrar uno no se renumera
el resto; un ítem nuevo toma el número siguiente al más alto (hoy 56).

Revisado contra el código el 2026-09-24.

## Bugs conocidos

- [ ] 1. `response.py:response_sdt_w_mkg` (mano levantada del SDT) exige el
      stim 5 (Speech Noise): con cualquier otro ruido baja la mano siempre.
      Además usa el modelo viejo de rango + curva sombra, distinto del "mejor
      de las dos vías" de `CalculateLogo`: dos modelos para el mismo
      fenómeno. § El update mentía la versión
- [ ] 2. `Audiometer._mkg_on` exige `"Invertido"` en el canal del ruido: en
      Normal el ruido suena pero no llega al motor y no enmascara. Lo que se
      oye y lo que se simula no coinciden. § El update mentía la versión
- [ ] 3. "Sin respuesta" (130) en el cliente: `src/audiometria/` y `src/abr/`
      leen `Aerea`/`Osea` crudos y tratan el 130 como 130 dB HL (el backend
      ya lo recorta al tope). § "Sin respuesta" (130) ya no es un umbral de
      130 dB
- [ ] 4. La tonal no distingue "no se midió" de "no respondió": las dos se
      guardan 130. Hace falta una marca por frecuencia (casilla o valor
      reservado) antes de poder cargar un caso con frecuencias sin probar.
      § "Sin respuesta" (130) ya no es un umbral de 130 dB
- [ ] 5. Voces de logoaudiometría: `ListWords.la_super` fuerza `feme1` porque
      no hay voces `male` grabadas. Falta grabar `male1`/`male2` (palabras +
      `none1/2/3`), decidir qué representa el número de voz y sacar el
      forzado. § Voces de respuesta logoaudiometria (ListWords.py)
- [ ] 6. El PDF del caso siempre dibuja ABR/VEMP con la normativa por defecto:
      no consulta la del curso (`AppConfig`, `normative_data.abr`).
      § Los trazos del PDF no son el generador
- [ ] 7. Ningún test compara `CaseWaveforms::CLICK_BASE` y
      `CaseOae::TEOAE/DPOAE/SFOAE/SOAE` contra `resources/*/normative_data.json`:
      se copiaron a mano. § Los trazos del PDF no son el generador
- [ ] 8. Un override de normativa por curso guardado con la clave vieja
      `ls_chirp` se aplica en el cliente (alias), pero `normativas.php` no lo
      muestra bajo "CE-Chirp LS". § ABR: catálogo real de estímulos y vía
      ósea que sí cambia el trazo
- [ ] 9. El informe de otoscopia no se guarda local: sin conexión, al cerrar la
      atención se pierde (el autosave de 30 s lo mitiga, pero solo sube).
      § Otoscopia: cono del espéculo e informe por cuadrantes

## Decisiones pendientes

Pedagógicas o de la docente; bloquean lo que cuelga de ellas.

- [ ] 10. **Dilema de enmascaramiento.** `_masking_calc` hace `sorted` al rango
      imposible y el paciente responde igual. Elegir: (a) dejarlo y que solo
      lo delate el panel, (b) que no responda en toda la franja, (c)
      sobreenmascaramiento gradual como en `CalculateLogo`. Con (b)/(c):
      sacar el `sorted`, revisar `_resolve_masked_threshold`,
      `response_*_w_msk` y `_decay_*`, y antes los casos armados con gap
      bilateral ≥ 40 dB. Pensar el inserto como salida (hoy la IA tonal es
      fija, sin supraaural/inserto). § Dilema de enmascaramiento
- [ ] 11. **Efecto oclusivo: fuente de la tabla** `[15,15,15,10,0…]`. Preguntarle
      a la docente (Studebaker y Yacullo crecen hacia los graves) y anotar la
      fuente en `oclusive_efect`. Los insertos casi lo anulan y no están
      modelados. § Valores por frecuencia: se dejan los de la docente
- [ ] 12. **CE del ruido enmascarante.** Confirmar `CE_TONAL` con la docente y si
      la cátedra suma un margen de seguridad fijo. Decidir si el equipo
      impide elegir un ruido que no corresponde a la prueba. § Tipo de ruido
      enmascarante y CE
- [ ] 13. **Curva sombra en logoaudiometría**: preguntarle a la docente qué
      discriminación espera en una anacusia unilateral. § Curva sombra en
      logoaudiometría
- [ ] 14. **Pediatría.** ¿Se implementan VRA y juego condicionado, o el caso
      pediátrico va solo por vía objetiva? ¿La edad la fija el docente o la
      sortea el generador? (La sonda de 1000 Hz ya está resuelta.) Después
      de decidir: las tres capas (coherencia en la ficha, paciente que no
      cierra umbral, registro del intento). § Edad del paciente
- [ ] 15. **¿Los pacientes están congelados o envejecen?** Sugerencia anotada:
      congelar todo y agregar al recién nacido "horas de vida al momento de
      la cita". § A decidir: ¿los pacientes están congelados o envejecen?
- [ ] 16. **Gradiente del timpanograma**: acá 1 = curva ancha, la de Brooks es al
      revés (`1 - esto`). Dar vuelta la resta toca `Z_225._calc_gradient`,
      `Z.move` y `CaseCharts::gradienteDe`. § Rangos de compliance y presión
      por letra
- [ ] 17. **Razón V/I del ABR** (piso normal pasó a 1.0): `v_i_factor` (default
      0.45, ayuda "1.0 = sin caída") ¿se renombra o se recalibra? ¿El límite
      normal sale de `amplitude_v_i_ratio` por población en vez de una
      constante? ¿Los `ABR_NEURAL_PRESETS` siguen dando el contraste?
      § La razón V/I normal es mayor que 1
- [ ] 18. **Efecto de oclusión en el ABR óseo** (postergado con aval del docente):
      pesa cuando haya tone burst de 500 Hz óseo con supraaural contralateral;
      hay que decidir si el panel declara el fono del ruido. § Umbral,
      polaridad y sobreenmascaramiento: los cuatro puntos
- [ ] 19. **Marcado automático del ECochG**: ¿lo ve el alumno o solo el docente?
      Hoy los dos. § Marcado automático
- [ ] 20. **Aviso de reloj desfasado en la app**: `BackendClient.clock_skew()`
      existe y está testeada, pero nadie la llama. ¿Al iniciar sesión o en el
      cartel de "sin conexión"? § El reloj: una sola zona
- [ ] 21. **F5 de cursos (ciclo de vida)**: `code`/`term`/fechas, clonar curso,
      purga por semestre, export CSV. A conversar: cómo se llama el periodo,
      qué arrastra "clonar", qué pasa con el semestre viejo. De esto depende
      que "Todos mis cursos" de la bandeja incluya cursos inactivos.
      § Rediseño de la gestión de cursos en el backend

## Funcionalidades

### Build y arranque
- [ ] 22. Achicar el build (~90 MB, solo `LabSim.spec`): tema GTK, QtQuick/Qml,
      Qt6Pdf, plataformas no-xcb, traducciones, imageformats sobrantes. No
      sacar QtMultimedia/FFmpeg, QtNetwork, QtOpenGL/QtSvg/QtTest. En
      Windows revisar además `opengl32sw.dll`. Probar que arranque y suene.
      § Build más liviano y arranque más rápido
- [ ] 23. Arranque ~2 s más rápido: importar `scipy.signal` dentro de las
      funciones (`abr/ABR_generator.py`, `vemp/engine.py`, `abr/smooth.py`) y
      precargarlo en un hilo después del login. § Build más liviano

### Otoscopia: derivación + aprobación docente + fase por alumno
Hoy todo alumno ve la fase 1 (`FASE_FIJA = 0` en `Otoscopia.py`).
§ Otoscopia: derivación + aprobación docente + fase por alumno
- [ ] 24. Derivación del alumno al cerrar la atención (`attendance_action.php`,
      `atendido`), separada de la nota general.
- [ ] 25. Bandeja docente para aprobar/rechazar derivaciones por alumno-paciente.
- [ ] 26. Tabla de progreso alumno-paciente (fase aprobada de cada uno).
- [ ] 27. Motor de selección de fase (clamp a la última), también en la app,
      mostrando el texto libre de la fase.
- [ ] 28. Aviso al alumno al aprobar/rechazar (`inbox_messages`).
- [ ] 29. Historial de derivaciones (quién, cuándo, quién aprobó).
- [ ] 30. Reglas de reintento tras un rechazo.
- [ ] 31. Otoscopía neumática y checklist de membrana sin localización (como
      OtoReport); hoy no se simula insuflación.

### Parámetros de audiometría configurables por curso
Candidatos: efecto oclusivo, IA aérea/ósea/habla, CE, PTA, `GAP_MAX_DB`,
gap significativo. § Parámetros de audiometría configurables por curso
- [ ] 32. Definir la key (`audiometry_params`, un solo blob).
- [ ] 33. Juntar los literales en un `audiometria/params.py` que consulte
      `app_config_store` con el valor actual como default.
- [ ] 34. Entrada en `src/CourseParams.php`, con límites que impidan valores
      imposibles y ayuda mecánica.
- [ ] 35. Confirmar qué pasa con los casos armados cuando un curso cambia un
      parámetro.
- [ ] 36. Unificar `GAP_MAX_DB` (hoy en cliente y backend).
- [ ] 37. CE dependiente de la frecuencia. § Tipo de ruido enmascarante y CE
- [ ] 38. Atenuación interaural del habla por bandas en vez del escalar 45.
      § Curva sombra en logoaudiometría

### Catálogo de cuadros: lo que el motor no puede armar
§ Catálogo de cuadros: lo que el motor todavía no puede armar
- [ ] 39. Reflejo presente con gap (dehiscencia de canal superior, acueducto
      vestibular dilatado).
- [ ] 40. Ósea supranormal (tercera ventana, Pendred, Mondini).
- [ ] 41. Eje temporal / fluctuación (Ménière, CMV, NIHL, salicilatos, tuba
      abierta). El cambio más grande.
- [ ] 42. Asimetría declarada por el cuadro (autoinmune, CMV).
- [ ] 43. Otoscopia ligada al cuadro (OMA, colesteatoma, perforación, glomus,
      atresia).
- [ ] 44. Timpanograma "no registrable" en `Z_OPTIONS`.
- [ ] 45. Eje no orgánico (inconsistencias, SRT vs PTA, Stenger).
- [ ] 46. Procesamiento auditivo central (pruebas dicóticas).
- [ ] 47. Hiperacusia / misofonía como eje del perfil.

### ABR
- [ ] 48. Conectar al modelo los 17 parámetros de `UNCONNECTED_SETTINGS`
      (envolvente del burst, ventana, notch, suavizado…): leerlo, testearlo y
      sacarlo de la lista. § Parámetros avanzados del ABR
- [ ] 49. Normativa: el tramo de 1 a 3 años cae en `child` (valores de adulto);
      burst de 1-4 kHz sigue derivado. § ABR: normativa anclada en bibliografía
- [ ] 50. Ficha PDF: tabla de umbrales por vía ósea (`umbral_por_estimulo_oseo`
      ya se calcula). § ABR: catálogo real de estímulos
- [ ] 51. Ficha de estudio: mostrar el ECochG. § Electrococleografía: el motor

### EOA
- [ ] 52. Parámetros propios del TEOAE en la ficha (reproducibilidad,
      estabilidad, nivel del click, barridos, jitter; y supresor SFOAE,
      L1/L2 DP) por oído en `cases.data['EOAS'][lado]`, leídos por el
      cliente y mostrados en el PDF. § La ficha de OEA no configura las
      transientes

### VEMP
- [ ] 53. Umbral y sintonía editables en la ficha (`_vemp.php`,
      `CaseForm::parseVemp`) para armar un hidrops a mano. § VEMP v2
- [ ] 54. Impedancia de electrodos (un campo más de `Ajustes`). § VEMP v2

### Impedanciometría
- [ ] 55. Compliance y presión exactas en la ficha: sortearlas en el backend al
      crear el caso y que la app las lea. § La compliance y la presión del
      timpanograma no se pueden anticipar

### Menores
- [ ] 56. Los `print()` de ABR, EOA y VEMP son de error; si algún día imprimen
      datos del caso, pasarlos a `debug_print`. § Consola: los volcados de
      depuración solo para docente
