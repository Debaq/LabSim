<?php

declare(strict_types=1);

require_once __DIR__ . '/AudiometriaTecnica.php';

/**
 * Cómo se muestran los indicadores de AudiometriaTecnica. Lo ven el docente
 * (admin/chat_detail.php) y el alumno (student/atencion.php) con el mismo
 * bloque; cambia el tono y qué se muestra:
 * - Docente: "Cumple / No cumple" y los umbrales del paciente al lado de
 *   los obtenidos.
 * - Alumno: "Para revisar" en vez de un error (mismo criterio que la OIRS)
 *   y sin los umbrales del paciente: ve si su umbral corresponde, no cuál
 *   era.
 * Solo pinta el contenido; la tarjeta la pone cada página.
 */
final class AudiometriaTecnicaVista
{
    private const ESTADOS = [
        'coincide' => ['Corresponde', 'ok'],
        'sombra' => ['Curva sombra', 'warn'],
        'difiere' => ['No corresponde', 'warn'],
        'sin cerrar' => ['Sin cerrar', 'warn'],
        'sin dato' => ['—', ''],
    ];

    public static function render(array $res, bool $docente): void
    {
        $p = $res['puntaje'];
        ?>
        <p style="margin:0.2rem 0 0.4rem;">
            <strong><?= (int) $p['cumple'] ?> de <?= (int) $p['total'] ?></strong> pasos de la técnica.
        </p>
        <?php if ($res['reconstruido']): ?>
        <p class="help" style="opacity:0.8;">Atención registrada antes de la versión actual del audiómetro: lo que oyó el paciente se recalculó y la duración de los estímulos no se puede medir.</p>
        <?php endif; ?>
        <?php
        if ($res['orden']['reglas'] || $res['orden']['observaciones']) {
            self::seccion('Orden de las pruebas', $res['orden']['reglas'], [], $res['orden']['observaciones'], $docente);
        }
        foreach (['aereos' => 'Umbrales aéreos', 'oseos' => 'Umbrales óseos'] as $via => $titulo) {
            $v = $res[$via];
            if (!$v['hecha'] && !$v['reglas']) {
                continue;
            }
            self::seccion($titulo, $v['reglas'], $v['oidos'], $v['observaciones'], $docente);
            if ($v['umbrales']) {
                self::tabla($v['umbrales'], $docente);
            }
        }
    }

    private static function seccion(string $titulo, array $reglas, array $oidos, array $observaciones, bool $docente): void
    {
        ?>
        <h4 style="margin:0.9rem 0 0.2rem;"><?= htmlspecialchars($titulo) ?></h4>
        <ul style="list-style:none; margin:0; padding:0;">
            <?php foreach ($reglas as $r) { self::regla($r, $docente); } ?>
        </ul>
        <?php foreach ($oidos as $oido => $lista): ?>
        <div style="margin:0.3rem 0 0 0.2rem; font-weight:600;"><?= htmlspecialchars($oido) ?></div>
        <ul style="list-style:none; margin:0; padding:0;">
            <?php foreach ($lista as $r) { self::regla($r, $docente); } ?>
        </ul>
        <?php endforeach; ?>
        <?php if ($observaciones): ?>
        <div style="margin-top:0.3rem; font-size:0.9em;"><strong>Observaciones:</strong>
            <ul style="margin:0.1rem 0 0 1.2rem; padding:0;">
                <?php foreach ($observaciones as $o): ?><li><?= htmlspecialchars($o) ?></li><?php endforeach; ?>
            </ul>
        </div>
        <?php endif; ?>
        <?php
    }

    private static function regla(array $r, bool $docente): void
    {
        if ($r['cumple'] === true) {
            $marca = '✓';
            $etiqueta = $docente ? 'Cumple' : 'Bien';
            $color = '#2e7d32';
        } elseif ($r['cumple'] === false) {
            $marca = '!';
            $etiqueta = $docente ? 'No cumple' : 'Para revisar';
            $color = '#c0392b';
        } else {
            $marca = '–';
            $etiqueta = 'No evaluable';
            $color = '#888';
        }
        ?>
        <li style="margin:0.25rem 0; font-size:0.9em; display:flex; gap:0.5rem; align-items:baseline;">
            <span title="<?= htmlspecialchars($etiqueta) ?>" style="color:<?= $color ?>; font-weight:700; min-width:1rem; text-align:center;"><?= $marca ?></span>
            <span><?= htmlspecialchars($r['texto']) ?>
                <span style="opacity:0.75;"><?= htmlspecialchars($r['detalle']) ?></span></span>
        </li>
        <?php
    }

    private static function tabla(array $umbrales, bool $docente): void
    {
        ?>
        <table style="margin-top:0.4rem; font-size:0.85em; border-collapse:collapse;">
            <tr>
                <th style="text-align:left; padding:0.2rem 0.6rem 0.2rem 0;">Oído</th>
                <th style="text-align:left; padding:0.2rem 0.6rem 0.2rem 0;">Frecuencia</th>
                <th style="text-align:left; padding:0.2rem 0.6rem 0.2rem 0;">Obtenido</th>
                <?php if ($docente): ?>
                <th style="text-align:left; padding:0.2rem 0.6rem 0.2rem 0;">Paciente</th>
                <th style="text-align:left; padding:0.2rem 0.6rem 0.2rem 0;">Sombra</th>
                <?php endif; ?>
                <th style="text-align:left; padding:0.2rem 0;"></th>
            </tr>
            <?php foreach ($umbrales as $oido => $filas): ?>
            <?php foreach ($filas as $f): ?>
            <?php [$label, $tipo] = self::ESTADOS[$f['estado']] ?? [$f['estado'], '']; ?>
            <tr style="border-top:1px solid var(--color-border, #ddd);">
                <td style="padding:0.2rem 0.6rem 0.2rem 0;"><?= htmlspecialchars((string) $oido) ?></td>
                <td style="padding:0.2rem 0.6rem 0.2rem 0;"><?= htmlspecialchars(AudiometriaTecnica::hz($f['freq'])) ?></td>
                <td style="padding:0.2rem 0.6rem 0.2rem 0;"><?= self::db($f['estimado'], $f['aprox']) ?><?= $f['con_ruido'] ? ' <span style="opacity:0.7;">(con ruido)</span>' : '' ?></td>
                <?php if ($docente): ?>
                <td style="padding:0.2rem 0.6rem 0.2rem 0;"><?= self::db($f['real'], null) ?></td>
                <td style="padding:0.2rem 0.6rem 0.2rem 0;"><?= $f['sombra'] !== null && $f['sombra'] !== $f['real'] ? self::db($f['sombra'], null) : '—' ?></td>
                <?php endif; ?>
                <td style="padding:0.2rem 0;"><span class="<?= $tipo === 'warn' ? 'badge-warn' : '' ?>"><?= htmlspecialchars($label) ?></span></td>
            </tr>
            <?php endforeach; ?>
            <?php endforeach; ?>
        </table>
        <?php
    }

    private static function db(?int $valor, ?int $aprox): string
    {
        if ($valor === null) {
            return $aprox !== null ? '~' . $aprox . ' dB' : '—';
        }
        return $valor >= 130 ? 'sin respuesta' : $valor . ' dB';
    }
}
