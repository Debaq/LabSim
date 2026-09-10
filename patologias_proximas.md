# Patologías próximas — backlog del catálogo de cuadros

Lista de trabajo para `CaseProfile::SCENARIOS` (el catálogo que consume el
generador de `case_create`). **No es material docente**: cada ficha dice qué
mide ese oído y con qué claves del catálogo se escribe, o por qué todavía no se
puede escribir. Lo clínico lo decide el docente al armar el caso.

## Cómo leer cada ficha

Los ejes que el catálogo tiene hoy, y nada más:

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
| `tinnitus` | `prob`, `ruido` (`Silbido Zumbido Siseo Pitido Campanilleo`), `frecuencia`, `permanente` |
| `conciencia` | rango del rasgo del paciente en la entrevista |
| `lateralidad` | sugerencia para el otro oído (`unilateral` / `bilateral`) |

Se derivan solos y **no se declaran**: reflejos acústicos (los apaga el
timpanograma de la sonda o un gap ≥ 10 dB), OEA (de `cce_pct` + gap), umbral ABR
por estímulo, reclutamiento, deterioro tonal (`carhart`, `stat`, `rosemberg`),
logoaudiometría, acumetría, SDT/SRT.

Presets ABR disponibles para `retro`: `schwannoma`, `nf2`, `angulo`,
`microvascular`, `ansd`, `esclerosis_multiple`, `infarto_pontino`,
`glioma_tronco`, `chiari_hic`, `kernicterus`, `leucodistrofia`,
`hereditaria_central`, `siderosis`, `toxico_metabolico`, `hipotermia_farmacos`,
`tec_tronco`, `bloqueo_proximal`, `prematuro`.

## Ya en el catálogo (21 cuadros, no duplicar)

`normal` · `otitis_media` · `otoesclerosis` · `disyuncion_cadena` ·
`fractura_cadena` · `fractura_longitudinal` · `perforacion` ·
`disfuncion_tubaria` · `tapon_cerumen` · `presbiacusia` · `muesca_4k` ·
`coclear_plana` · `meniere` · `subita` · `fractura_transversal` · `ototoxica` ·
`schwannoma` · `neuropatia` · `sensorioneural` · `mixta_otitis_cronica` ·
`mixta_otoesclerosis`

---

# 1. Conductivas (oído externo y medio)

Todas con `cce_pct [100, 100]`, `retro null`, `vemp ['type' => 'normal',
'umbral_gap' => true]`. Lo que las separa: forma del gap, `z` y `gap_max_db`.

| Cuadro | Patrón | Claves | Falta |
|---|---|---|---|
| **Cuerpo extraño en CAE** | Gap plano 20-35 dB si ocluye; curva A (el oído medio está sano) o no registrable por el objeto | `gap_shape` plano ~28, `gap_max_db 35`, `z ['A']`, `grados ['leve']`, `max_db 35`, unilateral, `conciencia` alta (brusco) | nada |
| **Otitis externa difusa** | Gap 15-30 dB por edema del CAE, dolor al tracción; oído medio normal | igual al anterior con `gap_max_db 30`, `z ['A']`, `etf 'Normal'` | el dolor/la otoscopia no salen del cuadro |
| **Estenosis / atresia congénita de CAE** | Gap grande y **plano** 45-60 dB desde el nacimiento, sin Carhart, timpanograma no registrable | `gap_shape` plano 50-55, `gap_max_db 60`, `grados ['leve','moderada']`, `max_db 60`, unilateral, `conciencia` baja (nació así) | no hay valor "no registrable" en `z`; hoy hay que poner `B` y mentir un poco |
| **Timpanoesclerosis / miringoesclerosis** | Rigidez: gap chico-medio 15-30 dB, peor en agudos que la efusión, curva **As** | `gap_shape` ~20 algo creciente en agudos, `gap_max_db 30`, `z ['As']`, `grados ['leve']` | nada |
| **Otitis media aguda** | Gap 25-40 dB en graves, curva B, cuadro de horas-días (lo separa de `otitis_media` la historia, no la curva) | clon de `otitis_media` con `gap_max_db 45`, `conciencia [90,100]`, `tinnitus prob` baja | la otoscopia (tímpano abombado) no está ligada al cuadro |
| **Colesteatoma** | Gap 30-50 dB, B, erosión progresiva de cadena; puede llevarse la ósea (→ mixta) | conductiva: `gap_max_db 55`, `grados ['leve','moderada']`; la versión con daño coclear ya es `mixta_otitis_cronica` | otoscopia ligada al cuadro |
| **Fijación congénita del estribo / malformación de cadena** | Gap plano 40-50 dB de toda la vida, **sin muesca de Carhart**, curva A o As | `gap_shape` plano ~45, `gap_max_db 50`, `z ['A','As']`, `grados ['leve','moderada']`, `max_db 50`, `conciencia` baja | nada |
| **Barotrauma de oído medio** | Gap 20-40 dB en graves, curva C/Cs o B si hay hemotímpano, brusco y reversible | `gap_shape` grave-dominante ~35, `gap_max_db 45`, `z ['C','B']`, `etf 'Disfunción tubaria'`, `conciencia [90,100]` | nada |
| **Tuba abierta (patulous)** | Autofonía, gap mínimo o nulo, timpanograma con **fluctuación respiratoria** | `etf 'Permeable'`, `gap_shape` ~10, `grados ['leve']` | el motor no modela la fluctuación del timpanograma con la respiración: sin eso el cuadro no se distingue de un oído normal |
| **Glomus timpánico (paraganglioma)** | Gap 20-40 dB + **tinnitus pulsátil** sincrónico con el pulso, masa retrotimpánica | `gap_shape` ~30, `z ['B','As']`, `tinnitus` | `TINNITUS_RUIDO_OPTIONS` no tiene "pulsátil", que es el hallazgo; agregarlo es 1 línea en `CaseBuilder` |

