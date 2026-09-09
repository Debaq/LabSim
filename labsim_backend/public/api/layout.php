<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Layout de la app de escritorio (módulos, sectores, boxes).
 *
 * Anónimo a propósito: el cliente lo pide al arrancar antes de loguearse,
 * y si el hosting/backend no responde simplemente abre la ventana de login
 * sin toolbar (ver app_layout.py del cliente). La metadata del layout no
 * es sensible -- son tooltips, tamaños de ventana y nombres de boxes.
 *
 * Antes vivía en resources/json/apps.json del cliente Python. Ahora lo
 * sirve el backend para que un cambio de estructura (agregar módulo,
 * renombrar box, mover tab) se haga en un solo lugar y se refleje al
 * próximo arranque de la app, sin tocar el binario.
 */

Response::json(Layout::payload());
