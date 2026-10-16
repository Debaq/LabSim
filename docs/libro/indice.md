# Evaluación y rehabilitación en otorrinolaringología — índice propuesto

*Un libro de casos clínicos.* Título elegido el 2026-10-15: un solo libro que
crece por secciones; LabSim, trainHIT y labyrinthus3d son simuladores de apoyo.

Borrador del índice (2026-10-15). Libro gratuito; licencia propuesta
**CC BY-NC-SA 4.0** (la obliga OtitisMediaKPJ, la única fuente con colesteatoma
y efusión).

El libro es la nueva versión del protocolo técnico de ORL, con sentido
pedagógico. Tiene dos tipos de capítulo, todos autónomos (se pueden leer
sueltos) y con sus referencias al final (no hay bibliografía general):

**Caja de herramientas (H1-H14): cómo se hace cada examen.** Una técnica por
capítulo, con la misma secuencia:

1. **Para qué sirve** — qué pregunta clínica responde
2. **Fundamento** — la fisiología justa para entender por qué se hace así
3. **Antes de empezar** — equipo, calibración, preparación del paciente
4. **Paso a paso** — el procedimiento, con el porqué de cada paso
5. **Cómo se informa** — criterios, valores de referencia, ejemplo de informe
6. **Errores frecuentes** — los que se ven en la práctica y en LabSim
7. **En LabSim** — cómo se practica en el simulador
8. **Referencias**

**Capítulos clínicos (1-20): cómo se razona.** Parten de un problema:

1. **Técnica en foco** — qué mirar de la técnica para ESTE problema (el cómo
   se hace está en la herramienta indicada con →)
2. **Fisiología** — lo que hay que entender del mecanismo
3. **Patología** — los cuadros del capítulo
4. **Razonamiento** — cómo se llega del resultado al diagnóstico
5. **Casos** — ficha, "¿qué pedirías?", resultados relatados con globos,
   razonamiento y diagnóstico. Cada caso sale de los generadores de la app
6. **Para cerrar** y **Referencias**

Antes de todo va **Bases**: B1 anatomía, B2 fisiología auditiva y vestibular (a cargo de una colega), B3 histología y B4 física.

Todos llevan recuadros: objetivos, ayuda memoria, ¿sabías que?, ojo clínico,
preguntas abiertas y comentarios. Las ilustraciones (dibujos tipo BioRender)
se marcan en el texto con `![qué muestra](ilustraciones/archivo.png)`; hasta
que existe el archivo sale un recuadro "ilustración pendiente". Cada capítulo tiene su generador
(`capitulos/NN-*.py`: casos y figuras) y su texto (`capitulos/NN-*.md`).

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

## Bases

Los bloques de **Fisiología** de los capítulos clínicos y el **Fundamento** de las herramientas quedan cortos y remiten acá.

### B1. Anatomía
Oído externo (pabellón, conducto y sus dos tercios), oído medio (membrana, cadena, músculos, trompa, mastoides), oído interno (cóclea, vestíbulo, canales semicirculares), VIII par y vía auditiva y vestibular central; nariz, fosas nasales y senos paranasales. Ilustraciones de bancos libres (Servier, OpenStax), no IA.

### B2. Fisiología auditiva y vestibular *(la escribe una colega; se recibe más adelante)*
Transmisión del oído medio, conducción ósea, mecánica coclear y tonotopía, amplificador coclear, transducción y sinapsis, potenciales cocleares, vía auditiva central; reflejo estapedial; fisiología vestibular (aceleraciones, reflejo vestíbulo-ocular y vestíbulo-espinal, compensación); fisiología nasal (ciclo nasal, resistencia al flujo).

### B3. Histología
Órgano de Corti (células ciliadas internas y externas, células de sostén, membrana tectoria), estría vascular y homeostasis del potasio, ganglio espiral, máculas y crestas ampulares, epitelio de la mucosa del oído medio y respiratorio nasal; qué tejido daña cada cuadro.

### B4. Física
El sonido: onda, frecuencia, período, longitud de onda, intensidad y presión; decibeles y sus referencias (SPL, HL, SL, nHL, eHL); tonos, ruidos y filtros; impedancia y admitancia (rigidez, masa, resistencia); resonancia; señal, ruido y promediación; acústica de la sala y del campo libre; flujo y resistencia de la vía aérea nasal.

## Caja de herramientas

