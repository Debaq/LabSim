# La pieza del laboratorio de sueño

Lo que el técnico ve desde la sala de control en la polisomnografía: la pieza por
la ventanilla y la cámara infrarroja del techo. Son fotos, no 3D (el build no usa
OpenGL), como la cabeza de `scripts/cabeza_electrodos`. Resultado en
`resources/psg_pieza/`; lo muestra `src/nasal/pieza_vista.py`.

- **Paciente:** MakeHuman 1.3 (`~/Escritorio/Proyectos/makehuman-lotes`), con
  `makehuman.json`: hombre de unos 50 años con sobrepeso, piel, polera, pelo y
  expresiones (dormido, despierto, boca abierta).
- **Pieza, cama, frazada y montaje:** los arma `gen_pieza.py` en Blender (5.2).
  - La frazada es tela simulada sobre el cuerpo ya acostado.
  - Las fajas siguen el contorno del tronco y se deforman con él.
  - La cánula, los electrodos de EEG, mastoides, EOG y mentón, y el oxímetro van
    pegados a la piel.
  - Los cables llegan al cabezal del velador.
- **Respiración:** shape keys `torax` y `abdomen` (separadas, para poder desfasarlas
  en la apnea obstructiva) en el cuerpo, la polera y las fajas.
- **Estados:** 3 poses, cada una con:
  - dormido: grilla de 4 niveles del tórax × 4 del abdomen, para la respiración en fase, la paradoja de
    la apnea obstructiva y el quedarse quieto de la central;
  - despierto (ojos abiertos y la cabeza algo girada): en fase;
  - roncando (boca abierta): en fase.
  LabSim funde los vecinos según `sueno.respiracion_en`, lo mismo que dibujan las bandas.
- **Vistas:** la ventanilla desde 5 puntos corridos a lo largo del vidrio (la
  sensación de profundidad al mover el mouse) y la cámara del techo.

## Generar

```bash
# 1. MakeHuman (solo la primera vez o si cambia makehuman.json; deja ~/.cache/labsim/psg_mh)
python3 - <<'EOF'
import json, os, pathlib
d = json.loads(pathlib.Path('scripts/psg_pieza/makehuman.json').read_text())
d['salida'] = os.path.expanduser(d['salida'])
pathlib.Path('/tmp/psg_mh.json').write_text(json.dumps(d))
EOF
python3 ~/Escritorio/Proyectos/makehuman-lotes/lotes.py /tmp/psg_mh.json

# 2. Blender: todos los cuadros (~1 h, 432 PNG)
blender -b -P scripts/psg_pieza/gen_pieza.py -- todo /tmp/psg_todo

# 3. Paquete para LabSim
python3 scripts/psg_pieza/empaquetar.py /tmp/psg_todo

# Los ronquidos (grabaciones CC0 de Freesound, recortadas por inspiración y por sexo):
# resources/audio/psg/<sexo>/<id>_<n>.wav y FUENTES.md
python3 scripts/psg_pieza/ronquidos.py
```

Para revisar algo suelto: `blender -b -P scripts/psg_pieza/gen_pieza.py -- muestra
<carpeta> izquierda despierto` (con `PSG_CARA=1` agrega un primer plano de la cara).

## Pendiente

- El montaje se ve siempre completo, aunque el alumno no haya puesto algún
  sensor (habría que renderizar cada sensor como capa aparte).
- El despertar se ve solo como respiraciones hondas con ronquido (las de recuperación); no hay
  movimiento del cuerpo.
