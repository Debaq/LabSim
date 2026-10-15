# Libro de casos LabSim — índice propuesto

Borrador del índice (2026-10-15). Libro gratuito; licencia propuesta
**CC BY-NC-SA 4.0** (la obliga OtitisMediaKPJ, la única fuente con colesteatoma
y efusión).

Cada capítulo tiene la misma estructura, y sus referencias van al final del
capítulo (no hay bibliografía general):

1. **Técnica** — la prueba que el capítulo enseña a hacer
2. **Fisiología** — lo que esa prueba mide
3. **Patología** — los cuadros del capítulo
4. **Razonamiento** — cómo se llega del resultado al diagnóstico
5. **Casos** — cada uno sale de una clave de `CaseProfile::SCENARIOS`, así
   que las figuras las genera el mismo motor de la app
6. **Referencias del capítulo**

Cada técnica se enseña una sola vez, en el capítulo donde más pesa; los
capítulos siguientes la dan por sabida.

**Leyenda:**

- Referencias: **✓** = ya está en el sistema (código entre paréntesis) ·
  **✗** = no la tenemos, buscarla.
  Patología: todos los cuadros tienen cita en `BibliografiaPatologias`
  (173 citas); no se repite en cada capítulo.
- Otoscopía: **V** = Viscaino 2020, U. de Chile (CC0) · **B** = Başaran (CC BY 4.0) ·
  **K** = OtitisMediaKPJ (CC BY-NC-SA 4.0) · **N** = membrana normal ·
  **✗** = sin foto libre.
- Motor: **(a mano)** = el docente lo arma forzando campos · **(TODO n)** =
  el motor todavía no puede.
- **★** = uno de los 10 pacientes de práctica deliberada (casos 33-42), ya armados.

---

## Preliminares

- Cómo leer este libro: los cinco bloques y la ficha de cada caso
- El elenco: los pacientes que vuelven a lo largo del libro
- Abreviaturas y símbolos del audiograma (✓ S03 ASHA 1990)
- Sobre las imágenes: otoscopías de bancos abiertos, rostros generados con IA,
  personajes ficticios

## Parte I — El oído que transmite

### 1. Antes de medir: el conducto
- **Técnica:** otoscopía (✗) · acumetría, Rinne y Weber (✓ BSA2022RW, KELLY2018, UNGAR2021, STANK1979)
- **Fisiología:** oído externo, resonancia del conducto, migración del epitelio y cerumen (✗)
- **Casos:**
  - Tapón de cerumen [`tapon_cerumen`] — V/B
  - Cuerpo extraño [`cuerpo_extrano_cae`] — B (3 fotos)
  - Otitis externa difusa [`otitis_externa`] — B
  - Estenosis / atresia congénita [`estenosis_atresia_cae`] — ✗
  - Carcinoma del conducto [`carcinoma_cae`] — ✗

### 2. Líquido detrás del tímpano
- **Técnica:** timpanometría de 226 Hz: tipos, volumen, compliancia, gradiente (✗); función tubaria (✓ WILLIAMS1975, SMITH2015, LU2026, LEE2026)
- **Fisiología:** trompa de Eustaquio y ventilación del oído medio (✗)
- **Casos:**
  - ★35 Benjamín, 5 años, resfríos todo el invierno [`otitis_media`] — K
  - Otitis media aguda [`otitis_media_aguda`] — B/K
  - Disfunción tubaria con presión negativa [`disfuncion_tubaria`] — ✗
  - Barotrauma [`barotrauma`] — ✗

### 3. Membrana y cadena
- **Técnica:** audiometría tonal por vía aérea y ósea (✓ ISO2010, ISO1989, ASHA2005, BSA2018, ISP2018, NTP285); grados (✓ S02 BIAP)
- **Fisiología:** adaptación de impedancias del oído medio, que son la relación de áreas y la palanca (✗); mecanismos de la conducción ósea (✗)
- **Casos:**
  - Perforación timpánica [`perforacion`] — K
  - Timpanoesclerosis / miringoesclerosis [`timpanoesclerosis`] — V/B
  - Disyunción de cadena [`disyuncion_cadena`] — N
  - Fractura de cadena [`fractura_cadena`] y longitudinal del peñasco [`fractura_longitudinal`] — ✗
  - Colesteatoma sin daño coclear [`colesteatoma`] — K
  - Glomus timpánico [`glomus_timpanico`] — ✗
  - ★41 Chofer de micro operado de niño [`oido_operado` / `mixta_otitis_cronica`] — K/B

### 4. Rigidez
- **Técnica:** reflejo estapedial: umbral, ipsi y contra, ON-OFF (✓ GSI-AR, DEBRUYNE1992, CAMICAS1992, COLLETTI1987); normas del umbral del reflejo y patrones de Jerger (✗)
- **Fisiología:** arco reflejo estapedial (✗); muesca de Carhart (✗ Carhart 1950)
- **Casos:**
  - ★34 Secretaria de notaría, 34 años [`otoesclerosis`] — N
  - Fijación congénita del estribo [`fijacion_congenita_estribo`] — N
  - Enfermedad de Paget [`paget`] — N

