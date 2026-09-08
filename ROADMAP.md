# Perfil auditivo unificado

Rama: `feat/perfil-auditivo-unificado`.

## El problema

`cases.data` es hoy una bolsa plana de exámenes independientes: `Aerea`,
`Osea`, `Z_OD`, `Reflex`, `ETF`, `ABR{type,umbral}`, `EOAS{type,umbral,desv}`,
`VEMP`. Cada módulo trae su propio selector de patología
(`normal`/`coclear`/`transmission`/`neural`) y su propio `umbral` escalar. Son
tres verdades separadas para un mismo oído.

Consecuencias concretas:

1. **El ABR no se puede caracterizar por frecuencia.** `abrBuild()` guarda un
   solo `umbral` por oído y `ABR_generator.py:1752` lo lee tal cual. El estímulo
   (`STIM_MAP`: click, Ls-chirp, CE-chirp, burst 500/1k/2k/4k) cambia latencias y
   amplitudes vía `get_baseline_values()`, pero **no cambia el umbral**. Una
   hipoacusia descendente responde igual a burst de 500 Hz que a burst de 4 kHz:
   el ejercicio de frecuencia específica no tiene nada que descubrir.
2. **Se pueden escribir pacientes imposibles.** Gap de 40 dB con reflejos
   presentes. Timpanograma B con OEA normales. ABR normal con audiograma
   profundo. `normalCoherenceError()` (`CaseBuilder.php:515`) solo revisa que un
   módulo marcado "Normal" no traiga umbral alto, y lo hace **dentro** de cada
   módulo, nunca entre módulos.
3. **Dos randomizadores independientes.** El "Autocompletar ABR"
   (`case_create.php:1871`) y el "Autocompletar EOA" (`EOAS_AUTOFILL_GRADES`)
   sortean por separado y ya pueden contradecirse entre sí.

## La idea

No juntar los tabs en una pantalla gigante. **El audiograma ya es el perfil**:
`Aerea` y `Osea` dicen cuánta pérdida hay y cuánta es conductiva, por
frecuencia. Lo único que el audiograma NO puede decir es **dónde está la lesión
dentro del componente sensorioneural** (cóclea vs retrococlear) y **con qué
patrón electrofisiológico**.

Eso es todo lo que agrega el perfil:

```php
'Perfil' => [
    'version' => 1,
    'OD' => [
        'cce_pct' => 0..100,  // del componente SN, cuánto es coclear (CCE)
        'retro'   => [ ...ABR_NEURAL_DEFAULTS ],  // el patrón retrococlear
    ],
    'OI' => [ ... ],
    // Qué proyecciones están en automático. Ausente/false = el docente
    // maneja ese campo a mano (comportamiento de todos los casos viejos).
    'auto' => ['abr' => false, 'eoas' => false, 'reflex' => false, 'recruit' => false],
]
```

Deliberadamente **no** se duplican `perdida[hz]` ni `gap[hz]` dentro del perfil:
serían una segunda fuente de verdad frente a `Aerea`/`Osea` y se
desincronizarían el primer día. Se derivan.

Por oído y por frecuencia `f`:

| Magnitud | Fórmula |
|---|---|
| `air[f]` | `Aerea[f]` |
| `bone[f]` | `Osea[f]` |
| `gap[f]` | `max(0, air[f] - bone[f])` |
| `sn[f]` | `bone[f]` (pérdida sensorioneural) |
| `cce[f]` | `sn[f] * cce_pct/100` (componente coclear: mata la OEA) |
| `retro_sn[f]` | `sn[f] * (1 - cce_pct/100)` (componente neural: OEA intacta) |

## Proyecciones

Cada examen es una vista del perfil. `auto` ON = derivado, campos read-only en
el formulario. `auto` OFF = el docente escribe a mano, como hoy.

### 1. Umbral ABR por estímulo (dB nHL)

```
umbral_nHL(stim) = Σ_f  w[stim][f] · nivel[f]  +  corr_nHL[stim]
```

`nivel[f]` = `air[f]` en vía aérea, `bone[f]` en vía ósea (con lo cual el gap
conductivo del ABR sale del audiograma solo, sin campo nuevo).

