#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════
#  LabSim 3.0 — Script de gestión
# ═══════════════════════════════════════════════════════
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
APP="$ROOT/tauri-app"
BACKEND="$ROOT/labsim-backend"

# ─── Colores ──────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

header() {
  echo ""
  echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}LabSim 3.0${NC} — $1"
  echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
  echo ""
}

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; exit 1; }
info() { echo -e "  ${DIM}→${NC} $1"; }
warn() { echo -e "  ${YELLOW}!${NC} $1"; }

# ─── Verificar dependencias ───────────────────────────
check_deps() {
  local missing=0
  for cmd in node npm cargo rustc php; do
    if command -v "$cmd" >/dev/null 2>&1; then
      ok "$cmd $(command $cmd --version 2>/dev/null | head -1 | grep -oP '[\d]+\.[\d]+\.[\d]+')"
    else
      warn "$cmd no encontrado"
      missing=1
    fi
  done
  if [ $missing -eq 1 ]; then
    echo ""
    warn "Algunas dependencias faltan. Puede que ciertos comandos no funcionen."
  fi
}

# ─── Instalar dependencias npm ────────────────────────
ensure_deps() {
  if [ ! -d "$APP/node_modules" ]; then
    info "Instalando dependencias npm..."
    (cd "$APP" && npm install)
  fi
}

# ─── Liberar puerto ───────────────────────────────────
free_port() {
  local port=$1
  if lsof -ti :"$port" >/dev/null 2>&1; then
    info "Liberando puerto $port..."
    lsof -ti :"$port" | xargs -r kill -9 2>/dev/null || true
    sleep 1
  fi
}

# ═══════════════════════════════════════════════════════
#  COMANDOS
# ═══════════════════════════════════════════════════════

cmd_dev() {
  header "Desarrollo"
  ensure_deps
  free_port 1420
  info "Frontend: http://localhost:1420"
  info "Hot reload activo"
  echo ""
  (cd "$APP" && npx tauri dev)
}

cmd_build() {
  header "Build"
  ensure_deps

  info "Verificando TypeScript..."
  (cd "$APP" && npx tsc --noEmit)
  ok "TypeScript OK"

  local bundle_flag=""
  if [ "$1" = "--no-bundle" ]; then
    bundle_flag="--no-bundle"
    info "Sin empaquetado (solo binario)"
  fi

  info "Compilando frontend + backend..."
  (cd "$APP" && npx tauri build $bundle_flag)
  ok "Build completado"

  # Mostrar salida
  local bin="$APP/src-tauri/target/release/labsim"
  if [ -f "$bin" ]; then
    echo ""
    local size=$(du -h "$bin" | cut -f1)
    ok "Binario: $size → $bin"
  fi

  local bundle_dir="$APP/src-tauri/target/release/bundle"
  if [ -d "$bundle_dir" ]; then
    find "$bundle_dir" -maxdepth 2 -type f \( -name "*.deb" -o -name "*.AppImage" -o -name "*.rpm" -o -name "*.dmg" -o -name "*.msi" \) 2>/dev/null | while read -r f; do
      local size=$(du -h "$f" | cut -f1)
      ok "Paquete: $size → $f"
    done
  fi
}

cmd_check() {
  header "Verificación"
  ensure_deps

  info "TypeScript..."
  (cd "$APP" && npx tsc --noEmit)
  ok "TypeScript OK"

  info "Rust..."
  (cd "$APP/src-tauri" && cargo build 2>&1 | tail -1)
  ok "Rust OK"

  echo ""
  ok "Todo compila correctamente"
}

cmd_migrate() {
  header "Migración de base de datos"
  if ! command -v php >/dev/null 2>&1; then
    fail "PHP no encontrado"
  fi
  php "$BACKEND/migrate.php"
  ok "Migración completada"
}

cmd_install_db() {
  header "Instalación de base de datos"
  if ! command -v php >/dev/null 2>&1; then
    fail "PHP no encontrado"
  fi
  php "$BACKEND/install.php"
  ok "Base de datos creada"
}

