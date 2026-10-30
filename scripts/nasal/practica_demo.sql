-- Carpeta de práctica "Nariz (demo interna)" con los pacientes nasales del
-- libro (fichas 151-162, ver scripts/nasal/sql_pacientes.py): nariz,
-- olfatometría (153), prick (154, 157), espirometría (157, 158) y sueño
-- (159-162, cap. 38). Solo la ve el
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
       c.id, CASE CAST(c.id AS INTEGER)
                 WHEN 153 THEN 'Rinoscopía, rinomanometría anterior, rinometría acústica y olfatometría'
                 WHEN 154 THEN 'Rinoscopía, rinomanometría anterior, rinometría acústica y prick test'
                 WHEN 157 THEN 'Espirometría con prueba broncodilatadora y prick test'
                 WHEN 158 THEN 'Espirometría con prueba broncodilatadora'
                 WHEN 159 THEN 'Poligrafía respiratoria'
                 WHEN 160 THEN 'Poligrafía respiratoria'
                 WHEN 161 THEN 'Polisomnografía'
                 WHEN 162 THEN 'Polisomnografía (la poligrafía previa no alcanzó)'
                 ELSE 'Rinoscopía, rinomanometría anterior y rinometría acústica' END,
       0, CAST(c.id AS INTEGER) - 150, 1
  FROM cases c WHERE CAST(c.id AS INTEGER) BETWEEN 151 AND 162
ON CONFLICT(folder_id, case_id) DO UPDATE SET active = 1, procedimiento = excluded.procedimiento;
