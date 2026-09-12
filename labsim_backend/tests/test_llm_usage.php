<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/LlmUsage.php';

/**
 * Contabilidad del consumo del LLM. Se testea la parte pura -- franja
 * horaria, lectura del bloque `usage` y costo -- que es donde un error no
 * se nota: la tabla igual se llena, solo que con el número equivocado.
 */

// --- Franja horaria de DeepSeek: L-V 01:00-04:00 y 06:00-10:00 UTC -------
$lunes = static fn(string $hora): int => (int) strtotime('2026-09-07 ' . $hora . ' UTC'); // lunes
$sabado = static fn(string $hora): int => (int) strtotime('2026-09-12 ' . $hora . ' UTC'); // sábado

t_eq(LlmUsage::ventana('deepseek', $lunes('02:00')), 'peak', 'Lunes 02:00 UTC: precio pleno');
t_eq(LlmUsage::ventana('deepseek', $lunes('01:00')), 'peak', 'El borde de abajo entra en la franja cara');
t_eq(LlmUsage::ventana('deepseek', $lunes('03:59')), 'peak', 'Un minuto antes del corte sigue caro');
t_eq(LlmUsage::ventana('deepseek', $lunes('04:00')), 'offpeak', 'El borde de arriba ya es rebajado');
t_eq(LlmUsage::ventana('deepseek', $lunes('05:30')), 'offpeak', 'El hueco entre las dos franjas es rebajado');
t_eq(LlmUsage::ventana('deepseek', $lunes('09:59')), 'peak', 'Segunda franja cara');
t_eq(LlmUsage::ventana('deepseek', $lunes('10:00')), 'offpeak', 'Y su corte');

// Lo que de verdad importa: el horario de clases chileno. 09:00 en Chile
// (UTC-4) son las 13:00 UTC, fuera de toda franja cara.
t_eq(LlmUsage::ventana('deepseek', $lunes('13:00')), 'offpeak', 'Mañana de clases en Chile: tarifa rebajada');
t_eq(LlmUsage::ventana('deepseek', $lunes('20:00')), 'offpeak', 'Tarde de clases en Chile: tarifa rebajada');

t_eq(LlmUsage::ventana('deepseek', $sabado('02:00')), 'offpeak', 'El fin de semana no tiene franja cara');

// Un backend compatible con OpenAI cobra plano: nunca se le descuenta.
t_eq(LlmUsage::ventana('openai_compatible', $lunes('13:00')), 'peak',
    'Sin horario diferido, toda llamada se anota a precio pleno');

// --- Lectura del bloque `usage` -----------------------------------------
$u = LlmUsage::normalizar([
    'prompt_tokens' => 1000,
    'prompt_cache_hit_tokens' => 900,
    'prompt_cache_miss_tokens' => 100,
    'completion_tokens' => 500,
    'completion_tokens_details' => ['reasoning_tokens' => 400],
    'total_tokens' => 1500,
]);
t_eq($u['cache_hit'], 900, 'Toma el corte de cache que reporta DeepSeek');
t_eq($u['cache_miss'], 100, 'Y los tokens nuevos');
t_eq($u['razonamiento'], 400, 'El razonamiento sale del bloque anidado');
t_eq($u['completion'], 500, 'completion YA incluye el razonamiento: no se le resta');

// Proveedor que no reporta cache: todo el prompt cuenta como nuevo. De
// más, nunca de menos -- lo contrario haría parecer barato lo que no lo es.
$sinCache = LlmUsage::normalizar(['prompt_tokens' => 800, 'completion_tokens' => 200, 'total_tokens' => 1000]);
t_eq($sinCache['cache_hit'], 0, 'Sin reporte de cache, no se asume ningún hit');
t_eq($sinCache['cache_miss'], 800, 'Y todo el prompt entra como token nuevo');

t_eq(LlmUsage::normalizar([])['total'], 0, 'Respuesta sin usage: todo en cero, no revienta');

// --- Costo ---------------------------------------------------------------
// Tarifas redondas para que la cuenta se pueda seguir a mano.
$cfg = ['price_cache_hit' => 0.1, 'price_cache_miss' => 1.0, 'price_output' => 10.0];

$fila = ['cache_hit' => 1000000, 'cache_miss' => 1000000, 'completion' => 1000000, 'ventana' => 'peak'];
t_close(LlmUsage::costo($fila, $cfg), 11.1, 0.0001, 'Precio pleno: un millón de cada uno suma las tres tarifas');

$fila['ventana'] = 'offpeak';
t_close(LlmUsage::costo($fila, $cfg), 5.55, 0.0001, 'Franja rebajada: exactamente la mitad');

// Sin tarifas cargadas el costo es cero, no un invento.
t_close(LlmUsage::costo($fila, []), 0.0, 0.0001, 'Sin tarifas no se estima ningún costo');

// El corte de cache es lo que decide la factura: los mismos tokens de
// prompt salen diez veces más caros si ninguno pegó en cache.
$todoCache = ['cache_hit' => 2000000, 'cache_miss' => 0, 'completion' => 0, 'ventana' => 'peak'];
$nadaCache = ['cache_hit' => 0, 'cache_miss' => 2000000, 'completion' => 0, 'ventana' => 'peak'];
t_true(LlmUsage::costo($nadaCache, $cfg) > LlmUsage::costo($todoCache, $cfg) * 9,
    'Sin cache, el mismo prompt cuesta un orden de magnitud más');

// --- Cortes de período ---------------------------------------------------
t_true(LlmUsage::desde(0) < gmdate('Y-m-d H:i:s'), 'El corte de "hoy" ya pasó');
t_true(LlmUsage::desde(30) < LlmUsage::desde(7), 'Treinta días arranca antes que siete');
t_true(LlmUsage::desde(7) < LlmUsage::desde(0), 'Y siete antes que hoy');
// Hoy más los seis anteriores, no siete hacia atrás. La tolerancia de una
// hora es por el cambio de horario de Chile: si el período cruza el domingo
// en que se adelanta el reloj, los seis días duran una hora menos. Ese
// desfase mueve una llamada de borde entre dos días, no el total.
$salto = strtotime(LlmUsage::desde(0) . ' UTC') - strtotime(LlmUsage::desde(7) . ' UTC');
t_true(abs($salto - 6 * 86400) <= 3600,
    '"Últimos 7 días" son hoy más los seis anteriores, no siete hacia atrás');