Pesos `w` (suman 1):

| Estímulo | 500 | 1000 | 2000 | 3000 | 4000 |
|---|---|---|---|---|---|
| `tone_burst_500Hz` | 1.00 | — | — | — | — |
| `tone_burst_1000Hz` | — | 1.00 | — | — | — |
| `tone_burst_2000Hz` | — | — | 1.00 | — | — |
| `tone_burst_4000Hz` | — | — | — | — | 1.00 |
| `click` | — | — | 0.35 | 0.30 | 0.35 |
| `ce_chirp` / `ls_chirp` | 0.15 | 0.20 | 0.25 | — | 0.40 |

Corrección conductual (dB HL) → electrofisiológico (dB nHL), `corr_nHL`:
burst 500 `+20`, burst 1k `+15`, burst 2k `+10`, burst 4k `+5`, click `+10`,
chirp `+5` (sincroniza mejor toda la partición coclear y baja algo el umbral).
Son los factores de corrección de la práctica clínica, usados al revés: en el
box se **restan** del nHL medido para estimar el audiograma; acá se **suman**,
porque el caso se define en dB HL y hay que producir lo que el equipo muestra.
Que un oído de 0 dB HL dé 20 dB nHL en burst de 500 no es un error, es el
hallazgo.

Esto es contenido pedagógico, no plomería: el alumno tiene que convertir nHL a
eHL para estimar el audiograma.

### 2. Tipo de patología ABR/EOA (`type`)

Derivado, por oído, con el **máximo** en 500-4000 (no el promedio: una
descendente con 500 y 1000 conservados promedia dentro de lo normal y se
clasificaba como oído sano, que es justo el caso que motivó todo esto):

- `gap_max >= 15` → `transmission`
- si no y `sn_max <= 25` y sin retro cargado → `normal`
- si no y `cce_pct >= 60` → `coclear`
- si no → `neural`

### 3. Desviaciones OEA por frecuencia (dB)

Misma ley que `oae_attenuation_db()` en `src/oae/generators/base.py`, pero
alimentada por la descomposición del perfil en vez de por un `type` + `umbral`
escalar:

```
desv[f] = min(45, max(0, cce[f] - 15) * 1.2  +  max(0, gap[f] - 8) * 2.0)
```

`retro_sn[f]` **no** entra: la cóclea está viva. Con eso la neuropatía
(`cce_pct` bajo + `retro` cargado) sale sola — OEA presentes, ABR desarmado —
sin cargarla a mano en dos tabs y rezar que no se contradigan.

### 4. Reflejos acústicos (`Reflex.ipsi` / `Reflex.contra`, dB HL)

- Gap en el oído **sonda** ≥ 10 dB → ausente (`130`).
- Gap en el oído **estimulado** → suma al umbral del reflejo dB a dB.
- Pérdida SN: umbral del reflejo sube `0.5 dB/dB` sobre 50 dB HL de `sn[f]`.
- Reclutamiento (`cce_pct` alto): el umbral del reflejo **no** sube en
  proporción a la pérdida — el SL del reflejo se achica, que es el hallazgo.
- `retro_sn` alto → reflejos elevados o ausentes + decay.

### 5. Reclutamiento (`recruit`, `SISI`, `Fowler.patterns`)

Derivados de `cce_pct` en las frecuencias que califican
(`fowlerQualifyingFreqs()` ya existe):
`cce_pct >= 80` → `complete`, SISI 80-100%, `recruit` true;
`50-79` → `partial`, SISI 40-60%; `< 50` → `none`, SISI 0-20%.

### 6. Logoaudiometría (`UMD`)

Máxima discriminación y a qué nivel se alcanza. El porcentaje cae despacio
en una coclear (`0.8 dB/dB` sobre 20 dB) y se desploma en una retrococlear
(`1.8 dB/dB` sobre 10 dB, más 20 puntos fijos si hay patrón retro cargado):
esa diferencia **es** la disociación audio-verbal, el signo retrococlear más
clásico que hay, y sin esto el caso no la podía mostrar.

