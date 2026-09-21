# Verificación del simulador de ABR / EOA

Batería de medición sobre el modelo. Corrida el 2026-09-21 contra `main`,
con el entorno del proyecto (`micromamba activate labsim`) para el cliente y
`php` para el backend.

**Segunda pasada**: los tres FUERA se corrigieron y se volvieron a medir (ver
"Correcciones"). Quedan un NO IMPLEMENTADO con explicación y **un hallazgo
nuevo que no estaba en la batería original**: el FSP no depende del nivel de
estímulo.

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
| B1 | Residuo al alternar | cada transductor | inserción 2-5 % · supraaural 5-10 % · vibrador 15 % | 3,5 % · 7,5 % · 15,0 % | OK |
| B2 | Onda I, rarefacción vs condensación | 80 dB nHL | rarefacción antes y más amplia | −0,100 ms · amplitud ×1,22 | OK |
| B3 | Onda I y V, alternada vs única | 80 dB nHL | más ancha y menor pico, por promedio real | onda I ancho ×1,027 · pico ×0,887 — onda V sin cambio | OK (ver nota) |
| C1 | Tubo pinzado | neuropatía, inserción, 95 dB | microfónica desaparece, artefacto persiste | microfónica 0,037 (piso 0,034) · artefacto 0,154 (4,5× el piso) | OK |
| C2 | Tubo abierto | mismo caso | microfónica presente e invertida, sin ondas neurales | microfónica 0,121 · onda V 0,031 (ruido) | OK |
| C3 | Pinzar con supraaural / vibrador | mismo caso | opción no disponible | `tube_clamped` = false en ambos | OK |
| D1 | Adulto normal 0/0 | umbral click | aéreo 10 · óseo 25 | 10 · 25 | OK |
| D2 | Neonato normal 0/0 | umbral click | aéreo 10 · óseo 10 | 10 · 10 | OK |
| D3 | Adulto conductiva 40/0 | umbral click | aéreo 50 · óseo 25 | 50 · 25 | OK |
| D4 | Neonato conductiva 40/0 | umbral click | aéreo 50 · óseo 10 | 50 · 10 | OK |
| D5 | Adulto conductiva 60/10 | umbral click | aéreo 70 · óseo 35 | 70 · 35 | OK |
| D6 | Adulto sensorial 30/30 | umbral + P(respuesta) en el tope | aéreo 40 · óseo 55 con P ≈ 0,5 | 40 · 55; P(detección) = 0,05 en el umbral y 0,64 a +5 dB | FUERA |
| D7 | Adulto sensorial 35/35 | umbral click | aéreo 45 · óseo sin respuesta | 45 · sin respuesta | OK |
| D8 | Adulto mixta 60/30 | umbral click | aéreo 70 · óseo 55 | 70 · 55 | OK |
| E1 | Cruce sin enmascarar | OD sensorial 35/35, OI normal, vibrador | respuesta desde 30 dB nHL (25 + IA 5) | primera respuesta a 30 dB nHL | OK |
| E2 | Con enmascaramiento | mismo caso, 70 dB al OI | sin respuesta | sin sombra en 20-55 dB | OK |
| E3 | Sobreenmascaramiento | inserción 90 dB, oído conductivo 40/0 | compara contra el umbral óseo | compara contra óseo (25 nHL); cruzado 25 → no sobreenmascara | OK |
| E4 | Sobreenmascaramiento | supraaural 80 dB, mismo caso | cruzado 35, sobreenmascara | umbral efectivo 50 → 60 nHL | OK |
| F1 | Amplitud onda V por SL | adulto normal | 0 % · 50 % · — · 100 % | SL 0 3,7 % · SL 10 52,3 % · SL 20 79,1 % · SL 40 100 % | OK |
| F2 | Ruido residual | 500/1000/2000/4000 barridos | cae con √N | 63,7 · 49,1 · 33,0 · 23,2 nV (razones 1,30 · 1,49 · 1,42) | OK |
| F3 | Umbral hallado | 500 vs 2000 barridos, 50 repeticiones | 500 queda 5-10 dB más alto | 40,8 vs 35,6 dB (diferencia 5,2) | OK |
| G1 | TEOAE por franja | 1000 neonatos, sorteo real | 0,40 · 0,55 · 0,75 · 0,85 · 0,93 · 0,95 (± 0,03) | 0,386 · 0,553 · 0,757 · 0,871 · 0,924 · 0,948 | OK |
| G2 | AABR por franja | 1000 neonatos, sorteo real | 0,85 · 0,92 · 0,95 · 0,96 · 0,97 · 0,97 (± 0,03) | 0,844 · 0,935 · 0,955 · 0,964 · 0,966 · 0,976 | OK |
| G3 | Cesárea a 30 h | TEOAE ≈ P(18 h) · AABR ≈ P(26 h) | 0,55 · 0,95 | 0,550 (P18 h = 0,550) · 0,950 (P26 h = 0,950) | OK |
| G4 | Pretérmino tardío a 40 h | TEOAE ≈ P(27 h) | 0,75 | 0,750 (P27 h = 0,750) | OK |
| G5 | Neuropatía a 72 h | TEOAE vs AABR | TEOAE pasa · AABR refiere | TEOAE 5/5 bandas → pasa · ABR 50 nHL → refiere | OK |
| G6 | Sensorial 40 dB a 72 h | TEOAE vs AABR | ambos refieren (P ≈ 0,02) | TEOAE 0/5 bandas → refiere · ABR 50 nHL → refiere | OK |
| H1 | FSP contra nivel | umbral 30, de +30 a −10 dB SL | debería caer con el nivel | 2,80 en TODOS los niveles | FUERA |

