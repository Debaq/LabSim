# Roadmap de estilo

Rediseño visual de LabSim. Referencia: el módulo VEMP (tarjetas blancas sobre
lienzo gris azulado, un solo acento morado, OD rojo y OI azul en todo).
Actualizado 2026-10-26 (tarde).

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
- [x] Lienzo del MDI con `tema.FONDO`; logo de marca de agua al 18 %.
- [x] Login: campos y botón con la paleta, enlaces en el acento (tamaño intacto: lo fija el
  servidor, 410x140).

### Otros
- [x] VEMP: referencia, sin cambios de diseño.

## Falta

### ABR
- [ ] Probar en la app real (solo se vio en renders offscreen).
- [ ] Decidir si `btn_norm_guides` (guías de norma, oculto) va o no.
- [ ] Revisar el panel de Marcas con ECochG y corticales con curvas marcadas de verdad.

### Resto de módulos
- [ ] AABR, EOAS (OAE), Audiómetro, Acumetría, Otoscopia, Z, Lista de palabras.
- [ ] Los que se crean sin `expand=True` en `main.py` probablemente tienen el mismo
  espacio vacío abajo: revisar cada uno.
- [ ] Probar la barra nueva en la app real (solo se vio en un render offscreen con botones de prueba).
- [ ] Agenda y fichas (Ficha clínica, Evolución, Chat).

### Transversal
- [ ] Bajar el exceso de blanco/claro en toda la app: la barra de estado, los módulos ya
  hechos (ABR, VEMP) y lo que falta. Decidir si se tiñe más con morado suave.
- [ ] Probar todo a 1366×768 / 1280×720 / 1024×768 con las resoluciones reales de los PC.
- [ ] Rellenar `tema.py` con lo que falte al ir sumando módulos (que no se copie color
  entre módulos).

## Relacionado

- Medición de tiempos en terreno: `core/tiempos.py`, `scripts/resumir_tiempos.py`. Con los
  datos de los PC se decide si el cuello es el dibujo, la red o los motores (Rust).