El porcentaje pesa 2-4 kHz (`SPEECH_WEIGHTS`), no el promedio de Fletcher:
las consonantes viven ahí, y con Fletcher a secas una descendente daba 100%
de discriminación. El nivel del máximo sí usa Fletcher + 35 dB. El gap no
baja el porcentaje — una conductiva no distorsiona — solo corre la curva.

El rollover ya venía del flag `recruit`, que deriva la sección 5
(`logoaudiometry.py:89`): media mecánica ya respondía al perfil y la otra
media no.

### 7. LDL / campo dinámico

`LDL_NORMAL_DB = 100`, y **no sube con la pérdida coclear**: el umbral sube,
el disconfort no, y el campo dinámico se cierra solo. El reclutamiento no
hay que dibujarlo, cae de la física. En una retrococlear el LDL sí acompaña
al umbral (campo dinámico conservado, `LDL_FULL_RANGE_DB = 95`), y el gap
corre todo hacia arriba porque el oído medio atenúa también lo fuerte.

### 8. Morfología de la curva del reflejo

Solo se deriva el patrón **OFF** (el reflejo que no se sostiene: decay,
signo retrococlear del mismo eje que el deterioro tonal). `invertido` y
`on-off` quedan siempre al docente: el primero es un artefacto de registro
y el segundo un hallazgo puntual, ninguno se deduce del sitio de la lesión.

### 9. Ya derivados hoy (precedente del patrón)

`Rinne`/`Weber` (`rinneAuto`/`weberAuto` + checkbox `acumetria_auto`),
`SDT`/`SRT` (Fletcher + `sdt_auto`/`srt_auto`). El mecanismo de
"auto con override manual" **ya existe en este formulario**; el trabajo es
generalizarlo, no inventarlo.

## Lo que NO se deriva, y por qué

- **Timpanograma y ETF.** Qué curva sale depende de la patología concreta
  (B ocupación, As rígido, Ad hipercompliante, C retracción) y es una
  decisión clínica, no una cuenta. Se avisa si contradice al gap: curva A
  con gap ≥ 20 dB, o curva B con gap < 10 dB.
- **VEMP.** El perfil no tiene eje vestibular. Un schwannoma deja el ABR
  desarmado y el VEMP normal si nadie lo toca. Agregar ese eje es otro
  refactor.
- **Parámetros de onda del ABR** (latencias y amplitudes onda por onda,
  FSP) y **ruido/sello de la OEA**: los sortean los "Autocompletar", que
  por eso siguen existiendo.

## Completitud: lo que no se calcula, se exige

`CaseCompleteness::pending()` es el criterio único de "caso listo". Revisa
solo lo que el perfil **no puede** calcular y quedó en su default:

- Timpanograma en A con gap ≥ 20 dB, o curva B/C/Cs con la ETF en "Normal".
- ABR con patología distinta de normal y las seis desviaciones de onda en 0
  (nunca se corrió el autocompletar): la curva sale con la morfología de un
  oído sano.
- VEMP normal sin tocar en un caso con patrón retrococlear cargado.

No revisa lo que puede estar vacío con razón: anamnesis, texto de
otoscopia, comportamiento del paciente.

Se aplica en tres lugares:

1. **El editor no guarda** con esto pendiente (distinto de los avisos de
   incoherencia, que sí se guardan tildando una casilla: aquellos pueden
   SER el ejercicio, esto es un dato que falta).
2. **La agenda no cita** un caso incompleto, y ofrece el link para
   completarlo.
3. **`patients.php` lo marca** como "incompleto", con el detalle en el
   tooltip. Buscar "incompleto" junta todos los que hay que arreglar.

Además el editor avisa antes de salir con cambios sin guardar
(`beforeunload` + confirmación propia en "Cancelar").

**Ojo con los casos que ya existen**: cualquiera con audiograma conductivo y
timpanograma A, o con patología de ABR sin desviaciones cargadas, pasa a ser
incitable hasta que se complete. No hay forma de medir cuántos son sin la
base de producción. Por eso el marcador de `patients.php` va primero: se ve
la lista antes de que el portón moleste.