### H1. Anamnesis, otoscopía y lavado de oídos
Entrevista audiológica (motivo, evolución, antecedentes, fármacos, ruido, acúfeno); otoscopía (técnica, hallazgos, cuándo no seguir); lavado de oídos (indicaciones y contraindicaciones). Refs: `tecnica_a.md` §1.

### H2. Acumetría
Rinne y Weber con diapasón: técnica, lectura, falsos negativos (✓ BSA2022RW, KELLY2018, UNGAR2021, STANK1979).

### H3. Audiometría tonal
Vía aérea y ósea: orden, método ascendente, criterio de umbral, colocación del vibrador, grados y símbolos (✓ ISO2010, ASHA2005, BSA2018, S02, S03); audiometría de screening y ocupacional (✓ ISP2018, ISP2012, PREXOR); alta frecuencia (`tecnica_a.md` §6).

### H4. Enmascaramiento
Por qué se cruza el sonido (atenuación interaural por transductor), cuándo enmascarar en aérea, ósea y logoaudiometría, cuánto ruido, y las técnicas: plateau de Hood, fórmulas de nivel mínimo y máximo, sobreenmascaramiento, efecto de oclusión, el dilema (✓ BSA2018, NTP285; `tecnica_b.md` §3).

### H5. Logoaudiometría y campo dinámico
SRT, umbral de detección, discriminación, PB máx., roll-over, listas en español de Chile; LDL y campo dinámico (`tecnica_a.md` §5).

### H6. Pruebas supraliminares
Reclutamiento (Fowler, SISI), deterioro tonal (Carhart, Rosenberg, STAT) y pruebas de pérdida no orgánica (Stenger, concordancia SRT-PTA) (`tecnica_b.md` §4, §5, §10).

### H7. Impedanciometría
Timpanometría de 226 y 1000 Hz (tipos, volumen, compliancia, gradiente), reflejo estapedial (umbral, patrones, ON-OFF, Metz, deterioro) y función tubaria (`tecnica_a.md` §2, §3, §8; ✓ GSI-AR, WILLIAMS1975, SMITH2015).

### H8. Audiometría pediátrica y campo libre
Observación conductual, VRA, audiometría por juego, campo libre (`tecnica_a.md` §7).

### H9. Emisiones otoacústicas
TEOAE, DPOAE y SOAE: sonda, criterios de presencia, tamizaje y clínica (`tecnica_b.md` §1; ✓ N01-N11).

### H10. Potenciales evocados auditivos de tronco
Montaje, estímulos, filtros y promediación; búsqueda de umbral (click y tone burst, nHL→eHL), PEAT neurootológico, vía ósea, AABR de tamizaje, artefactos (✓ F01-F27, A01-A06; `tecnica_b.md` §6-§9).

### H11. Electrococleografía
Electrodos, protocolo, PS/PA y razón de áreas; test de glicerol (✓ E01-E07).

### H12. VEMP
cVEMP y oVEMP: montaje, estímulo, corrección por EMG, umbral, asimetría (`tecnica_b.md` §11).

### H13. Potenciales de estado estable *(propuesto, del protocolo)*
ASSR: estimación de umbral por frecuencia.

### H14. Procesamiento auditivo central
Cuándo sospecharlo y a quién evaluar; batería: patrones de frecuencia y duración (FPT, DPS), resolución temporal (GIN, gap detection), escucha dicótica (dígitos dicóticos), interacción binaural (MLD), habla en ruido (HINT, SinB, Matrix); umbrales diferenciales; interpretación por edad e informe. Simulador de apoyo: AudioPAC (software propio, MIT, doi:10.5281/zenodo.19663724), también para las capturas.

**Equilibrio**

### H15. Examen vestibular con lentes de Frenzel y videonistagmografía *(del protocolo)*
Anamnesis del mareo; nistagmo espontáneo y evocado por la mirada con lentes de +20 dioptrías; videonistagmografía: pruebas oculomotoras (sacadas, seguimiento, optocinético) y posicionales. Simuladores: trainHIT y labyrinthus3d.

### H16. Prueba calórica *(del protocolo)*
Calórica mínima y bilateral con videonistagmografía: irrigación, velocidad de la fase lenta, paresia del canal y preponderancia direccional (fórmula de Jongkees), fijación visual.

