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
        'sin verificar' => ['No verificó 2/3 ni 3/5', 'warn'],
        'sin dato' => ['—', ''],
    ];

    public static function render(array $res, bool $docente): void
    {
        $p = $res['puntaje'];
        ?>
        <div style="display:flex; align-items:center; gap:0.8rem; margin:0.3rem 0 0.5rem; flex-wrap:wrap;">
            <span style="font-size:1.8em; font-weight:700; color:<?= self::color($p['pct']) ?>;"><?= self::pct($p['pct']) ?></span>
            <span style="flex:1; min-width:8rem;">
                <?php self::barra($p['pct']); ?>
                <span style="font-size:0.85em; opacity:0.8;">Logro de la técnica: <?= (int) $p['cumple'] ?> de <?= (int) $p['total'] ?> pasos.</span>
            </span>
        </div>
        <?php if ($res['reconstruido']): ?>
        <p class="help" style="opacity:0.8;">Atención registrada antes de la versión actual del audiómetro: lo que oyó el paciente se recalculó y la duración de los estímulos no se puede medir.</p>
        <?php endif; ?>
        <?php
        $secciones = [];
        if ($res['orden']['reglas'] || $res['orden']['observaciones']) {
            $secciones['orden'] = 'Orden de las pruebas';
        }
        foreach (['aereos' => 'Umbrales aéreos', 'oseos' => 'Umbrales óseos'] as $via => $titulo) {
            if ($res[$via]['hecha'] || $res[$via]['reglas']) {
                $secciones[$via] = $titulo;
            }
        }
        foreach ($secciones as $k => $titulo) {
            self::seccion($titulo, $res[$k], $docente);
        }
    }

    /** Una sección plegada: el título trae el porcentaje; adentro, el detalle. */
    private static function seccion(string $titulo, array $s, bool $docente): void
    {
        $p = $s['puntaje'];
        $pendientes = $p['total'] - $p['cumple'];
        ?>
        <details style="margin:0.5rem 0; border-top:1px solid var(--color-border, #ddd); padding-top:0.4rem;">
            <summary style="cursor:pointer;">
                <strong><?= htmlspecialchars($titulo) ?></strong>
                · <span style="color:<?= self::color($p['pct']) ?>; font-weight:700;"><?= self::pct($p['pct']) ?></span>
                <span style="opacity:0.75; font-size:0.9em;">(<?= (int) $p['cumple'] ?> de <?= (int) $p['total'] ?><?= $pendientes > 0 ? ' · ' . $pendientes . ($docente ? ' sin cumplir' : ' para revisar') : '' ?>)</span>
                <?php foreach ($s['puntaje_oidos'] ?? [] as $oido => $po): ?>
                <span style="opacity:0.75; font-size:0.9em;"> · <?= htmlspecialchars((string) $oido) ?> <?= self::pct($po['pct']) ?></span>
                <?php endforeach; ?>
            </summary>
            <ul style="list-style:none; margin:0.3rem 0 0; padding:0;">
                <?php foreach ($s['reglas'] as $r) { self::regla($r, $docente); } ?>
            </ul>
            <?php foreach ($s['oidos'] ?? [] as $oido => $lista): ?>
            <div style="margin:0.4rem 0 0 0.2rem; font-weight:600;"><?= htmlspecialchars((string) $oido) ?>
                <span style="font-weight:400; opacity:0.75;">· <?= self::pct($s['puntaje_oidos'][$oido]['pct'] ?? null) ?></span></div>
            <ul style="list-style:none; margin:0; padding:0;">
                <?php foreach ($lista as $r) { self::regla($r, $docente); } ?>
            </ul>
            <?php endforeach; ?>
            <?php if ($s['observaciones']): ?>
            <div style="margin-top:0.3rem; font-size:0.9em;"><strong>Advertencias</strong> <span style="opacity:0.75;">(no descuentan)</span>:
                <ul style="margin:0.1rem 0 0 1.2rem; padding:0;">
                    <?php foreach ($s['observaciones'] as $o): ?><li><?= htmlspecialchars($o) ?></li><?php endforeach; ?>
                </ul>
            </div>
            <?php endif; ?>
            <?php if (!empty($s['umbrales'])) { self::tabla($s['umbrales'], $docente); } ?>
        </details>
        <?php
    }

    /** "82 %", o una raya si no hubo nada evaluable. */
    public static function pct(?int $pct): string
    {
        return $pct === null ? '—' : $pct . ' %';
    }

    /** Verde desde 85 %, ámbar desde 60 %, rojo debajo. */
    public static function color(?int $pct): string
    {
        if ($pct === null) {
            return '#888';
        }
        return $pct >= 85 ? '#2e7d32' : ($pct >= 60 ? '#b26a00' : '#c0392b');
    }

    private static function barra(?int $pct): void
    {
        ?>
        <span style="display:block; height:0.5rem; border-radius:0.25rem; background:var(--color-border, #ddd); overflow:hidden; margin-bottom:0.2rem;">
            <span style="display:block; height:100%; width:<?= (int) ($pct ?? 0) ?>%; background:<?= self::color($pct) ?>;"></span>
        </span>
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
                <th style="text-align:left; padding:0.2rem 0.6rem 0.2rem 0;" title="Orden en que tomó los umbrales">#</th>
                <th style="text-align:left; padding:0.2rem 0.6rem 0.2rem 0;">Oído</th>
                <th style="text-align:left; padding:0.2rem 0.6rem 0.2rem 0;">Frecuencia</th>
                <th style="text-align:left; padding:0.2rem 0.6rem 0.2rem 0;">Obtenido</th>
                <?php if ($docente): ?>
                <th style="text-align:left; padding:0.2rem 0.6rem 0.2rem 0;">Paciente</th>
                <th style="text-align:left; padding:0.2rem 0.6rem 0.2rem 0;">Sombra</th>
                <?php endif; ?>
                <th style="text-align:left; padding:0.2rem 0;"></th>
            </tr>
            <?php $n = 0; ?>
            <?php foreach ($umbrales as $oido => $filas): ?>
            <?php foreach ($filas as $f): ?>
            <?php $n++; ?>
            <?php [$label, $tipo] = self::ESTADOS[$f['estado']] ?? [$f['estado'], '']; ?>
            <tr style="border-top:1px solid var(--color-border, #ddd);">
                <td style="padding:0.2rem 0.6rem 0.2rem 0; opacity:0.7;"><?= $n ?></td>
                <td style="padding:0.2rem 0.6rem 0.2rem 0;"><?= htmlspecialchars((string) $oido) ?></td>
                <td style="padding:0.2rem 0.6rem 0.2rem 0;"><?= htmlspecialchars(AudiometriaTecnica::hz($f['freq'])) ?><?= $f['repeticion'] ? ' <span style="opacity:0.7;">(' . (($f['innecesaria'] ?? false) ? 'repetición sin necesidad' : 'repetición') . ')</span>' : '' ?></td>
                <td style="padding:0.2rem 0.6rem 0.2rem 0;"><?= $f['sin_respuesta'] ?? false ? 'sin respuesta' : self::db($f['estimado'], $f['aprox']) ?><?= $f['con_ruido'] ? ' <span style="opacity:0.7;">(con ruido)</span>' : '' ?></td>
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
