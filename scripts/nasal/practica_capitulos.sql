-- Los pacientes nasales y de sueño del libro (fichas 151-162, ver
-- scripts/nasal/sql_pacientes.py) en la práctica libre, cada uno en la
-- carpeta de su capítulo, como el resto del libro (scripts/libro/
-- sql_practica.py): las ven todos. Antes estaban en "Nariz (demo interna)",
-- solo para el admin (2026-10-30, a pedido de él); esa carpeta se apaga.
-- Los equipos nasales siguen en 'development': el alumno ve al paciente,
-- pero los equipos solo los abre el admin hasta que se suelten.
-- Se puede volver a correr:
--     python3 scripts/consola.py script scripts/nasal/practica_capitulos.sql
INSERT INTO practice_folders (nombre, orden, created_by)
SELECT n, o, 1 FROM (SELECT 'Cap. 35 · Nariz tapada' n, 35 o UNION ALL SELECT 'Cap. 36 · Rinitis y vasoconstrictor', 36
                     UNION ALL SELECT 'Cap. 37 · Nariz y pulmón', 37 UNION ALL SELECT 'Cap. 38 · El que ronca', 38)
WHERE NOT EXISTS (SELECT 1 FROM practice_folders f WHERE f.nombre = n AND f.active = 1);
INSERT INTO practice_items (folder_id, case_id, procedimiento, show_study_sheet, orden, created_by)
SELECT (SELECT id FROM practice_folders WHERE active = 1 AND nombre = CASE
            WHEN CAST(c.id AS INTEGER) <= 153 THEN 'Cap. 35 · Nariz tapada'
            WHEN CAST(c.id AS INTEGER) <= 156 THEN 'Cap. 36 · Rinitis y vasoconstrictor'
            WHEN CAST(c.id AS INTEGER) <= 158 THEN 'Cap. 37 · Nariz y pulmón'
            ELSE 'Cap. 38 · El que ronca' END),
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
       1,
       CASE WHEN CAST(c.id AS INTEGER) <= 153 THEN CAST(c.id AS INTEGER) - 150
            WHEN CAST(c.id AS INTEGER) <= 156 THEN CAST(c.id AS INTEGER) - 153
            WHEN CAST(c.id AS INTEGER) <= 158 THEN CAST(c.id AS INTEGER) - 156
            ELSE CAST(c.id AS INTEGER) - 158 END,
       1
  FROM cases c WHERE CAST(c.id AS INTEGER) BETWEEN 151 AND 162
ON CONFLICT(folder_id, case_id) DO UPDATE SET orden = excluded.orden,
    procedimiento = excluded.procedimiento, active = 1;
UPDATE practice_folders SET active = 0 WHERE nombre = 'Nariz (demo interna)';