### H17. Video head impulse test (vHIT) *(del protocolo)*
Impulsos cefálicos por canal: ganancia del reflejo vestíbulo-ocular, sacadas encubiertas y manifiestas; comparación con la calórica.

### H18. Maniobras de diagnóstico y reposición *(del protocolo)*
VPPB: Dix-Hallpike y prueba de giro supino, lectura del nistagmo por canal; reposición (Epley, Semont, Lempert/barbacoa) y liberación de partículas.

### H19. Rehabilitación vestibular *(del protocolo)*
Evaluación funcional (DHI, pruebas de equilibrio), ejercicios de adaptación, sustitución y habituación, progresión, control y alta.

**Rehabilitación aural**

### H20. Prueba de audífonos *(del protocolo)*
Candidatura, selección y prueba del audífono: ganancia funcional en campo libre, discriminación con y sin audífono, molde y ventilación, entrega y control.

### H21. Revisión y medición electroacústica del audífono *(del protocolo)*
Revisión visoauditiva (molde, tubo, pila, micrófono, retroalimentación) y medición en acoplador: ganancia, salida máxima, distorsión y ruido interno.

**Salud ocupacional**

### H22. Audiometría ocupacional y vigilancia del ruido
Audiometría de screening y de operativo, evaluación de trabajadores expuestos a ruido (PREXOR, guía del ISP), criterios de daño y de derivación, protección auditiva; la parte médico-legal (SUSESO).

**Nariz**

### H23. Anamnesis rinológica y rinoscopía *(del protocolo)*
Motivo de consulta nasal, síntomas y antecedentes; rinoscopía anterior.

### H24. Rinomanometría anterior *(del protocolo)*
Resistencia nasal al flujo: técnica, curvas presión-flujo, prueba con vasoconstrictor e informe.

### H25. Rinometría acústica *(del protocolo)*
Áreas de sección transversal de la fosa nasal por reflexión acústica: técnica, curva, áreas mínimas y volumen, prueba con vasoconstrictor.

## Parte I — El oído que transmite

### 1. Antes de medir: el conducto
- **Técnica en foco** (→ H1, H2): otoscopía (✗) · acumetría, Rinne y Weber (✓ BSA2022RW, KELLY2018, UNGAR2021, STANK1979)
- **Fisiología:** oído externo, resonancia del conducto, migración del epitelio y cerumen (✗)
- **Casos:**
  - Tapón de cerumen [`tapon_cerumen`] — V/B
  - Cuerpo extraño [`cuerpo_extrano_cae`] — B (3 fotos)
  - Otitis externa difusa [`otitis_externa`] — B
  - Estenosis / atresia congénita [`estenosis_atresia_cae`] — ✗
  - Carcinoma del conducto [`carcinoma_cae`] — ✗

### 2. Líquido detrás del tímpano
- **Técnica en foco** (→ H7): timpanometría de 226 Hz: tipos, volumen, compliancia, gradiente (✗); función tubaria (✓ WILLIAMS1975, SMITH2015, LU2026, LEE2026)
- **Fisiología:** trompa de Eustaquio y ventilación del oído medio (✗)
- **Casos:**
  - ★35 Benjamín, 5 años, resfríos todo el invierno [`otitis_media`] — K
  - Otitis media aguda [`otitis_media_aguda`] — B/K
  - Disfunción tubaria con presión negativa [`disfuncion_tubaria`] — ✗
  - Barotrauma [`barotrauma`] — ✗

### 3. Membrana y cadena
- **Técnica en foco** (→ H3): audiometría tonal por vía aérea y ósea (✓ ISO2010, ISO1989, ASHA2005, BSA2018, ISP2018, NTP285); grados (✓ S02 BIAP)
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
- **Técnica en foco** (→ H7): reflejo estapedial: umbral, ipsi y contra, ON-OFF (✓ GSI-AR, DEBRUYNE1992, CAMICAS1992, COLLETTI1987); normas del umbral del reflejo y patrones de Jerger (✗)
- **Fisiología:** arco reflejo estapedial (✗); muesca de Carhart (✗ Carhart 1950)
- **Casos:**
  - ★34 Secretaria de notaría, 34 años [`otoesclerosis`] — N
  - Fijación congénita del estribo [`fijacion_congenita_estribo`] — N
  - Enfermedad de Paget [`paget`] — N

## Parte II — La cóclea

