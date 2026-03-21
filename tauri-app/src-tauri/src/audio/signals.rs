use crate::audio::dsp::*;
use rand::Rng;

/// Box-Muller transform for gaussian random numbers
fn rand_normal(rng: &mut impl Rng) -> f32 {
    let u1: f32 = rng.random::<f32>().max(1e-10);
    let u2: f32 = rng.random::<f32>();
    (-2.0 * u1.ln()).sqrt() * (2.0 * std::f32::consts::PI * u2).cos()
}

/// Trait para generadores de señal por bloques
pub trait Signal: Send {
    /// Genera el siguiente bloque de muestras f32. Retorna None cuando termina.
    fn next_block(&mut self, sample_rate: u32) -> Option<Vec<f32>>;
}

// =====================
// Tono Puro
// =====================

pub struct PureTone {
    pub freq: f32,
    pub level_dbfs: f32,
    pub duration: f32,
    pub block_size: usize,
    pub pulsatile_hz: Option<f32>,
    pub duty_cycle: f32,
    pub fm_dev: f32,
    pub fm_rate: f32,
    pub attack_ms: f32,
    pub release_ms: f32,
    // State
    phase: f32,
    fm_phase: f32,
    emitted: usize,
    n_total: usize,
    first_block: bool,
}

impl PureTone {
    pub fn new(freq: f32, duration: f32, level_dbfs: f32) -> Self {
        Self {
            freq, duration, level_dbfs,
            block_size: 1024,
            pulsatile_hz: None,
            duty_cycle: 0.5,
            fm_dev: 0.0,
            fm_rate: 5.0,
            attack_ms: 5.0,
            release_ms: 5.0,
            phase: 0.0,
            fm_phase: 0.0,
            emitted: 0,
            n_total: 0,
            first_block: true,
        }
    }

    pub fn with_pulsatile(mut self, hz: f32, duty: f32) -> Self {
        self.pulsatile_hz = Some(hz);
        self.duty_cycle = duty;
        self
    }
}

impl Signal for PureTone {
    fn next_block(&mut self, sample_rate: u32) -> Option<Vec<f32>> {
        if self.first_block {
            self.n_total = (self.duration * sample_rate as f32) as usize;
            self.first_block = false;
        }
        if self.emitted >= self.n_total {
            return None;
        }

        let n = (self.n_total - self.emitted).min(self.block_size);
        let amp = db_to_lin(self.level_dbfs);
        let sr = sample_rate as f32;
        let pi2 = 2.0 * std::f32::consts::PI;
        let phase_inc = pi2 * self.freq / sr;

        let mut block = vec![0.0_f32; n];

        if self.fm_dev != 0.0 {
            let _fm_inc = pi2 * self.fm_rate / sr;
            for i in 0..n {
                let t = (self.emitted + i) as f32 / sr;
                let inst_freq = self.freq + self.fm_dev * (pi2 * self.fm_rate * t + self.fm_phase).sin();
                self.phase += pi2 * inst_freq / sr;
                block[i] = self.phase.sin() * amp;
            }
            self.fm_phase = (self.fm_phase + pi2 * self.fm_rate * n as f32 / sr) % pi2;
        } else {
            for i in 0..n {
                block[i] = (self.phase + phase_inc * i as f32).sin() * amp;
            }
            self.phase = (self.phase + phase_inc * n as f32) % pi2;
        }

        // Pulsatile (PWM on/off)
        if let Some(pulse_hz) = self.pulsatile_hz {
            if pulse_hz > 0.0 {
                for i in 0..n {
                    let t = (self.emitted + i) as f32 / sr;
                    let phase_in_cycle = (t * pulse_hz) % 1.0;
                    if phase_in_cycle >= self.duty_cycle {
                        block[i] = 0.0;
                    }
                }
            }
        }

        // Envelope on first/last block
        let is_last = self.emitted + n >= self.n_total;
        if self.emitted == 0 || is_last {
            apply_envelope(&mut block, sample_rate, self.attack_ms, self.release_ms);
        }

        self.emitted += n;
        Some(block)
    }
}

