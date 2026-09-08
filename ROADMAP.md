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
burst 500 `+15`, burst 1k `+10`, burst 2k `+5`, burst 4k `+5`, click `0`,
chirp `-5` (el chirp sincroniza mejor y baja algo el umbral).

Esto es contenido pedagógico, no plomería: el alumno tiene que convertir nHL a
eHL para estimar el audiograma.

### 2. Tipo de patología ABR/EOA (`type`)

Derivado, por oído, con el promedio 500-4000:

- `gap_medio >= 15` → `transmission`
- si no y `sn_medio <= 25` y sin retro cargado → `normal`
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

### 6. Ya derivados hoy (precedente del patrón)

`Rinne`/`Weber` (`rinneAuto`/`weberAuto` + checkbox `acumetria_auto`),
`SDT`/`SRT` (Fletcher + `sdt_auto`/`srt_auto`). El mecanismo de
"auto con override manual" **ya existe en este formulario**; el trabajo es
generalizarlo, no inventarlo.

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

| # | Qué | Toca | Estado |
|---|---|---|---|
| 0 | `CaseProfile.php`: derivaciones puras + runner de tests PHP | `src/CaseProfile.php`, `tests/` | ☐ |
| 1 | `Perfil` persistido en `cases.data`, inferido de casos viejos, releído al editar | `CaseBuilder.php`, `case_create.php` | ☐ |
| 2 | **Umbral ABR por estímulo** (el pedido original) | `CaseProfile.php`, `ABR_generator.py`, `AbrMainWindow.py` | ☐ |
| 3 | Tab "Perfil auditivo": `cce_pct` + `retro` (se mudan del tab ABR) + checkboxes `auto` | `case_create.php` | ☐ |
| 4 | Proyecciones restantes: OEA, reflejos, reclutamiento, Carhart | `CaseProfile.php`, `case_create.php` | ☐ |
| 5 | `normalCoherenceError` → avisos de desvío del perfil, no errores duros | `CaseBuilder.php`, `case_create.php` | ☐ |
| 6 | Un solo randomizador de perfil; se retiran los dos autocompletar | `case_create.php`, `CaseBuilder.php` | ☐ |

Las fases 0-2 resuelven el problema que originó todo esto y no tocan ningún
caso guardado. De la 3 en adelante cambia el formulario.

## Riesgos

- `case_create.php` son 4119 líneas y `CaseBuilder.php` 1195. La fase 3 es la
  cara: mueve campos entre tabs.
- No hay infraestructura de tests PHP en el repo. La fase 0 la agrega (runner
  plano, sin composer ni PHPUnit: el backend no tiene dependencias hoy y no vale
  la pena agregarlas por esto).
- Los tests Python necesitan el venv con `--system-site-packages` (el Python del
  sistema no trae scipy/pyqtgraph).
