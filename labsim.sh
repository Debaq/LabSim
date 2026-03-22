#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════
#  LabSim 3.0 — Script de gestión interactivo
# ═══════════════════════════════════════════════════════

ROOT="$(cd "$(dirname "$0")" && pwd)"
APP="$ROOT/tauri-app"
BACKEND="$ROOT/labsim-backend"
OUTPUT="$ROOT/output"
TARGET="${CARGO_TARGET_DIR:-$APP/src-tauri/target}"

# ─── Colores ──────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }
info() { echo -e "  ${DIM}→${NC} $1"; }
warn() { echo -e "  ${YELLOW}!${NC} $1"; }

pause() {
  echo ""
  echo -e "  ${DIM}Presiona Enter para volver al menú...${NC}"
  read -r
}

# ─── Instalar dependencias npm si faltan ──────────────
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
  ensure_deps
  free_port 1420
  echo ""
  info "Frontend: http://localhost:1420"
  info "Hot reload activo"
  info "Ctrl+C para detener"
  echo ""
  (cd "$APP" && npx tauri dev)
}

cmd_build() {
  ensure_deps

  info "Verificando TypeScript..."
  if ! (cd "$APP" && npx tsc --noEmit); then
    fail "TypeScript tiene errores"
    return
  fi
  ok "TypeScript OK"

  info "Compilando sidecars (LLM + Speech)..."
  if ! (cd "$APP" && node scripts/build-sidecars.mjs); then
    fail "Build de sidecars falló"
    return
  fi
  ok "Sidecars compilados"

  info "Compilando frontend + backend..."
  if ! (cd "$APP" && npx tauri build); then
    fail "Build falló"
    return
  fi
  ok "Build completado"

  # Crear carpeta output con fecha
  local timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
  local out_dir="$OUTPUT/$timestamp"
  mkdir -p "$out_dir"

  # Copiar binario
  local bin=""
  for name in labsim LabSim lab-sim; do
    if [ -f "$TARGET/release/$name" ]; then
      bin="$TARGET/release/$name"
      break
    fi
  done
  if [ -n "$bin" ]; then
    cp "$bin" "$out_dir/"
    local bname=$(basename "$bin")
    local size=$(du -h "$out_dir/$bname" | cut -f1)
    ok "Binario: $size → output/$timestamp/$bname"
  else
    warn "No se encontró binario en $TARGET/release/"
  fi

  # Copiar paquetes
  local bundle_dir="$TARGET/release/bundle"
  if [ -d "$bundle_dir" ]; then
    find "$bundle_dir" -maxdepth 2 -type f \( -name "*.deb" -o -name "*.AppImage" -o -name "*.rpm" -o -name "*.dmg" -o -name "*.msi" \) 2>/dev/null | while read -r f; do
      cp "$f" "$out_dir/"
      local name=$(basename "$f")
      local size=$(du -h "$out_dir/$name" | cut -f1)
      ok "Paquete: $size → output/$timestamp/$name"
    done
  fi

  echo ""
  ok "Salida en: output/$timestamp/"

  # Listar builds anteriores
  local count=$(find "$OUTPUT" -maxdepth 1 -type d | tail -n +2 | wc -l)
  if [ "$count" -gt 1 ]; then
    info "$count builds en output/"
  fi
}

cmd_build_fast() {
  ensure_deps

  info "Verificando TypeScript..."
  if ! (cd "$APP" && npx tsc --noEmit); then
    fail "TypeScript tiene errores"
    return
  fi
  ok "TypeScript OK"

  info "Compilando sidecars (LLM + Speech)..."
  if ! (cd "$APP" && node scripts/build-sidecars.mjs); then
    fail "Build de sidecars falló"
    return
  fi
  ok "Sidecars compilados"

  info "Compilando solo binario (sin empaquetar)..."
  if ! (cd "$APP" && npx tauri build --no-bundle); then
    fail "Build falló"
    return
  fi

  local timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
  local out_dir="$OUTPUT/$timestamp"
  mkdir -p "$out_dir"

  local bin=""
  for name in labsim LabSim lab-sim; do
    if [ -f "$TARGET/release/$name" ]; then
      bin="$TARGET/release/$name"
      break
    fi
  done
  if [ -n "$bin" ]; then
    cp "$bin" "$out_dir/"
    local bname=$(basename "$bin")
    local size=$(du -h "$out_dir/$bname" | cut -f1)
    ok "Binario: $size → output/$timestamp/$bname"
  else
    warn "No se encontró binario en $TARGET/release/"
  fi
}

