# Verificación del simulador de ABR / EOA

Batería de medición sobre el modelo, sin tocar código. Corrida el 2026-09-21
contra `main` en el commit `5967ee2`, con el entorno del proyecto
(`micromamba activate labsim`) para el cliente y `php` para el backend.

Cada test usa semilla fija. Los bloques A, B, C, E y F miden el generador del
cliente (`src/abr/ABR_generator.py`, `src/oae/generators/`); los bloques D y G
miden la proyección del backend (`labsim_backend/src/CaseProfile.php`,
`NewbornScreening.php`).

## Resultado

| # | test | condición | esperado | obtenido | estado |
|---|---|---|---|---|---|
| A1 | Atenuación interaural | por transductor y población | 65 / 45 / 5 / 22 / 13,5 | 65,0 / 45,0 / 5,0 / 22,0 / 13,5 | OK |
| A2 | Latencia onda V | click 80 dB, inserción vs supraaural | 0,8 ms ± 0,1 (inserción más tardía) | 0,800 ms | OK |
| A3 | Interpicos | inserción vs supraaural | 0 ms ± 0,05 | I-III 0,000 · III-V 0,000 · I-V 0,000 | OK |
| A4 | Tope de salida | pedir 110 aéreo / 70 óseo | 100 / 55 | 100,0 / 55,0 | OK |
| A5 | Artefacto, nivel alto | polaridad única | 0,20/0,8 · 0,48/1,0 · 0,48/1,2 | 0,199/0,80 · 0,478/1,00 · 0,475/1,23 | OK |
| A6 | Artefacto vs onda I | 90 dB nHL | inserción sin superposición, supraaural con | inserción fin 0,795 < inicio I 0,882 · supraaural fin 0,995 > inicio I 0,082 | OK |
| B1 | Residuo al alternar | cada transductor | 10-20 % del artefacto | inserción 0 % · supraaural 0 % · vibrador 15 % | FUERA |
| B2 | Onda I, rarefacción vs condensación | 80 dB nHL | rarefacción antes y más amplia | −0,100 ms · amplitud ×1,22 | OK |
| B3 | Onda V, alternada vs única | 80 dB nHL | más ancha y menor pico | ancho ×1,05 · pico ×1,00 | FUERA |
| C1 | Tubo pinzado | neuropatía, inserción, 80 dB | microfónica desaparece, artefacto persiste | microfónica 0,058 (piso de ruido 0,046) · artefacto 0,037 | OK |
| C2 | Tubo abierto | mismo caso | microfónica presente e invertida, sin ondas neurales | microfónica 0,121 · onda V 0,031 (ruido) | OK |
| C3 | Pinzar con supraaural / vibrador | mismo caso | opción no disponible | `tube_clamped` = false en ambos | OK |
| D1 | Adulto normal 0/0 | umbral click | aéreo 10 · óseo 25 | 10 · 25 | OK |
| D2 | Neonato normal 0/0 | umbral click | aéreo 10 · óseo 10 | 10 · 10 | OK |
| D3 | Adulto conductiva 40/0 | umbral click | aéreo 50 · óseo 25 | 50 · 25 | OK |
| D4 | Neonato conductiva 40/0 | umbral click | aéreo 50 · óseo 10 | 50 · 10 | OK |
| D5 | Adulto conductiva 60/10 | umbral click | aéreo 70 · óseo 35 | 70 · 35 | OK |
| D6 | Adulto sensorial 30/30 | umbral + P(respuesta) en el tope | aéreo 40 · óseo 55 con P ≈ 0,5 | 40 · 55; respuesta determinista | NO IMPLEMENTADO |
| D7 | Adulto sensorial 35/35 | umbral click | aéreo 45 · óseo sin respuesta | 45 · sin respuesta | OK |
| D8 | Adulto mixta 60/30 | umbral click | aéreo 70 · óseo 55 | 70 · 55 | OK |
| E1 | Cruce sin enmascarar | OD sensorial 35/35, OI normal, vibrador | respuesta desde 25 dB nHL | primera respuesta a 31 dB nHL | FUERA |
| E2 | Con enmascaramiento | mismo caso, 70 dB al OI | sin respuesta | sin sombra en 20-55 dB | OK |
| E3 | Sobreenmascaramiento | inserción 90 dB, oído conductivo 40/0 | compara contra el umbral óseo | compara contra óseo (25 nHL); cruzado 25 → no sobreenmascara | OK |
| E4 | Sobreenmascaramiento | supraaural 80 dB, mismo caso | cruzado 35, sobreenmascara | umbral efectivo 50 → 60 nHL | OK |
| F1 | Amplitud onda V por SL | adulto normal | 0 % · 50 % · — · 100 % | SL 0 3,7 % · SL 10 52,3 % · SL 20 79,1 % · SL 40 100 % | OK |
| F2 | Ruido residual | 500/1000/2000/4000 barridos | cae con √N | 63,7 · 49,1 · 33,0 · 23,2 nV (razones 1,30 · 1,49 · 1,42) | OK |
| F3 | Umbral hallado | 500 vs 2000 barridos, 50 repeticiones | 500 queda 5-10 dB más alto | 40,8 vs 35,6 dB (diferencia 5,2) | OK |
| G1 | TEOAE por franja | 1000 neonatos de término | 0,40 · 0,55 · 0,75 · 0,85 · 0,93 · 0,95 | 0,400 · 0,550 · 0,750 · 0,850 · 0,930 · 0,950 | OK |
| G2 | AABR por franja | 1000 neonatos de término | 0,85 · 0,92 · 0,95 · 0,96 · 0,97 · 0,97 | 0,850 · 0,920 · 0,950 · 0,960 · 0,970 · 0,970 | OK |
| G3 | Cesárea a 30 h | TEOAE ≈ P(18 h) · AABR ≈ P(26 h) | 0,55 · 0,95 | 0,550 (P18 h = 0,550) · 0,950 (P26 h = 0,950) | OK |
| G4 | Pretérmino tardío a 40 h | TEOAE ≈ P(27 h) | 0,75 | 0,750 (P27 h = 0,750) | OK |
| G5 | Neuropatía a 72 h | TEOAE vs AABR | TEOAE pasa · AABR refiere | TEOAE 5/5 bandas → pasa · ABR 50 nHL → refiere | OK |
| G6 | Sensorial 40 dB a 72 h | TEOAE vs AABR | ambos refieren (P ≈ 0,02) | TEOAE 0/5 bandas → refiere · ABR 50 nHL → refiere | OK |

