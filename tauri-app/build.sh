#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "╔══════════════════════════════╗"
echo "║  LabSim 3.0 — Build         ║"
echo "╚══════════════════════════════╝"

# Check dependencies
command -v node  >/dev/null || { echo "✗ node no encontrado";  exit 1; }
command -v cargo >/dev/null || { echo "✗ cargo no encontrado"; exit 1; }

# Install npm deps if needed
if [ ! -d node_modules ]; then
  echo "→ Instalando dependencias npm..."
  npm install
fi

# Type check
echo "→ Verificando TypeScript..."
npx tsc --noEmit

# Build
echo "→ Compilando frontend + backend..."
npx tauri build --no-bundle

echo ""
echo "╔══════════════════════════════╗"
echo "║  Build completado!           ║"
echo "╚══════════════════════════════╝"
echo ""

# Show output
BUNDLE_DIR="src-tauri/target/release/bundle"
if [ -d "$BUNDLE_DIR" ]; then
  echo "Binarios generados:"
  find "$BUNDLE_DIR" -maxdepth 2 -type f \( -name "*.deb" -o -name "*.AppImage" -o -name "*.rpm" -o -name "*.dmg" -o -name "*.msi" -o -name "*.exe" \) 2>/dev/null | while read -r f; do
    SIZE=$(du -h "$f" | cut -f1)
    echo "  $SIZE  $f"
  done

  # Also show the raw binary
  BIN="src-tauri/target/release/labsim"
  if [ -f "$BIN" ]; then
    SIZE=$(du -h "$BIN" | cut -f1)
    echo "  $SIZE  $BIN (binario directo)"
  fi
fi