// =====================
// Ruido Blanco
// =====================

pub struct WhiteNoise {
    pub level_dbfs: f32,
    pub duration: f32,
    pub block_size: usize,
    emitted: usize,
    n_total: usize,
    first_block: bool,
}

impl WhiteNoise {
    pub fn new(duration: f32, level_dbfs: f32) -> Self {
        Self {
            duration, level_dbfs,
            block_size: 1024,
            emitted: 0, n_total: 0, first_block: true,
        }
    }
}

impl Signal for WhiteNoise {
    fn next_block(&mut self, sample_rate: u32) -> Option<Vec<f32>> {
        if self.first_block {
            self.n_total = (self.duration * sample_rate as f32) as usize;
            self.first_block = false;
        }
        if self.emitted >= self.n_total { return None; }

        let n = (self.n_total - self.emitted).min(self.block_size);
        let amp = db_to_lin(self.level_dbfs);
        let mut rng = rand::rng();
        let mut block: Vec<f32> = (0..n).map(|_| rand_normal(&mut rng) * amp).collect();

        let is_last = self.emitted + n >= self.n_total;
        if self.emitted == 0 || is_last {
            apply_envelope(&mut block, sample_rate, 5.0, 5.0);
        }
        self.emitted += n;
        Some(block)
    }
}

// =====================
// Ruido Rosa (Voss-McCartney)
// =====================

pub struct PinkNoise {
    pub level_dbfs: f32,
    pub duration: f32,
    pub block_size: usize,
    n_rows: usize,
    rows: Vec<f32>,
    emitted: usize,
    n_total: usize,
    first_block: bool,
}

impl PinkNoise {
    pub fn new(duration: f32, level_dbfs: f32) -> Self {
        let n_rows = 16;
        let mut rng = rand::rng();
        let rows: Vec<f32> = (0..n_rows).map(|_| rng.random::<f32>()).collect();
        Self {
            duration, level_dbfs,
            block_size: 1024,
            n_rows, rows,
            emitted: 0, n_total: 0, first_block: true,
        }
    }
}

impl Signal for PinkNoise {
    fn next_block(&mut self, sample_rate: u32) -> Option<Vec<f32>> {
        if self.first_block {
            self.n_total = (self.duration * sample_rate as f32) as usize;
            self.first_block = false;
        }
        if self.emitted >= self.n_total { return None; }

        let n = (self.n_total - self.emitted).min(self.block_size);
        let amp = db_to_lin(self.level_dbfs);
        let mut rng = rand::rng();
        let mut block = vec![0.0_f32; n];

        for i in 0..n {
            let k = rng.random_range(0..self.n_rows);
            self.rows[k] = rng.random::<f32>();
            block[i] = self.rows.iter().sum::<f32>();
        }

        // Normalize
        let mean: f32 = block.iter().sum::<f32>() / n as f32;
        let std: f32 = (block.iter().map(|x| (x - mean).powi(2)).sum::<f32>() / n as f32).sqrt() + 1e-8;
        for x in block.iter_mut() {
            *x = (*x - mean) / std * amp;
        }

        let is_last = self.emitted + n >= self.n_total;
        if self.emitted == 0 || is_last {
            apply_envelope(&mut block, sample_rate, 5.0, 5.0);
        }
        self.emitted += n;
        Some(block)
    }
}

// =====================
// Speech-Shaped Noise
// =====================

pub struct SpeechNoise {
    white: WhiteNoise,
    hp: Biquad,
    bp: Biquad,
    lp: Biquad,
}

