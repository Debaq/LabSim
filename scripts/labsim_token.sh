#!/usr/bin/env bash
# Guarda el token de la consola remota (admin -> Datos e IA -> Consola remota)
# en ~/.config/labsim/consola.env, de donde lo lee scripts/consola.py. Así el
# token no pasa por el chat.
#
#   labsim_token.sh lsc_...          guarda (reemplaza el anterior) y prueba
#   labsim_token.sh --borrar         borra el archivo (no revoca: eso es
#                                    "consola.py revocar" o el panel)
#
# LABSIM_CONSOLA_URL cambia el backend (por defecto, el de producción).
set -euo pipefail

ARCHIVO="$HOME/.config/labsim/consola.env"
URL="${LABSIM_CONSOLA_URL:-https://tmeduca.org/labsim/backend/public/api/consola.php}"

if [[ "${1:-}" == "--borrar" ]]; then
    rm -f "$ARCHIVO"
    echo "Borrado $ARCHIVO"
    exit 0
fi

TOKEN="${1:-}"
if [[ ! "$TOKEN" =~ ^lsc_[0-9a-f]{64}$ ]]; then
    echo "Uso: $(basename "$0") lsc_<64 caracteres>   (el token del panel)" >&2
    exit 1
fi

mkdir -p "$(dirname "$ARCHIVO")"
umask 077
printf 'LABSIM_CONSOLA_URL=%s\nLABSIM_CONSOLA_TOKEN=%s\n' "$URL" "$TOKEN" > "$ARCHIVO"
chmod 600 "$ARCHIVO"
echo "Guardado en $ARCHIVO"

# Prueba: sin mostrar el token, solo si el backend lo acepta y cuándo vence.
python3 "$(dirname "$(readlink -f "$0")")/consola.py" --env "$ARCHIVO" ping