## Dehiscencia del canal semicircular superior (tercera ventana)

**El cuadro que el motor todavía no puede armar, y vale la pena que pueda.**

Patrón: gap aéreo-óseo en graves (la ósea se vuelve **supranormal**, umbrales de
-5/-10 dB) con **reflejos acústicos presentes**, timpanograma A, y VEMP de
umbral **bajo** con amplitudes altas. Más Tullio y fenómeno de Hennebert.

Lo que choca con el motor hoy:

1. `reflexThreshold()` apaga el reflejo con cualquier gap ≥ `REFLEX_PROBE_GAP_DB`
   (10 dB). Acá el reflejo **tiene que estar presente con gap**: es justo lo que
   separa la tercera ventana de una otoesclerosis. Hace falta una excepción
   declarada por el cuadro (algo como `gap_con_reflejo => true`), no un ajuste
   del umbral global.
2. La ósea supranormal necesita `sn_shape` negativo en graves; el generador
   recorta a 0 (`aCinco()` hace `Math.max(0, …)`).
3. El VEMP con umbral bajo sí se puede: `'umbral' => ['CVEMP' => [50, 60], …]`,
   pero el cuadro además es conductivo y ahí el catálogo fuerza `umbral_gap`.
   Las dos formas son excluyentes por test, así que hay que decidir cuál gana.

Mismo problema, misma solución: **acueducto vestibular dilatado** (tercera
ventana del lado opuesto, con hipoacusia mixta progresiva en niños — suele ir con
Mondini/Pendred).

---

# 2. Sensoriales (cocleares)

`gap_shape []`, `retro null`, `cce_pct` alto (80-100: las OEA se caen con la
pérdida).

