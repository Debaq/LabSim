/**
 * TEOAEClinicalChartView - Vista de TEOAE Clínicas (determinística)
 * - Paneles de tiempo (A, B y A+B) por oído (OD / OI)
 * - Espectro tipo Fourier comparando Señal (A+B) vs Ruido (|A−B|/2)
 * - Usa waveforms reales si están en data.transientes_clinicas_waveforms
 * - Si no hay waveforms, sintetiza A/B de forma DETERMINÍSTICA basada en los SNR clínicos
 *   (seed a partir de los datos → mismas formas mientras no cambien)
 */

class TEOAEClinicalChartView {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.canvas = null;
        this.ctx = null;

        this.config = {
            margin: { top: 24, right: 24, bottom: 30, left: 42 },
            colors: {
                // Oídos
                od: '#dc3545',     // rojo
                oi: '#007bff',     // azul
                // Trazos A/B/A+B
                A: '#ff8f00',      // naranja
                B: '#9c27b0',      // morado
                AB: '#28a745',     // verde
                // Otros
                noise: '#666',
                grid: '#e0e0e0',
                gridMajor: '#c9c9c9',
                text: '#333',
                axis: '#555',
                panelBorder: '#e5e7eb'
            },
            // Layout: 2 filas de tiempo (OD/OI) + 1 fila de espectro
            layout: {
                timeRows: 2,
                spectrumRows: 1,
                rowGap: 12,
                timeHeightRatio: 0.58, // % del alto total para paneles de tiempo
            },
            synthesis: {
                defaultFs: 24000,            // Hz
                    durationMs: 12,              // ventana de ~12 ms
                    bandsHz: [1000, 1500, 2000, 3000, 4000], // bandas clínicas TEOAE
            }
        };

