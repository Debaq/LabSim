#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "╔══════════════════════════════╗"
echo "║   LabSim 3.0 — Dev Mode     ║"
echo "╚══════════════════════════════╝"

# Check dependencies
command -v node  >/dev/null || { echo "✗ node no encontrado";  exit 1; }
command -v cargo >/dev/null || { echo "✗ cargo no encontrado"; exit 1; }

# Install npm deps if needed
if [ ! -d node_modules ]; then
  echo "→ Instalando dependencias npm..."
  npm install
fi

# Kill any previous dev server on port 1420
if lsof -ti :1420 >/dev/null 2>&1; then
  echo "→ Liberando puerto 1420..."
  lsof -ti :1420 | xargs -r kill -9 2>/dev/null
  sleep 1
fi

echo "→ Lanzando Tauri en modo desarrollo..."
echo "  Frontend: http://localhost:1420"
echo "  Hot reload activo"
echo ""

npx tauri dev
