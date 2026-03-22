#!/usr/bin/env bash
# Propaga la versión de VERSION a todos los archivos del proyecto.
# Uso:
#   ./scripts/bump-version.sh          # lee VERSION actual
#   ./scripts/bump-version.sh 3.1.0    # actualiza VERSION y propaga

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION_FILE="$ROOT/VERSION"

if [[ $# -ge 1 ]]; then
    echo "$1" > "$VERSION_FILE"
fi

VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"

if [[ -z "$VERSION" ]]; then
    echo "Error: VERSION está vacío" >&2
    exit 1
fi

echo "Propagando versión $VERSION..."

# package.json
sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$ROOT/tauri-app/package.json"

# tauri.conf.json
sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$ROOT/tauri-app/src-tauri/tauri.conf.json"

# Cargo.toml (solo el workspace root, no los crates)
sed -i "0,/^version = \"[^\"]*\"/s//version = \"$VERSION\"/" "$ROOT/tauri-app/src-tauri/Cargo.toml"

echo "Listo:"
grep -n '"version"' "$ROOT/tauri-app/package.json" "$ROOT/tauri-app/src-tauri/tauri.conf.json"
grep -n '^version' "$ROOT/tauri-app/src-tauri/Cargo.toml"