### 5. Envejecer oyendo
- **Técnica en foco** (→ H5): logoaudiometría: SRT, discriminación, PB máx., roll-over, curva sombra (✗); LDL y campo dinámico (✗)
- **Fisiología:** tonotopía y codificación del habla (✗); umbrales por edad (✓ S01 ISO 7029)
- **Casos:**
  - ★36 Carpintero jubilado, 74 años, "yo escucho bien" [`presbiacusia`]
  - Diabetes / insuficiencia renal [`metabolica`]

### 6. Ruido
- **Técnica en foco** (→ H9, H3): emisiones otoacústicas TEOAE, DPOAE y SOAE (✗); audiometría ocupacional (✓ ISP2018, ISP2012, PREXOR); acufenometría (✗)
- **Fisiología:** células ciliadas externas, amplificador coclear, electromotilidad (✗)
- **Casos:**
  - ★33 Electricista de 23 años antes de entrar a la mina: la línea de base [`normal`]
  - ★37 Operador de chancador, 22 años de turnos [`nihl_cronica`]
  - Trauma acústico agudo [`trauma_acustico_agudo`] · muesca en 4 kHz [`muesca_4k`]

### 7. De un día para otro
- **Técnica en foco** (→ H4): enmascaramiento: cuándo y cuánto, atenuación interaural por transductor, plateau, efecto de oclusión (✓ BSA2018, NTP285; ✗ atenuación interaural de inserto/supraaural/vibrador, plateau de Hood)
- **Fisiología:** atenuación interaural y curva sombra (✗)
- **Casos:**
  - Hipoacusia súbita [`subita`]
  - Laberintitis [`laberintitis`]
  - Conmoción laberíntica [`conmocion_laberintica`]
  - ★42 Estudiante de 22 años, cófosis tras paperas [`parotiditis`]
  - Autoinmune / otosífilis [`autoinmune`] (TODO 42)

### 8. Lo que deja un tratamiento
- **Técnica en foco** (→ H3): monitoreo de ototoxicidad: audiometría de alta frecuencia y seriada, criterios de cambio (✗)
- **Fisiología:** por qué la base de la cóclea cae primero (✗)
- **Casos:**
  - Ototoxicidad por cisplatino o aminoglucósidos [`ototoxica`] (TODO 41)
  - Salicilatos y quinina: la que se recupera [`salicilatos`]
  - Post-radioterapia de cabeza y cuello [`post_radioterapia`]

### 9. Hidrops
- **Técnica en foco** (→ H11, H6): electrococleografía: SP/AP, área, electrodo (✓ E01-E07); reclutamiento: Fowler y SISI (✗)
- **Fisiología:** endolinfa, potencial endococlear, potencial de sumación (✗)
- **Casos:**
  - ★38 Profesora de lenguaje, primera crisis hace un año [`meniere`]
  - Hidrops retardado contralateral [`hidrops_retardado`]

### 10. Lo que viene en la familia
- **Técnica en foco** (→ H8): audiometría en el niño: conductual, condicionada por juego (✗)
- **Fisiología:** homeostasis del potasio en la cóclea y conexina 26; estría vascular (✗)
- **Casos:**
  - GJB2 [`gjb2`] · Waardenburg [`waardenburg`] · Usher 2 [`usher`]
  - Alport [`alport`] · Jervell-Lange-Nielsen [`jervell_lange_nielsen`] · Stickler [`stickler`]
  - Pendred / acueducto vestibular dilatado [`pendred`] (TODO 40)

## Parte III — Más allá de la cóclea

### 11. Asimetría que no cierra
- **Técnica en foco** (→ H6, H7, H10):
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
- **Técnica en foco** (→ H10): ABR: interpicos, diferencia interaural, efecto de la tasa (✓ F13, F10, F16)
- **Fisiología:** generadores de las ondas I-VII y vía auditiva central (✗ Møller)
- **Casos:**
  - Esclerosis múltiple [`esclerosis_multiple`]
  - Infarto pontino [`infarto_pontino`] · Infarto de la AICA [`infarto_aica`]
  - Glioma [`glioma_tronco`] · Chiari [`chiari_hic`] · HIC idiopática [`hic_idiopatica`]
  - Siderosis [`siderosis`] · TEC de tronco [`tec_tronco`]

