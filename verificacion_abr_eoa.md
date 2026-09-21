# Verificación del simulador de ABR / EOA

Batería de medición sobre el modelo. Última corrida: 2026-09-21 contra
`main`, con el entorno del proyecto (`micromamba activate labsim`) para el
cliente y `php` para el backend.

**Tercera pasada, sin FUERA.** Las dos primeras dejaron dos (D6 y el
hallazgo H1: el FSP no dependía del nivel de estímulo). Los dos se
corrigieron de raíz:

1. **El FSP se calcula sobre el trazo**, no se declara en el caso
   (`expected_fsp` + sorteo con F no central, criterio 3,1).
2. **El ruido del paciente se declara por las condiciones de registro**
   (nivel de referencia + barridos para el criterio), y el default deja la
   referencia EN EL UMBRAL con 2000 barridos.
3. **El umbral fisiológico está 9 dB por debajo del clínico**
   (`PHYSIOLOGICAL_OFFSET_DB`), así que en el umbral que declara el caso la
   onda V vale la mitad y el equipo la detecta en la mitad de los registros.

El único que había quedado fuera en esta pasada, F3, estaba mal planteado
en la batería y no en el modelo: el rango de 5-10 dB es el de UNA reducción
a la mitad de los barridos, y el test comparaba 500 contra 2000, que son
dos. Partido en F3a (1000 vs 2000) y F3b (500 vs 2000), el modelo cae
dentro de los dos.

Detalle del diseño en `TODO.md`. Cada test usa semilla fija. Los bloques A,
B, C, E y F miden el generador del cliente (`src/abr/ABR_generator.py`); los
bloques D y G, la proyección del backend
(`labsim_backend/src/CaseProfile.php`, `NewbornScreening.php`).

## Resultado

