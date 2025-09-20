/**
 * DPOAEClinicalChartView - Vista de DPOAE Clínicas (re-hecha)
 * - Soporta datos con llaves en Hz ("1000","1500",...) o kHz ("1.0","1.5",...)
 * - Eje Y configurable (por defecto −30…+30 dB SPL)
 * - Áreas de normalidad (P5–P95) + línea de ruido normativa
 * - Conecta solo puntos con respuesta "presente"
 * - Marca "presente" (●) y "ausente" (×)
 */

class DPOAEClinicalChartView {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.canvas = null;
        this.ctx = null;

        this.config = {
            margin: { top: 30, right: 40, bottom: 50, left: 60 },
            colors: {
                od: '#dc3545',
                oi: '#007bff',
                grid: '#e0e0e0',
                gridMajor: '#c9c9c9',
                text: '#333',
                normalArea: 'rgba(40, 167, 69, 0.15)',
                normalStroke: 'rgba(40, 167, 69, 0.5)',
                noiseLine: '#999',
                axis: '#555',
                panelBorder: '#e5e7eb'
            },
            // Límites Y (ajustable)
            limits: { yMin: -30, yMax: 30 },
        };

        // Datos normativos del DP-Gram
        // Frecuencias en kHz como claves numéricas
        this.normativeData = {
            1.0: { noise: -15, p5: 5,  p95: 22 },
            1.5: { noise: -16, p5: 4,  p95: 21 },
            2.0: { noise: -17, p5: 3,  p95: 18 },
            3.0: { noise: -18, p5: 1,  p95: 15 },
            4.0: { noise: -18, p5: -1, p95: 13 },
            5.0: { noise: -19, p5: -3, p95: 12 },
            6.0: { noise: -20, p5: -4, p95: 11 },
            7.0: { noise: -20, p5: -3, p95: 13 },
            8.0: { noise: -20, p5: -2, p95: 14 }
        };