impl SpeechNoise {
    pub fn new(duration: f32, level_dbfs: f32, sample_rate: u32) -> Self {
        let hp = Biquad::new(biquad_bandpass_coeffs(200.0, 0.5, sample_rate));
        let bp = Biquad::new(biquad_bandpass_coeffs(1000.0, 0.7, sample_rate));
        let lp = Biquad::new(biquad_bandpass_coeffs(6000.0, 0.5, sample_rate));
        Self {
            white: WhiteNoise::new(duration, level_dbfs),
            hp, bp, lp,
        }
    }
}

impl Signal for SpeechNoise {
    fn next_block(&mut self, sample_rate: u32) -> Option<Vec<f32>> {
        let block = self.white.next_block(sample_rate)?;
        let n = block.len();

        let mut hp_out = vec![0.0_f32; n];
        let mut bp_out = vec![0.0_f32; n];
        let mut lp_out = vec![0.0_f32; n];

        self.hp.process(&block, &mut hp_out);
        self.bp.process(&block, &mut bp_out);
        self.lp.process(&block, &mut lp_out);

        let mut result = vec![0.0_f32; n];
        let mut max_abs = 0.0_f32;
        for i in 0..n {
            result[i] = hp_out[i] + 1.5 * bp_out[i] + 0.6 * lp_out[i];
            max_abs = max_abs.max(result[i].abs());
        }
        // Normalize
        let norm = 1.0 / (max_abs + 1e-8);
        for x in result.iter_mut() {
            *x *= norm;
        }

        Some(result)
    }
}

// =====================
// Raw Samples (TTS output)
// =====================

pub struct RawSamplesSignal {
    samples: Vec<f32>,
    source_rate: u32,
    pos: f64,
    block_size: usize,
}

impl RawSamplesSignal {
    pub fn new(samples: Vec<f32>, source_rate: u32) -> Self {
        Self {
            samples,
            source_rate,
            pos: 0.0,
            block_size: 1024,
        }
    }
}

impl Signal for RawSamplesSignal {
    fn next_block(&mut self, sample_rate: u32) -> Option<Vec<f32>> {
        let src_len = self.samples.len();
        if src_len == 0 || self.pos >= src_len as f64 {
            return None;
        }

        let ratio = self.source_rate as f64 / sample_rate as f64;
        let mut block = Vec::with_capacity(self.block_size);

        for _ in 0..self.block_size {
            if self.pos >= src_len as f64 {
                break;
            }

            let idx = self.pos as usize;
            let frac = self.pos - idx as f64;

            // Linear interpolation for resampling
            let sample = if idx + 1 < src_len {
                self.samples[idx] as f64 * (1.0 - frac) + self.samples[idx + 1] as f64 * frac
            } else {
                self.samples[idx] as f64
            };

            block.push(sample as f32);
            self.pos += ratio;
        }

        if block.is_empty() {
            None
        } else {
            Some(block)
        }
    }
}

// =====================
// Narrow Band Noise
// =====================

pub struct NarrowBandNoise {
    white: WhiteNoise,
    filter: Biquad,
}

impl NarrowBandNoise {
    pub fn new(center_hz: f32, bandwidth_hz: f32, duration: f32, level_dbfs: f32, sample_rate: u32) -> Self {
        let q = (center_hz / bandwidth_hz.max(1.0)).max(0.1);
        let filter = Biquad::new(biquad_bandpass_coeffs(center_hz, q, sample_rate));
        Self {
            white: WhiteNoise::new(duration, level_dbfs),
            filter,
        }
    }
}

impl Signal for NarrowBandNoise {
    fn next_block(&mut self, sample_rate: u32) -> Option<Vec<f32>> {
        let block = self.white.next_block(sample_rate)?;
        let n = block.len();
        let mut result = vec![0.0_f32; n];
        self.filter.process(&block, &mut result);

        // Light normalization
        let max_abs = result.iter().map(|x| x.abs()).fold(0.0_f32, f32::max);
        let norm = 1.0 / (max_abs + 1e-6);
        for x in result.iter_mut() {
            *x *= norm;
        }

        Some(result)
    }
}
