#!/usr/bin/env node
/**
 * Build sidecar binaries and copy them to src-tauri/binaries/
 * with the correct target triple suffix for Tauri's externalBin.
 */
import { execSync } from 'child_process';
import { cpSync, mkdirSync, existsSync } from 'fs';
import { join, resolve } from 'path';

const ROOT = resolve(import.meta.dirname, '..');
const SRC_TAURI = join(ROOT, 'src-tauri');
const BINARIES_DIR = join(SRC_TAURI, 'binaries');

// Detect target triple
function getTargetTriple() {
  // If TAURI_ENV_TARGET_TRIPLE is set (by tauri-action), use it
  if (process.env.TAURI_ENV_TARGET_TRIPLE) {
    return process.env.TAURI_ENV_TARGET_TRIPLE;
  }

  const platform = process.platform;
  const arch = process.arch;

  if (platform === 'win32') {
    return arch === 'arm64' ? 'aarch64-pc-windows-msvc' : 'x86_64-pc-windows-msvc';
  } else if (platform === 'darwin') {
    return arch === 'arm64' ? 'aarch64-apple-darwin' : 'x86_64-apple-darwin';
  } else {
    return arch === 'arm64' ? 'aarch64-unknown-linux-gnu' : 'x86_64-unknown-linux-gnu';
  }
}

const triple = process.env.CARGO_BUILD_TARGET || getTargetTriple();
const ext = process.platform === 'win32' ? '.exe' : '';
const sidecars = ['sidecar-llm', 'sidecar-speech'];
const binaryNames = ['labsim-llm', 'labsim-speech'];

console.log(`Building sidecars for target: ${triple}`);

// Build all sidecars
const targetArgs = process.env.CARGO_BUILD_TARGET ? `--target ${triple}` : '';
const cmd = `cargo build -p sidecar-llm -p sidecar-speech --release ${targetArgs}`.trim();
console.log(`> ${cmd}`);
execSync(cmd, { cwd: SRC_TAURI, stdio: 'inherit' });

// Determine where cargo put the binaries
const cargoTarget = process.env.CARGO_TARGET_DIR || join(SRC_TAURI, 'target');
const releaseDir = process.env.CARGO_BUILD_TARGET
  ? join(cargoTarget, triple, 'release')
  : join(cargoTarget, 'release');

// Copy to binaries/ with triple suffix
mkdirSync(BINARIES_DIR, { recursive: true });

for (let i = 0; i < sidecars.length; i++) {
  const src = join(releaseDir, `${binaryNames[i]}${ext}`);
  const dst = join(BINARIES_DIR, `${binaryNames[i]}-${triple}${ext}`);

  if (!existsSync(src)) {
    console.error(`ERROR: ${src} not found`);
    process.exit(1);
  }

  cpSync(src, dst);
  console.log(`  ${binaryNames[i]} -> binaries/${binaryNames[i]}-${triple}${ext}`);
}

console.log('Sidecars ready.');
