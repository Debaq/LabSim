# Catálogo de cuadros — referencia y lo que falta

Los 49 cuadros que esta lista tenía pendientes ya están en
`CaseProfile::SCENARIOS` (2026-09-10): el catálogo pasó de 21 a 70. Lo que
queda acá es la **referencia de cómo se escribe una ficha** y la lista corta
de cuadros que el motor todavía no puede armar.

Lo clínico lo decide el docente al armar el caso: estas claves dicen qué
mide ese oído, no qué hay que enseñar.

## Cómo leer cada ficha

Los ejes que el catálogo tiene, y nada más:

| Clave | Qué fija |
|---|---|
| `categoria` | grupo del selector: `normal`, `conductiva`, `sensorial`, `neural`, `sensorioneural`, `mixta` |
| `sn_shape` / `sn_scale` | forma de la vía ósea por frecuencia (dB relativos) y rango de escala |
| `gap_shape` / `gap_scale` | forma del gap aéreo-óseo; `[]` = sin componente de transmisión |
| `gap_max_db` | techo del gap por frecuencia; tope absoluto `GAP_MAX_DB = 60` |
| `max_db` | techo del promedio BIAP (500/1k/2k/4k) |
| `grados` | grados de `GRADES` que el cuadro puede dar sin dejar de ser ese cuadro |
| `cce_pct` | proporción coclear del daño: manda las OEA (100 = coclear puro, 0 = retro puro) |
| `retro` | preset de `CaseBuilder::ABR_NEURAL_PRESETS`, o `null` |
| `z` / `etf` | timpanograma (`A As Ad C Cs B`) y función tubaria (`Normal`, `Disfunción tubaria`, `Permeable`, `No permeable`) |
| `vemp` | `type` (`normal utricular sacular neural`) + `umbral` por subtipo, o `umbral_gap` |
| `tinnitus` | `prob`, `ruido` (`Silbido Zumbido Siseo Pitido Campanilleo`), `frecuencia`, `permanente`, y `pulsatil` opcional |
| `conciencia` | rango del rasgo del paciente en la entrevista |
| `lateralidad` | sugerencia para el otro oído (`unilateral` / `bilateral`) |

Se derivan solos y **no se declaran**: reflejos acústicos (los apaga el
timpanograma de la sonda o un gap ≥ 10 dB), OEA (de `cce_pct` + gap), umbral
ABR por estímulo, reclutamiento, deterioro tonal (`carhart`, `stat`,
`rosemberg`), logoaudiometría, acumetría, SDT/SRT.

`tests/test_case_profile.php` es el contrato: cada grado declarado tiene que
ser alcanzable con la forma del cuadro (`techoBiap`), el gap tiene que caber
en su techo, y el perfil tiene que clasificar el cuadro como lo que dice
ser. Agregar una ficha sin tocar el test falla ahí antes que en el aula.

## Los que todavía no se pueden escribir

Cada uno está bloqueado por algo del motor, no por falta de datos. El
detalle de qué habría que cambiar está en `TODO.md`, sección "Catálogo de
cuadros: lo que el motor todavía no puede armar".

| Cuadro | Qué falta |
|---|---|
| **Dehiscencia del canal semicircular superior** | reflejo presente CON gap + ósea supranormal (negativa) |
| **Acueducto vestibular dilatado** | lo mismo: es la tercera ventana del otro lado |
| **Pendred / Mondini** | ídem, más el eje de progresión en escalones |
| **Tuba abierta (patulous)** | fluctuación respiratoria del timpanograma; sin eso no se distingue de un oído normal |
| **Ménière fluctuante, hidrops, autoinmune, CMV, NIHL en dos momentos** | eje temporal: hoy el caso es una foto (los cuadros existen, la evolución no) |
| **Procesamiento auditivo central** | no hay módulo donde vivan las pruebas dicóticas |
| **Simulación / no orgánico** | no hay eje de inconsistencia (SRT vs PTA, Stenger) |
| **Hiperacusia / misofonía** | el LDL es un campo del formulario, no un eje del perfil |
