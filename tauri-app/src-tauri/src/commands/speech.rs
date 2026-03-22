use tauri::State;
use crate::speech::SpeechState;
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::sync::{Arc, Mutex, atomic::{AtomicBool, Ordering}};

// Recording state
pub struct RecordingState {
    pub is_recording: Arc<AtomicBool>,
    pub samples: Arc<Mutex<Vec<f32>>>,
}

impl RecordingState {
    pub fn new() -> Self {
        Self {
            is_recording: Arc::new(AtomicBool::new(false)),
            samples: Arc::new(Mutex::new(Vec::new())),
        }
    }
}

#[tauri::command]
pub fn speech_status(speech: State<SpeechState>) -> bool {
    let engine = speech.engine.lock().unwrap();
    engine.is_loaded()
}

#[tauri::command]
pub async fn speech_load_model(speech: State<'_, SpeechState>) -> Result<bool, String> {
    let engine = speech.engine.clone();

    tauri::async_runtime::spawn_blocking(move || {
        let mut eng = engine.lock().unwrap();
        eng.load_model()
    })
    .await
    .map_err(|e| format!("Error en hilo: {}", e))??;

    Ok(true)
}

#[tauri::command]
pub fn speech_start_recording(recording: State<RecordingState>) -> Result<(), String> {
    if recording.is_recording.load(Ordering::Relaxed) {
        return Ok(()); // Already recording
    }

    // Clear previous samples
    recording.samples.lock().unwrap().clear();
    recording.is_recording.store(true, Ordering::Relaxed);

    let is_rec = recording.is_recording.clone();
    let samples = recording.samples.clone();

    std::thread::spawn(move || {
        let host = cpal::default_host();
        let device = match host.default_input_device() {
            Some(d) => d,
            None => { log::error!("No input device"); return; }
        };

        let config = cpal::StreamConfig {
            channels: 1,
            sample_rate: cpal::SampleRate(16000),
            buffer_size: cpal::BufferSize::Default,
        };

        let samples_clone = samples.clone();
        let is_rec_clone = is_rec.clone();

        let stream = device.build_input_stream(
            &config,
            move |data: &[f32], _: &cpal::InputCallbackInfo| {
                if is_rec_clone.load(Ordering::Relaxed) {
                    samples_clone.lock().unwrap().extend_from_slice(data);
                }
            },
            |err| log::error!("Error input stream: {}", err),
            None,
        );

        match stream {
            Ok(s) => {
                s.play().ok();
                while is_rec.load(Ordering::Relaxed) {
                    std::thread::sleep(std::time::Duration::from_millis(50));
                }
                drop(s);
            }
            Err(e) => log::error!("Error creating input stream: {}", e),
        }
    });

    Ok(())
}

#[tauri::command]
pub fn speech_stop_recording(recording: State<RecordingState>) -> Result<usize, String> {
    recording.is_recording.store(false, Ordering::Relaxed);
    std::thread::sleep(std::time::Duration::from_millis(100));
    let len = recording.samples.lock().unwrap().len();
    Ok(len)
}

#[tauri::command]
pub async fn speech_transcribe(
    speech: State<'_, SpeechState>,
    recording: State<'_, RecordingState>,
    language: String,
) -> Result<String, String> {
    let engine = speech.engine.clone();
    let samples = recording.samples.lock().unwrap().clone();

    if samples.is_empty() {
        return Err("No hay audio grabado".to_string());
    }

    tauri::async_runtime::spawn_blocking(move || {
        let mut eng = engine.lock().unwrap();
        eng.transcribe(&samples, &language)
    })
    .await
    .map_err(|e| format!("Error en hilo: {}", e))?
}

#[tauri::command]
pub fn speech_is_recording(recording: State<RecordingState>) -> bool {
    recording.is_recording.load(Ordering::Relaxed)
}
