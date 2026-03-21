fn main() {
  // Compile espeak-ng audio stubs (piper uses espeak only for phonemization)
  cc::Build::new()
    .file("espeak_audio_stubs.c")
    .compile("espeak_audio_stubs");

  tauri_build::build()
}
