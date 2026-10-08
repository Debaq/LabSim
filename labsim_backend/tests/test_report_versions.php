<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Db.php';
require_once __DIR__ . '/../src/ReportVersions.php';

/** Lo que muestra la lista de versiones reemplazadas de un informe. */

t_eq(ReportVersions::resumen('{"curvas":{"R1":{},"R2":{}},"conclusion":"Umbral 30 dB"}'),
     '2 curvas · "Umbral 30 dB"', 'Curvas y conclusión');
t_eq(ReportVersions::resumen('{"curvas":{}}'), '0 curvas', 'Informe vacío');
t_eq(ReportVersions::resumen('no es json'), 'datos ilegibles', 'JSON roto');
t_eq(ReportVersions::resumen('{"x":1}'), 'sin curvas ni conclusión', 'Sin nada reconocible');
$largo = ReportVersions::resumen('{"conclusion":"' . str_repeat('á', 100) . '"}');
t_eq(mb_strlen($largo), 83, 'Conclusión larga recortada con …');

// La migración reconoce el CHECK viejo (sin AABR) aunque ya tenga version.
$sql = file_get_contents(__DIR__ . '/../sql/schema.sql');
t_true(strpos($sql, "'AABR'") !== false, 'schema.sql acepta informes AABR');
t_true(strpos($sql, 'CREATE TABLE IF NOT EXISTS report_versions') !== false, 'schema.sql crea report_versions');