| paso | test | esperado | obtenido | estado |
|---|---|---|---|---|
| 1 | H1a FSP vs nivel (umbral 30, 2000 barridos) | monótono creciente | −10 dB 1,00 · 0 dB 3,26 · +10 6,23 · +20 9,85 · +30 10,69 | OK |
| 1 | H1b FSP−1 vs barridos | ×2 al duplicar | 500→1000 ×2,31 · 1000→2000 ×1,79 · 2000→4000 ×1,82 | OK |
| 1 | H1c FSP sin señal (30 dB bajo el umbral) | ≈ 1 | 1,00 | OK |
| 1 | H1d sorteo (80 registros iguales) | media = esperado, todos distintos | media 7,80 vs esperado 7,60 · 80/80 distintos · sd 3,27 | OK |
| 2 | H2a criterio en el punto declarado | FSP medio 3,1 | ref 40/N*1500 → 3,07 · 40/3000 → 3,07 · 55/2000 → 3,11 · 30/2000 → 3,13 | OK |
| 2 | H2b paciente más ruidoso | más barridos | N*1500 → 2000 barridos · N*3000 → 3250 | OK |
| 2 | H2c 10 dB bajo la referencia | más barridos | 2950 (contra 2000 en la referencia) | OK |
| 2 | H2d respuesta ausente en la referencia | cae al respaldo del equipo | σ del caso = None · residual 31,6 nV | OK |
| 2 | H2e conversión de casos viejos | N* = 2,1·2000/(FSP−1) | FSP 1,6→7000 · 2,0→4200 · 2,3→3231 · 2,8→2333 · 3,1→2000 · 4,0→1400 | OK |
| 3 | desfase umbral fisiológico | P ≈ 0,5 en el umbral del caso | 9,0 dB → P = 0,51 (150 reps, 2000 barridos) | OK |
| 3 | D6 sensorial 30/30, vibrador, 55 dB nHL | P ≈ 0,5 (0,40–0,60) | 0,50 (100 reps) | OK |
| 3 | F1 amplitud onda V por SL fisiológico | 0 % · 50 % · — · 100 % | SL 0 3,7 % · 10 52,3 % · 20 79,1 % · 40 100 % (umbral clínico 48,5 %) | OK |
| 3 | F3a umbral hallado, 1000 vs 2000 barridos | 5-7 dB más alto | 17,7 vs 12,2 dB → **5,5 dB** | OK |
| 3 | F3b umbral hallado, 500 vs 2000 barridos | 10-14 dB más alto | 24,7 vs 12,2 dB → **12,5 dB** | OK |
| 4 | A1 atenuación interaural | 65 / 45 / 5 / 22 / 13,5 | 65,0 / 45,0 / 5,0 / 22,0 / 13,5 | OK |
| 4 | A2 latencia onda V, inserción vs supraaural | 0,8 ms ± 0,1 | 0,800 ms | OK |
| 4 | A3 interpicos, inserción vs supraaural | 0 ms ± 0,05 | 0,000 / 0,000 / 0,000 | OK |
| 4 | A4 tope de salida (110 aéreo / 70 óseo) | 100 / 55 | 100,0 / 55,0 | OK |
| 4 | A5 artefacto, nivel alto | 0,20/0,8 · 0,48/1,0 · 0,48/1,2 | 0,199/0,80 · 0,478/1,00 · 0,475/1,23 | OK |
| 4 | A6 artefacto vs onda I a 90 dB | inserción separa, supraaural no | inserción fin 0,795 < inicio I 0,882 · supraaural 0,995 > 0,082 | OK |
| 4 | B1 residuo al alternar | 2-5 % · 5-10 % · 15 % | 3,5 % · 7,5 % · 15,0 % | OK |
| 4 | B2 onda I, rarefacción vs condensación | antes y más amplia | −0,100 ms · ×1,22 | OK |
| 4 | B3 alternada = promedio real | onda I más ancha y más baja, V sin cambio | I ancho ×1,039 pico ×0,887 · V ×1,000 / ×1,000 | OK |
| 4 | C1 tubo pinzado (neuropatía, 95 dB, 20000 barridos) | microfónica desaparece, artefacto persiste | microfónica 1,3× el piso (contra 4,0× abierto) · artefacto 0,132 µV intacto | OK |
| 4 | C2 tubo abierto | microfónica presente | 4,0× el piso | OK |
| 4 | C3 pinzar con supraaural / vibrador | no disponible | `tube_clamped` = false en ambos | OK |
| 4 | D1 adulto normal 0/0 | aéreo 10 · óseo 25 | 10 · 25 (hallados 10 · 30) | OK |
| 4 | D2 neonato normal 0/0 | aéreo 10 · óseo 10 | 10 · 10 (hallados 15 · 10) | OK |
| 4 | D3 adulto conductiva 40/0 | aéreo 50 · óseo 25 | 50 · 25 (hallado 50) | OK |
| 4 | D4 neonato conductiva 40/0 | aéreo 50 · óseo 10 | 50 · 10 (hallado 55) | OK |
| 4 | D5 adulto conductiva 60/10 | aéreo 70 · óseo 35 | 70 · 35 (hallado 40) | OK |
| 4 | D6 adulto sensorial 30/30 | aéreo 40 · óseo 55 | 40 · 55 | OK |
| 4 | D7 adulto sensorial 35/35 | aéreo 45 · óseo sin respuesta | 45 · sin respuesta (hallado 50) | OK |
| 4 | D8 adulto mixta 60/30 | aéreo 70 · óseo 55 | 70 · 55 (hallado 55) | OK |
| 4 | E1 cruce sin enmascarar (vibrador, OI normal) | respuesta desde 30 dB nHL | primera respuesta a 30 (barrido de 1 dB) | OK |
| 4 | E2 con 70 dB al OI | sin sombra | sin sombra en 20-55 dB | OK |
| 4 | E3 sobreenmascaramiento, inserción 90 dB | compara contra el óseo, no sobreenmascara | cruzado 25 = umbral óseo → umbral usado 50 | OK |
| 4 | E4 sobreenmascaramiento, supraaural 80 dB | sobreenmascara | cruzado 35 > 25 → umbral usado 60 | OK |
| 4 | F2 ruido residual (8 semillas) | cae como 1/√N | 101,7 · 68,5 · 47,9 · 35,9 nV (×1,48 · 1,43 · 1,33) | OK |
| 4 | G1 TEOAE por franja (1000 sorteos) | 0,40 · 0,55 · 0,75 · 0,85 · 0,93 · 0,95 ±0,03 | 0,386 · 0,553 · 0,736 · 0,861 · 0,930 · 0,954 | OK |
| 4 | G2 AABR por franja | 0,85 · 0,92 · 0,95 · 0,96 · 0,97 · 0,97 ±0,03 | 0,862 · 0,940 · 0,948 · 0,960 · 0,966 · 0,970 | OK |
| 4 | G3 cesárea a 30 h | TEOAE ≈ P(18 h) 0,55 · AABR ≈ P(26 h) 0,95 | 0,549 · 0,936 | OK |
| 4 | G4 pretérmino tardío a 40 h | TEOAE ≈ P(27 h) 0,75 | 0,749 | OK |
| 4 | G5 neuropatía, AABR 35 dB nHL | refiere | P(pasa) = 0,00 (control normal 1,00) | OK |
| 4 | G6 sensorial 40 dB, AABR 35 dB nHL | refiere | P(pasa) = 0,00 | OK |

