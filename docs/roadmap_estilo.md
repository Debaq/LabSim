# Roadmap de estilo

Rediseño visual de LabSim. Referencia: el módulo VEMP (tarjetas blancas sobre
lienzo gris con tinte morado, un solo acento morado, OD rojo y OI azul en todo).
Actualizado 2026-10-27.

## Reglas

- **Resolución:** la mayoría de los PC del laboratorio es menor que la del autor.
  Todo diseño se prueba a 1366×768, 1280×720 y 1024×768, no solo a la suya.
  Las resoluciones reales quedan en el evento `pantalla` de `core/tiempos.py`
  (archivos en `~/.local/share/LabSim/tiempos/`): leerlas al retirar los PC.
- **Alto antes que ancho:** el alto es lo que falta. Sobra ancho: se cambia por alto
  (paneles laterales angostos, nada apilado que se pueda poner al lado).
- **Colores en un solo sitio:** `src/core/tema.py` (paleta, QSS común, flechas de
  spinbox y combos, píldoras OD/OI). Cada módulo suma lo suyo (`abr/estilo.py`,
  `vemp/theme.py`). Los gráficos de pyqtgraph leen las mismas constantes.
- **Sin código muerto:** si algo ya no se usa con la integración a LabSim, se borra.
- **Marco MDI:** `FrameSubMdi(..., expand=True)` para que el módulo use todo el alto;
  sin eso queda en su alto natural y el sobrante se pierde en un espaciador.
- **No todo claro:** el rediseño viene quedando demasiado blanco/claro (nota del autor,
  2026-10-26). Blanco solo en tarjetas, botones y campos; barras, lienzos y fondos con
  tinte (`tema.LIENZO_APP`, gris azulado) o con más carácter. Revisar esto en cada módulo.
- **Paneles fijos, no QDockWidget:** los docks se anidaban mal (el monitor quedó en
  180 px de ancho). Layouts normales.

## Hecho

### Tema común
- [x] `core/tema.py` extraído del VEMP; VEMP sigue igual (`vemp/theme.py` reexporta).
- [x] Flechas de spinbox y combos (PNG dibujados en la carpeta de datos).
- [x] Pastilla OD/OI, tablas, pestañas, botones, campos de texto.

### ABR
- [x] Panel izquierdo (318 px) con fichas Configuración | Marcas.
- [x] Marcas: una grilla para los dos oídos (`abr/MarcasAbr.py`); `AbrTable` solo
  guarda datos y normativa. ECochG y corticales en la misma ficha, sin barras.
- [x] Monitor (EEG, FSP, datos de la curva) plegable; arranca plegado si la pantalla
  mide menos de 820 px de alto. Con la paleta.
- [x] Conclusiones en tres columnas a todo el alto (curvas | descripción | conclusión),
  sin título ni pestaña Esquema.
- [x] Latencia/Intensidad con la paleta y el resumen de curvas debajo.
- [x] Sin menú Archivo ni barra de estado; Parámetros avanzados es un botón al pie de
  Configuración.
- [x] Código muerto fuera (reloj, Caso siguiente, dock de valores, report_svg, modo OSCE
  estación 5, `AbrTableInfo`).
- [x] `expand=True` en el marco MDI del ABR.
- [x] Curvas OD/OI con la paleta, etiqueta de nivel suave.
- [x] Ancho mínimo bajó de 1121 a ~830 px; alto mínimo de 748 a ~490 px.
- [x] Lienzo más oscuro y paneles/tarjetas con borde marcado para distinguir sectores.
- [x] Marcas arrastrables con el mouse (la flecha corre pegada al trazo) y la bandera A'
  con Δ latencia/amplitud respecto de A. Las banderas A/A' se mantienen: son parte de lo
  que se enseña.

### Login y barra principal
- [x] Barra superior (34 px): pestañas de sección que se funden con la barra de abajo,
  botón Ingresar/Cerrar Sesión en píldora, botones de ventana sin caja.
- [x] Barra de módulos y acciones: fondo blanco con borde, botones con la paleta
  (activo = acento suave). Reglas por objectName en `dark.qss` para no filtrarse a los módulos.
- [x] Paleta de neutros con tinte morado (gris azulado chocaba con la barra): `tema.py`
  entero y `dark.qss` pasados; lienzo del MDI `tema.LIENZO_APP`; logo al 18 %.
- [x] Login: campos y botón con la paleta, enlaces en el acento (tamaño intacto: lo fija el
  servidor, 410x140).

### Agenda
- [x] Rehecha (2026-10-26): cabecera con título y subtítulo del día, vista Mi agenda | Práctica
  libre, navegación de día (‹ Hoy ›) y búsqueda; contadores por estado; tabla con columna
  Estado (icono + texto de color en vez de filas pintadas); estado vacío que explica qué hacer;
  panel del paciente elegido con los tres pasos (revisa la ficha → atiende → registra la
  evolución) y una pista de qué sigue. Piezas en `agenda/vista.py`.
