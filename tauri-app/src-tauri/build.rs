fn copy_espeak_data() {
    use std::path::PathBuf;

    let out_dir = std::env::var("OUT_DIR").unwrap();
    let profile = std::env::var("PROFILE").unwrap_or_else(|_| "debug".to_string());

    // Encontrar espeak-ng-data compilado por espeak-rs-sys dentro de OUT_DIR ancestors
    let mut search = PathBuf::from(&out_dir);
    let mut espeak_data_src: Option<PathBuf> = None;
    // Buscar hacia arriba en el árbol de build
    for _ in 0..10 {
        let candidate = search.join("espeak-ng-data");
        if candidate.exists() && candidate.is_dir() {
            espeak_data_src = Some(candidate);
            break;
        }
        // También buscar dentro de share/ (cmake suele poner ahí)
        let share_candidate = search.join("share").join("espeak-ng-data");
        if share_candidate.exists() && share_candidate.is_dir() {
            espeak_data_src = Some(share_candidate);
            break;
        }
        if !search.pop() {
            break;
        }
    }

    // También buscar en el build dir de espeak-rs-sys (share/espeak-ng-data)
    if espeak_data_src.is_none() {
        let out_path = PathBuf::from(&out_dir);
        // OUT_DIR suele ser target/<profile>/build/<pkg>/out
        // espeak-rs-sys genera espeak-ng-data en su propio OUT_DIR/share/
        if let Some(build_root) = out_path.ancestors().nth(3) {
            // Buscar en subdirectorios del build
            if let Ok(entries) = std::fs::read_dir(build_root) {
                for entry in entries.flatten() {
                    if entry.file_name().to_string_lossy().starts_with("espeak-rs-sys") {
                        let candidate = entry.path().join("out").join("share").join("espeak-ng-data");
                        if candidate.exists() && candidate.join("phondata").exists() {
                            espeak_data_src = Some(candidate);
                            break;
                        }
                    }
                }
            }
        }
    }

    if let Some(src) = espeak_data_src {
        // Destino: junto al ejecutable final
        let target_dir = PathBuf::from(&out_dir)
            .ancestors()
            .find(|p| p.ends_with(&profile))
            .map(|p| p.to_path_buf())
            .unwrap_or_else(|| PathBuf::from(&out_dir));
        let dst = target_dir.join("espeak-ng-data");

        if !dst.exists() || !dst.join("phondata").exists() {
            println!("cargo:warning=Copiando espeak-ng-data a {}", dst.display());
            copy_dir_recursive(&src, &dst);
        }
    } else {
        println!("cargo:warning=espeak-ng-data no encontrado en build dir, TTS puede fallar en runtime");
    }
}

fn copy_dir_recursive(src: &std::path::Path, dst: &std::path::Path) {
    std::fs::create_dir_all(dst).ok();
    if let Ok(entries) = std::fs::read_dir(src) {
        for entry in entries.flatten() {
            let src_path = entry.path();
            let dst_path = dst.join(entry.file_name());
            if src_path.is_dir() {
                copy_dir_recursive(&src_path, &dst_path);
            } else {
                std::fs::copy(&src_path, &dst_path).ok();
            }
        }
    }
}

fn main() {
  // Compile espeak-ng audio stubs (piper uses espeak only for phonemization)
  cc::Build::new()
    .file("espeak_audio_stubs.c")
    .compile("espeak_audio_stubs");

  // Copiar espeak-ng-data junto al ejecutable para Windows/distribución
  copy_espeak_data();

  tauri_build::build()
}