**32 OK · 3 FUERA · 1 NO IMPLEMENTADO**

## Tests FUERA

### B1 — residuo del artefacto con polaridad alternada

Obtenido: inserción **0,000 %**, supraaural **0,000 %**, vibrador **15,0 %**.

Solo el vibrador tiene residuo. En los fonos la cancelación se modela como
total (`ARTIFACT_ALT_RESIDUAL` en `ABR_generator.py`), porque el dato que
originó la constante hablaba de la vía ósea. Si el residuo también existe en
los fonos, es cambiar dos valores de ese diccionario.

### B3 — onda V con polaridad alternada

Obtenido: ancho **×1,050** (correcto, más ancha), amplitud de pico
**×1,000** (esperado: menor).

El ensanchamiento se aplica sobre la sigma de la onda y no sobre su
amplitud, así que la gaussiana queda más ancha pero igual de alta. Para que
el pico baje habría que repartir: ensanchar y dividir la amplitud por el
mismo factor, que es lo que pasa cuando se promedian dos respuestas
desfasadas a energía constante.

### E1 — primera respuesta por vía ósea sin enmascarar

Obtenido: **31 dB nHL** (sin sombra a 30, con sombra a 31).

El esperado de 25 asume atenuación interaural ósea de 0. El modelo usa 5 dB
—dentro del rango publicado de 0-10— así que la sombra necesita superar el
umbral óseo del oído sano (25 nHL) más esos 5. Con IA = 0 daría exactamente
25. Es decidir qué punto del rango publicado se simula.

## NO IMPLEMENTADO

### D6 — probabilidad de respuesta en el tope del vibrador

Los umbrales salen correctos (aéreo 40, óseo 55), pero una respuesta que
cae justo en el tope de salida se entrega siempre, no con probabilidad 0,5.

Se probó modelar compresión del vibrador en sus últimos dB y se descartó: el
umbral del caso ya está en unidades de dial, así que descontar ahí otra vez
convierte "respuesta frágil en el tope" en "respuesta ausente". Hoy la
fragilidad sale por otro lado —estimular en el umbral deja una onda mínima,
ver `WAVE_AMP_GROWTH`— y esa sí depende de cuánto promedie el alumno (ver
F3). Falta, si se quiere, el sorteo explícito.

## Cómo reproducirla

```bash
micromamba activate labsim          # cliente: numpy, scipy, PySide6
cd labsim_backend && php tests/run.php    # backend
```

Los bloques D y G se miden llamando a `CaseProfile::project()` y
`NewbornScreening::transientDb()` con percentil barrido de 0 a 1; los
bloques A, B, C, E y F, llamando a `ABR_Curve()` y a los helpers del
generador con `capture_id` fijo. Tres medidas necesitan cuidado y se dejan
anotadas porque la primera versión las midió mal:

- **C (microfónica)**: no se ve comparando el pico temprano, porque ahí
  domina el artefacto. Se mide como la diferencia entre las trazas de
  rarefacción y condensación, que es lo único que invierte. Con 2000
  barridos el ruido tapa el efecto: hay que subir a 20000 y contrastar
  contra el piso de la métrica (dos corridas iguales, 0,046 µV).
- **F2 (ruido)**: una sola realización tiene ~15 % de dispersión. Se
  promedian 8 semillas.
- **E1 (sombra)**: hay que barrer de a 1 dB para encontrar la transición;
  con paso de 5 dB parece caer entre 30 y 40.
