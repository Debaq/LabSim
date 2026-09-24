<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Oirs.php';

/**
 * Los avisos de la OIRS simulada se le muestran al alumno como lo que son:
 * una sugerencia del paciente virtual, parte del ejercicio (ver Oirs.php).
 * "Reclamo" se leía como una queja real.
 */

$viejo = [
    'tipo' => 'reclamo',
    'remitente' => 'Oficina de Informaciones, Reclamos y Sugerencias (OIRS)',
    'asunto' => 'OIRS: Aviso de reclamo por atención recibida',
    'cuerpo' => 'El paciente sintió que no le explicaron el examen.',
];
$alumno = Oirs::paraAlumno($viejo);
t_eq($alumno['tipo_label'], 'Sugerencia de mejora', 'Reclamo se nombra como sugerencia de mejora');
t_eq($alumno['remitente'], Oirs::REMITENTE, 'Remitente suave también en mensajes viejos');
t_eq($alumno['asunto'], 'Sugerencia de mejora sobre tu atención', 'Asunto viejo con "reclamo" se reemplaza');
t_eq($alumno['cuerpo'], $viejo['cuerpo'], 'El cuerpo (el motivo) no se toca');
t_true(strpos($alumno['aviso'], 'simulado') !== false, 'Lleva el aviso de que es simulado');
foreach (['remitente', 'asunto', 'tipo_label'] as $campo) {
    t_true(stripos($alumno[$campo], 'reclamo') === false, "Sin la palabra reclamo en {$campo}");
}

$merito = Oirs::paraAlumno(['tipo' => 'merito', 'asunto' => 'x', 'remitente' => 'y', 'cuerpo' => 'z']);
t_eq($merito['tipo_label'], 'Felicitación', 'Mérito se nombra como felicitación');
t_eq($merito['asunto'], 'Felicitación por tu atención', 'Asunto de felicitación');

$docente = Oirs::paraAlumno(['tipo' => 'mensaje', 'asunto' => 'Revisa tu ABR', 'remitente' => 'Prof. Soto', 'cuerpo' => '...']);
t_eq([$docente['asunto'], $docente['remitente'], $docente['tipo_label']],
     ['Revisa tu ABR', 'Prof. Soto', 'Mensaje docente'], 'Un mensaje del docente queda como lo escribió');
t_true(!isset($docente['aviso']), 'Sin aviso de simulado en mensajes del docente');