        // Eje X (kHz)
        this.frequencies = [1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0];
        // Frecuencias evaluadas clínicamente (kHz)
        this.testFrequencies = [1.0, 1.5, 2.0, 3.0, 4.0, 6.0];
    }

    // ===== Inicialización =====
    init() {
        this.canvas = document.getElementById(this.canvasId);
        if (!this.canvas) {
            console.warn(`Canvas ${this.canvasId} no encontrado`);
            return false;
        }
        this.ctx = this.canvas.getContext('2d');
        return true;
    }

    // ===== Render principal =====
    render(data) {
        if (!this.init()) return;

        const { ctx, canvas } = this;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const plotWidth  = canvas.width  - this.config.margin.left - this.config.margin.right;
        const plotHeight = canvas.height - this.config.margin.top  - this.config.margin.bottom;

        const { yMin, yMax } = this.config.limits;
        const yRange = yMax - yMin;

        // Escalas
        const xScale = (freqIndex) =>
        this.config.margin.left + (freqIndex / (this.frequencies.length - 1)) * plotWidth;

        const yScale = (amplitude) =>
        this.config.margin.top + plotHeight - ((amplitude - yMin) / yRange) * plotHeight;

        // Marco opcional
        this.strokeRect(this.config.margin.left, this.config.margin.top, plotWidth, plotHeight, this.config.colors.panelBorder);

        // Componentes
        this.drawGrid(plotWidth, plotHeight, xScale, yScale);
        this.drawNormalityAreas(xScale, yScale);
        this.drawNoiseLine(xScale, yScale);
        this.drawAxes(plotWidth, plotHeight, yScale);
        this.drawData(data, xScale, yScale);
        this.drawLegend();
    }

    // ===== Utilidades =====
    strokeRect(x, y, w, h, color) {
        const { ctx } = this;
        ctx.save();
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, w, h);
        ctx.restore();
    }

    /**
     * Obtiene medición por frecuencia, aceptando llaves "1000" (Hz) o "1.0" (kHz)
     */
    getMeasurement(earData, freqKHz) {
        if (!earData) return null;
        const keyHz  = String(Math.round(freqKHz * 1000)); // "1000"
        const keyKHz = freqKHz.toString();                  // "1" o "1.5"
        return earData[keyHz] || earData[keyKHz] || null;
    }

    // ===== Grid =====
    drawGrid(width, height, xScale, yScale) {
        const { ctx } = this;

        // Verticales (frecuencias)
        this.frequencies.forEach((freq, index) => {
            const x = xScale(index);
            const isTest = this.testFrequencies.includes(freq);

            ctx.strokeStyle = isTest ? this.config.colors.gridMajor : this.config.colors.grid;
            ctx.lineWidth = isTest ? 1.5 : 1;

            ctx.beginPath();
            ctx.moveTo(x, this.config.margin.top);
            ctx.lineTo(x, this.config.margin.top + height);
            ctx.stroke();
        });

        // Horizontales (dB)
        for (let db = this.config.limits.yMin; db <= this.config.limits.yMax; db += 5) {
            const y = yScale(db);
            const isMajor = (db % 10 === 0) || db === 0;

            ctx.strokeStyle = isMajor ? this.config.colors.gridMajor : this.config.colors.grid;
            ctx.lineWidth = (db === 0) ? 2 : 1;

            ctx.beginPath();
            ctx.moveTo(this.config.margin.left, y);
            ctx.lineTo(this.config.margin.left + width, y);
            ctx.stroke();
        }
    }

    // ===== Área de normalidad =====
    drawNormalityAreas(xScale, yScale) {
        const { ctx } = this;
        ctx.fillStyle = this.config.colors.normalArea;
        ctx.strokeStyle = this.config.colors.normalStroke;
        ctx.lineWidth = 1;

        ctx.beginPath();
        // Borde superior (P95)
        this.frequencies.forEach((freq, idx) => {
            const n = this.normativeData[freq];
            if (!n) return;
            const x = xScale(idx);
            const y = yScale(n.p95);
            if (idx === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
            // Borde inferior (P5) en reversa
            for (let i = this.frequencies.length - 1; i >= 0; i--) {
                const freq = this.frequencies[i];
                const n = this.normativeData[freq];
                if (!n) continue;
                const x = xScale(i);
                const y = yScale(n.p5);
                ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
    }

    // ===== Línea de ruido normativa =====
    drawNoiseLine(xScale, yScale) {
        const { ctx } = this;
        ctx.strokeStyle = this.config.colors.noiseLine;
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);

        ctx.beginPath();
        this.frequencies.forEach((freq, idx) => {
            const n = this.normativeData[freq];
            if (!n) return;
            const x = xScale(idx);
            const y = yScale(n.noise);
            if (idx === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
            ctx.stroke();
            ctx.setLineDash([]);
    }

    // ===== Ejes =====
    drawAxes(width, height, yScale) {
        const { ctx } = this;

        // X: etiquetas de frecuencia
        ctx.textAlign = 'center';
        this.frequencies.forEach((freq, index) => {
            const x = this.config.margin.left + (index / (this.frequencies.length - 1)) * width;

            if (this.testFrequencies.includes(freq)) {
                ctx.font = 'bold 11px Arial';
                ctx.fillStyle = this.config.colors.text;
            } else {
                ctx.font = '10px Arial';
                ctx.fillStyle = '#666';
            }

            const label = freq >= 1 ? `${freq}k` : `${freq * 1000}`;
            ctx.fillText(label, x, this.config.margin.top + height + 15);
        });

        // Y: etiquetas de dB
        ctx.textAlign = 'right';
        ctx.font = '11px Arial';
        ctx.fillStyle = this.config.colors.text;
        for (let db = this.config.limits.yMin; db <= this.config.limits.yMax; db += 10) {
            const y = yScale(db);
            ctx.fillText(`${db}`, this.config.margin.left - 10, y + 4);
        }

        // Títulos de ejes
        ctx.textAlign = 'center';
        ctx.font = 'bold 12px Arial';
        ctx.fillStyle = this.config.colors.axis;
        ctx.fillText('Frecuencia (Hz)', this.config.margin.left + width / 2, this.config.margin.top + height + 35);

        ctx.save();
        ctx.translate(20, this.config.margin.top + height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('Amplitud DPOAE (dB SPL)', 0, 0);
        ctx.restore();
    }

    // ===== Datos =====
    drawData(data, xScale, yScale) {
        const ears = [
            { key: 'oido_derecho',  color: this.config.colors.od, label: 'OD' },
            { key: 'oido_izquierdo', color: this.config.colors.oi, label: 'OI' }
        ];

        ears.forEach(ear => {
            const earData = data?.producto_distorsion_clinicas?.[ear.key];
            if (!earData) return;

            const presentPoints = [];
            const absentPoints  = [];

            this.testFrequencies.forEach(freqKHz => {
                const freqIndex = this.frequencies.indexOf(freqKHz);
                const m = this.getMeasurement(earData, freqKHz);

                if (m && m.amplitud !== null && m.amplitud !== undefined) {
                    const x = xScale(freqIndex);
                    const y = yScale(m.amplitud);

                    if (m.respuesta === 'presente') {
                        presentPoints.push({ x, y });
                    } else if (m.respuesta === 'ausente') {
                        absentPoints.push({ x, y });
                    }
                }
            });

            // Conectar solo los presentes
            if (presentPoints.length > 1) {
                this.ctx.strokeStyle = ear.color;
                this.ctx.lineWidth = 2;
                this.ctx.setLineDash([]);
                this.ctx.beginPath();
                presentPoints.forEach((p, i) => {
                    if (i === 0) this.ctx.moveTo(p.x, p.y);
                    else this.ctx.lineTo(p.x, p.y);
                });
                    this.ctx.stroke();
            }

            // Símbolos
            presentPoints.forEach(p => this.drawSymbol(p.x, p.y, 'circle', ear.color, true));
            absentPoints.forEach(p  => this.drawSymbol(p.x, p.y, 'x',      ear.color, false));
        });
    }

    drawSymbol(x, y, symbol, color, filled) {
        const { ctx } = this;
        ctx.fillStyle = color;
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;

        if (symbol === 'circle') {
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            if (filled) ctx.fill(); else ctx.stroke();
        } else if (symbol === 'x') {
            ctx.beginPath();
            ctx.moveTo(x - 4, y - 4);
            ctx.lineTo(x + 4, y + 4);
            ctx.moveTo(x + 4, y - 4);
            ctx.lineTo(x - 4, y + 4);
            ctx.stroke();
        }
    }

    // ===== Leyenda =====
    drawLegend() {
        const { ctx } = this;
        const y = this.config.margin.top + 5;

        ctx.font = '10px Arial';
        ctx.textAlign = 'left';

        // Área normal
        ctx.fillStyle = this.config.colors.normalArea;
        ctx.fillRect(this.config.margin.left, y, 15, 8);
        ctx.fillStyle = this.config.colors.text;
        ctx.fillText('Área normal (P5–P95)', this.config.margin.left + 20, y + 6);

        // Ruido (línea punteada)
        ctx.strokeStyle = this.config.colors.noiseLine;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.moveTo(this.config.margin.left + 150, y + 4);
        ctx.lineTo(this.config.margin.left + 165, y + 4);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillText('Nivel de ruido', this.config.margin.left + 170, y + 6);

        // Símbolos
        const y2 = y + 15;
        this.drawSymbol(this.config.margin.left + 7, y2, 'circle', this.config.colors.od, true);
        ctx.fillStyle = this.config.colors.text;
        ctx.fillText('OD Presente', this.config.margin.left + 20, y2 + 3);

        this.drawSymbol(this.config.margin.left + 100, y2, 'circle', this.config.colors.oi, true);
        ctx.fillText('OI Presente', this.config.margin.left + 113, y2 + 3);

        this.drawSymbol(this.config.margin.left + 200, y2, 'x', '#666', false);
        ctx.fillText('Ausente', this.config.margin.left + 213, y2 + 3);
    }

    // API pública simple
    update(data) { this.render(data); }
    resize(width, height) {
        if (this.canvas) {
            this.canvas.width = width;
            this.canvas.height = height;
        }
    }
    clear() {
        if (this.ctx) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
    }
}

// Exponer globalmente
window.DPOAEClinicalChartView = DPOAEClinicalChartView;