### 13. Oye pero no entiende
- **Técnica en foco** (→ H10, H9): microfónica coclear: polaridad (✓ F27), pinzar el tubo (✗); OEA + ABR juntos (✗)
- **Fisiología:** sincronía neural, sinapsis de la célula ciliada interna (✗)
- **Casos:**
  - ★40 Escolar de 15 años, "escucho que me hablan pero no entiendo" [`neuropatia`]
  - Neuropatía hereditaria [`neuropatia_hereditaria`]
  - Kernícterus [`kernicterus`] · Leucodistrofia [`leucodistrofia`]

### 14. Lo que mueve el ABR sin ser el oído
- **Técnica en foco** (→ H10): factores del sujeto: edad, sexo, temperatura, fármacos (✓ F09, F10, F20; ✗ temperatura)
- **Fisiología:** mielinización y maduración de la vía (✓ F19, F11; ✗ revisión de fisiología)
- **Casos:**
  - Hipotiroidismo [`toxico_metabolico`]
  - Hipotermia / depresores [`hipotermia_farmacos`]
  - Coma: bloqueo proximal [`bloqueo_proximal`]
  - Prematuro [`prematuro`]

## Parte IV — Mixtas y complicadas

### 15. Cuando también cae la ósea
- **Técnica en foco** (→ H4, H10): el dilema de enmascaramiento (✓ BSA2018; ✗ fuente clásica del dilema); ABR por vía ósea (✓ A02, A06, F18)
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
- **Técnica en foco** (→ H9, H10): TEOAE y AABR de tamizaje, protocolo y momento (✓ N01-N11, JCIH 2019)
- **Fisiología:** oído del recién nacido: vérnix, mesénquima, transitorio de las primeras horas (✓ N08; ✗ fuente de fisiología)
- **Casos:**
  - Recién nacido sano a las 12 h y a las 48 h [`normal` + `efusion_neonatal`]
  - AABR que pasa con TEOAE que refiere

### 17. El lactante que se estudia
- **Técnica en foco** (→ H7, H10):
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
- **Técnica en foco** (→ H10): promediación, FSP y ruido residual (✓ A01 Elberling y Don); rechazo de artefactos (✗); artefacto de estímulo, respuesta postauricular, falsa V (✗)
- **Fisiología:** el EEG de fondo, el músculo, y por qué el promedio mejora con la raíz de los barridos (✗)
- **Casos:**
  - Falsa onda V: los subpromedios A/B la delatan
  - Artefacto de estímulo: se confirma pinzando el tubo
  - Respuesta postauricular a 13 ms: replica en A/B y no es respuesta
  - Paciente inquieto: rechazo, barridos perdidos
  - Onda I ausente por el montaje: el falso retrococlear

### 19. El paciente que no calza
- **Técnica en foco** (→ H6, H5): pérdida no orgánica: SRT vs. PTA, Stenger, ABR mejor que el audiograma (✗)
- **Fisiología:** no aplica; acá el bloque es la conducta del paciente (✗ fuente)
- **Casos:**
  - Simulación (a mano; TODO 45)
  - El acompañante que contesta por el paciente

## Parte VII — Cuando también hay vértigo

### 20. VEMP
- **Técnica en foco** (→ H12): cVEMP y oVEMP: montaje, estímulo, corrección por EMG, umbral (✗ excepto Murofushi 2001, dentro de patologías)
- **Fisiología:** vía vestíbulo-cólica y vestíbulo-ocular, sáculo y utrículo (✗)
- **Casos:**
  - Ménière: VEMP sacular alterado [`meniere`]
  - Laberintitis vs. neuritis [`laberintitis`]
  - Schwannoma: VEMP ausente con oído medio sano [`schwannoma`]
  - Infarto de la AICA [`infarto_aica`]
  - Vía ósea del VEMP en la conductiva [`otoesclerosis`]

## Parte VIII — El equilibrio

### 21. Vértigo agudo
- **Técnica en foco** (→ H15, H17): nistagmo espontáneo con Frenzel, HINTS, vHIT al lado de la cama
- **Fisiología:** reflejo vestíbulo-ocular, asimetría de tono y compensación
- **Casos:**
  - Neuritis vestibular
  - Laberintitis
  - Vértigo agudo central que imita una neuritis

### 22. Gira al acostarse
- **Técnica en foco** (→ H18): Dix-Hallpike, giro supino, lectura del nistagmo por canal y maniobras de reposición
- **Fisiología:** canalitiasis y cupulolitiasis
- **Casos:**
  - VPPB del canal posterior
  - VPPB del canal horizontal (geotrópico y ageotrópico)

