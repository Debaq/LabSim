#!/usr/bin/env bash
# Arma los casos del libro que se piden por CUADRO (no por paciente demo),
# con el editor de casos de verdad y el azar sembrado:
#
#   docs/libro/figuras/armar_casos.sh [patrón…]      p. ej. cap11_*
#
# Para cada docs/libro/casos/<nombre>.json con
#   "caso": {"cuadro": {"OD": "schwannoma", "OI": "normal"},
#            "grado": {"OD": "moderada"}, "edad": 54, "sexo": "mujer", "semilla": 3}
# deja el cases.data en docs/libro/casos/generados/<nombre>.json, que es lo
# que lee hacer_figuras.py.
#
# Qué hace (mismo andamiaje que docs/manual/capturas/capturar_portal.sh):
#   1. Copia labsim_backend a un directorio temporal NUEVO, sin base ni config
#      ni datos: nunca toca producción ni el backend del repo.
#   2. Siembra una base de mentira (sembrar_portal.php) en php:7.4-cli.
#   3. Agrega a la COPIA una página que abre sesión de docente sin clave.
#   4. Chromium headless abre admin/case_create.php con Math.random sembrado,
#      elige edad, sexo, cuadro y grado, aprieta "Generar caso" y "Crear caso".
#      El generador y CaseForm::fromPost son los del sistema, sin copias.
#
# Requiere: podman, chromium, python3 con "websockets".
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
AQUI="$REPO/docs/libro/figuras"
CAPTURAS="$REPO/docs/manual/capturas"
TRABAJO="$(mktemp -d "${TMPDIR:-/tmp}/labsim_libro.XXXXXX")"
PUERTO="${PUERTO:-8796}"
IMAGEN="docker.io/library/php:7.4-cli"
NOMBRE="labsim-libro-casos-$PUERTO"

rsync -a \
    --exclude 'data/*.sqlite*' --exclude 'config/config.php' \
    --exclude 'data/reports/*' --exclude 'data/patient_photos/*' \
    --exclude 'data/otoscopia_photos/*' \
    "$REPO/labsim_backend/" "$TRABAJO/"

cat > "$TRABAJO/config/config.php" <<'PHP'
<?php
return [
    'db' => ['path' => __DIR__ . '/../data/labsim.sqlite'],
    'sync_poll_seconds' => 15,
    'lti_jwks_cache_seconds' => 3600,
    'pairing_code_ttl_seconds' => 300,
];
PHP
mkdir -p "$TRABAJO/_libro"
cp "$CAPTURAS/sembrar_portal.php" "$CAPTURAS/casos_demo.json" "$TRABAJO/_libro/"
SEMBRADO="$(podman run --rm -v "$TRABAJO:/app:Z" -w /app "$IMAGEN" \
    php _libro/sembrar_portal.php /app /app/_libro/casos_demo.json)"

cat > "$TRABAJO/public/fake_login_admin.php" <<'PHP'
<?php
// SOLO EN LA COPIA DEL LIBRO: abre la sesión del docente sembrado, sin clave.
declare(strict_types=1);
require_once __DIR__ . '/bootstrap.php';
Auth::startSession();
session_regenerate_id(true);
$_SESSION['admin_user_id'] = (int) ($_GET['uid'] ?? 0);
header('Location: admin/case_create.php');
PHP

cat > "$TRABAJO/_libro/ultimo_caso.php" <<'PHP'
<?php
// cases.data del último caso creado, tal como quedó en la base.
$pdo = new PDO('sqlite:/app/data/labsim.sqlite');
echo $pdo->query('SELECT data FROM cases ORDER BY id DESC LIMIT 1')->fetchColumn();
PHP

podman rm -f "$NOMBRE" >/dev/null 2>&1 || true
podman run -d --name "$NOMBRE" --network host -v "$TRABAJO:/app:Z" -w /app "$IMAGEN" \
    php -S "127.0.0.1:$PUERTO" -t public >/dev/null
trap 'podman rm -f "$NOMBRE" >/dev/null 2>&1 || true; rm -rf "$TRABAJO"' EXIT
for _ in $(seq 1 50); do
    curl -fs -o /dev/null "http://127.0.0.1:$PUERTO/fake_login_admin.php" && break
    sleep 0.2
done

python3 "$AQUI/armar_casos.py" "http://127.0.0.1:$PUERTO" "$NOMBRE" "$SEMBRADO" "$@"
