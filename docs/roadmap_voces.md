# Roadmap de voces

Voces sintéticas del paciente y del examinador para la audiometría y la
logoaudiometría. Se generan una vez y quedan como mp3 en `resources/audio/`:
la app no llama a ningún servicio, funciona sin internet.
Actualizado 2026-10-28. Decisiones en `docs/decisiones.md`
(§ Voces sintéticas con Google: plan, § Audios ordenados por carpeta y voces
de niños). TODO 69 y 70.

## Reglas

- **Dónde va cada audio** (anotado también en `audiometria/h_audio.py`):
  - `comandos/<clave>.mp3`: lo que dice el examinador por talkback (`create_command`).
  - `paciente/<voz>/<frase>.mp3`: frases sueltas del paciente (`create_voice`).
  - `logo/estimulos/<palabra>.mp3`: la palabra de la lista (`create_word`).
  - `logo/respuestas/<voz>/<palabra>.mp3`: el paciente la repite
    (`create_word_response`); `none1-3` = no la entendió.
  - `<voz>` = género + número: `feme1`, `male1`, `nino1`, `nina1`.
  - Nombres sin tildes ni ñ (`normalize`): `montana`, `companero`, `avion`.
- **Barato o gratis:** el autor pidió que fuera económico.
- **Generar con** `scripts/voces_edge.py` (lee las palabras de `ListWords.PALABRAS`,
  no rehace las que existen; para rehacer una se borra su mp3).

## Hecho

- [x] Probado Gemini TTS (`gemini-2.5-flash-preview-tts`, voces Puck y Leda con
  "voz de niño chileno de 7 años"): descartado, "valen hongo". Costaba < US$0,001
  por palabra.
- [x] Voces `nino1` y `nina1` con edge-tts para las 124 palabras de las cinco
  listas: `es-CL-LorenzoNeural` +45 Hz y `es-CL-CatalinaNeural` +40 Hz, las dos
  a -45 % (a -15 % y -30 % el autor las encontró rápidas). Silencio de los
  bordes recortado, mp3 96 kbit/s. Quedan mejor que Gemini, pero algunas suenan mal.
- [x] **Voces del paciente completas** (2026-10-30): `feme1` (es-PE-CamilaNeural,
  no Catalina, que es la del examinador), `male1` (es-CL-LorenzoNeural), `nino1`
  y `nina1`, cada una con las 124 palabras, `none1-3` ("No entendí", "¿Qué
  dijo?", "No sé") y las frases de las otras pruebas en `paciente/<voz>/`. Las
  grabadas (`feme1` 50 palabras, `feme2`, `male`) se reemplazaron. La voz la
  elige `h_audio.voz_del_paciente`: niño o niña hasta los 12 años, si no adulto,
  por el sexo del caso. Todo con `scripts/voces_edge.py`, a -17 LUFS.
- [x] **Talkback** (2026-10-30): las 23 instrucciones con una misma voz,
  `es-CL-CatalinaNeural` a -8 % (la grabada era femenina, ~240 Hz), con
  `scripts/voces_comandos.py`. Textos transcritos de las grabaciones (Whisper)
  y corregidos; STAT y Rosemberg escritos nuevos. -21 LUFS, como las grabadas.
- [x] `resources/audio` ordenado por carpeta (antes 291 archivos sueltos con
  prefijo `LP_palacios_`), rutas ajustadas en `h_audio`, `ListWords`,
  `Audiometer` y `test_comandos_voz`.

## Pendiente

- [ ] **Rehacer las que suenan mal.** Falta que el autor diga cuáles. Opciones por
  palabra: otro tono o velocidad, escribirla distinto para que la pronuncie
  mejor (`Pe-lota`, puntuación), o SSML con pausa.
- [ ] **Mejor calidad.** Azure Speech (oficial, plan gratis ~500 mil caracteres al
  mes, pide cuenta): revisar si tiene alguna voz infantil en español.
  edge-tts no es oficial y Microsoft lo puede cortar; los mp3 ya generados no se pierden.
