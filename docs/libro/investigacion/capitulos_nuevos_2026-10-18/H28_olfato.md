# Informe H28. Olfatometría

Archivos: `docs/libro/capitulos/H28-olfatometria.md` (.py sin cambios, CASOS = []), `docs/libro/ilustraciones/hacer_h28.py` y `h28-via.svg`, `h28-transduccion.svg`, `h28-pruebas.svg`, `h28-escalera.svg`, `h28-tdi.svg`, `h28-edad.svg`. Capítulo de 12 páginas, armado con `--sin-completo` y revisadas todas las páginas. Sin ✍. Sin commit.

Fuentes leídas en texto completo (no solo resumen): Oleszkiewicz 2019 (PMC6411676, tablas incluidas), Whitcroft 2023 (PDF abierto de Rhinology Suppl 33), Hummel 2017 (manuscrito aceptado UEA, usado solo como respaldo), Delgado-Losada 2020 (PMC7762307). Resúmenes de PubMed para: Hummel 1997, 2001, 2007, 2009; Gudziol 2006; Doty 1984 (Physiol Behav y Laryngoscope); Pekala 2016; Frasnelli 2005; Kleene 2008; Buck 1991; Doty 2012; Hannum 2020; Schriever 2018. Autores, revista, volumen, páginas y DOI de todas las referencias verificados en PubMed/Crossref.

## 1. Afirmación cuantitativa, referencia, verificación