| Cuadro | Patrón | Claves | Falta |
|---|---|---|---|
| **Hipoacusia por ruido (crónica, NIHL)** | Muesca 3-6 kHz **bilateral y simétrica** que se ensancha con los años; recuperación parcial en 8 kHz | clon de `muesca_4k` con `lateralidad 'bilateral'` y muesca más ancha (3k-6k altos); `cce_pct [85,100]`, tinnitus `prob` alta | la progresión (mismo paciente en dos momentos) no existe como eje |
| **Trauma acústico agudo (explosión)** | Unilateral o asimétrica, muesca profunda + a veces perforación → mixta | `sensorial` con muesca profunda; la versión con perforación necesita `gap_shape` y pasa a `mixta` | nada |
| **Ototoxicidad por salicilatos / quinina** | Plana leve-moderada **reversible** + tinnitus intenso | plana ~30 con `cce_pct [90,100]`, `tinnitus prob 0.9`, `permanente` bajo | la reversibilidad no se modela |
| **Laberintitis (viral / bacteriana / serosa)** | Profunda unilateral brusca + vértigo intenso; VEMP del lado abolido | `sn_shape` plano alto, `grados ['severa','profunda']`, `vemp ['type' => 'neural', 'umbral' => …]` alto, `conciencia [90,100]` | el vértigo solo vive en el texto de anamnesis |
| **Osificación coclear post-meningitis** | Profunda **bilateral**, OEA ausentes, ABR ausente; urgencia quirúrgica | `coclear_plana` con `grados ['profunda']`, `lateralidad 'bilateral'` | nada (es `coclear_plana` en su extremo) |
| **Conmoción laberíntica (TEC sin fractura)** | Agudos caídos unilateral + vértigo, tímpano normal, curva A | descendente ~45 en agudos, unilateral, `conciencia [90,100]` | nada |
| **Hidrops retardado** | Como Ménière pero años después de una pérdida profunda del mismo oído | clon de `meniere`; el eje que falta es la **fluctuación** | ídem Ménière |
| **Ménière — lo que falta** | El caso guarda una foto; el cuadro real sube y baja de semana a semana | — | sin eje temporal no hay forma de mostrar fluctuación; es el pedido más grande de este archivo junto con la tercera ventana |
| **Autoinmune del oído interno / otosífilis** | Bilateral asimétrica, **rápidamente progresiva**, fluctuante, responde a corticoides | plana-descendente 40-70, `lateralidad 'bilateral'`, asimetría marcada | la asimetría solo se sortea cuando los dos oídos traen el mismo cuadro |
| **Parotiditis / sarampión** | Unilateral profunda en la infancia, el resto normal | `coclear_plana` con `grados ['profunda']`, unilateral, `conciencia` baja (se descubre tarde) | nada |
| **Diabetes / insuficiencia renal** | Descendente bilateral simétrica, más rápida que la presbiacusia para la edad | clon de `presbiacusia` con escala mayor | el cuadro se solapa con la norma por edad; hace falta decir "peor que su mediana" |
| **Post-radioterapia** | Mixta: conductiva por otitis + coclear progresiva en agudos | `categoria 'mixta'` con `gap_shape` de efusión + descendente | nada |

## Genéticas y sindrómicas

Van todas como `sensorial` (o `neural` donde se indica) y lo que las separa es la
forma, la lateralidad y la edad de instalación, no el gen.

| Cuadro | Patrón | Claves |
|---|---|---|
| **No sindrómica GJB2 (conexina 26)** | Plana o descendente, **bilateral simétrica**, congénita, estable | `coclear_plana` con `conciencia` baja y `lateralidad 'bilateral'` |
| **Pendred** | Mixta/sensorial **progresiva** en escalones, malformación de Mondini, tercera ventana por acueducto dilatado | necesita el eje de tercera ventana (ver arriba) |
| **Usher** | Descendente bilateral progresiva + retinosis | `presbiacusia` en joven; el resto es anamnesis |
| **Waardenburg** | Unilateral o bilateral, profunda, estable, congénita | `coclear_plana` `['profunda']` |
| **Alport** | Descendente bilateral simétrica en agudos, adolescencia | clon de `ototoxica` sin el antecedente de fármaco |
| **Jervell-Lange-Nielsen** | Profunda bilateral congénita + QT largo | `coclear_plana` `['profunda']` bilateral |
| **Stickler** | Descendente + artropatía y miopía | descendente moderada bilateral |
| **CMV congénito** | Unilateral o asimétrica, **progresiva**, puede empezar normal | sin eje de progresión solo se puede mostrar una foto |
| **Rubéola / toxoplasmosis congénita** | Plana moderada-profunda bilateral | `coclear_plana` |
| **Kernicterus (hiperbilirrubinemia)** | **No es coclear**: ANSD con OEA conservadas | `categoria 'neural'`, `cce_pct [0,15]`, `retro 'kernicterus'` |

---

# 3. Neurales y retrococleares

Todos con `cce_pct` bajo (la disociación OEA presentes / ABR desarmado **es** el
hallazgo) y el preset de ABR que corresponde. Los 18 presets ya existen: lo que
falta es el cuadro de catálogo que los use.