### 23. Crisis que vuelven
- **Técnica en foco** (→ H15, H16, H12): VNG entre crisis, calórica, VEMP y audiometría seriada
- **Fisiología:** hidrops y migraña vestibular
- **Casos:**
  - Ménière en etapa avanzada
  - Migraña vestibular

### 24. Cuando fallan los dos lados
- **Técnica en foco** (→ H16, H17): calórica y vHIT bilaterales
- **Fisiología:** oscilopsia y pérdida del reflejo vestíbulo-ocular
- **Casos:**
  - Hipofunción vestibular bilateral por ototóxicos

### 25. Lo que viene de arriba
- **Técnica en foco** (→ H15): oculomotor (sacadas, seguimiento, optocinético) y nistagmo central
- **Fisiología:** cerebelo y vías vestibulares centrales
- **Casos:**
  - Vértigo de origen central (cerebelo, tronco)

### 26. Una tercera ventana
- **Técnica en foco** (→ H12, H3): VEMP de umbral bajo y gap con ósea supranormal
- **Fisiología:** tercera ventana del laberinto
- **Casos:**
  - Dehiscencia del canal semicircular superior

### 27. Mareo que no se va
- **Técnica en foco** (→ H19): evaluación funcional y cuestionarios
- **Fisiología:** compensación central y dependencia visual
- **Casos:**
  - Mareo postural perceptual persistente (PPPD)

## Parte IX — Rehabilitación auditiva

### 28. El primer audífono
- **Técnica en foco** (→ H20, H21, H5): candidatura, prueba, ganancia funcional y control
- **Fisiología:** campo dinámico y reclutamiento en el ajuste
- **Casos:**
  - Presbiacusia: el primer audífono
  - Hipoacusia unilateral: CROS o audífono

### 29. Cuando el audífono no alcanza
- **Técnica en foco** (→ H20, H5): discriminación con audífono y criterios de derivación a implante
- **Fisiología:** estimulación eléctrica del nervio
- **Casos:**
  - Candidato a implante coclear
  - Prótesis de conducción ósea en una conductiva que no se opera

### 30. Oír y no entender
- **Técnica en foco** (→ H14): batería de procesamiento central y entrenamiento auditivo
- **Fisiología:** plasticidad de la vía auditiva central
- **Casos:**
  - Niño con trastorno del procesamiento auditivo
  - Adulto mayor que no entiende en ruido con audiograma leve

## Parte X — Rehabilitación vestibular

### 31. Compensar una neuritis
- **Técnica en foco** (→ H19): ejercicios de adaptación y progresión
- **Fisiología:** adaptación del reflejo vestíbulo-ocular
- **Casos:**
  - Hipofunción unilateral después de una neuritis

### 32. Volver a caminar sin miedo
- **Técnica en foco** (→ H19): equilibrio, marcha y prevención de caídas
- **Fisiología:** sustitución visual y somatosensorial
- **Casos:**
  - Adulto mayor con caídas y mareo multifactorial

## Parte XI — Salud ocupacional

### 33. El trabajador expuesto a ruido
- **Técnica en foco** (→ H22): audiometría de vigilancia, comparación con la basal y derivación
- **Fisiología:** daño por ruido y desplazamiento temporal del umbral
- **Casos:**
  - Trabajador en vigilancia con cambio significativo del umbral
  - Trabajador nuevo con audiometría de ingreso alterada

### 34. El caso médico-legal
- **Técnica en foco** (→ H22, H6): evaluación de la pérdida no orgánica y del grado de daño
- **Fisiología:** lo que el ruido no explica
- **Casos:**
  - Exageración de la pérdida en una evaluación laboral

## Parte XII — La nariz

### 35. Nariz tapada
- **Técnica en foco** (→ H23, H24, H25): rinoscopía, rinomanometría y rinometría acústica
- **Fisiología:** válvula nasal y resistencia al flujo
- **Casos:**
  - Desviación septal
  - Colapso de la válvula nasal

### 36. Rinitis y vasoconstrictor
- **Técnica en foco** (→ H24, H25): prueba con vasoconstrictor
- **Fisiología:** tejido eréctil de los cornetes y ciclo nasal
- **Casos:**
  - Rinitis alérgica
  - Hipertrofia de cornetes