## Parte II — La cóclea

### 5. Envejecer oyendo
- **Técnica:** logoaudiometría: SRT, discriminación, PB máx., roll-over, curva sombra (✗); LDL y campo dinámico (✗)
- **Fisiología:** tonotopía y codificación del habla (✗); umbrales por edad (✓ S01 ISO 7029)
- **Casos:**
  - ★36 Carpintero jubilado, 74 años, "yo escucho bien" [`presbiacusia`]
  - Diabetes / insuficiencia renal [`metabolica`]

### 6. Ruido
- **Técnica:** emisiones otoacústicas TEOAE, DPOAE y SOAE (✗); audiometría ocupacional (✓ ISP2018, ISP2012, PREXOR); acufenometría (✗)
- **Fisiología:** células ciliadas externas, amplificador coclear, electromotilidad (✗)
- **Casos:**
  - ★33 Electricista de 23 años antes de entrar a la mina: la línea de base [`normal`]
  - ★37 Operador de chancador, 22 años de turnos [`nihl_cronica`]
  - Trauma acústico agudo [`trauma_acustico_agudo`] · muesca en 4 kHz [`muesca_4k`]

### 7. De un día para otro
- **Técnica:** enmascaramiento: cuándo y cuánto, atenuación interaural por transductor, plateau, efecto de oclusión (✓ BSA2018, NTP285; ✗ atenuación interaural de inserto/supraaural/vibrador, plateau de Hood)
- **Fisiología:** atenuación interaural y curva sombra (✗)
- **Casos:**
  - Hipoacusia súbita [`subita`]
  - Laberintitis [`laberintitis`]
  - Conmoción laberíntica [`conmocion_laberintica`]
  - ★42 Estudiante de 22 años, cófosis tras paperas [`parotiditis`]
  - Autoinmune / otosífilis [`autoinmune`] (TODO 42)

### 8. Lo que deja un tratamiento
- **Técnica:** monitoreo de ototoxicidad: audiometría de alta frecuencia y seriada, criterios de cambio (✗)
- **Fisiología:** por qué la base de la cóclea cae primero (✗)
- **Casos:**
  - Ototoxicidad por cisplatino o aminoglucósidos [`ototoxica`] (TODO 41)
  - Salicilatos y quinina: la que se recupera [`salicilatos`]
  - Post-radioterapia de cabeza y cuello [`post_radioterapia`]

### 9. Hidrops
- **Técnica:** electrococleografía: SP/AP, área, electrodo (✓ E01-E07); reclutamiento: Fowler y SISI (✗)
- **Fisiología:** endolinfa, potencial endococlear, potencial de sumación (✗)
- **Casos:**
  - ★38 Profesora de lenguaje, primera crisis hace un año [`meniere`]
  - Hidrops retardado contralateral [`hidrops_retardado`]

### 10. Lo que viene en la familia
- **Técnica:** audiometría en el niño: conductual, condicionada por juego (✗)
- **Fisiología:** homeostasis del potasio en la cóclea y conexina 26; estría vascular (✗)
- **Casos:**
  - GJB2 [`gjb2`] · Waardenburg [`waardenburg`] · Usher 2 [`usher`]
  - Alport [`alport`] · Jervell-Lange-Nielsen [`jervell_lange_nielsen`] · Stickler [`stickler`]
  - Pendred / acueducto vestibular dilatado [`pendred`] (TODO 40)

## Parte III — Más allá de la cóclea

### 11. Asimetría que no cierra
- **Técnica:**
  - Deterioro tonal de Carhart, Rosenberg y Stat (✗)
  - Decay del reflejo (✓ HIRSCH1983, ROSENHALL1979, COOK1999)
  - SISI (✗)
  - ABR neurootológico: latencias e interpicos (✓ F01, F09, F10, F14, F15, F16, F26)
- **Fisiología:** adaptación neural; qué mide la latencia (✗)
- **Casos:**
  - ★39 Contador de 54 años, "el teléfono solo con el izquierdo" [`schwannoma`]
  - NF2 [`nf2`] · Ángulo pontocerebeloso [`tumor_angulo`]
  - Compresión microvascular [`compresion_microvascular`]
  - Coclear con componente retrococlear [`sensorioneural`]