cmd_check() {
  info "TypeScript..."
  if (cd "$APP" && npx tsc --noEmit 2>&1); then
    ok "TypeScript OK"
  else
    fail "TypeScript tiene errores"
  fi

  info "Rust..."
  if (cd "$APP/src-tauri" && cargo build 2>&1 | tail -1); then
    ok "Rust OK"
  else
    fail "Rust tiene errores"
  fi

  echo ""
  ok "Todo compila correctamente"
}

cmd_clean() {
  echo ""
  echo -e "  ${BOLD}¿Qué limpiar?${NC}"
  echo ""
  echo "    1) node_modules + caché Vite"
  echo "    2) target/ (build cache Rust)"
  echo "    3) output/ (builds generados)"
  echo "    4) Todo"
  echo "    0) Cancelar"
  echo ""
  echo -ne "  ${CYAN}→${NC} "
  read -r choice

  case $choice in
    1)
      [ -d "$APP/node_modules" ] && rm -rf "$APP/node_modules" && ok "node_modules eliminado"
      [ -d "$APP/.vite" ] && rm -rf "$APP/.vite" && ok "Caché Vite eliminado"
      ;;
    2)
      local target="$TARGET"
      if [ -d "$target" ]; then
        local size=$(du -sh "$target" | cut -f1)
        warn "target/ ocupa $size"
        rm -rf "$target"
        ok "target/ eliminado"
      else
        info "target/ no existe"
      fi
      ;;
    3)
      if [ -d "$OUTPUT" ]; then
        local size=$(du -sh "$OUTPUT" | cut -f1)
        local count=$(find "$OUTPUT" -maxdepth 1 -type d | tail -n +2 | wc -l)
        warn "output/ tiene $count builds ($size)"
        rm -rf "$OUTPUT"
        ok "output/ eliminado"
      else
        info "output/ no existe"
      fi
      ;;
    4)
      [ -d "$APP/node_modules" ] && rm -rf "$APP/node_modules" && ok "node_modules eliminado"
      [ -d "$APP/.vite" ] && rm -rf "$APP/.vite" && ok "Caché Vite eliminado"
      [ -d "$TARGET" ] && rm -rf "$TARGET" && ok "target/ eliminado"
      [ -d "$OUTPUT" ] && rm -rf "$OUTPUT" && ok "output/ eliminado"
      ;;
    *) info "Cancelado" ;;
  esac
}

cmd_status() {
  # Git
  local branch=$(git -C "$ROOT" branch --show-current 2>/dev/null || echo "?")
  local commit=$(git -C "$ROOT" log --oneline -1 2>/dev/null || echo "?")
  local dirty=$(git -C "$ROOT" status --porcelain 2>/dev/null | wc -l)

  echo ""
  echo -e "  ${BOLD}Git${NC}"
  info "Branch: ${CYAN}$branch${NC}"
  info "Commit: $commit"
  [ "$dirty" -gt 0 ] && warn "$dirty archivos sin commitear" || ok "Limpio"

  # Archivos
  local ts_files=$(find "$APP/src" -name "*.tsx" -o -name "*.ts" 2>/dev/null | grep -v node_modules | wc -l)
  local rs_files=$(find "$APP/src-tauri/src" -name "*.rs" 2>/dev/null | wc -l)
  local php_files=$(find "$BACKEND" -name "*.php" 2>/dev/null | wc -l)
  local modules=$(find "$APP/src/modules" -maxdepth 1 -type d 2>/dev/null | tail -n +2 | wc -l)
  local windows=$(find "$APP/src/components/windows" -name "*-window.tsx" -o -name "*-placeholder.tsx" 2>/dev/null | wc -l)

  echo ""
  echo -e "  ${BOLD}Código${NC}"
  info "TypeScript/TSX: ${CYAN}$ts_files${NC} archivos"
  info "Rust: ${CYAN}$rs_files${NC} archivos"
  info "PHP: ${CYAN}$php_files${NC} archivos"
  info "Módulos clínicos: ${CYAN}$modules${NC}"
  info "Ventanas: ${CYAN}$windows${NC}"

  # Tamaños
  local app_size=$(du -sh "$APP/src" 2>/dev/null | cut -f1)
  local rust_size=$(du -sh "$APP/src-tauri/src" 2>/dev/null | cut -f1)
  local backend_size=$(du -sh "$BACKEND" 2>/dev/null | cut -f1)

  echo ""
  echo -e "  ${BOLD}Tamaños${NC}"
  info "Frontend: $app_size"
  info "Rust: $rust_size"
  info "Backend: $backend_size"

  [ -d "$TARGET" ] && info "Build cache: $(du -sh "$TARGET" | cut -f1)"
  [ -d "$APP/node_modules" ] && info "node_modules: $(du -sh "$APP/node_modules" | cut -f1)"

  if [ -d "$OUTPUT" ]; then
    local builds=$(find "$OUTPUT" -maxdepth 1 -type d | tail -n +2 | wc -l)
    info "Builds: $builds en output/"
  fi
}