## Parte XIII — Casos integradores
Los diez pacientes de práctica (33-42) otra vez, sin título ni pistas: la ficha
de estudio como la ve el alumno, y la resolución al final. Cada resolución remite
al capítulo donde está su técnica.

## Secciones de las próximas ediciones

Un solo libro que crece. Esta edición escribe la sección de **audición**
(Bases, Caja de herramientas H1-H14 y Partes I-VII). Las demás ya tienen su
lugar reservado en esqueleto, para que el libro crezca sin reordenarse:
equilibrio (H15-H19, Parte VIII), rehabilitación auditiva (H20-H21,
Parte IX), rehabilitación vestibular (Parte X), salud ocupacional (H22,
Parte XI) y nariz (H23-H25, Parte XII). Plan y fuentes en
`investigacion/inventario_vestibular_nasal.md`. Simuladores: trainHIT y
labyrinthus3d para lo vestibular (LabSim no se expande ahí), AudioPAC para
el procesamiento central; para la nariz todavía no hay.

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

## Investigación hecha (2026-10-15)

Las referencias marcadas ✗ arriba se buscaron y están en `docs/libro/investigacion/`,
cada artículo verificado con DOI o PMID en Crossref/PubMed:

| Archivo | Qué trae |
|---|---|
| `tecnica_a.md` | 59 refs: otoscopía, timpanometría 226 y 1000 Hz, reflejo, Carhart 1950, logoaudiometría (incluye listas chilenas: Burdiles 2024, Cañete 2024), LDL, ototoxicidad, audiometría pediátrica |
| `tecnica_b.md` | 96 refs: OEA, acufenometría, enmascaramiento (Hood, Naunton, atenuación interaural), Fowler, SISI, deterioro tonal, microfónica y tubo pinzado, temperatura, nHL→eHL, artefactos y PAM, no orgánica, VEMP |
| `fisiologia.md` | los 19 temas con 2-3 refs cada uno + textos generales (Pickles, Møller, Gelfand, Katz, Salesa, Suárez/Gil-Carcedo) |
| `imagenes.md` | otoscopías de glomus, hemotímpano, estenosis, carcinoma y retracción en artículos CC BY; anatomía (Servier, OpenStax, Gray, Blausen); fotos de técnica |

Ojo con CC BY-SA en imágenes: se pueden usar solo tal cual; para traducir o
rotular, preferir CC BY o dominio público.

## Le toca al autor

### Referencias que no están indexadas
- Listas chilenas originales: Rosenblüt y de Cruz (Rev Otorrinolaringol Chile, 1961 o 1962: las fuentes no coinciden) y Farfán, Solís y Palacio 2001 (Rev Chil Tecnol Méd). Están en papel o en la biblioteca.
- Tato y cols., bisílabos (Argentina, alrededor de 1948): está en el libro de Tato.
- Rosenberg 1958/1969 (deterioro tonal): fue congreso y folleto. Mientras tanto se cita Olsen y Noffsinger 1974.
- Ventry y Chaiklin 1965 y Chaiklin 1967 (J Aud Res, sin DOI): falta confirmar volumen y páginas.
- Stenger original (1900/1907).
- Páginas de Elpern y Naunton 1963; parte II de Buus 1982 (SISI); capítulo de enmascaramiento del Katz 7.ª ed. (número y autor).
- El texto de fisiología en español que usan tus alumnos, si no es Salesa.

### Imágenes
- Hemotímpano postraumático. Las fotos libres que hay son de hemotímpano espontáneo.
- Otoscopía de atresia congénita. Solo hay vista externa y TC.
- Carcinoma del conducto en etapa temprana, el que simula otitis externa.
- Serie de Sadé graduada (la publicada es ND) y serie de glomus por clase.
- Fotos de técnica: vibrador óseo en audiometría tonal, TIPtrode, sonda de timpanometría y montaje de ABR en adulto. Todas se pueden sacar en el laboratorio.

### Del motor (trabajo de código, no de búsqueda)
- TODO 40: ósea supranormal (Pendred)
- TODO 41-42: progresión y asimetría (CMV, ototoxicidad seriada, autoinmune)
- TODO 45: eje no orgánico (simulación)
- Figuras: motor hecho (`docs/libro/figuras/`): audiograma, logoaudiometría, timpanograma, reflejos, TEOAE, DPOAE, ABR, ECochG y VEMP; casos por cuadro con `armar_casos.sh`