| Afirmación | Referencia | Cómo se verificó |
|---|---|---|
| Autorreporte: especificidad 87 %, sensibilidad 31 % | Whitcroft 2023 (cita un estudio de población) | texto completo de la guía |
| 30 a 40 % de pacientes con RSC y olfato alterado se creen normales | Whitcroft 2023 (Delank) | texto completo |
| Prevalencia COVID-19: 77 % con pruebas vs 44 % subjetivo | Hannum 2020, vía Whitcroft 2023 | texto de la guía + resumen PubMed de Hannum (la versión Chem Senses) |
| 98 pacientes a los 18 meses: 37 % con alteración persistente, 60 % no lo sabía | Whitcroft 2023 (Tognetti) | texto completo; ambigüedad: "60 % de estos pacientes" |
| PD: ~90 % con pérdida en etapa temprana, precede a lo motor | Doty 2012 | resumen PubMed |
| Prevalencia 22,2 % (28,8 % psicofísica, 9,5 % subjetiva), 25 estudios, 175 073 | Desiato 2021 vía Whitcroft 2023 | texto de la guía; metadatos de Desiato en Crossref |
| 6 a 30 millones de neuronas; ~400 genes de receptor activos; un receptor por neurona | Whitcroft 2023 | texto completo |
| Transducción: GPCR, adenilil ciclasa, canal CNG (cationes, Ca2+), salida de Cl- por canal activado por Ca2+; respuesta transitoria con adaptación | Kleene 2008 (resumen), Whitcroft 2023 | resumen + texto |
| Umbral = periférico (enfermedad sinusal), D e I = supraumbral (Parkinson); 1 226 pacientes | Whitcroft 2023 | texto completo |
| Sensibilidad T 64 %, D 56 %, I 47 % (2 178 participantes) | Whitcroft 2023 | texto completo |
| Umbral es el subpuntaje que más baja con la edad | Oleszkiewicz 2019 | texto completo |
| Azar: D ~5,3/16, I 4/16; dos aciertos seguidos = 1/9 | cálculo propio (3-AFC y 4 opciones) | aritmética |
| 1 h sin comer, beber (salvo agua), fumar, chicle, colonia ni cepillarse; sala silenciosa y ventilada; guantes sin olor | Delgado-Losada 2020 | texto completo de métodos |
| Anestesia tópica puede alterar el olfato; evitarla hasta después de la prueba | Whitcroft 2023 | texto completo |
| Bolígrafo de 14 cm, tampón con 4 mL; tapa fuera ~3 s; punta de una narina a otra | Oleszkiewicz 2019 | texto completo |
| Umbral: n-butanol (agua) o PEA (propilenglicol), 4 %, 16 pasos 1:2, tríos cada 20 s, comienza por la concentración más baja, promedio de las últimas 4 inversiones, puntaje 1-16 | Oleszkiewicz 2019 | texto completo |
| D: 16 tríos, ~3 s dentro del trío, 20-30 s entre tríos; I: 16 olores, 4 opciones, 20-30 s; venda en T y D; TDI 1-48 | Oleszkiewicz 2019 | texto completo |
| Cortes: anosmia funcional <=16; hiposmia 16,25-30,5; normosmia 30,75-41,25; superior >=41,5 | Oleszkiewicz 2019 | texto completo |
| Percentil 10 por edad: 19,4; 28,5; 30,75; 30,5; 28,15; 27,25; 24,88; 19,2; 13 | Oleszkiewicz 2019 | texto del artículo |
| Promedios TDI por grupo (25,21 a 23,30) | Oleszkiewicz 2019, tabla 1 | extraídos del XML del artículo (columna "todos"); redondeados en la figura |
| Mujeres +1,3 puntos | Oleszkiewicz 2019 | texto completo |
| Con el corte joven: 60 % de sanos de 71-80 años quedan hipósmicos; 10,7 % en 31-40 | Oleszkiewicz 2019, tabla 2 | tabla del artículo |
| DMI: TDI 5,5; I y D 3; T 2,5; >60 % notó mejoría con +5,5 | Gudziol 2006 (resumen) y Whitcroft 2023 (ref. 383 = Gudziol 2006) | resumen PubMed + lista de referencias de la guía |
| Cribado I de 12 ítems: ningún anósmico (n=112) superó 8 | Hummel 2001 | resumen PubMed |
| Diferencia lateral >=3 puntos: 15 % controles (479), 26 % RSC (765), 32 % tumores (53); umbral <2,5 e I <3 para seguir bilateral (acuerdo 70 %) | Whitcroft 2023 (Gudziol 2007) | texto completo |
| UPSIT: primer test "raspa y huele", r = 0,918 a 6 meses, detecta simulación | Doty 1984 | resumen PubMed |
| Entrenamiento: 40 vs 16, 2 veces al día, 12 semanas, rosa/eucalipto/limón/clavo | Hummel 2009 | resumen PubMed |
| Metaanálisis entrenamiento: 10 estudios, 639 pacientes, TDI +3,77 (IC 2,28-5,26), mejora D e I, no T | Pekala 2016 | resumen PubMed |
| Corticoides, lavados mejor que aerosoles, contraindicaciones (diabetes), dupilumab, cirugía solo en RSC | Whitcroft 2023 | recomendaciones del texto |
| Pronóstico: postraumática ~30 %; sinusal rara vez mejora sin tratamiento; posinfecciosa ~1/3 de 262 en 14 meses | Whitcroft 2023; Hummel 2017 (cifra tomada de H25) | texto completo |
| QOD: 205 pacientes, 25 controles; parosmia sufre más | Frasnelli 2005 | resumen PubMed |
| Validación española: descriptores cambiados (trementina, chucrut, manzanilla), p10 27,8 (veintes) etc. | Delgado-Losada 2020 | texto completo |

## 2. Lo tomado de la clase y qué dijo la literatura

Confirmado: epitelio olfatorio en el techo, neuronas bipolares con cilios en moco, axones por la lámina cribosa al bulbo, mitrales y en penacho a la corteza primaria (Whitcroft 2023); anosmia como pérdida del olfato; regeneración desde células basales (se dice "capaces de regenerarse", no "única neurona con regeneración").

Incongruencias o no confirmadas:
- **"Sin pasar por el tálamo"**: la clase lo afirma; Whitcroft 2023 describe la proyección directa a la corteza primaria y un papel del tálamo en la atención, pero no lo enuncia. Queda en el texto con `verificar`.
- **"20-30 nervios olfatorios (filetes)"** y **"cortisol +100 % con estimulación eléctrica"**: no verificados, no usados.
- **"ÚNICA neurona del SN con regeneración continua"**: no confirmado (hay neurogénesis en otras zonas); no usado.

