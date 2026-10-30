# Roadmap nasal

Todo lo nasal del libro (H25 a H32, casos de los caps. 35 a 38) entra a
LabSim como **demo interna**: solo la ve el admin (permission 777), los
alumnos no. Decidido por él el 2026-10-29 ("todo en labsim, vamos a hacer
todo pero solo demos internas que no podrán ver los estudiantes por ahora").
Revierte la decisión del 2026-10-16 de dejar lo nasal fuera de LabSim
(§ Nariz: todo en LabSim, como demo interna, en `docs/decisiones.md`).

## Reglas

- **Cómo queda oculto:** dos boxes nuevos con `activo = false` y sus
  módulos en `state = 'development'` (`labsim_backend/src/Layout.php`). El
  alumno no ve la pestaña ni puede activar el botón; el admin los ve igual
  que hoy ve el Box Otoneurología (`_apply_admin_overrides_if_any` en
  `main.py`). Los códigos van en `GATED_MODULE_CODES` pero **no** en
  `Courses::MODULES`: el docente no los puede prender en un curso hasta que
  se decida soltarlos.
- **Sin datos del caso, el módulo no mide** (como el resto: nada de
  pacientes "normales" de relleno). Cada examen lee su bloque de
  `cases.data`.
- **El modelo es el de RinoSim** (`~/Escritorio/Proyectos/rinosim`), portado
  a Python con los mismos números: el mismo paciente y la misma semilla dan
  la misma curva que las figuras del libro. RinoSim sigue siendo la fuente de
  las figuras de H26/H27 y caps. 35/36; si cambia el modelo, cambia en los
  dos lados (prueba de equivalencia con números de referencia del JS).
- **Sin scipy** (numpy, `core/dsp.py` si hace falta filtrar).
- Pantallas de equipo con el estilo actual (`docs/roadmap_estilo.md`);
  probar a 1366×768.
- **Cada equipo registra cada acción y todas sus variables** en
  action_logs con su prefijo (como `audio_`, `z_`; aquí `rm_`, `ra_`,
  `rs_`), incluido lo que el equipo no sabe. Vale para F5-F7.

## Módulos

| Código | Examen | Libro | Box |
|---|---|---|---|
| `RS` | Rinoscopía anterior | H25 | Box Rinología |
| `RM` | Rinomanometría anterior | H26 | Box Rinología |
| `RA` | Rinometría acústica | H27 | Box Rinología |
| `OLF` | Olfatometría | H28 | Box Rinología |
| `PRICK` | Prick test | H29 | Box Rinología |
| `ESP` | Espirometría | H30 | Box Rinología |
| `PSG` | Polisomnografía y poligrafía | H31 | Laboratorio de sueño |
| `CPAP` | CPAP y avance mandibular | H32 | Laboratorio de sueño |

Datos del caso: `cases.data['NASAL']` es el paciente de RinoSim tal cual
(`lados.D/I` con narina, válvula, cornete, desviación, meato, pólipos,
congestión; `ciclo`; `perforacion`). Los demás bloques (`OLFATO`, `PRICK`,
`ESPIRO`, `SUENO`) se definen en su fase.

## Fases

**Para retomar (2026-10-29):** F0-F4 y F6 hechas; la rinomanometría (F2b),
la rinometría acústica (F2c) y la espirometría (F6) falta verlas en la app
real. Lo que sigue es **F5 (olfatometría y prick test)** o F7 (sueño). La
rinoscopía (F4) está en pausa por el aspecto.

- [x] **F0. Base.** Boxes y códigos en `Layout.php`, `GATED_MODULE_CODES`,
      iconos, `ModulePlaceholder` para cada código en `main.py`. Sin esto
      el botón del admin revienta con KeyError.
- [x] **F1. Modelo de RinoSim en Python** (`src/nasal/`): `modelo.py`,
      `rinomanometria.py`, `rinometria.py`, `azar.py` (mulberry32 + FNV-1a,
      idéntico al JS). Pruebas: las de RinoSim portadas
      (`tests/test_nasal_{modelo,rinomanometria,rinometria}.py`) y la
      equivalencia contra el JS (`tests/test_nasal_equivalencia.py`, máx.
      3e-12 relativo; regenerar con `node scripts/nasal/exportar_referencia.mjs
      tests/data/nasal_referencia.json`). Seis rarezas del JS anotadas en el
      encabezado de cada archivo, portadas tal cual.
- [x] **F2. Rinomanometría y rinometría acústica** como equipos
      (`nasal/equipos.py`, `nasal/graficos.py`, `nasal/sesion.py`): sello,
      medir FND/FNI, vasoconstrictor, errores de técnica "simulados" a mano,
      curva en cuatro cuadrantes, resistencia según la presión, tabla a
      75/150 Pa, Broms; calibrar, tres registros, MCA1 y MCA2, cambio con
      VC (la rinometría como equipo de verdad: F2c).
      Las dos ventanas comparten la nariz de la atención (el VC de una vale
      para la otra) y el ciclo nasal corre con el reloj. "Lo que el equipo no
      sabe" solo para docente/admin. La medición corre en `hilos.en_fondo`
      (una fosa de RM tarda ~0,7 s). Probado a 1366 y 1024 de ancho
      (`tests/test_nasal_equipos.py`). **Sin informe todavía:** sumar los
      tipos a `reports.tipo` es una migración (CHECK en la tabla); va en F3.
- [x] **F2b. Rinomanometría como se hace** (2026-10-29, a pedido de él;
      tests y capturas a 1366 y 1024, **sin ver en la app real**). Cómo
      queda hoy:
      - **Paciente** (`nasal/paciente_rm.py`): la cara de la rinoscopía con
        la máscara oronasal y el adaptador con su tubo. Clic en una narina
        pone o saca el adaptador (solo sin máscara). Los errores se ven sin
        carteles: boca abierta por la máscara, máscara chueca, oliva
        asomando; la máscara se empaña al espirar.
      - **En vivo** apenas hay adaptador o máscara: adaptador solo = presión
        sin flujo; máscara sola = flujo por las dos fosas (la otra narina
        abierta en la red, `AREA_NARINA_LIBRE`), sin presión. Indicaciones
        al paciente (tranquilo, cerrar la boca, parejo, fuerte) que tardan
        1-2 respiraciones.
      - **Grabar** descarta lo anterior, graba 10/15/20/30/60 s (zona
        sombreada, cuenta de segundos y ciclos) y promedia todos los ciclos
        completos (~3,2 s cada uno; con menos de 3 no guarda). Cancelar no
        guarda. Después sigue en vivo.
      - **Vasoconstrictor en el paciente** (fármaco, fosa, puff; sin máscara
        ni adaptador), efecto a los 15 min de reloj con cuenta regresiva y
        "saltar la espera" para el docente. Por fosa en la sesión
        (`sesion.vc_puesto`): vale también en la rinometría y la rinoscopía.
        Lo medido antes de tiempo se rotula "con VC" sin efecto.
      - **Temperatura y humedad de la sala** en la barra del equipo y en el
        PDF (no mueven el modelo). Fuera el encabezado con nombre y edad:
        queda una línea de mensajes.
      - **Modelo:** `mide_fosa` partido en `Red` + `ciclo` + `resumen` sin
        cambiar números (la equivalencia con el JS pasa); `Registro` genera
        ciclo a ciclo con la condición de ese momento y `mide_registro` lo
        rehace desde la receta del informe.
      - **Registro de acciones** (`sesion.registrar`): `rm_`, `ra_`, `rs_` a
        action_logs, como el audiómetro, con la verdad del modelo en el
        payload (el backend no la puede calcular). Rótulos en
        `Metrics::ACTION_LABELS`. Indicadores con esos datos: TODO 74, para
        más adelante.
      - Decisiones en `docs/decisiones.md`: § Rinomanometría: en vivo,
        grabación por tiempo y vasoconstrictor con espera; § Equipos
        nasales: cada acción y todas las variables a action_logs.
- [x] **F2c. Rinometría acústica como se hace** (2026-10-29, a pedido de
      él; tests, capturas a 1366 y arrastre con mouse simulado, **sin ver en
      la app real**). Es del equipo de LabSim: RinoSim no tiene toma en vivo
      ni cursores, y las figuras del libro siguen saliendo de `mide_fosa`.
      - **Iniciar/Detener por fosa.** Cada pulso cruza la pantalla de
        izquierda a derecha en 0,8 s; la variación entre pulsos es chica
        adelante y grande atrás (`rinometria.dispersion`, multiplicativa),
        el doble con fuga y el triple respirando (y lo de atrás salta).
      - **Tres curvas** sobre los últimos 8 pulsos: promedio y límites
        (± 2 DE del log del área) con la banda sombreada. **Baremos**
        verde/ámbar/rojo del semiancho de la banda en MCA1, MCA2 y 0-5 cm
        (verde ≤ 4 %, ámbar ≤ 8 %).
      - **Detener guarda el promedio** como registro; tres por fosa, con un
        cuarto quedan los tres últimos. Receta por pulso (semilla, número,
        estado, errores): `rehace_fosa` lo rehace igual al retomar.
      - **MCA1 y MCA2 con cursores** que se arrastran; el equipo lee el
        área donde quedan (no busca el valle). Aparecen al azar; el combo
        "Cursores MCA1 y MCA2 en" elige la curva. El valle automático y la
        verdad, para el docente.
      - **Parámetros** (`rinometria.PARAMETROS`): D1, MCA1, D2, MCA2, V1,
        V0-2, V0-5, V2-5, V0-7, CV de MCA1/MCA2, criterio 0,03 y la nariz
        entera (D + I). Sin MCA3 ni áreas a distancias fijas: si él los
        echa de menos.
      - Acciones: `ra_iniciar`, `ra_registro` (con baremos y valle),
        `ra_marcar`, `ra_detener`, `ra_cancelar`.
      - Decisiones en `docs/decisiones.md`: § Rinometría acústica: en vivo,
        Iniciar y Detener; § MCA1 y MCA2 con cursores, y todos los
        parámetros.
- [x] **F3. Caso nasal e informe** (hecho 2026-10-29, sin ver en navegador):
      - Ficha **Nariz** en `case_create.php`, solo para el admin
        (`CaseReview::TABS['nariz']`: `solo_admin`, no revisable, no
        renumera las 11). Cuadros de RinoSim con 8 variantes precalculadas
        (`scripts/nasal/cuadros_backend.py` → `resources/nasal/cuadros.json`;
        las variantes que se salían de los rangos de la tabla se recortan
        al rango, solo en el editor). `CaseForm::parseNasal` valida.
        El hidden `nasal_json` viaja para todos: un docente que edita un
        caso con nariz no la borra. `case_import.php` no lo trae.
      - Informes `RINOMANOMETRIA` y `RINOMETRIA`: CHECK de `reports.tipo`
        (schema + migración, centinela `'RINOMETRIA'`; probada con el sqlite
        de Python porque aquí no hay pdo_sqlite), endpoint, rótulos, PDF con
        gráficos + tabla + avisos. En la app, pestaña Informe, autosave y
        retomar: se guarda CÓMO se tomó cada medición y se recalcula igual.
      - **Al desplegar:** la primera subida de informe (de cualquiera)
        reconstruye la tabla `reports`; mejor correr antes "Aplicar schema"
        en `admin/database.php` con respaldo y sin clases.
- [x] **F3b. Pacientes de los caps. 35 y 36** con su bloque `NASAL`, en
      producción desde el 2026-10-29: fichas 151-156 (Carlos, Mónica, Rocío,
      Sofía, Álvaro, Marcos), carpeta "Libro · nariz (demo)", fuera de la
      práctica libre. La nariz es el cuadro y la semilla de RinoSim de sus
      figuras (`scripts/nasal/sql_pacientes.py`). El minuto del ciclo de
      cada atención es otro que el de la figura: los números pueden no ser
      los del libro hasta poner vasoconstrictor.
- [x] **F4. Rinoscopía** (hecho 2026-10-29, sin ver en la app real).
      Fotos libres no alcanzan: la rinoscopía de H25 se mira recta, a 30° y
      a 60°, y ninguna foto trae esas miradas del mismo paciente (lo libre
      es casi todo endoscopía; ver `libro-orl/trabajo/investigacion/imagenes_nasales.md`).
      Decidido con él: **la fosa se arma en 3D desde la misma nariz del caso**
      y se dibuja trazando rayos con numpy (`nasal/rinoscopia.py`, sin
      módulos de Qt nuevos). Tabique (desviación, espolón, concavidad del
      otro lado, perforación), cornetes (el inferior con su hueso y su
      mucosa: el vasoconstrictor de la RM lo achica aquí también), pólipos
      en el meato medio, color de la mucosa y secreción (`NASAL.rinoscopia`,
      editable en la ficha Nariz). El visor (`nasal/RinoscopiaWindow.py`):
      fosa + cabeza (recta, 30°, 60°, o de a 10°), imágenes en segundo
      plano y guardadas en el equipo. Informe por fosa (tabique, cornetes,
      meato medio, mucosa, secreción, perforación, observaciones) +
      conclusión, tipo `RINOSCOPIA` con PDF; anota solo qué fosa miró
      primero y en qué posiciones. "Lo que hay" para el docente.
      Después (mismo día, a pedido de él): la cara de frente
      (`resources/rinoscopia`, cuadros de labyrinthus3d de 0° a 60°), ▲/▼
      "Reclinar" mantenidas, el espéculo es el mouse sobre la narina y el
      interior se abre al costado. **En pausa: "está feísimo, déjalo por
      ahora"** (2026-10-29). Pendiente cuando se retome: el aspecto general
      (la bata celeste, el interior), textura de mucosa de fotos reales con
      licencia (hoy ruido procedural), bordes dentados al agrandar, y el
      interior que cambia cada 10° aunque la cabeza vaya de a 2°.
- [ ] **F5. Olfatometría y prick test.**
- [x] **F6. Espirometría** (2026-10-29, a pedido de él; tests y capturas
      a 1366, **sin ver en la app real ni la tarjeta en el navegador**).
      Decisiones en `docs/decisiones.md` (§ Espirometría: en vivo,
      conducida por el alumno; § Los tipos de informe de nariz y sueño;
      § Espirometría en el caso).
      - **Modelo** (`nasal/espirometria.py`): el de H30 calibrado para que una
        maniobra bien hecha mida la FVC, el FEV1 y el PEF del caso; GLI-2012
        (`resources/nasal/gli2012.json`, el del libro); análisis del equipo
        solo con la señal; tabla de aceptabilidad de H30, grados A-F,
        respuesta sobre el teórico; jeringa de 3 L.
      - **Equipo** (`nasal/EspirometriaWindow.py`): pinza y boquilla en la
        cara del paciente, talla y peso, verificar y calibrar, cero de flujo,
        Iniciar y cinco indicaciones (teclas 1-5), curvas en vivo, tabla de
        maniobras con "Lo que viste", broncodilatador con espera, informe
        en el formato SER 2024 con los indicadores de OVAS (FIF50,
        FEF50/FIF50, FEV1/PEF). Errores simulados: tos, inicio lento, no
        inspira al máximo, cierre de glotis, fuga, boquilla tapada, cero
        corrido, descalibrado. Acciones `esp_`.
      - **Backend**: tipo `ESPIROMETRIA` (y de una vez `OLFATOMETRIA`,
        `PRICK`, `POLISOMNOGRAFIA`, `CPAP`: una sola reconstrucción de
        `reports`, centinela `'CPAP'`), PDF con curvas, datos del examen y
        tabla; tarjeta Pulmón en la ficha Nariz (`public/js/case/pulmon.js`,
        `CaseForm::parseEspiro`).
      - **Pacientes del cap. 37**: fichas 157 (asma) y 158 (estenosis
        traqueal), `scripts/nasal/sql_pacientes.py` con su bloque `ESPIRO`
        (los números de los informes del libro). SQL listo, sin cargar en
        producción.
      - De paso: los equipos nasales no tenían `submit_report` y cada cierre
        de atención los contaba como informe no subido.
- [ ] **F7. Sueño:** poligrafía/PSG (registro, puntuación de eventos, IAH)
      y titulación de CPAP; casos del cap. 38.

## Fuera, por ahora

- Soltarlo a los alumnos (Courses::MODULES, práctica libre, manual).
- Errores conocidos del modelo de RinoSim (anotados en
  `libro-orl/ESTADO.md`, "Errores del simulador detectados"): se portan tal
  cual y se arreglan en los dos lados a la vez.