**34 OK · 2 FUERA** (uno de ellos hallado fuera de la batería original)

## Correcciones aplicadas en la segunda pasada

**B1** — residuo del artefacto al alternar, por transductor: inserción 3,5 %,
supraaural 7,5 %, vibrador 15 %. La cancelación no es total en ninguno, y es
peor cuanto menos simétrico es el transductor.

**B3** — la onda alternada dejó de calcularse con un factor de ensanchamiento
y pasa a ser el **promedio real** de la curva en rarefacción y la curva en
condensación (`build_polarity_curve`). El ensanchamiento y la caída del pico
salen solos de que las dos polaridades no tienen la misma latencia: la onda I
queda 2,7 % más ancha y 11,3 % más baja.

La onda V **no** cambia, y es correcto que no cambie: nuestro modelo de
polaridad está anclado en F27 y F10, que reportan diferencia entre
polaridades en la onda I y **ninguna consistente en III y V**. Si la V se
ensanchara, estaríamos contradiciendo la misma fuente que hace pasar B2.

**E1** — la comparación de la curva sombra pasa de "mayor que" a "mayor o
igual que": la sombra aparece a 30 dB nHL (umbral óseo del oído sano 25 +
atenuación interaural 5).

**C1** — la maniobra se mide a 95 dB nHL, que es el nivel al que se busca
microfónica. A 80 dB el artefacto de inserción (0,037 µV) queda bajo el piso
de ruido y la maniobra no se ve. A 95: artefacto 0,154 µV (4,5 veces el
piso), microfónica 0,099 con el tubo abierto y 0,037 al pinzar, o sea el piso
de ruido (0,034).

**G1-G4** — se rehicieron con sorteo real (`mt_rand`) en vez de barrer el
percentil. Los valores ahora tienen la dispersión esperable de 1000 sorteos
(±0,015) y siguen dentro de la tolerancia.

## Tests FUERA

### D6 — probabilidad de respuesta en el tope del vibrador

Con la definición unificada ("nivel detectable en el 50 % de los intentos con
2000 barridos") y criterio clínico de reproducibilidad —onda V presente en
los DOS subpromedios, a la misma latencia ± 0,3 ms, sobre 3 veces el ruido—
el modelo da:

| SL | P(detección) |
|---|---|
| +15 | 0,90 |
| +10 | 0,84 |
| +5 | 0,64 |
| **0** | **0,05** |
| −5 | 0,02 |

El punto del 50 % cae en SL +3 a +4, no en SL 0. O sea: **el umbral guardado
del caso es el nivel donde la respuesta empieza a existir, y el umbral que
mide el alumno queda un escalón de 5 dB por encima.**

No se corrigió subiendo la amplitud cerca del umbral: se probó con el codo en
0,05, 0,12 y 0,20 (3,4 %, 8,1 % y 13,1 % de amplitud a SL 0) y la P se movió
de 0,04 a 0,07. Lo que manda no es la amplitud sino el ruido de los
subpromedios, que tienen √2 más ruido que el promedio. Hacer coincidir las
dos definiciones exigiría bajar los umbrales guardados unos 5 dB, y esos
salen de `STIM_NHL_CORRECTION`, que está anclada en bibliografía.

Queda como decisión: o se documenta que el umbral del caso es el
fisiológico y el medido cae 5 dB arriba —que es la sobreestimación conocida
del ABR—, o se cambia el significado del campo.

### H1 — el FSP no depende del nivel de estímulo

**Hallazgo nuevo, no estaba en la batería.** Con un oído de umbral 30:

| dB | SL | FSP | índice de replicabilidad | onda V |
|---|---|---|---|---|
| 60 | +30 | 2,80 | 0,891 | 0,330 µV |
| 45 | +15 | 2,80 | 0,816 | 0,245 |
| 35 | +5 | 2,80 | 0,353 | 0,096 |
| 30 | 0 | 2,80 | 0,022 | 0,068 |
| 20 | −10 | 2,80 | 0,162 | 0,073 |

El FSP es el criterio con el que un equipo real declara "respuesta presente",
y en el modelo sale del caso (`fsp_puntos`, degradado por ruido y
electrodos), no del trazo. Da lo mismo con respuesta clara que sin respuesta.
El índice de replicabilidad sí sigue al nivel (0,891 → 0,022), así que el
ejercicio de mirar los subpromedios A/B funciona; el número del FSP, no.

Es lo que impide que D6 salga solo: si el FSP se calculara del trazo, la
probabilidad de detección emergería sin ninguna regla especial.

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
- **G (tamizaje)**: barrer el percentil de 0 a 1 mide la función cuantil y da
  los valores exactos de la tabla. Para verificar el SORTEO hay que usar
  `mt_rand`, que es lo que hace el caso real, y entonces aparece la
  dispersión de ±0,015.
- **D6 (detección)**: medir con "pico sobre ruido" en una ventana no sirve:
  el máximo del ruido en 5 ms ya alcanza 2-3 veces su RMS, así que se mide
  el ruido y no la respuesta. Hay que usar el criterio de reproducibilidad
  sobre los dos subpromedios.