- [x] Iconos de línea propios en `core/iconos.py` (QPainter, sin QtSvg). Usarlos en los demás
  módulos en vez de texto o símbolos.
- [x] Alto adaptable: el del servidor (580) es el mínimo y la agenda crece hasta casi todo el
  alto del área MDI (`ALTO_ADAPTABLE` en `ui_helpers.py`); se fija al abrirla, no sigue un
  cambio de tamaño de la ventana principal.
- [x] Tamaño de la ventana en `Layout.php`: 940x580 (antes 900x400). `FrameSubMdi(expand=True)`
  ya no deja la franja de 40 px abajo.
- [ ] Probar en la app real (solo renders offscreen con datos de prueba).
- [x] Ficha clínica: encabezado con el paciente y botón Hablar con el paciente; datos,
  puntualidad e historial como tarjetas con iconos (`core/ficha.py`, también en Mis pacientes).
- [x] Chat con el paciente: burbujas redondeadas que se adaptan al ancho (ventana de 440x500,
  antes 480x280), encabezado con la cara, estados, enviar con icono; tests en
  `tests/test_chat_ui.py`.
- [x] Iconos por examen y módulo (`core/iconos.ICONO_MODULO`) en pestañas, botones de módulo
  y de acción; con poco ancho (<1280) las acciones quedan solo con icono.
- [x] Evolución: encabezado, pasos de la atención y botón Guardar con icono.

### Otoscopia
- [x] Rehecha (2026-10-26): pestañas con subrayado y icono, una tarjeta por oído con píldora OD/OI,
  visor con esquinas redondeadas y estado vacío con icono, selector de espéculo con rótulo y pista;
  Informe con tarjetas por oído, rótulos de sección y paleta de hallazgos con la paleta de
  `tema.py` (los colores por hallazgo y el esquema ocre se mantienen: son los de OtoReport).
  `expand=True` en el marco MDI.
- [ ] Probar en la app real (solo render offscreen a 1000x580 y 1024x560).

### Acumetría
- [x] Rehecha (2026-10-26): mandos en una tarjeta angosta (diapasón y oído como botones
  segmentados, OD rojo / OI azul; pasos con icono) y la conversación en otra a todo el alto,
  con "Tú" y "Paciente" coloreados. `expand=True`. De paso: `_rinne_probado` nacía con la clave
  `conducto` y el resto del código usa `pabellon` (KeyError al comparar antes de cualquier cambio).
- [ ] Probar en la app real (solo render offscreen a 900x520 y 700x420).

### Lista de palabras
- [x] Rehecha (2026-10-26): sin acordeón ni pestañas. Estado arriba ("Última: palabra" y si el
  dictado del audiómetro está activo, con los dB), selector de las 5 listas y las 25 palabras de la
  lista elegida en una grilla de 5x5 a la vista. Las palabras ya dictadas se atenúan para no
  perder el hilo (se limpian al cambiar de caso). UI armada en código (`PALABRAS`, `GRUPOS`);
  borrados `Ui_ListWord.py` y `ListWord.ui`. Ventana 440x420 (antes 170x500), `expand=True`.
  Los botones conservan el nombre `btn_<lista><n>[_2]` que usa `pushaudio`.
- [ ] Probar en la app real: `Layout.php` cambió (W 440x420), hay que subir el backend.

### EOAS (OAE)
- [x] Solo el marco (2026-10-26): los gráficos de los cuatro paneles NO se tocan, el autor los da
  por buenos. Pestañas con subrayado, grupos de parámetros como tarjetas, OD rojo / OI azul al
  marcarse, Iniciar como botón principal (todo por QSS + propiedades desde `OaeMainWindow`, sin
  tocar el armado de los paneles). Informe en tarjetas: cabecera con evaluador/fecha/atención y
  lo capturado, hallazgos y conclusión lado a lado. `expand=True`.
- [ ] Probar en la app real; los paneles siguen con sus colores inline de estado (SOAE, métricas).

### AABR
- [x] Rehecho (2026-10-27): panel de configuración angosto (242 px) con el paciente arriba, oído
  como botones OD/OI y bloques Estímulo | Registro; cabecera con los cuatro pasos como stepper
  (número → check verde) e Iniciar/Detener; sonda y curva en una tarjeta (curva del color del oído,
  eje en µV sin el "x0.001", X fijo en 0-12 ms); barridos con barra fina, cuatro datos grandes y el
  veredicto en una caja propia (PASA verde / REFIERE rojo, con icono); informe en tarjeta con las
  píldoras OD/OI. `expand=True`. Mínimo ~890x570, entra en la ventana del servidor (980x620).
