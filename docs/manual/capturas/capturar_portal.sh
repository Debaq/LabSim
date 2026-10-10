#!/usr/bin/env bash
# Capturas del PORTAL WEB DEL ESTUDIANTE (labsim_backend/public/student/)
# para el manual, con datos INVENTADOS. Reproducible:
#
#   docs/manual/capturas/capturar_portal.sh [directorio de trabajo] [puerto]
#
# Qué hace:
#   1. Copia labsim_backend a un directorio de trabajo NUEVO (por defecto uno
#      temporal), sin base, sin config y sin informes: nunca toca la base de
#      producción ni el labsim_backend del repo.
#   2. Escribe config/config.php y siembra la base con sembrar_portal.php
#      (alumna Valentina Rojas, pacientes de casos_demo.json) dentro de un
#      contenedor php:7.4-cli -- el PHP del sistema no trae pdo_sqlite y el
#      hosting corre 7.4.
#   3. Agrega a la COPIA dos páginas de mentira (solo existen ahí):
#        public/fake_lti_launch.php    firma un launch LTI 1.1 como Moodle y
#                                      lo manda a lti/launch.php (la página
#                                      "Ingreso correcto" con el botón
#                                      "Ver mis pacientes");
#        public/fake_login_student.php abre la sesión de alumno igual que
#                                      student/sso.php y redirige.
#   4. Levanta el servidor PHP en un contenedor, saca las capturas con
#      capturar_portal.py (Chromium headless por DevTools) y lo detiene.
#
# Salida: docs/manual/img/estudiante/web-*.png
# Requiere: podman, chromium, pdftoppm (poppler), python3 con "websockets".
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CAPTURAS="$REPO/docs/manual/capturas"
SALIDA="$REPO/docs/manual/img/estudiante"
TRABAJO="${1:-$(mktemp -d "${TMPDIR:-/tmp}/labsim_portal.XXXXXX")}"
PUERTO="${2:-8795}"
IMAGEN="docker.io/library/php:7.4-cli"
NOMBRE="labsim-portal-manual-$PUERTO"

if [ -e "$TRABAJO/data/labsim.sqlite" ]; then
    echo "Ya hay una base en $TRABAJO: usa un directorio nuevo." >&2
    exit 1
fi
mkdir -p "$TRABAJO"
echo "Copia de trabajo: $TRABAJO"

# 1. Copia sin datos privados.
rsync -a \
    --exclude 'data/*.sqlite*' --exclude 'config/config.php' \
    --exclude 'data/reports/*' --exclude 'data/patient_photos/*' \
    "$REPO/labsim_backend/" "$TRABAJO/"

# 2. Config y siembra.
# Misma forma que config/config.example.php (lo que genera install.php).
cat > "$TRABAJO/config/config.php" <<'PHP'
<?php
return [
    'db' => ['path' => __DIR__ . '/../data/labsim.sqlite'],
    'sync_poll_seconds' => 15,
    'lti_jwks_cache_seconds' => 3600,
    'pairing_code_ttl_seconds' => 300,
];
PHP
mkdir -p "$TRABAJO/_manual"
cp "$CAPTURAS/sembrar_portal.php" "$CAPTURAS/casos_demo.json" "$TRABAJO/_manual/"
SEMBRADO="$(podman run --rm -v "$TRABAJO:/app:Z" -w /app "$IMAGEN" \
    php _manual/sembrar_portal.php /app /app/_manual/casos_demo.json)"
echo "Sembrado: $SEMBRADO"

# Fotos de otoscopía de la ficha de estudio (caso 37, el de la práctica
# libre): las mismas membranas de las capturas de la app. Van en JPEG
# porque el php:7.4-cli no trae GD para convertir el webp.
mkdir -p "$TRABAJO/data/otoscopia_photos"
for lado in od oi; do
    magick "$CAPTURAS/otoscopia/$lado.webp" -quality 90 "$TRABAJO/data/otoscopia_photos/37_${lado}_0.jpg"
done

# 3. Páginas de mentira, solo en la copia.
cat > "$TRABAJO/public/fake_login_student.php" <<'PHP'
<?php
// SOLO PARA CAPTURAS: abre la sesión de alumno como student/sso.php, sin
// token, y redirige a student/<to>.
declare(strict_types=1);
require_once __DIR__ . '/bootstrap.php';
$to = (string) ($_GET['to'] ?? 'mis_pacientes.php');
if (!preg_match('/^[a-z_]+\.php(\?[A-Za-z0-9_=&]*)?(#[a-z]+)?$/', $to)) {
    http_response_code(400);
    exit('to inválido');
}
Auth::startSession();
session_regenerate_id(true);
$_SESSION['student_user_id'] = (int) ($_GET['uid'] ?? 0);
header('Location: student/' . $to);
PHP

cat > "$TRABAJO/public/fake_lti_launch.php" <<'PHP'
<?php
// SOLO PARA CAPTURAS: hace de Moodle. Firma un launch LTI 1.1 de la alumna
// sembrada (clave labsim-demo) y lo envía solo a lti/launch.php.
declare(strict_types=1);
require_once __DIR__ . '/../src/OAuth1.php';
$url = 'http://' . $_SERVER['HTTP_HOST'] . '/lti/launch.php';
$p = [
    'lti_message_type' => 'basic-lti-launch-request',
    'lti_version' => 'LTI-1p0',
    'resource_link_id' => 'labsim-actividad-1',
    'resource_link_title' => 'LabSim',
    'user_id' => 'moodle-1042',
    'roles' => 'Learner',
    'lis_person_name_full' => 'Valentina Rojas',
    'lis_person_contact_email_primary' => 'valentina.rojas@alumnos.ejemplo.cl',
    'context_id' => 'AUD301',
    'context_title' => 'Audiología Clínica I',
    'oauth_consumer_key' => 'labsim-demo',
    'oauth_nonce' => bin2hex(random_bytes(12)),
    'oauth_signature_method' => 'HMAC-SHA1',
    'oauth_timestamp' => (string) time(),
    'oauth_version' => '1.0',
];
$p['oauth_signature'] = OAuth1::sign($p, 'POST', $url, 'secreto-demo');
echo '<!doctype html><meta charset="utf-8"><form id="f" method="post" action="lti/launch.php">';
foreach ($p as $k => $v) {
    echo '<input type="hidden" name="' . htmlspecialchars($k) . '" value="' . htmlspecialchars($v) . '">';
}
echo '</form><script>document.getElementById("f").submit();</script>';
PHP

# 4. Servidor, capturas y limpieza (el contenedor se detiene pase lo que pase).
podman rm -f "$NOMBRE" >/dev/null 2>&1 || true
podman run -d --name "$NOMBRE" --network host -v "$TRABAJO:/app:Z" -w /app "$IMAGEN" \
    php -S "127.0.0.1:$PUERTO" -t public >/dev/null
trap 'podman rm -f "$NOMBRE" >/dev/null 2>&1 || true' EXIT
for _ in $(seq 1 50); do
    curl -fs -o /dev/null "http://127.0.0.1:$PUERTO/fake_lti_launch.php" && break
    sleep 0.2
done

mkdir -p "$SALIDA"
python3 "$CAPTURAS/capturar_portal.py" "http://127.0.0.1:$PUERTO" "$SALIDA" "$TRABAJO/_chromium" "$SEMBRADO"
echo "Listo: $SALIDA/web-*.png"