cmd_deps() {
  echo ""
  for cmd in node npm cargo rustc php git; do
    if command -v "$cmd" >/dev/null 2>&1; then
      local ver=$("$cmd" --version 2>/dev/null | head -1)
      ok "$cmd — $ver"
    else
      fail "$cmd — no encontrado"
    fi
  done
}

# ═══════════════════════════════════════════════════════
#  MENÚ INTERACTIVO
# ═══════════════════════════════════════════════════════

show_menu() {
  clear
  echo ""
  echo -e "  ${CYAN}╔══════════════════════════════════════╗${NC}"
  echo -e "  ${CYAN}║${NC}        ${BOLD}LabSim 3.0${NC}                   ${CYAN}║${NC}"
  echo -e "  ${CYAN}║${NC}  ${DIM}Plataforma de Simulación Clínica${NC}   ${CYAN}║${NC}"
  echo -e "  ${CYAN}╚══════════════════════════════════════╝${NC}"
  echo ""
  echo -e "  ${BOLD}Desarrollo${NC}"
  echo -e "    ${GREEN}1${NC})  Modo desarrollo (hot reload)"
  echo -e "    ${GREEN}2${NC})  Verificar compilación"
  echo ""
  echo -e "  ${BOLD}Build${NC}"
  echo -e "    ${GREEN}3${NC})  Build completo (binario + paquetes)"
  echo -e "    ${GREEN}4${NC})  Build rápido (solo binario)"
  echo ""
  echo -e "  ${BOLD}Mantenimiento${NC}"
  echo -e "    ${GREEN}5${NC})  Estado del proyecto"
  echo -e "    ${GREEN}6${NC})  Verificar dependencias"
  echo -e "    ${GREEN}7${NC})  Limpiar"
  echo ""
  echo -e "    ${RED}0${NC})  Salir"
  echo ""
  echo -ne "  ${CYAN}→${NC} "
}

# ═══════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════

# Si se pasa un argumento, ejecutar directo (para CI/scripts)
if [ $# -gt 0 ]; then
  case "$1" in
    dev)         cmd_dev ;;
    build)       cmd_build ;;
    build-fast)  cmd_build_fast ;;
    check)       cmd_check ;;
    clean)       cmd_clean ;;
    status)      cmd_status ;;
    deps)        cmd_deps ;;
    *)           echo "Comando desconocido: $1"; exit 1 ;;
  esac
  exit 0
fi

# Modo interactivo
while true; do
  show_menu
  read -r choice

  case $choice in
    1)  cmd_dev; pause ;;
    2)  cmd_check; pause ;;
    3)  cmd_build; pause ;;
    4)  cmd_build_fast; pause ;;
    5)  cmd_status; pause ;;
    6)  cmd_deps; pause ;;
    7)  cmd_clean; pause ;;
    0)
      echo ""
      echo -e "  ${DIM}Hasta luego.${NC}"
      echo ""
      exit 0
      ;;
    *)
      warn "Opción inválida"
      sleep 1
      ;;
  esac
done
