# Límites del simulador que el libro explicaba (2026-10-19)

El libro de ORL explicaba en su texto, en recuadros, en notas sobre las
figuras y en las guías del docente lo que LabSim todavía no hace o hace
distinto de la clínica. El autor decidió sacarlo del libro ("hoy están,
mañana no") y dejarlo anotado aquí para repararlo. Revisado solo el tomo II
(capítulos 01 a 36); el tomo I se verá aparte.

Entre paréntesis, el capítulo del libro donde aparecía.

## Lo que no coincide con la clínica

- **Dehiscencia del canal superior:** no se simula (26).
- **La vía ósea no baja de 0 dB:** no hay ósea supranormal en la tercera
  ventana (26; ver "Ósea supranormal" en decisiones.md).
- **Reflejo con gap:** el reflejo se apaga desde unos 10 dB de gap en el oído
  de la sonda. En la tercera ventana (Pendred, dehiscencia) el reflejo sigue
  presente con gap. La figura del caso 26.3 (Pendred) muestra un reflejo que
  falta en 500 Hz por esta razón (26; ver "Reflejo presente con gap").
- **VEMP en el acueducto vestibular dilatado:** sale en rango normal; la
  literatura lo espera con umbral bajo y amplitud alta (Zhou y Gopen, 2011)
  (26).
- **Rinne:** se invierte con 15 dB de gap. La BSA (2022) pone el límite entre
  17,5 y 30 dB con 512 Hz; entre estudios va de 13 a 40 dB (Kelly y cols.,
  2018) (01).
- **Forma OFF del reflejo:** en las fuentes revisadas no se encontró una
  descripción del OFF aislado, sin deflexión al comienzo (04). La figura 4.1
  del libro (`ilustraciones/hacer_cap04.py`) la dibuja.
- **Respuesta postauricular (PAMR):** su latencia queda fija y desaparece al
  bajar el nivel. En personas reales el primer pico está entre 12,5 y 15 ms
  según la intensidad y el tono muscular, puede registrarse a menos de 20 dB
  del umbral subjetivo y, al bajar el estímulo, cae en amplitud y se alarga
  en latencia (O'Beirne y Patuzzi, 1999; Purdy y cols., 2005) (18).
- **Bloqueo proximal del VIII:** no atrasa la onda I. En Starr (1976), cuando
  la I estaba, venía con latencia prolongada (14).
- **Prematuro:** la fila normativa se elige por edad cronológica, no
  posconcepcional; el cuadro no guarda las semanas de gestación. La
  literatura describe el alargamiento sobre todo en el III-V y atribuye parte
  del retraso de la I y la V al oído medio (Eggermont y Salamy, 1988) (14).
  Las filas de edad cambian a los 3 meses; para prematuros calza mejor una
  tabla por edad posconcepcional (Rosa y cols., 2014).
- **Ménière:** los casos muestran siempre el típico (ECochG y VEMP alterados).
  En el *Coclear plana* no hay patrón de hidrops en la ECochG ni en el VEMP
  (09, 23).
- **Correcciones nHL → eHL:** más altas que las de protocolos como el de
  Columbia Británica (Hatton y cols., 2022) (17).
- **Impedancias del AABR:** se muestran con límite de 20 kΩ y no frenan la
  prueba; los equipos de tamizaje usan 5 a 12 kΩ (16).
- **Intensidades del VEMP:** no son las del protocolo (20). La vía ósea usa
  una escala propia, de 20 a 75 dB FL, con una ventaja declarada de 15 dB
  sobre el sonido; un vibrador B-71 en la mastoides con 500 Hz es efectivo
  alrededor de los 135 dB pkFL (H12). La figura cap20-oseo decía "100 dB SPL
  (LabSim)" y "70 dB FL (LabSim)"; hoy rotula solo el transductor.
- **Tope del dial de reflejos:** 120 dB SPL; la BSA recomienda no pasar de
  105 dB HL con tonos (105-117 dB SPL según frecuencia y vía) (04).

## Lo que falta

- **Pacientes que cambian:** cada paciente es una foto. No hay audiometría de
  base ni controles seriados, recuperación, fluctuación ni progresión (07, 08,
  23). Tampoco existe la prueba de glicerol.
- **Alta frecuencia:** los casos llegan hasta 8 kHz (08).
- **Desplazamiento temporal del umbral (TTS) y reposo auditivo:** el paciente
  responde con su umbral permanente (33).
- **Audiometría infantil:** el niño responde como un adulto colaborador a
  cualquier edad; a los 8 meses entrega un audiograma que en la vida real no
  se obtendría. La audiometría guarda la curva completa (125 a 8.000 Hz)
  aunque a esa edad se mida de 250 a 4.000 Hz (10). El campo libre no se
  practica.
- **No orgánico:** no se puede cargar un audiograma *informado* distinto del
  verdadero, ni el umbral verdadero de un oído que el paciente dice tener
  sordo; solo existe la casilla Stenger, que supone el oído igual al otro. El
  paciente no se cansa ni se confunde (19, 34).
- **ASSR y cálculo de porcentajes de daño médico-legal** (34).
- **Audífono:** no hay curva con audífono ni discriminación con audífono (28,
  29).
- **Temperatura:** no hay campo de temperatura; la hipotermia está solo en el
  cuadro (14).
- **Migraña vestibular:** no hay cuadro (23).
- **Vestibular y postural:** solo existe el VEMP. No hay nistagmo, VNG,
  calórica, vHIT, examen posicional, posturografía, rehabilitación,
  tensiómetro ni cuestionarios (21-24, 27, 31, 32).
- **Pruebas centrales y habla en ruido** (30).
- **Lavado de oído** (H1; el tomo I todavía lo menciona).

# Tomo I (herramientas)

Desde el 2026-10-19 el tomo I tampoco explica el simulador: las secciones
"En LabSim" salen del libro (quedan solo las preguntas para practicar) y las
preliminares remiten al manual del estudiante. Por capítulo, lo que el libro
explicaba: los límites, para repararlos, y el manejo, para revisar que esté
en `docs/manual/manual-estudiante.md`.

## H3 · Audiometría tonal

- Límites: la alta frecuencia (9-16 kHz) no se practica; los casos llegan a
  8 kHz. El paciente no se distrae ni responde al azar: en su umbral contesta
  siempre.
- Manejo (verificar en el manual): hay que darle la instrucción antes de cada
  prueba; responde según sus umbrales verdaderos y sin enmascarar da la curva
  sombra; topes del vibrador (70 dB de 1 a 4 kHz, menos en graves); efecto de
  oclusión con el fono de enmascaramiento; el indicador de técnica revisa la
  instrucción, el oído de partida, terminar un oído antes del otro, la duración
  del tono, el 10 abajo-5 arriba y si los umbrales coinciden con la audición
  del paciente; la escala BIAP la calcula el equipo.
