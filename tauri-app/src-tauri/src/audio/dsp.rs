/// Convierte dB (amplitud) a factor lineal
pub fn db_to_lin(db: f32) -> f32 {
    10.0_f32.powf(db / 20.0)
}

/// Aplica fade in/out lineal para evitar clics
pub fn apply_envelope(signal: &mut [f32], sample_rate: u32, attack_ms: f32, release_ms: f32) {
    let n = signal.len();
    let a = ((sample_rate as f32 * attack_ms / 1000.0) as usize).min(n);
    let r = ((sample_rate as f32 * release_ms / 1000.0) as usize).min(n);

    // Fade in
    for i in 0..a {
        signal[i] *= i as f32 / a as f32;
    }
    // Fade out
    for i in 0..r {
        let idx = n - 1 - i;
        signal[idx] *= i as f32 / r as f32;
    }
}

/// Coeficientes biquad bandpass (RBJ cookbook)
pub fn biquad_bandpass_coeffs(fc: f32, q: f32, sr: u32) -> BiquadCoeffs {
    let w0 = 2.0 * std::f32::consts::PI * fc / sr as f32;
    let alpha = w0.sin() / (2.0 * q);
    let cos_w0 = w0.cos();
    BiquadCoeffs {
        b0: q * alpha,
        b1: 0.0,
        b2: -q * alpha,
        a0: 1.0 + alpha,
        a1: -2.0 * cos_w0,
        a2: 1.0 - alpha,
    }
}

pub struct BiquadCoeffs {
    pub b0: f32,
    pub b1: f32,
    pub b2: f32,
    pub a0: f32,
    pub a1: f32,
    pub a2: f32,
}

/// Filtro biquad IIR Direct Form I (mono)
pub struct Biquad {
    b0: f32,
    b1: f32,
    b2: f32,
    a1: f32,
    a2: f32,
    x1: f32,
    x2: f32,
    y1: f32,
    y2: f32,
}

impl Biquad {
    pub fn new(coeffs: BiquadCoeffs) -> Self {
        let a0 = coeffs.a0;
        Self {
            b0: coeffs.b0 / a0,
            b1: coeffs.b1 / a0,
            b2: coeffs.b2 / a0,
            a1: coeffs.a1 / a0,
            a2: coeffs.a2 / a0,
            x1: 0.0,
            x2: 0.0,
            y1: 0.0,
            y2: 0.0,
        }
    }

    pub fn process(&mut self, input: &[f32], output: &mut [f32]) {
        for i in 0..input.len() {
            let xi = input[i];
            let yi = self.b0 * xi + self.b1 * self.x1 + self.b2 * self.x2
                - self.a1 * self.y1 - self.a2 * self.y2;
            output[i] = yi;
            self.x2 = self.x1;
            self.x1 = xi;
            self.y2 = self.y1;
            self.y1 = yi;
        }
    }
}
