# OSCE de demostración (ETMP196, 2026-11-26)

Tres OSCE de demo (bloques 9:00, 10:00 y 14:00 con 5, 5 y 4 alumnos), en
cadena de a 2, estaciones de 6 min y cambio de 1 min para que cada bloque
quepa en una hora (8 turnos con 5 alumnos: ~55 min).

Cómo se armaron, sin poder bajar la base de prod (150 MB, la consola corta en 4 MB):
1. Una copia local del backend con una base vacía de OSCE (curso con id 2
   creado a mano, como en prod).
2. `php armar_demo.php` crea todo con el código del sistema (Osce::crear,
   OscePauta::cargarBase, OscePreguntas, OsceApp::guardarTarea).
3. `python3 exportar.py labsim.sqlite demo_osce.sql` pasa las filas de las tablas
   osce* a INSERT con sus ids.
4. `python3 scripts/consola.py script demo_osce.sql`, en una transacción
   (las tablas osce* estaban vacías en prod; respaldo previo con `consola.py backup`).

Pacientes: adultos normales 110/115/133 (configuración y marcaje de PEATC,
ECochG y cVEMP); latencias normales 157/158/159 (P300, MLR, CAEP); lactantes
102/104/26 (protocolo); caso integrado PEATC + ECochG con hidrops de un lado
38/119/136 (conclusión, con su conclusión esperada).