- [x] De paso, en `tema.py`: las flechas de los spinbox tapaban el borde derecho del campo y se
  veían "afuera" (`subcontrol-origin: border` → `padding`). Afecta a todos los módulos.
- [x] `tema.aplicar_estilo` pone `WA_StyledBackground`: los módulos que son `QWidget` (Acumetría,
  Otoscopia, Lista de palabras, Z) no pintaban el lienzo y quedaban con el gris del sistema.
- [ ] Probar en la app real (solo renders offscreen a 980x620 y 1024x590).

### Impedanciómetro (Z)
- [x] Marco nuevo (2026-10-27); la pantalla azul y sus gráficos NO se tocan (son los del equipo).
  La pantalla va en un bisel oscuro con las seis teclas blandas debajo, como teclas del equipo.
  Mandos en tres tarjetas: Prueba (Timpanograma, Reflejos, Tone Decay, ETF, marcada la que se ve),
  Mandos (perilla nueva, Leak, Presión ▲/▼, Estímulo como botón principal) y Equipo (oído OD/OI,
  sonda 226/1000 e IPSI/CONTRA como botones segmentados que muestran el estado; antes eran
  "OD/OI" e "IPSI/CONTRA" que alternaban sin decir cuál estaba puesto) e Imprimir.
  UI armada en código (`impedanciometria/control_ui.py`); borrados `Ui_Z_control.py` y
  `Z_control.ui`, y el botón Release, que no hacía nada. `expand=True`. Mínimo ~650x550.
- [x] `core/perilla.py`: QDial dibujado con la paleta (arco de recorrido o marcas si da la vuelta).
  Para los diales del audiómetro también.
- [ ] Probar en la app real; las capturas del manual del estudiante (§22) muestran el marco viejo.

### Audiómetro
- [x] Rehecho (2026-10-27) sin tocar la pantalla blanca del equipo (rótulos y vúmetros): va en una
  tarjeta, sin el bisel oscuro del Z (al autor no le gustó acá). Un canal por tarjeta (Salida,
  Estímulo, Transductor; perilla con Pulsado, Invertir y Estímulo; el canal 2 en espejo) y al
  centro Frecuencia, Pasos, Tiempo, Logoaudiometría, Talkback/Alternado y las perillas chicas de
  Monitor y Talkback. Las teclas marcan lo que está puesto, como las luces del equipo: Derecha
  rojo, Izquierda azul, el resto en el acento (se lee de los rótulos de la pantalla).
  Los widgets siguen saliendo de `Ui_Audiometer.py`; `audiometria/panel_ui.py` los reacomoda
  después de setupUi. `expand=True`. Mínimo ~730x500.
- [x] Perillas sin fin (intensidad, Leak del Z): marcas todas iguales; las gruesas sugerían una
  posición fija que un encoder no tiene.
- [ ] Probar en la app real con sonido.

### Otros
- [x] VEMP: referencia, sin cambios de diseño.

## Falta

### ABR
- [ ] Probar en la app real (solo se vio en renders offscreen).
- [ ] Decidir si `btn_norm_guides` (guías de norma, oculto) va o no.
- [ ] Revisar el panel de Marcas con ECochG y corticales con curvas marcadas de verdad.

### Resto de módulos
- [ ] Comandos de voz, Bandeja de entrada y Mis pacientes (ventanas internas) con el diseño nuevo.
- [ ] Decidir si los botones de módulo (OT, AC, A, Z...) muestran el nombre en vez del código.
- [ ] Los que se crean sin `expand=True` en `main.py` probablemente tienen el mismo
  espacio vacío abajo: revisar cada uno.
- [ ] Probar en la app real lo hecho el 2026-10-26: barra, login, agenda, ficha, evolución y
  chat (solo renders offscreen). `Layout.php` cambió (Agenda 940x580, Chat 440x500): hay que
  subir el backend para que los equipos lo reciban.

### Transversal
- [ ] Bajar el exceso de blanco/claro en toda la app: la barra de estado (sigue gris del
  sistema), los módulos ya hechos (ABR, VEMP) y lo que falta. La paleta con tinte morado
  gustó; falta aplicarla igual a lo que queda.
- [ ] Dos textos con `#1f2933` fijo (`core/secretaria.py`, `core/actualizacion_kiosko.py`) y
  el QSS de `abr/style_base.qss`: pasarlos a `tema.py`.
- [ ] Probar todo a 1366×768 / 1280×720 / 1024×768 con las resoluciones reales de los PC.
- [ ] Rellenar `tema.py` con lo que falte al ir sumando módulos (que no se copie color
  entre módulos).

## Relacionado

- Medición de tiempos en terreno: `core/tiempos.py`, `scripts/resumir_tiempos.py`. Con los
  datos de los PC se decide si el cuello es el dibujo, la red o los motores (Rust).
