-- Las carpetas del libro adentro de la carpeta del libro (practice_folders.grupo,
-- ver Practica::lista y la agenda de la app). Correr DESPUÉS de desplegar el
-- backend y de "Aplicar schema" (agrega la columna). Se puede volver a correr.
--     python3 scripts/consola.py script scripts/libro/grupo_libro.sql
UPDATE practice_folders SET grupo = 'Evaluación y rehabilitación en otorrinolaringología'
 WHERE active = 1 AND (nombre LIKE 'Cap. %' OR nombre LIKE 'H%· %');