### 12. El tronco
- **Técnica:** ABR: interpicos, diferencia interaural, efecto de la tasa (✓ F13, F10, F16)
- **Fisiología:** generadores de las ondas I-VII y vía auditiva central (✗ Møller)
- **Casos:**
  - Esclerosis múltiple [`esclerosis_multiple`]
  - Infarto pontino [`infarto_pontino`] · Infarto de la AICA [`infarto_aica`]
  - Glioma [`glioma_tronco`] · Chiari [`chiari_hic`] · HIC idiopática [`hic_idiopatica`]
  - Siderosis [`siderosis`] · TEC de tronco [`tec_tronco`]

### 13. Oye pero no entiende
- **Técnica:** microfónica coclear: polaridad (✓ F27), pinzar el tubo (✗); OEA + ABR juntos (✗)
- **Fisiología:** sincronía neural, sinapsis de la célula ciliada interna (✗)
- **Casos:**
  - ★40 Escolar de 15 años, "escucho que me hablan pero no entiendo" [`neuropatia`]
  - Neuropatía hereditaria [`neuropatia_hereditaria`]
  - Kernícterus [`kernicterus`] · Leucodistrofia [`leucodistrofia`]

### 14. Lo que mueve el ABR sin ser el oído
- **Técnica:** factores del sujeto: edad, sexo, temperatura, fármacos (✓ F09, F10, F20; ✗ temperatura)
- **Fisiología:** mielinización y maduración de la vía (✓ F19, F11; ✗ revisión de fisiología)
- **Casos:**
  - Hipotiroidismo [`toxico_metabolico`]
  - Hipotermia / depresores [`hipotermia_farmacos`]
  - Coma: bloqueo proximal [`bloqueo_proximal`]
  - Prematuro [`prematuro`]

## Parte IV — Mixtas y complicadas

### 15. Cuando también cae la ósea
- **Técnica:** el dilema de enmascaramiento (✓ BSA2018; ✗ fuente clásica del dilema); ABR por vía ósea (✓ A02, A06, F18)
- **Fisiología:** por qué la ósea cae en la otoesclerosis sin daño coclear (✗ Carhart 1950, ya pedido en el cap. 4)
- **Casos:**
  - Otitis crónica con daño coclear [`mixta_otitis_cronica`] — K/B
  - Otoesclerosis avanzada [`mixta_otoesclerosis`]
  - Colesteatoma con fístula [`colesteatoma_fistula`] — K
  - Fractura transversal [`fractura_transversal`] — ✗
  - Trauma craneal completo [`trauma_craneal_completo`] — ✗
  - Osificación coclear post-meningitis [`osificacion_coclear`]

## Parte V — El recién nacido

### 16. Tamizaje: las primeras horas
- **Técnica:** TEOAE y AABR de tamizaje, protocolo y momento (✓ N01-N11, JCIH 2019)
- **Fisiología:** oído del recién nacido: vérnix, mesénquima, transitorio de las primeras horas (✓ N08; ✗ fuente de fisiología)
- **Casos:**
  - Recién nacido sano a las 12 h y a las 48 h [`normal` + `efusion_neonatal`]
  - AABR que pasa con TEOAE que refiere

### 17. El lactante que se estudia
- **Técnica:**
  - Timpanometría de 1000 Hz (✗)
  - ABR con tone burst y estimación de umbral, corrección nHL a eHL (✓ F23, A03; ✗ tablas de corrección)
  - Vía ósea del lactante (✓ A04, A05, A06)
- **Fisiología:** maduración del oído medio y del tronco (✓ F11, F12, F07, F25)
- **Casos:**
  - CMV congénito [`cmv_congenito`] (TODO 41-42)
  - Rubéola / toxoplasmosis [`rubeola_congenita`]
  - Asfixia perinatal [`asfixia_perinatal`]

## Parte VI — Cuando el problema es la técnica

### 18. El ABR que engaña
- **Técnica:** promediación, FSP y ruido residual (✓ A01 Elberling y Don); rechazo de artefactos (✗); artefacto de estímulo, respuesta postauricular, falsa V (✗)
- **Fisiología:** el EEG de fondo, el músculo, y por qué el promedio mejora con la raíz de los barridos (✗)
- **Casos:**
  - Falsa onda V: los subpromedios A/B la delatan
  - Artefacto de estímulo: se confirma pinzando el tubo
  - Respuesta postauricular a 13 ms: replica en A/B y no es respuesta
  - Paciente inquieto: rechazo, barridos perdidos
  - Onda I ausente por el montaje: el falso retrococlear

### 19. El paciente que no calza
- **Técnica:** pérdida no orgánica: SRT vs. PTA, Stenger, ABR mejor que el audiograma (✗)
- **Fisiología:** no aplica; acá el bloque es la conducta del paciente (✗ fuente)
- **Casos:**
  - Simulación (a mano; TODO 45)
  - El acompañante que contesta por el paciente

## Parte VII — Cuando también hay vértigo