## 3. Incongruencias de literatura entre fuentes (para el autor)

- Corte de hiposmia: 30,75 (Oleszkiewicz 2019, grupo 21-30) vs 30,5 (Oleszkiewicz dice que era el corte "hasta ahora") vs 30,3 (resumen de Hummel 2007 para 16-35 años). El texto lo explica en el recuadro de normas.
- Definición de inversión: Oleszkiewicz escribe "dos aciertos seguidos o un error marcan un punto de inversión", lo que leído literal contaría todo cambio de concentración. Aquí se usa la definición estándar de escalera (cambio de dirección) y 7 inversiones. Pendiente de confirmar con el manual del fabricante o Hummel 1997/2007.
- Anosmia funcional: Oleszkiewicz define "anosmia funcional" <=16 por D e I de 8 (90 % de anósmicos); el porcentaje de funcional en sanos de la tabla 2 es 0,45 % global.

## 4. `verificar` abiertos (6)

1. Ausencia de relevo talámico obligatorio (ver arriba).
2. Doty 1978: anósmicos detectan vapores irritantes por trigémino (resumen de PubMed vacío). La referencia se quitó de la lista; el ejemplo del amoníaco queda marcado.
3. Número total de inversiones (7) y definición de inversión (ver arriba).
4. UPSIT: 40 olores, 4 opciones, categorías de clasificación (el resumen de Doty 1984 no las trae).
5. Que la detección de simulación del UPSIT se base en puntajes bajo el azar.
6. No se encontró validación chilena del Sniffin' Sticks ni del UPSIT. No usar normas de otro país sin comprobar que los olores y descriptores se reconocen localmente.

## 5. Problemas de builder y otros

- `docs/libro/ilustraciones/hacer_h29.py` está **roto**: hace `from hacer_h25 import ... IZQ` y también usa `c.raw`, que `hacer_h25.Lienzo` no tiene (`ImportError: cannot import name 'IZQ'`). Los SVG de H29 existen, pero el script no corre; hay que arreglarlo en la renumeración (probablemente importaba de otro módulo). `hacer_h28.py` es autónomo (subclase de Lienzo con `raw`).
- La portada del capítulo imprime un autor de byline asignado por el builder ("Vanessa Uribe-Hernández"); no lo toqué.
- Las tablas dentro de la sección a dos columnas se parten entre columnas/páginas (tabla de clasificación del TDI); sin remedio sin tocar el builder.
- Escalera: en `:::imagen` con ancho=100% quedaba media página en blanco; se movió la figura al inicio de "Paso a paso" con ancho=90%.

## 6. Cambios sugeridos en otros capítulos

- **H25** (sección "Alteraciones del olfato"): la frase "La medición del olfato con pruebas psicofísicas no se trata en esta herramienta" debe remitir a → H28. La cifra "cerca de 5 % de la población general" (Hummel 2017) convive con 22,2 % (metaanálisis, Desiato 2021 vía Whitcroft 2023): son definiciones y métodos distintos; sugerido añadir una línea que aclare cuál es cuál. La referencia 2017 puede acompañarse con Whitcroft 2023 (actualización).
- **Cap. 35** (línea 293-294 y 343-347, caso Rocío): "evaluación del olfato" → "(→ H28)".
- **Cap. 36** (líneas 170-181, RSC con pólipos): remitir a → H28 cuando se habla de medir la pérdida del olfato; mencionar que el tratamiento con corticoides se evalúa con TDI (DMI 5,5).
- **Checklist**: marcar como ✓ en la fila "Métodos de exploración psicofísica del olfato" (H28), y ◐/✓ en "Mecanismos de transducción en el neuroepitelio olfatorio y vía olfatoria central" (H28 Fundamento; la histología del epitelio sigue pendiente en B3).
- **indice.md**, entrada H28: el sumario actual es compatible; podría agregar "ortonasal/retronasal, TDI, diferencia mínima importante, olfatometría objetiva".
