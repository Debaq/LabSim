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
      75/150 Pa, Broms; calibrar, tres registros, MCA1 y MCA2, cambio con VC.
      Las dos ventanas comparten la nariz de la atención (el VC de una vale
      para la otra) y el ciclo nasal corre con el reloj. "Lo que el equipo no
      sabe" solo para docente/admin. La medición corre en `hilos.en_fondo`
      (una fosa de RM tarda ~0,7 s). Probado a 1366 y 1024 de ancho
      (`tests/test_nasal_equipos.py`). **Sin informe todavía:** sumar los
      tipos a `reports.tipo` es una migración (CHECK en la tabla); va en F3.
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
- [ ] **F6. Espirometría** (maniobra, aceptabilidad y repetibilidad, prueba
      broncodilatadora, LIN y z-score); caso del cap. 37.
- [ ] **F7. Sueño:** poligrafía/PSG (registro, puntuación de eventos, IAH)
      y titulación de CPAP; casos del cap. 38.

## Fuera, por ahora

- Soltarlo a los alumnos (Courses::MODULES, práctica libre, manual).
- Errores conocidos del modelo de RinoSim (anotados en
  `libro-orl/ESTADO.md`, "Errores del simulador detectados"): se portan tal
  cual y se arreglan en los dos lados a la vez.
