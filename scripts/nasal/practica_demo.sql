-- Carpeta de práctica "Nariz (demo interna)" con los pacientes nasales del
-- libro (fichas 151-156, ver scripts/nasal/sql_pacientes.py). Solo la ve el
-- admin (practice_folders.solo_admin = 1, ver Practica::lista).
--
-- Cargar DESPUÉS de desplegar Practica.php y api/practica.php y de correr
-- "Aplicar schema" (agrega la columna solo_admin): con el backend viejo la
-- carpeta les aparecería a los alumnos. Se puede volver a correr.
--     python3 scripts/consola.py script scripts/nasal/practica_demo.sql
INSERT INTO practice_folders (nombre, orden, created_by, solo_admin)
SELECT 'Nariz (demo interna)', 900, 1, 1
WHERE NOT EXISTS (SELECT 1 FROM practice_folders WHERE nombre = 'Nariz (demo interna)' AND active = 1);
UPDATE practice_folders SET solo_admin = 1 WHERE nombre = 'Nariz (demo interna)';
INSERT INTO practice_items (folder_id, case_id, procedimiento, show_study_sheet, orden, created_by)
SELECT (SELECT id FROM practice_folders WHERE nombre = 'Nariz (demo interna)' AND active = 1),
       c.id, 'Rinoscopía, rinomanometría anterior y rinometría acústica', 0, CAST(c.id AS INTEGER) - 150, 1
  FROM cases c WHERE CAST(c.id AS INTEGER) BETWEEN 151 AND 156
ON CONFLICT(folder_id, case_id) DO UPDATE SET active = 1;