| Cuadro | `retro` | Patrón | Claves |
|---|---|---|---|
| **NF2** | `nf2` | Mismo patrón del schwannoma **en los dos oídos**: sin asimetría el IT5 no ayuda | clon de `schwannoma` con `lateralidad 'bilateral'`, `vemp type 'neural'` |
| **Meningioma / epidermoide del ángulo** | `angulo` | Indistinguible del schwannoma en el ABR | clon de `schwannoma` |
| **Compresión microvascular del VIII** | `microvascular` | Alteración leve, a veces solo a tasas altas | pérdida leve descendente, `cce_pct [40,70]` |
| **Esclerosis múltiple** | `esclerosis_multiple` | Audiograma normal o casi, I-III normal y III-V largo, fatiga a tasas altas | `sn_shape` bajo, `grados ['leve']`, `cce_pct [20,60]`, bilateral |
| **Infarto pontino / AICA** | `infarto_pontino` | Brusco, III-V largo, puede dejar audiograma casi normal | `conciencia [90,100]`, unilateral |
| **Glioma de tronco** | `glioma_tronco` | Progresivo, III-V largo | bilateral asimétrico |
| **Siderosis superficial del SNC** | `siderosis` | Bilateral progresiva + ataxia, desincronía alta | bilateral, `cce_pct [10,40]` |
| **Chiari / hipertensión intracraneal** | `chiari_hic` | Todo corrido + interpicos largos | bilateral, `grados ['leve']` |
| **Leucodistrofias (Krabbe, adrenoleucodistrofia)** | `leucodistrofia` | Interpicos muy largos con audiograma conservado, niño | bilateral, `cce_pct [0,20]` |
| **Neuropatías hereditarias (CMT, Friedreich)** | `hereditaria_central` | I-III largo, progresión lenta | bilateral |
| **TEC de tronco** | `tec_tronco` | Brusco post trauma | unilateral o bilateral, `conciencia [90,100]` |
| **Bloqueo proximal del VIII** | `bloqueo_proximal` | Sin ondas desde III | unilateral |
| **Tóxico-metabólico (hepática, hipotiroidismo)** | `toxico_metabolico` | Todo lento y reversible | bilateral, `grados ['leve']` |
| **Hipotermia / depresores del SNC** | `hipotermia_farmacos` | Corre **todo**, onda I incluida, interpicos normales | bilateral, audiograma normal |
| **Prematuro (inmadurez de la vía)** | `prematuro` | Latencias largas por edad, no patología | `grados []`, bilateral, `conciencia` baja |

---

# 4. Mixtas

| Cuadro | Patrón | Claves |
|---|---|---|
| **Colesteatoma con fístula laberíntica** | Gap grande + caída coclear + vértigo con presión | `gap_shape` de colesteatoma + `sn_shape` moderado, `z ['B']`, `gap_max_db 55` |
| **Oído operado (timpanoplastia / mastoidectomía)** | Gap residual 10-30 dB, cavidad, a veces ósea caída | `gap_shape` ~20, `z ['Ad','B']`, `grados ['leve','moderada']` |
| **Enfermedad de Paget / otoespongiosis** | Mixta bilateral progresiva con componente conductivo moderado | `gap_shape` ~25 + descendente, bilateral |
| **Carcinoma de CAE / tumor temporal** | Gap grande unilateral + compromiso coclear + parálisis facial | `gap_shape` 40-50 + `sn_shape` alto |
| **Trauma craneal completo** | Fractura longitudinal (gap) + conmoción laberíntica (ósea) en el mismo oído | combinar `fractura_longitudinal` con `sn_shape` de conmoción |

---

# 5. Lo que el motor no puede hoy

Ordenado por cuántos cuadros desbloquea:

1. **Reflejo presente con gap** (`gap_con_reflejo`) — desbloquea dehiscencia del
   canal superior y acueducto dilatado. Hoy `reflexThreshold()` apaga el reflejo
   con gap ≥ 10 dB sin excepción.
2. **Ósea supranormal** (umbrales negativos) — misma familia; `aCinco()` recorta
   a 0.
3. **Eje temporal / fluctuación** — Ménière, hidrops retardado, autoinmune,
   tuba abierta, salicilatos, y toda progresión (NIHL, CMV, Pendred). Es el
   cambio más grande: hoy un caso es una foto.
4. **Asimetría declarada por el cuadro** — hoy solo se sortea asimetría cuando
   los dos oídos traen el mismo cuadro y el mismo grado.
5. **Otoscopia ligada al cuadro** — OMA, colesteatoma, perforación, glomus y
   atresia tienen hallazgo otoscópico obligado y hoy se carga aparte.
6. **Timpanograma "no registrable"** y **fluctuación respiratoria** — atresia de
   CAE y tuba abierta.
7. **Tinnitus pulsátil** en `TINNITUS_RUIDO_OPTIONS` — glomus.
8. **Eje no orgánico** (respuestas inconsistentes, SRT que no cuadra con el PTA,
   Stenger positivo) — simulación y exageración. No hay nada de esto en el
   perfil, y es un ejercicio entero.
9. **Procesamiento auditivo central** — audiograma normal con pruebas dicóticas
   alteradas; no hay módulo donde vivir.
10. **Hiperacusia / misofonía** — el LDL es un campo del formulario pero no un
    eje del perfil.