cmd_clean() {
  header "Limpieza"

  if [ -d "$APP/node_modules" ]; then
    info "Eliminando node_modules..."
    rm -rf "$APP/node_modules"
    ok "node_modules eliminado"
  fi

  if [ -d "$APP/.vite" ]; then
    info "Eliminando caché Vite..."
    rm -rf "$APP/.vite"
    ok "Caché Vite eliminado"
  fi

  local target="$APP/src-tauri/target"
  if [ -d "$target" ]; then
    local size=$(du -sh "$target" | cut -f1)
    echo ""
    warn "target/ ocupa $size"
    read -p "  ¿Eliminar target/? (s/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
      rm -rf "$target"
      ok "target/ eliminado"
    fi
  fi
}

cmd_status() {
  header "Estado del proyecto"

  # Git
  local branch=$(git -C "$ROOT" branch --show-current 2>/dev/null)
  local commits=$(git -C "$ROOT" log --oneline -1 2>/dev/null)
  ok "Branch: $branch"
  ok "Último commit: $commits"

  # Archivos
  local ts_files=$(find "$APP/src" -name "*.tsx" -o -name "*.ts" | grep -v node_modules | wc -l)
  local rs_files=$(find "$APP/src-tauri/src" -name "*.rs" | wc -l)
  local php_files=$(find "$BACKEND" -name "*.php" | wc -l)
  local modules=$(find "$APP/src/modules" -maxdepth 1 -type d | tail -n +2 | wc -l)
  local simulators=$(find "$APP/src/components/windows" -name "*-window.tsx" -o -name "*-placeholder.tsx" | wc -l)

  echo ""
  info "TypeScript/TSX: $ts_files archivos"
  info "Rust: $rs_files archivos"
  info "PHP: $php_files archivos"
  info "Módulos clínicos: $modules"
  info "Ventanas/simuladores: $simulators"

  # Tamaños
  echo ""
  local app_size=$(du -sh "$APP/src" 2>/dev/null | cut -f1)
  local rust_size=$(du -sh "$APP/src-tauri/src" 2>/dev/null | cut -f1)
  local backend_size=$(du -sh "$BACKEND" 2>/dev/null | cut -f1)
  info "Frontend: $app_size"
  info "Rust: $rust_size"
  info "Backend: $backend_size"

  if [ -d "$APP/src-tauri/target" ]; then
    local target_size=$(du -sh "$APP/src-tauri/target" 2>/dev/null | cut -f1)
    info "target/ (build cache): $target_size"
  fi
}

cmd_deps() {
  header "Dependencias"
  check_deps
}

# ═══════════════════════════════════════════════════════
#  HELP
# ═══════════════════════════════════════════════════════

cmd_help() {
  echo ""
  echo -e "${BOLD}LabSim 3.0${NC} — Script de gestión"
  echo ""
  echo -e "${BOLD}Uso:${NC} ./labsim.sh <comando> [opciones]"
  echo ""
  echo -e "${BOLD}Desarrollo:${NC}"
  echo "  dev              Lanzar en modo desarrollo (hot reload)"
  echo "  build            Compilar para producción"
  echo "  build --no-bundle  Compilar sin empaquetar (solo binario)"
  echo "  check            Verificar que TypeScript y Rust compilan"
  echo ""
  echo -e "${BOLD}Base de datos:${NC}"
  echo "  install-db       Crear base de datos desde cero (install.php)"
  echo "  migrate          Ejecutar migraciones (migrate.php)"
  echo ""
  echo -e "${BOLD}Mantenimiento:${NC}"
  echo "  clean            Limpiar node_modules, caché, target/"
  echo "  status           Estado del proyecto (archivos, tamaños, git)"
  echo "  deps             Verificar dependencias instaladas"
  echo ""
  echo -e "${BOLD}Ejemplos:${NC}"
  echo "  ./labsim.sh dev"
  echo "  ./labsim.sh build --no-bundle"
  echo "  ./labsim.sh migrate"
  echo "  ./labsim.sh status"
  echo ""
}

# ═══════════════════════════════════════════════════════
#  ROUTER
# ═══════════════════════════════════════════════════════

case "${1:-help}" in
  dev)        cmd_dev ;;
  build)      cmd_build "$2" ;;
  check)      cmd_check ;;
  migrate)    cmd_migrate ;;
  install-db) cmd_install_db ;;
  clean)      cmd_clean ;;
  status)     cmd_status ;;
  deps)       cmd_deps ;;
  help|--help|-h) cmd_help ;;
  *)
    echo -e "${RED}Comando desconocido:${NC} $1"
    cmd_help
    exit 1
    ;;
esac
