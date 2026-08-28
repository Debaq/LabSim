# TODO

## Voces de respuesta logoaudiometria (ListWords.py)

Bug: paciente "no responde" en logoaudiometria. Causa real: `create_word_response`
(lib/h_audio.py) arma el nombre de archivo como
`audio/LP_palacios_r_{sex}{number}_{name}.mp3`, usando `gender`/`id` reales
de la ficha del paciente. Solo existen grabadas las voces `feme1` y `feme2`
(`resources/audio/LP_palacios_r_feme{1,2}_*.mp3`) — no hay ninguna voz `male`
grabada, y ningun otro numero de id tiene voz asociada. Si el archivo no
existe, Qt/ffmpeg falla en silencio ("No existe el fichero o el directorio")
y no suena nada, dando la impresion de que el paciente no responde.

Fix temporal aplicado en `ListWords.la_super` (src/ListWords.py): se fuerza
siempre `gender="feme"` e `id=1`, ignorando el genero/id real del paciente,
para que siempre use una voz que sí existe.

Pendiente:
- [ ] Grabar voces `male1`/`male2` (set completo de palabras + `none1/2/3`).
- [ ] Decidir que representa realmente el numero de voz (¿variante de
      locutor, no el id de la ficha?) y mapear correctamente en vez de
      hardcodear a 1.
- [ ] Quitar el forzado temporal en `ListWords.la_super` una vez resuelto.
