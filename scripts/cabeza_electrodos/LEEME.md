# Cabeza giratoria para poner electrodos

La cabeza y los sitios 10-20 / 10-10 de labyrinthus3d, fotografiados desde
muchos ángulos para que LabSim la muestre girando sin 3D (el build no usa
OpenGL, ver `LabSim.spec`). Resultado en `resources/cabeza/`; lo muestra
`core/cabeza_electrodos.py`.

`captura.html` carga `modelos/cabeza.glb` y `js/electrodos.js` de
labyrinthus3d sin tocarlos, apoya los sitios sobre la piel (`apoyaSitios`) y
por cada cuadro manda el WebP (fondo transparente) y dónde cae cada sitio
visible. Gira la cabeza y no la cámara: la luz queda fija.

    S=$(mktemp -d); mkdir -p $S/www $S/out
    cp captura.html $S/www/; cp servidor.py $S/
    ln -s ~/Escritorio/Proyectos/labyrinthus3d/js $S/www/js
    ln -s ~/Escritorio/Proyectos/labyrinthus3d/modelos $S/www/modelos
    python3 $S/servidor.py 8731 &
    chromium --headless=new --no-sandbox --use-angle=swiftshader \
        --enable-unsafe-swiftshader --user-data-dir=$S/perfil \
        "http://127.0.0.1:8731/captura.html?yaw=2&pitch=-20,-10,0,10,20,30,40,50,60"
    # termina cuando aparece $S/out/fin.txt (unos minutos); $S/out/log.txt dice si falló
    python3 empaquetar.py $S/out <commit de labyrinthus3d>

three.js sale de jsdelivr: hace falta red al generar (no al usar LabSim).
Los sitios del cuerpo (ECM, esternón, clavícula, nuca) necesitan la persona
de pie de labyrinthus3d: todavía no van.