### 20. VEMP
- **Técnica:** cVEMP y oVEMP: montaje, estímulo, corrección por EMG, umbral (✗ excepto Murofushi 2001, dentro de patologías)
- **Fisiología:** vía vestíbulo-cólica y vestíbulo-ocular, sáculo y utrículo (✗)
- **Casos:**
  - Ménière: VEMP sacular alterado [`meniere`]
  - Laberintitis vs. neuritis [`laberintitis`]
  - Schwannoma: VEMP ausente con oído medio sano [`schwannoma`]
  - Infarto de la AICA [`infarto_aica`]
  - Vía ósea del VEMP en la conductiva [`otoesclerosis`]

## Parte VIII — Casos integradores
Los diez pacientes de práctica (33-42) otra vez, sin título ni pistas: la ficha
de estudio como la ve el alumno, y la resolución al final. Cada resolución remite
al capítulo donde está su técnica.

## Apéndices
- A. Tablas normativas del ABR y la ECochG por población (las citas, en los caps. 11, 12, 9)
- B. Clasificaciones: BIAP, timpanogramas, patrones de reflejo, acumetría
- C. Tamizaje: tasas de pase por hora de vida
- D. Glosario
- E. Créditos de imágenes y licencias

---

## La ficha de cada caso

1. **El paciente:** rostro generado + la anamnesis como la redacta la ficha de estudio
2. **Lo que se ve:** otoscopía OD/OI
3. **¿Qué pedirías?:** la batería, antes de mostrarla
4. **Resultados:** figuras de LabSim
5. **Razonamiento:** lo escribe el autor
6. **Diagnóstico y qué sigue**

---

## Lo que no tenemos

### Referencias de técnica
| Cap. | Falta |
|---|---|
| 1 | Técnica de otoscopía |
| 2 | Timpanometría: clasificación (Jerger 1970 / Lidén), normas de volumen, compliancia y gradiente |
| 4 | Normas del umbral del reflejo estapedial; patrones de reflejo de Jerger |
| 5 | Logoaudiometría (SRT, discriminación, PB máx., roll-over); LDL y campo dinámico; listas en español de Chile |
| 6 | OEA: TEOAE, DPOAE y SOAE (técnica y criterios de presencia); acufenometría |
| 7 | Atenuación interaural por transductor; método del plateau (Hood) |
| 8 | Guía de monitoreo de ototoxicidad (ASHA u otra) con criterios de cambio |
| 9 | Fowler y SISI |
| 10 | Audiometría pediátrica: observación conductual y condicionada por juego |
| 11 | Deterioro tonal (Carhart, Rosenberg, Stat) |
| 13 | Microfónica coclear y la prueba de pinzar el tubo |
| 14 | Efecto de la temperatura en el ABR |
| 15 | Fuente clásica del dilema de enmascaramiento |
| 17 | Timpanometría de 1000 Hz; tablas de corrección nHL → eHL |
| 18 | Rechazo de artefactos; artefacto de estímulo; respuesta postauricular |
| 19 | Pérdida no orgánica: Stenger, concordancia SRT-PTA |
| 20 | VEMP: técnica de cVEMP y oVEMP, corrección por EMG, normas |

### Referencias de fisiología
No hay ninguna en el sistema, y hace falta una por capítulo:

- Oído externo: resonancia del conducto y cerumen
- Trompa de Eustaquio
- Adaptación de impedancias del oído medio
- Conducción ósea
- Arco reflejo
- Muesca de Carhart
- Tonotopía y codificación del habla
- Células ciliadas externas y electromotilidad
- Atenuación interaural
- Vulnerabilidad de la base de la cóclea
- Endolinfa y potencial endococlear
- Potasio y conexina 26
- Adaptación neural
- Generadores del ABR
- Sincronía neural y sinapsis de la célula ciliada interna
- Maduración de la vía
- Oído del recién nacido
- EEG de fondo y promediación
- Vía vestíbulo-cólica

Un tratado o dos que cubran casi todo resolverían la mayoría, por ejemplo Pickles, Møller o un handbook de audiología clínica.

### Imágenes
- **Otoscopías sin fuente libre:** glomus, hemotímpano (barotrauma, fracturas), atresia o estenosis del conducto, carcinoma del conducto, membrana retraída
- **Ilustraciones de anatomía y fisiología:** no hay ninguna (oído externo, medio e interno, órgano de Corti, vía auditiva, vía del VEMP)
- **Fotos de técnica:** otoscopía, posición del vibrador óseo, montaje de electrodos del ABR, ECochG y VEMP, sonda de timpanometría. Se pueden sacar en el laboratorio.

### Del motor (no es para buscar, es trabajo de código)
- TODO 40: ósea supranormal (Pendred)
- TODO 41-42: progresión y asimetría (CMV, ototoxicidad seriada, autoinmune)
- TODO 45: eje no orgánico (simulación)
- Generar casos con semilla fuera del navegador
- `CaseCharts` a SVG/PNG para las figuras del libro
