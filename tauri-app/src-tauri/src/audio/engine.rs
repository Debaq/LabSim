use crate::audio::backend::AudioBackend;
use crate::audio::signals::*;
use std::sync::{Arc, Mutex};

pub struct AudioEngine {
    backend: Arc<Mutex<AudioBackend>>,
    sample_rate: u32,
}

impl AudioEngine {
    pub fn new() -> Result<Self, String> {
        let backend = AudioBackend::new()?;
        let sample_rate = backend.sample_rate();
        Ok(Self {
            backend: Arc::new(Mutex::new(backend)),
            sample_rate,
        })
    }

    #[allow(dead_code)]
    pub fn sample_rate(&self) -> u32 {
        self.sample_rate
    }

    pub fn play_tone(
        &self,
        freq: f32,
        duration: f32,
        level_dbfs: f32,
        pulsatile_hz: Option<f32>,
        duty_cycle: f32,
    ) -> Result<(), String> {
        let mut tone = PureTone::new(freq, duration, level_dbfs);
        if let Some(hz) = pulsatile_hz {
            tone = tone.with_pulsatile(hz, duty_cycle);
        }
        let mut backend = self.backend.lock().unwrap();
        backend.play(Box::new(tone))
    }

    pub fn play_white_noise(&self, duration: f32, level_dbfs: f32) -> Result<(), String> {
        let noise = WhiteNoise::new(duration, level_dbfs);
        let mut backend = self.backend.lock().unwrap();
        backend.play(Box::new(noise))
    }

    pub fn play_pink_noise(&self, duration: f32, level_dbfs: f32) -> Result<(), String> {
        let noise = PinkNoise::new(duration, level_dbfs);
        let mut backend = self.backend.lock().unwrap();
        backend.play(Box::new(noise))
    }

    pub fn play_speech_noise(&self, duration: f32, level_dbfs: f32) -> Result<(), String> {
        let noise = SpeechNoise::new(duration, level_dbfs, self.sample_rate);
        let mut backend = self.backend.lock().unwrap();
        backend.play(Box::new(noise))
    }

    pub fn play_nbn(
        &self,
        center_hz: f32,
        bandwidth_hz: f32,
        duration: f32,
        level_dbfs: f32,
    ) -> Result<(), String> {
        let noise = NarrowBandNoise::new(center_hz, bandwidth_hz, duration, level_dbfs, self.sample_rate);
        let mut backend = self.backend.lock().unwrap();
        backend.play(Box::new(noise))
    }

    pub fn play_raw_samples(&self, samples: Vec<f32>, source_sample_rate: u32) -> Result<(), String> {
        let signal = RawSamplesSignal::new(samples, source_sample_rate);
        let mut backend = self.backend.lock().unwrap();
        backend.play(Box::new(signal))
    }

    pub fn stop(&self) {
        let mut backend = self.backend.lock().unwrap();
        backend.stop();
    }

    #[allow(dead_code)]
    pub fn is_playing(&self) -> bool {
        let backend = self.backend.lock().unwrap();
        backend.is_playing()
    }
}