        // Caché determinística por oído
        this._cache = {
            od: { hash: null, A: null, B: null, sampleRate: null },
            oi: { hash: null, A: null, B: null, sampleRate: null }
        };
    }

    /**
     * Inicialización del canvas
     */
    init() {
        this.canvas = document.getElementById(this.canvasId);
        if (!this.canvas) {
            console.warn(`Canvas ${this.canvasId} no encontrado`);
            return false;
        }
        this.ctx = this.canvas.getContext('2d');
        return true;
    }

    /**
     * Render principal
     */
    render(data) {
        if (!this.init()) return;

        const { ctx, canvas } = this;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Dimensiones base
        const W = canvas.width;
        const H = canvas.height;
        const { margin, layout } = this.config;

        const innerW = W - margin.left - margin.right;
        const innerH = H - margin.top - margin.bottom;

        // Partición vertical: tiempo (arriba) + espectro (abajo)
        const timeAreaH = innerH * layout.timeHeightRatio;
        const spectrumAreaH = innerH - timeAreaH - layout.rowGap;

        // Paneles de tiempo (dos filas: OD, OI)
        const timeRowH = (timeAreaH - layout.rowGap) / layout.timeRows;

        const panels = {
            timeOD: { x: margin.left, y: margin.top, w: innerW, h: timeRowH },
            timeOI: { x: margin.left, y: margin.top + timeRowH + layout.rowGap, w: innerW, h: timeRowH },
            spectrum: { x: margin.left, y: margin.top + timeAreaH + layout.rowGap, w: innerW, h: spectrumAreaH }
        };

        // Preparar datos por oído: waveforms reales o síntesis determinística por SNR
        const prepared = this.prepareEarData(data);

        // ======== PANEL TIEMPO OD ========
        this.drawWavePanel(
            panels.timeOD,
            prepared.od.A,
            prepared.od.B,
            prepared.od.sampleRate,
            'OD  –  Respuestas A, B y A+B',
            this.config.colors
        );

        // ======== PANEL TIEMPO OI ========
        this.drawWavePanel(
            panels.timeOI,
            prepared.oi.A,
            prepared.oi.B,
            prepared.oi.sampleRate,
            'OI  –  Respuestas A, B y A+B',
            this.config.colors
        );

        // ======== PANEL ESPECTRO (Señal vs Ruido) ========
        const specOD = this.computeSignalNoiseSpectrum(prepared.od);
        const specOI = this.computeSignalNoiseSpectrum(prepared.oi);

        this.drawSpectrumPanel(panels.spectrum, specOD, specOI);

        // Leyenda global
        this.drawGlobalLegend(margin.left, margin.top - 8);
    }

    // =================== PREPARACIÓN DE DATOS ===================

    /**
     * Prepara datos por oído:
     * - Usa data.transientes_clinicas_waveforms si existe
     * - Si no, sintetiza de forma determinística a partir de los SNR clínicos
     */
    prepareEarData(data) {
        const wf = data?.transientes_clinicas_waveforms || {};
        const clinical = data?.transientes_clinicas || {};

        const od = this.prepareSingleEar(wf.oido_derecho, clinical?.oido_derecho, 'od');
        const oi = this.prepareSingleEar(wf.oido_izquierdo, clinical?.oido_izquierdo, 'oi');

        return { od, oi };
    }

    /**
     * Prepara datos de un oído: waveforms reales o síntesis determinística cacheada
     */
    prepareSingleEar(wfEar, clinicalEar, earKey) {
        const fs = wfEar?.sampleRate || this.config.synthesis.defaultFs;

        // Si hay waveforms reales, usarlas
        if (wfEar?.A?.length && wfEar?.B?.length) {
            const A = Float32Array.from(wfEar.A);
            const B = Float32Array.from(wfEar.B);
            return { A, B, sampleRate: fs, source: 'raw' };
        }

        // === SÍNTESIS DETERMINÍSTICA + CACHÉ ===
        const signature = this._serializeClinicalEar(clinicalEar);
        const hash = this._hashString(`${earKey}|${fs}|${signature}`);

        // Intentar cachear
        const slot = this._cache[earKey === 'od' ? 'od' : 'oi'];
        if (slot.hash === hash && slot.A && slot.B && slot.sampleRate === fs) {
            return { A: slot.A, B: slot.B, sampleRate: fs, source: 'synthetic-cached' };
        }

        // PRNG con seed estable
        const rnd = this._prng(hash);

        const duration = this.config.synthesis.durationMs / 1000;
        const N = Math.max(256, Math.floor(fs * duration));
        const { bandsHz } = this.config.synthesis;

        // Envelope TEOAE (decaimiento exponencial ~4 ms)
        const env = new Float32Array(N);
        const tau = 0.004;
        for (let n = 0; n < N; n++) {
            const t = n / fs;
            env[n] = Math.exp(-t / tau);
        }

        // Ganancias por banda desde SNR clínico (heurístico estático)
        const bandGains = bandsHz.map(f => {
            const snr = parseFloat(clinicalEar?.[String(f)]?.snr ?? '0') || 0;
            return Math.min(1.2, Math.max(0.2, (snr / 12)));
        });

        const A = new Float32Array(N);
        const B = new Float32Array(N);

        // Componer senoides por banda con fases determinísticas
        bandsHz.forEach((f, i) => {
            const w = 2 * Math.PI * f / fs;
            const g = bandGains[i];

            const phiA = rnd() * 2 * Math.PI;
            const phiB = rnd() * 2 * Math.PI;

            for (let n = 0; n < N; n++) {
                A[n] += env[n] * g * Math.sin(w * n + phiA);
                B[n] += env[n] * g * Math.sin(w * n + phiB);
            }
        });

        // Ruido de fondo determinístico
        for (let n = 0; n < N; n++) {
            A[n] += (rnd() - 0.5) * 0.02;
            B[n] += (rnd() - 0.5) * 0.02;
        }

        // Normalización suave
        const maxAbs = Math.max(this.maxAbs(A), this.maxAbs(B), 1e-6);
        const scale = 0.9 / maxAbs;
        for (let n = 0; n < N; n++) { A[n] *= scale; B[n] *= scale; }

        // Guardar en caché
        slot.hash = hash;
        slot.A = A;
        slot.B = B;
        slot.sampleRate = fs;

        return { A, B, sampleRate: fs, source: 'synthetic' };
    }

    // Serializa SNR/respuesta en orden de bandas para hashing determinístico
    _serializeClinicalEar(clinicalEar) {
        const bands = this.config.synthesis.bandsHz;
        const parts = bands.map(hz => {
            const k = String(hz);
            const snr = clinicalEar?.[k]?.snr ?? '';
            const resp = clinicalEar?.[k]?.respuesta ?? '';
            return `${k}:${snr}|${resp}`;
        });
        return parts.join(';');
    }

    // Hash simple 32-bit (tipo FNV-like)
    _hashString(str) {
        let h = 2166136261 >>> 0;
        for (let i = 0; i < str.length; i++) {
            h ^= str.charCodeAt(i);
            h = Math.imul(h, 16777619);
        }
        return h >>> 0;
    }

    // PRNG determinístico (mulberry32)
    _prng(seed) {
        let t = seed >>> 0;
        return function() {
            t += 0x6D2B79F5;
            let r = Math.imul(t ^ (t >>> 15), 1 | t);
            r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
            return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
        };
    }

    maxAbs(arr) {
        let m = 0;
        for (let i = 0; i < arr.length; i++) m = Math.max(m, Math.abs(arr[i]));
        return m;
    }

    // =================== DIBUJO: WAVEFORMS ===================

    drawWavePanel(panel, waveA, waveB, fs, title, colors) {
        const { ctx } = this;
        const { x, y, w, h } = panel;

        // Marco
        this.strokeRect(x, y, w, h, colors.panelBorder);

        // Ejes / grilla simple
        this.drawGridTime(x, y, w, h);

        // Título
        ctx.fillStyle = colors.text;
        ctx.font = 'bold 11px Arial';
        ctx.textAlign = 'left';
        ctx.fillText(title, x + 6, y + 14);

        // Área de ploteo (dejamos banda superior para título)
        const topPad = 20;
        const plotX = x + 6;
        const plotY = y + topPad;
        const plotW = w - 12;
        const plotH = h - topPad - 8;

        // Escala tiempo (0…N/fs)
        const N = Math.min(waveA.length, waveB.length);
        const tMax = N / fs;

        const xScale = (t) => plotX + (t / tMax) * plotW;

        // Escala amplitud (±1 normalizado)
        const yScale = (amp) => plotY + (1 - (amp + 1) / 2) * plotH;

        // A+B
        const AB = new Float32Array(N);
        for (let i = 0; i < N; i++) AB[i] = waveA[i] + waveB[i];

        // Trazos
        this.drawPolyline(waveA, fs, xScale, yScale, colors.A, 1.5);
        this.drawPolyline(waveB, fs, xScale, yScale, colors.B, 1.5);
        this.drawPolyline(AB, fs, xScale, yScale, colors.AB, 2.0);

        // Leyenda local
        this.drawMiniLegend(plotX + 6, plotY + 10, [
            { color: colors.A, label: 'A' },
            { color: colors.B, label: 'B' },
            { color: colors.AB, label: 'A+B' },
        ]);
    }

    drawPolyline(signal, fs, xScale, yScale, color, width = 1.5) {
        const { ctx } = this;

        ctx.save();
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = width;

        const N = signal.length;
        const step = Math.max(1, Math.floor(N / 1000)); // decimación para performance

        for (let i = 0; i < N; i += step) {
            const t = i / fs;
            const x = xScale(t);
            const y = yScale(signal[i]);

            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }

        ctx.stroke();
        ctx.restore();
    }

    drawGridTime(x, y, w, h) {
        const { ctx } = this;
        const grid = this.config.colors.grid;
        const major = this.config.colors.gridMajor;

        // Margen arriba para título
        const topPad = 20;
        const gy0 = y + topPad;
        const gh = h - topPad - 8;
        const gx0 = x + 6;
        const gw = w - 12;

        ctx.save();

        // Líneas horizontales (amp): -1, -0.5, 0, 0.5, 1
        [ -1, -0.5, 0, 0.5, 1 ].forEach(val => {
            const yy = gy0 + (1 - (val + 1) / 2) * gh;
            ctx.strokeStyle = val === 0 ? major : grid;
            ctx.beginPath();
            ctx.moveTo(gx0, yy);
            ctx.lineTo(gx0 + gw, yy);
            ctx.stroke();
        });

        // Verticales de tiempo (cada 2 ms en 12 ms)
        const msMarks = [0, 2, 4, 6, 8, 10, 12];
        msMarks.forEach(ms => {
            const xPos = gx0 + (ms / 12) * gw;
            ctx.strokeStyle = ms % 4 === 0 ? major : grid;
            ctx.beginPath();
            ctx.moveTo(xPos, gy0);
            ctx.lineTo(xPos, gy0 + gh);
            ctx.stroke();

            if (ms % 4 === 0) {
                ctx.fillStyle = this.config.colors.axis;
                ctx.font = '10px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(`${ms} ms`, xPos, gy0 + gh + 12);
            }
        });

        ctx.restore();
    }

    drawMiniLegend(x, y, items) {
        const { ctx } = this;
        ctx.save();
        ctx.font = '10px Arial';
        ctx.textAlign = 'left';
        let off = 0;
        items.forEach(it => {
            ctx.fillStyle = it.color;
            ctx.fillRect(x + off, y - 6, 10, 3);
            ctx.fillStyle = this.config.colors.text;
            ctx.fillText(` ${it.label}`, x + off + 12, y);
            off += 56;
        });
        ctx.restore();
    }

    strokeRect(x, y, w, h, color) {
        const { ctx } = this;
        ctx.save();
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, w, h);
        ctx.restore();
    }

    // =================== ESPECTRO SEÑAL vs RUIDO ===================

    computeSignalNoiseSpectrum(ear) {
        const { A, B, sampleRate: fs } = ear;
        const N = Math.min(A.length, B.length);
        const AB = new Float32Array(N);
        const noise = new Float32Array(N);

        for (let i = 0; i < N; i++) {
            AB[i] = A[i] + B[i];
            noise[i] = 0.5 * Math.abs(A[i] - B[i]); // estimación simple del ruido
        }

        const fftAB = this.simpleDFTMagnitude(AB);
        const fftNoise = this.simpleDFTMagnitude(noise);

        const freqs = new Float32Array(fftAB.length);
        const binHz = fs / (2 * (fftAB.length - 1)); // mapear 0..Nyquist a bins
        for (let k = 0; k < freqs.length; k++) freqs[k] = k * binHz;

        return { freqs, signalMag: fftAB, noiseMag: fftNoise, fs };
    }

    /**
     * DFT sencillo (magnitud) de mitad de espectro (0..Nyquist)
     * - Ventana Hann para reducir leakage
     * - Magnitud en dB relativos y normalizada al pico (0 dB)
     */
    simpleDFTMagnitude(signal) {
        const N = signal.length;
        const K = Math.floor(N / 2) + 1; // 0..Nyquist
        const mag = new Float32Array(K);

        // Ventana Hann
        const win = new Float32Array(N);
        for (let n = 0; n < N; n++) win[n] = 0.5 * (1 - Math.cos(2 * Math.PI * n / (N - 1)));

        for (let k = 0; k < K; k++) {
            let re = 0, im = 0;
            const angBase = -2 * Math.PI * k / N;
            for (let n = 0; n < N; n++) {
                const s = signal[n] * win[n];
                const ang = angBase * n;
                re += s * Math.cos(ang);
                im += s * Math.sin(ang);
            }
            const amp = Math.sqrt(re * re + im * im) / (N / 2);
            mag[k] = 20 * Math.log10(amp + 1e-9); // dB relativo
        }

        // Normalizar pico a 0 dB (visual)
        let maxVal = -Infinity;
        for (let i = 0; i < K; i++) if (mag[i] > maxVal) maxVal = mag[i];
        for (let i = 0; i < K; i++) mag[i] -= maxVal;

        return mag;
    }

    drawSpectrumPanel(panel, specOD, specOI) {
        const { ctx } = this;
        const { x, y, w, h } = panel;
        const { grid, gridMajor, text, noise, od, oi } = this.config.colors;

        this.strokeRect(x, y, w, h, this.config.colors.panelBorder);

        // Título
        ctx.fillStyle = text;
        ctx.font = 'bold 11px Arial';
        ctx.textAlign = 'left';
        ctx.fillText('Espectro (Señal A+B vs Ruido | dB re. pico)', x + 6, y + 14);

        // Área de ploteo
        const topPad = 22;
        const leftPad = 34;
        const rightPad = 10;
        const bottomPad = 18;

        const px = x + leftPad;
        const py = y + topPad;
        const pw = w - leftPad - rightPad;
        const ph = h - topPad - bottomPad;

        // Rango Y fijo para dB relativos (de -60 a 0 dB)
        const yMin = -60, yMax = 0;
        const yScale = (db) => py + (1 - (db - yMin) / (yMax - yMin)) * ph;

        // Eje Y y grilla
        ctx.save();
        ctx.strokeStyle = grid;
        ctx.lineWidth = 1;

        for (let db = yMin; db <= yMax; db += 10) {
            const yy = yScale(db);
            ctx.strokeStyle = db === 0 ? gridMajor : grid;
            ctx.beginPath();
            ctx.moveTo(px, yy);
            ctx.lineTo(px + pw, yy);
            ctx.stroke();

            ctx.fillStyle = text;
            ctx.font = '10px Arial';
            ctx.textAlign = 'right';
            ctx.fillText(`${db}`, px - 4, yy + 3);
        }
        ctx.restore();

        // Escala X log (frecuencia en Hz)
        const fMin = 500; // evita muy baja frecuencia
        const fMax = Math.min(8000, (specOD?.fs || 24000) / 2);

        const logMin = Math.log10(fMin);
        const logMax = Math.log10(fMax);
        const xScale = (f) => px + ((Math.log10(f) - logMin) / (logMax - logMin)) * pw;

        // Grilla vertical en frecuencias marcadas
        const marks = [500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000].filter(f => f >= fMin && f <= fMax);
        ctx.save();
        marks.forEach(f => {
            const xx = xScale(f);
            ctx.strokeStyle = (f === 1000 || f === 2000 || f === 4000) ? gridMajor : grid;
            ctx.beginPath();
            ctx.moveTo(xx, py);
            ctx.lineTo(xx, py + ph);
            ctx.stroke();

            ctx.fillStyle = this.config.colors.axis;
            ctx.font = '10px Arial';
            ctx.textAlign = 'center';
            const label = f >= 1000 ? `${(f/1000).toFixed(f % 1000 === 0 ? 0 : 1)}k` : `${f}`;
            ctx.fillText(label, xx, py + ph + 12);
        });
        ctx.restore();

        // Trazado de espectros
        const drawCurve = (spec, color, isNoise=false) => {
            if (!spec?.freqs?.length) return;
            const { freqs, signalMag, noiseMag } = spec;
            const yData = isNoise ? noiseMag : signalMag;

            const N = yData.length;
            let started = false;

            ctx.save();
            ctx.beginPath();
            ctx.lineWidth = isNoise ? 1.5 : 2.0;
            ctx.strokeStyle = color;
            if (isNoise) ctx.setLineDash([4, 3]);

            for (let i = 0; i < N; i++) {
                const f = freqs[i];
                if (f < fMin || f > fMax) continue;

                const xx = xScale(f);
                const yy = yScale(yData[i]);
                if (!started) { ctx.moveTo(xx, yy); started = true; }
                else ctx.lineTo(xx, yy);
            }
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.restore();
        };

        // OD (señal y ruido)
        drawCurve(specOD, od, false);
        drawCurve(specOD, noise, true);

        // OI (señal y ruido)
        drawCurve(specOI, oi, false);
        drawCurve(specOI, noise, true);

        // Leyenda local
        this.drawMiniLegend(px + 6, py + 14, [
            { color: this.config.colors.od, label: 'Señal OD (A+B)' },
                            { color: this.config.colors.oi, label: 'Señal OI (A+B)' },
                            { color: this.config.colors.noise, label: 'Ruido (|A−B|/2)' },
        ]);
    }

    // =================== LEYENDA GLOBAL ===================

    drawGlobalLegend(x, y) {
        const { ctx } = this;
        ctx.save();
        ctx.font = '10px Arial';
        ctx.textAlign = 'left';

        const items = [
            { color: this.config.colors.A,  label: 'A' },
            { color: this.config.colors.B,  label: 'B' },
            { color: this.config.colors.AB, label: 'A+B' },
            { color: this.config.colors.od, label: 'Señal OD' },
            { color: this.config.colors.oi, label: 'Señal OI' },
            { color: this.config.colors.noise, label: 'Ruido' },
        ];

        let off = 0;
        items.forEach(it => {
            ctx.fillStyle = it.color;
            ctx.fillRect(x + off, y - 6, 10, 3);
            ctx.fillStyle = this.config.colors.text;
            ctx.fillText(` ${it.label}`, x + off + 12, y);
            off += 90;
        });

        ctx.restore();
    }
}

// Exponer globalmente
window.TEOAEClinicalChartView = TEOAEClinicalChartView;
