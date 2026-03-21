use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::StreamConfig;
use std::sync::mpsc;
use std::sync::{Arc, atomic::{AtomicBool, Ordering}};

use crate::audio::signals::Signal;

pub struct AudioBackend {
    device: cpal::Device,
    config: StreamConfig,
    playing: Arc<AtomicBool>,
    stop_tx: Option<mpsc::Sender<()>>,
}

// cpal::Device is Send on Linux/macOS
unsafe impl Send for AudioBackend {}

impl AudioBackend {
    pub fn new() -> Result<Self, String> {
        let host = cpal::default_host();
        let device = host
            .default_output_device()
            .ok_or("No se encontró dispositivo de audio")?;
        let supported = device
            .default_output_config()
            .map_err(|e| format!("Error config audio: {}", e))?;

        let config: StreamConfig = supported.into();

        Ok(Self {
            device,
            config,
            playing: Arc::new(AtomicBool::new(false)),
            stop_tx: None,
        })
    }

    pub fn sample_rate(&self) -> u32 {
        self.config.sample_rate.0
    }

    #[allow(dead_code)]
    pub fn is_playing(&self) -> bool {
        self.playing.load(Ordering::Relaxed)
    }

    pub fn stop(&mut self) {
        self.playing.store(false, Ordering::Relaxed);
        if let Some(tx) = self.stop_tx.take() {
            let _ = tx.send(());
        }
    }

    pub fn play(&mut self, mut signal: Box<dyn Signal>) -> Result<(), String> {
        self.stop(); // Stop any current playback

        let sample_rate = self.config.sample_rate.0;
        let channels = self.config.channels as usize;
        let playing = self.playing.clone();
        playing.store(true, Ordering::Relaxed);

        let (stop_tx, stop_rx) = mpsc::channel();
        self.stop_tx = Some(stop_tx);

        // Pre-generate blocks in a buffer channel
        let (block_tx, block_rx) = mpsc::sync_channel::<Vec<f32>>(4);

        // Producer thread: generate signal blocks
        let playing_prod = playing.clone();
        std::thread::spawn(move || {
            while playing_prod.load(Ordering::Relaxed) {
                match signal.next_block(sample_rate) {
                    Some(block) => {
                        if block_tx.send(block).is_err() {
                            break;
                        }
                    }
                    None => break,
                }
            }
            playing_prod.store(false, Ordering::Relaxed);
        });

        // Audio callback reads from channel
        let playing_cb = playing.clone();
        let mut buffer: Vec<f32> = Vec::new();
        let mut buf_pos = 0;

        let stream = self.device
            .build_output_stream(
                &self.config,
                move |data: &mut [f32], _: &cpal::OutputCallbackInfo| {
                    for frame in data.chunks_mut(channels) {
                        if buf_pos >= buffer.len() {
                            // Need more data
                            match block_rx.try_recv() {
                                Ok(new_block) => {
                                    buffer = new_block;
                                    buf_pos = 0;
                                }
                                Err(_) => {
                                    // No data available
                                    for s in frame.iter_mut() {
                                        *s = 0.0;
                                    }
                                    if !playing_cb.load(Ordering::Relaxed) {
                                        return;
                                    }
                                    continue;
                                }
                            }
                        }

                        let sample = if buf_pos < buffer.len() {
                            buffer[buf_pos].clamp(-0.9999, 0.9999)
                        } else {
                            0.0
                        };
                        buf_pos += 1;

                        // Write same sample to all channels (mono -> stereo)
                        for s in frame.iter_mut() {
                            *s = sample;
                        }
                    }
                },
                move |err| {
                    log::error!("Error stream audio: {}", err);
                },
                None,
            )
            .map_err(|e| format!("Error creando stream: {}", e))?;

        stream.play().map_err(|e| format!("Error play: {}", e))?;

        // Wrap stream in a Send-safe container
        #[allow(dead_code)]
        struct SendStream(cpal::Stream);
        unsafe impl Send for SendStream {}

        let send_stream = SendStream(stream);

        // Wait for completion or stop signal
        let playing_wait = playing.clone();
        std::thread::spawn(move || {
            loop {
                if stop_rx.try_recv().is_ok() || !playing_wait.load(Ordering::Relaxed) {
                    break;
                }
                std::thread::sleep(std::time::Duration::from_millis(50));
            }
            drop(send_stream);
            playing_wait.store(false, Ordering::Relaxed);
        });

        Ok(())
    }
}