**44 OK · 0 FUERA**

## Dos cosas que conviene tener a mano

### El desfase del umbral fisiológico es de 9 dB

Más de los 3-5 dB que se estimaban a ojo, pero no es un número elegido: se
calibró contra el criterio FSP ≥ 3,1, que era la idea. Lo que deja es lo que
se quería:

- en el umbral clínico del caso la onda V mide el **48 %** de su amplitud a
  SL 40, y el FSP ronda 3,1 con 2000 barridos;
- o sea que ahí el equipo declara respuesta en la mitad de los registros;
- el alumno que promedia poco o no repite **sobreestima el umbral**, igual
  que en la clínica.

### El umbral del caso está referido a 2000 barridos

Es parte de la definición, no un detalle: el umbral que declara el docente
es el nivel donde el equipo dice "presente" en la mitad de los registros
**con 2000 barridos**. Quien promedie más puede encontrar respuesta algo por
DEBAJO del umbral declarado, y eso es correcto: es lo que pasa en la clínica
cuando se promedia mucho en un paciente tranquilo. En la ficha, el campo
lleva la nota "referido a 2000 barridos".

### Barridos y umbral: media son 6 dB

Cada vez que se parten los barridos a la mitad, el umbral hallado sube unos
6 dB. Medido sobre un umbral declarado de 10 dB nHL: 500 → 24,7 · 1000 →
17,7 · 2000 → 12,2 · 4000 → 9,5. Es la consecuencia directa de la curva de
crecimiento que exige F1 (50 % de amplitud a 10 dB sobre el umbral
fisiológico) combinada con el 1/√N del promediado, y por eso empinar la
curva para "arreglar" F3 rompería F1.

Dos lecturas de esa serie que conviene no confundir:

- **Los 9,5 dB a 4000 barridos no son un error de redondeo**: el piso no es
  el umbral declarado (10) sino el **fisiológico**, que con el desfase de 9
  dB queda en 1 dB nHL. Promediando más se encuentra respuesta por debajo
  del declarado, hasta que la amplitud se acerca a cero y el escalón se
  achica (7,0 · 5,5 · 2,7 dB): cerca del umbral fisiológico, agregar
  barridos rinde cada vez menos.
- **Los 2,2 dB entre 12,2 hallado y 10 declarado** salen del paso de 5 dB de
  la búsqueda y están dentro de la tolerancia.

**Para armar casos:** con N* = 800 al nivel de referencia, el alumno que se
detiene a los 400 barridos va a informar un umbral ~6 dB más alto que el
declarado. Sirve como pregunta: por qué su umbral quedó más alto que el
esperado.

## Cómo reproducirla

```bash
micromamba activate labsim                # cliente: numpy, scipy, PySide6
python tests/test_abr_generator.py        # 1 test = 1 propiedad del modelo
python tests/test_abr_panel.py
cd labsim_backend && php tests/run.php    # backend (3916 asserts)
```

Los bloques D y G se miden llamando a `CaseProfile::project()` y
`NewbornScreening::transientDb()`; los bloques A, B, C, E y F, llamando a
`generate_curve()` con `capture_id` fijo. Seis medidas necesitan cuidado y se
dejan anotadas porque alguna versión las midió mal:

- **C (microfónica)**: no se ve comparando el pico temprano, porque ahí
  domina el artefacto. Se mide como la diferencia entre rarefacción y
  condensación, que es lo único que invierte, a 95 dB nHL y con 20000
  barridos, y se contrasta contra el piso de la MISMA métrica con las dos
  trazas en la misma polaridad.
- **F2 (ruido)**: una sola realización tiene ~15 % de dispersión. Se
  promedian 8 semillas.
- **E1 (sombra)**: hay que barrer de a 1 dB; con paso de 5 parece caer entre
  30 y 40.
- **G (tamizaje)**: barrer el percentil mide la función cuantil; para
  verificar el SORTEO hay que usar `mt_rand`, que es lo que corre en el caso
  real, y ahí aparece la dispersión de ±0,015.
- **D6 y todo lo que sea "probabilidad de detección"**: se mide con el FSP
  del propio registro contra el criterio 3,1, nunca con "pico sobre ruido"
  en una ventana: el máximo del ruido en 5 ms ya alcanza 2-3 veces su RMS,
  así que esa métrica mide el ruido y no la respuesta.
- **`generate_curve` y no `ABR_Curve`**: el envoltorio reinterpreta el
  argumento de promediación y fabrica promedios intermedios, así que medir
  barridos con él da números que no son los del registro.