## Lo que tiene que seguir pudiendo romperse

No todo se proyecta, y forzar coherencia mataría la mitad de los ejercicios:

- **No orgánica / Stenger**: el audiograma miente a propósito.
- **Falsa onda V**: artefacto que el docente arma a mano.
- **ANSD**: sale del modelo (`cce_pct` bajo), pero sus parámetros finos no.
- Cualquier caso donde el docente quiera una incoherencia como ejercicio.

Por eso el perfil **avisa, no bloquea**, y `auto` es por módulo. Si el modelo
pasa a ser obligatorio, el refactor fracasó.

## Compatibilidad

`buildCaseData()` sigue emitiendo **exactamente las mismas claves**
(`Aerea`, `Z_OD`, `Reflex`, `ABR`, `EOAS`, …). Cambia solo de dónde salen los
números. El cliente de escritorio (Audiometer.py, Z.py, ABR, OAE) no se entera,
salvo en la fase 2 (umbral ABR por estímulo), que llega como clave **nueva** con
fallback al escalar de siempre.

Casos ya guardados: sin `Perfil`, se infiere `cce_pct` del `type` que ya tienen
(`coclear`/`transmission` → 100, `neural` → 0, `normal` → 100) y **todos los
`auto` arrancan apagados**. Un caso viejo abierto y guardado de nuevo tiene que
producir el mismo JSON que antes. Es el criterio de no-regresión de la fase 1.

## Fases

Las seis están hechas en `feat/perfil-auditivo-unificado`. Nada se probó todavía
en el formulario real corriendo contra la base: los tests cubren las
derivaciones y el cliente, no la página.

| # | Qué | Toca | Estado |
|---|---|---|---|
| 0 | `CaseProfile.php`: derivaciones puras + runner de tests PHP | `src/CaseProfile.php`, `tests/` | ✅ |
| 1 | `Perfil` persistido en `cases.data`, inferido de casos viejos, releído al editar | `CaseBuilder.php`, `case_create.php` | ✅ |
| 2 | **Umbral ABR por estímulo** (el pedido original) | `CaseProfile.php`, `ABR_generator.py`, `case_create.php` | ✅ |
| 3 | Tab "Perfil auditivo": `cce_pct` + `retro` (se mudan del tab ABR) + checkboxes `auto` | `case_create.php` | ✅ |
| 4 | Proyecciones restantes: OEA, reflejos, reclutamiento, deterioro tonal | `CaseProfile.php`, `case_create.php` | ✅ |
| 5 | Avisos de desvío del perfil (no errores duros), con confirmación explícita | `CaseProfile.php`, `case_create.php` | ✅ |
| 6 | Sorteo de cuadro clínico completo desde el perfil | `CaseProfile.php`, `case_create.php` | ✅ |

Las fases 0-2 resuelven el problema que originó todo esto y no tocan ningún
caso guardado. De la 3 en adelante cambia el formulario.

**Corrección sobre el plan original de la fase 6:** los dos "Autocompletar"
NO se retiran. El perfil subsume la parte donde se contradecían — umbral y
patología — pero cada uno sigue sorteando cosas que el perfil no describe y
que el generador necesita: latencias y amplitudes onda por onda y FSP en el
ABR, ruido del paciente y sello de sonda en la OEA. Sacarlos hubiera borrado
ese detalle. Lo que se agrega es el sorteo de **cuadro clínico** en la
pestaña Perfil, que escribe audiograma + sitio de lesión + patrón retro de
una vez y enciende las derivaciones.

## Riesgos

- `case_create.php` son 4119 líneas y `CaseBuilder.php` 1195. La fase 3 es la
  cara: mueve campos entre tabs.
- No hay infraestructura de tests PHP en el repo. La fase 0 la agrega (runner
  plano, sin composer ni PHPUnit: el backend no tiene dependencias hoy y no vale
  la pena agregarlas por esto).
- Los tests Python necesitan el venv con `--system-site-packages` (el Python del
  sistema no trae scipy/pyqtgraph).
